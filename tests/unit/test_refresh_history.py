import json
from pathlib import Path

from hermes_youtube_curator.cli.refresh_history import run_refresh_history
from hermes_youtube_curator.youtube.history_collector import (
    HistoryCollector,
    _normalize_recency_bucket,
)


def test_refresh_history_persists_recency(app_context):
    payload = run_refresh_history(app_context)
    artifact = json.loads(Path(payload["artifact_path"]).read_text(encoding="utf-8"))
    assert payload["history_item_count"] == 1
    assert artifact["history_items"][0]["recency_bucket"] == "same-day"


def test_normalize_recency_bucket_handles_expected_ranges():
    assert _normalize_recency_bucket("just now") == "immediate"
    assert _normalize_recency_bucket("2 hours ago") == "same-day"
    assert _normalize_recency_bucket("3 days ago") == "recent"
    assert _normalize_recency_bucket("2 weeks ago") == "older"
    assert _normalize_recency_bucket("May 18") == "older"
    assert _normalize_recency_bucket("Nov 2, 2025") == "older"


def test_extract_visible_history_uses_section_renderers():
    collector = HistoryCollector()

    class _FakePage:
        def evaluate(self, _script: str):
            return [
                {
                    "title": "Ludwig Absolutely Cooks Cinna",
                    "channel_name": "Ludwig VODs",
                    "url": "https://www.youtube.com/watch?v=76-Ipjkvmgg",
                    "watched_at_hint": "Today",
                    "section_header": "Today",
                },
                {
                    "title": "Gemma Guide - Visual Assistant with Spatial Grounding",
                    "channel_name": "Dan Parii",
                    "url": "https://www.youtube.com/watch?v=xtAuC4PHdzY",
                    "watched_at_hint": "May 18",
                    "section_header": "May 18",
                },
            ]

    items = collector._extract_visible_history(_FakePage())

    assert items == [
        {
            "title": "Ludwig Absolutely Cooks Cinna",
            "channel_name": "Ludwig VODs",
            "url": "https://www.youtube.com/watch?v=76-Ipjkvmgg",
            "video_id": "76-Ipjkvmgg",
            "watched_at_hint": "Today",
            "recency_bucket": "immediate",
        },
        {
            "title": "Gemma Guide - Visual Assistant with Spatial Grounding",
            "channel_name": "Dan Parii",
            "url": "https://www.youtube.com/watch?v=xtAuC4PHdzY",
            "video_id": "xtAuC4PHdzY",
            "watched_at_hint": "May 18",
            "recency_bucket": "older",
        },
    ]
