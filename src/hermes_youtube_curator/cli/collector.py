from __future__ import annotations

import argparse
import json
import sys

from hermes_youtube_curator.cli.recent import run_recent
from hermes_youtube_curator.cli.refresh_history import run_refresh_history
from hermes_youtube_curator.cli.refresh_home import run_refresh_home
from hermes_youtube_curator.pipeline.context import AppContext


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hermes-youtube-curator")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("refresh-home")
    subparsers.add_parser("refresh-history")

    recent = subparsers.add_parser("recent")
    recent.add_argument("--kind", choices=["recommendations", "history"], required=True)
    recent.add_argument("--limit", type=int, default=30)
    recent.add_argument("--offset", type=int, default=0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    context = AppContext.build()

    if args.command == "refresh-home":
        payload = run_refresh_home(context)
    elif args.command == "refresh-history":
        payload = run_refresh_history(context)
    elif args.command == "recent":
        sys.stdout.write(
            run_recent(context, kind=args.kind, limit=args.limit, offset=args.offset) + "\n"
        )
        return 0
    else:
        raise AssertionError(f"Unhandled command: {args.command}")

    if isinstance(payload, dict):
        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0 if payload.get("run_status") != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
