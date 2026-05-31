import json

from hermes_youtube_curator.cli.refresh_history import run_refresh_history
from hermes_youtube_curator.cli.refresh_home import run_refresh_home


def _read_jsonl(path):
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_wiki_store_initializes_hermes_layout(app_context):
    wiki = app_context.wiki

    assert (wiki.wiki_path / "SCHEMA.md").exists()
    assert (wiki.wiki_path / "index.md").exists()
    assert (wiki.wiki_path / "log.md").exists()
    assert (wiki.wiki_path / "raw" / "articles").is_dir()
    assert (wiki.wiki_path / "raw" / "transcripts").is_dir()
    assert (wiki.wiki_path / "raw" / "curator" / "runs").is_dir()
    assert wiki.videos_path.exists()
    assert wiki.recommendation_events_path.exists()
    assert wiki.watch_history_events_path.exists()


def test_refresh_commands_write_wiki_raw_indexes(app_context):
    home_payload = run_refresh_home(app_context)
    history_payload = run_refresh_history(app_context)

    videos = app_context.wiki.read_videos()
    recommendation_events = _read_jsonl(app_context.wiki.recommendation_events_path)
    history_events = _read_jsonl(app_context.wiki.watch_history_events_path)

    assert set(videos) >= {"vid-1", "vid-2", "vid-3"}
    assert len(recommendation_events) == home_payload["recommendation_count"]
    assert len(history_events) == history_payload["history_item_count"]
    assert recommendation_events[0]["event_type"] == "recommendation"
    assert history_events[0]["event_type"] == "watch_history"
    assert history_events[0]["recency_bucket"] == "same-day"
    assert any(
        path.name.startswith("home-")
        for path in (app_context.wiki.raw_curator_dir / "runs").glob("*.json")
    )
    assert any(
        path.name.startswith("history-")
        for path in (app_context.wiki.raw_curator_dir / "runs").glob("*.json")
    )

    home_manifest = next(
        path
        for path in (app_context.wiki.raw_curator_dir / "runs").glob("home-*.json")
    )
    history_manifest = next(
        path
        for path in (app_context.wiki.raw_curator_dir / "runs").glob("history-*.json")
    )
    assert "snapshot" not in json.loads(home_manifest.read_text(encoding="utf-8"))
    assert "snapshot" not in json.loads(history_manifest.read_text(encoding="utf-8"))


def test_history_events_only_append_new_videos(app_context):
    first_payload = run_refresh_history(app_context)
    first_events = _read_jsonl(app_context.wiki.watch_history_events_path)

    second_payload = run_refresh_history(app_context)
    second_events = _read_jsonl(app_context.wiki.watch_history_events_path)

    assert first_payload["history_item_count"] == second_payload["history_item_count"]
    assert len(first_events) == 1
    assert second_events == first_events
