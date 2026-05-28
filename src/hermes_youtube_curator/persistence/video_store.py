from __future__ import annotations

import sqlite3
from pathlib import Path


class VideoStore:
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
                create table if not exists canonical_videos (
                    video_id text primary key,
                    canonical_video_id text not null,
                    title text,
                    channel_name text
                );
                create table if not exists selection_decisions (
                    selection_id text not null,
                    video_id text not null,
                    decision text not null,
                    reason text not null,
                    primary key (selection_id, video_id)
                );
                """
            )

    def link_video(
        self,
        *,
        video_id: str,
        canonical_video_id: str,
        title: str | None = None,
        channel_name: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert or replace into canonical_videos (
                    video_id, canonical_video_id, title, channel_name
                ) values (?, ?, ?, ?)
                """,
                (video_id, canonical_video_id, title, channel_name),
            )

    def save_selection_decision(
        self,
        *,
        selection_id: str,
        video_id: str,
        decision: str,
        reason: str,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                insert or replace into selection_decisions (
                    selection_id, video_id, decision, reason
                ) values (?, ?, ?, ?)
                """,
                (selection_id, video_id, decision, reason),
            )
