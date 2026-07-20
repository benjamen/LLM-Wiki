# Lint checklist

`py scripts/wiki_tool.py lint` enforces the mechanical checks. This file adds the judgement checks
a script can't make. Run both during a lint pass.

## Automated (enforced by `wiki_tool.py lint` — errors block the pre-commit hook)

- [ ] Every page has all required frontmatter: `type`, `aliases`, `created`, `updated`, `sources`.
- [ ] `type` is one of concept|entity|summary|synthesis|comparison|query.
- [ ] Every `sources:` entry points to an existing file in `raw/`.
- [ ] No broken `[[wikilinks]]` (resolved by basename ∪ aliases, ignoring code spans).
- [ ] No orphan pages (0 inbound links) — *warning*.
- [ ] No duplicate slug/alias keys — *warning*.
- [ ] `wiki/catalog.jsonl` is current (`build --check`).

## Judgement (human/agent review — not automatable)

- [ ] **Contradictions** — do any pages disagree without a `## Tensions / open questions`
      section naming the disagreeing sources?
- [ ] **Stale claims** — has a newer source superseded something an older page still asserts?
- [ ] **Thin synthesis** — concept pages with only one source that should be enriched, or
      synthesis pages that just list instead of arguing.
- [ ] **Missing epistemic markers** — strong claims on synthesis pages with neither a citation
      nor a `[P]`/`[?]` marker (see `frontmatter-schema.md`).
- [ ] **Under-linking** — pages that should reference each other but don't; missing `related:`.
- [ ] **Index drift** — do `wiki/indexes/*` and `wiki/overview.md` reflect the current pages and
      counts? (These are hand-curated; the tool never rewrites them.)
- [ ] **Missing pages** — concepts referenced in prose that deserve their own page but lack one
      (a `[[link]]` to a not-yet-written page is fine as a marker, but track the important ones).
- [ ] **Purpose alignment** — is new content in scope per `purpose.md`?

Record findings and fixes with `py scripts/wiki_tool.py log "…" --tag lint`.
