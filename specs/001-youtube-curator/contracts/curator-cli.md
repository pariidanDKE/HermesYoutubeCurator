# Contract: Curator CLI Entry Points

These commands are internal operator-facing interfaces. They are deterministic program entrypoints, not freeform agent tools. Exact flag names may evolve, but the contract below defines the required behavior and output expectations.

These CLI entrypoints are orchestration surfaces, not prescriptions for one top-level package per command. They may compose a smaller number of deeper modules internally.

## `morning-run`

**Purpose**: Execute the full scheduled pipeline from collection through curation.

**Inputs**:
- Access to configured runtime dependencies
- Access to a valid signed-in browser session
- Active scheduler or equivalent manual invocation context

**Behavior**:
- Starts a new run record
- Executes homepage and history collection
- Executes enrichment selection
- Executes deep enrichment for selected candidates
- Executes curation and report generation
- Returns a machine-readable run summary

**Outputs**:
- `run_status`
- `run_id`
- `digest_id` when curation occurs
- `report_artifact_path`
- `warnings[]`

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

## `select-enrichment`

**Purpose**: Produce a bounded selection of video IDs that deserve deeper enrichment.

**Inputs**:
- Latest recommendation snapshot
- Latest history snapshot if available
- Relevant preference memory and historical artifacts

**Behavior**:
- Evaluates collected candidates against current context
- Decides `enrich_now`, `defer`, or `skip` for each relevant candidate
- Records reasons for the selection decisions
- Writes a structured enrichment-selection artifact

**Outputs**:
- `run_status`
- `selection_id`
- `selected_video_ids[]`
- `artifact_path`
- `warnings[]`

## `enrich-videos`

**Purpose**: Enrich selected video items with metadata, descriptions, and transcripts when available.

**Inputs**:
- Set of selected video identifiers or unresolved canonical videos

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
- Latest enrichment-selection artifact
- Enriched video details for selected candidates
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
