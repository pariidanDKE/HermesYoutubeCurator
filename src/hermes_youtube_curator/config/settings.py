from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


@dataclass(slots=True)
class Settings:
    state_dir: Path
    artifact_dir: Path
    sqlite_path: Path
    home_fixture: Path | None
    history_fixture: Path | None
    enrichment_fixture: Path | None
    telegram_outbox: Path | None
    scheduler: str
    max_enrichment: int
    telegram_fail_delivery: bool
    wiki_path: Path | None = None
    youtube_user_data_dir: Path | None = None
    youtube_cdp_url: str | None = None
    youtube_home_scroll_count: int = 3
    youtube_scroll_pause_seconds: float = 1.5
    youtube_capture_timeout_seconds: int = 30
    youtube_home_url: str = "https://www.youtube.com/"
    youtube_history_url: str = "https://www.youtube.com/feed/history"

    def __post_init__(self) -> None:
        if self.wiki_path is None:
            self.wiki_path = self.state_dir / "wiki"

    @classmethod
    def from_env(cls) -> "Settings":
        state_dir = Path(os.getenv("HYC_STATE_DIR", ".local/state/hermes-youtube-curator"))
        artifact_dir = Path(
            os.getenv("HYC_ARTIFACT_DIR", str(state_dir / "artifacts"))
        )
        sqlite_path = Path(os.getenv("HYC_SQLITE_PATH", str(state_dir / "curator.db")))
        wiki_path = Path(os.getenv("HYC_WIKI_PATH", str(state_dir / "wiki")))
        return cls(
            state_dir=state_dir,
            artifact_dir=artifact_dir,
            sqlite_path=sqlite_path,
            home_fixture=_optional_path("HYC_HOME_FIXTURE"),
            history_fixture=_optional_path("HYC_HISTORY_FIXTURE"),
            enrichment_fixture=_optional_path("HYC_ENRICHMENT_FIXTURE"),
            telegram_outbox=_optional_path("HYC_TELEGRAM_OUTBOX"),
            wiki_path=wiki_path,
            scheduler=os.getenv("HYC_SCHEDULER", "hermes-cron"),
            max_enrichment=int(os.getenv("HYC_MAX_ENRICHMENT", "3")),
            telegram_fail_delivery=_bool_env("HYC_TELEGRAM_FAIL_DELIVERY"),
            youtube_user_data_dir=_optional_path("HYC_YOUTUBE_USER_DATA_DIR"),
            youtube_cdp_url=os.getenv("HYC_YOUTUBE_CDP_URL"),
            youtube_home_scroll_count=int(os.getenv("HYC_YOUTUBE_HOME_SCROLL_COUNT", "3")),
            youtube_scroll_pause_seconds=float(
                os.getenv("HYC_YOUTUBE_SCROLL_PAUSE_SECONDS", "1.5")
            ),
            youtube_capture_timeout_seconds=int(
                os.getenv("HYC_YOUTUBE_CAPTURE_TIMEOUT_SECONDS", "30")
            ),
        )


def _optional_path(name: str) -> Path | None:
    raw = os.getenv(name)
    return Path(raw) if raw else None
