from __future__ import annotations

import json
import re
from pathlib import Path

from hermes_youtube_curator.models import utc_now
from hermes_youtube_curator.pipeline.context import AppContext

# Video-ID extraction mirrors the youtube-content fetch_transcript.py helper, so
# either a full YouTube URL or a bare 11-char video ID is accepted.
_VIDEO_ID_PATTERNS = [
    re.compile(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([a-zA-Z0-9_-]{11})"),
    re.compile(r"^([a-zA-Z0-9_-]{11})$"),
]


def _extract_video_id(url_or_id: str) -> str:
    value = (url_or_id or "").strip()
    for pattern in _VIDEO_ID_PATTERNS:
        match = pattern.search(value)
        if match:
            return match.group(1)
    return value


def _format_timestamp(seconds: float) -> str:
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes}:{secs:02d}"


def _fetch_segments(video_id: str, languages: list[str] | None) -> list[dict]:
    # youtube-transcript-api v1.x: YouTubeTranscriptApi().fetch(...) yields
    # snippet objects with .text/.start/.duration.
    from youtube_transcript_api import YouTubeTranscriptApi

    api = YouTubeTranscriptApi()
    result = api.fetch(video_id, languages=languages) if languages else api.fetch(video_id)
    return [
        {"text": seg.text, "start": seg.start, "duration": seg.duration}
        for seg in result
    ]


def _save_transcript(
    context: AppContext,
    *,
    video_id: str,
    url: str,
    duration: str,
    full_text: str,
) -> Path:
    """Persist the FULL transcript + metadata to raw/transcripts/<id>.md.

    Disk is cheap, so the saved file is never truncated — only what is printed
    to the subagent's context is bounded. Metadata (title/channel/url) is pulled
    from the collector's videos.json when the video is known there.
    """
    store = context.wiki
    try:
        videos = store.read_videos()
    except (FileNotFoundError, json.JSONDecodeError):
        videos = {}
    record = videos.get(video_id) or videos.get(url) or {}

    transcripts_dir = store.transcripts_dir
    transcripts_dir.mkdir(parents=True, exist_ok=True)
    target = transcripts_dir / f"{video_id}.md"

    frontmatter = (
        "---\n"
        f"video_id: {video_id}\n"
        f"title: {json.dumps(record.get('title', ''), ensure_ascii=False)}\n"
        f"channel: {json.dumps(record.get('channel_name', ''), ensure_ascii=False)}\n"
        f"url: {record.get('url', url)}\n"
        f"duration: {duration}\n"
        f"fetched_at: {utc_now()}\n"
        "source: youtube-transcript-api\n"
        "---\n\n"
    )
    target.write_text(frontmatter + full_text + "\n", encoding="utf-8")
    return target


def run_fetch_transcript(
    context: AppContext,
    *,
    url: str,
    save: bool = False,
    max_chars: int = 12000,
    language: str | None = None,
) -> str:
    """Fetch a transcript once: persist the full text, print a bounded slice.

    The single API call serves both consumers — the digest subagent summarizes
    the printed slice, and the wiki enricher later reads the saved file. A long
    podcast can be tens of thousands of tokens, so only the first `max_chars`
    are printed; the saved file keeps the full text.
    """
    video_id = _extract_video_id(url)
    languages = [item.strip() for item in language.split(",")] if language else None

    try:
        segments = _fetch_segments(video_id, languages)
    except Exception as exc:  # noqa: BLE001 - surface any fetch failure to the caller
        return json.dumps({"video_id": video_id, "error": str(exc)})

    full_text = " ".join(seg["text"] for seg in segments)
    duration = (
        _format_timestamp(segments[-1]["start"] + segments[-1]["duration"])
        if segments
        else "0:00"
    )

    saved_path = None
    if save:
        saved_path = _save_transcript(
            context, video_id=video_id, url=url, duration=duration, full_text=full_text
        )

    header = {
        "video_id": video_id,
        "duration": duration,
        "segment_count": len(segments),
        "char_count": len(full_text),
        "truncated": len(full_text) > max_chars,
        "saved": str(saved_path) if saved_path else None,
    }
    return json.dumps(header) + "\n" + full_text[:max_chars]
