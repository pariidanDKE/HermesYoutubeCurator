from __future__ import annotations

from datetime import UTC, datetime

from hermes_youtube_curator.cli.results import CommandResult


def finalize_result(
    payload: dict[str, object],
    *,
    required_keys: set[str],
    warnings: list[str] | None = None,
) -> CommandResult:
    missing = sorted(required_keys - payload.keys())
    if missing:
        return CommandResult(
            payload={
                "run_status": "failed",
                "failure_reason": f"Missing required result keys: {', '.join(missing)}",
                "warnings": warnings or [],
            },
            exit_code=1,
        )
    payload.setdefault("generated_at", datetime.now(UTC).replace(microsecond=0).isoformat())
    payload.setdefault("warnings", warnings or [])
    return CommandResult(payload=payload)
