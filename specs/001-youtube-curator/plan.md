# Implementation Plan: YouTube Curator

**Branch**: `001-youtube-curator` | **Date**: 2026-05-26 | **Spec**: [spec.md](/home/dan-parii/Documents/HermesYoutubeCurator/specs/001-youtube-curator/spec.md)
**Input**: Feature specification from `/specs/001-youtube-curator/spec.md`

**Note**: This plan is shaped for the DEV "Build With Hermes Agent" challenge, so Hermes Agent must be doing meaningful work at the center of the system rather than acting as a thin wrapper around scripts.

## Summary

Build a personal YouTube curator around a deterministic morning pipeline. Hermes cron is the preferred configured scheduler for starting the run, though another configured deterministic scheduler remains acceptable if operationally simpler. Python modules collect the signed-in YouTube home feed and recent watch history, and the system records structured candidate snapshots. Hermes then uses recent behavior and persistent preference memory to decide which video IDs deserve deeper enrichment, after which deterministic enrichers fetch descriptions and richer metadata while the bundled `youtube-content` skill is the preferred transcript path. Hermes finally ranks recommendations, generates digests and idea prompts, applies a dedicated curator skill to shape Telegram-facing message structure and link policy, prepares approval-gated memory proposals, and delivers the resulting digest through Hermes Telegram messaging. WhatsApp remains a stretch-goal follow-up rather than part of the v1 delivery path.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Playwright, YouTube Data API v3 client, `youtube-transcript-api`, Hermes Agent, Hermes bundled `youtube-content` skill, Hermes Telegram messaging gateway, vLLM, SQLite client library, Pydantic-style data validation, pytest  
**Storage**: SQLite for durable state and JSON snapshots for raw run artifacts  
**Testing**: pytest for contract and integration coverage at orchestration, YouTube collection and enrichment, curation, persistence, delivery, and adapter seams  
**Target Platform**: Linux-first local or VPS environment with browser automation support; macOS-compatible for development  
**Project Type**: Single Python application with Hermes skill assets and scheduled automation entrypoints  
**Performance Goals**: Prefer a typical refresh-plus-curation cycle to complete within 5 minutes; up to 10 minutes is acceptable for personal scheduled use, with digest review staying under 5 minutes for the user  
**Constraints**: Logged-in extraction must remain read-only, external browsing must stay restricted to defined YouTube collection flows, recurring runs must be triggered by a deterministic configured scheduler with Hermes cron preferred, delivery must go through bounded Hermes Telegram integration rather than ad hoc chat automation, Hermes tool access must be constrained to an explicit allowlist for normal curator runs, memory updates require explicit approval, Hermes self-improvement behaviors must be evaluated before they become part of the normal operating path, the design must keep one primary execution path per behavior, the design must favor a few deep modules over many stage packages, and the system must degrade gracefully when history, descriptions, transcripts, or delivery targets are unavailable  
**Scale/Scope**: Single-user personal curator, one signed-in YouTube account, recurring scheduled runs, one primary Telegram delivery destination, and a modest history of snapshots and reports stored locally

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Simplicity: PASS. The design uses one primary path: Hermes cron, or another explicitly configured deterministic scheduler if needed, triggers collection, Hermes curates every collected run, deterministic enrichment runs when selected, then Hermes delivers through a configured Telegram target. No run-level skip branch, agent-owned wake-up logic, or hosted fallback branch is retained in the baseline plan.
- Stack Fit: PASS. The plan stays close to a Python + API library + Playwright + Hermes gateway + Markdown-guidance stack.
- Module Seams: PASS AFTER DEEPENING. The design groups complexity into a few deep modules: `pipeline/` for orchestration, `youtube/` for collection plus enrichment behind external adapters, `curation/` for Hermes-backed selection plus synthesis, `persistence/` for SQLite and artifact storage, and `delivery/` for Telegram transport.
- Testing Seams: PASS. Planned test coverage focuses on the public interfaces of the deep modules and their adapters rather than helper-level stage tests.
- Source Verification: PASS WITH REQUIRED FOLLOW-THROUGH. Before implementation begins, current docs or upstream source must be recorded for Playwright, the YouTube Data API client, `youtube-transcript-api`, Hermes Agent, the bundled `youtube-content` skill, Hermes Telegram messaging, and vLLM.
- Hermes challenge alignment: PASS. Hermes Agent remains central through contextual selection, curation, messaging delivery, memory, and report generation rather than being an incidental dependency.

