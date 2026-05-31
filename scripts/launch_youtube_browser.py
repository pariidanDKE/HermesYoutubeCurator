#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path
from shutil import which


PROFILE_DIR = Path(".local/state/hermes-youtube-curator/chrome-profile")
CDP_PORT = 9222


def main() -> int:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    executable_path = which("google-chrome") or which("google-chrome-stable")
    if not executable_path:
        raise RuntimeError("Google Chrome is required for YouTube browser debugging.")

    command = [
        executable_path,
        f"--user-data-dir={PROFILE_DIR.resolve()}",
        "--profile-directory=Default",
        f"--remote-debugging-port={CDP_PORT}",
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
