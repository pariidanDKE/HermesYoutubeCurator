# Research: YouTube Curator

## Decision 1: Use deterministic browser automation for signed-in collection

**Decision**: Use Playwright-driven Python scripts to capture the signed-in YouTube home feed and recent watch history.

**Rationale**: The core product depends on signals that are specific to a signed-in personal account, including homepage recommendations, the recent history tab, and recency cues that are not reliably available through public APIs alone. Playwright supports repeatable, read-only collection while keeping browsing behavior scripted and constrained.

**Alternatives considered**:
- Selenium: viable but heavier and less aligned with modern Python browser automation ergonomics.
- Public API only: insufficient for personalized homepage and watch-history capture.
- Fully agent-driven browsing: rejected because it weakens guardrails and makes extraction less deterministic.

## Decision 2: Enrich collected videos with API metadata and transcripts when available

**Decision**: After initial collection, enrich videos using YouTube Data API v3 for metadata and `youtube-transcript-api` for transcripts when accessible.

**Rationale**: Homepage/history extraction alone gives weak evidence for summarization. The product goal requires descriptions, richer metadata, and transcript-based summaries when possible. Separating collection from enrichment also makes failure handling clearer and allows partial success when one enrichment source is unavailable.

**Alternatives considered**:
- Screen-scraped metadata only: too shallow for meaningful summaries.
- Manual transcript scraping from pages: more brittle than a dedicated transcript client.
- Transcript-only enrichment: insufficient because descriptions, channel metadata, and publication context remain useful even when no transcript exists.

## Decision 3: Keep Hermes Agent at the center of orchestration, memory, and report generation

**Decision**: Use Hermes Agent for scheduled runs, skills, long-term memory, approval-gated memory proposals, and final report generation.

**Rationale**: The DEV challenge explicitly rewards meaningful Hermes usage, and this project’s main differentiator is longitudinal taste memory rather than raw extraction. Hermes’ documented strengths include a built-in learning loop, skills, persistent memory, scheduled automations, and multi-step reasoning, which map directly to curation, recurring reports, and self-improving preference modeling. This keeps Hermes as the heart of the system instead of a thin shell around a scraper. Sources: [Hermes challenge page](https://dev.to/challenges/hermes-agent-2026-05-15), [Hermes Agent GitHub README](https://github.com/NousResearch/hermes-agent).

**Alternatives considered**:
- Pure Python pipeline with no agent: simpler, but it misses the challenge goal and weakens the memory/skills story.
- Let Hermes do live browsing itself: rejected because the spec requires deterministic, guardrailed extraction.
- Use Hermes only for report formatting: too shallow to be a credible challenge submission.

## Decision 4: Use local-first reasoning with vLLM plus Qwen/Qwen3.6-27B

**Decision**: Use vLLM serving a Qwen/Qwen3.6-27B-class model as the preferred reasoning backend for ranking, summarization, theme extraction, idea generation, and taste synthesis.

**Rationale**: The curator needs recurring reasoning over private local artifacts. A local-first stack improves controllability, keeps iteration cheap for scheduled runs, and fits the user’s stated preference. vLLM is a pragmatic serving layer for repeated inference workloads.

**Alternatives considered**:
- Smaller local models: potentially cheaper but may underperform on nuanced curation and summarization.
- DeepSeek API or Kimi API as primary: easier to bootstrap, but weaker fit for local-first control and privacy.
- Hybrid fallback only: retained as a backup path if local quality is insufficient.

## Decision 5: Allow optional remote-model fallback without changing the core architecture

**Decision**: If local model quality is insufficient, support a hybrid path where Hermes can call DeepSeek API or Kimi API for selected reasoning tasks.

**Rationale**: This preserves implementation flexibility without committing the product to a hosted-only architecture. The system can stay local-first while still having a practical escape hatch for summary quality or ideation quality issues.

**Alternatives considered**:
- No fallback at all: risks stalling the project if local quality disappoints.
- Hosted-only reasoning: weakens the local-first design preference.

## Decision 6: Store durable state in SQLite and raw artifacts in JSON snapshots

**Decision**: Use SQLite for normalized durable state and JSON files for raw run snapshots and generated reports.

**Rationale**: The curator is single-user and local. SQLite is sufficient for histories, preferences, and cross-run linking, while raw JSON snapshots preserve the original extracted evidence for debugging, replay, and agent re-analysis.

**Alternatives considered**:
- JSON only: too awkward for longitudinal queries and deduplication.
- Postgres: unnecessary operational overhead for a personal tool.

## Decision 7: Treat recommendation feed and recent watch history as separate but linked input streams

**Decision**: Model homepage recommendations and recent watch history as separate snapshots that can be merged during curation.

**Rationale**: They serve different purposes. Recommendations represent present opportunities; history represents immediate taste and recency context. Keeping them separate simplifies failure handling when one source is unavailable and makes recency-aware ranking easier to reason about.

**Alternatives considered**:
- Merge both into one untyped blob: simpler short-term, but worse for debugging and analysis.
- Ignore history: loses a strong signal for what the user wants right now.

## Decision 8: Use explicit contracts for CLI entrypoints and snapshot artifacts

**Decision**: Define lightweight contracts for operator-facing CLI commands and machine-readable snapshot/report artifacts.

**Rationale**: This project is internal but still has important boundaries between deterministic scripts, Hermes orchestration, and stored artifacts. Contract docs will keep the scripts composable and make testing easier.

**Alternatives considered**:
- No contracts: faster initially, but causes drift between scripts, storage, and Hermes prompts.
- Full OpenAPI service design: unnecessary because this is not primarily a network service.
