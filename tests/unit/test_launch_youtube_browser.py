"""Tests for cross-platform Chrome detection in scripts/launch_youtube_browser.py.

The launcher is a standalone script (not part of the package), so we load it by
path. _find_chrome() branches on sys.platform and probes the filesystem, so each
OS is simulated by monkeypatching `which`, `sys.platform`, the environment, and
Path.exists — no real Chrome (or Windows/macOS host) required.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_LAUNCHER = Path(__file__).resolve().parents[2] / "scripts" / "launch_youtube_browser.py"
_spec = importlib.util.spec_from_file_location("launch_youtube_browser", _LAUNCHER)
launcher = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(launcher)


def test_prefers_binary_on_path(monkeypatch):
    # A binary found on PATH wins, regardless of OS or install-location probing.
    monkeypatch.setattr(launcher.sys, "platform", "win32")
    monkeypatch.setattr(launcher, "which", lambda name: "/usr/bin/google-chrome" if name == "google-chrome" else None)
    assert launcher._find_chrome() == "/usr/bin/google-chrome"


def test_macos_app_location(monkeypatch):
    # Nothing on PATH; fall back to the standard macOS .app location.
    monkeypatch.setattr(launcher.sys, "platform", "darwin")
    monkeypatch.setattr(launcher, "which", lambda _name: None)
    monkeypatch.setattr(launcher.Path, "exists", lambda self: str(self).endswith("Google Chrome"))
    assert launcher._find_chrome() == "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def test_windows_program_files(monkeypatch):
    # Nothing on PATH; fall back to the Program Files install location.
    monkeypatch.setattr(launcher.sys, "platform", "win32")
    monkeypatch.setattr(launcher, "which", lambda _name: None)
    monkeypatch.setenv("PROGRAMFILES", r"C:\Program Files")
    monkeypatch.setattr(launcher.Path, "exists", lambda self: str(self).endswith("chrome.exe"))
    found = launcher._find_chrome()
    assert found is not None
    assert found.endswith("chrome.exe")
    assert "Program Files" in found


def test_returns_none_when_missing(monkeypatch):
    # Nothing on PATH and no install location present -> None (caller raises).
    monkeypatch.setattr(launcher.sys, "platform", "darwin")
    monkeypatch.setattr(launcher, "which", lambda _name: None)
    monkeypatch.setattr(launcher.Path, "exists", lambda self: False)
    assert launcher._find_chrome() is None
