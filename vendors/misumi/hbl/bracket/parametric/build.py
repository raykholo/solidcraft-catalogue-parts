#!/usr/bin/env python3
"""Build the parametric MISUMI bracket generator package (hbl-bracket/): the model hbl-bracket.sc, tables/*.csv and generator.toml.

The L bracket is drawn ONCE, driven by user parameters (arm lengths, plate thicknesses, hole diameter and positions, tab size). The 19
catalogue rows (data/types.csv, one per type) become configuration rows; the optional features (the two tabs of the HBK types, the second
foot hole, the second wall hole) are suppression columns of those rows AND drive_suppression rules on a unitless parameter. Run through
solidcraft-cli:

    SC_CLI=<solidcraft-cli> python3 build.py [--out DIR]
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from runtime.table import read_csv
import pkgfiles

PKG = "hbl-bracket"
DATA = HERE.parent / "data"
CLI = os.environ.get("SC_CLI", "solidcraft-cli")
BODY = "Bracket"

# user parameters: (name, default expression, unit, comment); the defaults are the HBLTSW5 row with the tabs on, so that
# every feature can be created, then suppressed where the row does not have it
PARAMS = [("width", "14", "mm", "plate width W (extrusion direction X)"), ("foot_len", "57", "mm", "foot arm length (Y), from the wall outer face"),
          ("wall_len", "57", "mm", "wall arm height (Z), from the foot outer face"), ("foot_t", "5", "mm", "foot thickness"),
          ("wall_t", "5", "mm", "wall thickness"), ("hole_d", "5.5", "mm", "hole diameter"),
          ("hole_off", "0", "mm", "hole centre line offset from the width centre (the eccentric types: hole_x - width / 2)"),
          ("tab_w", "6", "mm", "tab width on the centre line (HBK types)"), ("tab_h", "1", "mm", "tab height proud of the outer faces (HBK types)"),
          ("fh1", "30", "mm", "first foot hole, from the wall outer face"), ("fh2", "50", "mm", "second foot hole"),
          ("wh1", "30", "mm", "first wall hole, from the foot outer face"), ("wh2", "50", "mm", "second wall hole"),
          ("tabs", "0", "", "1 = the HBK types: tabs on the bottom of both arms"), ("foot_n", "1", "", "foot holes: 1 or 2"),
          ("wall_n", "1", "", "wall holes: 1 or 2")]
DERIVED = [("hole_x", "width / 2 + hole_off", "mm", "hole centres across the width")]
FEATS = ["FootTab", "WallTab", "FootHole2", "WallHole2"]        # the optional features: suppression columns and rules (the first holes are always there)

from runtime.parametric.process import run_build

def run(cmds, src=None, save=None, workdir=None):
    return run_build(cmds, src, save, workdir, detailed=False, executable=CLI)

def cell(v):
    return f"{v:g}" if isinstance(v, float) else str(v)

def row_values(r):
    pos = lambda s: [float(x) for x in s.split("|")] if s else []
    fh, wh = pos(r["foot_holes"]), pos(r["wall_holes"])
    v = {"width": r["width"], "foot_len": r["foot"], "wall_len": r["wall"], "foot_t": r["foot_t"], "wall_t": r["wall_t"], "hole_d": r["hole_d"],
         "hole_off": (float(r["hole_x"]) - float(r["width"]) / 2) if r["hole_x"] else 0,
         "tab_w": r["tab_w"] if float(r["tab_w"]) else 6, "tab_h": r["tab_h"] if float(r["tab_h"]) else 1,   # inert at the defaults when the tabs are off
         "fh1": fh[0], "fh2": fh[1] if len(fh) > 1 else 0, "wh1": wh[0], "wh2": wh[1] if len(wh) > 1 else 0,
         "tabs": 1 if float(r["tab_w"]) else 0, "foot_n": len(fh), "wall_n": len(wh)}
    return {f"param:{k}": cell(x) for k, x in v.items()}, {"FootTab": not v["tabs"], "WallTab": not v["tabs"], "FootHole2": len(fh) < 2, "WallHole2": len(wh) < 2}

def build(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    pkg = out / PKG; (pkg / "tables").mkdir(parents=True, exist_ok=True)
    wd = Path(tempfile.mkdtemp())
    rows = read_csv(DATA / "types.csv")
    cmds = []
    def add(c, **kw): cmds.append({"command": c, "params": kw})
    for n, e, u, c in PARAMS + DERIVED:
        add("parameters.add", name=n, expression=e, unit=u, comment=c)
    add("component.create", name="MISUMI bracket")
    # L section on YZ (sketch x = world Y along the foot, sketch y = world Z along the wall), extruded along X by the width
    add("sketch.create", plane="YZ", name="Profile")
    add("sketch.line", points=[[0, 0], ["foot_len", 0], ["foot_len", "foot_t"], ["wall_t", "foot_t"], ["wall_t", "wall_len"], [0, "wall_len"]], closed=True)
    add("sketch.finish")
    add("solid.extrude", distance="width", name="Extrusion", body_name=BODY)
    # tabs: tab_w wide on the centre line, tab_h proud of the outer face, over the whole arm (appearance, approximate, as in the Python part)
    add("solid.box", length="tab_w", width="foot_len", height="tab_h", corner=["width / 2 - tab_w / 2", 0, "-tab_h"], operation="join", targets=[BODY], name="FootTab")
    add("solid.box", length="tab_w", width="tab_h", height="wall_len", corner=["width / 2 - tab_w / 2", "-tab_h", 0], operation="join", targets=[BODY], name="WallTab")
    for i in (1, 2):
        add("solid.cylinder", diameter="hole_d", height="foot_t + tab_h + 2 mm", base=["hole_x", f"fh{i}", "-tab_h - 1 mm"], axis="Z", operation="cut",
            targets=[BODY], name=f"FootHole{i}")
    for i in (1, 2):
        add("solid.cylinder", diameter="hole_d", height="wall_t + tab_h + 2 mm", base=["hole_x", "-tab_h - 1 mm", f"wh{i}"], axis="Y", operation="cut",
            targets=[BODY], name=f"WallHole{i}")
    for f in FEATS:
        add("timeline.suppress", feature=f, suppressed=True)
    add("browser.visibility", items=["Profile"], visible=False)
    res = run(cmds, save=wd / "stage1.sc", workdir=wd)
    ids = {}
    for c, r in zip(cmds, res):
        nm = c["params"].get("name")
        if isinstance(r, dict) and r.get("feature") is not None and nm and c["command"].startswith("solid."): ids[nm] = r["feature"]
    missing = [f for f in FEATS if f not in ids]
    if missing: sys.exit(f"no feature id in the replies for {missing}")
    # ---- configuration table: one row per type, suppression columns, rules -------------------------------------------------
    cfg = [{"command": "config.configure", "params": {"params": [n for n, *_ in PARAMS], "features": FEATS}}]
    for r in rows:
        vals, sup = row_values(r)
        vals.update({f"suppress:{k}": v for k, v in sup.items()})
        cfg.append({"command": "config.row", "params": {"name": r["type"], "values": vals}})
    # the "Default" row that config.configure makes from the current values is the stage-1 working state, not a catalogue row: drop it
    cfg.append({"command": "config.activate", "params": {"row": rows[0]["type"]}})
    cfg.append({"command": "config.row", "params": {"name": "Default", "delete": True}})
    rules = []
    def rule(rid, name, cond, eff): rules.append({"id": rid, "name": name, "condition": cond, "effect": eff})
    pc = lambda n, op, e: {"type": "parameter", "parameter": n, "operator": op, "expression": str(e)}
    for n, cond in (("FootTab", pc("tabs", "eq", 1)), ("WallTab", pc("tabs", "eq", 1)), ("FootHole2", pc("foot_n", "ge", 2)), ("WallHole2", pc("wall_n", "ge", 2))):
        rule(f"{n}-on", f"{n} on", cond, {"type": "drive_suppression", "feature": ids[n], "value": False})
        rule(f"{n}-off", f"{n} off", {"type": "not", "condition": cond}, {"type": "drive_suppression", "feature": ids[n], "value": True})
    always = {"type": "always"}
    rule("tabs-range", "tabs 0 or 1", always, {"type": "parameter_range", "parameter": "tabs", "minimum": "0", "maximum": "1"})
    rule("foot-n-range", "foot holes 1 or 2 (S40 p.539 / p.540 drawings)", always, {"type": "parameter_range", "parameter": "foot_n", "minimum": "1", "maximum": "2"})
    rule("wall-n-range", "wall holes 1 or 2 (S40 p.539 / p.540 drawings)", always, {"type": "parameter_range", "parameter": "wall_n", "minimum": "1", "maximum": "2"})
    from runtime.parametric import limit_rules
    cfg.append({"command": "config.rule", "params": {"rules": limit_rules(rules)}})
    cfg.append({"command": "config.activate", "params": {"row": rows[0]["type"]}})
    run(cfg, src=wd / "stage1.sc", save=pkg / f"{PKG}.sc", workdir=wd)
    pkgfiles.write_tables(pkg, DATA); pkgfiles.write_toml(pkg, DATA)
    shutil.rmtree(wd, ignore_errors=True)
    return ids

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); a = ap.parse_args()
    ids = build(Path(a.out)); print(f"built {PKG}.sc with {len(ids)} named features")
