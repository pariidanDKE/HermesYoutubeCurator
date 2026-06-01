from hermes_youtube_curator.cli.refresh_history import run_refresh_history
from hermes_youtube_curator.cli.refresh_home import run_refresh_home


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
