from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CommandResult:
    payload: dict[str, Any]
    exit_code: int = 0
    warnings: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        merged = dict(self.payload)
        merged["warnings"] = [*merged.get("warnings", []), *self.warnings]
        return json.dumps(merged, indent=2)
