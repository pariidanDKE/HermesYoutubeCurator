---
name: youtube-curator
description: "Personal YouTube recommendation curator using repo-collected raw wiki evidence."
version: 0.2.0
platforms: [linux]
metadata:
  hermes:
    tags: [youtube, curator, recommendations, telegram, wiki]
    related_skills: [youtube-content, llm-wiki]
---

# YouTube Curator Skill

Use this skill when running the personal YouTube curator cron job. The Python
repo only refreshes deterministic evidence; you (the curator agent) own
interpretation, curation, and the final digest. Two heavy/untrusted jobs are
delegated to isolated subagents so they never enter your context:

- **Transcript subagent** (untrusted internet text) — fetches + persists +
  summarizes transcripts.
- **Wiki-enricher subagent** (large reads + durable writes) — turns the shortlist
  and saved transcripts into wiki pages (runs before the digest is written).

You own only the cheap, trusted work: two bounded `recent` reads, the shortlist,
and writing the digest.

## When to Use

- Use when a cron/script run prints paths under a HermesYoutubeCurator wiki,
  especially `raw/curator/videos.json`, `recommendation-events.jsonl`, or
  `watch-history-events.jsonl`.
- Use when the user asks for a YouTube recommendation digest from their current
  home feed and recent watch history.
- Transcripts: do NOT use the `youtube-content` skill directly, and never fetch a
  transcript into your own context. Delegate the transcript subagent (step 4),
  which runs the curator's own `fetch-transcript --save` command. That command
  fetches once, persists the full transcript to `raw/transcripts/<id>.md`, and
  prints a bounded slice for the subagent to summarize.

## Evidence Contract

- `raw/curator/videos.json`: canonical video index keyed by YouTube video ID or
  collected URL. Treat this as the deduplicated video memory.
- `raw/curator/recommendation-events.jsonl`: append-only home-feed observations.
  Repeated recommendations are a signal, but not proof of quality.
- `raw/curator/watch-history-events.jsonl`: append-only first-seen history
  observations. Treat this as the strongest current-interest signal.
- `raw/curator/runs/`: small manifests pointing to full Python artifacts.
- `raw/transcripts/`: per-video transcript files (`<video_id>.md`) written by the
  transcript subagent. The enricher reads these; you do not.
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
   Layer") — typically the two reads above. Prefer recent observations over older
   ones. Never read the raw event files whole.
3. Build the shortlist and assign tiers (see "Telegram Digest Format"). Favor
   videos that match current interests, repeated themes, active projects, or
   useful novelty. Deprioritize obvious repeats, already-watched videos, very
   stale items, weak clickbait, or items with too little evidence.
4. **Delegate ONE transcript subagent** to deepen the few picks worth it
   (typically the top pick per tier — about 2–4 videos total, not every
   candidate). Call `delegate_task` with `toolsets: ["terminal"]` and a goal
   listing those videos' IDs and telling the subagent to, for EACH id, run
   exactly this command and then return ONE 2–3 sentence summary per video:

   ```
   cd /home/dan-parii/Documents/HermesYoutubeCurator && .venv/bin/python -m hermes_youtube_curator.cli.collector fetch-transcript --url <VIDEO_ID> --save
   ```

   Pass the bare 11-char video ID (not a full URL with `?`/`&`). The command
   prints a JSON header line (`video_id`, `duration`, `saved`, `truncated`)
   followed by the transcript text — the subagent summarizes the text and returns
   the summaries to you. The full transcript stays in the subagent's context and
   on disk, never in yours. Use each returned summary to sharpen that pick's
   "Why". If the subagent fails, is denied, times out, or returns nothing, skip
   those summaries and produce the digest anyway — NEVER block the digest on a
   transcript.
5. **Delegate ONE wiki-enricher subagent BEFORE writing the digest** — do this
   now so the digest stays your final, last action and this enrichment step is
   never dropped. Call `delegate_task` with `toolsets: ["file"]` (file tools only
   — NOT `terminal`) and pass, in `context`: your shortlist (titles, channels,
   tiers) and the transcript summaries from step 4, plus the three ABSOLUTE paths
   exactly as the script printed them — the `transcripts_path=`, `entities_path=`,
   and `concepts_path=` lines. Copy those absolute paths verbatim; do NOT shorten
   them to bare names like `entities/` and do NOT construct your own paths — a
   relative path resolves against the wrong directory and every write will be
   blocked. Instruct the enricher to write only under the given absolute
   `entities_path`/`concepts_path` and to follow the "Wiki Enrichment Rules"
   below. The enricher's output is wiki files, not a user message — ignore its
   return text. If it fails or is denied, skip it; never block the digest on
   enrichment.
