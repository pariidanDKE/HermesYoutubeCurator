# Feature Specification: YouTube Curator

**Feature Branch**: `001-youtube-curator`  
**Created**: 2026-05-25  
**Status**: Draft  
**Input**: User description: "@/home/dan-parii/Documents/HermesYoutubeCurator/specs/raw-spec.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review curated recommendations (Priority: P1)

As the owner of the curator, I want the system to collect my current YouTube recommendations together with recent watch-history signals into a structured snapshot and deliver a ranked digest to my Telegram inbox so I can quickly decide what is worth watching, saving, or ignoring.

**Why this priority**: This is the core value of the feature. Without reliable collection, curation, and delivery of recommendations, the rest of the system has no useful user-facing output.

**Independent Test**: Can be fully tested by running a scheduled collection cycle against a signed-in YouTube feed and recent watch history and confirming that the user receives a delivered digest with ranked recommendations and clear watch, save, or skip guidance informed by both sources.

**Acceptance Scenarios**:

1. **Given** the user has an accessible signed-in YouTube home feed, **When** the system performs a collection cycle, **Then** it records a structured snapshot of recommendations and their available metadata.
2. **Given** the user has accessible recent watch history, **When** the system performs a collection cycle, **Then** it records recently watched videos together with recency information that can inform current recommendation relevance.
3. **Given** a new structured snapshot is available, **When** the curation workflow runs, **Then** the user receives a delivered ranked digest that highlights notable recommendations and explains why they matter in light of both current recommendations and recent viewing behavior.

---

### User Story 2 - Selectively enrich the most promising videos (Priority: P2)

As the owner of the curator, I want the system to gather richer video metadata such as descriptions and, when available, transcripts for the most promising recommendations so it can produce actual video summaries along with ideas and research directions without spending effort equally on every candidate.

**Why this priority**: The curator becomes materially more useful when it converts recommendations into actionable outputs and uses contextual judgment to spend enrichment effort where it matters most.

**Independent Test**: Can be fully tested by providing a structured snapshot containing multiple recommended videos plus recent-history and memory context, then confirming that the system selects a subset for deeper enrichment and produces summary notes, idea prompts, and suggested research directions derived from that material.

**Acceptance Scenarios**:

1. **Given** a structured snapshot with multiple candidate recommendations, recent-history context, and preference memory, **When** the enrichment-selection workflow runs, **Then** it prioritizes the video IDs most worth deeper enrichment and records why they were chosen.
2. **Given** selected recommendations have available descriptions or transcripts, **When** the curation workflow analyzes the enriched results, **Then** it produces concise summaries of important videos and recurring themes grounded in that content.
3. **Given** curated recommendations reveal promising topics or arguments, **When** the curation workflow completes, **Then** it proposes video ideas, script directions, or research questions linked to that content.

---

### User Story 3 - Build long-term interest memory with guardrails (Priority: P3)

As the owner of the curator, I want the system to detect recurring interests over time and suggest memory updates under strict controls so that the curator improves without becoming an unrestricted autonomous agent.

**Why this priority**: Long-term learning increases strategic value, but it must remain constrained and reviewable to avoid unsafe or misleading behavior.

**Independent Test**: Can be fully tested by processing multiple snapshots across separate runs and confirming that the system identifies repeated themes, proposes preference updates, and does not perform unrestricted browsing or account actions.

**Acceptance Scenarios**:

1. **Given** the system has access to multiple past snapshots, **When** it compares them over time, **Then** it identifies recurring themes, shifting interests, or recommendation drift.
2. **Given** the system believes long-term preferences should be updated, **When** it prepares a memory update, **Then** it presents the update as a proposal for approval rather than silently changing long-term memory.
3. **Given** the curation workflow is operating normally, **When** it processes recommendations, **Then** it stays within read-only, structured, and restricted operating boundaries.

### Edge Cases

