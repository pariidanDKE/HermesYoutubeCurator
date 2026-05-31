from __future__ import annotations

from hermes_youtube_curator.cli.guards import finalize_result
from hermes_youtube_curator.pipeline.context import AppContext


def run_refresh_home(context: AppContext) -> dict[str, object]:
    snapshot = context.home_collector.collect(context.settings)
    artifact = context.artifacts.write("snapshots", snapshot.snapshot_id, snapshot)
    context.wiki.record_home_snapshot(snapshot, artifact_path=artifact)
    return finalize_result(
        {
            "run_status": "success" if snapshot.collection_status == "success" else "partial",
            "snapshot_id": snapshot.snapshot_id,
            "recommendation_count": snapshot.recommendation_count,
            "artifact_path": str(artifact),
            "warnings": snapshot.warnings,
        },
        required_keys={
            "run_status",
            "snapshot_id",
            "recommendation_count",
            "artifact_path",
            "warnings",
        },
    ).payload
