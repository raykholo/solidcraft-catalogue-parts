#!/usr/bin/env python3
"""Build the parametric MISUMI centre-hole-height-optional housing generator package (housing-g/): the model housing-g.sc, tables/*.csv and
generator.toml. The generator.rhai next to them is written by hand.

The housing is drawn ONCE, driven by user parameters (flange, body, chamfer, length, hole spacing, bore diameter and the centre height `hc`, the
free ordering option). The catalogue rows (data/housing-g.csv: one per dr, single and double each) become 10 configuration rows; `hc` is
a free parameter whose allowed values per dr are rules. Run through solidcraft-cli (SC_CLI), CI does it:

    python3 build.py [--package-only]        --package-only writes tables and generator.toml without SolidCraft
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime.table import read_csv
from runtime.parametric import kit as pk

PKG = HERE / "housing-g"
DATA = HERE.parent / "data"
MODEL = "housing-g.sc"
TEMPLATE = r"E\-LBHG[W:double]{dr}\-{h}"
FALLBACK = "{raw}"

def drows():
    return [r for r in read_csv(DATA / "housing-g.csv")]

def row_name(fam, r): return f"{fam}-{r['dr']}"

def write_package():
    rows = drows()
    pk.write_csv(PKG / "tables/housing-g.csv", ["key"] + list(rows[0].keys()), [[r["dr"]] + list(r.values()) for r in rows])
    pk.write_csv(PKG / "tables/params.csv", ["name", "value", "unit", "source", "page", "status"],
                 [["drs", "|".join(r["dr"] for r in rows), "", "S14", "p.491 table", "labelled"]])
    lines = ['format = "solidcraft-generator/2"', 'id = "housing-g"',
             'name = "MISUMI Economy linear bushing housing units, center hole height optional (E-LBHG, E-LBHGW)"', 'license = "CC0-1.0"',
             f'model = "{MODEL}"', "", "[parameters]", 'hc = { type = "int", min = 15, max = 50, unit = "mm" }', "",
             "# Ordering code: E-LBHG[W]<dr>-<H>. The second template takes any other text so that generator.rhai can refuse it with the shape message.",
             "[[template]]", f"pattern = '{TEMPLATE}'", "", "[[template]]", f"pattern = '{FALLBACK}'", ""]
    for r in rows:
        for fam in ("G", "GW"):
            lines += [f'[rows."{row_name(fam, r)}"]', f'source = "MISUMI Economy catalogue 2025 ({r["source"]}, sources.toml)"', f'page = "{r["page"]}"',
                      'status = "verified"', ""]
    from runtime.parametric.manifest import write_manifest
    write_manifest((PKG / "generator.toml"), "\n".join(lines), {'dr': {'type': 'text', 'min': 1, 'max': 2, 'escape': '[0-9]'}, 'h': {'type': 'text', 'min': 1, 'max': 2, 'escape': '[0-9]'}, 'raw': {'type': 'text', 'min': 1, 'max': 128, 'escape': '[ -~]'}})

# ---- the model --------------------------------------------------------------------------------------------------------
COLUMNS = ["dr", "hc", "hoff", "fw", "fs", "bw", "c1", "l1", "hd", "tl", "t1", "drk"]
UNITLESS = {"drk"}
PARAMS = {  # name: (comment)
    "dr": "shaft bore diameter dr", "hc": "centre height H above the base (the ordering option, +-0.05)", "hoff": "H1 - H, total height offset (0/-0.5)",
    "fw": "flange width L", "fs": "flange thickness S", "bw": "body width W", "c1": "upper corner chamfer C1 (appearance, approximate)",
    "l1": "mounting hole spacing L1 (across the flange)", "hd": "mounting hole diameter d", "tl": "length T (single or double)",
    "t1": "mounting hole spacing T1 (along the length)", "drk": "dr as a number (rule conditions)"}

def values(fam, r):
    dbl = fam == "GW"
    v = dict(dr=r["dr"], hc=r["H_choices"].split("|")[0], hoff=r["H1_offset"], fw=r["L"], fs=r["S"], bw=r["W"], c1=r["C1"], l1=r["L1"], hd=r["d"],
             tl=r["T_double" if dbl else "T_single"], t1=r["T1_double" if dbl else "T1_single"], drk=r["dr"])
    return {k: (x if k in UNITLESS else f"{x} mm") for k, x in v.items()}

def geometry():
    c = []
    def add(cmd, **p): c.append({"command": cmd, "params": p})
    first = values("G", drows()[0])
    for k in COLUMNS:
        add("parameters.add", name=k, expression=first[k].replace(" mm", ""), unit="" if k in UNITLESS else "mm", comment=PARAMS[k])
    add("parameters.add", name="h1", expression="hc + hoff", unit="mm", comment="total height H1 = H + offset")
    add("component.create", name="Housing G")
    add("sketch.create", plane={"origin": [0, "tl / 2", 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Profile")
    add("sketch.line", points=[["-fw / 2", 0], ["fw / 2", 0], ["fw / 2", "fs"], ["bw / 2", "fs"], ["bw / 2", "h1 - c1"], ["bw / 2 - c1", "h1"],
                               ["-bw / 2 + c1", "h1"], ["-bw / 2", "h1 - c1"], ["-bw / 2", "fs"], ["-fw / 2", "fs"]], closed=True)
    add("sketch.finish")
    add("solid.extrude", distance="tl", name="Body", body_name="Housing")
    add("solid.cylinder", diameter="dr", height="tl + 2", base=[0, "-tl / 2 - 1", "hc"], axis="Y", operation="cut", name="Shaft bore")
    i = 0
    for sx in (-1, 1):
        for sy in (-1, 1):
            i += 1
            add("solid.cylinder", diameter="hd", height="fs + 2", base=[("-" if sx < 0 else "") + "l1 / 2", ("-" if sy < 0 else "") + "t1 / 2", -1],
                axis="Z", operation="cut", name=f"Mounting hole {i}")
    add("browser.visibility", items=["Profile"], visible=False)
    return c

def rules(ids):
    pc = lambda n, op, e: {"type": "parameter", "parameter": n, "operator": op, "expression": str(e)}
    out = [{"id": "hc-range", "name": "Centre height 15 to 50 mm (S14 p.491)", "condition": {"type": "always"},
            "effect": {"type": "parameter_range", "parameter": "hc", "minimum": "15 mm", "maximum": "50 mm"}}]
    for r in drows():
        out.append({"id": f"hc-{r['dr']}", "name": f"Centre heights offered for dr {r['dr']} (S14 p.491 table)", "condition": pc("drk", "eq", r["dr"]),
                    "effect": {"type": "allow_parameter_values", "parameter": "hc", "expressions": [f"{h} mm" for h in r["H_choices"].split("|")]}})
    return out

def build():
    rows = []
    for r in drows():
        for fam in ("G", "GW"):
            v = {f"param:{k}": x for k, x in values(fam, r).items()}
            rows.append((row_name(fam, r), v))
    pk.build_model(PKG, MODEL, geometry(), COLUMNS, [], rows, rules, row_name("G", drows()[0]))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--package-only", action="store_true"); a = ap.parse_args()
    write_package()
    if not a.package_only:
        build(); print(f"built {MODEL}")
