# Research: YouTube Curator

## Decision 1: Use deterministic browser automation for signed-in collection

**Decision**: Use Playwright-driven Python scripts to capture the signed-in YouTube home feed and recent watch history.

**Rationale**: The core product depends on signals that are specific to a signed-in personal account, including homepage recommendations, the recent history tab, and recency cues that are not reliably available through public APIs alone. Playwright supports repeatable, read-only collection while keeping browsing behavior scripted and constrained.

**Alternatives considered**:
- Selenium: viable but heavier and less aligned with modern Python browser automation ergonomics.
- Public API only: insufficient for personalized homepage and watch-history capture.
- Fully agent-driven browsing: rejected because it weakens guardrails and makes extraction less deterministic.

**Source verification required before implementation**:
- Current Playwright Python documentation for browser/session handling.
- Current upstream/source behavior for the selected signed-in session strategy.

## Decision 2: Use a deterministic scheduler for recurring runs

**Decision**: Use a deterministic scheduler to start the morning pipeline, with Hermes built-in cron as the preferred option when it is configured explicitly and kept deterministic.

**Rationale**: Time-based execution is infrastructure, not intelligence. A deterministic scheduler expresses the policy clearly, keeps the execution path simple, and avoids fake autonomy. Hermes' built-in cron is still deterministic when configured explicitly, and it is the simplest path when the agent, skill, and delivery environment already live inside Hermes. The architectural concern is not "Hermes vs non-Hermes" but "configured schedule vs agent-decided wake-up."

**Alternatives considered**:
- Hermes-owned scheduling decisions: rejected because there is no meaningful product value in having the agent decide when a fixed daily run should occur.
- OS-level cron or systemd as the default: acceptable fallback, but less aligned with the desired simplicity when Hermes cron is sufficient.
- Manual-only operation: too fragile for a recurring curator.

## Decision 3: Let Hermes select which videos deserve deeper enrichment

**Decision**: After deterministic collection, use Hermes to choose which video IDs deserve deeper enrichment based on current recommendations, recent watch history, and persistent preference memory.

**Rationale**: This is a real contextual decision that benefits from memory and judgment. It is a better use of agent reasoning than scheduling or freeform browsing, and it allows the system to spend transcript/metadata effort on the candidates most likely to matter.

**Alternatives considered**:
- Enrich every collected video equally: simpler, but wastes effort on low-value items.
- Hard-coded enrichment heuristics only: easier to implement, but less adaptive to taste, mood, and recent viewing patterns.

**Source verification required before implementation**:
- Current Hermes Agent documentation or upstream source for skills, memory, and invocation behavior.
- Current bundled `youtube-content` skill documentation and helper-script behavior.

## Decision 4: Enrich selected videos with API metadata and transcripts when available

**Decision**: After selection, enrich the chosen videos using YouTube Data API v3 for metadata, with the bundled `youtube-content` skill as the preferred transcript path and direct `youtube-transcript-api` integration only as a fallback if the bundled skill proves insufficient.

**Rationale**: Homepage/history extraction alone gives weak evidence for summarization. The product goal requires descriptions, richer metadata, and transcript-based summaries when possible. The bundled `youtube-content` skill already covers transcript fetching and transcript-to-format workflows, so it is the simplest transcript path unless it proves inadequate. Grouping collection and enrichment behind the same YouTube boundary keeps failure handling clear and keeps the rest of the system insulated from source-specific details.

**Alternatives considered**:
- Screen-scraped metadata only: too shallow for meaningful summaries.
- Manual transcript scraping from pages: more brittle than a dedicated transcript client or the bundled Hermes skill.
- Transcript-only enrichment: insufficient because descriptions, channel metadata, and publication context remain useful even when no transcript exists.

**Source verification required before implementation**:
- Current YouTube Data API v3 documentation for the chosen endpoints and quotas.
- Current bundled `youtube-content` skill documentation and helper-script behavior.
- Current `youtube-transcript-api` documentation or installed source for transcript availability and failure behavior, if fallback integration is needed.

## Decision 5: Keep Hermes Agent at the center of curation, memory, and report generation

