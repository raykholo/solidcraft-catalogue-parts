#!/usr/bin/env python3
"""Build the parametric MISUMI shaft generator package (sfj-shaft/): the model sfj-shaft.sc, tables/*.csv and generator.toml.

The shaft is modelled ONCE: a cylinder D x L along X, an optional left and right step (cylinders of diameter P), tapped ends and flats, each
optional feature a feature of the model that a rule suppresses unless its option parameter is present ("absent" is a parameter value: a
length of 0 for the steps, a thread of 0 for the taps, -1 mm for a flat position). The configuration rows are the diameters of
data/diameters.csv (D, flat depth H, wrench flat W and l1). Run through solidcraft-cli:

    SC_CLI=<solidcraft-cli> python3 build.py [--out DIR]
"""
from __future__ import annotations
import argparse, csv, importlib, shutil, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime.table import read_csv
from runtime.pharness import cli

sh = importlib.import_module("vendors.misumi.sfj.shaft.src.shaft")
PKG = "sfj-shaft"
DATA = HERE.parent / "data"
Dlist = sorted(sh.D_TABLE)

def g(v): return f"{v:g}"

def run(cmds, src=None, save=None):
    res, err = cli(cmds, src=src, save=save)
    if err: sys.exit(f"solidcraft-cli failed: {err}")
    return res

# ---- the tapped-end sizes each host face can carry (every size of every table that tapes that end) -------------------------
NO_PITCH = {2.6}              # M2.6 has no coarse ISO pitch: solid.hole refuses it ("give one, e.g. M2.6x0.25"), for the Python generator too
def sizes(*tables):
    out = set()
    for t in tables:
        for _, ms in t.values(): out |= set(ms)
    return sorted(out - NO_PITCH)
def step_sizes(*tables):
    out = set()
    for t in tables:
        for row in t.values(): out |= set(row["M"])
    return sorted(out)
L_SHAFT = sizes(*sh.FAM_TAP.values())
R_SHAFT = sizes(sh.FAM_TAP["Z"], sh.FAM_TAP["W"])
L_STEP = step_sizes(*sh.FAM_STEP.values())
R_STEP = step_sizes(sh.FAM_STEP["PH"])

# parameters: (name, creation value, unit, comment)
PARAMS = [("D", "50", "mm", "shaft diameter (row of data/diameters.csv)"), ("W", "41", "mm", "wrench flat width across flats (data/wrench.csv; D 6 and over)"),
          ("l1", "20", "mm", "wrench flat length (data/wrench.csv)"), ("H", "3", "mm", "flat surface depth FC / WFC (params.csv flat_depth_*)"),
          ("L", "100", "mm", "length L (main body for the stepped types)"), ("lkc", "0", "", "1 = LKC (0.1 mm length steps; tolerance text only)"),
          ("part_type", "E-PSFJ", "text", "catalogue type (E-PSFJ, E-SSFPG ...): material, tolerance class and finish only, no geometry"),
          ("F", "4", "mm", "left step length F (0 = no step)"), ("P", "40", "mm", "step diameter P"), ("T", "4", "mm", "right step length T (0 = no step)"),
          ("m_left", "3", "mm", "left tapped end: nominal thread M (0 = none)"), ("m_right", "3", "mm", "right tapped end: nominal thread N (0 = none)"),
          ("md", "0", "", "1 = MD: effective tap length M x 3 on the left end"),
          ("sc", "10", "mm", "SC: wrench flat position (-1 = none)"), ("sx", "10", "mm", "SX: distance to the second wrench flat set (-1 = none)"),
          ("wsc", "10", "mm", "WSC: position of the first of two wrench flats (-1 = none)"), ("xw", "10", "mm", "X: distance between the two WSC flats"),
          ("fc", "10", "mm", "FC: length of the flat surface (-1 = none)"), ("fa", "10", "mm", "FC from the left end: A (-1 = from the right)"),
          ("fe", "10", "mm", "FC from the right end: E (-1 = from the left)"),
          ("wfc", "10", "mm", "WFC: length of the two flat surfaces (-1 = none)"), ("wa", "10", "mm", "WFC: A from the left end"), ("we", "10", "mm", "WFC: E from the right end"),
          ("lfc", "2", "mm", "LFC: length of the set screw flat on the left step (-1 = none)"), ("la", "0", "mm", "LFC: A from the step end"),
          ("lfd", "1", "mm", "LFC flat depth (p.437: 1 for P up to 16, else 2)")]
