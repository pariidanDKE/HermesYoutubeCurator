# Quickstart: YouTube Curator

## 1. Prepare the environment

- Install Python 3.11+.
- Install Hermes Agent and confirm the CLI is available.
- Install browser automation dependencies required for Playwright.
- Prepare access to YouTube Data API v3 for metadata enrichment.
- Prepare transcript access through `youtube-transcript-api`.
- If using the preferred local reasoning stack, prepare vLLM plus a Qwen/Qwen3.6-27B-class model.

## 2. Configure the project

- Create local configuration for:
  - signed-in browser profile or session strategy for YouTube
  - metadata enrichment credentials
  - local model endpoint details
  - optional remote fallback model credentials
  - storage paths for SQLite and JSON artifacts
- Keep configuration outside committed source where secrets are involved.

## 3. Validate deterministic extraction

- Run the homepage refresh entrypoint to capture a recommendation snapshot.
- Run the history refresh entrypoint to capture a recent watch-history snapshot.
- Confirm both snapshots are stored as JSON artifacts and that partial failures are visible rather than silent.

## 4. Validate enrichment

- Run the enrichment step against collected video identifiers.
- Confirm that descriptions are attached when available.
- Confirm that transcripts are attached when available and that missing transcripts are handled gracefully.

## 5. Validate Hermes orchestration

- Register the curator skills with Hermes.
- Execute a manual curator run that:
  - loads the newest snapshots
  - checks whether meaningful changes justify curation
  - generates a digest, summaries, and idea proposals
  - produces memory proposals instead of auto-writing persistent taste memory

## 6. Validate scheduled operation

- Configure Hermes scheduled execution or an equivalent scheduler to trigger periodic refresh and curation.
- Run several representative manual or scheduled cycles.
- Confirm that the digest reflects:
  - homepage recommendations
  - recent watch-history recency signals
  - richer metadata such as descriptions and transcripts when available
  - Hermes-driven synthesis, reporting, and memory proposals

## 7. Evaluate challenge fit

- Confirm that Hermes is doing substantive work at the heart of the project:
  - orchestration
  - memory
  - skill execution
  - recurring reports
  - long-term taste modeling
- Confirm the deterministic scripts remain the sensor layer rather than the decision-making center.
