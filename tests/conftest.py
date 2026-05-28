from __future__ import annotations

import json
from pathlib import Path

import pytest

from hermes_youtube_curator.config.settings import Settings
from hermes_youtube_curator.models import RecommendationItem, RecommendationSnapshot
from hermes_youtube_curator.pipeline.context import AppContext


@pytest.fixture()
def fixture_dir(tmp_path: Path) -> Path:
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    (fixture_dir / "homepage.json").write_text(
        json.dumps(
            {
                "recommendations": [
                    {
                        "video_id": "vid-1",
                        "title": "Practical agent design",
                        "channel_name": "Hermes Lab",
                        "url": "https://youtube.com/watch?v=vid-1",
                        "display_position": 1,
                        "description_excerpt": "Designing bounded agent loops.",
                    },
                    {
                        "video_id": "vid-2",
                        "title": "SQLite for local apps",
                        "channel_name": "Data Craft",
                        "url": "https://youtube.com/watch?v=vid-2",
                        "display_position": 2,
                    },
                    {
                        "video_id": "vid-3",
                        "title": "Yesterday's topic again",
                        "channel_name": "Hermes Lab",
                        "url": "https://youtube.com/watch?v=vid-3",
                        "display_position": 3,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    (fixture_dir / "history.json").write_text(
        json.dumps(
            {
                "history_items": [
                    {
                        "video_id": "vid-3",
                        "title": "Yesterday's topic again",
                        "channel_name": "Hermes Lab",
                        "url": "https://youtube.com/watch?v=vid-3",
                        "watched_at_hint": "2 hours ago",
                        "recency_bucket": "same-day",
                        "display_position": 1,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (fixture_dir / "enrichment.json").write_text(
        json.dumps(
            {
                "videos": [
                    {
                        "video_id": "vid-1",
                        "title": "Practical agent design",
                        "channel_name": "Hermes Lab",
                        "metadata_status": "available",
                        "description_text": "A deterministic agent workflow overview.",
                        "transcript_status": "available",
                        "transcript_text": "Transcript text for vid-1.",
                    },
                    {
                        "video_id": "vid-2",
                        "title": "SQLite for local apps",
                        "channel_name": "Data Craft",
                        "metadata_status": "available",
                        "description_text": "Patterns for durable local state.",
                        "transcript_status": "unavailable",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    return fixture_dir


@pytest.fixture()
def app_context(tmp_path: Path, fixture_dir: Path) -> AppContext:
    state_dir = tmp_path / "state"
    settings = Settings(
        state_dir=state_dir,
        artifact_dir=state_dir / "artifacts",
        sqlite_path=state_dir / "curator.db",
        home_fixture=fixture_dir / "homepage.json",
        history_fixture=fixture_dir / "history.json",
        enrichment_fixture=fixture_dir / "enrichment.json",
        telegram_outbox=state_dir / "telegram.log",
        scheduler="hermes-cron",
        max_enrichment=2,
        telegram_fail_delivery=False,
    )
    context = AppContext.build(settings)
    context.home_collector = _FixtureHomeCollector()
    return context


class _FixtureHomeCollector:
    def collect(self, settings: Settings) -> RecommendationSnapshot:
        if not settings.home_fixture:
            return RecommendationSnapshot(
                recommendations=[],
                collection_status="partial",
                session_state="missing_fixture",
                warnings=["Homepage fixture not configured; returning empty snapshot."],
            )

        payload = json.loads(settings.home_fixture.read_text(encoding="utf-8"))
        return RecommendationSnapshot(
            recommendations=[
                RecommendationItem(**item) for item in payload["recommendations"]
            ],
            collection_status=payload.get("collection_status", "success"),
            session_state=payload.get("session_state", "valid"),
            warnings=payload.get("warnings", []),
        )
