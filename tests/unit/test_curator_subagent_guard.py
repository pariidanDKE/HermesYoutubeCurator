"""Tests for the curator-subagent-guard transcript-command allowlist.

The guard is the sole hard control constraining the transcript subagent — the
component that processes untrusted YouTube transcript text — so its
fetch-transcript allowlist is a security boundary, not a convenience check. These
tests pin the legitimate command shapes AND the injection variants that the old
substring/regex implementation let through (python -c, `#`-comment token
smuggling, metacharacter-free os.system, chaining, env prefixes, bad ids).

The plugin dir name has hyphens, so it isn't importable as a package — load it by
path. Importing only needs the @@WIKI_PATH@@ placeholder, which resolves fine.
"""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

# The guard reads HYC_WIKI_PATH at import to resolve its wiki root (else the
# @@WIKI_PATH@@ deploy placeholder, which isn't absolute). Pin an absolute root so
# the curator `cat <wiki file>` allowlist has a real base to validate against.
os.environ.setdefault("HYC_WIKI_PATH", "/tmp/hyc-test-wiki")

_GUARD = (
    Path(__file__).resolve().parents[2]
    / "deploy"
    / "plugins"
    / "curator-subagent-guard"
    / "__init__.py"
)
_spec = importlib.util.spec_from_file_location("curator_subagent_guard", _GUARD)
guard = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(guard)

_allowed = guard._is_allowed_transcript_command
_PY = ".venv/bin/python"
_MOD = "hermes_youtube_curator.cli.collector"
_ID = "dQw4w9WgXcQ"  # a valid 11-char video id


# --- legitimate commands: must be ALLOWED -----------------------------------

@pytest.mark.parametrize(
    "cmd",
    [
        f"{_PY} -m {_MOD} fetch-transcript --url {_ID} --save",
        f"cd /home/x/repo && {_PY} -m {_MOD} fetch-transcript --url {_ID} --save",
        f"{_PY} -m {_MOD} fetch-transcript --url {_ID} --save 2>&1",
        f"python3 -m {_MOD} fetch-transcript --url {_ID}",
        f"{_PY} -m {_MOD} fetch-transcript --url={_ID} --save",
        f"{_PY} -m {_MOD} fetch-transcript --url {_ID} --max-chars 8000 --language en,tr",
    ],
)
def test_legitimate_commands_allowed(cmd):
    assert _allowed(cmd) is True


# --- the reported exploit variants: must be BLOCKED -------------------------

@pytest.mark.parametrize(
    "cmd",
    [
        # python -c arbitrary code, with required substrings smuggled in a # comment
        f'{_PY} -c "__import__(\'os\').system(\'touch /tmp/pwned\')" #{_MOD} fetch-transcript',
        # metacharacter-free pure-python file write (no shell metachars at all)
        f'{_PY} -c "open(\'/tmp/pwned\',\'w\').write(\'x\')" #{_MOD} fetch-transcript',
        # `#` comment smuggling without -c
        f"{_PY} -m evil.module #{_MOD} fetch-transcript --url {_ID}",
        # chaining: a second command after a valid-looking one
        f"{_PY} -m {_MOD} fetch-transcript --url {_ID}; rm -rf /",
        f"{_PY} -m {_MOD} fetch-transcript --url {_ID} && curl evil",
        f"{_PY} -m {_MOD} fetch-transcript --url {_ID} | sh",
        # command substitution / backticks
        f"{_PY} -m {_MOD} fetch-transcript --url $(whoami)",
        f"{_PY} -m {_MOD} fetch-transcript --url `whoami`",
        # redirect to a file
        f"{_PY} -m {_MOD} fetch-transcript --url {_ID} > /etc/cron.d/x",
        # env-var / interpreter-shim prefix (e.g. LD_PRELOAD)
        f"LD_PRELOAD=/tmp/x.so {_PY} -m {_MOD} fetch-transcript --url {_ID}",
        f"env {_PY} -m {_MOD} fetch-transcript --url {_ID}",
        # wrong/extra module or subcommand
        f"{_PY} -m {_MOD} refresh-home",
        f"{_PY} -m os fetch-transcript --url {_ID}",
        # unknown flag / bare positional
        f"{_PY} -m {_MOD} fetch-transcript --url {_ID} --evil x",
        f"{_PY} -m {_MOD} fetch-transcript {_ID}",
        # malformed value (not an 11-char id) — traversal / injection attempts
        f"{_PY} -m {_MOD} fetch-transcript --url ../../etc/passwd",
        f'{_PY} -m {_MOD} fetch-transcript --url "a b"',
        # --url missing entirely
        f"{_PY} -m {_MOD} fetch-transcript --save",
        # not python at all
        f"bash -c '{_MOD} fetch-transcript'",
        # empty / junk
        "",
        "   ",
    ],
)
def test_injection_variants_blocked(cmd):
    assert _allowed(cmd) is False


