#!/usr/bin/env python3
"""Build the parametric MISUMI wide-block linear bushing housing package (bushing-housing/): the model bushing-housing.sc, tables/*.csv and
generator.toml. The generator.rhai next to them is written by hand.

The housing is drawn ONCE, driven by user parameters (profile, length, hole spacing, pilot and dowel sizes). The catalogue rows (data/single.csv,
data/double.csv: single / medium and double / medium long / long per dr, 40 rows) are configuration rows; the thread size, the third mounting row
of the long type and the dowel hole sites are per-row suppression columns, the dowel option is a free parameter with drive_suppression rules.

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

PKG = HERE / "bushing-housing"
DATA = HERE.parent / "data"
MODEL = "bushing-housing.sc"
TEMPLATE = r"E\-LBHN[W:double]{dr}[{length: D|L}][\-P:dowel]"
FALLBACK = "{raw}"
THREADS = ["M4", "M5", "M6", "M8", "M10"]

# series -> (table, length column, L1 column, tolerance (upper, lower) columns; a number is a fixed 0)
SERIES = {"single": ("single", "L_single", "L1_single", ("dr_tol_single_upper", "dr_tol_single_lower")),
          "medium": ("single", "L_medium", "L1_medium", ("dr_tol_medium_upper", "dr_tol_medium_lower")),
          "double": ("double", "L_double", "L1_double", (None, "dr_tol_double")),
          "medlong": ("double", "L_medlong", "L1_medlong", (None, "dr_tol_medlong")),
          "long": ("double", "L_long", "L1_long", (None, "dr_tol_long"))}

def catalogue():
    """[(configuration row name, series, data row)] in catalogue order."""
    tabs = {"single": read_csv(DATA / "single.csv"), "double": read_csv(DATA / "double.csv")}
    out = []
    for series, (tab, lcol, *_rest) in SERIES.items():
        for r in tabs[tab]:
            if r[lcol] != "":
                out.append((f"{series}-{r['dr']}", series, r))
    return out

def write_package():
    for name in ("single", "double"):
        rows = read_csv(DATA / f"{name}.csv")
        pk.write_csv(PKG / f"tables/{name}.csv", ["key"] + list(rows[0].keys()), [[r["dr"]] + list(r.values()) for r in rows])
    cat = catalogue()
    lists = {s: "|".join(r["dr"] for n, ss, r in cat if ss == s) for s in SERIES}
    pk.write_csv(PKG / "tables/params.csv", ["name", "value", "unit", "source", "page", "status"],
                 [[f"drs_{s}", v, "", "S12", "p.485 p.486 p.487 tables", "labelled"] for s, v in lists.items()])
    lines = ['format = "solidcraft-generator/2"', 'id = "bushing-housing"',
             'name = "MISUMI Economy linear bushing housing units, wide blocks (E-LBHN, E-LBHNW), with or without dowel holes"', 'license = "CC0-1.0"',
             f'model = "{MODEL}"', "", "[parameters]", 'dowel = { type = "int", min = 0, max = 1 }', "",
             "# Ordering code: E-LBHN[W]<dr>[D|L][-P]. The second template takes any other text so that generator.rhai can refuse it with the shape message.",
             "[[template]]", f"pattern = '{TEMPLATE}'", "", "[[template]]", f"pattern = '{FALLBACK}'", ""]
    for name, series, r in cat:
        lines += [f'[rows."{name}"]', f'source = "MISUMI Economy catalogue 2025 ({r["source"]}, sources.toml)"', f'page = "{r["page"]}"', 'status = "verified"', ""]
    from runtime.parametric.manifest import write_manifest
    write_manifest((PKG / "generator.toml"), "\n".join(lines), {'dr': {'type': 'text', 'min': 1, 'max': 2, 'escape': '[0-9]'}, 'raw': {'type': 'text', 'min': 1, 'max': 128, 'escape': '[ -~]'}})

# ---- the model --------------------------------------------------------------------------------------------------------
COLUMNS = ["dr", "bl", "l1", "bw", "bh", "hb", "h1", "h2", "w1", "td", "pd", "dp", "dl", "dwx", "dwy", "dowel", "dowel_ok"]
UNITLESS = {"dowel", "dowel_ok"}
PARAMS = {"dr": "shaft bore diameter dr", "bl": "length L", "l1": "mounting hole spacing along the length L1", "bw": "width W", "bh": "height H",
          "hb": "bore axis h below the top face", "h1": "H1, from the top face down to the foot", "h2": "H2, height of the top shoulders",
          "w1": "mounting hole spacing across W1", "td": "thread depth l", "pd": "pilot hole diameter d (through the full height)",
          "dp": "dowel hole diameter P", "dl": "dowel hole depth l2", "dwx": "dowel hole offset across (appearance, approximate)",
          "dwy": "dowel hole offset along (appearance, approximate)", "dowel": "1 = the two dowel holes (-P)",
          "dowel_ok": "1 = the catalogue lists dowel holes for this dr"}

def values(series, r):
    tab, lcol, l1col, _t = SERIES[series]
    mid = series in ("medlong", "long")
    has_p = r["P"] != ""
    v = dict(dr=r["dr"], bl=r[lcol], l1=r[l1col], bw=r["W"], bh=r["H"], hb=r["h"], h1=r["H1"], h2=r["H2"], w1=r["W1"], td=r["l"], pd=r["d"],
             dp=r["P"] if has_p else "3", dl=r["l2"] if has_p else "4",
             dwx="0" if mid else repr(float(r["W1"]) / 2), dwy=repr(float(r[l1col]) / 2) if mid else "0", dowel="0", dowel_ok="1" if has_p else "0")
    return {k: (x if k in UNITLESS else f"{x} mm") for k, x in v.items()}

def geometry(cat):
    c = []
    def add(cmd, **p): c.append({"command": cmd, "params": p})
    first = values(cat[0][1], cat[0][2])
    for k in COLUMNS:
        add("parameters.add", name=k, expression=first[k].replace(" mm", ""), unit="" if k in UNITLESS else "mm", comment=PARAMS[k])
    add("parameters.add", name="wall_step", expression="1", unit="mm", comment="step of the lower body wall behind the top shoulders (appearance, approximate)")
    add("parameters.add", name="foot_frac", expression="0.16", unit="", comment="half foot width as a fraction of W (appearance, approximate)")
    add("component.create", name="Bushing housing")
    add("sketch.create", plane={"origin": [0, "bl / 2", 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Profile")
    add("sketch.line", points=[["-foot_frac * bw", 0], ["foot_frac * bw", 0], ["bw / 2 - wall_step", "bh - h1"], ["bw / 2 - wall_step", "bh - h2"],
                               ["bw / 2", "bh - h2"], ["bw / 2", "bh"], ["-bw / 2", "bh"], ["-bw / 2", "bh - h2"], ["-bw / 2 + wall_step", "bh - h2"],
                               ["-bw / 2 + wall_step", "bh - h1"]], closed=True)
    add("sketch.finish")
    add("solid.extrude", distance="bl", name="Body", body_name="Housing")
    add("solid.cylinder", diameter="dr", height="bl + 2", base=[0, "-bl / 2 - 1", "bh - hb"], axis="Y", operation="cut", name="Shaft bore")
    ends = [("-w1 / 2", "-l1 / 2"), ("-w1 / 2", "l1 / 2"), ("w1 / 2", "-l1 / 2"), ("w1 / 2", "l1 / 2")]
    mids = [("-w1 / 2", 0), ("w1 / 2", 0)]
    for nm, pts in (("Thread sketch", ends), ("Thread sketch mid", mids)):
        add("sketch.create", plane={"origin": [0, 0, "bh"], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name=nm)
        for x, y in pts:
            add("sketch.point", point=[x, y])
        add("sketch.finish")
    for m in THREADS:     # the thread designation cannot come from a parameter: one feature per size, created while a row of that size is live
        r0 = next(v for n, s, r in cat for v in [values(s, r)] if r["M"] == m)
        add("parameters.change", changes={k: x for k, x in r0.items()})
        for nm, sk in ((f"Mounting thread {m}", "Thread sketch"), (f"Mounting thread mid {m}", "Thread sketch mid")):
            add("solid.hole", sketch=sk, thread=m, depth="td", name=nm)
            add("timeline.suppress", feature=nm, suppressed=True)
    add("parameters.change", changes={k: x for k, x in first.items()})
    for i, (x, y) in enumerate(ends + mids):      # the pilot diameter d continues from the thread depth l down through the base
        add("solid.cylinder", diameter="pd", height="bh - td + 1", base=[x, y, -1], axis="Z", operation="cut", name=f"Pilot hole {i + 1}")
        if i >= 4:
            add("timeline.suppress", feature=f"Pilot hole {i + 1}", suppressed=True)
    for i, s in enumerate(("-", "")):
        add("solid.cylinder", diameter="dp", height="dl + 1", base=[f"{s}dwx", f"{s}dwy", "bh - dl"], axis="Z", operation="cut", name=f"Dowel hole {i + 1}")
        add("timeline.suppress", feature=f"Dowel hole {i + 1}", suppressed=True)
    add("browser.visibility", items=["Profile", "Thread sketch", "Thread sketch mid"], visible=False)
    return c

FEATURES = [f"Mounting thread {m}" for m in THREADS] + [f"Mounting thread mid {m}" for m in THREADS] + ["Pilot hole 5", "Pilot hole 6", "Dowel hole 1", "Dowel hole 2"]

def rows_of(cat):
    rows = []
    for name, series, r in cat:
        v = {f"param:{k}": x for k, x in values(series, r).items()}
        for m in THREADS:
            v[f"suppress:Mounting thread {m}"] = r["M"] != m
            v[f"suppress:Mounting thread mid {m}"] = not (r["M"] == m and series == "long")
        v["suppress:Pilot hole 5"] = v["suppress:Pilot hole 6"] = series != "long"
        v["suppress:Dowel hole 1"] = v["suppress:Dowel hole 2"] = True
        rows.append((name, v))
    return rows

def rules(ids):
    pc = lambda n, op, e: {"type": "parameter", "parameter": n, "operator": op, "expression": str(e)}
    out = [{"id": "dowel-range", "name": "Dowel holes: 0 or 1 (-P)", "condition": {"type": "always"},
            "effect": {"type": "parameter_range", "parameter": "dowel", "minimum": "0", "maximum": "1"}},
           {"id": "dowel-listed", "name": "No dowel hole version for this dr (S12 p.485 / p.487: the dowel hole table starts at dr 8)", "condition": pc("dowel_ok", "eq", 0),
            "effect": {"type": "allow_parameter_values", "parameter": "dowel", "expressions": ["0"]}}]
    for i in (1, 2):
        fid = ids[f"Dowel hole {i}"]
        out.append({"id": f"dowel-{i}-on", "name": f"Dowel hole {i} when dowel = 1", "condition": pc("dowel", "eq", 1),
                    "effect": {"type": "drive_suppression", "feature": fid, "value": False}})
        out.append({"id": f"dowel-{i}-off", "name": f"No dowel hole {i} when dowel = 0", "condition": pc("dowel", "eq", 0),
                    "effect": {"type": "drive_suppression", "feature": fid, "value": True}})
    return out

def build():
    cat = catalogue()
    pk.build_model(PKG, MODEL, geometry(cat), COLUMNS, FEATURES, rows_of(cat), rules, cat[0][0])

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--package-only", action="store_true"); a = ap.parse_args()
    write_package()
    if not a.package_only:
        build(); print(f"built {MODEL}")
