"""Export of a generator folder to a SolidCraft generator package (runtime/package.py, docs/generator-package.md).

Each generator has a hand-written description here (one module per generator id, `describe(gen) -> dict`): the grammar, the lookups,
variables, rules and command template in the package format, and the catalogue tables (copied from data/*.csv, with derived columns
where the format has no loops: polygons, point lists). `export(gen)` adds what is common: id, guarantee level, sources, provenance
text, RFC 0019 declarations, checks.
"""
from __future__ import annotations
import csv, importlib, io, json, tomllib
from pathlib import Path
from runtime import provenance, registry

def csv_text(header: list, rows: list) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    for r in rows:
        w.writerow([_c(v) for v in r])
    return buf.getvalue()

def _c(v):
    if isinstance(v, float):
        return str(int(v)) if v == int(v) and abs(v) < 1e15 else repr(v)
    return v

def pts(points) -> str:
    """A `points` cell: "x y;x y"."""
    return ";".join(f"{_c(float(x))} {_c(float(y))}" for x, y in points)

def table(columns: dict, key: list, header: list, rows: list) -> dict:
    return {"columns": columns, "key": key, "csv": csv_text(header, rows)}

def package_id(gen) -> str:
    return gen.id.replace(".", "-")

def measured(gen) -> dict:
    """checks/<latest solidcraft version>/package-measured.json: volume, bounding box and face count per code, written by
    `tools/package-equiv --build --record` on a real SolidCraft."""
    for v in reversed(provenance.check_versions(gen)):
        f = gen.dir / "checks" / v / "package-measured.json"
        if f.is_file():
            return json.loads(f.read_text())
    return {}

def export(gen) -> dict:
    mod = importlib.import_module("runtime.package_export." + gen.id.replace(".", "_").replace("-", "_"))
    body = mod.describe(gen)
    m = gen.manifest
    lib = tomllib.loads((registry.ROOT / "library.toml").read_text())
    src = provenance.sources(gen)
    level, why = provenance.badge(gen)
    if level is None:
        raise SystemExit(f"{gen.id}: below Checked, not exportable: {why}")
    d = m.get("declares", {})
    matches = []
    for pm in d.get("matches", []):
        x = {k: v for k, v in pm.items() if k != "negative_examples"}
        x["negative"] = pm.get("negative_examples", [])
        matches.append(x)
    ng = m.get("guarantee", {}).get("not_guaranteed", [])
    prov = (f"Generated from the catalogue generator {gen.id} {m['version']} of {lib['repo']}; every number is a row of a table below with its source, "
            f"page and status. Verified by: {provenance.verified_by(gen)}. Not guaranteed (appearance, approximate): "
            + "; ".join(x[:150] for x in ng))
    prov = prov[:1990] + ("..." if len(prov) > 1990 else "")
    pkg = {
        "format": "solidcraft-generator/1",
        "min_solidcraft": m["min_host_version"],
        "id": package_id(gen),
        "name": m["name"],
        "description": f"{m['name']}. Part of the catalogue-parts library; not made, endorsed or checked by the manufacturer, no manufacturer CAD, logo or photo used.",
        "license": lib["license"],
        "author": lib["publisher"],
        "guarantee": level.lower(),
        "provenance": prov,
        "sources": [{"id": s["id"], "title": s["catalogue"], "url": s["url"], "pages": s.get("pages", "")} for s in src.get("source", [])],
        "declares": {"labels": d.get("labels", []), "keywords": d.get("keywords", []), "vendor": d.get("vendor", ""), "matches": matches},
    }
    pkg.update(body["package"])
    # checks: every valid code of codes.txt (dimensions = the package's own variables, exact; volume / bbox / faces when recorded on a
    # real SolidCraft), then every code that must be refused (with the package's own refusal text)
    from runtime.package import Package, Refusal
    probe = Package(pkg)
    meas = measured(gen)
    checks, bad = [], []
    for c in gen.codes():
        try:
            env, _ = probe.run(c.code)
        except Refusal as r:
            if c.valid:
                raise SystemExit(f"{gen.id}: the package refuses the valid code {c.code}: {r}")
            bad.append({"code": c.code, "invalid": True, "message_contains": str(r)})
            continue
        if not c.valid:
            raise SystemExit(f"{gen.id}: the package accepts {c.code}, which codes.txt says must be rejected")
        ck = {"code": c.code, "dimensions": {k: env[k] for k in body["dimension_vars"]}}
        ck.update(meas.get(c.code, {}))
        checks.append(ck)
    pkg["checks"] = checks + bad
    pkg["x-generator"] = {"id": gen.id, "version": m["version"], "sources_hash": provenance.sources_hash(gen), "level": level,
                          "checked_on": (provenance.check_versions(gen) or [""])[-1]}
    rv = gen.dir / "review.toml"
    if provenance.review_problems(gen) == []:
        r = tomllib.loads(rv.read_text())
        pkg["x-generator"]["review"] = {k: r[k] for k in ("reviewer_kind", "reviewer", "author", "date", "sources_hash") if k in r}
    return pkg
