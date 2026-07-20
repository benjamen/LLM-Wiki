# CLAUDE.md — LLM Wiki operating instructions

This vault is a persistent, LLM-maintained knowledge base built on Andrej Karpathy's **LLM
Wiki** pattern. This file is the **canonical schema** — the "constitution" the agent follows.
Read it in full before any ingest, query, or lint pass. Behaviour changes by editing this file
and the `schema/` docs, not by writing code. (Codex users: `agents.md` points here.)

Read [`purpose.md`](purpose.md) too — it states *why* this vault exists and what it is trying to
become. Consult it on every ingest and query, and suggest updates when the direction drifts.

## The three layers

1. **`raw/`** — immutable source material (articles, transcripts, specs). Never edit or delete a
   raw file's content; it is the source of truth, so the wiki can always be re-compiled. Marking
   ingest status in raw frontmatter is the one allowed metadata touch.
2. **`wiki/`** — the LLM-owned knowledge base (this is what you query against). You write it; the
   human reads it.
3. **schema** — this file + `schema/` + `_templates/`. How the wiki is structured and maintained.

## Folder roles

- `raw/` — unprocessed sources. Permanent record. See layer 1 above.
- `wiki/summaries/` — one short summary page per raw source, in your own words (`type: summary`).
- `wiki/concepts/` — one page per durable concept/idea/framework (`type: concept`).
- `wiki/entities/` — one page per person, org, tool, or system (`type: entity`).
- `wiki/syntheses/` — cross-cluster argumentative overviews (`type: synthesis`); one per concept
  cluster. Layer 2 of the navigation cascade.
- `wiki/comparisons/` — side-by-side comparisons/tables (`type: comparison`).
- `wiki/queries/` — substantial query answers filed back as pages (`type: query`).
- `wiki/indexes/` — hand-curated catalogs: `SOURCE_CATALOG.md`, `ENTITY_INDEX.md`,
  `CONCEPT_INDEX.md`. Keep current. **Never auto-overwritten** by tooling.
- `wiki/overview.md` — a short global summary of the whole wiki; refresh it on each ingest.
- `wiki/catalog.jsonl` — machine catalog, **generated** by `wiki_tool.py build` (don't hand-edit).
- `outputs/` — substantial, reusable generated artifacts (reports, diagrams-as-markdown).
- `schema/` — detailed rules (see below). `_templates/` — one starter per page type.
- `scripts/wiki_tool.py` — deterministic maintenance tool. `log.md` — append-only timeline.

## Schema reference (read as needed)

- [`schema/frontmatter-schema.md`](schema/frontmatter-schema.md) — required fields, `related:`,
  epistemic markers, the supported YAML subset.
- [`schema/naming-conventions.md`](schema/naming-conventions.md) — slugs, page-type → folder map.
- [`schema/workflow-examples.md`](schema/workflow-examples.md) — worked ingest/query/lint recipes.
- [`schema/lint-checklist.md`](schema/lint-checklist.md) — the checklist `wiki_tool.py lint` enforces.

## Ingest pass (new files in `raw/`, or on request) — two steps

Karpathy's ingest is single-step; we split it (per nash_su) for quality.

**Step 1 — Analysis (read, don't write yet).** For each unprocessed source (`py
scripts/wiki_tool.py source-status --unprocessed`): read it fully and produce a short structured
analysis — key entities & concepts, connections to existing pages, contradictions/tensions with
what's already written, and which pages to create vs. update. Discuss with the human if they're
present.

**Step 2 — Generation (write).** From the analysis:
- Write/update `wiki/summaries/<slug>.md` (3–8 sentences, your own words).
- Create or update the concept/entity pages, folding new info in **in your own words** and adding
  `[[wikilinks]]` liberally (under-linking is the #1 failure mode). Keep `related:` current.
- On contradiction, **do not silently overwrite** — add a `## Tensions / open questions` section
  naming which sources disagree.
- Refresh `wiki/overview.md` and the relevant `wiki/indexes/` files.
- Set the raw file's frontmatter `status: processed` + `processed_date` (metadata only).
- `py scripts/wiki_tool.py build` then `py scripts/wiki_tool.py lint` (fix errors).
- `py scripts/wiki_tool.py log "<what changed>" --tag ingest`.

A single source typically touches 10–15 pages. Ingest one source at a time; supervise the first
several (see the onboarding guidance in `schema/workflow-examples.md`).

## Query pass (the user asks a question)

- Answer from `wiki/` (the compiled layer) — start at `wiki/indexes/`, follow `[[links]]` and
  `related:`. Only fall back to `raw/` if the wiki doesn't cover it. Use `py scripts/wiki_tool.py
  search "<terms>"` to locate pages.
- If the answer is a substantial, reusable artifact (comparison, briefing, synthesis), file it to
  `wiki/queries/` (or `wiki/comparisons/`, or `outputs/` if large) and link it from related pages.
  Quick facts: just answer.
- `py scripts/wiki_tool.py log "<question> → <what was filed>" --tag query`.

## Lint pass (periodically / on request)

Run `py scripts/wiki_tool.py lint` (and `build --check`). It checks frontmatter, valid `type`,
`sources` existence, broken `[[wikilinks]]`, and orphans. Then eyeball `schema/lint-checklist.md`
for the judgement items a script can't catch (stale claims, thin synthesis, missing markers).
Fix, then `log … --tag lint`.

## Conventions (summary — detail in `schema/`)

- Frontmatter on every wiki page: `type`, `aliases`, `created`, `updated`, `sources`, and
  (recommended) `related`. Summaries/pages must keep `sources` pointing at real `raw/` files.
- One idea per page; prefer many small linked pages over few long ones.
- **Epistemic markers** in prose: unmarked = wiki-synthesis; `[P]` our own position; `[?]`
  uncertain/unverified; source-attributable claims cite the summary/raw. See the frontmatter doc.
- Never edit `raw/` content or hand-edit `wiki/catalog.jsonl`. Everything is a git repo of
  markdown — commit in logical chunks.

## Tooling quickref

```
py scripts/wiki_tool.py doctor          # health check
py scripts/wiki_tool.py build           # regenerate wiki/catalog.jsonl
py scripts/wiki_tool.py lint            # validate (errors block the pre-commit hook)
py scripts/wiki_tool.py source-status   # which raw/ sources are processed
py scripts/wiki_tool.py search "<q>"    # keyword search over pages
py scripts/wiki_tool.py log "<msg>" --tag ingest|query|lint|maintain
```
A pre-commit hook runs `build` + `lint` automatically. One-time setup on a fresh clone:
`git config core.hooksPath .githooks` (see `README.md`). Windows: Python is the `py` launcher.