COLUMNS = [n for n, *_ in PARAMS]
DEFAULT = {n: ("0" if n in ("F", "T", "m_left", "m_right", "md", "lkc") else "-1" if n in ("sc", "sx", "wsc", "fc", "fa", "fe", "wfc", "wa", "we", "lfc", "la") else v)
           for n, v, *_ in PARAMS}
DEFAULT["part_type"] = "E-PSFJ"; DEFAULT["xw"] = "0"; DEFAULT["lfd"] = "1"

def build(out: Path):
    pkg = out / PKG; (pkg / "tables").mkdir(parents=True, exist_ok=True)
    wd = Path(tempfile.mkdtemp())
    cmds = []
    def add(c, **kw): cmds.append({"command": c, "params": kw})
    for n, e, u, c in PARAMS: add("parameters.add", name=n, expression=e, unit=u, comment=c)
    add("parameters.add", name="tl_depth", expression="m_left * (2 + md)", unit="mm", comment="left tap depth: M x 2 (MD: M x 3)")
    add("parameters.add", name="tr_depth", expression="m_right * 2", unit="mm", comment="right tap depth: N x 2")
    add("component.create", name="MISUMI shaft")
    add("solid.cylinder", diameter="D", height="L", base=[0, 0, 0], axis="X", operation="new", body_name="Shaft", name="Shaft")
    add("solid.cylinder", diameter="P", height="F", base=["-F", 0, 0], axis="X", operation="join", targets=["Shaft"], name="Left step")
    add("solid.cylinder", diameter="P", height="T", base=["L", 0, 0], axis="X", operation="join", targets=["Shaft"], name="Right step")
    holes = []                                  # (feature name, group, size)
    def steps(left, right):
        add("timeline.suppress", feature="Left step", suppressed=not left); add("timeline.suppress", feature="Right step", suppressed=not right)
    def group(tag, pos, depth, sz, left, right):
        steps(left, right)
        for m in sz:
            nm = f"Tap {tag} M{g(m)}"
            add("solid.hole", position=pos, thread=f"M{g(m)}", depth=depth, targets=["Shaft"], name=nm)
            add("timeline.suppress", feature=nm, suppressed=True)
            holes.append((nm, tag, m))
    group("L shaft", [0, 0, 0], "tl_depth", L_SHAFT, False, False)
    group("R shaft", ["L", 0, 0], "tr_depth", R_SHAFT, False, False)
    group("L step", ["-F", 0, 0], "tl_depth", L_STEP, True, False)
    group("R step", ["L + T", 0, 0], "tr_depth", R_STEP, False, True)
    steps(True, True)
    for h, *_ in holes: pass
    # flats: Python's solid.box cuts, with the options' parameters as expressions
    boxes = []                                  # (name, condition parameter)
    big = "(D + 2 mm)"
    def ybox(nm, x0, length, lo, w, cond, bigv=big):   # slab on the +/-Y side: corner y = lo, thickness w across Y, full height
        add("solid.box", length=length, width=w, height=bigv, corner=[x0, lo, f"-{bigv} / 2"], operation="cut", targets=["Shaft"], name=nm); boxes.append((nm, cond))
    def zbox(nm, x0, length, lo, w, cond, bigv=big):
        add("solid.box", length=length, width=bigv, height=w, corner=[x0, f"-{bigv} / 2", lo], operation="cut", targets=["Shaft"], name=nm); boxes.append((nm, cond))
    wsc_w = "(D / 2 + 1 mm - W / 2)"; fc_w = "(H + 1 mm)"; neg = "(-D / 2 - 1 mm)"; half = "(D / 2 - H)"
    ybox("SC a", "sc", "l1", "W / 2", wsc_w, "sc"); ybox("SC b", "sc", "l1", neg, wsc_w, "sc")
    zbox("SX a", "sc + l1 + sx", "l1", "W / 2", wsc_w, "sx"); zbox("SX b", "sc + l1 + sx", "l1", neg, wsc_w, "sx")
    ybox("WSC Y a", "wsc", "l1", "W / 2", wsc_w, "wsc"); ybox("WSC Y b", "wsc", "l1", neg, wsc_w, "wsc")
    zbox("WSC Z a", "wsc + l1 + xw", "l1", "W / 2", wsc_w, "wsc"); zbox("WSC Z b", "wsc + l1 + xw", "l1", neg, wsc_w, "wsc")
    ybox("FC from left", "fa", "fc", half, fc_w, "fa"); ybox("FC from right", "L - fe - fc", "fc", half, fc_w, "fe")
    ybox("WFC Y", "wa", "wfc", half, fc_w, "wfc"); zbox("WFC Z", "L - we - wfc", "wfc", half, fc_w, "wfc")
    lbig = "(P + 2 mm)"
    ybox("LFC", "-F + la", "lfc", "P / 2 - lfd", "(lfd + 1 mm)", "lfc", lbig)
    add("browser.visibility", items=[], visible=True) if False else None
    res = run(cmds, save=wd / "stage1.sc")
    ids = {}
    for c, r in zip(cmds, res):
        nm = c["params"].get("name")
        if isinstance(r, dict) and r.get("feature") is not None and nm and c["command"].startswith("solid."): ids[nm] = r["feature"]
    # ---- configuration table: columns, one row per diameter, rules --------------------------------------------------------
    feats = ["Left step", "Right step"] + [h[0] for h in holes] + [b[0] for b in boxes]
    cfg = [{"command": "config.configure", "params": {"params": COLUMNS, "features": feats}}]
    wr = {r["D"]: r for r in read_csv(DATA / "wrench.csv")}
    for D in Dlist:
        vals = {f"param:{n}": DEFAULT[n] for n in COLUMNS}
        vals["param:D"] = str(D); vals["param:P"] = str(D); vals["param:H"] = g(sh.flat_depth(D))
        if str(D) in wr: vals["param:W"] = wr[str(D)]["W"]; vals["param:l1"] = wr[str(D)]["l1"]
        for f in feats: vals[f"suppress:{f}"] = True
        cfg.append({"command": "config.row", "params": {"name": str(D), "values": vals}})
    rules = []
    def rule(rid, name, cond, eff): rules.append({"id": rid, "name": name, "condition": cond, "effect": eff})
    pc = lambda n, op, e: {"type": "parameter", "parameter": n, "operator": op, "expression": str(e)}
    always = {"type": "always"}
    rule("length-range", "Length 10 to 1500 mm (S8 p.432 spec table)", always, {"type": "parameter_range", "parameter": "L", "minimum": "10 mm", "maximum": "1500 mm"})
    rule("m_left-values", "Left thread M: none or a size of the tap tables (S8 p.433, S30 p.434-438)", always,
         {"type": "allow_parameter_values", "parameter": "m_left", "expressions": ["0 mm"] + [f"{g(m)} mm" for m in sorted(set(L_SHAFT) | set(L_STEP))]})
    rule("m_right-values", "Right thread N: none or a size of the tap tables (S30 p.435-438)", always,
         {"type": "allow_parameter_values", "parameter": "m_right", "expressions": ["0 mm"] + [f"{g(m)} mm" for m in sorted(set(R_SHAFT) | set(R_STEP))]})
    def onoff(nm, cond):
        rule(nm + "-on", nm + " on", cond, {"type": "drive_suppression", "feature": ids[nm], "value": False})
        rule(nm + "-off", nm + " off", {"type": "not", "condition": cond}, {"type": "drive_suppression", "feature": ids[nm], "value": True})
    onoff("Left step", pc("F", "gt", "0 mm")); onoff("Right step", pc("T", "gt", "0 mm"))
    for nm, tag, m in holes:
        end = pc("m_left", "eq", f"{g(m)} mm") if tag.startswith("L") else pc("m_right", "eq", f"{g(m)} mm")
        stp = pc("F", "gt", "0 mm") if tag.startswith("L") else pc("T", "gt", "0 mm")
        onoff(nm, {"type": "all", "conditions": [end, stp if tag.endswith("step") else {"type": "not", "condition": stp}]})
    for nm, c in boxes: onoff(nm, pc(c, "ge", "0 mm"))
    cfg.append({"command": "config.rule", "params": {"rules": rules}})
    cfg.append({"command": "config.activate", "params": {"row": "10"}})
    run(cfg, src=wd / "stage1.sc", save=pkg / f"{PKG}.sc")
    write_tables(pkg); write_toml(pkg)
    shutil.rmtree(wd, ignore_errors=True)
    return ids

