from __future__ import annotations

from hermes_youtube_curator.cli.guards import finalize_result
from hermes_youtube_curator.models import (
    EnrichmentSelection,
    HistorySnapshot,
    RecommendationSnapshot,
    VideoContentDetail,
)
from hermes_youtube_curator.pipeline.context import AppContext


def run_curator(
    context: AppContext,
    snapshot: RecommendationSnapshot | None = None,
    history: HistorySnapshot | None = None,
    selection: EnrichmentSelection | None = None,
    details: list[VideoContentDetail] | None = None,
):
    snapshot = snapshot or context.home_collector.collect(context.settings)
    history = history or context.history_collector.collect(context.settings.history_fixture)
    details = details or []
    digest, warnings, skip_reason = context.curator.curate(snapshot, history, selection, details)
    if digest is None:
        return finalize_result(
            {
                "run_status": "skipped",
                "skip_reason": skip_reason,
                "digest_id": None,
                "report_artifact_path": None,
                "memory_proposal_count": 0,
                "warnings": warnings,
            },
            required_keys={
                "run_status",
                "skip_reason",
                "digest_id",
                "report_artifact_path",
                "memory_proposal_count",
                "warnings",
            },
        ).payload, None

    artifact = context.artifacts.write("digests", digest.digest_id, digest)
    digest.artifact_path = str(artifact)
    context.sqlite.save_digest(digest)
    return finalize_result(
        {
            "run_status": "success" if not warnings else "partial",
            "skip_reason": None,
            "digest_id": digest.digest_id,
            "report_artifact_path": str(artifact),
            "memory_proposal_count": len(digest.memory_proposals),
            "warnings": warnings,
        },
        required_keys={
            "run_status",
            "skip_reason",
            "digest_id",
            "report_artifact_path",
            "memory_proposal_count",
            "warnings",
        },
    ).payload, digest
