from __future__ import annotations

import argparse
import sys

from hermes_youtube_curator.cli.refresh_history import run_refresh_history
from hermes_youtube_curator.cli.refresh_home import run_refresh_home
from hermes_youtube_curator.pipeline.context import AppContext


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hermes-youtube-curator")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in [
        "refresh-home",
        "refresh-history",
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
    else:
        raise AssertionError(f"Unhandled command: {args.command}")

    sys.stdout.write(f"{payload}\n" if isinstance(payload, str) else "")
    if isinstance(payload, dict):
        import json

        sys.stdout.write(json.dumps(payload, indent=2) + "\n")
    return 0 if payload.get("run_status") != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
