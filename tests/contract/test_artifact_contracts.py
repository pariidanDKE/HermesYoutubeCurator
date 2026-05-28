import json
from pathlib import Path

from hermes_youtube_curator.cli.enrich_videos import run_enrich_videos
from hermes_youtube_curator.cli.refresh_history import run_refresh_history
from hermes_youtube_curator.cli.refresh_home import run_refresh_home
from hermes_youtube_curator.cli.run_curator import run_curator
from hermes_youtube_curator.cli.select_enrichment import run_select_enrichment


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


def test_selection_digest_and_delivery_artifacts(app_context):
    _, selection = run_select_enrichment(app_context)
    selection_artifact = _load(app_context.artifacts.latest("selections").as_posix())
    assert set(selection_artifact) >= {
        "selection_id",
        "run_id",
        "selected_at",
        "decisions",
        "selection_status",
    }

    _, details = run_enrich_videos(app_context, selection)
    payload, _ = run_curator(app_context, selection=selection, details=details)
    digest_artifact = _load(payload["report_artifact_path"])
    assert set(digest_artifact) >= {"digest_id", "generated_at", "summary_text", "confidence_level"}
