# Contract: Snapshot and Evidence Artifacts

These artifact contracts are shared data seams across the system. They do not imply that each artifact type needs its own top-level implementation module.

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

> Selection and enrichment artifacts are no longer produced by the Python package. Enrichment selection, metadata, and transcripts are handled by Hermes at curation time (reading the wiki raw/index evidence and using the bundled `youtube-content` skill), not written as Python artifacts.

## Failure and Partial-Success Rules

- Every artifact-producing step must emit a clear status value (`collection_status`).
- Missing or partial collection must be represented explicitly rather than omitted silently.
- A partial-success run may still record the snapshot it captured if the remaining evidence is sufficient for downstream curation.
