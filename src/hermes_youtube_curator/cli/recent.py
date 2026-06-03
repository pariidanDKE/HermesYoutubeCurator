from __future__ import annotations

import json

from hermes_youtube_curator.pipeline.context import AppContext

# Bookkeeping fields that bloat the slice without helping curation. Stripped so
# the model sees only signal (title, channel, url, hints) rather than repeated
# absolute paths and internal IDs.
_NOISE_FIELDS = frozenset(
    {
        "artifact_path",
        "run_id",
        "snapshot_id",
        "history_snapshot_id",
        "event_type",
        "source",
    }
)


def run_recent(context: AppContext, *, kind: str, limit: int, offset: int) -> str:
    """Return the most recent raw events as compact JSON.

    The raw event logs are append-only, so the newest entries are at the end of
    the file. This returns a bounded, newest-first window so Hermes never has to
    read the (large, ever-growing) raw files whole.
    """
    store = context.wiki
    if kind == "recommendations":
        path = store.recommendation_events_path
    elif kind == "history":
        path = store.watch_history_events_path
    else:
        raise ValueError(f"Unknown kind: {kind!r}")

    events = store.read_events(path)
    window = list(reversed(events))[offset : offset + limit]
    trimmed = [
        {key: value for key, value in event.items() if key not in _NOISE_FIELDS}
        for event in window
    ]
    return json.dumps(trimmed, indent=2)
