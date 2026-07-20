#!/usr/bin/env python3
"""wiki_tool.py — deterministic maintenance tool for the LLM Wiki vault.

Stdlib only. Designed for Windows where Python is reachable via the `py` launcher:

    py scripts/wiki_tool.py <command> [options]

Commands:
    doctor         Non-mutating health check (dirs, py version, hooksPath, counts).
    build          Regenerate wiki/catalog.jsonl (machine catalog). Does NOT rewrite
                   the hand-curated wiki/indexes/*.md (except inside opt-in auto markers).
    lint           Validate frontmatter, page types, source links, and [[wikilinks]].
    source-status  List raw/ sources by processed state (alias: source-scan).
    search         Keyword search over wiki pages.
    log            Append a dated entry to log.md.

Exit codes: 0 = ok, 1 = errors found, 2 = usage/IO error.

The frontmatter parser is deliberately narrow — it handles only the forms this vault
uses (scalars, inline `[a, b, "c"]` arrays, and `key:` + `  - item` block lists). Any
page whose frontmatter does not yield the required keys is reported by `lint` rather
than silently mis-parsed.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
WIKI = ROOT / "wiki"
INDEX_DIR = WIKI / "indexes"
LOG = ROOT / "log.md"
CATALOG = WIKI / "catalog.jsonl"

# Folders that hold frontmatter'd wiki pages (some may not exist yet).
PAGE_DIRS = [
    WIKI / "concepts",
    WIKI / "entities",
    WIKI / "summaries",
    WIKI / "syntheses",
    WIKI / "comparisons",
    WIKI / "queries",
]
VALID_TYPES = {"concept", "entity", "summary", "synthesis", "comparison", "query"}
REQUIRED_FIELDS = ["type", "aliases", "created", "updated", "sources"]

AUTO_BEGIN = "<!-- wiki_tool:auto:begin -->"
AUTO_END = "<!-- wiki_tool:auto:end -->"


# --------------------------------------------------------------------------- #
# IO + parsing helpers
# --------------------------------------------------------------------------- #
def read_text(path):
    return path.read_text(encoding="utf-8")


def split_inline_array(s):
    """Split the inside of `[a, b, "c, d"]` on commas outside double quotes."""
    items, buf, in_q = [], [], False
    for ch in s:
        if ch == '"':
            in_q = not in_q
            buf.append(ch)
        elif ch == "," and not in_q:
            items.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        items.append("".join(buf))
    return [_unquote(x) for x in items]


def _unquote(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
        return s[1:-1].strip()
    return s


def split_frontmatter(text):
    """Return (frontmatter_dict, body, fm_line_count). ({},text,0) if no block."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, 0
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1:])
            return parse_frontmatter(fm), body, i + 1
    return {}, text, 0  # unterminated block -> treat as no frontmatter


