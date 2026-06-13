---
name: youtube-curator
description: "Personal YouTube recommendation curator using repo-collected raw wiki evidence."
version: 0.3.0
platforms: [linux]
metadata:
  hermes:
    tags: [youtube, curator, recommendations, telegram, wiki]
    related_skills: [youtube-content, llm-wiki]
---

# YouTube Curator Skill

Cron-only skill for the daily YouTube digest. The pre-run script refreshes raw
evidence; you own the judgment (shortlist + digest) and delegate two isolated
subagents for the heavy/untrusted work, so their large or hostile content never
enters your context:
- **transcript subagent** — untrusted transcript text
- **wiki-enricher** — large reads + durable wiki writes

Use only `terminal` and `delegate_task`. Don't plan, make todo lists, or hunt for
other tools/skills. Go straight from evidence to digest — don't deliberate over
every candidate.

## Bounded reads

Raw event logs are large and append-only — **never read them whole** (it blows the
context budget). Read newest-first slices via the collector (cwd is the repo):

```bash
.venv/bin/python -m hermes_youtube_curator.cli.collector recent --kind recommendations --limit 30
.venv/bin/python -m hermes_youtube_curator.cli.collector recent --kind history --limit 30
```

Page with `--offset 30/60` only if a decision needs it; never read `videos.json`
whole. Signal weighting: **watch history is the strongest current-interest
signal**; repeated recommendations are a signal, not proof of quality.

## Procedure

1. Read the script output — its printed `*_path=` lines are the source of truth
   for this run.
2. Run the two `recent` reads above, then `cat <interests_path>` (printed by the
   script). **`interests.md` is your primary ranking signal** — what the user is
   into right now.
3. Build the shortlist and assign tiers (see Digest Format). Favor matches to
   `interests.md`, repeated themes, active projects, and useful novelty; drop
   repeats, already-watched, stale, weak clickbait, and thin-evidence items.
4. **Delegate the transcript subagent** (`delegate_task`, `toolsets: ["terminal"]`)
   for the ~2–4 picks worth deepening (top of each tier). Goal: for each **bare
   11-char video ID** (not a full URL — `?`/`&` break it), run exactly this and
   return one 2–3 sentence summary per video:
   ```
   cd @@REPO@@ && .venv/bin/python -m hermes_youtube_curator.cli.collector fetch-transcript --url <VIDEO_ID> --save
   ```
   Use the summaries to sharpen each "Why".
5. **Delegate the wiki-enricher** (`delegate_task`, `toolsets: ["file"]`), before
   the digest. Goal: `read_file` the guide at the script's `agent_guide_path` and
   follow it. In `context` give the shortlist (titles/channels/tiers), the step-4
   summaries, and the script's `transcripts_path` / `entities_path` /
   `concepts_path` / `interests_path` / `user_memory_path` — **copy those absolute
   paths verbatim; a relative path resolves to the wrong directory and every write
   is blocked.** (The enricher reads `user_memory_path` to fold the user's
   chat-stated taste into `interests.md`.) Ignore its return text (it writes files).
6. **Gate, then digest.** Before writing, confirm you delegated BOTH subagents
   (steps 4 and 5); if either is missing, do it now — you may not produce the
   digest until both are done. Then produce the Telegram digest (below) as your
   final response — the last thing you do. Cron delivers it; do not call a
   send-message tool.

A subagent that fails, is denied, times out, or returns nothing never blocks the
digest — skip it and continue.

## Telegram Digest Format

Concise and scannable, three tiers:

```text
YouTube Curator

Summary:
<2-3 sentences on what the feed seems to be about today and how history affected it.>

🧠 Pure learning:
1. <title>\n   Channel: <channel>\n   ⏱️ <duration>\n   Why: <reason — tutorials, educational deep-dives, model architecture>\n   Link: <url>\n\n🎤 Infotainment:\n1. <title>\n   Channel: <channel>\n   ⏱️ <duration>\n   Why: <reason — market news, political/economic commentary, witty takes on current events>\n   Link: <url>\n\n🍿 Pure entertainment:\n1. <title>\n   Channel: <channel>\n   ⏱️ <duration>\n   Why: <reason — YT drama, celebrity beef, brain-off content>\n   Link: <url>\n
Ideas / research:
- <one concrete idea, question, or follow-up if supported>

Proposed preferences:
- <A grounded question citing the units/history prompting it, e.g. "Your history
  this week is heavy on AI/ML architecture deep-dives (BLT, LeCun's LLM critique)
  — make that a standing 'Pure learning' preference?">
```

Omit any tier with no useful entries (but always keep `Summary`).

## Preferences

- Evolving **taste** lives in `interests.md` (read each run, maintained by the
  enricher). **Format** preferences live in this skill.
- In a scheduled run, only *propose* preferences (the digest section above),
  grounded in the run's evidence. Never self-edit the skill unattended — apply an
  approved preference only in an interactive session.

## Guardrails

- Never modify the user's YouTube account (no like/subscribe/comment, no history
  changes, no arbitrary browsing).
- Prefer current raw/wiki evidence over generic priors.
- If evidence is sparse or collection failed, produce a short partial digest — or
  reply exactly `[SILENT]` only when there is genuinely nothing useful to report.
