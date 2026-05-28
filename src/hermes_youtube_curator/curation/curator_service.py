from __future__ import annotations

from hermes_youtube_curator.models import (
    CurationDigest,
    EnrichmentSelection,
    HistorySnapshot,
    IdeaProposal,
    MemoryProposal,
    RankedVideo,
    RecommendationItem,
    RecommendationSnapshot,
    VideoContentDetail,
)


class CuratorService:
    def curate(
        self,
        snapshot: RecommendationSnapshot,
        history: HistorySnapshot | None,
        selection: EnrichmentSelection | None,
        details: list[VideoContentDetail],
    ) -> tuple[CurationDigest | None, list[str], str | None]:
        warnings: list[str] = []
        if not snapshot.recommendations:
            return (
                None,
                ["No homepage recommendations available for curation."],
                "no_recommendations",
            )

        detail_map = {detail.video_id: detail for detail in details}
        selected_ids = set(selection.selected_video_ids) if selection else set()
        recent_ids = {item.video_id for item in history.history_items} if history else set()

        watch_list: list[RankedVideo] = []
        save_list: list[RankedVideo] = []
        skip_list: list[RankedVideo] = []

        for item in snapshot.recommendations:
            ranked = self._rank_item(
                item,
                detail_map.get(item.video_id or ""),
                selected_ids,
                recent_ids,
            )
            if item.video_id in recent_ids:
                skip_list.append(ranked)
            elif item.video_id in selected_ids or len(watch_list) < 2:
                watch_list.append(ranked)
            else:
                save_list.append(ranked)

        idea_proposals = [
            IdeaProposal(
                idea_type="research_direction",
                title=f"Follow-up from {watch_list[0].title}",
                description=(
                    "Review the top watch candidate and capture any reusable ideas or scripts."
                ),
            )
        ] if watch_list else []

        memory_proposals = [
            MemoryProposal(
                title="Emerging channel affinity",
                description=f"Consider remembering interest in {watch_list[0].channel_name}.",
            )
        ] if watch_list else []

        history_notes = []
        if recent_ids:
            history_notes.append(
                "Recently watched items were pushed toward skip to avoid near-duplicate picks."
            )
        if not history:
            warnings.append("History snapshot unavailable; ranking uses homepage evidence only.")

        digest = CurationDigest(
            summary_text=(
                "Top homepage candidates were ranked using recent-watch suppression "
                "and enriched context where available."
            ),
            confidence_level="medium" if history else "low",
            watch_list=watch_list[:3],
            save_list=save_list[:3],
            skip_list=skip_list[:3],
            history_influence_notes=history_notes,
            selection_influence_notes=[selection.selection_summary] if selection else [],
            idea_proposals=idea_proposals,
            memory_proposals=memory_proposals,
        )
        return digest, warnings, None

    def render_message(self, digest: CurationDigest) -> str:
        sections = [
            "YouTube Curator",
            "",
            digest.summary_text,
            "",
            "Watch now:",
        ]
        sections.extend(self._render_videos(digest.watch_list))
        sections.append("")
        sections.append("Save for later:")
        sections.extend(self._render_videos(digest.save_list))
        if digest.skip_list:
            sections.append("")
            sections.append("Skip for now:")
            sections.extend(self._render_videos(digest.skip_list))
        return "\n".join(sections)

    def _rank_item(
        self,
        item: RecommendationItem,
        detail: VideoContentDetail | None,
        selected_ids: set[str],
        recent_ids: set[str],
    ) -> RankedVideo:
        reason = (
            "Selected for enrichment."
            if item.video_id in selected_ids
            else "Visible on homepage."
        )
        if item.video_id in recent_ids:
            reason = "Seen in recent history; deprioritized."
        summary = (
            detail.description_text
            if detail and detail.description_text
            else item.description_excerpt
        )
        return RankedVideo(
            video_id=item.video_id,
            title=item.title,
            channel_name=item.channel_name,
            url=item.url,
            reason=reason,
            summary=summary,
        )

    def _render_videos(self, videos: list[RankedVideo]) -> list[str]:
        if not videos:
            return ["- None"]
        rendered = []
        for video in videos:
            suffix = f" ({video.url})" if video.url else ""
            rendered.append(f"- {video.title} by {video.channel_name}: {video.reason}{suffix}")
        return rendered