def parse_frontmatter(fm):
    data = {}
    lines = fm.splitlines()
    i = 0
    key_re = re.compile(r"^([A-Za-z_][\w-]*):\s?(.*)$")
    while i < len(lines):
        line = lines[i]
        m = key_re.match(line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if val.startswith("[") and val.endswith("]"):
            data[key] = split_inline_array(val[1:-1])
        elif val == "":
            # possible block list on following indented "- " lines
            items = []
            j = i + 1
            while j < len(lines) and re.match(r"^\s+-\s+", lines[j]):
                items.append(_unquote(re.sub(r"^\s+-\s+", "", lines[j])))
                j += 1
            if items:
                data[key] = items
                i = j
                continue
            data[key] = ""
        else:
            data[key] = _unquote(val)
        i += 1
    return data


def strip_code(text):
    """Blank out fenced blocks (preserving line count) then inline code spans."""
    def repl_fence(m):
        return "\n" * m.group(0).count("\n")

    text = re.sub(r"(?ms)^[ \t]*```.*?^[ \t]*```", repl_fence, text)

    def repl_inline(m):
        return " " * len(m.group(0))

    text = re.sub(r"(`+)(.+?)\1", repl_inline, text)
    return text


LINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")


def extract_links(text):
    """Yield (target, lineno) for each [[wikilink]] in code-stripped text."""
    stripped = strip_code(text)
    out = []
    for m in LINK_RE.finditer(stripped):
        raw = m.group(1).replace("\\|", "|")  # unescape table-escaped pipes
        target = raw.split("|")[0].split("#")[0].strip()
        if target:
            lineno = stripped[: m.start()].count("\n") + 1
            out.append((target, lineno))
    return out


def slug_of(path):
    return path.stem


def h1_title(body):
    for line in body.splitlines():
        m = re.match(r"^#\s+(.+)$", line)
        if m:
            return m.group(1).strip()
    return None


def existing_page_dirs():
    return [d for d in PAGE_DIRS if d.is_dir()]


def iter_pages():
    """Yield (path, meta, body) for every wiki page in the typed page dirs."""
    for d in existing_page_dirs():
        for path in sorted(d.glob("*.md")):
            text = read_text(path)
            meta, body, _ = split_frontmatter(text)
            yield path, meta, body


def index_files():
    if not INDEX_DIR.is_dir():
        return []
    return sorted(INDEX_DIR.glob("*.md"))


def rel(path):
    return path.relative_to(ROOT).as_posix()


def build_resolution_index():
    """Map lowercased basename & aliases -> page path. Returns (index, collisions)."""
    idx, collisions = {}, []
    def add(key, path):
        k = key.strip().lower()
        if not k:
            return
        if k in idx and idx[k] != path:
            collisions.append((k, idx[k], path))
        else:
            idx.setdefault(k, path)
    for path, meta, _ in iter_pages():
        add(slug_of(path), path)
        aliases = meta.get("aliases", [])
        if isinstance(aliases, list):
            for a in aliases:
                add(a, path)
    # index files and overview are valid link targets, not "pages"
    for path in index_files():
        add(slug_of(path), path)
    if (WIKI / "overview.md").exists():
        add("overview", WIKI / "overview.md")
    return idx, collisions


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def cmd_doctor(args):
    ok = True
    print("wiki_tool doctor\n" + "-" * 40)
    print(f"[info] python : {sys.version.split()[0]}")
    print(f"[info] root   : {ROOT}")

    required_dirs = [RAW, WIKI, INDEX_DIR, WIKI / "concepts", WIKI / "summaries"]
    for d in required_dirs:
        mark = "ok  " if d.is_dir() else "FAIL"
        if not d.is_dir():
            ok = False
        print(f"[{mark}] dir {rel(d)}")
    for d in [WIKI / "entities", WIKI / "syntheses", WIKI / "comparisons", WIKI / "queries"]:
        mark = "ok  " if d.is_dir() else "warn"
        print(f"[{mark}] dir {rel(d)}")

    for f in [ROOT / "agents.md", LOG, ROOT / "scripts" / "wiki_tool.py"]:
        mark = "ok  " if f.exists() else "warn"
        print(f"[{mark}] file {rel(f)}")
    hook = ROOT / ".githooks" / "pre-commit"
    print(f"[{'ok  ' if hook.exists() else 'warn'}] file {rel(hook)}")

    try:
        hp = subprocess.run(
            ["git", "config", "--get", "core.hooksPath"],
            cwd=str(ROOT), capture_output=True, text=True,
        ).stdout.strip()
    except Exception:
        hp = ""
    print(f"[{'ok  ' if hp else 'warn'}] core.hooksPath = {hp or '(unset)'}")

    counts = {}
    for path, meta, _ in iter_pages():
        counts[meta.get("type", "?")] = counts.get(meta.get("type", "?"), 0) + 1
    print(f"[info] pages  : {dict(sorted(counts.items()))}")
    raw_n = len(list(RAW.glob("*.md"))) if RAW.is_dir() else 0
    print(f"[info] raw    : {raw_n} source files")
    if CATALOG.exists():
        newest = max((p.stat().st_mtime for p, _, _ in iter_pages()), default=0)
        fresh = CATALOG.stat().st_mtime >= newest
        print(f"[{'ok  ' if fresh else 'warn'}] catalog.jsonl {'fresh' if fresh else 'STALE (run build)'}")
    else:
        print("[warn] catalog.jsonl missing (run build)")
    return 0 if ok else 1


def _catalog_lines():
    rows = []
    for path, meta, body in iter_pages():
        rows.append({
            "path": rel(path),
            "type": meta.get("type", ""),
            "title": h1_title(body) or slug_of(path),
            "aliases": meta.get("aliases", []) if isinstance(meta.get("aliases"), list) else [],
            "sources": meta.get("sources", []) if isinstance(meta.get("sources"), list) else [],
            "updated": meta.get("updated", ""),
            "slug": slug_of(path),
        })
    rows.sort(key=lambda r: r["path"])
    return [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in rows]


def _auto_stats_block():
    counts = {}
    for _, meta, _ in iter_pages():
        counts[meta.get("type", "?")] = counts.get(meta.get("type", "?"), 0) + 1
    parts = ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
    return f"_Auto-generated by wiki_tool build — {parts}._"


def cmd_build(args):
    content = "\n".join(_catalog_lines())
    if content:
        content += "\n"
    if args.check:
        current = read_text(CATALOG) if CATALOG.exists() else ""
        if current != content:
            print("catalog.jsonl is STALE — run: py scripts/wiki_tool.py build")
            return 1
        print("catalog.jsonl is up to date.")
        return 0
    CATALOG.write_text(content, encoding="utf-8")
    print(f"wrote {rel(CATALOG)} ({len(content.splitlines())} pages)")

    # Refresh only opt-in auto-marker regions in index files; never clobber prose.
    for path in index_files():
        text = read_text(path)
        if AUTO_BEGIN in text and AUTO_END in text:
            new = re.sub(
                re.escape(AUTO_BEGIN) + r".*?" + re.escape(AUTO_END),
                AUTO_BEGIN + "\n" + _auto_stats_block() + "\n" + AUTO_END,
                text, flags=re.DOTALL,
            )
            if new != text:
                path.write_text(new, encoding="utf-8")
                print(f"updated auto block in {rel(path)}")
    return 0


def cmd_lint(args):
    errors, warnings = [], []
    resolution, collisions = build_resolution_index()
    for k, a, b in collisions:
        warnings.append(f"duplicate link key '{k}': {rel(a)} vs {rel(b)}")

    inbound = {}  # page path -> count of inbound links from other pages/indexes
    pages = list(iter_pages())
    page_paths = {p for p, _, _ in pages}

    def resolve(target):
        return resolution.get(target.strip().lower())

    # frontmatter + type + sources + link validation
    for path, meta, body in pages:
        r = rel(path)
        for f in REQUIRED_FIELDS:
            if f not in meta or meta.get(f) in ("", None):
                errors.append(f"{r}: missing required frontmatter field '{f}'")
        t = meta.get("type", "")
        if t and t not in VALID_TYPES:
            errors.append(f"{r}: invalid type '{t}' (allowed: {sorted(VALID_TYPES)})")
        srcs = meta.get("sources", [])
        if isinstance(srcs, list):
            for s in srcs:
                if not (ROOT / s).exists():
                    errors.append(f"{r}: source not found: {s}")

    # link resolution across pages AND index files (so index links are checked too)
    link_sources = [(p, read_text(p)) for p in page_paths] + [(p, read_text(p)) for p in index_files()]
    overview = WIKI / "overview.md"
    if overview.exists():
        link_sources.append((overview, read_text(overview)))
    for path, text in link_sources:
        for target, lineno in extract_links(text):
            dest = resolve(target)
            if dest is None:
                errors.append(f"{rel(path)}:{lineno}: broken wikilink [[{target}]]")
            elif dest in page_paths and dest != path:
                inbound[dest] = inbound.get(dest, 0) + 1

    # orphans (warning): a page with no inbound link at all
    for path, _, _ in pages:
        if inbound.get(path, 0) == 0:
            warnings.append(f"orphan (no inbound links): {rel(path)}")

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print("-" * 40)
    print(f"{len(errors)} error(s), {len(warnings)} warning(s) across {len(pages)} pages")
    if errors:
        return 1
    if warnings and args.strict:
        return 1
    return 0


def cmd_source_status(args):
    if not RAW.is_dir():
        print("no raw/ dir", file=sys.stderr)
        return 2
    processed, unprocessed = [], []
    for path in sorted(RAW.glob("*.md")):
        meta, _, _ = split_frontmatter(read_text(path))
        status = meta.get("status", "")
        if status == "processed":
            processed.append((path.name, meta.get("processed_date", "")))
        else:
            unprocessed.append(path.name)
    if args.unprocessed:
        for name in unprocessed:
            print(name)
        return 0
    print(f"processed ({len(processed)}):")
    for name, d in processed:
        print(f"  [x] {name}  ({d})")
    print(f"unprocessed ({len(unprocessed)}):")
    for name in unprocessed:
        print(f"  [ ] {name}")
    return 0


def cmd_search(args):
    terms = [t.lower() for t in args.query]
    results = []
    for path, meta, body in iter_pages():
        title = (h1_title(body) or slug_of(path)).lower()
        aliases = " ".join(meta.get("aliases", []) if isinstance(meta.get("aliases"), list) else []).lower()
        text = strip_code(body).lower()
        score = 0
        matched_all = True
        for t in terms:
            hits = title.count(t) * 5 + aliases.count(t) * 4 + text.count(t)
            if hits == 0:
                matched_all = False
            score += hits
        if score and (matched_all or args.any):
            results.append((score, rel(path), h1_title(body) or slug_of(path)))
    results.sort(reverse=True)
    if not results:
        print("no matches")
        return 0
    for score, r, title in results[: args.limit]:
        print(f"{score:4d}  {r}  — {title}")
    return 0


def cmd_log(args):
    tag = args.tag or "note"
    line = f"\n{date.today().isoformat()} — {tag} — {args.message}\n"
    existing = read_text(LOG) if LOG.exists() else "# Log\n"
    if not existing.endswith("\n"):
        existing += "\n"
    LOG.write_text(existing + line, encoding="utf-8")
    print(f"appended to {rel(LOG)}: {tag} — {args.message}")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv=None):
    try:  # keep Unicode output safe on Windows consoles (cp1252)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    p = argparse.ArgumentParser(prog="wiki_tool", description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="health check")

    pb = sub.add_parser("build", help="regenerate catalog.jsonl")
    pb.add_argument("--check", action="store_true", help="compare only; exit 1 if stale")

    pl = sub.add_parser("lint", help="validate the wiki")
    pl.add_argument("--strict", action="store_true", help="treat warnings as errors")

    for name in ("source-status", "source-scan"):
        ps = sub.add_parser(name, help="list raw sources by processed state")
        ps.add_argument("--unprocessed", action="store_true", help="print unprocessed basenames only")

    psr = sub.add_parser("search", help="keyword search over wiki pages")
    psr.add_argument("query", nargs="+")
    psr.add_argument("--limit", type=int, default=20)
    psr.add_argument("--any", action="store_true", help="match any term instead of all")

    pg = sub.add_parser("log", help="append a dated entry to log.md")
    pg.add_argument("message")
    pg.add_argument("--tag", default=None, help="ingest|query|lint|build|reorg|maintain|note")

    args = p.parse_args(argv)
    dispatch = {
        "doctor": cmd_doctor,
        "build": cmd_build,
        "lint": cmd_lint,
        "source-status": cmd_source_status,
        "source-scan": cmd_source_status,
        "search": cmd_search,
        "log": cmd_log,
    }
    try:
        return dispatch[args.cmd](args)
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    sys.exit(main())