# --- curator MAIN agent allowlist (recent read + cat of a wiki file) ----------
#
# The curator ingests scraped titles/description excerpts while holding terminal +
# delegate_task, so its terminal is restricted to the two shapes it actually uses.
# _WIKI_ROOT is the @@WIKI_PATH@@ placeholder at import time; build paths under it.

_curator_allowed = guard._is_allowed_curator_command
_WIKI = guard._WIKI_ROOT


@pytest.mark.parametrize(
    "cmd",
    [
        f"{_PY} -m {_MOD} recent --kind recommendations --limit 30",
        f"{_PY} -m {_MOD} recent --kind history --limit 30",
        f"python3 -m {_MOD} recent --kind history --limit 30 --offset 60",
        f"cd /home/x/repo && {_PY} -m {_MOD} recent --kind recommendations --limit 30",
        f"{_PY} -m {_MOD} recent --kind recommendations --limit 30 2>&1",
        f"{_PY} -m {_MOD} recent --kind=history --limit=30",
        f"cat {_WIKI}/interests.md",
    ],
)
def test_curator_legitimate_commands_allowed(cmd):
    assert _curator_allowed(cmd) is True


@pytest.mark.parametrize(
    "cmd",
    [
        # the subagent's command is NOT a curator command (different subcommand)
        f"{_PY} -m {_MOD} fetch-transcript --url {_ID} --save",
        # arbitrary subcommands / modules
        f"{_PY} -m {_MOD} refresh-home",
        f"{_PY} -m os recent --kind history",
        # missing required --kind, or a bad --kind value
        f"{_PY} -m {_MOD} recent --limit 30",
        f"{_PY} -m {_MOD} recent --kind everything --limit 30",
        # non-int numeric flags / unknown flags / bare positionals
        f"{_PY} -m {_MOD} recent --kind history --limit ten",
        f"{_PY} -m {_MOD} recent --kind history --evil x",
        f"{_PY} -m {_MOD} recent history",
        # cat escaping the wiki, traversal, relative, or extra args
        "cat /etc/passwd",
        f"cat {_WIKI}/../../etc/passwd",
        "cat interests.md",
        f"cat {_WIKI}/interests.md {_WIKI}/index.md",
        # -c / chaining / substitution / redirect / env prefix
        f'{_PY} -c "__import__(\'os\').system(\'id\')" #{_MOD} recent',
        f"{_PY} -m {_MOD} recent --kind history; rm -rf /",
        f"{_PY} -m {_MOD} recent --kind history | sh",
        f"{_PY} -m {_MOD} recent --kind $(whoami)",
        f"{_PY} -m {_MOD} recent --kind history > /etc/cron.d/x",
        f"env {_PY} -m {_MOD} recent --kind history",
        # empty / junk
        "",
        "   ",
    ],
)
def test_curator_injection_variants_blocked(cmd):
    assert _curator_allowed(cmd) is False
