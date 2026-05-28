from __future__ import annotations

from pathlib import Path

from hermes_youtube_curator.models import CurationDigest, DeliveryRecord, new_id


class TelegramDeliveryService:
    def __init__(self, outbox_path: Path | None, fail_delivery: bool = False) -> None:
        self.outbox_path = outbox_path
        self.fail_delivery = fail_delivery

    def deliver(self, digest: CurationDigest, message: str) -> DeliveryRecord:
        if self.fail_delivery:
            return DeliveryRecord(
                digest_id=digest.digest_id,
                delivery_target="telegram",
                delivery_status="failed",
                failure_reason="Configured delivery failure for testing.",
            )

        if self.outbox_path:
            self.outbox_path.parent.mkdir(parents=True, exist_ok=True)
            with self.outbox_path.open("a", encoding="utf-8") as handle:
                handle.write(f"[{digest.digest_id}]\n{message}\n\n")

        return DeliveryRecord(
            digest_id=digest.digest_id,
            delivery_target="telegram",
            delivery_status="delivered",
            platform_message_id=new_id("telegram"),
        )
