"""The provenance record of a generator: where its numbers come from, how they were verified, what is not guaranteed.
tools/provenance writes PROVENANCE.md from this; nothing here is typed by hand, so the file cannot claim more than was done.

Guarantee levels (one badge): Checked = the automatic spec check passes for every code in codes.txt; Reviewed = Checked plus an
independent reviewer's sign-off (review.toml); Drawing-matched = Reviewed plus a drawing match (drawing-match.toml). Nothing below
Checked can be published (tools/build-index refuses it).
"""
from __future__ import annotations
import hashlib, json, re, tomllib
from pathlib import Path
from runtime.registry import Generator

LEVELS = ("Checked", "Reviewed", "Drawing-matched")

def _ver_key(v: str):
    return tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.-]", v))

def sources_hash(g: Generator) -> str:
    h = hashlib.sha256()
    for p in [g.dir / "sources.toml", *sorted((g.dir / "data").glob("*.csv"))]:
        h.update(p.name.encode()); h.update(b"\0"); h.update(p.read_bytes()); h.update(b"\0")
    return "sha256:" + h.hexdigest()

def sources(g: Generator) -> dict:
    return tomllib.loads((g.dir / "sources.toml").read_text())

def check_versions(g: Generator) -> list[str]:
    d = g.dir / "checks"
    return sorted((p.name for p in d.iterdir() if p.is_dir()), key=_ver_key) if d.is_dir() else []

def results(g: Generator, ver: str) -> list[dict]:
    """One entry per valid code in codes.txt: code, name, passed, total, fails, missing."""
    out = []
    for c in g.codes():
        if not c.valid:
            continue
        f = g.dir / "checks" / ver / (c.name + ".txt")
        if not f.exists():
            out.append(dict(code=c.code, name=c.name, opts=c.opts, passed=0, total=0, fails=0, missing=True)); continue
        txt = f.read_text().splitlines()
        m = re.match(r"(\d+)/(\d+) passed", txt[-1]) if txt else None
        fails = sum(1 for l in txt if l.startswith("FAIL"))
        out.append(dict(code=c.code, name=c.name, opts=c.opts, passed=int(m.group(1)) if m else 0, total=int(m.group(2)) if m else 0,
                        fails=fails, missing=m is None))
    return out

def badge(g: Generator):
    """(level or None, why not)."""
    vers = check_versions(g)
    if not vers:
        return None, "no checks/<solidcraft version>/ results"
    res = results(g, vers[-1])
    if not res:
        return None, "codes.txt lists no valid code"
    bad = [r["name"] for r in res if r["missing"] or r["fails"] or r["passed"] != r["total"]]
    if bad:
        return None, f"spec check not passing / missing on {vers[-1]} for: {', '.join(bad)}"
    level = "Checked"
    if review_problems(g) == []:
        level = "Reviewed"
        if (g.dir / "drawing-match.toml").exists():
            level = "Drawing-matched"
    return level, ""

def dimension_ids(g: Generator) -> set:
    return {d["id"] for d in sources(g).get("dimension", [])}

def review_problems(g: Generator):
    """None when there is no review.toml; [] when it raises the level to Reviewed; else why it does not (docs/review.md):
    every [[dimension]] of sources.toml has a [[row]] with verdict "agree" or "corrected", the review names a reviewer who is
    not the author, and sources_hash equals the current one (a data change after the review voids it)."""
    rv = g.dir / "review.toml"
    if not rv.exists():
        return None
    r = tomllib.loads(rv.read_text()); out = []
    if not r.get("reviewer"): out.append("no reviewer")
    if r.get("reviewer_kind") not in ("ai", "person"): out.append('reviewer_kind must be "ai" or "person"')
    if r.get("reviewer") and r.get("reviewer") == r.get("author"): out.append("the reviewer is the author")
    if r.get("sources_hash") != sources_hash(g): out.append("sources.toml or data/ changed after the review")
    rows = {x.get("id"): x for x in r.get("row", [])}
    missing = sorted(dimension_ids(g) - set(rows))
    if missing: out.append("dimension rows not reviewed: " + ", ".join(map(str, missing)))
    bad = sorted(i for i, x in rows.items() if x.get("verdict") not in ("agree", "corrected"))
    if bad: out.append("rows not signed off: " + ", ".join(map(str, bad)))
    return out

def verified_by(g: Generator) -> str:
    """One line for the generator page: who or what verified it. Never implies a person when the reviewer was an AI."""
    vers = check_versions(g)
    parts = [f"automatic spec check of every code in codes.txt on SolidCraft {vers[-1]}" if vers else "no automatic check yet"]
    if review_problems(g) == []:
        r = tomllib.loads((g.dir / "review.toml").read_text())
        if r["reviewer_kind"] == "ai":
            parts.append(f"independent AI re-read of every dimension row against the cited pages (cell by cell, {r.get('date', '?')}); not reviewed by a person")
        else:
            parts.append(f"independent review by {r['reviewer']} (every dimension row against the cited pages, {r.get('date', '?')})")
    if (g.dir / "drawing-match.toml").exists():
        parts.append("drawing match (drawing-match.toml)")
    return "; ".join(parts)

def _cell(s) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")