def write_tables(pkg: Path):
    t = pkg / "tables"
    for f in ("params", "types", "diameters", "tap", "tap_jc", "tap_jz", "tap_jw", "stepped_pg", "stepped_ph", "wrench"):
        shutil.copy(DATA / f"{f}.csv", t / f"{f}.csv")
    # derived rows the script reads (the lists of sizes and the catalogue page of each family), generated from the tables above
    rows = [["d_list", "|".join(str(d) for d in Dlist), "", "S8", "p.432 spec table", "labelled"]]
    for f in ("tap", "tap_jc", "tap_jz", "tap_jw", "stepped_pg", "stepped_ph"):
        rows.append([f"keys_{f}", "|".join(r["D"] for r in read_csv(DATA / f"{f}.csv")), "", "S8;S30", f"p.433-438 {f}", "labelled"])
    for fam, page in sh.FAM_PAGE.items():
        rows.append([f"page_{fam}", str(page), "", "S8;S30", f"p.{page}", "labelled"])
    with open(t / "params.csv", "a", newline="") as fh:
        csv.writer(fh, lineterminator="\n").writerows(rows)

TEMPLATES = [r"E\-{type: text 1..10 [A-Z]}{d: int 0..99}\-{length: decimal}{opts: bag(M:num, N:num, MD:num, F:int, P:int, T:int, SC:int, SX:int, WSC:int, X:int, FC:int, WFC:int, LFC:int, A:int, E:int, LKC)}",
             "{raw: text 1..128 [A-Za-z0-9._ /-]}"]

