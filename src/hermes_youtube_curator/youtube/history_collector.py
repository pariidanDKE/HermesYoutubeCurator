from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from time import sleep
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse

from hermes_youtube_curator.config.settings import Settings
from hermes_youtube_curator.models import HistoryItem, HistorySnapshot
from hermes_youtube_curator.youtube.browser import (
    YouTubeSessionError,
    ensure_signed_in,
    open_youtube_page,
)

if TYPE_CHECKING:
    from playwright.sync_api import Page
else:
    Page = Any

logger = logging.getLogger(__name__)

# Selector for the per-video cards we extract. Kept in sync with the node query
# inside _extract_visible_history so the coverage check counts the same elements.
_ROW_SELECTOR = (
    "yt-lockup-view-model, ytd-video-renderer, ytd-rich-item-renderer, ytd-reel-item-renderer"
)


class HistoryCollector:
    def collect(self, settings: Settings) -> HistorySnapshot:
        if settings.youtube_cdp_url:
            return self._collect_live(settings)
        if settings.history_fixture:
            return self._collect_fixture(settings.history_fixture)
        return HistorySnapshot(
            history_items=[],
            collection_status="partial",
            warnings=["History collection is not configured; continuing without history evidence."],
        )

    def _collect_fixture(self, fixture_path: Path) -> HistorySnapshot:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        items = [HistoryItem(**item) for item in payload["history_items"]]
        return HistorySnapshot(
            history_items=items,
            collection_status=payload.get("collection_status", "success"),
            warnings=payload.get("warnings", []),
        )

    def _collect_live(self, settings: Settings) -> HistorySnapshot:
        warnings: list[str] = []
        try:
            with open_youtube_page(settings) as page:
                page.goto(settings.youtube_history_url, wait_until="domcontentloaded")
                ensure_signed_in(page)
                items = self._capture_history(page, settings)
                if not items:
                    warnings.append(self._diagnose_empty_history(page))
                else:
                    warnings.extend(self._coverage_warnings(page, len(items)))
                page.goto(settings.youtube_home_url, wait_until="domcontentloaded")
        except YouTubeSessionError as exc:
            return HistorySnapshot(
                history_items=[],
                collection_status="partial",
                warnings=[str(exc)],
            )
        except Exception as exc:
            return HistorySnapshot(
                history_items=[],
                collection_status="partial",
                warnings=[f"History collection failed: {exc}"],
            )

        return HistorySnapshot(
            history_items=items,
            collection_status="success" if items else "partial",
            warnings=warnings,
        )

    def _capture_history(self, page: Page, settings: Settings) -> list[HistoryItem]:
        page.wait_for_selector(
            "ytd-section-list-renderer, ytd-browse[page-subtype='history']",
            timeout=settings.youtube_capture_timeout_seconds * 1000,
        )
        captured: dict[str, HistoryItem] = {}
        display_position = 1

        for capture_index in range(settings.youtube_history_scroll_count + 1):
            for entry in self._extract_visible_history(page):
                dedupe_key = entry["video_id"] or entry["url"] or entry["title"]
                if dedupe_key in captured:
                    continue
                captured[dedupe_key] = HistoryItem(
                    title=entry["title"],
                    channel_name=entry["channel_name"],
                    watched_at_hint=entry["watched_at_hint"],
                    url=entry["url"],
                    video_id=entry["video_id"],
                    recency_bucket=entry["recency_bucket"],
                    display_position=display_position,
                )
                display_position += 1

            if capture_index == settings.youtube_history_scroll_count:
                break
            page.mouse.wheel(0, 1400)
            sleep(settings.youtube_scroll_pause_seconds)

        return list(captured.values())

    def _extract_visible_history(self, page: Page) -> list[dict[str, str | None]]:
        raw_items = page.evaluate(
            """
            () => {
              const clean = (value) => (value || '').replace(/\\s+/g, ' ').trim();
              // Each ytd-item-section-renderer on the history page is a *date group*
              // (e.g. "Today", "Yesterday", "Jun 6") containing many videos. We must
              // iterate the individual video cards inside the sections, not the
              // sections themselves, or we capture only one video per day.
              //
              // YouTube has migrated history rows to the newer `yt-lockup-view-model`
              // component; the legacy `ytd-video-renderer` is all but gone. We match
              // both so a future re-migration in either direction keeps working.
              const nodes = Array.from(document.querySelectorAll(
                'yt-lockup-view-model, ytd-video-renderer, ytd-rich-item-renderer, ytd-reel-item-renderer'
              ));

              return nodes.map((card) => {
                const link = card.querySelector('a#video-title, a[href*="/watch"], a[href*="/shorts/"]');
                // `.yt-lockup-metadata-view-model__title` is the lockup title; the
                // h3/#video-title/yt-formatted-string variants cover legacy renderers.
                const titleHeading = Array.from(card.querySelectorAll(
                  '.yt-lockup-metadata-view-model__title, h3 a span, h3, #video-title, yt-formatted-string'))
                  .map((node) => clean(node.textContent))
                  .find((value) => value && !/^(today|yesterday|monday|tuesday|wednesday|thursday|friday|saturday|sunday)$/i.test(value));
                // Lockups expose the title as a non-"Go to channel" aria-label too.
                const titleAria = Array.from(card.querySelectorAll('a[aria-label]'))
                  .map((node) => node.getAttribute('aria-label') || '')
                  .find((value) => value && !value.startsWith('Go to channel '));
                const metadata = Array.from(card.querySelectorAll('#metadata-line span, .metadata-snippet-text'))
                  .map((node) => (node.textContent || '').replace(/\\s+/g, ' ').trim())
                  .filter(Boolean);
                const text = clean(card.innerText);
                const sectionHeader = card.closest('ytd-item-section-renderer, ytd-rich-section-renderer')
                  ?.querySelector('#title, h2, yt-formatted-string#title')
                  ?.textContent
                  ?.replace(/\\s+/g, ' ')
                  .trim() || null;
                const channelAria = Array.from(card.querySelectorAll('[aria-label]'))
                  .map((node) => node.getAttribute('aria-label') || '')
                  .find((value) => value.startsWith('Go to channel '));
                const channelName = clean(
                  card.querySelector('#channel-name, ytd-channel-name, #byline-container')
                    ?.textContent
                ) || (channelAria ? channelAria.replace(/^Go to channel\\s+/, '') : null);
                const watchedHint = metadata.find((value) =>
                  /ago|today|yesterday|just now/i.test(value)
                ) || text.match(/(?:just now|today|yesterday|\\d+\\s+(?:seconds?|minutes?|hours?|days?|weeks?|months?|years?)\\s+ago)/i)?.[0]
                  || sectionHeader;
                const title = titleHeading || clean(titleAria) || clean(link?.getAttribute('title') || link?.textContent);
                return {
                  title,
                  channel_name: channelName,
                  url: link?.href || null,
                  watched_at_hint: watchedHint,
                  section_header: sectionHeader,
                };
              })
              .filter((item) => item.title && item.url && item.watched_at_hint);
            }
            """
        )

        extracted: list[dict[str, str | None]] = []
        for item in raw_items:
            extracted.append(
                {
                    "title": item["title"],
                    "channel_name": item["channel_name"] or "Unknown channel",
                    "url": item["url"],
                    "video_id": _extract_video_id(item["url"]),
                    "watched_at_hint": item["watched_at_hint"],
                    "recency_bucket": _normalize_recency_bucket(item["watched_at_hint"]),
                }
            )
        return extracted

    def _coverage_warnings(self, page: Page, captured_count: int) -> list[str]:
        """Flag runs that captured far fewer items than the page actually holds.

        A silent YouTube DOM change (stale row selector) or an over-strict filter
        shows up here as "many candidate rows / date sections but few captured",
        so a degraded scrape stops masquerading as a healthy `success` run.
        """
        counts = page.evaluate(
            """
            (rowSelector) => ({
              rows: document.querySelectorAll(rowSelector).length,
              sections: document.querySelectorAll('ytd-item-section-renderer').length,
            })
            """,
            _ROW_SELECTOR,
        )
        rows = counts["rows"]
        sections = counts["sections"]
        logger.info(
            "history capture: %d items from %d candidate rows across %d date sections",
            captured_count,
            rows,
            sections,
        )

        warnings: list[str] = []
        if rows >= 10 and captured_count < rows * 0.5:
            warnings.append(
                f"History capture looks low: extracted {captured_count} items from "
                f"{rows} candidate rows on the page — the row selector or extraction "
                "filter may be stale (YouTube DOM change)."
            )
        if sections >= 3 and captured_count <= sections:
            warnings.append(
                f"History capture looks collapsed: {captured_count} items across "
                f"{sections} date sections (~one per day) — extraction may be reading "
                "one video per date group instead of all of them."
            )
        return warnings

    def _diagnose_empty_history(self, page: Page) -> str:
        diagnostics = page.evaluate(
            """
            () => ({
              url: window.location.href,
              title: document.title,
              videoRenderers: document.querySelectorAll('ytd-video-renderer').length,
              richItems: document.querySelectorAll('ytd-rich-item-renderer').length,
              signInLinks: document.querySelectorAll("a[href*='ServiceLogin']").length,
              bodyTextSample: document.body?.innerText?.slice(0, 500) || '',
            })
            """
        )
        return (
            "History page loaded but no watch entries were extracted: "
            f"url={diagnostics['url']!r}, "
            f"title={diagnostics['title']!r}, "
            f"video_renderers={diagnostics['videoRenderers']}, "
            f"rich_items={diagnostics['richItems']}, "
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


def _normalize_recency_bucket(watched_at_hint: str | None) -> str | None:
    if not watched_at_hint:
        return None

    normalized = watched_at_hint.strip().lower()
    if normalized in {"just now", "today"}:
        return "immediate"
    if "minute" in normalized or "hour" in normalized or normalized == "yesterday":
        return "same-day"
    if "day" in normalized:
        return "recent"
    if "week" in normalized or "month" in normalized or "year" in normalized:
        return "older"
    if normalized in _WEEKDAY_NAMES:
        return "same-day" if normalized == _today_weekday_name() else "recent"
    if _looks_like_calendar_date(normalized):
        return "older"
    return None


_WEEKDAY_NAMES = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}


def _today_weekday_name() -> str:
    return datetime.now(UTC).strftime("%A").lower()


def _looks_like_calendar_date(value: str) -> bool:
    month_names = {
        "january",
        "jan",
        "february",
        "feb",
        "march",
        "mar",
        "april",
        "apr",
        "may",
        "june",
        "jun",
        "july",
        "jul",
        "august",
        "aug",
        "september",
        "sep",
        "sept",
        "october",
        "oct",
        "november",
        "nov",
        "december",
        "dec",
    }
    parts = value.replace(",", "").split()
    return len(parts) >= 2 and parts[0] in month_names and parts[1].isdigit()
