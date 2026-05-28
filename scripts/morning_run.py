#!/usr/bin/env python3
# ruff: noqa: I001
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hermes_youtube_curator.cli.main import main


raise SystemExit(main(["morning-run"]))
