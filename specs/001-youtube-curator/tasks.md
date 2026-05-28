# Tasks: YouTube Curator

**Input**: Design documents from `/specs/001-youtube-curator/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Include seam, contract, and adapter tests where they protect deterministic CLI behavior, Hermes integration boundaries, or persistence/delivery contracts.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the Python project skeleton and capture the verified integration references needed before implementation.

- [X] T001 Create the application package and test directory skeleton in `src/hermes_youtube_curator/__init__.py`, `src/hermes_youtube_curator/cli/__init__.py`, `src/hermes_youtube_curator/pipeline/__init__.py`, `src/hermes_youtube_curator/youtube/__init__.py`, `src/hermes_youtube_curator/curation/__init__.py`, `src/hermes_youtube_curator/persistence/__init__.py`, `src/hermes_youtube_curator/delivery/__init__.py`, `tests/contract/__init__.py`, and `tests/integration/__init__.py`
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

- [X] T006 Define shared Pydantic-style domain models for runs, snapshots, selections, digests, and delivery records in `src/hermes_youtube_curator/models.py`
- [X] T007 [P] Implement artifact serialization and JSON storage helpers in `src/hermes_youtube_curator/persistence/artifacts.py`
- [X] T008 [P] Implement SQLite schema initialization and repository scaffolding for runs, videos, digests, and deliveries in `src/hermes_youtube_curator/persistence/sqlite_store.py`
- [X] T009 [P] Implement structured logging and machine-readable result helpers for CLI commands in `src/hermes_youtube_curator/cli/results.py`
- [X] T010 [P] Implement the deterministic orchestration context and dependency wiring in `src/hermes_youtube_curator/pipeline/context.py`
- [X] T011 [P] Create CLI entrypoint wrappers for `morning-run`, `refresh-home`, `refresh-history`, `select-enrichment`, `enrich-videos`, and `run-curator` in `src/hermes_youtube_curator/cli/main.py`
- [X] T012 Implement command exit-code gates and result validation shared by all entrypoints in `src/hermes_youtube_curator/cli/guards.py`
- [X] T013 [P] Add contract tests for CLI machine-readable outputs defined in `specs/001-youtube-curator/contracts/curator-cli.md` in `tests/contract/test_cli_contracts.py`
- [X] T014 [P] Add artifact contract tests for snapshot, selection, digest, and delivery records from `specs/001-youtube-curator/contracts/snapshot-artifacts.md` in `tests/contract/test_artifact_contracts.py`
- [X] T015 Add integration tests for shared CLI guards and run-summary failure handling in `tests/integration/test_cli_guards.py`

**Checkpoint**: Foundation ready; deterministic commands and shared artifacts exist behind stable seams.

---

## Phase 3: User Story 1 - Review curated recommendations (Priority: P1) 🎯 MVP

**Goal**: Collect homepage and recent-history evidence, generate a Hermes-backed digest, and deterministically deliver it to Telegram.

**Independent Test**: Run the homepage/history collection, curator, and delivery entrypoints against fixture data or a configured environment and confirm a digest is produced with a recorded Telegram delivery outcome.

### Tests for User Story 1

- [X] T016 [P] [US1] Add integration tests for homepage collection and snapshot persistence in `tests/integration/test_refresh_home.py`
- [X] T017 [P] [US1] Add integration tests for history collection and recency signal persistence in `tests/integration/test_refresh_history.py`
- [X] T018 [P] [US1] Add integration tests for the full `morning-run` happy path and partial-evidence path in `tests/integration/test_morning_run.py`
- [X] T019 [P] [US1] Add contract tests for Telegram delivery records and transport outcomes in `tests/contract/test_delivery_contracts.py`

### Implementation for User Story 1

- [ ] T020 [P] [US1] Implement signed-in homepage collection with Playwright in `src/hermes_youtube_curator/youtube/home_collector.py`
- [ ] T021 [P] [US1] Implement recent watch-history collection with Playwright in `src/hermes_youtube_curator/youtube/history_collector.py`
- [X] T023 [US1] Implement the `refresh-home` command flow and machine-readable output in `src/hermes_youtube_curator/cli/refresh_home.py`
- [X] T024 [US1] Implement the `refresh-history` command flow and machine-readable output in `src/hermes_youtube_curator/cli/refresh_history.py`
- [ ] T025 [US1] Implement Hermes curator invocation and digest synthesis using local artifacts in `src/hermes_youtube_curator/curation/curator_service.py`
- [ ] T026 [US1] Implement deterministic Telegram delivery through Hermes in `src/hermes_youtube_curator/delivery/telegram.py`
- [X] T027 [US1] Implement the `run-curator` command flow in `src/hermes_youtube_curator/cli/run_curator.py`
- [X] T028 [US1] Implement the end-to-end `morning-run` orchestration in `src/hermes_youtube_curator/cli/morning_run.py`
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

- [X] T033 [P] [US2] Implement canonical video linking and enrichment selection repositories in `src/hermes_youtube_curator/persistence/video_store.py`
- [ ] T034 [P] [US2] Implement deterministic metadata enrichment adapters and preferred bundled-skill transcript integration in `src/hermes_youtube_curator/youtube/enrichment.py`
- [ ] T035 [US2] Implement Hermes-driven enrichment selection in `src/hermes_youtube_curator/curation/selection_service.py`
- [X] T036 [US2] Implement the `select-enrichment` command flow in `src/hermes_youtube_curator/cli/select_enrichment.py`
- [X] T037 [US2] Implement the `enrich-videos` command flow in `src/hermes_youtube_curator/cli/enrich_videos.py`
- [X] T038 [US2] Integrate bundled `youtube-content` usage into `skills/youtube-curator/SKILL.md`, adding supplemental local skill steps only if required
- [X] T039 [US2] Add Hermes curator skill setup commands and transcript dependency guidance in `scripts/setup_hermes_curator.sh`
- [X] T040 [US2] Update curator synthesis to consume enriched descriptions and transcripts in `src/hermes_youtube_curator/curation/curator_service.py`
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

- [ ] T044 [P] [US3] Extend persistence models and repositories for theme history and memory proposals in `src/hermes_youtube_curator/persistence/memory_store.py`
- [ ] T045 [P] [US3] Implement cross-run theme analysis and memory proposal synthesis in `src/hermes_youtube_curator/curation/memory_service.py`
- [ ] T046 [US3] Integrate approval-gated memory proposals into the curator output pipeline in `src/hermes_youtube_curator/curation/curator_service.py`
- [ ] T047 [US3] Add Hermes setup commands for curator skill registration and bounded self-learning loop configuration in `scripts/setup_hermes_curator.sh`
- [ ] T048 [US3] Document the review-and-approval loop for memory proposals in `specs/001-youtube-curator/quickstart.md`

**Checkpoint**: User Story 3 is functional; the curator can learn across runs, but all durable preference changes remain explicit proposals.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Harden runtime behavior, validate the full operator workflow, and tighten documentation after the main stories are working.

- [ ] T049 [P] Add fixture artifacts covering partial collection, repeated recommendations, and delivery failures in `tests/fixtures/`
- [X] T050 Add end-to-end run scripts and smoke checks for local operator use in `scripts/morning_run.py`, `scripts/refresh_home.py`, `scripts/refresh_history.py`, `scripts/select_enrichment.py`, `scripts/enrich_videos.py`, and `scripts/run_curator.py`
- [ ] T051 [P] Add delivery retry, idempotency, and failure-recording hardening in `src/hermes_youtube_curator/delivery/telegram.py`
- [ ] T052 [P] Add schema migration notes and backup/restore guidance for local state in `specs/001-youtube-curator/quickstart.md`
- [ ] T053 Run quickstart validation and update operator-facing setup instructions in `specs/001-youtube-curator/quickstart.md`
- [ ] T055 Add deterministic scheduler setup examples and operator guidance for recurring runs, covering OS cron/systemd and the chosen Hermes scheduling path if adopted, in `ops/cron/youtube-curator.cron`, `ops/systemd/hermes-youtube-curator.service`, `ops/systemd/hermes-youtube-curator.timer`, and `specs/001-youtube-curator/quickstart.md`
- [ ] T057 Add Hermes tool-allowlist setup and guardrail validation for normal curator runs in `scripts/setup_hermes_curator.sh`, `specs/001-youtube-curator/quickstart.md`, and `tests/contract/test_guardrails.py`

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
Task: "Implement canonical video linking and enrichment selection repositories in src/hermes_youtube_curator/persistence/video_store.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate the command gates, artifact outputs, and deterministic Telegram delivery.
5. Use that result to judge whether the chosen local model and Hermes flow are good enough before investing further in deeper persistence or learning behavior.

### Incremental Delivery

1. Ship the deterministic collector + curator + Telegram MVP from US1.
2. Add skill-guided selection and enrichment from US2 once the base model path is proven, preferring the bundled `youtube-content` skill for transcripts.
3. Add longitudinal memory proposals and the constrained self-learning loop from US3 after the base curation quality is acceptable.
4. Harden retries, idempotency, and operator workflow in Phase 6.

### Notes

- The task order intentionally prioritizes proving the Python and Hermes flow before deeper optimization.
- Deterministic scheduling stays upstream; Hermes does not own wake-up logic.
- Telegram delivery is deterministic whenever a digest exists.
- Persistence starts as the minimum needed to support artifacts, run records, and delivery tracking, then expands for longitudinal memory.