**Decision**: Use Hermes Agent for enrichment selection, final curation, long-term memory, approval-gated memory proposals, and report generation.

**Rationale**: The DEV challenge explicitly rewards meaningful Hermes usage, and this project’s main differentiator is longitudinal taste memory rather than raw extraction. Hermes’ strengths include a learning loop, skills, persistent memory, and multi-step reasoning, which map directly to selection, curation, recurring reports, and self-improving preference modeling. This keeps Hermes as the heart of the high-judgment parts of the system instead of a thin shell around a scraper.

**Alternatives considered**:
- Pure Python pipeline with no agent: simpler, but it misses the challenge goal and weakens the memory/skills story.
- Let Hermes do live browsing itself: rejected because the spec requires deterministic, guardrailed extraction.
- Use Hermes only for report formatting: too shallow to be a credible challenge submission.
- Multiple narrowly split curator skills: rejected as unnecessary complexity before a single skill proves insufficient.

**Source verification required before implementation**:
- Current Hermes Agent documentation or upstream source for skills, memory, and invocation behavior.

## Decision 5A: Treat Hermes self-improvement as a bounded capability to evaluate, not a baseline dependency

**Decision**: Use Hermes memory and skill systems conservatively in v1. The core curator should rely on explicit skills, explicit prompts, and approval-gated memory proposals first, while Hermes self-improvement behavior is evaluated in a dedicated profile before becoming part of the normal operating path.

**Rationale**: Current Hermes documentation confirms that memory is bounded, session-start scoped, and edited through the `memory` tool, while skills are mutable `SKILL.md` assets that Hermes can create or rewrite through `skill_manage`. Those capabilities are powerful, but this is the user's first Hermes project and the operational behavior is not yet known well enough to make autonomous skill creation or aggressive memory mutation a core dependency. A conservative stance preserves the project's one-simple-path requirement while leaving room to adopt more of Hermes' learning loop once it has been observed under real usage.

**Operational guidance**:
- Use one explicit curator skill as the primary delivery-format and curation-style surface.
- Keep long-term memory changes approval-gated in product logic rather than relying on silent memory writes.
- Evaluate Hermes profile isolation, memory persistence across sessions, skill loading, and skill mutation behavior before enabling any autonomous self-improvement workflow.
- Prefer AGENTS.md and the curated skill for stable steering; use Hermes memory for compact learned preferences and environment facts only after validation.

**Alternatives considered**:
- Rely on Hermes auto-created skills and self-managed memory from the start: rejected as too opaque for a first implementation.
- Avoid Hermes memory and skills entirely: rejected because it weakens the challenge fit and removes a meaningful long-term differentiator.

## Decision 6: Use a single local-first reasoning path with vLLM plus Qwen/Qwen3.6-27B

**Decision**: Use vLLM serving a Qwen/Qwen3.6-27B-class model as the reasoning backend for enrichment selection, ranking, summarization, theme extraction, idea generation, and taste synthesis.

**Rationale**: The curator needs recurring reasoning over private local artifacts. A local-first stack improves controllability, keeps iteration cheap for scheduled runs, and fits the user’s stated preference. A single reasoning path also aligns with the constitution rule against preserving multiple branches for the same behavior.

**Alternatives considered**:
- Smaller local models: potentially cheaper but may underperform on nuanced curation and summarization.
- Hosted APIs as a baseline branch: rejected because they add a second execution path and weaken the local-first design.

**Source verification required before implementation**:
- Current vLLM documentation or source for deployment/runtime requirements.
- Current model packaging/runtime details for the chosen Qwen variant.

## Decision 7: Store durable operational state in Hermes-compatible wiki raw/index files

**Decision**: Use a file-based wiki raw/index layer as the current authoritative operational store. The store lives under `HYC_WIKI_PATH` and follows the Hermes `research-llm-wiki` shape: `SCHEMA.md`, `index.md`, `log.md`, `raw/`, `entities/`, `concepts/`, `comparisons/`, and `queries/`. Project-specific deterministic files live under `raw/curator/`: `videos.json`, `recommendation-events.jsonl`, `watch-history-events.jsonl`, and `runs/*.json`.

