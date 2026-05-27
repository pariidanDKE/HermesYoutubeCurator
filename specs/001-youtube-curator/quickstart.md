# Quickstart: YouTube Curator

## 1. Prepare the environment

- Install Python 3.11+.
- Install Hermes Agent and confirm the CLI is available.
- Install browser automation dependencies required for Playwright.
- Prepare access to YouTube Data API v3 for metadata enrichment.
- Prepare transcript access through `youtube-transcript-api`.
- Prepare the local reasoning stack with vLLM plus a Qwen/Qwen3.6-27B-class model.
- Prepare a deterministic scheduler such as cron or a systemd timer for the morning run.

## 2. Verify current dependency guidance before coding

- Record the current docs or upstream/source references for Playwright, Hermes Agent, the YouTube Data API client, `youtube-transcript-api`, vLLM, and Hermes Telegram delivery.
- Prefer official docs or upstream source over memory when confirming setup steps or runtime behavior.

## 3. Configure the project

- Create local configuration for:
  - signed-in browser profile or session strategy for YouTube
  - metadata enrichment credentials
  - local model endpoint details
  - storage paths for SQLite and JSON artifacts
  - scheduler configuration for the recurring run
  - Hermes Telegram delivery target
- Keep configuration outside committed source where secrets are involved.
- Prefer a deep-module layout where `pipeline` orchestrates, `youtube` owns YouTube evidence gathering and enrichment, `curation` owns Hermes-backed decisions and digest generation, `persistence` owns SQLite and artifact storage, and `delivery` owns Telegram transport.

## 4. Configure delivery

- Run Telegram bot setup for Hermes.
- Configure the primary Telegram chat or channel for digest delivery.
- Confirm Hermes can deliver a simple test message to the target.

## 5. Validate deterministic extraction

- Run the homepage refresh entrypoint to capture a recommendation snapshot.
- Run the history refresh entrypoint to capture a recent watch-history snapshot.
- Confirm both snapshots are stored as JSON artifacts and that partial failures are visible rather than silent.

## 6. Validate enrichment selection

- Run the enrichment-selection entrypoint against the newest snapshots.
- Confirm it chooses a subset of video IDs for deeper enrichment.
- Confirm the recorded reasons reflect recommendation context, recent watch history, and persistent preference memory.
- Confirm the selection behavior is tested through the `curation` interface rather than through a standalone shallow `select` package.

## 7. Validate enrichment

- Run the enrichment step against the selected video identifiers.
- Confirm that descriptions are attached when available.
- Confirm that transcripts are attached when available and that missing transcripts are handled gracefully.
- Confirm the collection and enrichment behaviors both sit behind the `youtube` interface rather than being split into separate top-level stage packages.

## 8. Validate Hermes curation

- Register the single curator skill with Hermes.
- Execute a manual curator run that:
  - loads the newest snapshots and enrichment-selection output
  - checks whether meaningful changes justify curation
  - generates a digest, summaries, and idea proposals
  - produces memory proposals instead of auto-writing persistent taste memory

## 9. Validate delivery

- Deliver the generated digest to the configured Telegram target.
- Confirm delivery outcomes are stored as structured records.
- Confirm Telegram transport details stay inside the `delivery` boundary and are not exposed to `curation` or `pipeline` callers.

## 10. Validate scheduled operation

- Configure cron, a systemd timer, or an equivalent scheduler to trigger the recurring run.
- Run several representative manual or scheduled cycles.
- Confirm that the digest reflects:
  - homepage recommendations
  - recent watch-history recency signals
  - selective deep enrichment of the most promising candidates
  - richer metadata such as descriptions and transcripts when available
  - Hermes-driven synthesis, reporting, and Telegram delivery

## 11. Evaluate challenge fit

- Confirm that Hermes is doing substantive work at the heart of the project:
  - enrichment selection
  - curation
  - delivery
  - memory
  - skill execution
  - recurring reports
  - long-term taste modeling
- Confirm the deterministic scripts remain the sensor and execution layer rather than the decision-making center for infrastructure concerns.
- Confirm top-level packages reflect real dependency boundaries rather than mirroring every CLI subcommand.
