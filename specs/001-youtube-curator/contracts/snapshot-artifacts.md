# Contract: Snapshot and Report Artifacts

## Recommendation Snapshot Artifact

**Required top-level fields**:
- `snapshot_id`
- `captured_at`
- `source`
- `recommendations[]`
- `collection_status`

**Per-item minimum fields**:
- `title`
- `channel_name`
- `url` or `video_id`

**Optional per-item fields**:
- `description_excerpt`
- `section_label`
- `thumbnail_url`
- `display_position`

## History Snapshot Artifact

**Required top-level fields**:
- `history_snapshot_id`
- `captured_at`
- `source`
- `history_items[]`
- `collection_status`

**Per-item minimum fields**:
- `title`
- `channel_name`
- `url` or `video_id`
- `watched_at_hint`

**Optional per-item fields**:
- `recency_bucket`
- `display_position`

## Enriched Video Artifact

**Required fields**:
- `video_id` or equivalent canonical key
- `metadata_status`
- `enriched_at`

**Optional fields**:
- `description_text`
- `transcript_status`
- `transcript_text`
- `published_at`
- `duration`

## Curation Digest Artifact

**Required fields**:
- `digest_id`
- `generated_at`
- `summary_text` or explicit skip decision
- `confidence_level`

**Recommended fields**:
- `watch_list[]`
- `save_list[]`
- `skip_list[]`
- `history_influence_notes`
- `video_summaries[]`
- `idea_proposals[]`
- `memory_proposals[]`

## Failure and Partial-Success Rules

- Every artifact-producing step must emit a clear status value.
- Missing transcript or metadata enrichment must be represented explicitly rather than omitted silently.
- A partial-success run may still produce downstream artifacts if the remaining evidence is sufficient for curation.
