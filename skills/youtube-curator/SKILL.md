---
name: youtube-curator
description: "Personal YouTube recommendation curator using repo-collected raw wiki evidence."
version: 0.1.0
platforms: [linux]
metadata:
  hermes:
    tags: [youtube, curator, recommendations, telegram, wiki]
    related_skills: [youtube-content, llm-wiki]
---

# YouTube Curator Skill

Use this skill when running the personal YouTube curator cron job. The Python
repo only refreshes deterministic evidence; Hermes owns interpretation,
curation, transcript lookup, wiki synthesis, and Telegram delivery.

## When to Use

- Use when a cron/script run prints paths under a HermesYoutubeCurator wiki,
  especially `raw/curator/videos.json`, `recommendation-events.jsonl`, or
  `watch-history-events.jsonl`.
- Use when the user asks for a YouTube recommendation digest from their current
  home feed and recent watch history.
- Pair with `youtube-content` only when transcript-aware evaluation would
  materially improve a small number of recommendations.
- Pair with `llm-wiki` only when synthesizing durable wiki pages from raw
  evidence or saved research, not for every digest.

## Evidence Contract

- `raw/curator/videos.json`: canonical video index keyed by YouTube video ID or
  collected URL. Treat this as the deduplicated video memory.
- `raw/curator/recommendation-events.jsonl`: append-only home-feed observations.
  Repeated recommendations are a signal, but not proof of quality.
- `raw/curator/watch-history-events.jsonl`: append-only first-seen history
  observations. Treat this as the strongest current-interest signal.
- `raw/curator/runs/`: small manifests pointing to full Python artifacts.
- `entities/`, `concepts/`, `comparisons/`, and `queries/`: synthesized wiki
  pages. Use them as durable taste/project context if they exist.
- If the script output includes warnings or partial collection status, mention
  the reduced confidence briefly.

## Curation Procedure

1. Read the script output first. Use the printed wiki/raw paths as the source of
   truth for this run.
2. Inspect recent recommendation events and watch-history events. Prefer recent
   observations over older observations.
3. Build a shortlist of candidates. Favor videos that match current interests,
   repeated themes, active projects, or useful novelty.
4. Deprioritize obvious repeats, already watched videos, very stale items, weak
   clickbait, or recommendations with too little evidence.
5. Use `youtube-content` for at most a few high-value videos when transcript or
   description context would change the recommendation. Do not enrich every
   video by default.
6. Produce the Telegram digest as the final response. Hermes cron will deliver
   the final response automatically; do not call a send-message tool.

## Telegram Digest Format

Keep the message concise and scannable.

```text
YouTube Curator

Summary:
<2-3 sentences on what the feed seems to be about today and how history affected it.>

Watch now:
1. <title> — <channel>
   Why: <specific reason grounded in evidence/history/taste>
   Link: <url>

Save for later:
1. <title> — <channel>
   Why: <reason>
   Link: <url>

Skip / low priority:
1. <title> — <channel>
   Why: <short reason>

Ideas / research:
- <one concrete idea, question, or follow-up if supported>

Memory proposals:
- Proposed: <preference/theme to remember>
  Evidence: <brief supporting evidence>
  Status: pending user approval
```

If a section has no useful entries, omit that section except `Summary`.

## Memory And Wiki Rules

- Do not silently mutate long-term taste memory.
- Present preference changes as explicit `pending` proposals unless the user has
  clearly approved applying them.
- Use `llm-wiki` for durable synthesis only when the digest reveals a stable
  theme, project, entity, comparison, or research note worth preserving.
- Raw collector files are evidence, not prose memory. Do not rewrite raw files.

## Guardrails

- Never modify the user's YouTube account.
- Do not like, subscribe, comment, delete history, or open arbitrary browsing
  paths as part of curation.
- Prefer current raw/wiki evidence over generic priors.
- If evidence is sparse or collection failed, produce a short partial digest or
  say `[SILENT]` only when there is genuinely nothing useful to report.
