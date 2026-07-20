# Agent instructions — LLM Wiki

The canonical schema for this vault lives in **[`CLAUDE.md`](CLAUDE.md)**. Read it in full before
any ingest, query, or lint pass.

This `agents.md` exists so non-Claude agents (e.g. OpenAI Codex) find the instructions by their
conventional filename. There is no separate content here — everything is in `CLAUDE.md` and the
`schema/` folder it references:

- [`CLAUDE.md`](CLAUDE.md) — layers, folder roles, ingest/query/lint workflows, conventions, tooling.
- [`purpose.md`](purpose.md) — why this vault exists and what it aims to become.
- [`schema/frontmatter-schema.md`](schema/frontmatter-schema.md) — page frontmatter + epistemic markers.
- [`schema/naming-conventions.md`](schema/naming-conventions.md) — slugs and page-type → folder map.
- [`schema/workflow-examples.md`](schema/workflow-examples.md) — worked recipes.
- [`schema/lint-checklist.md`](schema/lint-checklist.md) — the maintenance checklist.

Deterministic tooling: `py scripts/wiki_tool.py <doctor|build|lint|source-status|search|log>`.