**Rationale**: The curator is single-user and local. A small JSON/JSONL index is enough for the current deterministic queries: what videos exist, when videos were recommended, and what appeared in watch history. Keeping these files inside the wiki raw layer also makes the same evidence available to Hermes for later synthesis without introducing a second persistence root. SQLite remains available in the current code for existing run/digest/delivery scaffolding, but it is no longer the chosen source of truth for video, recommendation, or history persistence.

**Alternatives considered**:
- SQLite as authoritative event/index store: robust, but likely premature while the app only needs a few append-only indexes and a canonical video map.
- Postgres: unnecessary operational overhead for a personal tool.
- Loose artifact JSON only: too weak because deterministic code still needs stable indexes for videos, recommendations, and watch history.

**Source verification required before implementation**:
- Current Hermes `research-llm-wiki` guidance for wiki layout, raw source handling, schema, index, and log conventions.

## Decision 7A: Use synthesized wiki pages and Hermes memory above the raw/index layer

**Decision**: Use `raw/curator/` files for facts and events, use wiki pages for durable synthesized taste knowledge, and use Hermes memory only as a compact active summary once the curation path exists.

**Comparison**:
- **Wiki raw/index files**: deterministic, inspectable, easy to back up, and directly compatible with the Hermes wiki skill.
- **Synthesized wiki pages**: good for channel affinities, recurring topics, avoided formats, and long-term taste maps.
- **Hermes memory**: good for short active preference summaries, but too opaque to serve as the full durable knowledge base.
- **SQLite**: still a possible later optimization if JSON/JSONL file scans become painful or constraints/migrations become valuable.

**Rationale**: This keeps the current implementation simple while preserving the Karpathy/Hermes split: raw sources remain immutable or append-only, the wiki compounds knowledge from those sources, and active memory stays small.

## Decision 8: Treat recommendation feed and recent watch history as separate but linked input streams

**Decision**: Model homepage recommendations and recent watch history as separate snapshots that can be merged during selection and curation.

**Rationale**: They serve different purposes. Recommendations represent present opportunities; history represents immediate taste and recency context. Keeping them separate simplifies failure handling when one source is unavailable and makes recency-aware ranking easier to reason about.

**Alternatives considered**:
- Merge both into one untyped blob: simpler short-term, but worse for debugging and analysis.
- Ignore history: loses a strong signal for what the user wants right now.

## Decision 9: Use explicit contracts for CLI entrypoints and snapshot artifacts

**Decision**: Define lightweight contracts for operator-facing CLI commands and machine-readable snapshot/report artifacts.

**Rationale**: This project is internal but still has important boundaries between deterministic scripts, Hermes selection/curation, and stored artifacts. Contract docs will keep the scripts composable and make seam-focused testing easier.

**Alternatives considered**:
- No contracts: faster initially, but causes drift between scripts, storage, and Hermes prompts.
- Full OpenAPI service design: unnecessary because this is not primarily a network service.

## Decision 9A: Deepen around stable dependency boundaries rather than pipeline stages

**Decision**: Organize the implementation around a few deep modules such as `youtube`, `curation`, `persistence`, and `delivery`, while keeping `pipeline` as a thin orchestration layer.

**Rationale**: Collection, transcript retrieval, metadata enrichment, ranking, digest generation, and memory proposals each contain meaningful internal complexity, but that complexity clusters by dependency boundary rather than by CLI stage name. A top-level package per stage would create shallow wrappers and single-adapter seams. Deep modules let the implementation absorb that complexity behind fewer interfaces and keep tests focused on behavior.

**Dependency-shape guidance**:
- In-process coordination stays inside the owning deep module.
- Wiki raw/index files plus local artifact storage are treated as a local-substitutable seam and tested against local fixtures rather than mocks.
- Browser automation, YouTube APIs/transcripts, Hermes/vLLM invocation, and Telegram delivery are treated as real external or remote seams with production and test adapters.
- Ports are introduced only when at least two adapters are justified, typically production plus test.

**Alternatives considered**:
- One top-level module per pipeline stage: rejected because it creates shallow orchestration packages and pushes tests below the real behavior surface.
- Full service decomposition across internal APIs: rejected because the project is a single-user local application and does not benefit from distributed seams.

