from hermes_youtube_curator.cli.enrich_videos import run_enrich_videos
from hermes_youtube_curator.cli.select_enrichment import run_select_enrichment


def test_enrichment_contract_explicit_missing_transcript(app_context):
    _, selection = run_select_enrichment(app_context)
    payload, details = run_enrich_videos(app_context, selection)
    assert payload["transcript_enriched_count"] == 1
    assert any(detail.transcript_status == "unavailable" for detail in details)


def test_enrichment_contract_preserves_selected_video_ids(app_context):
    payload, selection = run_select_enrichment(app_context)
    enriched_payload, details = run_enrich_videos(app_context, selection)
    assert payload["selected_video_ids"] == [detail.video_id for detail in details]
    assert enriched_payload["videos_processed"] == len(details)
