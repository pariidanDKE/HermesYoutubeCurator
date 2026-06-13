from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hermes_youtube_curator.models import (
    HistoryItem,
    HistorySnapshot,
    RecommendationItem,
    RecommendationSnapshot,
    utc_now,
)

# Steering for the wiki-enricher subagent. Lives in the wiki (read at run time)
# rather than the curator skill, so the curator's prompt stays lean and the
# wiki's operating manual lives with the wiki. This is a distilled version of the
# `llm-wiki` skill scoped to the curator's narrow enrichment job.
_AGENT_GUIDE = """# Wiki Agent Guide

This folder is a personal YouTube-curation knowledge base (Karpathy LLM-wiki
pattern). It compounds durable knowledge across daily curator runs so curation
gets smarter about the user's taste over time.

## What's here
- `raw/` — immutable source material; NEVER edit. `raw/curator/` has the collected
  recommendation/history events + `videos.json`; `raw/transcripts/<id>.md` holds
  full video transcripts saved during a run.
- `entities/` — pages for concrete things: channels, people, tools, products, orgs.
- `concepts/` — pages for durable topics / interests / formats / taste patterns.
- `comparisons/`, `queries/` — side-by-side analyses and saved answers.
- `interests.md` — the user's evolving taste profile (see below). The single most
  important page for steering curation.
- `SCHEMA.md`, `index.md`, `log.md` — structure spec, page catalog, action log.

## You are the wiki-enricher subagent
You are given a shortlist of digest videos + transcript summaries, and the absolute
paths to `entities/`, `concepts/`, `interests.md`, and `user_memory_path` (the
user's stated-taste memory file). Turn that into durable wiki knowledge WITHOUT
polluting the wiki. Do the steps IN THIS ORDER — the high-value updates come first
so they are never dropped:

1. ORIENT — read `SCHEMA.md` and `index.md`, and `search_files` existing
   `entities/`/`concepts/` before creating a page so you extend, not duplicate.
   Then `read_file` `user_memory_path` once and pull out ONLY the lines about the
   user's YouTube/content taste — ignore unrelated facts. Work from the **transcript
   summaries already in your context** — do NOT open files under `raw/transcripts/`;
   reading full transcripts will exhaust your turn budget before you write anything.
   Cover ONLY channels/topics in the provided shortlist; skip ephemeral items.
2. UPDATE `interests.md` FIRST (see below) — the single highest-value action, done
   before any page. Fold in the user's stated taste from `user_memory_path` as the
   HIGHEST-weight signal (it is explicit human feedback), merged with what the
   shortlist shows. `interests.md` is the only place this taste persists for the
   curator's ranking.
3. WRITE PAGES — at most ~4 `entities/` and ~3 `concepts/` per run (prefer fewer),
   each with YAML frontmatter (title, created, updated, type, tags, sources) and at
   least 2 `[[wikilinks]]`. Append, don't rewrite: extend an existing page with a
   dated bullet rather than overwriting it.
4. UPDATE NAVIGATION — add each new page to `index.md` under its section, and append
   one line to `log.md`: `## [YYYY-MM-DD] enrich | <what changed>`.
5. GATE — before you finish, confirm you (a) updated `interests.md` and (b) appended
   to `log.md`. If either is missing, do it NOW. Do not end until both are done.

CONTAINMENT: write ONLY under the absolute `entities/`, `concepts/`, and
`interests.md` paths you were handed, plus `index.md`/`log.md` in the same wiki
root. Never touch `raw/`. You have no shell.

## interests.md — the taste profile
A living, evidence-grounded summary of what the user is into, used by the curator
to rank recommendations. Keep it tight and current:
- Maintain a short list of active interest areas (e.g. "LLM architecture",
  "developer tooling"), each a one-line note + a few example videos/channels
  (with video IDs) as evidence, dated when added.
- When watch history / the shortlist shows a sustained new interest, add or
  strengthen an area. When an area stops appearing, note it as cooling — do NOT
  delete history; mark it.
- Reflect only what the collected signal shows. This is taste evidence, not a wishlist.
"""


