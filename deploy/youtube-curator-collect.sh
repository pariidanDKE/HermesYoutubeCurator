#!/usr/bin/env bash
set -euo pipefail

# Hermes cron launcher for the YouTube Curator collector.
#
# This is the SOURCE OF TRUTH. setup.sh copies it into ~/.hermes/scripts/
# (cron requires scripts to live there) and substitutes @@REPO@@ with the
# real repo path. It invokes the Python package in the repo via the repo's
# own uv-managed virtualenv (the package is NOT on system python3).

REPO="@@REPO@@"
VENV_PY="$REPO/.venv/bin/python"
STATE="$REPO/.local/state/hermes-youtube-curator"
WIKI="$STATE/wiki"
RAW="$WIKI/raw/curator"
CDP_URL="http://127.0.0.1:9222"

cd "$REPO"

if [ ! -x "$VENV_PY" ]; then
  echo "Repo virtualenv python not found at $VENV_PY" >&2
  echo "Create it with: cd $REPO && uv sync" >&2
  exit 1
fi

export HYC_STATE_DIR="$STATE"
export HYC_ARTIFACT_DIR="$STATE/artifacts"
export HYC_WIKI_PATH="$WIKI"
export WIKI_PATH="$WIKI"
export HYC_YOUTUBE_USER_DATA_DIR="$STATE/chrome-profile"
export HYC_YOUTUBE_CDP_URL="$CDP_URL"

# Keep collection conservative for scheduled use: one page load plus two scrolls
# per feed, with a pause between scrolls and between home/history collection.
export HYC_YOUTUBE_HOME_SCROLL_COUNT="${HYC_YOUTUBE_HOME_SCROLL_COUNT:-2}"
export HYC_YOUTUBE_SCROLL_PAUSE_SECONDS="${HYC_YOUTUBE_SCROLL_PAUSE_SECONDS:-2.5}"
export HYC_YOUTUBE_CAPTURE_TIMEOUT_SECONDS="${HYC_YOUTUBE_CAPTURE_TIMEOUT_SECONDS:-30}"

cdp_ready() {
  curl -fsS --max-time 2 "$CDP_URL/json/version" >/dev/null
}

if ! cdp_ready; then
  echo "Chrome CDP is not reachable at $CDP_URL; launching YouTube browser."
  nohup "$VENV_PY" scripts/launch_youtube_browser.py > "$STATE/youtube-browser.log" 2>&1 &
  sleep 8
fi

if ! cdp_ready; then
  echo "Chrome CDP is still not reachable at $CDP_URL after launch attempt."
  echo "Check $STATE/youtube-browser.log and make sure Chrome can start."
  exit 1
fi

"$VENV_PY" -m hermes_youtube_curator.cli.collector refresh-home
sleep 10
"$VENV_PY" -m hermes_youtube_curator.cli.collector refresh-history

echo "wiki_path=$WIKI"
echo "raw_curator_path=$RAW"
echo "videos=$RAW/videos.json"
echo "recommendation_events=$RAW/recommendation-events.jsonl"
echo "watch_history_events=$RAW/watch-history-events.jsonl"
# Absolute paths the wiki-enricher subagent must be handed verbatim (the curator
# must NOT construct these itself — bare relative names resolve against the
# workdir, not the wiki, and the guard then blocks the write).
echo "transcripts_path=$WIKI/raw/transcripts"
echo "entities_path=$WIKI/entities"
echo "concepts_path=$WIKI/concepts"
