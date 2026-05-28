from __future__ import annotations

from hermes_youtube_curator.models import (
    EnrichmentDecision,
    EnrichmentSelection,
    HistorySnapshot,
    RecommendationSnapshot,
)


class SelectionService:
    def select(
        self,
        run_id: str,
        snapshot: RecommendationSnapshot,
        history: HistorySnapshot | None,
        *,
        max_enrichment: int,
    ) -> EnrichmentSelection:
        recent_ids = {item.video_id for item in history.history_items} if history else set()
        decisions: list[EnrichmentDecision] = []
        chosen = 0
        for item in sorted(
            snapshot.recommendations,
            key=lambda current: (current.display_position or 9999, current.title.lower()),
        ):
            if item.video_id in recent_ids:
                decisions.append(
                    EnrichmentDecision(
                        video_id=item.video_id,
                        decision="skip",
                        reason="Already watched recently; lower-value enrichment candidate.",
                        priority_score=0.1,
                    )
                )
                continue
            decision = "enrich_now" if chosen < max_enrichment else "defer"
            chosen += 1 if decision == "enrich_now" else 0
            decisions.append(
                EnrichmentDecision(
                    video_id=item.video_id,
                    decision=decision,
                    reason="High homepage priority and not present in recent history.",
                    priority_score=max(0.0, 1.0 - ((item.display_position or 1) - 1) * 0.1),
                )
            )
        return EnrichmentSelection(
            run_id=run_id,
            decisions=decisions,
            selection_summary="Prefer early homepage candidates that were not watched recently.",
        )
