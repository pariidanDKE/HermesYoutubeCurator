# HermesYoutubeCurator Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-05-26

## Active Technologies

- Python 3.11+ + Playwright, YouTube Data API v3 client, `youtube-transcript-api`, Hermes Agent, vLLM, SQLite client library, Pydantic-style data validation, pytest (001-youtube-curator)

## Project Structure

```text
src/
tests/
```

## Commands

cd src && pytest && ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes

- 001-youtube-curator: Added Python 3.11+ + Playwright, YouTube Data API v3 client, `youtube-transcript-api`, Hermes Agent, vLLM, SQLite client library, Pydantic-style data validation, pytest

<!-- MANUAL ADDITIONS START -->
- Follow `.specify/memory/constitution.md` for repository-wide engineering rules.
- Default to one simple execution path, a conservative Python-centric stack,
  clear module seams, seam-focused tests, and current-source verification.
<!-- MANUAL ADDITIONS END -->
