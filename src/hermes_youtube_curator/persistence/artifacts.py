from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hermes_youtube_curator.models import serialize


class ArtifactStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def write(self, artifact_type: str, artifact_id: str, payload: Any) -> Path:
        target_dir = self.base_dir / artifact_type
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{artifact_id}.json"
        target.write_text(json.dumps(serialize(payload), indent=2) + "\n", encoding="utf-8")
        return target

    def read(self, path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def latest(self, artifact_type: str) -> Path | None:
        target_dir = self.base_dir / artifact_type
        if not target_dir.exists():
            return None
        candidates = sorted(target_dir.glob("*.json"), key=lambda path: path.stat().st_mtime)
        return candidates[-1] if candidates else None
