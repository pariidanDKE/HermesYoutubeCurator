from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from hermes_youtube_curator.models import CollectionRun, CurationDigest, DeliveryRecord, serialize


class SQLiteStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                create table if not exists runs (
                    run_id text primary key,
                    trigger_type text not null,
                    run_status text not null,
                    started_at text not null,
                    completed_at text,
                    failure_reason text,
                    warnings_json text not null,
                    digest_id text,
                    report_artifact_path text
                );
                create table if not exists digests (
                    digest_id text primary key,
                    generated_at text not null,
                    summary_text text not null,
                    confidence_level text not null,
                    payload_json text not null
                );
                create table if not exists deliveries (
                    delivery_record_id text primary key,
                    digest_id text not null,
                    delivery_target text not null,
                    attempted_at text not null,
                    delivery_status text not null,
                    platform_message_id text,
                    failure_reason text,
                    payload_json text not null
                );
                """
            )

    def save_run(self, run: CollectionRun) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert or replace into runs (
                    run_id, trigger_type, run_status, started_at, completed_at,
                    failure_reason, warnings_json, digest_id, report_artifact_path
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.trigger_type,
                    run.run_status,
                    run.started_at,
                    run.completed_at,
                    run.failure_reason,
                    json.dumps(run.warnings),
                    run.digest_id,
                    run.report_artifact_path,
                ),
            )

    def save_digest(self, digest: CurationDigest) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert or replace into digests (
                    digest_id, generated_at, summary_text, confidence_level, payload_json
                ) values (?, ?, ?, ?, ?)
                """,
                (
                    digest.digest_id,
                    digest.generated_at,
                    digest.summary_text,
                    digest.confidence_level,
                    json.dumps(serialize(digest)),
                ),
            )

    def save_delivery(self, delivery: DeliveryRecord) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert or replace into deliveries (
                    delivery_record_id, digest_id, delivery_target, attempted_at,
                    delivery_status, platform_message_id, failure_reason, payload_json
                ) values (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    delivery.delivery_record_id,
                    delivery.digest_id,
                    delivery.delivery_target,
                    delivery.attempted_at,
                    delivery.delivery_status,
                    delivery.platform_message_id,
                    delivery.failure_reason,
                    json.dumps(serialize(delivery)),
                ),
            )

    def count_rows(self, table: str) -> int:
        with self._connect() as conn:
            row = conn.execute(f"select count(*) from {table}").fetchone()
        return int(row[0]) if row else 0
