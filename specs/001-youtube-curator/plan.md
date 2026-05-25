# Implementation Plan: YouTube Curator

**Branch**: `001-youtube-curator` | **Date**: 2026-05-26 | **Spec**: [spec.md](/home/dan-parii/Documents/HermesYoutubeCurator/specs/001-youtube-curator/spec.md)
**Input**: Feature specification from `/specs/001-youtube-curator/spec.md`

**Note**: This plan is shaped for the DEV "Build With Hermes Agent" challenge, so Hermes Agent must be doing meaningful work at the center of the system rather than acting as a thin wrapper around scripts.

## Summary

Build a personal YouTube curator that combines deterministic collection of the signed-in YouTube home feed and recent watch history with Hermes Agent orchestration, memory, and skills. Python scripts will gather structured snapshots and enrich them with metadata, descriptions, and transcripts when available. Hermes will decide whether a run is worth curating, rank recommendations against recent viewing behavior and long-term taste memory, then generate digests, summaries, idea prompts, and approval-gated memory proposals. The system is local-first for reasoning with vLLM plus Qwen/Qwen3.6-27B, with optional remote-model fallback only if local quality is insufficient.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Playwright, YouTube Data API v3 client, `youtube-transcript-api`, Hermes Agent, vLLM, SQLite client library, Pydantic-style data validation, pytest  
**Storage**: SQLite for durable state and JSON snapshots for raw run artifacts  
**Testing**: pytest for unit, integration, and contract coverage; fixture-based snapshot tests for extractor outputs  
**Target Platform**: Linux-first local or VPS environment with browser automation support; macOS-compatible for development  
**Project Type**: Single Python application with Hermes skill assets and scheduled automation entrypoints  
**Performance Goals**: Complete a typical refresh-plus-curation cycle quickly enough for personal scheduled use, with digest review staying under 5 minutes for the user  
**Constraints**: Logged-in extraction must remain read-only, external browsing must stay restricted to defined YouTube collection flows, memory updates require explicit approval, and the system must degrade gracefully when history, descriptions, or transcripts are unavailable  
**Scale/Scope**: Single-user personal curator, one signed-in YouTube account, recurring scheduled runs, and a modest history of snapshots and reports stored locally

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The current constitution file is still an unfilled template, so there are no active project-specific governance gates to enforce yet.

- Gate status: PASS
- Noted risk: Because the constitution is not yet defined, architectural discipline must come from this plan and later task scoping rather than repository-wide rules.
- Hermes challenge alignment: PASS. Hermes Agent remains central through scheduling, skills, memory, and report generation rather than being an incidental dependency.

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
    ├── curation/
    ├── extractors/
    ├── enrichers/
    ├── memory/
    ├── models/
    ├── reporting/
    ├── scheduling/
    ├── storage/
    └── utils/

skills/
├── youtube-curator/
├── video-idea-miner/
├── research-synthesizer/
└── memory-maintainer/

scripts/
├── refresh_home.py
├── refresh_history.py
├── enrich_videos.py
└── run_curator.py

tests/
├── contract/
├── fixtures/
├── integration/
└── unit/
```

**Structure Decision**: Use a single Python project for deterministic extraction, enrichment, storage, and orchestration glue, with Hermes-facing skills stored separately so they can evolve as explicit agent assets. This keeps browser/data collection testable and constrained while preserving the Hermes-centric challenge angle.

## Complexity Tracking

No constitution violations or exceptional complexity allowances are currently required.