## Decision 10: Prefer skills plus repo-local scripts over MCP for YouTube enrichment

**Decision**: Use Hermes skills and repo-local Python helpers for enrichment rather than introducing MCP.

**Rationale**: The enrichment workflow is specific to this repository and does not need a service-style tool boundary. Current Hermes documentation shows that skills are instruction documents that can call helper scripts directly, and the bundled `youtube-content` skill already covers transcript fetching and transcript-to-format transformations. For this project, that makes a skill-plus-script approach simpler and more aligned with the constitution than adding a separate MCP layer. Deterministic Playwright collection remains outside Hermes, while transcript-oriented formatting and selected enrichment can happen through explicit Hermes skills and repo-local adapters.

**Documented `youtube-content` scope**:
- The bundled skill is for YouTube transcript extraction and transformation into summaries, chapters, threads, blog posts, or quotes.
- The documented helper script fetches transcripts.
- The skill instructions then tell Hermes to transform the transcript into the requested output format.
- The documented skill does not claim to provide full signed-in recommendation capture or complete video metadata enrichment.

**Alternatives considered**:
- Local MCP server: rejected as an unnecessary extra layer for repo-local logic.
- Broad browser-driven Hermes enrichment for everything: rejected because it weakens determinism for the core pipeline.
- Custom transcript logic only: viable, but it duplicates a useful bundled Hermes capability before proving the need.

**Implementation guidance**:
- Keep Playwright collection deterministic and outside Hermes.
- Use the bundled `youtube-content` skill as the preferred transcript-oriented enrichment path; add supplemental local skills only if the bundled skill proves insufficient.
- Keep metadata enrichment in direct Python adapters where structured non-transcript fields are needed.
- Let the dedicated curator skill own message framing and transcript-formatting guidance rather than creating a separate MCP surface.

**Source verification required before implementation**:
- Current bundled `youtube-content` skill documentation and helper-script behavior.
- Current Hermes skills system documentation for SKILL.md execution patterns.
- Current `youtube-transcript-api` documentation or installed source for transcript availability and failure behavior.

## Decision 11: Use Hermes Telegram delivery for v1 and treat WhatsApp as a stretch goal

**Decision**: Deliver curator digests through Hermes Telegram messaging in v1, and treat WhatsApp delivery as a future stretch goal rather than a core launch requirement.

**Rationale**: The Vigil Crest write-up describes a Telegram-based Hermes instance where the whole interaction happens in Telegram and the repo is a configured Hermes instance rather than a standalone app. Hermes' current docs also show Telegram as a straightforward bot-based integration with scheduled-task delivery to a configured home channel. WhatsApp is supported by Hermes, but the documented path is a paired chat bridge and is more setup-heavy than Telegram. For v1, Telegram gives the simplest path to a reliable personal inbox while leaving room to add WhatsApp later if daily usage demands it.

**Verified delivery findings**:
- Hermes supports Telegram as a full-featured conversational bot and scheduled task delivery to a configured home channel.
- Hermes supports WhatsApp through `hermes whatsapp`, including `bot` and `self-chat` modes, and the gateway can auto-start the WhatsApp bridge from a saved paired session.
- Hermes config recognizes `whatsapp` and `telegram` as built-in messaging platforms.
- Hermes CLI exposes `hermes whatsapp` for configuration and pairing.
- Hermes messaging platforms support attachment delivery via `MEDIA:` tags when the platform supports native attachments.
- The Vigil Crest DEV write-up explicitly says the agent is talked to on Telegram and that the repo is a configured Hermes instance.

**Alternatives considered**:
- WhatsApp-first delivery in v1: possible, but more complex than needed for the first release.
- Direct WhatsApp Cloud API delivery as the primary v1 delivery path: possible, but it adds Meta Business Platform setup, webhook handling, and template/message-policy complexity that is unnecessary when Hermes already has a built-in messaging system.
- Separate non-Hermes delivery subsystem: rejected because it duplicates a capability Hermes already provides.

**Stretch-goal note**:
- WhatsApp remains desirable for later because it matches the user's real daily messaging habits, but it is intentionally out of the v1 contract.

