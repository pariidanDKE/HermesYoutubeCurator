#!/usr/bin/env python3
from __future__ import annotations

import subprocess
from pathlib import Path
from shutil import which


PROFILE_DIR = Path(".local/state/hermes-youtube-curator/chrome-profile")


def main() -> int:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    executable_path = which("google-chrome") or which("google-chrome-stable")
    if not executable_path:
        raise RuntimeError("Google Chrome is required for YouTube login profile setup.")

    command = [
        executable_path,
        f"--user-data-dir={PROFILE_DIR.resolve()}",
        "--profile-directory=Default",
        "https://www.youtube.com/",
    ]
    print(f"Using profile: {PROFILE_DIR.resolve()}")
    print(f"Using browser: {executable_path}")
    print("Log in to YouTube in the Chrome window, then close that window.")
    subprocess.run(command, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
