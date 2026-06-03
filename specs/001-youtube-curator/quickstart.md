# Quickstart: YouTube Curator

## 1. Configure local state

- Copy `.env.example` values into your shell or local env file.
- Point `HYC_HOME_FIXTURE` and `HYC_HISTORY_FIXTURE` at real collected artifacts or keep the sample `tests/fixtures/*.json` files for smoke testing.
- Keep `HYC_SCHEDULER=hermes-cron` unless you intentionally switch to OS cron or systemd.
- Optional: set `HYC_WIKI_PATH` to choose the Hermes-compatible wiki root. By default it is `.local/state/hermes-youtube-curator/wiki`.

## 2. Prepare Hermes

- Install the repo-local skill by copying `skills/youtube-curator/SKILL.md` into `~/.hermes/skills/youtube-curator/SKILL.md`.
- Keep the bundled `youtube-content` Hermes skill enabled; it is the preferred transcript workflow for curator summarization guidance.
- Configure Hermes Telegram delivery before live scheduled runs; Telegram delivery is handled by Hermes cron, not by this Python package.

## 3. Run the deterministic pipeline

- Homepage snapshot: `python3 -m hermes_youtube_curator.cli.main refresh-home`
- History snapshot: `python3 -m hermes_youtube_curator.cli.main refresh-history`

These two commands are the entire Python surface: they collect evidence into the wiki raw/index layer. Enrichment selection and transcript/metadata enrichment are owned by Hermes at curation time, not by Python CLI commands.

## 4. Expected behavior

- Artifacts are written under `HYC_ARTIFACT_DIR` as JSON.
- Operational video, recommendation, and watch-history indexes are written under `HYC_WIKI_PATH/raw/curator/`.
- Hermes Agent owns digest generation and Telegram delivery during the cron run.
- Missing history, descriptions, or transcripts produce explicit partial warnings instead of aborting the entire run.
- There is no snapshot-skip branch in the normal path. Curation runs whenever enough evidence exists.

## 5. Scheduling

- Preferred path: Hermes cron.
- Hermes cron runs scripts from `~/.hermes/scripts/`; copy `scripts/youtube_curator_refresh_for_hermes.sh` there as `youtube-curator-refresh.sh`.
- Do not use `--no-agent` for the curator job. The script refreshes raw wiki evidence, then Hermes Agent uses that script output as context and delivers the final digest.
- Example: `hermes cron create "0 8 * * *" --name youtube-curator --script youtube-curator-refresh.sh --skill youtube-curator --workdir /home/dan-parii/Documents/HermesYoutubeCurator --deliver telegram "After the script refreshes the YouTube curator raw wiki files, read the paths in Script Output and produce a concise Telegram digest with watch/save/skip recommendations, history influence notes, and explicit memory proposals only. Do not modify YouTube."`

## 6. Guardrails

- Keep transcript work on the bundled `youtube-content` path plus this repo’s explicit curator skill guidance.
- Do not add MCP for enrichment in the normal path.
- Keep long-term preference changes as digest proposals until an explicit approval workflow is added.

## 7. Validation

- Smoke check: run `python3 -m hermes_youtube_curator.cli.main refresh-home` and `python3 -m hermes_youtube_curator.cli.main refresh-history` with the sample fixtures from `.env.example`.
- Verification command: `uv run --with pytest --with ruff sh -lc 'ruff check . && pytest'`
