import json
from pathlib import Path

from hermes_youtube_curator.cli.refresh_home import run_refresh_home


def test_refresh_home_persists_snapshot(app_context):
    payload = run_refresh_home(app_context)
    artifact = json.loads(Path(payload["artifact_path"]).read_text(encoding="utf-8"))
    assert payload["recommendation_count"] == 3
    assert len(artifact["recommendations"]) == 3
