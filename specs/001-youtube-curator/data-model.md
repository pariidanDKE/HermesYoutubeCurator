# Data Model: YouTube Curator

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
- Has zero or one `Video Content Detail`

**Validation Rules**:
- `video_id` should be unique when available

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
- `confidence_level`: qualitative confidence label
- `artifact_path`: path to stored report artifact

**Relationships**:
- Belongs to one `Collection Run`
- May reference many `Canonical Video`
- May contain many `Idea Proposal`
- May contain many `Preference Memory Proposal`

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
