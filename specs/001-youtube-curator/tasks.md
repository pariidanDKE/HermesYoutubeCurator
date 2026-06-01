# Tasks: YouTube Curator

**Input**: Design documents from `/specs/001-youtube-curator/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Include seam, contract, and adapter tests where they protect deterministic CLI behavior, Hermes integration boundaries, or persistence/delivery contracts.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Current Reality And Priority Order

The original task list created useful module seams, but some checked tasks were
completed only as fixture-backed or heuristic skeletons. Treat this section as
the source of truth for the next implementation pass.

### Current Reality

- `src/hermes_youtube_curator/youtube/home_collector.py` now has a real
  Playwright/CDP collection path that attaches to an already-open, logged-in
  Chrome YouTube tab launched by `scripts/launch_youtube_browser.py`.
- `src/hermes_youtube_curator/youtube/history_collector.py` now has a real
  Playwright/CDP collection path that reads YouTube history sections from the
  already-open, logged-in Chrome session.
- The fixture-only `youtube/enrichment.py` and the heuristic
  `curation/selection_service.py` were removed entirely (along with the
  `select-enrichment`/`enrich-videos` commands and the `curation/` package).
  Enrichment selection and enrichment are now owned by Hermes at curation time,
  using the bundled `youtube-content` skill for transcripts.
- Python CLI entrypoints are limited to deterministic evidence generation
  (`refresh-home`, `refresh-history`). Selection, enrichment, curation, and
  Telegram delivery are owned by Hermes cron/manual operation.

### Current Baseline And Next Priorities

- **Baseline**: Use the Hermes-compatible wiki raw/index layer as the current
  persistence path for videos, recommendation events, watch-history events, and
  run artifacts. SQLite and local Telegram delivery have been removed from the
  Python package.
- **P1**: Configure Hermes cron/manual operation to invoke the deterministic
  Python collection commands, read the wiki raw/index evidence, and perform
  agent-owned selection and curation.
- **P1**: Run and harden the full end-to-end integration path:
  launch logged-in browser, collect home/history, persist evidence, invoke
  Hermes, send Telegram, and record structured results.
- **P2**: Add real metadata/transcript enrichment after the base live
  home/history/Hermes/Telegram loop is proven.
- **P2**: Add long-term memory proposals and approval flow after the persistence
  decision is settled.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the Python project skeleton and capture the verified integration references needed before implementation.

- [X] T001 Create the application package and test directory skeleton in `src/hermes_youtube_curator/__init__.py`, `src/hermes_youtube_curator/cli/__init__.py`, `src/hermes_youtube_curator/pipeline/__init__.py`, `src/hermes_youtube_curator/youtube/__init__.py`, `src/hermes_youtube_curator/curation/__init__.py`, `src/hermes_youtube_curator/persistence/__init__.py`, `tests/contract/__init__.py`, and `tests/integration/__init__.py`
- [X] T002 Initialize the Python project metadata and runtime dependencies in `pyproject.toml`
- [X] T003 [P] Add environment and path configuration scaffolding in `src/hermes_youtube_curator/config/settings.py` and `.env.example`
- [X] T004 [P] Configure linting and pytest defaults in `pyproject.toml` and `tests/conftest.py`
- [X] T005 [P] Record current source-verified setup notes for Playwright, Hermes Agent, the bundled `youtube-content` skill, Hermes Telegram, YouTube Data API, `youtube-transcript-api`, and vLLM in `specs/001-youtube-curator/research.md`
- [X] T054 [P] Create the Hermes curator skill for Telegram message framing, section order, top/bottom guidance, and link inclusion policy in `skills/youtube-curator/SKILL.md`
- [X] T056 [P] Evaluate Hermes profile isolation, memory persistence, skill loading/mutation behavior, Hermes cron setup, and bundled `youtube-content` reuse for this project in `specs/001-youtube-curator/research.md` and `specs/001-youtube-curator/quickstart.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish shared models, artifact contracts, deterministic entrypoint scaffolding, and the core seams every story depends on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Define shared Pydantic-style domain models for runs, snapshots, selections, and optional Hermes digest validation in `src/hermes_youtube_curator/models.py`
- [X] T007 [P] Implement artifact serialization and JSON storage helpers in `src/hermes_youtube_curator/persistence/artifacts.py`
- [X] T008 [P] Removed SQLite schema/repository scaffolding after choosing the wiki raw/index layer as the only Python-owned persistence path
- [X] T008A [P0] Implement Hermes-compatible wiki raw/index persistence for videos, recommendation events, watch-history events, and run artifacts in `src/hermes_youtube_curator/persistence/wiki_store.py`
- [X] T009 [P] Implement structured logging and machine-readable result helpers for CLI commands in `src/hermes_youtube_curator/cli/results.py`
- [X] T010 [P] Implement the deterministic orchestration context and dependency wiring in `src/hermes_youtube_curator/pipeline/context.py`
- [X] T011 [P] Create CLI entrypoints for `refresh-home`, `refresh-history`, `select-enrichment`, and `enrich-videos` in `src/hermes_youtube_curator/cli/main.py`
- [X] T012 Implement command exit-code gates and result validation shared by all entrypoints in `src/hermes_youtube_curator/cli/guards.py`
- [X] T013 [P] Add contract tests for CLI machine-readable outputs defined in `specs/001-youtube-curator/contracts/curator-cli.md` in `tests/contract/test_cli_contracts.py`
- [X] T014 [P] Add artifact contract tests for snapshot, selection, and enrichment records from `specs/001-youtube-curator/contracts/snapshot-artifacts.md` in `tests/contract/test_artifact_contracts.py`
- [X] T015 Add integration tests for shared CLI guards and run-summary failure handling in `tests/integration/test_cli_guards.py`

