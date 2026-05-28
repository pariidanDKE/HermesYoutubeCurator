from hermes_youtube_curator.cli.enrich_videos import run_enrich_videos
from hermes_youtube_curator.cli.morning_run import run_morning_run
from hermes_youtube_curator.cli.refresh_history import run_refresh_history
from hermes_youtube_curator.cli.refresh_home import run_refresh_home
from hermes_youtube_curator.cli.run_curator import run_curator
from hermes_youtube_curator.cli.select_enrichment import run_select_enrichment


def test_refresh_home_contract(app_context):
    payload = run_refresh_home(app_context)
    assert set(payload) >= {
        "run_status",
        "snapshot_id",
        "recommendation_count",
        "artifact_path",
        "warnings",
    }


def test_refresh_history_contract(app_context):
    payload = run_refresh_history(app_context)
    assert set(payload) >= {
        "run_status",
        "history_snapshot_id",
        "history_item_count",
        "artifact_path",
        "warnings",
    }


def test_select_enrichment_contract(app_context):
    payload, _ = run_select_enrichment(app_context)
    assert set(payload) >= {
        "run_status",
        "selection_id",
        "selected_video_ids",
        "artifact_path",
        "warnings",
    }


def test_enrich_videos_contract(app_context):
    _, selection = run_select_enrichment(app_context)
    payload, _ = run_enrich_videos(app_context, selection)
    assert set(payload) >= {
        "run_status",
        "videos_processed",
        "metadata_enriched_count",
        "transcript_enriched_count",
        "artifact_paths",
        "warnings",
    }


def test_run_curator_contract(app_context):
    _, selection = run_select_enrichment(app_context)
    _, details = run_enrich_videos(app_context, selection)
    payload, _ = run_curator(app_context, selection=selection, details=details)
    assert set(payload) >= {
        "run_status",
        "skip_reason",
        "digest_id",
        "report_artifact_path",
        "memory_proposal_count",
        "warnings",
    }


def test_morning_run_contract(app_context):
    payload = run_morning_run(app_context)
    assert set(payload) >= {"run_status", "run_id", "digest_id", "report_artifact_path", "warnings"}
