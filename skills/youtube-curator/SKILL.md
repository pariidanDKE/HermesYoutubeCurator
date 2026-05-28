# YouTube Curator Skill

Use this skill to shape Telegram-facing curator output after deterministic collection and enrichment have already happened in Python.

## Scope

- Keep section order fixed: summary, watch now, save for later, skip for now, ideas, memory proposals.
- Include direct video links when available.
- Prefer concise reasons over long narration.
- Use the bundled `youtube-content` skill as the preferred transcript workflow whenever transcript-aware summarization is needed.
- Do not introduce MCP tools or alternate browsing paths.

## Top Guidance

- Start with the strongest recommendation first.
- Keep the opening summary to 2-3 sentences.
- Mention when ranking relied on homepage-only evidence because history was unavailable.

## Bottom Guidance

- End with one concrete idea or research direction when evidence supports it.
- Present long-term preference changes as explicit proposals, never as applied facts.
