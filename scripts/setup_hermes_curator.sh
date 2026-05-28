#!/usr/bin/env bash
set -euo pipefail

cat <<'EOF'
Hermes YouTube Curator setup

1. Install the repo skill:
   mkdir -p ~/.hermes/skills/youtube-curator
   cp skills/youtube-curator/SKILL.md ~/.hermes/skills/youtube-curator/SKILL.md

2. Keep the bundled youtube-content skill enabled for transcript work.

3. Prefer Hermes cron for recurring runs:
   hermes cron add "0 8 * * *" -- ./scripts/morning_run.py

4. Keep the normal curator tool allowlist narrow:
   - repo-local CLI entrypoints only
   - bundled youtube-content
   - Hermes Telegram delivery
EOF