- What happens when the signed-in YouTube session is unavailable, expired, or partially loaded during a scheduled collection cycle?
- What happens when recommendation data is available but recent watch history cannot be accessed, or vice versa?
- How does the system handle recommendations that are missing metadata, descriptions, or transcripts?
- What happens when a snapshot contains mostly repeated recommendations and very little materially new content?
- How does the system treat videos that were watched very recently so it does not over-recommend near-duplicates or already-satisfied interests?
- How does the system respond when the curation output contains conflicting signals about what the user will value?
- What happens when the Telegram delivery path is unavailable or disconnected at delivery time?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST collect the user's current signed-in YouTube home feed into a structured snapshot during a scheduled or manually triggered run.
- **FR-002**: The system MUST collect the user's recent watch history, including the identity of recently watched videos and how recently they were watched, during the same run when that source is accessible.
- **FR-003**: The system MUST capture available metadata needed for curation across both recommendations and recent watch history, including video identity, creator identity, visible context, and other directly accessible descriptive details.
- **FR-004**: The system MUST analyze each collected snapshot to rank recommendations by likely relevance and highlight high-signal content for the user.
- **FR-005**: The system MUST use recent watch history as an input signal when judging what the user is likely to want to watch next.
- **FR-006**: The system MUST account for watch recency so that very recently watched topics or videos can influence prioritization, repetition avoidance, and recommendation framing.
- **FR-007**: The system MUST generate a user-facing digest that identifies watch, save, or skip candidates and explains the reasoning in plain language.
- **FR-008**: The system MUST choose which recommended videos deserve deeper enrichment using current recommendation context, recent watch history, and persistent preference memory.
- **FR-009**: The system MUST retrieve or attach richer content sources for selected recommended videos when available, including descriptions and transcripts, so they can be used during curation.
- **FR-010**: The system MUST generate concise video summaries, topic groupings, and recurring-theme observations from curated recommendations using the richest available source material.
- **FR-011**: The system MUST propose creative outputs derived from curated recommendations, including idea prompts, script directions, or research questions where relevant.
- **FR-012**: The system MUST connect current recommendations to the user's ongoing interests, projects, previously observed themes, or very recent viewing behavior when enough context exists.
- **FR-013**: The system MUST maintain a history of snapshots and curation outputs so that recommendations and themes can be analyzed across time.
- **FR-014**: The system MUST identify recurring interests, theme drift, or recommendation drift across multiple runs and present those findings in user-understandable terms.
- **FR-015**: The system MUST treat long-term preference or memory changes as proposals that require user approval before they are applied.
- **FR-016**: The system MUST operate within constrained guardrails that prevent unrestricted browsing, account interaction, arbitrary filesystem changes, and unrestricted tool use during normal curation workflows.
- **FR-017**: The system MUST remain read-only with respect to the user's YouTube account during collection and curation activities.
- **FR-018**: The system MUST handle missing, incomplete, or inconsistent recommendation data, history data, descriptions, or transcripts without failing the entire run.
- **FR-019**: The system MUST record when a run fails or encounters partial evidence so the user can review what happened.
- **FR-020**: The system MUST use a deterministic configured scheduler for recurring runs rather than asking the agent to decide when to wake up.
- **FR-021**: The system MUST deliver completed digests through a Hermes Telegram messaging channel in v1.
- **FR-022**: The system MUST surface delivery success or failure through Hermes cron/operator output for each produced digest; the Python package MUST NOT own Telegram delivery state.
- **FR-023**: The system SHOULD leave room for a future WhatsApp delivery target as a stretch goal without making it part of the v1 delivery contract.

### Key Entities *(include if feature involves data)*

