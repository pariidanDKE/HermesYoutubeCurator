# Installing HermesYoutubeCurator

This is **not a clone-and-run app.** It's a *configured personal setup* that wires
this repo into your own [Hermes Agent](https://hermes-agent.nousresearch.com)
install: a daily cron job that scrapes *your* logged-in YouTube feed, curates it,
and sends a Telegram digest. You bring the Hermes install, the model, the Telegram
bot, and the YouTube login; this repo is the recipe and the portable parts.

## Two ways to use this document

- **Do it yourself** — read top to bottom and run each step. Every step says what
  it's *for*, what to *run*, and how to *check* it worked.
- **Hand it to your agent** — paste this whole file into your Hermes (or any
  coding) agent: *"Here's an install runbook for this repo. Work through it,
  verifying each step, and stop at every 🧑 marker to ask me."* The agent handles
  the fiddly parts (path substitution, editing `jobs.json`) for you.

### Legend

- **🧑 USER ACTION REQUIRED** — a step only a human can do (a login, a credential,
  a judgment call). **If you are an agent executing this runbook, do not attempt
  it — pause and ask your user to do it, then continue once they confirm.**
- **✅ Verify** — a quick check that the step actually worked before moving on.

Throughout, `<REPO>` means the **absolute path** to this cloned repo (run `pwd`
from the repo root to get it), and `<HERMES_HOME>` means your Hermes home
(`~/.hermes` unless you set `HERMES_HOME`).

---

## Prerequisites

Before anything below, confirm these exist:

- **Hermes Agent**, already set up with a connected model and a Telegram bot +
  home channel. (Any Hermes-supported model works; this was built against local
  vLLM — pick a model with reliable tool-calling, the flow does two delegations
  per run.)
- **`uv`** — https://docs.astral.sh/uv/ (manages the Python env). Install it
  **standalone** (the official installer: `curl -LsSf https://astral.sh/uv/install.sh | sh`),
  **not** through pyenv/`pip install uv` inside a Python env. A pyenv-shimmed `uv`
  lets pyenv read this repo's `.python-version` *first* and demand an exact
  installed version, which breaks `uv sync` in step 1.
- **Google Chrome** — used for the logged-in scrape over CDP; no separate browser
  download needed. The step-8 launcher auto-detects it on `PATH`
  (`google-chrome`/`chrome`/`chromium`) or in the standard macOS
  (`/Applications/Google Chrome.app`) and Windows (`Program Files`) install
  location.
- **Python ≥ 3.11.**

✅ Verify:
```bash
command -v uv && command -v hermes
test -d "${HERMES_HOME:-$HOME/.hermes}" && echo "hermes home OK"
```
Chrome isn't checked here — its binary name/location differs per OS; step 8's
launcher auto-detects it and errors clearly if it's missing.

> **Platform note.** Written for Linux/macOS, where every command below runs
> as-is. **macOS** works unchanged. **WSL2** behaves like Linux. **Native
> Windows** runs these through the Git Bash that Hermes bundles, but with two
> swaps: use `.venv/Scripts/python.exe` (not `.venv/bin/python`), and your Hermes
> home is `%LOCALAPPDATA%\hermes` (not `~/.hermes`). WSL2 is the smoother Windows
> route.

### Step 0 — Is Hermes itself ready?  🧑 USER ACTION REQUIRED

This repo is a *recipe layered onto a working Hermes install* — it does **not**
install Hermes, pick a model, or create your Telegram bot. Those involve
credentials and OAuth, so **if you're an agent, run the checks below, then for
anything missing, hand the linked source to your user and pause** — don't install
Hermes or wire up keys yourself.

| Need | Check (exit 0 / shows config = ready) | If missing → source |
|------|----------------------------------------|---------------------|
| **Hermes installed** | `command -v hermes` | One-liner install + first run: [Quickstart](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart). Linux/macOS/WSL2: `curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh \| bash` · Windows (beta): `iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)` |
| **A model connected** (tool-calling capable) | `hermes model` lists a current provider/model | Pick one interactively with `hermes model`, or see [Configuration → providers/models](https://hermes-agent.nousresearch.com/docs/user-guide/configuration). Want one subscription for model + tools instead of per-provider keys? [Nous Portal](https://portal.nousresearch.com) ([Tool Gateway docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/tool-gateway)). |
| **Telegram gateway up** | `hermes gateway status` shows running, with `telegram` connected | Create the bot + home channel and connect it: `hermes gateway setup`, then `hermes gateway start` (or `run` in the foreground on WSL). Full walkthrough: [Messaging Gateway guide](https://hermes-agent.nousresearch.com/docs/user-guide/messaging). |

> Top-level docs index: [hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/).
> Once all three checks pass (Hermes on `PATH`, a model selected, gateway running
> with Telegram connected), continue with the Prerequisites verify above and the
> numbered steps below.

---

## 1. Build the Python environment

**Goal:** create the repo's virtualenv with the package + Playwright. The launcher
runs the package from *this* venv, not system Python.

**Do:**
```bash
cd <REPO>
uv sync
```

✅ Verify: `test -x <REPO>/.venv/bin/python && echo OK`

---

## 2. Deploy the cron launcher

**Goal:** Hermes runs cron scripts from `<HERMES_HOME>/scripts/`, so the launcher
must live there with your real repo path baked in (it ships with a `@@REPO@@`
placeholder).

**Do:** copy `deploy/youtube-curator-collect.sh` into `<HERMES_HOME>/scripts/`,
replacing every `@@REPO@@` with `<REPO>`, and make it executable:
```bash
mkdir -p "$HOME/.hermes/scripts"
sed "s|@@REPO@@|$(pwd)|g" deploy/youtube-curator-collect.sh \
    > "$HOME/.hermes/scripts/youtube-curator-collect.sh"
chmod +x "$HOME/.hermes/scripts/youtube-curator-collect.sh"
```

✅ Verify: `grep -c @@REPO@@ "$HOME/.hermes/scripts/youtube-curator-collect.sh"`
prints `0` (no placeholders left).

---

## 3. Deploy the guard plugin

**Goal:** the `curator-subagent-guard` plugin hard-restricts the curator's
delegated subagents (defense against prompt-injection from untrusted transcripts).
It ships with a `@@WIKI_PATH@@` placeholder for your wiki location.

**Do:** copy the plugin into `<HERMES_HOME>/plugins/`, substituting the wiki path:
```bash
WIKI="$(pwd)/.local/state/hermes-youtube-curator/wiki"
DST="$HOME/.hermes/plugins/curator-subagent-guard"
mkdir -p "$DST"
sed "s|@@WIKI_PATH@@|$WIKI|g" deploy/plugins/curator-subagent-guard/__init__.py > "$DST/__init__.py"
cp deploy/plugins/curator-subagent-guard/plugin.yaml "$DST/plugin.yaml"
```

✅ Verify: `grep -c @@WIKI_PATH@@ "$DST/__init__.py"` prints `0`. (The guard finds
the curator *cron job* itself, by skill name — no job id to substitute.)

> **Why not `hermes plugins install`?** That command clones a *standalone Git
> repo* verbatim — but this guard is an in-repo plugin that needs its
> `@@WIKI_PATH@@` placeholder substituted with your wiki path at deploy time,
> which a clone can't do. The manual copy above is the right fit here. (You'd only
> use `hermes plugins install` if the guard were split into its own repo and made
> env-var-only via `HYC_WIKI_PATH` — see the note at the end.)

---

## 4. Deploy the skill

**Goal:** the curator agent loads the `youtube-curator` skill each run; Hermes
discovers skills under `<HERMES_HOME>/skills/`. The skill's transcript-fetch
command ships with a `@@REPO@@` placeholder (the curator `cd`s into the repo to
run the collector from its venv), so it must be substituted at deploy time — just
like the launcher in step 2.

**Do:** copy the skill into `<HERMES_HOME>/skills/`, replacing every `@@REPO@@`
with `<REPO>`:
```bash
DST="$HOME/.hermes/skills/youtube-curator"
mkdir -p "$DST"
cp -r skills/youtube-curator/. "$DST/"
# bake the real repo path into the transcript-fetch command
find "$DST" -type f -name '*.md' -exec \
    sed -i '' "s|@@REPO@@|$(pwd)|g" {} +   # Linux/WSL: drop the '' after -i
```

✅ Verify: `test -f "$DST/SKILL.md" && echo OK` and
`grep -rc @@REPO@@ "$DST"` prints `0` (no placeholders left).

---

## 5. Create the cron job

**Goal:** schedule the daily run (08:00) that launches the collector script, then
hands off to the curator agent.

**Do** (skip if a job named `YouTube Curator` already exists):
```bash
hermes cron create "0 8 * * *" \
  "Read the collector output above: it lists the wiki/raw paths for this run. Follow the youtube-curator skill to read recent recommendation and watch-history evidence and produce the Telegram digest in the skill's format. If collection failed or evidence is sparse, send a short partial digest." \
  --name "YouTube Curator" \
  --skill youtube-curator \
  --script youtube-curator-collect.sh \
  --deliver telegram \
  --workdir "$(pwd)"
```

✅ Verify: `hermes cron list` shows a **YouTube Curator** job.

---

## 6. Grant the job its toolsets

**Goal:** the job needs three toolsets — `terminal` (collector + transcript
commands), `delegation` (subagents), and `file` (the enricher's reads/writes).
`hermes cron create` has no flag for this, so it's set directly in `jobs.json`.

**Do:** add `["terminal", "delegation", "file"]` as the `enabled_toolsets` of the
`YouTube Curator` job in `<HERMES_HOME>/cron/jobs.json`. If you're following along
by hand, this snippet does it safely:
```bash
python3 - "$HOME/.hermes/cron/jobs.json" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path))
for job in data.get("jobs", []):
    if job.get("name") == "YouTube Curator":
        job["enabled_toolsets"] = ["terminal", "delegation", "file"]
json.dump(data, open(path, "w"), indent=2)
print("set enabled_toolsets")
PY
```

✅ Verify: the `YouTube Curator` entry in `jobs.json` lists all three toolsets.

---

## 7. Enable the guard plugin  🧑 USER ACTION REQUIRED

> Enabling a plugin changes what runs in your Hermes install. **If you're an
> agent: confirm with the user before enabling it.**

**Goal:** a deployed plugin does nothing until it's enabled.

**Do:**
```bash
hermes plugins enable curator-subagent-guard
```

Or, equivalently, add it under `plugins.enabled` in `<HERMES_HOME>/config.yaml`:
```yaml
plugins:
  enabled:
    - curator-subagent-guard
```

✅ Verify: `hermes plugins list` shows `curator-subagent-guard` as **enabled**.

---

## 8. Log into YouTube once  🧑 USER ACTION REQUIRED

> **If you're an agent: you cannot do this — it requires the user's Google
> credentials in an interactive browser. Ask your user to run the command below
> and sign in, then tell you when they've closed the window.**

**Goal:** the scraper reads your *personalised* feed, so it needs your logged-in
Chrome profile. You sign in once; the cron reuses that profile thereafter.

**Do:**
```bash
.venv/bin/python scripts/launch_youtube_browser.py
```
Sign in on the Chrome window that opens, confirm you can see your normal YouTube
home feed, then close the window.

✅ Verify: a profile exists at
`<REPO>/.local/state/hermes-youtube-curator/chrome-profile/`.

---

## 9. Confirm model + Telegram  🧑 USER ACTION REQUIRED

> **If you're an agent: ask your user to confirm these are connected — you can't
> verify their model/Telegram credentials for them.**

**Goal:** the digest is delivered over Telegram by a tool-calling model; both must
already be wired into Hermes (see Prerequisites).

**Do:** confirm in Hermes that a model is connected and the Telegram bot + home
channel work (e.g. send yourself a test message).

✅ Verify: user confirms model responds and Telegram delivers.

---

## 10. Restart the gateway  🧑 USER ACTION REQUIRED

> **If you're an agent: restarting the gateway interrupts any live Hermes session.
> Ask your user before doing it.**

**Goal:** load the newly-deployed plugin and job.

**Do:**
```bash
hermes gateway restart
```

✅ Verify: `hermes gateway status` shows it running.

---

## 11. Test the run

**Goal:** confirm the whole pipeline works end to end.

**Do:** run the `YouTube Curator` job once from `hermes cron list` (or trigger it
however your Hermes exposes manual runs).

✅ Verify, in order:
- The collector logs print `wiki_path=…` plus the `*_path=` lines (transcripts,
  entities, concepts, interests, agent_guide, user_memory).
- A digest arrives in your Telegram home channel.
- `<REPO>/.local/state/hermes-youtube-curator/wiki/interests.md` has gained
  content (the enricher ran and wrote the taste profile).

---

## Troubleshooting

- **Agent spins in tool-loops / leaks reasoning tags.** Some local models need
  these knobs in `<HERMES_HOME>/config.yaml`:
  ```yaml
  agent:
    tool_use_enforcement: false   # don't force a tool call every turn
    reasoning_effort: low
  ```
- **No personalised feed / login lost.** Re-run step 8; the Chrome profile may
  have been cleared or signed out.
- **Chrome won't start under cron.** Check
  `<REPO>/.local/state/hermes-youtube-curator/youtube-browser.log`.
- **Enricher writes get blocked.** The guard only allows writes under the wiki's
  `entities/`/`concepts/` dirs and the root files `interests.md`/`index.md`/
  `log.md`. Make sure the curator hands the enricher the **absolute** paths the
  launcher printed, verbatim.
- **Digest never arrives.** Re-check steps 6 (toolsets), 7 (guard enabled), and 9
  (Telegram); look at the job's run logs in Hermes.

---

## Appendix: publishing the guard as a standalone plugin (optional)

The guard is deployed here as an **in-repo plugin** (step 3) because it needs its
`@@WIKI_PATH@@` placeholder substituted at deploy time — so the one-command
`hermes plugins install owner/repo` (which clones a Git repo verbatim) doesn't
apply. If you'd rather get the native one-command install, you can convert it:

1. **Drop the placeholder, go env-var-only.** The guard already falls back to
   `HYC_WIKI_PATH` (`_WIKI_ROOT = os.environ.get("HYC_WIKI_PATH") or "@@WIKI_PATH@@"`).
   Remove the placeholder and require `HYC_WIKI_PATH` to be set **in the gateway's
   environment** (where the hook runs — not just the cron launcher's).
2. **Move it to its own Git repo** (just the `curator-subagent-guard/` dir).
3. Install + enable in one step:
   ```bash
   hermes plugins install <owner>/curator-subagent-guard --enable
   ```

Trade-off: you swap a `sed` + copy for a new requirement (a gateway-level env
var). Worth it only if you want to distribute the guard independently; for a
single personal setup, the in-repo copy in step 3 is simpler.
