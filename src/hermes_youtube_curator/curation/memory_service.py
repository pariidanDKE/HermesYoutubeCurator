from __future__ import annotations

from hermes_youtube_curator.models import CurationDigest


class MemoryService:
    def summarize(self, digest: CurationDigest) -> list[str]:
        return [proposal.title for proposal in digest.memory_proposals]
