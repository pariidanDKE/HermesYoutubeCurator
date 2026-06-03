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
- Use `llm-wiki` each run to enrich the wiki with a small amount of durable
  context (new channels as entities, recurring themes as concepts). See
  Curation Procedure step 6.

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

## Reading The Raw Layer (Bounded)

The raw event logs are large and append-only — they grow every run. Never `Read`
them whole; doing so will blow the context budget. Instead, fetch bounded,
newest-first slices with the collector CLI (the job runs with the repo as its
working directory):

```bash
# Most recent home-feed recommendations
.venv/bin/python -m hermes_youtube_curator.cli.collector recent --kind recommendations --limit 30

# Most recent watch-history observations
.venv/bin/python -m hermes_youtube_curator.cli.collector recent --kind history --limit 30
```

Start with `--limit 30`. Page further only when a decision genuinely needs more
history (`--offset 30`, `--offset 60`, ...). Do not read `videos.json` whole — it
is a large dedup index; resolve specific video IDs only when necessary.

## Curation Procedure

1. Read the script output first. Use the printed wiki/raw paths as the source of
   truth for this run.
2. Fetch recent observations with the `recent` command (see "Reading The Raw
   Layer"). Prefer recent observations over older ones. Never read the raw event
   files whole.
3. Build a shortlist of candidates. Favor videos that match current interests,
   repeated themes, active projects, or useful novelty.
4. Deprioritize obvious repeats, already watched videos, very stale items, weak
   clickbait, or recommendations with too little evidence.
5. Use `youtube-content` for at most a few high-value videos when transcript or
   description context would change the recommendation. Do not enrich every
   video by default.
6. Enrich the wiki (durable memory) *before* composing the final response, using
   `llm-wiki`. First point it at the curator wiki — `llm-wiki` defaults to
   `~/wiki`, so set its target to the `wiki_path` printed in the script output,
   e.g. `export WIKI_PATH="<wiki_path from script output>"`. Then record a *small*
   amount of lasting context:
   - `entities/`: create or update a page for a notable new channel, creator, or
     product (especially recurring ones) — what they make and which tier they fit
     (learning / infotainment / entertainment).
   - `concepts/`: append to a page for a recurring theme or topic (e.g. a specific
     AI/ML subject or an ongoing thread), noting new videos that fit it.
   Keep it bounded: at most a few pages per run, prefer updating existing pages
   over creating new ones, and never rewrite a page wholesale. If nothing this run
   is durable enough to preserve, skip enrichment — do not invent pages.
7. Produce the Telegram digest as the final response. Hermes cron will deliver
   the final response automatically; do not call a send-message tool.

## Telegram Digest Format

Keep the message concise and scannable. Use three tiers instead of "watch now / save for later":

```text
YouTube Curator

Summary:
<2-3 sentences on what the feed seems to be about today and how history affected it.>

🧠 Pure learning:
1. <title> — <channel>
   Why: <reason — tutorials, educational deep-dives, model architecture>
   Link: <url>

🎤 Infotainment:
1. <title> — <channel>
   Why: <reason — market news, political/economic commentary, witty takes on current events>
   Link: <url>

🍿 Pure entertainment:
1. <title> — <channel>
   Why: <reason — YT drama, celebrity beef, brain-off content>
   Link: <url>

Ideas / research:
- <one concrete idea, question, or follow-up if supported>

Memory proposals:
- Proposed: <preference/theme to remember>
  Evidence: <brief supporting evidence>
  Status: pending user approval
```

**Tier definitions:**
- **Pure learning**: AI/ML tutorials, educational deep-dives, model architecture, technical walkthroughs
- **Infotainment**: Stock market news, political/economic commentary, witty takes on current events
- **Pure entertainment**: YouTube drama, celebrity beef (e.g. Drake/Kendrick), brain-off content

If a tier has no useful entries, omit that tier (but always keep `Summary`).

## Memory And Wiki Rules

- Do not silently mutate long-term taste memory.
- Present preference changes as explicit `pending` proposals unless the user has
  clearly approved applying them.
- Enrich the wiki via `llm-wiki` each run (see Curation Procedure step 6), but
  keep it bounded: a few entity/concept pages, update over create, never wholesale
  rewrites. Reserve `comparisons/` and `queries/` for when a run genuinely reveals
  one worth preserving.
- Raw collector files are evidence, not prose memory. Do not rewrite raw files.

## Guardrails

- Never modify the user's YouTube account.
- Do not like, subscribe, comment, delete history, or open arbitrary browsing
  paths as part of curation.
- Prefer current raw/wiki evidence over generic priors.
- If evidence is sparse or collection failed, produce a short partial digest or
  say `[SILENT]` only when there is genuinely nothing useful to report.