**Checkpoint**: Foundation ready; deterministic commands and shared artifacts exist behind stable seams.

---

## Phase 3: User Story 1 - Review curated recommendations (Priority: P1) 🎯 MVP

**Goal**: Collect homepage and recent-history evidence, generate a Hermes-backed digest, and deterministically deliver it to Telegram.

**Independent Test**: Run homepage/history collection against fixture data or a configured environment, then validate the Hermes cron/manual flow produces and delivers the digest.

### Tests for User Story 1

- [X] T016 [P] [US1] Add integration tests for homepage collection and snapshot persistence in `tests/integration/test_refresh_home.py`
- [X] T017 [P] [US1] Add integration tests for history collection and recency signal persistence in `tests/integration/test_refresh_history.py`
- [X] T018 [P] [US1] Removed the local full-run integration path after Hermes cron became the owner of curation and delivery
- [X] T019 [P] [US1] Removed local Telegram delivery contract tests after Hermes cron became the delivery path

### Implementation for User Story 1

- [X] T020 [P0] [US1] Implement signed-in homepage collection with Playwright in `src/hermes_youtube_curator/youtube/home_collector.py` using the logged-in Chrome/CDP attach path
- [X] T021 [P0] [US1] Implement recent watch-history collection with Playwright in `src/hermes_youtube_curator/youtube/history_collector.py` using the logged-in Chrome/CDP attach path
- [X] T023 [US1] Implement the `refresh-home` command flow and machine-readable output in `src/hermes_youtube_curator/cli/refresh_home.py`
- [X] T024 [P0] [US1] Update the `refresh-history` command flow in `src/hermes_youtube_curator/cli/refresh_history.py` to use the real history collector instead of fixture input
- [X] T025 [P1] [US1] Removed the optional programmatic Hermes curator harness; Hermes cron/manual operation is the only digest path
- [ ] T026 [P1] [US1] Validate deterministic Telegram delivery through Hermes cron configuration and operator docs
- [ ] T027 [P1] [US1] Document and validate the Hermes cron/manual curator flow that runs deterministic Python collection commands, reads wiki raw/index evidence, and performs agent-owned curation
- [ ] T028 [P1] [US1] Validate the end-to-end Hermes cron job using `scripts/youtube_curator_refresh_for_hermes.sh`, wiki raw/index evidence, Hermes curation, and Hermes Telegram delivery
- [X] T029 [US1] Add operator documentation for the MVP command sequence and required env vars in `specs/001-youtube-curator/quickstart.md`

**Checkpoint**: User Story 1 is functional; the system can collect evidence, generate a digest, and record deterministic Telegram delivery.

---

## Phase 4: User Story 2 - Selectively enrich the most promising videos (Priority: P2)

**Goal**: Let Hermes choose which candidates deserve enrichment and use richer metadata/transcripts through direct Python adapters plus Hermes skill-guided transcript handling to improve the digest.

**Independent Test**: Run selection and enrichment against snapshot fixtures and confirm Hermes chooses a bounded subset, enrichment artifacts are produced, and the curator uses those richer artifacts in the final digest.

