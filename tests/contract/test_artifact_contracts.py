import json
from pathlib import Path

from hermes_youtube_curator.cli.refresh_history import run_refresh_history
from hermes_youtube_curator.cli.refresh_home import run_refresh_home


def _load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def test_snapshot_artifacts(app_context):
    home = run_refresh_home(app_context)
    history = run_refresh_history(app_context)
    home_artifact = _load(home["artifact_path"])
    history_artifact = _load(history["artifact_path"])
    assert set(home_artifact) >= {
        "snapshot_id",
        "captured_at",
        "source",
        "recommendations",
        "collection_status",
    }
    assert set(history_artifact) >= {
        "history_snapshot_id",
        "captured_at",
        "source",
        "history_items",
        "collection_status",
    }
