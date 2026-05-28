from hermes_youtube_curator.cli.morning_run import run_morning_run


def test_morning_run_happy_path(app_context):
    payload = run_morning_run(app_context)
    assert payload["run_status"] == "success"
    assert payload["digest_id"] is not None


def test_morning_run_partial_history_path(app_context):
    app_context.settings.history_fixture = None
    payload = run_morning_run(app_context)
    assert payload["run_status"] == "partial"
    assert payload["digest_id"] is not None
