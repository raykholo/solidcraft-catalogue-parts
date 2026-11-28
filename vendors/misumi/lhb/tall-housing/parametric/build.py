#!/usr/bin/env python3
"""Build the parametric MISUMI tall-block linear bushing housing package (tall-housing/): the model tall-housing.sc, tables/*.csv and
generator.toml. The generator.rhai next to them is written by hand.

The housing is drawn ONCE, driven by user parameters (block, bore, hole spacings, counterbore, dowel sizes). The catalogue rows (data/blocks.csv,
41 rows: single, double, medium, medium long and long per dr, with the dowel table data/dowel.csv joined by (series, dr)) are configuration rows; the
thread sizes of the M1 and M2 holes, the third M2 hole and counterbore of the long type are per-row suppression columns, the dowel option is a
free parameter with drive_suppression rules.

    python3 build.py [--package-only]        --package-only writes tables and generator.toml without SolidCraft (CI runs the whole build)
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime.table import read_csv
from runtime.parametric import kit as pk

PKG = HERE / "tall-housing"
DATA = HERE.parent / "data"
MODEL = "tall-housing.sc"
TEMPLATE = r"E\-LBHS[W:double]{dr}[{length: D|S|L}][\-P:dowel]"
FALLBACK = "{raw}"
THREADS = ["M4", "M5", "M6", "M8", "M10"]
SERIES = ["single", "double", "medium", "medlong", "long"]

def key(r): return f"{r['series']}-{r['dr']}"

def blocks(): return read_csv(DATA / "blocks.csv")
def dowels(): return {key(r): r for r in read_csv(DATA / "dowel.csv")}

def write_package():
    for name in ("blocks", "dowel"):
        rows = read_csv(DATA / f"{name}.csv")
        pk.write_csv(PKG / f"tables/{name}.csv", ["key"] + list(rows[0].keys()), [[key(r)] + list(r.values()) for r in rows])
    pk.write_csv(PKG / "tables/params.csv", ["name", "value", "unit", "source", "page", "status"],
                 [[f"drs_{s}", "|".join(r["dr"] for r in blocks() if r["series"] == s), "", "S14", "p.488 p.489 p.490 tables", "labelled"] for s in SERIES])
    lines = ['format = "solidcraft-generator/2"', 'id = "tall-housing"',
             'name = "MISUMI Economy linear bushing housing units, tall blocks with dowel holes (E-LBHS, E-LBHSW)"', 'license = "CC0-1.0"',
             f'model = "{MODEL}"', "", "[parameters]", 'dowel = { type = "int", min = 0, max = 1 }', "",
             "# Ordering code: E-LBHS[W]<dr>[D|S|L][-P]. The second template takes any other text so that generator.rhai can refuse it with the shape message.",
             "[[template]]", f"pattern = '{TEMPLATE}'", "", "[[template]]", f"pattern = '{FALLBACK}'", ""]
    for r in blocks():
        lines += [f'[rows."{key(r)}"]', f'source = "MISUMI Economy catalogue 2025 ({r["source"]}, sources.toml)"', f'page = "{r["page"]}"', 'status = "verified"', ""]
    from runtime.parametric.manifest import write_manifest
    write_manifest((PKG / "generator.toml"), "\n".join(lines), {'dr': {'type': 'text', 'min': 1, 'max': 2, 'escape': '[0-9]'}, 'raw': {'type': 'text', 'min': 1, 'max': 128, 'escape': '[ -~]'}})

# ---- the model --------------------------------------------------------------------------------------------------------
COLUMNS = ["dr", "bl", "l1", "l2", "hb", "bw", "bh", "tl", "m1d", "m2d", "cbd", "cbt", "dp", "dl", "dwx", "dwy", "dowel", "dowel_ok"]
UNITLESS = {"dowel", "dowel_ok"}
PARAMS = {"dr": "shaft bore diameter dr", "bl": "length L", "l1": "M1 hole spacing L1 (along the length)", "l2": "M2 hole spacing L2",
          "hb": "bore axis height h above the base", "bw": "width W", "bh": "height H", "tl": "M2 holes l below the top face",
          "m1d": "M1 effective thread length", "m2d": "M2 effective thread length", "cbd": "counterbore diameter d1", "cbt": "counterbore depth t",
          "dp": "dowel hole diameter P", "dl": "dowel hole depth l2", "dwx": "dowel hole offset across F / 2 (appearance, approximate)",
          "dwy": "dowel hole offset along E / 2 (appearance, approximate)", "dowel": "1 = the two dowel holes (-P)",
          "dowel_ok": "1 = the catalogue lists dowel holes for this series and dr"}

def values(r, dw):
    single = r["series"] == "single"
    v = dict(dr=r["dr"], bl=r["L"], l1=r["L1"], l2=r["L2"], hb=r["h"], bw=r["W"], bh=r["H"], tl=r["l"], m1d=r["M1_eff"], m2d=r["M2_eff"], cbd=r["d1"], cbt=r["t"],
             dp=dw["P"] if dw else "3", dl=dw["l2"] if dw else "4",
             dwx=repr(float(dw["F"]) / 2) if dw and single else "0", dwy=repr(float(dw["E"]) / 2) if dw else "0", dowel="0", dowel_ok="1" if dw else "0")
    return {k: (x if k in UNITLESS else f"{x} mm") for k, x in v.items()}

def geometry():
    rows, dws = blocks(), dowels()
    vals = [(r, values(r, dws.get(key(r)))) for r in rows]
    first = vals[0][1]
    c = []
    def add(cmd, **p): c.append({"command": cmd, "params": p})
    for k in COLUMNS:
        add("parameters.add", name=k, expression=first[k].replace(" mm", ""), unit="" if k in UNITLESS else "mm", comment=PARAMS[k])
    add("parameters.add", name="m1_xf", expression="0.35", unit="", comment="x of the vertical M1 holes as a fraction of W (appearance, approximate)")
    add("component.create", name="Tall housing")
    add("sketch.create", plane={"origin": [0, "bl / 2", 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Profile")
    add("sketch.line", points=[["-bw / 2", 0], ["bw / 2", 0], ["bw / 2", "bh"], ["-bw / 2", "bh"]], closed=True)
    add("sketch.finish")
    add("solid.extrude", distance="bl", name="Body", body_name="Housing")
    add("solid.cylinder", diameter="dr", height="bl + 2", base=[0, "-bl / 2 - 1", "hb"], axis="Y", operation="cut", name="Shaft bore")
    add("sketch.create", plane={"origin": [0, 0, "bh"], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="M1 sketch")
    add("sketch.point", point=["m1_xf * bw", "-l1 / 2"]); add("sketch.point", point=["-m1_xf * bw", "l1 / 2"])
    add("sketch.finish")
    add("sketch.create", plane={"origin": ["bw / 2", 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}, name="M2 sketch")
    add("sketch.point", point=["-l2 / 2", "bh - tl"]); add("sketch.point", point=["l2 / 2", "bh - tl"])
    add("sketch.finish")
    add("sketch.create", plane={"origin": ["bw / 2", 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}, name="M2 sketch mid")
    add("sketch.point", point=[0, "bh - tl"])
    add("sketch.finish")
    def live(col, m):          # a row with this thread size: the parameters it sets, so the feature is created on a body that fits it
        return next(v for r, v in vals if r[col] == m)
    for m in THREADS:          # the thread designation cannot come from a parameter: one feature per size, suppressed per row
        add("parameters.change", changes=live("M1", m))
        add("solid.hole", sketch="M1 sketch", thread=m, depth="m1d", name=f"Thread M1 {m}")
        add("timeline.suppress", feature=f"Thread M1 {m}", suppressed=True)
    for m in THREADS:
        add("parameters.change", changes=live("M2", m))
        for nm, sk in ((f"Thread M2 {m}", "M2 sketch"), (f"Thread M2 mid {m}", "M2 sketch mid")):
            add("solid.hole", sketch=sk, thread=m, depth="m2d", name=nm)
            add("timeline.suppress", feature=nm, suppressed=True)
    add("parameters.change", changes=first)
    for i, y in enumerate(("-l2 / 2", "l2 / 2", 0)):     # counterbores d1 x t from the -X face, coaxial with M2
        add("solid.cylinder", diameter="cbd", height="cbt + 1", base=["-bw / 2 - 1", y, "bh - tl"], axis="X", operation="cut", name=f"Counterbore {i + 1}")
        if i == 2:
            add("timeline.suppress", feature="Counterbore 3", suppressed=True)
    for i, s in enumerate(("-", "")):
        add("solid.cylinder", diameter="dp", height="dl + 1", base=[f"{s}dwx", f"{s}dwy", "bh - dl"], axis="Z", operation="cut", name=f"Dowel hole {i + 1}")
        add("timeline.suppress", feature=f"Dowel hole {i + 1}", suppressed=True)
    add("browser.visibility", items=["Profile", "M1 sketch", "M2 sketch", "M2 sketch mid"], visible=False)
    return c

FEATURES = ([f"Thread M1 {m}" for m in THREADS] + [f"Thread M2 {m}" for m in THREADS] + [f"Thread M2 mid {m}" for m in THREADS]
            + ["Counterbore 3", "Dowel hole 1", "Dowel hole 2"])

def rows_of():
    dws = dowels(); out = []
    for r in blocks():
        v = {f"param:{k}": x for k, x in values(r, dws.get(key(r))).items()}
        for m in THREADS:
            v[f"suppress:Thread M1 {m}"] = r["M1"] != m
            v[f"suppress:Thread M2 {m}"] = r["M2"] != m
            v[f"suppress:Thread M2 mid {m}"] = not (r["M2"] == m and r["series"] == "long")
        v["suppress:Counterbore 3"] = r["series"] != "long"
        v["suppress:Dowel hole 1"] = v["suppress:Dowel hole 2"] = True
        out.append((key(r), v))
    return out

def rules(ids):
    pc = lambda n, op, e: {"type": "parameter", "parameter": n, "operator": op, "expression": str(e)}
    out = [{"id": "dowel-range", "name": "Dowel holes: 0 or 1 (-P)", "condition": {"type": "always"},
            "effect": {"type": "parameter_range", "parameter": "dowel", "minimum": "0", "maximum": "1"}},
           {"id": "dowel-listed", "name": "No dowel hole version for this series and dr (S14 p.488 to p.490 dowel tables)", "condition": pc("dowel_ok", "eq", 0),
            "effect": {"type": "allow_parameter_values", "parameter": "dowel", "expressions": ["0"]}}]
    for i in (1, 2):
        fid = ids[f"Dowel hole {i}"]
        out.append({"id": f"dowel-{i}-on", "name": f"Dowel hole {i} when dowel = 1", "condition": pc("dowel", "eq", 1),
                    "effect": {"type": "drive_suppression", "feature": fid, "value": False}})
        out.append({"id": f"dowel-{i}-off", "name": f"No dowel hole {i} when dowel = 0", "condition": pc("dowel", "eq", 0),
                    "effect": {"type": "drive_suppression", "feature": fid, "value": True}})
    return out

def build():
    rows = rows_of()
    pk.build_model(PKG, MODEL, geometry(), COLUMNS, FEATURES, rows, rules, rows[0][0])

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--package-only", action="store_true"); a = ap.parse_args()
    write_package()
    if not a.package_only:
        build(); print(f"built {MODEL}")
