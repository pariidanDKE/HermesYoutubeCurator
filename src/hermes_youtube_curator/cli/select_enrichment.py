from __future__ import annotations

from hermes_youtube_curator.cli.guards import finalize_result
from hermes_youtube_curator.models import CollectionRun
from hermes_youtube_curator.pipeline.context import AppContext


def run_select_enrichment(
    context: AppContext,
    run: CollectionRun | None = None,
):
    run = run or CollectionRun(trigger_type="manual", run_status="running")
    snapshot = context.home_collector.collect(context.settings)
    history = context.history_collector.collect(context.settings.history_fixture)
    selection = context.selection.select(
        run.run_id,
        snapshot,
        history,
        max_enrichment=context.settings.max_enrichment,
    )
    artifact = context.artifacts.write("selections", selection.selection_id, selection)
    return finalize_result(
        {
            "run_status": "success",
            "selection_id": selection.selection_id,
            "selected_video_ids": selection.selected_video_ids,
            "artifact_path": str(artifact),
            "warnings": [],
        },
        required_keys={
            "run_status",
            "selection_id",
            "selected_video_ids",
            "artifact_path",
            "warnings",
        },
    ).payload, selection
