# Data Model: YouTube Curator

These entities describe durable records and artifacts. They are not a one-to-one prescription for top-level modules. Multiple entities can and should live behind the same deep module when they share a stable responsibility or dependency boundary.

## Recommendation Snapshot

**Purpose**: Captures the state of the signed-in YouTube home feed for a single collection run.

**Fields**:
- `snapshot_id`: stable unique identifier
- `captured_at`: timestamp of the collection run
- `source`: fixed value identifying the homepage source
- `session_state`: whether the signed-in session was valid, partial, or failed
- `recommendation_count`: number of items captured
- `page_context`: optional contextual metadata such as locale or feed section labels
- `raw_artifact_path`: path to stored JSON snapshot

**Relationships**:
- Has many `Recommendation Item`
- Belongs to one `Collection Run`

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
- `history_item_count`: number of items captured
- `raw_artifact_path`: path to stored JSON snapshot

**Relationships**:
- Has many `History Item`
- Belongs to one `Collection Run`

**Validation Rules**:
- `captured_at` is required
- `history_item_count` must be zero or greater

## Recommendation Item

**Purpose**: Represents one recommended video found on the homepage feed.

**Fields**:
- `video_id`: platform video identifier when available
- `title`: displayed video title
- `channel_name`: displayed creator/channel name
- `channel_id`: channel identifier when available
- `url`: canonical or collected watch URL
- `description_excerpt`: directly available description text, if any
- `thumbnail_url`: optional thumbnail reference
- `display_position`: relative ordering within the snapshot
- `section_label`: optional feed grouping label
- `metadata_status`: completeness marker for collected metadata

**Relationships**:
- Belongs to one `Recommendation Snapshot`
- May have one `Enrichment Selection Item`
- May have one `Video Content Detail`
- May link to one `Canonical Video`

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
- May link to one `Canonical Video`

**Validation Rules**:
- At least one of `video_id` or `url` must exist
- `recency_bucket` must be one of the supported categories if populated

## Canonical Video

**Purpose**: Normalized cross-run record of a video used to deduplicate recommendation and history items.

**Fields**:
- `canonical_video_id`: internal unique identifier
- `video_id`: platform identifier
- `title`: best-known title
- `channel_name`: best-known creator name
- `channel_id`: creator identifier when available
- `published_at`: publication timestamp when available
- `duration`: normalized duration when available
- `metadata_last_refreshed_at`: last successful enrichment time

**Relationships**:
- Can be referenced by many `Recommendation Item`
- Can be referenced by many `History Item`
- Can be referenced by many `Enrichment Selection Item`
- Has zero or one `Video Content Detail`

**Validation Rules**:
- `video_id` should be unique when available

## Enrichment Selection

**Purpose**: Records one agent-assisted decision pass that prioritizes which candidate videos deserve deeper enrichment for a run.

**Fields**:
- `selection_id`: stable unique identifier
- `run_id`: parent run
- `selected_at`: timestamp of the decision
- `selection_model`: reasoning backend identifier used for the decision
- `selection_summary`: short explanation of overall prioritization
- `artifact_path`: path to the stored selection artifact when persisted separately

**Relationships**:
- Belongs to one `Collection Run`
- Has many `Enrichment Selection Item`

**Validation Rules**:
- `selected_at` is required

## Enrichment Selection Item

**Purpose**: Stores the decision for a single candidate video in the enrichment-selection pass.

**Fields**:
- `selection_item_id`: stable unique identifier
- `selection_id`: parent selection
- `canonical_video_id`: chosen canonical video reference when available
- `video_id`: platform video identifier when canonicalization is not complete
- `decision`: `enrich_now`, `defer`, or `skip`
- `priority_score`: normalized priority value when available
- `reason`: user-facing explanation grounded in current context

**Relationships**:
- Belongs to one `Enrichment Selection`
- May reference one `Canonical Video`

**Validation Rules**:
- `decision` must be one of the supported selection outcomes
- At least one of `canonical_video_id` or `video_id` must exist

## Video Content Detail

**Purpose**: Stores richer enrichment material used for summaries and curation.

**Fields**:
- `canonical_video_id`: reference to the normalized video
- `description_text`: full or enriched description text
- `transcript_status`: unavailable, partial, available, or failed
- `transcript_text`: transcript body when available
- `metadata_source_status`: summary of enrichment success
- `enriched_at`: timestamp of the last enrichment attempt

**Relationships**:
- Belongs to one `Canonical Video`

**Validation Rules**:
- At least one of `description_text` or `transcript_text` should exist for a successful enriched record

