# Contract: Curator CLI Entry Points

These commands are internal operator-facing interfaces. Exact flag names may evolve, but the contract below defines the required behavior and output expectations.

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

## `enrich-videos`

**Purpose**: Enrich collected video items with metadata, descriptions, and transcripts when available.

**Inputs**:
- Set of collected video identifiers or unresolved canonical videos

**Behavior**:
- Fetches metadata enrichment for target videos
- Attaches descriptions when available
- Attaches transcripts when available
- Records partial failures without aborting the entire batch

**Outputs**:
- `run_status`
- `videos_processed`
- `metadata_enriched_count`
- `transcript_enriched_count`
- `warnings[]`

## `run-curator`

**Purpose**: Execute the Hermes-driven curation workflow for the newest available inputs.

**Inputs**:
- Latest recommendation snapshot
- Latest history snapshot if available
- Relevant prior memory and historical artifacts

**Behavior**:
- Determines whether meaningful change justifies curation
- Produces either a skip decision or a digest
- Generates summaries, ranked recommendations, and idea proposals
- Produces approval-gated memory proposals

**Outputs**:
- `run_status`
- `skip_reason` when skipped
- `digest_id` when curation occurs
- `report_artifact_path`
- `memory_proposal_count`
- `warnings[]`
