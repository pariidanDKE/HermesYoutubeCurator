from __future__ import annotations

import argparse
import sys

from hermes_youtube_curator.cli.enrich_videos import run_enrich_videos
from hermes_youtube_curator.cli.morning_run import run_morning_run
from hermes_youtube_curator.cli.refresh_history import run_refresh_history
from hermes_youtube_curator.cli.refresh_home import run_refresh_home
from hermes_youtube_curator.cli.run_curator import run_curator
from hermes_youtube_curator.cli.select_enrichment import run_select_enrichment
from hermes_youtube_curator.pipeline.context import AppContext


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hermes-youtube-curator")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in [
        "morning-run",
        "refresh-home",
        "refresh-history",
        "select-enrichment",
        "enrich-videos",
        "run-curator",
    ]:
        subparsers.add_parser(command)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    context = AppContext.build()

    if args.command == "refresh-home":
        payload = run_refresh_home(context)
    elif args.command == "refresh-history":
        payload = run_refresh_history(context)
    elif args.command == "select-enrichment":
        payload, _ = run_select_enrichment(context)
    elif args.command == "enrich-videos":
        _, selection = run_select_enrichment(context)
        payload, _ = run_enrich_videos(context, selection)
    elif args.command == "run-curator":
        payload, _ = run_curator(context)
    else:
        payload = run_morning_run(context)

    sys.stdout.write(f"{payload}\n" if isinstance(payload, str) else "")
    if isinstance(payload, dict):
        import json

        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0 if payload.get("run_status") != "failed" else 1
