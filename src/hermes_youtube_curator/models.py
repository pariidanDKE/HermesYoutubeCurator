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



