# Data Model: YouTube Curator

These entities describe durable records and artifacts. They are not a one-to-one prescription for top-level modules. Multiple entities can and should live behind the same deep module when they share a stable responsibility or dependency boundary.

**Ownership note**: The Python package owns only the two collection snapshots and their items, persisted as raw JSON artifacts and into the wiki raw/index layer. Enrichment selection, enriched video detail, the curation digest, idea/memory proposals, and the delivery outcome are produced and owned by Hermes at curation time. They are described here as product entities, not Python-persisted records, and the earlier `Collection Run`, `Enrichment Selection`, `Video Content Detail`, and `Canonical Video` records were removed from the Python package.

## Recommendation Snapshot

**Purpose**: Captures the state of the signed-in YouTube home feed for a single collection run.

**Fields**:
- `snapshot_id`: stable unique identifier
- `captured_at`: timestamp of the collection run
- `source`: fixed value identifying the homepage source
- `session_state`: whether the signed-in session was valid, partial, or failed
- `collection_status`: success or partial completeness marker
- `recommendation_count`: number of items captured
- `warnings`: collection warnings recorded without aborting the run

**Relationships**:
- Has many `Recommendation Item`
- Captured during one run (a Hermes cron firing); the full snapshot is also written as a raw JSON artifact

**Validation Rules**:
- `captured_at` is required
- `source` must identify a supported collection source
- `recommendation_count` must be zero or greater

## Recent Watch History Snapshot

**Purpose**: Captures recently watched videos and recency signals from the YouTube history view for a single collection run.

**Fields**:
- `history_snapshot_id`: stable unique identifier
- `captured_at`: timestamp of the collection run
- `source`: fixed value identifying the history source
- `collection_status`: success or partial completeness marker
- `history_item_count`: number of items captured
- `warnings`: collection warnings recorded without aborting the run

**Relationships**:
- Has many `History Item`
- Captured during one run (a Hermes cron firing); the full snapshot is also written as a raw JSON artifact

**Validation Rules**:
- `captured_at` is required
- `history_item_count` must be zero or greater

## Recommendation Item

**Purpose**: Represents one recommended video found on the homepage feed.

**Fields**:
- `video_id`: platform video identifier when available
- `title`: displayed video title
- `channel_name`: displayed creator/channel name
- `url`: canonical or collected watch URL
- `description_excerpt`: directly available description text, if any
- `thumbnail_url`: optional thumbnail reference
- `content_type`: collected item type when distinguishable (e.g. video)
- `duration_hint`, `view_count_hint`, `age_hint`: directly visible metadata hints when present
- `display_position`: relative ordering within the snapshot
- `section_label`: optional feed grouping label
- `metadata_status`: completeness marker for collected metadata

**Relationships**:
- Belongs to one `Recommendation Snapshot`
- Upserted into the wiki `raw/curator/videos.json` index, keyed by `video_id` or `url`

**Validation Rules**:
- At least one of `video_id` or `url` must exist
- `display_position` must be positive if present

## History Item

**Purpose**: Represents one recently watched video used as a recency signal.

**Fields**:
- `video_id`: platform video identifier when available
- `title`: displayed video title
- `channel_name`: displayed creator/channel name
- `url`: canonical or collected watch URL
- `watched_at_hint`: human-readable or parsed recency indicator captured from the page
- `recency_bucket`: normalized recentness category such as immediate, same-day, or older
- `display_position`: relative ordering in the history list

**Relationships**:
- Belongs to one `Recent Watch History Snapshot`
- Upserted into the wiki `raw/curator/videos.json` index, keyed by `video_id` or `url`

**Validation Rules**:
- At least one of `video_id` or `url` must exist
- `recency_bucket` must be one of the supported categories if populated

## Curation Digest *(Hermes-owned)*

**Purpose**: User-facing output summarizing the current run. Produced by Hermes at curation time from the wiki evidence, not persisted as a Python record.

**Fields**:
- `summary_text`: top-level digest narrative
- `watch_list`: recommended items to watch now
- `save_list`: recommended items to save for later
- `skip_list`: items explicitly deprioritized
- `history_influence_notes`: explanation of how recent viewing influenced the ranking
- `confidence_level`: qualitative confidence label

**Relationships**:
- Produced for one run
- May contain many `Idea Proposal`
- May contain many `Preference Memory Proposal`

**Validation Rules**:
- At least one of `watch_list`, `save_list`, `skip_list`, or `summary_text` must be populated

## Idea Proposal *(Hermes-owned)*

**Purpose**: An idea, research direction, or script prompt produced from curated material.

**Fields**:
- `idea_type`: video idea, script angle, research direction, hook, or theme
- `title`: concise label
- `description`: generated explanation

**Relationships**:
- Belongs to one `Curation Digest`

## Preference Memory Proposal *(Hermes-owned)*

**Purpose**: A suggested long-term memory update pending approval.

**Fields**:
- `title`: concise label for the proposed change
- `description`: user-facing recommendation and supporting justification
- `approval_state`: pending, approved, or rejected

**Relationships**:
- Belongs to one `Curation Digest`

**Validation Rules**:
- `approval_state` defaults to `pending`
- A durable preference change requires explicit approval before it is applied

## Hermes Delivery Outcome *(Hermes-owned)*

**Purpose**: The Hermes-owned outcome of delivering a digest to Telegram, surfaced through cron/operator output rather than Python persistence.

**Fields**:
- `delivery_status`: `sent`, `failed`, `skipped`, or unknown from operator output
- `failure_reason`: explanation when delivery fails
- `platform_message_id`: platform-specific message identifier when available
- `attempted_at`: timestamp of the delivery attempt

**Relationships**:
- Produced by Hermes cron/manual operation outside the Python package

**Validation Rules**:
- `delivery_status` must be one of the supported outcomes when reported

## Suggested Module Ownership

- `youtube` owns collection-facing records: `Recommendation Snapshot`, `Recent Watch History Snapshot`, `Recommendation Item`, and `History Item`.
- `persistence` owns raw artifact storage and the wiki raw/index layer (`videos.json`, the append-only event logs, and run manifests) without becoming the place where business decisions are made.
- `pipeline` coordinates deterministic evidence collection across a run but stays thin; entity names do not imply separate top-level stage modules.
- Hermes (at curation time) owns enrichment selection, transcript/metadata enrichment, the `Curation Digest`, `Idea Proposal`, `Preference Memory Proposal`, Telegram delivery, and the delivery outcome. These are not Python-persisted records.