- **Recommendation Snapshot**: A time-bounded record of the user's visible YouTube recommendations and their accessible metadata at the moment of collection.
- **Recent Watch History Snapshot**: A time-bounded record of recently watched videos and how recently the user watched them.
- **Recommendation Item**: An individual recommended video entry with descriptive attributes such as title, creator, visible context, and supporting metadata used during curation.
- **History Item**: An individual recently watched video entry with descriptive attributes and recency information used to infer current interests and avoid stale or redundant suggestions.
- **Enrichment Selection**: A recorded decision about which candidate videos should receive deeper enrichment, which should be deferred, and why.
- **Video Content Detail**: Supplemental source material for a recommended video, such as its description or transcript, used to produce richer summaries when available.
- **Curation Digest**: A structured user-facing output that ranks recommendations, groups themes, and suggests watch, save, or skip actions.
- **Hermes Delivery Outcome**: The Hermes-owned result of sending a digest to the configured Telegram destination, surfaced through cron/operator output rather than Python persistence.
- **Idea Proposal**: A generated creative or research suggestion derived from curated recommendations, such as a video idea, script angle, or follow-up question.
- **Preference Memory Proposal**: A suggested update to the user's long-term interests or preferences that remains pending until the user approves it.
- **Theme History**: A longitudinal record of recurring topics, changing interests, and recommendation patterns observed across multiple runs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In at least 95% of successful collection runs, the system produces a structured snapshot and a curation result without manual intervention.
- **SC-002**: In at least 90% of successful runs where recent watch history is accessible, the system incorporates recency-aware history signals into recommendation ranking and explanation output.
- **SC-003**: In user testing across 20 consecutive runs, the user can review each delivered digest and decide what to watch, save, or ignore in under 5 minutes per run.
- **SC-004**: At least 80% of digests contain at least one recommendation the user judges to be worth watching, saving, or researching further.
- **SC-005**: When descriptions or transcripts are available for selected recommended videos, at least 80% of generated video summaries are judged by the user to be accurate and useful.
- **SC-006**: After 4 weeks of use, the system identifies at least three recurring themes or interest patterns that the user confirms are accurate and useful.
- **SC-007**: 100% of long-term preference changes are presented as explicit proposals requiring approval before becoming part of persistent memory.
- **SC-008**: In validation runs designed to test guardrails, the system performs no unauthorized account actions and no unrestricted browsing outside the defined collection scope.
- **SC-009**: In at least 95% of runs that produce a digest, the system records a Telegram delivery outcome.

## Assumptions

- The curator is intended for a single owner using their own signed-in YouTube account rather than for multiple concurrent users.
- The initial release focuses on YouTube home feed recommendations and adjacent recommendation metadata, not full browsing across arbitrary sites.
- Recent watch history is a valuable signal for current intent, even if only a limited window of recent items is accessible per run.
- The system may rely on scheduled recurring runs as the default operating mode, with manual runs available for testing or on-demand use.
- Hermes cron is an acceptable and preferred scheduler when it is configured explicitly and kept deterministic.
- If transcripts or other richer metadata are unavailable for a recommendation, the system still produces the best possible curation output from the accessible information and clearly reflects the reduced evidence available for summary quality.
- The user values recommendation quality, idea generation, and long-term pattern detection more than real-time reaction speed.
- Approval is required before any long-term memory or preference change is persisted.
- Telegram is the primary v1 delivery channel because it is the simpler Hermes messaging path.

## Implementation Constraints

- **IC-001**: The implementation MUST keep one primary execution path for each collection, enrichment, and curation behavior rather than preserving fallback branches for the same work.
- **IC-002**: The implementation MUST stay close to a simple Python-centric stack built around API libraries, Playwright, local Markdown guidance, and minimal supporting infrastructure.
- **IC-003**: The implementation MUST favor a small number of deep modules organized around stable responsibilities such as orchestration, YouTube evidence gathering, curation, persistence, and delivery rather than assigning a top-level module to every pipeline stage.
- **IC-004**: The implementation MUST introduce ports only where the dependency shape justifies at least two adapters, typically production plus test, and MUST avoid single-adapter indirection.
- **IC-005**: Any tests added for this feature MUST focus on deep-module interfaces, contracts, or external adapters rather than private implementation details.
- **IC-006**: Before implementation of third-party integrations, the plan and research artifacts MUST record the current documentation or source references consulted for those integrations.