**Architectural seams to preserve**:
- **Scheduler -> Pipeline**: A deterministic scheduler triggers the run without agent wake-up logic.
- **Pipeline -> YouTube**: Collection and enrichment happen through the `youtube` module rather than exposing browser or API details to the rest of the system.
- **Pipeline -> Curation**: Selection, ranking, summarization, and memory proposals happen through the `curation` module rather than through separate stage packages.
- **YouTube/Curation/Delivery -> Persistence**: Storage is handled through one local-substitutable persistence seam.
- **Curation -> Delivery**: Hermes Telegram delivery sends the completed digest without coupling curation to platform-specific details.

**Source verification required before implementation**:
- Current Hermes Telegram setup docs.
- Current Hermes configuration and CLI references for messaging platforms.
- Current Hermes WhatsApp setup docs if the stretch goal is pursued later.

## Implementation Notes: current repo path

- The implemented repo path keeps one deterministic pipeline: `refresh-home` -> `refresh-history` -> `select-enrichment` -> `enrich-videos` -> `run-curator` -> Telegram delivery.
- No MCP layer was added for enrichment or delivery. Transcript-aware guidance lives in `skills/youtube-curator/SKILL.md`, which explicitly points Hermes at the bundled `youtube-content` skill as the preferred transcript workflow.
- No snapshot-diff skip branch was added. The curator only skips when there is not enough evidence to curate, not because the newest snapshot resembles a previous one.
- Hermes cron is the preferred recurring scheduler in the implementation docs and setup script. OS cron and systemd examples remain operator-facing fallback infrastructure, not agent-owned wake-up logic.
- Hermes profile isolation and long-term mutation remain conservative in the current implementation: message framing is skill-driven, memory proposals stay approval-gated in digest output, and there is no autonomous skill or memory rewriting path in the normal run flow.

## Local inference notes: Qwen3.6-27B on RTX 3090 (24 GB)

**Chosen checkpoint**: `QuantTrio/Qwen3.6-27B-AWQ` — INT4 AWQ, group_size 128, zero_point=True (GEMM kernel, not Marlin). Attention projections (q/k/v), first layer, and linear attention components are intentionally kept in full precision by the quantizer. This is a quality-first choice: asymmetric quantization with unquantized attention preserves reasoning fidelity at the cost of Marlin kernel compatibility and a slightly higher VRAM footprint.

**VRAM reality on stock vLLM (0.18.0)**:
- Model weights load at ~18.83 GiB with `--language-model-only`
- The initial profiling/warmup run (runs a forward pass at `max_model_len`) temporarily allocates ~3 GiB in activations on top of weights
- That leaves roughly 1.5–2 GiB for the minimal KV cache allocation during CUDA graph profiling
- At default BF16 KV cache precision, this limits `max_model_len` to approximately 24576 tokens before startup OOM
- Serving flags: `--language-model-only`, `--gpu-memory-utilization 0.95`, `--quantization awq`, `--reasoning-parser qwen3`, `--tool-call-parser qwen3_coder`

**High-context alternative (requires patched vLLM)**:
The checkpoint `Lorbus/Qwen3.6-27B-int4-AutoRound` combined with TurboQuant 3-bit KV cache compression (`--kv-cache-dtype turboquant_3bit_nc`) and MTP speculative decoding achieves 85–106 TPS and 125K context on a single 3090. This requires Genesis patches (Sandermage) to unlock TurboQuant on Qwen3.6's hybrid DeltaNet architecture, plus a custom CUDA graph patch — neither is in stock vLLM. See: [An Overnight Stack for Qwen3.6-27B: 85 TPS, 125K Context, Vision — on One RTX 3090](https://medium.com/@fzbcwvv/an-overnight-stack-for-qwen3-6-27b-85-tps-125k-context-vision-on-one-rtx-3090-0d95c6291914).

**Incremental context expansion path (no patches needed)**:
If 24576 tokens proves insufficient for long transcripts or multi-video batches, the first lever is `--kv-cache-dtype fp8` (stock vLLM, halves KV cache size) which should allow approximately 40–48K context. The patched TurboQuant stack remains an option if even more context is needed and the operational overhead of maintaining a patched vLLM is acceptable.
