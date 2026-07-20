# Frontmatter schema

Every page in `wiki/` (except the hand-curated `wiki/indexes/*` and `wiki/overview.md`) starts
with a YAML frontmatter block. Keep it to the forms below — `scripts/wiki_tool.py` uses a
**narrow, hand-written parser** (no PyYAML) that understands only these shapes. Anything fancier
(nested maps, `>`/`|` block scalars, flow maps) will be mis-read; `lint` flags any page that
fails to yield the required keys, so errors fail loud rather than silently.

## Fields

```yaml
---
type: concept | entity | summary | synthesis | comparison | query   # REQUIRED
aliases: [Display Name, alt name, "name, with comma"]                 # REQUIRED (may be empty [])
created: YYYY-MM-DD                                                   # REQUIRED
updated: YYYY-MM-DD                                                   # REQUIRED
sources:                                                              # REQUIRED (block list)
  - "raw/some-source.md"
related: [other-slug, another-slug]                                  # RECOMMENDED (3–5 neighbours)
---
```

- **`type`** — one of the six values; determines the folder (see `naming-conventions.md`).
- **`aliases`** — inline array. Every alias becomes a resolvable `[[wikilink]]` target, so keep
  them **unique across the vault** (lint warns on collisions). Quote any item containing a comma.
- **`created` / `updated`** — ISO dates. Bump `updated` whenever you meaningfully change a page.
- **`sources`** — block list of paths to `raw/` files that support the page. `lint` errors if a
  listed file doesn't exist. Summaries have exactly one; synthesis/concept pages often several.
- **`related`** — inline array of nearest-neighbour slugs (navigation cascade, layer 3). Optional
  but recommended; `wiki_tool` can suggest candidates from link co-occurrence.

## Supported YAML subset (what the parser accepts)

- `key: value` — scalar (optional surrounding quotes stripped).
- `key: [a, b, "c, d"]` — inline array (split on commas **outside** double quotes).
- `key:` then indented `  - item` lines — block list.

That is all. No nested structures.

## Epistemic markers (in the body, not frontmatter)

Adapted from Paulo de Assis. Because our concept/synthesis pages are inherently cross-source
synthesis, the **default (unmarked) prose on a concept/synthesis page is wiki-synthesis**. Use
inline markers only to flag the exceptions:

- `[P]` — **our own position / editorial recommendation**, not something a source says.
- `[?]` — **uncertain / unverified** (a shaky date, attribution, or inference). Pair with a note.
- Source-attributable claims should cite the summary or raw source (e.g. via `[[summary-slug]]`)
  rather than a marker.

Example: `The pattern likely suits teams of <10 [P], though no source tests this [?].`

Keep markers sparse and meaningful — they are a targeted defence against
[[hallucination-propagation]], not decoration. `lint`/the checklist flag synthesis pages that
make strong claims with neither a citation nor a marker.
