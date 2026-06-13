# HermesYoutubeCurator

A personal YouTube recommendation curator that runs as a [Hermes Agent](https://hermes-agent.nousresearch.com) cron job. Each morning it browses *your* logged-in YouTube home feed and watch history, decides what's actually worth your time, and sends a tiered digest to Telegram — then quietly grows a small personal wiki of the topics and channels you keep coming back to.

It is **not a clone-and-run app.** Like other Hermes projects (e.g. [`vigil-crest`](https://github.com/earlgreyhot1701D/vigil-crest)), it's a *configured personal setup*: you bring your own Hermes install, model, Telegram bot, and YouTube login. This repo is the recipe and the portable parts; [`INSTALL.md`](INSTALL.md) is the step-by-step runbook that wires them into your Hermes install.

## What it does

Every run (default 08:00 daily):

1. **Collects** — a headless-ish Chrome session (your logged-in profile, driven over CDP) scrapes your YouTube home feed + watch history into a local raw "wiki" layer. Deterministic; no LLM.
2. **Curates** — the agent reads bounded slices of that raw evidence and produces a three-tier Telegram digest (🧠 Pure learning / 🎤 Infotainment / 🍿 Pure entertainment) with durations and a transcript-grounded "Why" per pick.
3. **Enriches** — durable `entities/` and `concepts/` wiki pages accrete from what you watch, so the curator's taste model improves over time.

## How it works

```
cron (08:00)
  └─ youtube-curator-collect.sh         # launches Chrome (CDP) + runs the collector
        └─ refresh-home / refresh-history  (deterministic scrape → raw/ wiki layer)
  └─ Hermes agent (the "curator"), loading the youtube-curator skill
        ├─ reads bounded `recent` slices of the raw evidence
        ├─ delegates → TRANSCRIPT subagent   (terminal): fetch+save+summarize picks
        ├─ delegates → WIKI-ENRICHER subagent (file):    writes entities/ & concepts/
        └─ writes the 3-tier digest  ──► Telegram
```

Two heavy/untrusted jobs are isolated into delegated subagents so they never enter the curator's context. A `pre_tool_call` guard plugin (`curator-subagent-guard`) hard-restricts those subagents: the transcript one may *only* run the `fetch-transcript` command; the enricher may *only* write under the wiki's `entities/`/`concepts/` dirs — defense-in-depth against prompt injection from untrusted transcript text. See [deploy/plugins/curator-subagent-guard/](deploy/plugins/curator-subagent-guard/).

## Prerequisites

- **Hermes Agent** installed, with a model connected and a **Telegram** bot + home channel. (Any Hermes-supported model works; this build was developed against local vLLM — Gemma-4-12B / Qwen3.5-9B.) Don't have these yet? [`INSTALL.md` → Step 0](INSTALL.md) has the checks and the official sources for [installing Hermes](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart), [connecting a model](https://hermes-agent.nousresearch.com/docs/user-guide/configuration), and [setting up the Telegram gateway](https://hermes-agent.nousresearch.com/docs/user-guide/messaging).
- **`uv`** (https://docs.astral.sh/uv/) for the Python env.
- **Google Chrome** — used for the logged-in scrape; Playwright connects to it over CDP, so no extra browser download is needed. The launcher auto-detects it on `PATH` (`google-chrome`/`chrome`/`chromium`) or in the standard macOS/Windows install location.
- Python ≥ 3.11.

## Setup

```bash
git clone <this-repo> && cd HermesYoutubeCurator
```

Then follow **[`INSTALL.md`](INSTALL.md)** — a verify-as-you-go runbook (each step says what it's for, what to run, and how to check it). You can run it yourself or hand the whole file to your agent. It does the mechanical wiring:

- `uv sync` → builds `.venv` with the package + Playwright
- deploys the launcher to `~/.hermes/scripts/` (cron requires scripts there)
- deploys the guard plugin to `~/.hermes/plugins/` (substituting your wiki path)
- deploys the skill to `~/.hermes/skills/youtube-curator/`
- creates the cron job and sets its `enabled_toolsets` (`terminal`, `delegation`, `file`)

…and walks you through the **manual steps only you can do**:

1. **Enable the guard** in `~/.hermes/config.yaml`:
   ```yaml
   plugins:
     enabled:
       - curator-subagent-guard
   ```
2. **Log into YouTube once** in the scraping profile:
   ```bash
   .venv/bin/python scripts/launch_youtube_browser.py
   ```
   Sign in on the Chrome window that opens, then close it. The cron reuses that logged-in profile (at `.local/state/hermes-youtube-curator/chrome-profile`) to read your personalised feed.
3. Confirm a **model + Telegram** are connected in Hermes.
4. **Restart the gateway** so the plugin + job load: `hermes gateway restart`.
5. **Test:** run the `YouTube Curator` job from `hermes cron list`.

## Repo layout

```
src/hermes_youtube_curator/        # the Python package (collectors, CLI, persistence)
  cli/collector.py                 #   refresh-home / refresh-history / recent / fetch-transcript
scripts/launch_youtube_browser.py  # launches the logged-in Chrome (CDP) profile
skills/youtube-curator/SKILL.md    # the curator skill (Hub/agentskills.io-compatible)
deploy/
  youtube-curator-collect.sh       # cron launcher (source of truth; @@REPO@@ templated)
  plugins/curator-subagent-guard/  # the security guard plugin (source of truth)
INSTALL.md                         # runbook that wires all of the above into ~/.hermes/
```

The repo is the single source of truth; following [`INSTALL.md`](INSTALL.md) copies the deployable parts into `~/.hermes/`. State (the wiki, the Chrome profile, raw events) lives under `.local/state/` and is git-ignored.

## Notes & limitations

- **Browser-in-cron is the hard part.** Scraping a *personalised* feed needs a real logged-in browser; there's no API for it. We drive a persistent Chrome profile over CDP, which runs reliably under the scheduler (a fresh-headless-per-run approach does not).
- **Model tool-calling matters.** The flow leans on reliable structured tool-calls (two delegations per run). Local models vary: Qwen3.5-9B was reliable; Gemma-4-12B occasionally leaks reasoning-channel tags into output. Pick a model with solid tool-call support.
- **Agent config knobs.** Two settings in `~/.hermes/config.yaml` were essential to stop a local model from runaway tool-loops — set them if you see the agent spinning:
  ```yaml
  agent:
    tool_use_enforcement: false   # don't force a tool call every turn
    reasoning_effort: low
  ```
- **Memory is off for scheduled runs**, so durable taste/format preferences live in the skill, not long-term memory.
- **`uv.lock` is git-ignored by default.** For a reproducible app install you may want to commit it (un-ignore in `.gitignore`) so `uv sync` resolves the exact same dependency versions everywhere.