def write_toml(pkg: Path):
    lines = ['format = "solidcraft-generator/2"', f'id = "{PKG}"', 'name = "MISUMI Economy Series linear shafts (E- prefix): plain, tapped, stepped, flats"', 'license = "CC0-1.0"',
             f'model = "{PKG}.sc"', "", "[parameters]", 'part_type = { type = "text", default = "E-PSFJ" }',
             'd = { type = "int", min = 0, max = 99 }', 'length = { type = "decimal", min = 10, max = 1500, step = 0.1, unit = "mm" }', "",
             "# one template for the ordering code, a catch-all behind it so that the script gives the 'expected ...' refusal of the Python generator"]
    for p in TEMPLATES: lines += ["[[template]]", f"pattern = '{p}'", ""]
    for r in read_csv(DATA / "diameters.csv"):
        lines += [f'[rows."{r["D"]}"]', f'source = "MISUMI Economy Series catalogue 2025 (sources.toml S8), {r["page"]}"', f'page = "{r["page"]}"', 'status = "verified"',
                  'note = "diameter row: g7 / f8 limits, flat depth and wrench flat of this D; the options are parameters"', ""]
    (pkg / "generator.toml").write_text("\n".join(lines))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); a = ap.parse_args()
    ids = build(Path(a.out)); print(f"built {PKG}.sc with {len(ids)} named features")