## Architectural Seams

- **Scheduler -> Pipeline**: Hermes cron is the preferred scheduler and any configured deterministic scheduler may start the run; `pipeline/` receives a bounded "run now" trigger and does not contain agent-owned wake-up logic.
- **Pipeline -> YouTube**: `pipeline/` asks `youtube/` to collect homepage and history evidence and later to enrich selected videos; callers consume typed results rather than browser state or API specifics.
- **Pipeline -> Curation**: `pipeline/` hands snapshots, history, prior memory, and enriched content to `curation/`, which owns enrichment selection, ranking, summaries, idea proposals, and memory proposals.
- **YouTube -> Persistence**: `youtube/` emits structured snapshot and enrichment artifacts that `persistence/` stores and reloads without leaking scraper or API details upward.
- **Curation -> Persistence**: `curation/` records selection artifacts, digests, and approval-gated memory proposals through `persistence/` rather than managing storage details itself.
- **Curation -> Delivery**: `curation/` produces a completed digest artifact; `delivery/` sends it to the configured Telegram target without exposing transport details to curation logic.
- **Delivery -> Persistence**: `delivery/` records whether delivery succeeded or failed and stores enough structured detail for retry or review.
- **Internal vs External Seams**: Ports are justified only at real dependency boundaries such as browser automation, YouTube APIs/transcripts, Hermes/vLLM invocation, and Telegram delivery. In-process coordination stays inside the deep modules rather than being surfaced as public seams.

## Project Structure

### Documentation (this feature)

```text
specs/001-youtube-curator/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── curator-cli.md
│   └── snapshot-artifacts.md
└── tasks.md
```

### Source Code (repository root)

```text
src/
└── hermes_youtube_curator/
    ├── cli/
    ├── config/
    ├── pipeline/
    ├── youtube/
    ├── curation/
    ├── persistence/
    ├── delivery/
    └── models.py

skills/
└── youtube-curator/

scripts/
├── morning_run.py
├── refresh_home.py
├── refresh_history.py
├── select_enrichment.py
├── enrich_videos.py
├── run_curator.py
└── setup_hermes_curator.sh

ops/
├── cron/
│   └── youtube-curator.cron
└── systemd/
    ├── hermes-youtube-curator.service
    └── hermes-youtube-curator.timer

tests/
├── contract/
├── fixtures/
└── integration/
```

**Structure Decision**: Use a single Python project with a few deep modules. `pipeline/` remains intentionally thin and coordinates the run. `youtube/` is a deep module that owns both deterministic collection and bounded enrichment behind adapters for Playwright, the YouTube Data API, and transcript retrieval. `curation/` is a deep module that owns Hermes-backed enrichment selection, ranking, digest generation, and approval-gated memory proposals behind one behavioral interface, while the dedicated `skills/youtube-curator/` asset shapes Telegram message framing, section order, link-inclusion policy, transcript-oriented formatting guidance, and reuse of the bundled `youtube-content` skill as the preferred transcript workflow. `persistence/` owns SQLite plus artifact storage as one local-substitutable seam. `delivery/` owns Telegram transport and delivery records. Hermes memory and skill mutation are treated as bounded capabilities to evaluate, not assumptions baked into the first working path.

## Complexity Tracking

No constitution violations or exceptional complexity allowances are currently required.
