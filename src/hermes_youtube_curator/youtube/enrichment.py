from __future__ import annotations

import json
from pathlib import Path

from hermes_youtube_curator.models import VideoContentDetail


class EnrichmentService:
    def __init__(self, fixture_path: Path | None) -> None:
        self.fixture_map = self._load_fixture(fixture_path)

    def _load_fixture(self, fixture_path: Path | None) -> dict[str, dict[str, str]]:
        if not fixture_path:
            return {}
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        return {item["video_id"]: item for item in payload["videos"]}

    def enrich(self, video_ids: list[str]) -> tuple[list[VideoContentDetail], list[str]]:
        results: list[VideoContentDetail] = []
        warnings: list[str] = []
        for video_id in video_ids:
            item = self.fixture_map.get(video_id)
            if not item:
                results.append(
                    VideoContentDetail(
                        video_id=video_id,
                        metadata_status="missing",
                        transcript_status="unavailable",
                    )
                )
                warnings.append(f"No enrichment fixture for {video_id}.")
                continue
            results.append(VideoContentDetail(**item))
        return results, warnings