def render(g: Generator) -> str:
    m = g.manifest; src = sources(g)
    vers = check_versions(g); ver = vers[-1] if vers else None
    level, why = badge(g)
    res = results(g, ver) if ver else []
    L = []
    L.append(f"# Provenance: {g.id} {m['version']}\n")
    L.append("Generated by `tools/provenance` from `generator.toml`, `sources.toml`, `data/*.csv` and `checks/`. Never edit by hand: "
             "`tools/lint` fails when this file differs from what the tool writes.\n")
    L.append("Manufacturer names and ordering codes are used only to say what each part is. This part is not made, endorsed or checked by the "
             "manufacturer, and no manufacturer CAD file, logo or photo was used.\n")
    L.append(f"**Guarantee level: {level or 'NOT PUBLISHABLE (' + why + ')'}**  "
             f"(levels: Checked = automatic spec check; Reviewed = + independent reviewer; Drawing-matched = + drawing match)\n")
    L.append(f"**Verified by:** {verified_by(g)}.\n")
    L.append("## Based on\n")
    L.append("| Id | Document | URL | Pages used |\n|----|----------|-----|-----------|")
    for d in src.get("source", []):
        L.append(f"| {d['id']} | {_cell(d['catalogue'])} | {d['url']} | {_cell(d.get('pages', ''))} |")
    rows = src.get("dimension", [])
    cnt: dict = {}
    for r in rows:
        cnt[r["status"]] = cnt.get(r["status"], 0) + 1
    L.append(f"\n{len(rows)} cited rows ({', '.join(f'{v} {k}' for k, v in sorted(cnt.items()))}). \"labelled\" / \"published\" = a number printed in the "
             "catalogue; \"measured\" = read from the vertex coordinates of the published vector drawing; \"derived\" = computed from labelled "
             "numbers; \"approximate\" = an estimate, shown only as appearance or as an illustration choice.\n")
    L.append("| # | Item | Value | Source | Page / how | Status |\n|---|------|-------|--------|-----------|--------|")
    for r in rows:
        L.append(f"| {r['id']} | {_cell(r['item'])} | {_cell(r.get('value', ''))} | {_cell(';'.join(r['source']))} | {_cell(r.get('page', ''))} | {r['status']} |")
    L.append("\nData tables (every row cites a source id and page):\n")
    for p in sorted((g.dir / "data").glob("*.csv")):
        n = max(0, len(p.read_text().splitlines()) - 1)
        L.append(f"- `data/{p.name}`: {n} rows")
    L.append(f"\nSources hash: `{sources_hash(g)}` (sha256 over `sources.toml` and `data/*.csv`).\n")
    L.append("## Verified by\n")
    L.append("1. **Automatic spec check** (`tools/check`): every code in `codes.txt` is built with solidcraft-cli and every dimension is "
             "compared with the datasheet value within the stated tolerance.")
    if res:
        tot = sum(r["total"] for r in res); okn = sum(r["passed"] for r in res)
        L.append(f"   - SolidCraft {ver}: {okn} of {tot} dimension rows match, over {len(res)} codes.")
        L.append("   - CI run: none yet (placeholder `<link to the generator.yml run>`; filled by CI once the repository exists).\n")
        L.append("   | Code | Options | Result | File |\n   |------|---------|--------|------|")
        for r in res:
            L.append(f"   | `{r['code']}` | {', '.join(r['opts']) or '-'} | {r['passed']}/{r['total']} | `checks/{ver}/{r['name']}.txt` |")
    else:
        L.append("   - no results yet.")
    inv = [c for c in g.codes() if not c.valid]
    if inv:
        L.append(f"\n   Invalid codes that must be rejected with a message (`!` lines in codes.txt): {len(inv)}.")
    rv = g.dir / "review.toml"; rp = review_problems(g)
    if rp is None:
        L.append("\n2. **Independent review:** none yet.")
    else:
        r = tomllib.loads(rv.read_text())
        rows = r.get("row", [])
        L.append(f"\n2. **Independent review:** `review.toml`, by {r.get('reviewer', '?')} on {r.get('date', '?')} "
                 f"({sum(1 for x in rows if x.get('verdict') == 'agree')} rows agree, "
                 f"{sum(1 for x in rows if x.get('verdict') == 'corrected')} corrected). "
                 + ("Valid for the current sources." if not rp else "NOT counted: " + "; ".join(rp) + "."))
    dm = g.dir / "drawing-match.toml"
    L.append("3. **Drawing match** (only where the vendor allows it): " + ("recorded in `drawing-match.toml`." if dm.exists() else "none yet."))
    L.append("\n## Not guaranteed\n")
    L.append("Everything tagged \"appearance, approximate\" in the part, and every illustration choice. It is shown for looks only and is not "
             "checked against a catalogue dimension:\n")
    for item in m.get("guarantee", {}).get("not_guaranteed", []):
        L.append(f"- {item}")
    L.append("\n## Recipe stored on a placed part\n")
    L.append("```json\n" + json.dumps({"generator": g.id, "version": m["version"], "code": "<the ordering code>",
                                      "sources_hash": sources_hash(g)}, indent=2) + "\n```")
    L.append("\n(`schema/recipe.schema.json`). SolidCraft can show which generator and which datasheet edition made a part and warn when a newer "
             "verified version exists.\n")
    return "\n".join(L)
