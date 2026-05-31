from __future__ import annotations

from pathlib import Path

import pytest

from hermes_youtube_curator.config.settings import Settings
from hermes_youtube_curator.youtube.history_collector import HistoryCollector


@pytest.fixture()
def live_history_settings(tmp_path: Path) -> Settings:
    state_dir = Path(".local/state/hermes-youtube-curator")
    return Settings(
        state_dir=state_dir,
        artifact_dir=state_dir / "artifacts",
        sqlite_path=state_dir / "curator.db",
        home_fixture=None,
        history_fixture=None,
        enrichment_fixture=None,
        telegram_outbox=state_dir / "telegram.log",
        scheduler="manual-test",
        max_enrichment=2,
        telegram_fail_delivery=False,
        youtube_user_data_dir=state_dir / "chrome-profile",
        youtube_cdp_url="http://127.0.0.1:9222",
        youtube_home_scroll_count=2,
        youtube_scroll_pause_seconds=0.0,
        youtube_capture_timeout_seconds=10,
    )


def test_collect_live_history_records_structure(
    live_history_settings: Settings,
) -> None:
    pytest.importorskip("playwright", reason="playwright not installed")

    collector = HistoryCollector()
    snapshot = collector.collect(live_history_settings)

    assert snapshot.collection_status == "success", snapshot.warnings
    assert snapshot.history_item_count > 0
    assert all(
        item.title and item.channel_name and item.url and item.watched_at_hint
        for item in snapshot.history_items
    )
    assert any(item.recency_bucket for item in snapshot.history_items[:10])
