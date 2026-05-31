from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from hermes_youtube_curator.config.settings import Settings

if TYPE_CHECKING:
    from playwright.sync_api import Browser, Page, Playwright
else:
    Browser = Page = Playwright = Any


class YouTubeSessionError(RuntimeError):
    """Raised when the collector cannot attach to a usable YouTube browser tab."""


@contextmanager
def open_youtube_page(settings: Settings) -> Iterator[Page]:
    if not settings.youtube_cdp_url:
        raise YouTubeSessionError(
            "YouTube collection requires an already-running Chrome debug session. "
            "Start it with scripts/launch_youtube_browser.py and set "
            "HYC_YOUTUBE_CDP_URL=http://127.0.0.1:9222."
        )

    from playwright.sync_api import sync_playwright

    playwright: Playwright | None = None
    browser: Browser | None = None
    try:
        playwright = sync_playwright().start()
        browser = playwright.chromium.connect_over_cdp(settings.youtube_cdp_url)
        pages = [
            page
            for context in browser.contexts
            for page in context.pages
            if page.url.startswith("https://www.youtube.com/")
        ]
        if not pages:
            raise YouTubeSessionError(
                "No open YouTube tab found in the Chrome debug session. "
                "Open https://www.youtube.com/ in that browser and rerun collection."
            )
        yield pages[0]
    finally:
        if browser is not None:
            browser.close()
        if playwright is not None:
            playwright.stop()


def ensure_signed_in(page: Page) -> str:
    try:
        page.wait_for_load_state("domcontentloaded")
    except Exception as exc:
        raise YouTubeSessionError(f"YouTube tab did not finish loading: {exc}") from exc

    sign_in_link = page.locator("a[aria-label*='Sign in'], a[href*='ServiceLogin']")
    try:
        if sign_in_link.count() > 0 and sign_in_link.first.is_visible():
            raise YouTubeSessionError(
                "The open YouTube tab is not signed in. Log in in the Chrome window started "
                "by scripts/launch_youtube_browser.py and rerun collection."
            )
    except YouTubeSessionError:
        raise
    except Exception:
        pass

    return "valid"
