from __future__ import annotations
# ruff: noqa: I001

from hermes_youtube_curator.cli.guards import finalize_result
from hermes_youtube_curator.cli.enrich_videos import run_enrich_videos
from hermes_youtube_curator.cli.refresh_history import run_refresh_history
from hermes_youtube_curator.cli.refresh_home import run_refresh_home
from hermes_youtube_curator.cli.run_curator import run_curator
from hermes_youtube_curator.cli.select_enrichment import run_select_enrichment
from hermes_youtube_curator.models import CollectionRun, utc_now
from hermes_youtube_curator.pipeline.context import AppContext


def run_morning_run(context: AppContext) -> dict[str, object]:
    run = CollectionRun(trigger_type=context.settings.scheduler, run_status="running")
    context.sqlite.save_run(run)

    home_result = run_refresh_home(context)
    history_result = run_refresh_history(context)
    selection_result, selection = run_select_enrichment(context, run)
    enrich_result, details = run_enrich_videos(context, selection)
    snapshot = context.home_collector.collect(context.settings)
    history = context.history_collector.collect(context.settings)
    curator_result, digest = run_curator(context, snapshot, history, selection, details)

    warnings = [
        *home_result.get("warnings", []),
        *history_result.get("warnings", []),
        *selection_result.get("warnings", []),
        *enrich_result.get("warnings", []),
        *curator_result.get("warnings", []),
    ]

    run.run_status = "success"
    results = [home_result, history_result, enrich_result, curator_result]
    if any(result["run_status"] in {"partial", "failed"} for result in results):
        run.run_status = "partial"
    if digest:
        message = context.curator.render_message(digest)
        delivery = context.delivery.deliver(digest, message)
        context.sqlite.save_delivery(delivery)
        if delivery.delivery_status != "delivered":
            warnings.append(delivery.failure_reason or "Delivery failed.")
            run.run_status = "partial"
        run.digest_id = digest.digest_id
        run.report_artifact_path = digest.artifact_path
    run.completed_at = utc_now()
    run.warnings = warnings
    context.sqlite.save_run(run)

    return finalize_result(
        {
            "run_status": run.run_status,
            "run_id": run.run_id,
            "digest_id": run.digest_id,
            "report_artifact_path": run.report_artifact_path,
            "warnings": warnings,
        },
        required_keys={"run_status", "run_id", "digest_id", "report_artifact_path", "warnings"},
    ).payload
