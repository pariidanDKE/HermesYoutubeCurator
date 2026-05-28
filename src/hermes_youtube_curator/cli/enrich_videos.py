from __future__ import annotations

from hermes_youtube_curator.cli.guards import finalize_result
from hermes_youtube_curator.models import EnrichmentSelection
from hermes_youtube_curator.pipeline.context import AppContext


def run_enrich_videos(
    context: AppContext,
    selection: EnrichmentSelection,
):
    details, warnings = context.enrichment.enrich(selection.selected_video_ids)
    artifact_paths = [
        str(context.artifacts.write("enrichment", detail.video_id, detail)) for detail in details
    ]
    metadata_enriched_count = sum(
        1 for detail in details if detail.metadata_status == "available"
    )
    transcript_enriched_count = sum(
        1 for detail in details if detail.transcript_status == "available"
    )
    return finalize_result(
        {
            "run_status": "success" if not warnings else "partial",
            "videos_processed": len(details),
            "metadata_enriched_count": metadata_enriched_count,
            "transcript_enriched_count": transcript_enriched_count,
            "artifact_paths": artifact_paths,
            "warnings": warnings,
        },
        required_keys={
            "run_status",
            "videos_processed",
            "metadata_enriched_count",
            "transcript_enriched_count",
            "artifact_paths",
            "warnings",
        },
    ).payload, details
