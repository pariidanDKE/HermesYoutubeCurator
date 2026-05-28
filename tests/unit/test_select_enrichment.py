from hermes_youtube_curator.cli.select_enrichment import run_select_enrichment


def test_select_enrichment_records_reasons(app_context):
    payload, selection = run_select_enrichment(app_context)
    assert payload["selected_video_ids"] == ["vid-1", "vid-2"]
    assert all(decision.reason for decision in selection.decisions)
