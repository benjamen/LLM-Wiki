# Log

Running timeline of ingest, query, lint, and maintenance passes. Append only — don't rewrite
history. Use `py scripts/wiki_tool.py log "<msg>" --tag <ingest|query|lint|maintain>` to append.

## Format
`YYYY-MM-DD — [ingest|query|lint|maintain] — what happened`

---

2026-07-20 — setup — Template vault created (structure, tooling, schema, and templates carried
over from the llm-wiki best-practice vault; all content emptied). Fill in purpose.md, drop sources
into raw/, then run an ingest pass.
