# Contract: Curator CLI Entry Points

These commands are internal operator-facing interfaces. They are deterministic program entrypoints, not freeform agent tools. Exact flag names may evolve, but the contract below defines the required behavior and output expectations.

These CLI entrypoints are orchestration surfaces, not prescriptions for one top-level package per command. They may compose a smaller number of deeper modules internally.

The Python CLI is intentionally limited to deterministic evidence collection (`refresh-home`, `refresh-history`). Enrichment selection, metadata/transcript enrichment, ranking, and digest generation are owned by Hermes at curation time (reading the wiki raw/index evidence and using the bundled `youtube-content` skill for transcripts), so they are no longer Python CLI commands.

## `refresh-home`

**Purpose**: Capture the signed-in YouTube homepage recommendation feed.

**Inputs**:
- Access to a valid signed-in browser session
- Output location or run context

**Behavior**:
- Opens the supported YouTube home feed context
- Collects visible recommendation items and directly available metadata
- Writes a structured recommendation snapshot artifact
- Returns a machine-readable run summary

**Outputs**:
- `run_status`
- `snapshot_id`
- `recommendation_count`
- `artifact_path`
- `warnings[]`

## `refresh-history`

**Purpose**: Capture recently watched videos and recency hints from YouTube history.

**Inputs**:
- Access to a valid signed-in browser session
- Output location or run context

**Behavior**:
- Opens the supported history context
- Collects recent watch entries and watched-recently signals
- Writes a structured history snapshot artifact
- Returns a machine-readable run summary

**Outputs**:
- `run_status`
- `history_snapshot_id`
- `history_item_count`
- `artifact_path`
- `warnings[]`
