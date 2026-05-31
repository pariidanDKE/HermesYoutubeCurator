from __future__ import annotations

from hermes_youtube_curator.cli.guards import finalize_result
from hermes_youtube_curator.pipeline.context import AppContext


def run_refresh_history(context: AppContext) -> dict[str, object]:
    snapshot = context.history_collector.collect(context.settings)
    artifact = context.artifacts.write("history", snapshot.history_snapshot_id, snapshot)
    return finalize_result(
        {
            "run_status": "success" if snapshot.collection_status == "success" else "partial",
            "history_snapshot_id": snapshot.history_snapshot_id,
            "history_item_count": snapshot.history_item_count,
            "artifact_path": str(artifact),
            "warnings": snapshot.warnings,
        },
        required_keys={
            "run_status",
            "history_snapshot_id",
            "history_item_count",
            "artifact_path",
            "warnings",
        },
    ).payload
