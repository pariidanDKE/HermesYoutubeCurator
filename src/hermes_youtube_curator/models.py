from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


def serialize(value: Any) -> Any:
    if is_dataclass(value):
        return {key: serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [serialize(item) for item in value]
    return value


@dataclass(slots=True)
class RecommendationItem:
    title: str
    channel_name: str
    url: str | None = None
    video_id: str | None = None
    description_excerpt: str | None = None
    section_label: str | None = None
    thumbnail_url: str | None = None
    content_type: str | None = None
    duration_hint: str | None = None
    view_count_hint: str | None = None
    age_hint: str | None = None
    display_position: int | None = None
    metadata_status: str = "available"

    def __post_init__(self) -> None:
        if not (self.url or self.video_id):
            raise ValueError("Recommendation item requires url or video_id")


@dataclass(slots=True)
class RecommendationSnapshot:
    recommendations: list[RecommendationItem]
    snapshot_id: str = field(default_factory=lambda: new_id("snapshot"))
    captured_at: str = field(default_factory=utc_now)
    source: str = "youtube_home"
    collection_status: str = "success"
    session_state: str = "valid"
    warnings: list[str] = field(default_factory=list)

    @property
    def recommendation_count(self) -> int:
        return len(self.recommendations)


@dataclass(slots=True)
class HistoryItem:
    title: str
    channel_name: str
    watched_at_hint: str
    url: str | None = None
    video_id: str | None = None
    recency_bucket: str | None = None
    display_position: int | None = None

    def __post_init__(self) -> None:
        if not (self.url or self.video_id):
            raise ValueError("History item requires url or video_id")


@dataclass(slots=True)
class HistorySnapshot:
    history_items: list[HistoryItem]
    history_snapshot_id: str = field(default_factory=lambda: new_id("history"))
    captured_at: str = field(default_factory=utc_now)
    source: str = "youtube_history"
    collection_status: str = "success"
    warnings: list[str] = field(default_factory=list)

    @property
    def history_item_count(self) -> int:
        return len(self.history_items)


@dataclass(slots=True)
class EnrichmentDecision:
    decision: str
    reason: str
    video_id: str | None = None
    canonical_video_id: str | None = None
    priority_score: float | None = None

    def __post_init__(self) -> None:
        if self.decision not in {"enrich_now", "defer", "skip"}:
            raise ValueError("Unsupported enrichment decision")
        if not (self.video_id or self.canonical_video_id):
            raise ValueError("Decision requires video_id or canonical_video_id")


@dataclass(slots=True)
class EnrichmentSelection:
    run_id: str
    decisions: list[EnrichmentDecision]
    selection_id: str = field(default_factory=lambda: new_id("selection"))
    selected_at: str = field(default_factory=utc_now)
    selection_status: str = "success"
    selection_summary: str = ""

    @property
    def selected_video_ids(self) -> list[str]:
        return [
            decision.video_id
            for decision in self.decisions
            if decision.decision == "enrich_now" and decision.video_id
        ]


@dataclass(slots=True)
class VideoContentDetail:
    video_id: str
    metadata_status: str
    enriched_at: str = field(default_factory=utc_now)
    description_text: str | None = None
    transcript_status: str | None = None
    transcript_text: str | None = None
    published_at: str | None = None
    duration: str | None = None
    channel_name: str | None = None
    title: str | None = None


@dataclass(slots=True)
class IdeaProposal:
    idea_type: str
    title: str
    description: str


@dataclass(slots=True)
class MemoryProposal:
    title: str
    description: str
    approval_state: str = "pending"


@dataclass(slots=True)
class RankedVideo:
    video_id: str | None
    title: str
    channel_name: str
    reason: str
    url: str | None = None
    summary: str | None = None


@dataclass(slots=True)
class CurationDigest:
    summary_text: str
    confidence_level: str
    watch_list: list[RankedVideo] = field(default_factory=list)
    save_list: list[RankedVideo] = field(default_factory=list)
    skip_list: list[RankedVideo] = field(default_factory=list)
    history_influence_notes: list[str] = field(default_factory=list)
    selection_influence_notes: list[str] = field(default_factory=list)
    idea_proposals: list[IdeaProposal] = field(default_factory=list)
    memory_proposals: list[MemoryProposal] = field(default_factory=list)
    generated_at: str = field(default_factory=utc_now)
    digest_id: str = field(default_factory=lambda: new_id("digest"))
    artifact_path: str | None = None


@dataclass(slots=True)
class DeliveryRecord:
    digest_id: str
    delivery_target: str
    delivery_status: str
    attempted_at: str = field(default_factory=utc_now)
    delivery_record_id: str = field(default_factory=lambda: new_id("delivery"))
    platform_message_id: str | None = None
    failure_reason: str | None = None


@dataclass(slots=True)
class CollectionRun:
    trigger_type: str
    run_status: str = "started"
    started_at: str = field(default_factory=utc_now)
    run_id: str = field(default_factory=lambda: new_id("run"))
    completed_at: str | None = None
    failure_reason: str | None = None
    warnings: list[str] = field(default_factory=list)
    digest_id: str | None = None
    report_artifact_path: str | None = None
