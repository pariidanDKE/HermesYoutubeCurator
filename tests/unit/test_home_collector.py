from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from hermes_youtube_curator.config.settings import Settings
import hermes_youtube_curator.youtube.home_collector as home_collector_module
from hermes_youtube_curator.youtube.home_collector import HomeCollector


class _FakeMouse:
    def __init__(self) -> None:
        self.wheel_calls: list[tuple[int, int]] = []

    def wheel(self, delta_x: int, delta_y: int) -> None:
        self.wheel_calls.append((delta_x, delta_y))


class _FakePage:
    def __init__(self, batches: list[list[dict[str, str | None]]]) -> None:
        self._batches = batches
        self._batch_index = 0
        self.mouse = _FakeMouse()
        self.waited_for: list[tuple[str, int]] = []

    def wait_for_selector(self, selector: str, timeout: int) -> None:
        self.waited_for.append((selector, timeout))

    def evaluate(self, _script: str):
        return self._batches[min(self._batch_index, len(self._batches) - 1)]


def test_capture_homepage_dedupes_and_orders_entries() -> None:
    collector = HomeCollector()
    page = _FakePage(
        [
            [
                {
                    "title": "Video One",
                    "channel_name": "Channel A",
                    "url": "https://www.youtube.com/watch?v=vid-1",
                    "thumbnail_url": "https://img/1.jpg",
                    "description_excerpt": "First batch item.",
                },
                {
                    "title": "Video Two",
                    "channel_name": "Channel B",
                    "url": "https://www.youtube.com/watch?v=vid-2",
                    "thumbnail_url": "https://img/2.jpg",
                    "description_excerpt": "First batch item.",
                },
            ],
            [
                {
                    "title": "Video Two",
                    "channel_name": "Channel B",
                    "url": "https://www.youtube.com/watch?v=vid-2",
                    "thumbnail_url": "https://img/2.jpg",
                    "description_excerpt": "Duplicate after scroll.",
                },
                {
                    "title": "Video Three",
                    "channel_name": "Channel C",
                    "url": "https://www.youtube.com/watch?v=vid-3",
                    "thumbnail_url": "https://img/3.jpg",
                    "description_excerpt": "New after scroll.",
                },
            ],
            [
                {
                    "title": "Video Three",
                    "channel_name": "Channel C",
                    "url": "https://www.youtube.com/watch?v=vid-3",
                    "thumbnail_url": "https://img/3.jpg",
                    "description_excerpt": "Still visible.",
                }
            ],
        ]
    )

    original_extract = collector._extract_visible_recommendations

    def scripted_extract(current_page):
        batch = original_extract(current_page)
        current_page._batch_index += 1
        return batch

    collector._extract_visible_recommendations = scripted_extract  # type: ignore[method-assign]

    snapshot_items = collector._capture_homepage(
        page,
        Settings(
            state_dir=Path("."),
            artifact_dir=Path("./artifacts"),
            home_fixture=None,
            history_fixture=None,
            scheduler="test",
            youtube_home_scroll_count=2,
            youtube_scroll_pause_seconds=0.0,
            youtube_capture_timeout_seconds=5,
        ),
    )

    assert [item.video_id for item in snapshot_items] == ["vid-1", "vid-2", "vid-3"]
    assert [item.display_position for item in snapshot_items] == [1, 2, 3]
    assert [item.content_type for item in snapshot_items] == ["video", "video", "video"]
    assert len(page.mouse.wheel_calls) == 2
    assert page.waited_for[0][0].startswith("ytd-rich-grid-renderer")
    assert page.waited_for[0][1] == 5000


def test_capture_homepage_uses_meaningful_title_over_duration_overlay() -> None:
    collector = HomeCollector()
    page = _FakePage(
        [
            [
                {
                    "title": "DRAKE: Sundae Conversation with Caleb Pressley",
                    "channel_name": "Sundae Conversation",
                    "url": "https://www.youtube.com/watch?v=vFGWIhnE3i4",
                    "thumbnail_url": "https://img/1.jpg",
                    "description_excerpt": "14M views • 3 years ago",
                    "content_type": "video",
                    "duration_hint": None,
                    "view_count_hint": "14M views",
                    "age_hint": "3 years ago",
                }
            ]
        ]
    )

    items = collector._capture_homepage(
        page,
        Settings(
            state_dir=Path("."),
            artifact_dir=Path("./artifacts"),
            home_fixture=None,
            history_fixture=None,
            scheduler="test",
            youtube_home_scroll_count=0,
            youtube_scroll_pause_seconds=0.0,
            youtube_capture_timeout_seconds=5,
        ),
    )

    assert items[0].title == "DRAKE: Sundae Conversation with Caleb Pressley"
    assert items[0].channel_name == "Sundae Conversation"
    assert items[0].video_id == "vFGWIhnE3i4"
    assert items[0].content_type == "video"
    assert items[0].duration_hint is None
    assert items[0].view_count_hint == "14M views"
    assert items[0].age_hint == "3 years ago"


def test_collect_navigates_to_home_before_capture(monkeypatch) -> None:
    collector = HomeCollector()
    settings = Settings(
        state_dir=Path("."),
        artifact_dir=Path("./artifacts"),
        home_fixture=None,
        history_fixture=None,
        scheduler="test",
        youtube_home_url="https://www.youtube.com/",
    )
    page = _FakePage([])
    page.goto_calls = []

    def goto(url: str, wait_until: str):
        page.goto_calls.append((url, wait_until))

    page.goto = goto

    @contextmanager
    def fake_open_youtube_page(_settings):
        yield page

    monkeypatch.setattr(home_collector_module, "open_youtube_page", fake_open_youtube_page)
    monkeypatch.setattr(home_collector_module, "ensure_signed_in", lambda _page: "valid")
    monkeypatch.setattr(collector, "_capture_homepage", lambda _page, _settings: [])
    monkeypatch.setattr(collector, "_diagnose_empty_homepage", lambda _page: "empty")

    collector.collect(settings)

    assert page.goto_calls == [("https://www.youtube.com/", "domcontentloaded")]