6. Produce the Telegram digest (see format below) as your final response, using
   the summaries from step 4. This MUST be the last thing you do — Hermes cron
   delivers the final response automatically; do not call a send-message tool.

## Execution Rules

- Use only the `terminal` and `delegate_task` tools. Do not plan, make todo
  lists, read files yourself, or hunt for other tools/skills — everything you
  need is in this skill.
- Keep reasoning short and direct: `recent` data → shortlist → transcript
  delegate → enricher delegate → digest. The digest is ALWAYS last; both
  delegations happen before it. Do not deliberate at length over every candidate.
- Exactly two delegations per run: one transcript subagent (step 4), one enricher
  (step 5), both before the digest. Do not delegate per-video or spawn extra
  subagents.

## Wiki Enrichment Rules

These are the instructions to embed in the enricher subagent's goal/context. The
enricher reads the digest + saved transcripts + existing wiki, then writes a few
durable pages — without polluting the wiki.

- **Scope**: only the videos/channels/topics in the provided shortlist and their
  saved transcripts in `raw/transcripts/`. Do not invent topics.
- **Read before write**: use `search_files` to find existing `entities/` and
  `concepts/` pages, then `read_file` the matching ones. Update/extend a matching
  page instead of creating a near-duplicate. Your tools are EXACTLY `search_files`,
  `read_file`, `write_file`, `patch` — never call any other tool name.
- **Append, don't rewrite**: when extending an existing page, add a dated note or
  a new bullet; do not rewrite or delete existing content.
- **Hard cap per run**: at most ~4 `entities/` pages and ~3 `concepts/` pages.
  Prefer fewer. Skip anything that is ephemeral or weakly evidenced.
- **Containment**: write ONLY under the absolute `entities_path`/`concepts_path`
  you were handed (e.g. `<entities_path>/<Channel_Name>.md`). Never write outside
  the wiki, never touch `raw/` (it is evidence), and never run shell commands (the
  enricher has no terminal). Writes outside those two dirs are blocked in code.

## Telegram Digest Format

Keep the message concise and scannable. Use three tiers instead of "watch now / save for later":

```text
YouTube Curator

Summary:
<2-3 sentences on what the feed seems to be about today and how history affected it.>

🧠 Pure learning:
1. <title> — <channel>
   ⏱️ <duration>
   Why: <reason — tutorials, educational deep-dives, model architecture>
   Link: <url>

🎤 Infotainment:
1. <title> — <channel>
   ⏱️ <duration>
   Why: <reason — market news, political/economic commentary, witty takes on current events>
   Link: <url>

🍿 Pure entertainment:
1. <title> — <channel>
   ⏱️ <duration>
   Why: <reason — YT drama, celebrity beef, brain-off content>
   Link: <url>

Ideas / research:
- <one concrete idea, question, or follow-up if supported>

Proposed preferences:
- <A grounded question that cites the specific units/history prompting it, e.g.
  "Your watch history this week is heavy on AI/ML model-architecture deep-dives
  (BLT transformer, LeCun's LLM critique) — want me to make that a standing
  'Pure learning' preference?">
```

**Tier definitions:**
- **Pure learning**: AI/ML tutorials, educational deep-dives, model architecture, technical walkthroughs
- **Infotainment**: Stock market news, political/economic commentary, witty takes on current events
- **Pure entertainment**: YouTube drama, celebrity beef (e.g. Drake/Kendrick), brain-off content

If a tier has no useful entries, omit that tier (but always keep `Summary`).

## Preferences And Memory Rules

- Durable taste and format preferences live in **this skill**, not long-term
  memory. Scheduled (cron) runs have memory disabled, so anything in `USER.md` is
  invisible to the digest — only this skill is re-read each run.
- During a scheduled run, only *propose* preferences (the "Proposed preferences"
  section), grounded in the run's evidence. Never silently self-edit the skill in
  an unattended run.
- Apply an approved preference only in an interactive conversation, after the user
  says yes: edit this skill — update the relevant `Telegram Digest Format` wording
  or a short `Learned Preferences` list. Keep it concise; update existing wording
  rather than appending endlessly, so the skill stays small and the context budget
  stays bounded.
- Raw collector files are evidence, not prose memory. Do not rewrite raw files.

## Guardrails

- Never modify the user's YouTube account.
- Do not like, subscribe, comment, delete history, or open arbitrary browsing
  paths as part of curation.
- Prefer current raw/wiki evidence over generic priors.
- If evidence is sparse or collection failed, produce a short partial digest or
  say `[SILENT]` only when there is genuinely nothing useful to report.
