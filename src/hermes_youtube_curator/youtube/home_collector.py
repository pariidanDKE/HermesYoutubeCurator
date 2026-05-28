from __future__ import annotations

from time import sleep
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse

from hermes_youtube_curator.config.settings import Settings
from hermes_youtube_curator.models import RecommendationItem, RecommendationSnapshot
from hermes_youtube_curator.youtube.browser import (
    YouTubeSessionError,
    ensure_signed_in,
    open_youtube_page,
    persist_storage_state,
)

if TYPE_CHECKING:
    from playwright.sync_api import Page
else:
    Page = Any


class HomeCollector:
    def collect(self, settings: Settings) -> RecommendationSnapshot:
        warnings: list[str] = []
        try:
            with open_youtube_page(settings, url=settings.youtube_home_url) as page:
                session_state, session_warnings = ensure_signed_in(page, settings)
                warnings.extend(session_warnings)
                if not page.url.startswith(settings.youtube_home_url):
                    page.goto(settings.youtube_home_url, wait_until="domcontentloaded")
                persist_storage_state(page, settings)
                recommendations = self._capture_homepage(page, settings)
                if not recommendations:
                    warnings.append(self._diagnose_empty_homepage(page))
        except YouTubeSessionError as exc:
            return RecommendationSnapshot(
                recommendations=[],
                collection_status="partial",
                session_state="login_required",
                warnings=[str(exc)],
            )
        except Exception as exc:
            return RecommendationSnapshot(
                recommendations=[],
                collection_status="partial",
                session_state="collector_error",
                warnings=[f"Homepage collection failed: {exc}"],
            )

        return RecommendationSnapshot(
            recommendations=recommendations,
            collection_status="success" if recommendations else "partial",
            session_state=session_state,
            warnings=warnings,
        )

    def _capture_homepage(
        self,
        page: Page,
        settings: Settings,
    ) -> list[RecommendationItem]:
        page.wait_for_selector(
            "ytd-rich-grid-renderer, ytd-browse[page-subtype='home']",
            timeout=settings.youtube_capture_timeout_seconds * 1000,
        )
        captured: dict[str, RecommendationItem] = {}
        display_position = 1

        for capture_index in range(settings.youtube_home_scroll_count + 1):
            for entry in self._extract_visible_recommendations(page):
                dedupe_key = entry["video_id"] or entry["url"] or entry["title"]
                if dedupe_key in captured:
                    continue
                captured[dedupe_key] = RecommendationItem(
                    title=entry["title"],
                    channel_name=entry["channel_name"],
                    url=entry["url"],
                    video_id=entry["video_id"],
                    description_excerpt=entry["description_excerpt"],
                    thumbnail_url=entry["thumbnail_url"],
                    content_type=entry["content_type"],
                    duration_hint=entry["duration_hint"],
                    view_count_hint=entry["view_count_hint"],
                    age_hint=entry["age_hint"],
                    display_position=display_position,
                )
                display_position += 1

            if capture_index == settings.youtube_home_scroll_count:
                break
            page.mouse.wheel(0, 1400)
            sleep(settings.youtube_scroll_pause_seconds)

        return list(captured.values())

    def _extract_visible_recommendations(self, page: Page) -> list[dict[str, str | None]]:
        raw_items = page.evaluate(
            """
            () => Array.from(document.querySelectorAll(
                'ytd-rich-item-renderer, ytd-rich-grid-media, ytd-video-renderer'
              ))
              .map((card) => {
                const links = Array.from(card.querySelectorAll('a[href]'));
                const videoLinks = links.filter((link) =>
                  link.href.includes('/watch') || link.href.includes('/shorts/')
                );
                const invalidTitle = /^(watch|mix|\\d{1,2}:\\d{2}(?::\\d{2})?)$/i;
                const titleLink = videoLinks.find((link) => {
                  const text = (link.getAttribute('title') || link.innerText || '').trim();
                  return text && !invalidTitle.test(text);
                });
                const fallbackVideoLink = videoLinks[0] || null;
                const channelNode = links.find((link) =>
                  link.href.includes('/@') || link.href.includes('/channel/')
                );
                const imageNode = card.querySelector('img');
                const metadataLine = card.querySelector('#metadata-line');
                const title = titleLink?.getAttribute('title') || titleLink?.innerText?.trim() || null;
                const text = (card.innerText || '').replace(/\\s+/g, ' ').trim();
                const ariaLabels = Array.from(card.querySelectorAll('[aria-label]'))
                  .map((node) => node.getAttribute('aria-label') || '')
                  .filter(Boolean);
                const durationFromText = text.match(/\\b\\d{1,2}:\\d{2}(?::\\d{2})?\\b/)?.[0] || null;
                const durationFromAria = ariaLabels.find((label) =>
                  /\\b\\d+\\s+(seconds?|minutes?|hours?)\\b/i.test(label)
                ) || null;
                const views = text.match(/\\b[\\d,.]+\\s*[KMB]?\\s+views\\b/i)?.[0] || null;
                const age = ariaLabels.find((label) =>
                    /\\b\\d+\\s+(seconds?|minutes?|hours?|days?|weeks?|months?|years?)\\s+ago\\b/i.test(label)
                  )
                  || text.match(/\\b\\d+\\s+(seconds?|minutes?|hours?|days?|weeks?|months?|years?)\\s+ago\\b/i)?.[0]
                  || null;
                const hasSponsored = /\\bSponsored\\b/i.test(text);
                const hasShorts = (titleLink?.href || fallbackVideoLink?.href || '').includes('/shorts/')
                  || card.className.includes('ytd-rich-shelf-renderer');
                return {
                  title,
                  channel_name: channelNode?.textContent?.trim() || null,
                  url: titleLink?.href || fallbackVideoLink?.href || null,
                  thumbnail_url: imageNode?.src || imageNode?.getAttribute('src') || null,
                  description_excerpt: metadataLine?.textContent?.trim() || null,
                  content_type: hasSponsored ? 'ad' : hasShorts ? 'short' : 'video',
                  duration_hint: durationFromText || durationFromAria,
                  view_count_hint: views,
                  age_hint: age,
                };
              })
              .filter((item) => item.title && item.url);
            """
        )

        extracted: list[dict[str, str | None]] = []
        for item in raw_items:
            extracted.append(
                {
                    "title": item["title"],
                    "channel_name": item["channel_name"] or "Unknown channel",
                    "url": item["url"],
                    "thumbnail_url": item.get("thumbnail_url"),
                    "description_excerpt": item.get("description_excerpt"),
                    "content_type": item.get("content_type") or "video",
                    "duration_hint": item.get("duration_hint"),
                    "view_count_hint": item.get("view_count_hint"),
                    "age_hint": item.get("age_hint"),
                    "video_id": _extract_video_id(item["url"]),
                }
            )
        return extracted

    def _diagnose_empty_homepage(self, page: Page) -> str:
        diagnostics = page.evaluate(
            """
            () => ({
              url: window.location.href,
              title: document.title,
              richItems: document.querySelectorAll('ytd-rich-item-renderer').length,
              videoTitles: document.querySelectorAll('#video-title').length,
              thumbnails: document.querySelectorAll('a#thumbnail').length,
              avatarButtons: document.querySelectorAll('button#avatar-btn').length,
              signInLinks: document.querySelectorAll("a[href*='ServiceLogin']").length,
              bodyTextSample: document.body?.innerText?.slice(0, 500) || '',
            })
            """
        )
        return (
            "Homepage loaded but no recommendations were extracted: "
            f"url={diagnostics['url']!r}, "
            f"title={diagnostics['title']!r}, "
            f"rich_items={diagnostics['richItems']}, "
            f"video_titles={diagnostics['videoTitles']}, "
            f"thumbnails={diagnostics['thumbnails']}, "
            f"avatar_buttons={diagnostics['avatarButtons']}, "
            f"sign_in_links={diagnostics['signInLinks']}, "
            f"body_sample={diagnostics['bodyTextSample']!r}"
        )


def _extract_video_id(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    if parsed.path == "/watch":
        values = parse_qs(parsed.query).get("v")
        return values[0] if values else None
    if parsed.path.startswith("/shorts/"):
        return parsed.path.split("/shorts/", 1)[1].split("/", 1)[0]
    return None
