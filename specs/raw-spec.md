# YouTube Curator — Hermes Architecture Spec

## Goal

Build a personal YouTube curator that:

* monitors my logged-in YouTube homepage/feed
* extracts recommendations and metadata
* uses Hermes Agent for orchestration, memory, and long-term curation
* uses a local model for reasoning/summarization
* generates digests, ideas, scripts, and research directions
* operates with strong guardrails

---

# Core Philosophy

Separate:

* deterministic extraction
* agent reasoning
* memory/orchestration

The agent should not freely browse the web initially.

Instead:

```text
scripts sense the world
Hermes interprets the world
```

---

# High-Level Architecture

```text
scheduled script
  ↓
logged-in YouTube session
  ↓
extract structured snapshot
  ↓
wake Hermes Agent
  ↓
Hermes curator skill
  ↓
digests + ideas + summaries + memory proposals
```

---

# Why Hermes

Hermes is primarily useful for:

* scheduled recurring runs
* persistent memory
* reusable skills
* long-term project continuity
* orchestration
* idea accumulation
* recurring workflows
* conversational interaction

Hermes is NOT the main browser safety layer.

---

# System Responsibilities

## Extraction Layer

Deterministic Python scripts should:

* open logged-in YouTube
* extract recommendations/feed data
* fetch metadata/transcripts/descriptions
* generate structured snapshots
* decide whether to wake Hermes

The extraction layer should remain:

* simple
* deterministic
* constrained
* read-only

---

## Hermes Layer

Hermes should:

* curate recommendations
* detect recurring topics/themes
* summarize content
* propose research directions
* generate video ideas
* generate script ideas/outlines
* connect videos to ongoing interests/projects
* maintain long-term preference memory
* organize follow-up actions

Hermes should operate on structured snapshots rather than raw browsing.

---

# Suggested Workflow

```text
cron/scheduler
  ↓
YouTube extraction script
  ↓
compare against previous snapshots
  ↓
if meaningful changes:
    wake Hermes
else:
    skip run
```

---

# Proposed Hermes Skills

## youtube-curator

Responsibilities:

* rank recommendations
* identify high-signal content
* generate watch/save/skip lists
* detect themes

---

## video-idea-miner

Responsibilities:

* extract possible content ideas
* identify interesting arguments/questions
* generate hooks/titles
* suggest essay/video directions

---

## research-synthesizer

Responsibilities:

* connect videos across time
* summarize recurring concepts
* identify emerging interests
* generate deeper research paths

---

## memory-maintainer

Responsibilities:

* propose preference updates
* identify repeated interests
* organize long-term curator memory

Memory updates should ideally require approval.

---

# Guardrail Philosophy

Constrain the environment instead of relying on prompt safety.

Important principles:

* read-only behavior
* limited tool access
* restricted navigation
* structured inputs
* structured outputs
* isolated runtime
* conservative memory updates

---

# Important Design Principle

The local model should not directly control:

* arbitrary browser navigation
* account interactions
* filesystem access
* shell execution
* unrestricted tools

The browser should behave more like:

```text
sensor layer
```

rather than:

```text
autonomous operator
```

---

# Long-Term Direction

Potential future capabilities:

* evolving taste profile
* recommendation drift analysis
* semantic clustering of interests
* learning trajectory tracking
* content pipeline generation
* automatic research queues
* idea incubation over time
* personal media knowledge base

---

# Development Strategy

Start with:

1. stable browser extraction
2. structured snapshots
3. Hermes scheduled runs
4. basic curator skill
5. memory + recurring themes
6. idea generation
7. deeper synthesis later

Avoid building a fully autonomous browsing agent initially.

---

# Core Insight

The real value is not:

```text
agent watches YouTube
```

The real value is:

```text
persistent system that develops an evolving model
of my interests, research directions, and creative ideas
across weeks and months
```
