from hermes_youtube_curator.cli.enrich_videos import run_enrich_videos
from hermes_youtube_curator.cli.select_enrichment import run_select_enrichment


def test_enrich_videos_handles_partial_success(app_context):
    _, selection = run_select_enrichment(app_context)
    selection.decisions[1].video_id = "missing-video"
    payload, details = run_enrich_videos(app_context, selection)
    assert payload["run_status"] == "partial"
    assert len(details) == 2
    assert payload["metadata_enriched_count"] == 1