class WikiStore:
    def __init__(self, wiki_path: Path) -> None:
        self.wiki_path = wiki_path
        self.raw_curator_dir = wiki_path / "raw" / "curator"
        self.runs_dir = self.raw_curator_dir / "runs"
        self._initialize()

    @property
    def videos_path(self) -> Path:
        return self.raw_curator_dir / "videos.json"

    @property
    def recommendation_events_path(self) -> Path:
        return self.raw_curator_dir / "recommendation-events.jsonl"

    @property
    def watch_history_events_path(self) -> Path:
        return self.raw_curator_dir / "watch-history-events.jsonl"

    @property
    def transcripts_dir(self) -> Path:
        return self.wiki_path / "raw" / "transcripts"

    def _initialize(self) -> None:
        for relative_path in [
            "raw/articles",
            "raw/papers",
            "raw/transcripts",
            "raw/assets",
            "raw/curator/runs",
            "entities",
            "concepts",
            "comparisons",
            "queries",
        ]:
            (self.wiki_path / relative_path).mkdir(parents=True, exist_ok=True)

        self._write_once(
            self.wiki_path / "SCHEMA.md",
            """# Wiki Schema

## Domain
Personal YouTube curation: recommendations, watch history, videos, channels, topics, taste, and curator decisions.

## Raw Curator Files
- `raw/curator/videos.json`: canonical video index keyed by YouTube video ID or collected URL.
- `raw/curator/recommendation-events.jsonl`: append-only recommendation observations.
- `raw/curator/watch-history-events.jsonl`: append-only first-seen watch-history observations.
- `raw/curator/runs/`: small immutable manifests that point at full app artifacts.

## Wiki Pages
- `entities/`: concrete videos, channels, tools, people, products, and organizations.
- `concepts/`: durable interests, formats, topics, and taste patterns.
- `comparisons/`: side-by-side analyses worth preserving.
- `queries/`: substantial saved answers or reports.
- `interests.md`: the user's evolving taste profile — read by the curator each run to rank recommendations, maintained by the wiki-enricher.

## Agent Guide
See `AGENT.md` for what this wiki is and exactly how the wiki-enricher subagent should maintain it.

## Conventions
- File names are lowercase, hyphenated markdown.
- Agent-owned pages use YAML frontmatter with title, created, updated, type, tags, and sources.
- Raw curator files are deterministic source material for code and wiki synthesis.
""",
        )
        self._write_once(
            self.wiki_path / "index.md",
            """# Wiki Index
> Content catalog for synthesized curator knowledge.

## Entities

## Concepts

## Comparisons

## Queries
""",
        )
        self._write_once(
            self.wiki_path / "log.md",
            f"""# Wiki Log

## [{utc_now()[:10]}] create | Wiki initialized
- Structure created for Hermes YouTube Curator.
""",
        )
        self._write_once(self.wiki_path / "AGENT.md", _AGENT_GUIDE)
        self._write_once(
            self.wiki_path / "interests.md",
            f"""---
title: Personal Taste Profile
type: profile
created: {utc_now()[:10]}
updated: {utc_now()[:10]}
---

# Interests

> The user's evolving YouTube taste. Read by the curator each run to rank
> recommendations; maintained by the wiki-enricher. Evidence-grounded and dated —
> reflect only what the collected signal actually shows, not a wishlist.

## Active interest areas
<!-- One bullet per area: **Area** — one-line note. Evidence: <titles / video IDs>. (added YYYY-MM-DD) -->

## Cooling / dormant
<!-- Areas that have not appeared in recent history. Note, do not delete. -->
""",
        )
        self._write_json_if_missing(self.videos_path, {})
        self.recommendation_events_path.touch(exist_ok=True)
        self.watch_history_events_path.touch(exist_ok=True)

    def record_home_snapshot(
        self,
        snapshot: RecommendationSnapshot,
        *,
        artifact_path: Path,
        run_id: str | None = None,
    ) -> None:
        self._upsert_videos(snapshot.recommendations, source="recommendation")
        for item in snapshot.recommendations:
            self._append_jsonl(
                self.recommendation_events_path,
                {
                    "event_type": "recommendation",
                    "run_id": run_id,
                    "snapshot_id": snapshot.snapshot_id,
                    "observed_at": snapshot.captured_at,
                    "source": snapshot.source,
                    "video_id": item.video_id,
                    "url": item.url,
                    "title": item.title,
                    "channel_name": item.channel_name,
                    "display_position": item.display_position,
                    "section_label": item.section_label,
                    "content_type": item.content_type,
                    "duration_hint": item.duration_hint,
                    "view_count_hint": item.view_count_hint,
                    "age_hint": item.age_hint,
                    "artifact_path": str(artifact_path),
                },
            )
        self.write_run_artifact(
            snapshot.snapshot_id,
            "home",
            {
                "type": "home",
                "artifact_path": str(artifact_path),
                "captured_at": snapshot.captured_at,
                "collection_status": snapshot.collection_status,
                "item_count": snapshot.recommendation_count,
                "snapshot_id": snapshot.snapshot_id,
            },
        )

    def record_history_snapshot(
        self,
        snapshot: HistorySnapshot,
        *,
        artifact_path: Path,
        run_id: str | None = None,
    ) -> None:
        self._upsert_videos(snapshot.history_items, source="history")
        existing_history_keys = self._event_keys(
            self.watch_history_events_path,
            video_id_field="video_id",
            url_field="url",
        )
        for item in snapshot.history_items:
            item_key = item.video_id or item.url
            if item_key in existing_history_keys:
                continue
            self._append_jsonl(
                self.watch_history_events_path,
                {
                    "event_type": "watch_history",
                    "run_id": run_id,
                    "history_snapshot_id": snapshot.history_snapshot_id,
                    "observed_at": snapshot.captured_at,
                    "source": snapshot.source,
                    "video_id": item.video_id,
                    "url": item.url,
                    "title": item.title,
                    "channel_name": item.channel_name,
                    "watched_at_hint": item.watched_at_hint,
                    "recency_bucket": item.recency_bucket,
                    "display_position": item.display_position,
                    "artifact_path": str(artifact_path),
                },
            )
        self.write_run_artifact(
            snapshot.history_snapshot_id,
            "history",
            {
                "type": "history",
                "artifact_path": str(artifact_path),
                "captured_at": snapshot.captured_at,
                "collection_status": snapshot.collection_status,
                "item_count": snapshot.history_item_count,
                "history_snapshot_id": snapshot.history_snapshot_id,
            },
        )

    def read_videos(self) -> dict[str, dict[str, Any]]:
        return json.loads(self.videos_path.read_text(encoding="utf-8"))

    def read_events(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def write_run_artifact(self, artifact_id: str, artifact_type: str, payload: Any) -> Path:
        target = self.runs_dir / f"{artifact_type}-{artifact_id}.json"
        target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return target

    def _upsert_videos(
        self,
        items: list[RecommendationItem] | list[HistoryItem],
        *,
        source: str,
    ) -> None:
        videos = self.read_videos()
        now = utc_now()
        for item in items:
            key = item.video_id or item.url
            if not key:
                continue
            current = videos.get(key, {})
            videos[key] = {
                **current,
                "video_id": item.video_id,
                "url": item.url,
                "title": item.title,
                "channel_name": item.channel_name,
                "first_seen_at": current.get("first_seen_at", now),
                "last_seen_at": now,
                "last_seen_source": source,
            }
        self.videos_path.write_text(
            json.dumps(videos, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def _write_once(self, path: Path, content: str) -> None:
        if not path.exists():
            path.write_text(content, encoding="utf-8")

    def _write_json_if_missing(self, path: Path, payload: Any) -> None:
        if not path.exists():
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def _event_keys(self, path: Path, *, video_id_field: str, url_field: str) -> set[str]:
        keys: set[str] = set()
        for event in self.read_events(path):
            key = event.get(video_id_field) or event.get(url_field)
            if key:
                keys.add(str(key))
        return keys
