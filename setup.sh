#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# HermesYoutubeCurator — one-shot setup.
#
# Wires the repo into a local Hermes Agent install: builds the venv, deploys
# the launcher + guard plugin + skill into ~/.hermes/, and creates the cron job.
# Idempotent-ish: safe to re-run (it won't create a duplicate cron job).
#
# It does NOT do the things only you can do — log into YouTube, connect a
# Telegram bot, pick a model. Those are printed as manual steps at the end.
# ---------------------------------------------------------------------------

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
STATE="$REPO/.local/state/hermes-youtube-curator"
WIKI="$STATE/wiki"
JOB_NAME="YouTube Curator"
JOB_PROMPT="Read the collector output above: it lists the wiki/raw paths for this run. Follow the youtube-curator skill to read recent recommendation and watch-history evidence and produce the Telegram digest in the skill's format. If collection failed or evidence is sparse, send a short partial digest."

say()  { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m! %s\033[0m\n' "$*"; }

# ---------------------------------------------------------------------------
# 1. Prerequisites
# ---------------------------------------------------------------------------
say "Checking prerequisites"
command -v uv      >/dev/null || { echo "Missing 'uv' (https://docs.astral.sh/uv/). Install it and re-run." >&2; exit 1; }
command -v hermes  >/dev/null || { echo "Missing 'hermes' CLI. Install Hermes Agent first." >&2; exit 1; }
command -v google-chrome >/dev/null || command -v google-chrome-stable >/dev/null || \
  warn "google-chrome not found on PATH — the YouTube scraper needs it (see README)."
[ -d "$HERMES_HOME" ] || { echo "No Hermes home at $HERMES_HOME. Run the Hermes setup wizard first." >&2; exit 1; }
echo "repo:    $REPO"
echo "hermes:  $HERMES_HOME"

# ---------------------------------------------------------------------------
# 2. Python environment (uv-managed venv with the package + playwright)
# ---------------------------------------------------------------------------
say "Building the repo virtualenv (uv sync)"
( cd "$REPO" && uv sync )

# ---------------------------------------------------------------------------
# 3. Deploy launcher into ~/.hermes/scripts/  (cron requires scripts there)
# ---------------------------------------------------------------------------
say "Deploying the cron launcher"
mkdir -p "$HERMES_HOME/scripts"
sed "s|@@REPO@@|$REPO|g" "$REPO/deploy/youtube-curator-collect.sh" \
    > "$HERMES_HOME/scripts/youtube-curator-collect.sh"
chmod +x "$HERMES_HOME/scripts/youtube-curator-collect.sh"
echo "-> $HERMES_HOME/scripts/youtube-curator-collect.sh"

# ---------------------------------------------------------------------------
# 4. Deploy guard plugin into ~/.hermes/plugins/  (wiki path substituted)
# ---------------------------------------------------------------------------
say "Deploying the curator-subagent-guard plugin"
GUARD_DST="$HERMES_HOME/plugins/curator-subagent-guard"
mkdir -p "$GUARD_DST"
sed "s|@@WIKI_PATH@@|$WIKI|g" "$REPO/deploy/plugins/curator-subagent-guard/__init__.py" \
    > "$GUARD_DST/__init__.py"
cp "$REPO/deploy/plugins/curator-subagent-guard/plugin.yaml" "$GUARD_DST/plugin.yaml"
echo "-> $GUARD_DST/"

# ---------------------------------------------------------------------------
# 5. Deploy the skill into ~/.hermes/skills/
# ---------------------------------------------------------------------------
say "Deploying the youtube-curator skill"
SKILL_DST="$HERMES_HOME/skills/youtube-curator"
mkdir -p "$SKILL_DST"
cp -r "$REPO/skills/youtube-curator/." "$SKILL_DST/"
echo "-> $SKILL_DST/"

# ---------------------------------------------------------------------------
# 6. Create the cron job (skip if a job with this name already exists)
# ---------------------------------------------------------------------------
say "Creating the cron job"
if hermes cron list 2>/dev/null | grep -qF "$JOB_NAME"; then
  echo "A job named '$JOB_NAME' already exists — leaving it as-is."
else
  hermes cron create "0 8 * * *" "$JOB_PROMPT" \
    --name "$JOB_NAME" \
    --skill youtube-curator \
    --script youtube-curator-collect.sh \
    --deliver telegram \
    --workdir "$REPO"
fi

# ---------------------------------------------------------------------------
# 7. Grant the job its toolsets (cron create has no --toolsets flag, so we
#    patch jobs.json directly — it's JSON, stdlib only).
#    terminal = the collect/transcript commands; delegation = subagents;
#    file = the wiki-enricher subagent's read/write tools.
# ---------------------------------------------------------------------------
say "Setting enabled_toolsets on the job"
JOBS_JSON="$HERMES_HOME/cron/jobs.json"
if [ -f "$JOBS_JSON" ]; then
  python3 - "$JOBS_JSON" "$JOB_NAME" <<'PY'
import json, sys
path, name = sys.argv[1], sys.argv[2]
data = json.load(open(path))
want = ["terminal", "delegation", "file"]
changed = False
for job in data.get("jobs", []):
    if job.get("name") == name and job.get("enabled_toolsets") != want:
        job["enabled_toolsets"] = want
        changed = True
if changed:
    json.dump(data, open(path, "w"), indent=2)
    print(f"  set enabled_toolsets={want}")
else:
    print("  already set (or job not found)")
PY
else
  warn "No jobs.json at $JOBS_JSON yet — re-run after the gateway has written it."
fi

# ---------------------------------------------------------------------------
# 8. Point at the README for the manual steps (the things only you can do)
# ---------------------------------------------------------------------------
say "Mechanical setup done."
echo "Now finish the MANUAL steps in README.md (\"Setup\" section): enable the"
echo "guard plugin, log into YouTube once, confirm model + Telegram, restart the"
echo "gateway, then run the job."
