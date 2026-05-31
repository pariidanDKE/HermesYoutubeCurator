# Quickstart: YouTube Curator

## 1. Configure local state

- Copy `.env.example` values into your shell or local env file.
- Point `HYC_HOME_FIXTURE`, `HYC_HISTORY_FIXTURE`, and `HYC_ENRICHMENT_FIXTURE` at real collected artifacts or keep the sample `tests/fixtures/*.json` files for smoke testing.
- Keep `HYC_SCHEDULER=hermes-cron` unless you intentionally switch to OS cron or systemd.
- Optional: set `HYC_WIKI_PATH` to choose the Hermes-compatible wiki root. By default it is `.local/state/hermes-youtube-curator/wiki`.

## 2. Prepare Hermes

- Install the repo-local skill with `scripts/setup_hermes_curator.sh`.
- Keep the bundled `youtube-content` Hermes skill enabled; it is the preferred transcript workflow for curator summarization guidance.
- Configure Hermes Telegram delivery before live runs. The current repo implementation also supports a deterministic outbox file path via `HYC_TELEGRAM_OUTBOX` for dry-run validation.

## 3. Run the deterministic pipeline

- Homepage snapshot: `python3 -m hermes_youtube_curator.cli.main refresh-home`
- History snapshot: `python3 -m hermes_youtube_curator.cli.main refresh-history`
- Selection: `python3 -m hermes_youtube_curator.cli.main select-enrichment`
- Enrichment: `python3 -m hermes_youtube_curator.cli.main enrich-videos`
- Curation: `python3 -m hermes_youtube_curator.cli.main run-curator`
- Full run: `python3 -m hermes_youtube_curator.cli.main morning-run`

## 4. Expected behavior

- Artifacts are written under `HYC_ARTIFACT_DIR` as JSON.
- Operational video, recommendation, and watch-history indexes are written under `HYC_WIKI_PATH/raw/curator/`.
- Existing run/digest/delivery SQLite scaffolding still writes to `HYC_SQLITE_PATH` while downstream Hermes delivery work is unfinished.
- Missing history, descriptions, or transcripts produce explicit partial warnings instead of aborting the entire run.
- There is no snapshot-skip branch in the normal path. Curation runs whenever enough evidence exists.

## 5. Scheduling

- Preferred path: Hermes cron.
- Example: `hermes cron add "0 8 * * *" -- python3 -m hermes_youtube_curator.cli.main morning-run`
- Fallback operator examples live in `ops/cron/youtube-curator.cron` and `ops/systemd/`.

## 6. Guardrails

- Keep transcript work on the bundled `youtube-content` path plus this repo’s explicit curator skill guidance.
- Do not add MCP for enrichment in the normal path.
- Keep long-term preference changes as digest proposals until an explicit approval workflow is added.

## 7. Validation

- Smoke check: run `python3 -m hermes_youtube_curator.cli.main morning-run` with the sample fixtures from `.env.example`.
- Verification command: `uv run --with pytest --with ruff sh -lc 'ruff check . && pytest'`