## Delivery Target

**Purpose**: Represents a configured Hermes messaging destination for curator output.

**Fields**:
- `delivery_target_id`: stable unique identifier
- `platform`: `telegram`
- `target_identifier`: platform-specific chat, user, or channel identifier
- `target_label`: human-readable label for the destination
- `is_primary`: whether this is the preferred delivery target
- `is_enabled`: whether delivery to this target is active

**Relationships**:
- Can be referenced by many `Delivery Record`

**Validation Rules**:
- `platform` must be `telegram` in v1
- Only one enabled target should be marked primary per curator profile

## Collection Run

**Purpose**: Top-level record of one scheduled or manual system run.

**Fields**:
- `run_id`: stable unique identifier
- `trigger_type`: scheduled or manual
- `started_at`: run start timestamp
- `completed_at`: run completion timestamp
- `run_status`: success, partial, skipped, or failed
- `skip_reason`: explanation when no curation is performed
- `failure_reason`: explanation when the run fails

**Relationships**:
- Has zero or one `Recommendation Snapshot`
- Has zero or one `Recent Watch History Snapshot`
- Has zero or one `Enrichment Selection`
- Has zero or one `Curation Digest`

**Validation Rules**:
- `started_at` is required
- `run_status` must be one of the supported lifecycle values

## Curation Digest

**Purpose**: User-facing output summarizing the current run.

**Fields**:
- `digest_id`: stable unique identifier
- `run_id`: parent run
- `generated_at`: creation timestamp
- `summary_text`: top-level digest narrative
- `watch_list`: recommended items to watch now
- `save_list`: recommended items to save for later
- `skip_list`: items explicitly deprioritized
- `history_influence_notes`: explanation of how recent viewing influenced the ranking
- `artifact_path`: path to stored report artifact
- `confidence_level`: qualitative confidence label

**Relationships**:
- Belongs to one `Collection Run`
- May reference many `Canonical Video`
- May contain many `Idea Proposal`
- May contain many `Preference Memory Proposal`
- May have many `Delivery Record`

**Validation Rules**:
- `generated_at` is required
- At least one of `watch_list`, `save_list`, `skip_list`, or `summary_text` must be populated unless the run is explicitly skipped

## Idea Proposal

**Purpose**: Stores an idea, research direction, or script prompt produced from curated material.

**Fields**:
- `idea_id`: stable unique identifier
- `digest_id`: parent digest
- `idea_type`: video idea, script angle, research direction, hook, or theme
- `title`: concise label
- `description`: generated explanation
- `supporting_videos`: related canonical videos

**Relationships**:
- Belongs to one `Curation Digest`

## Preference Memory Proposal

**Purpose**: Stores a suggested long-term memory update pending approval.

**Fields**:
- `proposal_id`: stable unique identifier
- `digest_id`: parent digest
- `proposed_at`: creation timestamp
- `proposal_text`: user-facing recommendation for memory change
- `justification`: supporting evidence from repeated patterns
- `status`: pending, approved, or rejected

**Relationships**:
- Belongs to one `Curation Digest`

**Validation Rules**:
- `status` defaults to `pending`
- Approved proposals must have an approval timestamp once implemented

## Delivery Record

**Purpose**: Records the outcome of attempting to deliver a digest to a messaging target.

**Fields**:
- `delivery_record_id`: stable unique identifier
- `digest_id`: parent digest
- `delivery_target_id`: target destination
- `attempted_at`: timestamp of the delivery attempt
- `delivery_status`: `sent`, `failed`, or `skipped`
- `failure_reason`: explanation when delivery fails
- `platform_message_id`: platform-specific message identifier when available

**Relationships**:
- Belongs to one `Curation Digest`
- Belongs to one `Delivery Target`

**Validation Rules**:
- `attempted_at` is required
- `delivery_status` must be one of the supported outcomes

## Suggested Module Ownership

- `youtube` owns collection-facing and enrichment-facing records such as `Recommendation Snapshot`, `Recent Watch History Snapshot`, `Recommendation Item`, `History Item`, `Canonical Video`, and `Video Content Detail`.
- `curation` owns `Enrichment Selection`, `Enrichment Selection Item`, `Curation Digest`, and any derived `Idea Proposal` or `Preference Memory Proposal` content.
- `delivery` owns delivery transport behavior and `Delivery Record` creation.
- `persistence` owns storage and retrieval of all of the above records without becoming the place where business decisions are made.
- `pipeline` coordinates these records across a run but should remain thin; their existence does not imply separate top-level stage modules.