### Tests for User Story 2

- [X] T030 [P] [US2] Add integration tests for enrichment selection decisions and stored reasons in `tests/integration/test_select_enrichment.py`
- [X] T031 [P] [US2] Add integration tests for metadata/transcript enrichment partial-success behavior in `tests/integration/test_enrich_videos.py`
- [X] T032 [P] [US2] Add contract tests for bundled `youtube-content` transcript integration and enrichment artifact behavior in `tests/contract/test_enrichment_contracts.py`

### Implementation for User Story 2

- [X] T033 [P] [US2] Implement canonical video linking through the wiki raw/index persistence layer instead of a separate SQLite-backed video store
- [ ] T034 [P2] [US2] Implement deterministic metadata enrichment adapters and preferred bundled-skill transcript integration in `src/hermes_youtube_curator/youtube/enrichment.py`
- [ ] T035 [P1] [US2] Implement Hermes-driven enrichment selection in `src/hermes_youtube_curator/curation/selection_service.py`
- [X] T036 [US2] Implement the `select-enrichment` command flow in `src/hermes_youtube_curator/cli/select_enrichment.py`
- [X] T037 [US2] Implement the `enrich-videos` command flow in `src/hermes_youtube_curator/cli/enrich_videos.py`
- [X] T038 [US2] Integrate bundled `youtube-content` usage into `skills/youtube-curator/SKILL.md`, adding supplemental local skill steps only if required
- [X] T039 [US2] Add Hermes curator skill setup commands and transcript dependency guidance in `specs/001-youtube-curator/quickstart.md`
- [ ] T040 [P2] [US2] Update the Hermes curator skill/prompt flow to consume enriched descriptions and transcripts after real enrichment exists
- [ ] T041 [US2] Document transcript helper usage, Hermes skill setup flow, and model-evaluation workflow in `specs/001-youtube-curator/quickstart.md`

**Checkpoint**: User Story 2 is functional; Hermes can choose a bounded set of videos, use transcript and metadata helpers, and produce richer summaries.

---

## Phase 5: User Story 3 - Build long-term interest memory with guardrails (Priority: P3)

**Goal**: Add reviewable memory proposals, longitudinal theme tracking, and a constrained Hermes self-learning loop without allowing unrestricted autonomy.

**Independent Test**: Process multiple prior runs and confirm the curator surfaces recurring themes and memory proposals while requiring approval before any persistent preference update is applied.

### Tests for User Story 3

- [ ] T042 [P] [US3] Add integration tests for cross-run theme analysis and memory proposal generation in `tests/integration/test_memory_proposals.py`
- [ ] T043 [P] [US3] Add contract tests for memory proposal persistence and approval state transitions in `tests/contract/test_memory_contracts.py`

### Implementation for User Story 3

- [ ] T044 [P2] [US3] Implement theme-history and memory-proposal persistence as synthesized wiki pages, using Hermes memory only as a compact active summary
- [ ] T045 [P2] [US3] Implement cross-run theme analysis and memory proposal synthesis in the Hermes wiki/skill flow
- [ ] T046 [US3] Integrate approval-gated memory proposals into the Hermes curator output flow
- [ ] T047 [US3] Add Hermes setup commands for curator skill registration and bounded self-learning loop configuration in `specs/001-youtube-curator/quickstart.md`
- [ ] T048 [US3] Document the review-and-approval loop for memory proposals in `specs/001-youtube-curator/quickstart.md`

**Checkpoint**: User Story 3 is functional; the curator can learn across runs, but all durable preference changes remain explicit proposals.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Harden runtime behavior, validate the full operator workflow, and tighten documentation after the main stories are working.

