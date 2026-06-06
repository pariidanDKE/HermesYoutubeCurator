from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hermes_youtube_curator.models import (
    HistoryItem,
    HistorySnapshot,
    RecommendationItem,
    RecommendationSnapshot,
    utc_now,
)


class WikiStore:
    def __init__(self, wiki_path: Path) -> None:
        self.wiki_path = wiki_path
        self.raw_curator_dir = wiki_path / "raw" / "curator"
        self.runs_dir = self.raw_curator_dir / "runs"
        self._initialize()

    @property
    def videos_path(self) -> Path:
        return self.raw_curator_dir / "videos.json"

    @property
    def recommendation_events_path(self) -> Path:
        return self.raw_curator_dir / "recommendation-events.jsonl"

    @property
    def watch_history_events_path(self) -> Path:
        return self.raw_curator_dir / "watch-history-events.jsonl"

    @property
    def transcripts_dir(self) -> Path:
        return self.wiki_path / "raw" / "transcripts"

    def _initialize(self) -> None:
        for relative_path in [
            "raw/articles",
            "raw/papers",
            "raw/transcripts",
            "raw/assets",
            "raw/curator/runs",
            "entities",
            "concepts",
            "comparisons",
            "queries",
        ]:
            (self.wiki_path / relative_path).mkdir(parents=True, exist_ok=True)

        self._write_once(
            self.wiki_path / "SCHEMA.md",
            """# Wiki Schema

## Domain
Personal YouTube curation: recommendations, watch history, videos, channels, topics, taste, and curator decisions.

## Raw Curator Files
- `raw/curator/videos.json`: canonical video index keyed by YouTube video ID or collected URL.
- `raw/curator/recommendation-events.jsonl`: append-only recommendation observations.
- `raw/curator/watch-history-events.jsonl`: append-only first-seen watch-history observations.
- `raw/curator/runs/`: small immutable manifests that point at full app artifacts.

## Wiki Pages
- `entities/`: concrete videos, channels, tools, people, products, and organizations.
- `concepts/`: durable interests, formats, topics, and taste patterns.
- `comparisons/`: side-by-side analyses worth preserving.
- `queries/`: substantial saved answers or reports.

## Conventions
- File names are lowercase, hyphenated markdown.
- Agent-owned pages use YAML frontmatter with title, created, updated, type, tags, and sources.
- Raw curator files are deterministic source material for code and wiki synthesis.
""",
        )
        self._write_once(
            self.wiki_path / "index.md",
            """# Wiki Index
> Content catalog for synthesized curator knowledge.

## Entities

## Concepts

## Comparisons

## Queries
""",
        )
        self._write_once(
            self.wiki_path / "log.md",
            f"""# Wiki Log

## [{utc_now()[:10]}] create | Wiki initialized
- Structure created for Hermes YouTube Curator.
""",
        )
        self._write_json_if_missing(self.videos_path, {})
        self.recommendation_events_path.touch(exist_ok=True)
        self.watch_history_events_path.touch(exist_ok=True)

    def record_home_snapshot(
        self,
        snapshot: RecommendationSnapshot,
        *,
        artifact_path: Path,
        run_id: str | None = None,
    ) -> None:
        self._upsert_videos(snapshot.recommendations, source="recommendation")
        for item in snapshot.recommendations:
            self._append_jsonl(
                self.recommendation_events_path,
                {
                    "event_type": "recommendation",
                    "run_id": run_id,
                    "snapshot_id": snapshot.snapshot_id,
                    "observed_at": snapshot.captured_at,
                    "source": snapshot.source,
                    "video_id": item.video_id,
                    "url": item.url,
                    "title": item.title,
                    "channel_name": item.channel_name,
                    "display_position": item.display_position,
                    "section_label": item.section_label,
                    "content_type": item.content_type,
                    "duration_hint": item.duration_hint,
                    "view_count_hint": item.view_count_hint,
                    "age_hint": item.age_hint,
                    "artifact_path": str(artifact_path),
                },
            )
        self.write_run_artifact(
            snapshot.snapshot_id,
            "home",
            {
                "type": "home",
                "artifact_path": str(artifact_path),
                "captured_at": snapshot.captured_at,
                "collection_status": snapshot.collection_status,
                "item_count": snapshot.recommendation_count,
                "snapshot_id": snapshot.snapshot_id,
            },
        )

    def record_history_snapshot(
        self,
        snapshot: HistorySnapshot,
        *,
        artifact_path: Path,
        run_id: str | None = None,
    ) -> None:
        self._upsert_videos(snapshot.history_items, source="history")
        existing_history_keys = self._event_keys(
            self.watch_history_events_path,
            video_id_field="video_id",
            url_field="url",
        )
        for item in snapshot.history_items:
            item_key = item.video_id or item.url
            if item_key in existing_history_keys:
                continue
            self._append_jsonl(
                self.watch_history_events_path,
                {
                    "event_type": "watch_history",
                    "run_id": run_id,
                    "history_snapshot_id": snapshot.history_snapshot_id,
                    "observed_at": snapshot.captured_at,
                    "source": snapshot.source,
                    "video_id": item.video_id,
                    "url": item.url,
                    "title": item.title,
                    "channel_name": item.channel_name,
                    "watched_at_hint": item.watched_at_hint,
                    "recency_bucket": item.recency_bucket,
                    "display_position": item.display_position,
                    "artifact_path": str(artifact_path),
                },
            )
        self.write_run_artifact(
            snapshot.history_snapshot_id,
            "history",
            {
                "type": "history",
                "artifact_path": str(artifact_path),
                "captured_at": snapshot.captured_at,
                "collection_status": snapshot.collection_status,
                "item_count": snapshot.history_item_count,
                "history_snapshot_id": snapshot.history_snapshot_id,
            },
        )

    def read_videos(self) -> dict[str, dict[str, Any]]:
        return json.loads(self.videos_path.read_text(encoding="utf-8"))

    def read_events(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def write_run_artifact(self, artifact_id: str, artifact_type: str, payload: Any) -> Path:
        target = self.runs_dir / f"{artifact_type}-{artifact_id}.json"
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return target

    def _upsert_videos(
        self,
        items: list[RecommendationItem] | list[HistoryItem],
        *,
        source: str,
    ) -> None:
        videos = self.read_videos()
        now = utc_now()
        for item in items:
            key = item.video_id or item.url
            if not key:
                continue
            current = videos.get(key, {})
            videos[key] = {
                **current,
                "video_id": item.video_id,
                "url": item.url,
                "title": item.title,
                "channel_name": item.channel_name,
                "first_seen_at": current.get("first_seen_at", now),
                "last_seen_at": now,
                "last_seen_source": source,
            }
        self.videos_path.write_text(
            json.dumps(videos, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _write_once(self, path: Path, content: str) -> None:
        if not path.exists():
            path.write_text(content, encoding="utf-8")

    def _write_json_if_missing(self, path: Path, payload: Any) -> None:
        if not path.exists():
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def _event_keys(self, path: Path, *, video_id_field: str, url_field: str) -> set[str]:
        keys: set[str] = set()
        for event in self.read_events(path):
            key = event.get(video_id_field) or event.get(url_field)
            if key:
                keys.add(str(key))
        return keys
