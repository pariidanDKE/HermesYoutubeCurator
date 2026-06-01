from __future__ import annotations

from dataclasses import dataclass

from hermes_youtube_curator.config.settings import Settings
from hermes_youtube_curator.persistence.artifacts import ArtifactStore
from hermes_youtube_curator.persistence.wiki_store import WikiStore
from hermes_youtube_curator.youtube.history_collector import HistoryCollector
from hermes_youtube_curator.youtube.home_collector import HomeCollector


@dataclass(slots=True)
class AppContext:
    settings: Settings
    artifacts: ArtifactStore
    wiki: WikiStore
    home_collector: HomeCollector
    history_collector: HistoryCollector

    @classmethod
    def build(cls, settings: Settings | None = None) -> "AppContext":
        settings = settings or Settings.from_env()
        settings.state_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            settings=settings,
            artifacts=ArtifactStore(settings.artifact_dir),
            wiki=WikiStore(settings.wiki_path),
            home_collector=HomeCollector(),
            history_collector=HistoryCollector(),
        )
