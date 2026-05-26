<!--
Sync Impact Report
Version change: unversioned template -> 1.0.0
Modified principles:
- Template Principle 1 -> I. Prefer One Simple Path
- Template Principle 2 -> II. Stay Close to the Proven Stack
- Template Principle 3 -> III. Separate Concerns with Deep Modules
- Template Principle 4 -> IV. Test the Seams
- Template Principle 5 -> V. Verify Against Current Sources
Added sections:
- Engineering Boundaries
- Delivery Workflow
Removed sections:
- None
Templates requiring updates:
- ✅ .specify/templates/plan-template.md
- ✅ .specify/templates/spec-template.md
- ✅ .specify/templates/tasks-template.md
- ✅ README.md
- ✅ AGENTS.md
- ⚠ pending: .specify/templates/commands/*.md (directory not present in this repo)
Follow-up TODOs:
- None
-->

# HermesYoutubeCurator Constitution

## Core Principles

### I. Prefer One Simple Path
Every feature MUST begin with the simplest execution path that solves the real
requirement. If an approach does not work, it MUST be removed or replaced, not
kept behind a fallback branch, alternate flow, or speculative abstraction.
Multiple branches for the same execution are allowed only when the user-facing
requirement itself demands them and the distinction is explicit in the spec.
Rationale: a single path is easier to reason about, debug, and maintain.

### II. Stay Close to the Proven Stack
The default stack MUST remain close to this repository's current shape: Python,
API-oriented libraries, Playwright when browser automation is required, and
Markdown-based skills and agent guidance. New frameworks, orchestration layers,
or infrastructure-heavy subsystems MUST be rejected unless the simpler stack
cannot satisfy a concrete requirement recorded in the plan. Rationale: this
project values leverage from familiar tools over novelty or architectural reach.

### III. Separate Concerns with Deep Modules
New behavior MUST be introduced behind small, explicit interfaces and placed in
separate modules when it represents a distinct concern. Modules SHOULD be deep:
they SHOULD hide substantial behavior behind a simple API instead of spreading
logic across many shallow helpers. Plans and specs MUST describe the seams
between modules so responsibilities stay clear. Rationale: clean seams reduce
coupling and make change safer.

### IV. Test the Seams
When tests are justified, they MUST verify the seams between modules, adapters,
and external dependencies rather than private implementation details. Unit or
integration labels matter less than the target: tests MUST exercise contracts,
data flow, and failure handling at module boundaries. Tests that mainly mirror
internal code structure SHOULD be rejected. Rationale: seam-focused tests stay
stable while still protecting behavior that matters.

### V. Verify Against Current Sources
Engineers MUST not rely on memory for nontrivial library, API, or framework
behavior. Before implementation, they MUST consult current documentation and
SHOULD prefer primary sources such as official docs, upstream repositories, or
local installed source when available. Plans, research notes, or implementation
notes MUST record the sources consulted for decisions that depend on external
behavior. Rationale: current source verification is the only reliable guard
against stale assumptions.

## Engineering Boundaries

- Prefer direct Python modules, small adapters, and explicit data flow over
  global orchestration or hidden control paths.
- Reject speculative extensibility, generic plugin systems, or extra layers
  unless the current feature requires them now.
- Keep repository structure legible; new modules must have a clear owner
  concern and a narrow public surface.
- External services and libraries must be wrapped at the seam where the project
  depends on them so callers use project-shaped interfaces rather than vendor
  details.

## Delivery Workflow

- Every specification MUST state the simplest acceptable implementation and any
  stack constraints before design work expands.
- Every implementation plan MUST include a constitution check covering
  simplicity, stack fit, module seams, seam-focused testing, and source
  verification.
- When a new dependency or unfamiliar API is involved, the relevant current
  documentation or source reference MUST be captured in the plan, research, or
  task artifacts before coding proceeds.
- Code review and self-review MUST reject changes that preserve failed ideas as
  fallbacks, mix unrelated concerns, or add tests away from the architectural
  seams.

## Governance

This constitution overrides local habit and template defaults. Amendments
require updating this file, recording the rationale in the Sync Impact Report,
and propagating the change to affected templates and guidance documents in the
same change set when possible.

Versioning policy follows semantic versioning for governance:
- MAJOR for incompatible principle removals or redefinitions.
- MINOR for new principles or materially expanded obligations.
- PATCH for clarifications that do not change expected behavior.

Compliance review is mandatory during planning, implementation, and review.
Every plan, task list, and merge-ready change MUST show how it satisfies the
principles above or explicitly justify a narrow exception.

**Version**: 1.0.0 | **Ratified**: 2026-05-26 | **Last Amended**: 2026-05-26
