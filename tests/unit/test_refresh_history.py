import json
from pathlib import Path

from hermes_youtube_curator.cli.refresh_history import run_refresh_history


def test_refresh_history_persists_recency(app_context):
    payload = run_refresh_history(app_context)
    artifact = json.loads(Path(payload["artifact_path"]).read_text(encoding="utf-8"))
    assert payload["history_item_count"] == 1
    assert artifact["history_items"][0]["recency_bucket"] == "same-day"
