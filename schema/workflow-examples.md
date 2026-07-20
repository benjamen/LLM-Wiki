# Workflow examples

Worked recipes for the three operations. See `CLAUDE.md` for the authoritative summary.

## Two-step ingest

```
# 1. Find unprocessed sources
py scripts/wiki_tool.py source-status --unprocessed

# 2. STEP 1 — Analysis (read only). For the source, note:
#    - key entities & concepts it introduces or adds evidence to
#    - connections to existing pages (search first)
py scripts/wiki_tool.py search "<a key term from the source>"
#    - contradictions/tensions with existing pages
#    - the list of pages to CREATE vs UPDATE

# 3. STEP 2 — Generation (write), guided by the analysis:
#    - wiki/summaries/<author-topic>.md   (3–8 sentences, your words)
#    - create/update concept & entity pages; add [[wikilinks]] + related:
#    - add "## Tensions / open questions" where sources disagree
#    - refresh wiki/overview.md and wiki/indexes/*

# 4. Mark the source processed (metadata only; never touch raw body)
#    add to its frontmatter:  status: processed  /  processed_date: YYYY-MM-DD

# 5. Rebuild + validate + log
py scripts/wiki_tool.py build
py scripts/wiki_tool.py lint
py scripts/wiki_tool.py log "Ingested <source>: +N pages, updated M" --tag ingest
```

**Onboarding / supervision (Paulo de Assis):** the wiki is *not* your whole library — copy a
source into `raw/` only when ready. Supervise the first ~5–15 ingests closely; batch-ingest only
once the wiki has enough structure to guide itself. Priority test: *"would I cite this in
something I'm writing now?"*

## Query

```
py scripts/wiki_tool.py search "compounding knowledge"
# read the top pages + follow [[links]] and related:; answer from wiki/, not raw/
# if the answer is reusable, file it:
#   wiki/queries/<slug>.md      (analysis / synthesis answer)
#   wiki/comparisons/<slug>.md  (a table)
#   outputs/<slug>.md           (large artifact) and link it from related pages
py scripts/wiki_tool.py log "Q: <question> → filed wiki/queries/<slug>.md" --tag query
```

## Lint / maintain

```
py scripts/wiki_tool.py build --check   # is catalog.jsonl current?
py scripts/wiki_tool.py lint            # 0 errors expected; fix any
# then eyeball schema/lint-checklist.md for judgement items
py scripts/wiki_tool.py log "Lint: <findings/fixes>" --tag lint
```
