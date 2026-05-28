from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from time import monotonic, sleep
from typing import TYPE_CHECKING, Any

from hermes_youtube_curator.config.settings import Settings

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext, Page, Playwright
else:
    Browser = BrowserContext = Page = Playwright = Any


class YouTubeSessionError(RuntimeError):
    """Raised when the YouTube collector cannot establish a usable signed-in session."""


@contextmanager
def open_youtube_page(
    settings: Settings,
    *,
    url: str,
) -> Iterator[Page]:
    from playwright.sync_api import sync_playwright

    playwright: Playwright | None = None
    browser: Browser | None = None
    context: BrowserContext | None = None
    external_browser = False
    try:
        playwright = sync_playwright().start()
        if settings.youtube_cdp_url:
            external_browser = True
            browser = playwright.chromium.connect_over_cdp(settings.youtube_cdp_url)
            if not browser.contexts:
                raise YouTubeSessionError(
                    f"No Chrome contexts available at {settings.youtube_cdp_url}."
                )
            context = browser.contexts[0]
        else:
            launch_kwargs = {"headless": settings.youtube_headless}
            if settings.youtube_browser_executable:
                launch_kwargs["executable_path"] = str(settings.youtube_browser_executable)
            elif settings.youtube_user_data_dir:
                raise YouTubeSessionError(
                    "Authenticated YouTube collection requires an installed Chrome executable. "
                    "Set HYC_YOUTUBE_BROWSER_EXECUTABLE to google-chrome or google-chrome-stable."
                )

        if settings.youtube_user_data_dir and not settings.youtube_cdp_url:
            context = playwright.chromium.launch_persistent_context(
                str(settings.youtube_user_data_dir),
                **launch_kwargs,
            )
        elif not settings.youtube_cdp_url:
            browser = playwright.chromium.launch(**launch_kwargs)
            context_kwargs: dict[str, str] = {}
            if settings.youtube_storage_state and settings.youtube_storage_state.exists():
                context_kwargs["storage_state"] = str(settings.youtube_storage_state)
            context = browser.new_context(**context_kwargs)

        page = context.pages[0] if context.pages else context.new_page()
        page.goto(url, wait_until="domcontentloaded")
        yield page
    finally:
        if settings.youtube_debug_hold_seconds > 0:
            sleep(settings.youtube_debug_hold_seconds)
        if context is not None and not external_browser:
            context.close()
        if browser is not None and not external_browser:
            browser.close()
        if playwright is not None:
            playwright.stop()


def ensure_signed_in(page: Page, settings: Settings) -> tuple[str, list[str]]:
    warnings: list[str] = []
    if accept_google_consent(page):
        warnings.append("Accepted Google consent prompt before checking YouTube login state.")

    if _page_is_signed_in(page):
        return "valid", warnings

    if settings.youtube_allow_manual_login and not settings.youtube_headless:
        warnings.append(
            "YouTube session was not signed in; waiting for a manual login in the open browser."
        )
        _wait_for_manual_login(page, settings)
        if _page_is_signed_in(page):
            return "valid", warnings

    raise YouTubeSessionError(
        "YouTube login required. Configure HYC_YOUTUBE_USER_DATA_DIR or "
        "HYC_YOUTUBE_STORAGE_STATE, or run headful with "
        "HYC_YOUTUBE_ALLOW_MANUAL_LOGIN=true to complete login manually."
    )


def accept_google_consent(page: Page) -> bool:
    try:
        body_text = page.locator("body").inner_text(timeout=2_000)
    except Exception:
        return False

    if "Before you continue" not in body_text and "cookies and data" not in body_text:
        return False

    clicked = page.evaluate(
        """
        () => {
          const labels = ['Accept all', 'I agree', 'Reject all'];
          const candidates = Array.from(document.querySelectorAll('button, [role="button"]'));
          for (const label of labels) {
            const match = candidates.find((node) => (node.innerText || '').trim() === label);
            if (match) {
              match.scrollIntoView({block: 'center'});
              match.click();
              return label;
            }
          }
          return null;
        }
        """
    )
    if clicked:
        page.wait_for_load_state("domcontentloaded")
        return True
    return False


def persist_storage_state(page: Page, settings: Settings) -> None:
    if not settings.youtube_storage_state:
        return
    settings.youtube_storage_state.parent.mkdir(parents=True, exist_ok=True)
    page.context.storage_state(path=str(settings.youtube_storage_state))


def _wait_for_manual_login(page: Page, settings: Settings) -> None:
    timeout_at = monotonic() + settings.youtube_manual_login_timeout_seconds
    if page.url.startswith("https://www.youtube.com/"):
        page.goto("https://accounts.google.com/ServiceLogin?service=youtube")

    while monotonic() < timeout_at:
        if _page_is_signed_in(page):
            return
        sleep(2.0)
        try:
            page.reload(wait_until="domcontentloaded")
        except Exception:
            continue

    raise YouTubeSessionError(
        f"Timed out waiting for manual YouTube login after "
        f"{settings.youtube_manual_login_timeout_seconds} seconds."
    )


def _page_is_signed_in(page: Page) -> bool:
    try:
        page.wait_for_load_state("domcontentloaded")
    except Exception:
        return False

    avatar_button = page.locator("button#avatar-btn")
    sign_in_link = page.locator("a[aria-label*='Sign in'], a[href*='ServiceLogin']")
    try:
        if avatar_button.count() > 0 and avatar_button.first.is_visible():
            return True
    except Exception:
        return False
    try:
        if sign_in_link.count() > 0 and sign_in_link.first.is_visible():
            return False
    except Exception:
        pass
    return "ServiceLogin" not in page.url
