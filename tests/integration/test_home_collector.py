from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from hermes_youtube_curator.config.settings import Settings
from hermes_youtube_curator.youtube.browser import open_youtube_page
from hermes_youtube_curator.youtube.home_collector import HomeCollector


@pytest.fixture()
def live_home_settings(tmp_path: Path) -> Settings:
    state_dir = Path(".local/state/hermes-youtube-curator")
    return Settings(
        state_dir=state_dir,
        artifact_dir=state_dir / "artifacts",
        home_fixture=None,
        history_fixture=None,
        scheduler="manual-test",
        youtube_user_data_dir=state_dir / "chrome-profile",
        youtube_cdp_url="http://127.0.0.1:9222",
        youtube_home_scroll_count=2,
        youtube_scroll_pause_seconds=0.0,
        youtube_capture_timeout_seconds=10,
    )


def test_collect_live_homepage_records_structure(
    live_home_settings: Settings,
) -> None:
    pytest.importorskip("playwright", reason="playwright not installed")

    collector = HomeCollector()
    snapshot = collector.collect(live_home_settings)
    raw_cards = _sample_homepage_cards(live_home_settings)
    artifact_path = live_home_settings.artifact_dir / "integration-home-snapshot.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(
        json.dumps(
            {
                "user_data_dir": str(live_home_settings.youtube_user_data_dir),
                "cdp_url": live_home_settings.youtube_cdp_url,
                "collection_status": snapshot.collection_status,
                "session_state": snapshot.session_state,
                "warnings": snapshot.warnings,
                "recommendation_count": snapshot.recommendation_count,
                "raw_card_sample": raw_cards,
                "recommendations": [
                    {
                        "title": item.title,
                        "channel_name": item.channel_name,
                        "url": item.url,
                        "video_id": item.video_id,
                        "content_type": item.content_type,
                        "duration_hint": item.duration_hint,
                        "view_count_hint": item.view_count_hint,
                        "age_hint": item.age_hint,
                        "display_position": item.display_position,
                    }
                    for item in snapshot.recommendations
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nSaved live homepage snapshot preview to: {artifact_path}")
    print(f"collection_status={snapshot.collection_status}")
    print(f"session_state={snapshot.session_state}")
    print(f"recommendation_count={snapshot.recommendation_count}")
    if snapshot.warnings:
        print("warnings:")
        for warning in snapshot.warnings:
            print(f"- {warning}")
    print("recommendations:")
    for item in snapshot.recommendations[:10]:
        print(
            f"- #{item.display_position} {item.title} | "
            f"{item.channel_name} | {item.content_type or 'unknown-type'} | "
            f"{item.duration_hint or 'no-duration'} | {item.view_count_hint or 'no-views'} | "
            f"{item.age_hint or 'no-age'} | {item.video_id or 'no-video-id'} | {item.url}"
        )
    print("raw_card_sample:")
    for index, card in enumerate(raw_cards[:5], start=1):
        print(f"- raw #{index}:")
        print(f"  tag={card['tag_name']} text={card['text_sample']!r}")
        print(f"  links={card['links'][:3]}")
        print(f"  aria_labels={card['aria_labels'][:3]}")

    assert snapshot.collection_status == "success", snapshot.warnings
    assert snapshot.recommendation_count > 0
    assert all(item.title and item.channel_name and item.url for item in snapshot.recommendations)
    assert not any(
        item.title.lower() in {"watch", "mix"} or re.fullmatch(r"\d{1,2}:\d{2}(?::\d{2})?", item.title)
        for item in snapshot.recommendations[:10]
    )


def _sample_homepage_cards(settings: Settings) -> list[dict[str, object]]:
    with open_youtube_page(settings) as page:
        page.wait_for_selector(
            "ytd-rich-item-renderer, ytd-rich-grid-media, ytd-video-renderer",
            timeout=settings.youtube_capture_timeout_seconds * 1000,
        )
        return page.evaluate(
            """
            () => Array.from(document.querySelectorAll(
                'ytd-rich-item-renderer, ytd-rich-grid-media, ytd-video-renderer'
              ))
              .slice(0, 8)
              .map((card) => ({
                tag_name: card.tagName.toLowerCase(),
                id: card.id || null,
                classes: card.className || null,
                text_sample: (card.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 700),
                links: Array.from(card.querySelectorAll('a[href]')).slice(0, 8).map((link) => ({
                  text: (link.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 160),
                  title: link.getAttribute('title'),
                  href: link.href,
                  aria_label: link.getAttribute('aria-label'),
                  id: link.id || null,
                })),
                images: Array.from(card.querySelectorAll('img')).slice(0, 4).map((image) => ({
                  alt: image.getAttribute('alt'),
                  src: image.currentSrc || image.src || image.getAttribute('src'),
                })),
                aria_labels: Array.from(card.querySelectorAll('[aria-label]')).slice(0, 8).map((node) => ({
                  tag: node.tagName.toLowerCase(),
                  id: node.id || null,
                  aria_label: node.getAttribute('aria-label'),
                  text: (node.innerText || '').replace(/\\s+/g, ' ').trim().slice(0, 160),
                })),
              }));
            """
        )
