from __future__ import annotations

import json
from pathlib import Path

from hermes_youtube_curator.models import HistoryItem, HistorySnapshot


class HistoryCollector:
    def collect(self, fixture_path: Path | None) -> HistorySnapshot:
        if not fixture_path:
            return HistorySnapshot(
                history_items=[],
                collection_status="partial",
                warnings=["History fixture not configured; continuing without history evidence."],
            )

        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        items = [HistoryItem(**item) for item in payload["history_items"]]
        return HistorySnapshot(
            history_items=items,
            collection_status=payload.get("collection_status", "success"),
            warnings=payload.get("warnings", []),
        )
