from __future__ import annotations

from dataclasses import dataclass

from hermes_youtube_curator.config.settings import Settings
from hermes_youtube_curator.curation.curator_service import CuratorService
from hermes_youtube_curator.curation.memory_service import MemoryService
from hermes_youtube_curator.curation.selection_service import SelectionService
from hermes_youtube_curator.delivery.telegram import TelegramDeliveryService
from hermes_youtube_curator.persistence.artifacts import ArtifactStore
from hermes_youtube_curator.persistence.sqlite_store import SQLiteStore
from hermes_youtube_curator.persistence.wiki_store import WikiStore
from hermes_youtube_curator.youtube.enrichment import EnrichmentService
from hermes_youtube_curator.youtube.history_collector import HistoryCollector
from hermes_youtube_curator.youtube.home_collector import HomeCollector


@dataclass(slots=True)
class AppContext:
    settings: Settings
    artifacts: ArtifactStore
    sqlite: SQLiteStore
    wiki: WikiStore
    home_collector: HomeCollector
    history_collector: HistoryCollector
    enrichment: EnrichmentService
    selection: SelectionService
    curator: CuratorService
    memory: MemoryService
    delivery: TelegramDeliveryService

    @classmethod
    def build(cls, settings: Settings | None = None) -> "AppContext":
        settings = settings or Settings.from_env()
        settings.state_dir.mkdir(parents=True, exist_ok=True)
        return cls(
            settings=settings,
            artifacts=ArtifactStore(settings.artifact_dir),
            sqlite=SQLiteStore(settings.sqlite_path),
            wiki=WikiStore(settings.wiki_path),
            home_collector=HomeCollector(),
            history_collector=HistoryCollector(),
            enrichment=EnrichmentService(settings.enrichment_fixture),
            selection=SelectionService(),
            curator=CuratorService(),
            memory=MemoryService(),
            delivery=TelegramDeliveryService(
                settings.telegram_outbox,
                fail_delivery=settings.telegram_fail_delivery,
            ),
        )