- [ ] T049 [P] Add fixture artifacts covering partial collection, repeated recommendations, and delivery failures in `tests/fixtures/`
- [X] T050 Add end-to-end CLI smoke checks for local operator use through `python3 -m hermes_youtube_curator.cli.main`
- [ ] T051 [P] Add Hermes cron delivery retry, idempotency, and failure-recording operator guidance
- [ ] T052 [P] Add schema migration notes and backup/restore guidance for local state in `specs/001-youtube-curator/quickstart.md`
- [ ] T053 Run quickstart validation and update operator-facing setup instructions in `specs/001-youtube-curator/quickstart.md`
- [ ] T055 Add deterministic scheduler setup examples and operator guidance for recurring runs, covering OS cron/systemd and the chosen Hermes scheduling path if adopted, in `ops/cron/youtube-curator.cron`, `ops/systemd/hermes-youtube-curator.service`, `ops/systemd/hermes-youtube-curator.timer`, and `specs/001-youtube-curator/quickstart.md`
- [ ] T057 Add Hermes tool-allowlist setup and guardrail validation for normal curator runs in `specs/001-youtube-curator/quickstart.md` and `tests/contract/test_guardrails.py`
- [X] T058 [P0] Add a short persistence decision record to `specs/001-youtube-curator/research.md` comparing SQLite event/artifact indexing with a Karpathy-style LLM Wiki / Hermes memory layer for agent-readable long-term knowledge

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; defines the MVP.
- **User Story 2 (Phase 4)**: Depends on User Story 1’s shared curation and CLI scaffolding.
- **User Story 3 (Phase 5)**: Depends on User Story 1 persistence and curator flow; benefits from User Story 2 enriched evidence.
- **Polish (Phase 6)**: Depends on whichever stories are in scope.

### User Story Dependencies

- **US1**: Starts after Phase 2 and is independently shippable as the MVP.
- **US2**: Starts after Phase 2, but in practice should build on US1 because the enriched digest extends the existing curator path.
- **US3**: Starts after Phase 2, but depends on stored runs and digests established in US1 and is stronger with US2 enrichment in place.

### Within Each User Story

- Contract and integration tests should be written before or alongside the first implementation task they protect.
- Collection adapters precede CLI command wiring.
- Persistence and artifact support precede orchestration.
- Hermes integration tasks precede setup scripts and operator docs.
- Delivery and memory changes must record explicit structured outcomes rather than relying on side effects.

### Parallel Opportunities

- T003-T005 can run in parallel after T002.
- T007-T014 can run in parallel once T006 establishes the shared model surface.
- In US1, T020 and T021 can run in parallel; T023 and T024 can follow in parallel.
- In US2, T033, T034, and T038 can run in parallel before T035-T040 converge.
- In US3, T044 and T045 can run in parallel before T046 and T047.

---

## Parallel Example: User Story 1

```bash
# Launch US1 collection tests together:
Task: "Add integration tests for homepage collection and snapshot persistence in tests/integration/test_refresh_home.py"
Task: "Add integration tests for history collection and recency signal persistence in tests/integration/test_refresh_history.py"

# Launch US1 collectors together:
Task: "Implement signed-in homepage collection with Playwright in src/hermes_youtube_curator/youtube/home_collector.py"
Task: "Implement recent watch-history collection with Playwright in src/hermes_youtube_curator/youtube/history_collector.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch US2 integration/contract tests together:
Task: "Add integration tests for enrichment selection decisions and stored reasons in tests/integration/test_select_enrichment.py"
Task: "Add integration tests for metadata/transcript enrichment partial-success behavior in tests/integration/test_enrich_videos.py"
Task: "Add contract tests for transcript-helper and enrichment artifact behavior in tests/contract/test_enrichment_contracts.py"

# Launch US2 enrichment components together:
Task: "Implement deterministic metadata and transcript enrichment adapters in src/hermes_youtube_curator/youtube/enrichment.py"
Task: "Integrate bundled youtube-content usage and any repo-local transcript helper invocation into skills/youtube-curator/SKILL.md"
Task: "Implement canonical video linking through the wiki raw/index persistence layer"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate the command gates, artifact outputs, and Hermes-owned Telegram delivery.
5. Use that result to judge whether the chosen local model and Hermes flow are good enough before investing further in deeper persistence or learning behavior.

### Incremental Delivery

1. Ship the deterministic collector plus Hermes curator and Telegram MVP from US1.
2. Add skill-guided selection and enrichment from US2 once the base model path is proven, preferring the bundled `youtube-content` skill for transcripts.
3. Add longitudinal memory proposals and the constrained self-learning loop from US3 after the base curation quality is acceptable.
4. Harden retries, idempotency, and operator workflow in Phase 6.

### Notes

- The task order intentionally prioritizes proving the Python and Hermes flow before deeper optimization.
- Deterministic scheduling stays upstream; Hermes does not own wake-up logic.
- Telegram delivery is deterministic whenever a digest exists.
- Persistence starts as the minimum needed to support artifacts, run records, and delivery tracking, then expands for longitudinal memory.
