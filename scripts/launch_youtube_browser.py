#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from shutil import which


PROFILE_DIR = Path(".local/state/hermes-youtube-curator/chrome-profile")
CDP_PORT = 9222


def _find_chrome() -> str | None:
    """Locate a Chrome/Chromium binary across Linux, macOS, and Windows.

    Tries PATH first (covers Linux, WSL, and Windows when Chrome is on PATH;
    `which` resolves `chrome` -> `chrome.exe` via PATHEXT), then the standard
    per-OS install locations that aren't usually on PATH.
    """
    for name in ("google-chrome", "google-chrome-stable", "chrome", "chromium", "chromium-browser"):
        found = which(name)
        if found:
            return found

    candidates: list[str] = []
    if sys.platform == "darwin":
        candidates += [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
    elif sys.platform == "win32":
        for env in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            base = os.environ.get(env)
            if base:
                candidates.append(str(Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe"))

    return next((path for path in candidates if Path(path).exists()), None)


def main() -> int:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    executable_path = _find_chrome()
    if not executable_path:
        raise RuntimeError(
            "Google Chrome not found. Install Chrome, or put it on PATH. Looked for "
            "google-chrome/chrome/chromium on PATH and the standard macOS/Windows "
            "install locations."
        )

    command = [
        executable_path,
        f"--user-data-dir={PROFILE_DIR.resolve()}",
        "--profile-directory=Default",
        f"--remote-debugging-port={CDP_PORT}",
        # Stop Chrome from downloading its multi-GB on-device AI model
        # (OptGuideOnDeviceModel / Gemini Nano) into this scraping profile.
        "--disable-features=OptimizationGuideOnDeviceModel,OptimizationHintsFetching",
        "https://www.youtube.com/",
    ]
    print(f"Using profile: {PROFILE_DIR.resolve()}")
    print(f"Using browser: {executable_path}")
    print(f"CDP URL: http://127.0.0.1:{CDP_PORT}")
    print("Log in to YouTube if needed, then keep this Chrome window open for collection.")
    subprocess.Popen(command)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
