# Naming conventions

## Slugs (filenames)

- Lowercase kebab-case: `compounding-knowledge.md`, `andrej-karpathy.md`.
- One concept/entity per file. The slug is the primary `[[wikilink]]` target, so make it stable
  and descriptive; add human-readable forms as `aliases`.
- Obsidian resolves `[[links]]` by **basename**, independent of folder — so a page can move
  between `wiki/` subfolders without breaking links. Keep slugs unique across the whole vault
  (two files with the same basename in different folders create an ambiguous target).
- Avoid spaces and punctuation in wiki slugs. (Raw source filenames may contain spaces, commas,
  and apostrophes — that's fine; only `wiki/` pages follow this rule.)

## Page type → folder map

| `type`        | Folder               | What it holds |
|---------------|----------------------|---------------|
| `summary`     | `wiki/summaries/`    | one per raw source, in your own words |
| `concept`     | `wiki/concepts/`     | durable ideas, frameworks, terms |
| `entity`      | `wiki/entities/`     | people, orgs, tools, systems |
| `synthesis`   | `wiki/syntheses/`    | argumentative overview across a cluster |
| `comparison`  | `wiki/comparisons/`  | side-by-side tables / contrasts |
| `query`       | `wiki/queries/`      | substantial filed query answers |

Non-page files: `wiki/indexes/*` (catalogs, hand-curated), `wiki/overview.md` (global summary),
`wiki/catalog.jsonl` (generated). Large generated artifacts go in `outputs/`.

## Summary-page slugs

Summaries are named after the **source**, not a concept, to avoid basename collisions with concept
pages — e.g. `karpathy-llm-wiki-gist.md`, `mcveety-okf-data-sharing.md` (typically
`<author>-<topic>`).

## Aliases

Give each page the natural display names people might link with (`[[RAG]]`, `[[Retrieval-Augmented
Generation]]`). Keep them unique — `lint` warns on duplicate alias/slug keys.
