#!/usr/bin/env python3
"""Build the parametric MISUMI shaft-holder generator package (shf-shaft-holder/): the model shf-shaft-holder.sc, tables/*.csv and generator.toml.

One model for the four families (T-shaped with slit, with side slit, thickened, and the aluminium C-SHA), drawn ONCE and driven by user parameters.
The 30 catalogue rows ((family, D) of data/dims.csv and data/csha.csv) are configuration rows; the free value is the height H, whose allowed
list per row (h_all, and h_alu for the aluminium types) is a set of `allow_parameter_values` rules. The per-family topology is a set of suppression
columns of the rows and the same features are driven by `drive_suppression` rules on unitless parameters (fam, base_n, screws, msize).
A thread designation cannot come from a parameter, so there is one tapped-hole feature per thread size, switched by `msize`. Run through solidcraft-cli:

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

PKG = "shf-shaft-holder"
DATA = HERE.parent / "data"
CLI = os.environ.get("SC_CLI", "solidcraft-cli")
BODY = "Body"
FAM = {"slit": 0, "thick": 0, "side": 1, "csha": 2}

# user parameters: (name, default expression, unit, comment); the defaults are the thickened D30 row (the most features alive)
PARAMS = [("bore", "30", "mm", "shaft bore D"), ("th", "35", "mm", "thickness T (Y)"), ("base_len", "85", "mm", "foot length L"),
          ("foot_t", "10", "mm", "foot thickness S"), ("top_w", "45", "mm", "top width W"), ("h", "25", "mm", "bore centre height H (free: a list per row)"),
          ("h1_off", "33", "mm", "overall height H1 = H + h1_off"), ("l1", "65", "mm", "base hole pitch L1"), ("d_base", "6.6", "mm", "base hole d"),
          ("e_off", "24", "mm", "screw axis E (above the bore centre; from the bore centre across for the side slit)"),
          ("m_depth", "0", "mm", "tapped depth (0 = through the wall)"), ("d2", "9", "mm", "screw clearance hole d2"), ("d1", "14", "mm", "counterbore d1"),
          ("l_cb", "9", "mm", "counterbore depth l"), ("c_slit", "3", "mm", "slit width C (side slit: height; C-SHA: the drawn 2 mm slit)"),
          ("fam", "0", "", "0 slit and thickened, 1 side slit, 2 C-SHA"), ("screws", "2", "", "clamp screws: 1 or 2"), ("base_n", "4", "", "base holes: 2 or 4"),
          ("msize", "8", "", "clamp thread size M"), ("alu", "0", "", "1 = aluminium type (E-SHSTA / E-SHWTA): the h_alu list applies"),
          ("sel", "1", "", "row number (selects the allowed heights)"), ("part_type", "E-SHSTBN", "text", "catalogue type (material and finish only)")]
DERIVED = [("h1", "h + h1_off", "mm", "overall height H1"), ("sy1", "-(screws - 1) * th / 4", "mm", "first clamp screw / second base row offset (0 for one screw)"),
           ("sy2", "th / 4", "mm", "second clamp screw offset"),
           ("thr_depth", "m_depth + (1 - sign(m_depth / 1 mm)) * (top_w - c_slit) / 2", "mm", "tapped depth: m_depth, or the wall (W - C) / 2 when it is 0")]
COLUMNS = [n for n, *_ in PARAMS]
VT = [(4, 1), (5, 1), (6, 1), (8, 1), (8, 2), (12, 1), (12, 2)]     # (thread size, screw number) of the slit / thickened / C-SHA family
ST = [4, 6, 8]                                                        # side slit thread sizes
FEATS_BASE = ["ShaftBore", "BaseA1", "BaseA2", "BaseB1", "BaseB2", "BaseB3", "BaseB4"]
FEATS_V = ["VSlit", "VClear1", "VCbore1", "VClear2", "VCbore2"] + [f"VThread_M{m}_{k}" for m, k in VT]
FEATS_S = ["SideSlit", "SideClear", "SideCbore"] + [f"SideThread_M{m}" for m in ST]
FEATS = FEATS_BASE + FEATS_V + FEATS_S

from runtime.parametric.process import run_build

def run(cmds, src=None, save=None, workdir=None):
    return run_build(cmds, src, save, workdir, detailed=False, executable=CLI)

def cell(v):
    return f"{v:g}" if isinstance(v, float) else str(v)

def rows_of():
    """[(key, family, D, values dict, suppressed features set, h list, h_alu list)] for every catalogue row."""
    out = []
    for r in read_csv(DATA / "dims.csv"):
        fam = r["family"]; D = int(r["D"]); hs = [int(x) for x in r["h_all"].split("|")]; ha = [int(x) for x in r["h_alu"].split("|")] if r["h_alu"] else []
        v = dict(bore=r["D"], th=r["T"], base_len=r["L"], foot_t=r["S"], top_w=r["W"], h=hs[0], h1_off=r["h1_off"], l1=r["L1"], d_base=r["d"], e_off=r["E"],
                 m_depth=r["m_depth"], d2=r["d2"], d1=r["d1"], l_cb=r["l"], c_slit=r["C"], fam=FAM[fam], screws=r["screws"], base_n=r["base_holes"],
                 msize=r["M"], alu=0, sel=len(out) + 1, part_type={"slit": "E-SHSTB", "side": "E-SHWTB", "thick": "E-SHSTBN"}[fam])
        out.append((f"{fam}-{D}", fam, D, v, hs, ha))
    for r in read_csv(DATA / "csha.csv"):
        D = int(r["D"]); H = int(r["H"])
        v = dict(bore=r["D"], th=r["T"], base_len=r["L_ref"], foot_t=r["S_ref"], top_w=r["W_ref"], h=H, h1_off=int(r["H1_ref"]) - H, l1=r["L1"], d_base=r["d"],
                 e_off=(int(r["H1_ref"]) - H) / 2, m_depth=0, d2=1, d1=2, l_cb=1, c_slit=2, fam=2, screws=1, base_n=2, msize=r["M"], alu=0, sel=len(out) + 1,
                 part_type="C-SHA")
        out.append((f"csha-{D}", "csha", D, v, [H], []))
    return out

def alive(v):
    """The features a row keeps (the rest is suppressed): by family, screws, base holes and thread size."""
    fam, scr, bn, m = int(v["fam"]), int(v["screws"]), int(v["base_n"]), int(v["msize"])
    on = {"ShaftBore"}
    on |= {"BaseA1", "BaseA2"} if bn == 2 else {"BaseB1", "BaseB2", "BaseB3", "BaseB4"}
    if fam != 1:
        on |= {"VSlit", f"VThread_M{m}_1"}
    if fam == 0:
        on |= {"VClear1", "VCbore1"}
        if scr >= 2: on |= {"VClear2", "VCbore2", f"VThread_M{m}_2"}
    if fam == 1:
        on |= {"SideSlit", "SideClear", "SideCbore", f"SideThread_M{m}"}
    return on

def build(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    pkg = out / PKG; (pkg / "tables").mkdir(parents=True, exist_ok=True)
    wd = Path(tempfile.mkdtemp())
    rows = rows_of()
    cmds = []
    def add(c, **kw): cmds.append({"command": c, "params": kw})
    for n, e, u, c in PARAMS:
        add("parameters.add", name=n, expression=e, unit=u, comment=c)
    for n, e, u, c in DERIVED:
        add("parameters.add", name=n, expression=e, unit=u, comment=c)
    add("component.create", name="MISUMI shaft holder")
    # profile: foot L x S with a top W wide up to H1; extruded T symmetric about y = 0 (the plane sits at y = T / 2 and the extrusion runs toward -Y)
    add("sketch.create", plane={"origin": [0, "th / 2", 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Profile")
    add("sketch.line", points=[["-base_len / 2", 0], ["base_len / 2", 0], ["base_len / 2", "foot_t"], ["top_w / 2", "foot_t"], ["top_w / 2", "h1"],
                               ["-top_w / 2", "h1"], ["-top_w / 2", "foot_t"], ["-base_len / 2", "foot_t"]], closed=True)
    add("sketch.finish")
    add("solid.extrude", distance="th", name="Extrusion", body_name=BODY)
    def cyl(name, dia, height, base, axis):
        add("solid.cylinder", diameter=dia, height=height, base=base, axis=axis, operation="cut", targets=[BODY], name=name)
    def box(name, length, width, height, corner):
        add("solid.box", length=length, width=width, height=height, corner=corner, operation="cut", targets=[BODY], name=name)
    cyl("ShaftBore", "bore", "th + 2 mm", [0, "-th / 2 - 1 mm", "h"], "Y")
    for i, sx in enumerate(("-", "")):
        cyl(f"BaseA{i + 1}", "d_base", "foot_t + 2 mm", [f"{sx}l1 / 2", 0, "-1 mm"], "Z")
    for i, (sx, sy) in enumerate((("-", "-"), ("", "-"), ("-", ""), ("", ""))):
        cyl(f"BaseB{i + 1}", "d_base", "foot_t + 2 mm", [f"{sx}l1 / 2", f"{sy}th / 4", "-1 mm"], "Z")
    # slit and thickened and C-SHA: vertical slit, clearance + counterbore from the left face, tapped hole from the slit face
    box("VSlit", "c_slit", "th + 2 mm", "h1_off + 1 mm", ["-c_slit / 2", "-th / 2 - 1 mm", "h"])
    for k, y in ((1, "sy1"), (2, "sy2")):
        cyl(f"VClear{k}", "d2", "(top_w - c_slit) / 2 + 1 mm", ["-top_w / 2 - 1 mm", y, "h + e_off"], "X")
        cyl(f"VCbore{k}", "d1", "l_cb + 1 mm", ["-top_w / 2 - 1 mm", y, "h + e_off"], "X")
    for k, y in ((1, "sy1"), (2, "sy2")):
        add("sketch.create", plane={"origin": ["c_slit / 2", y, "h + e_off"], "x_dir": [0, 0, 1], "y_dir": [0, 1, 0]}, name=f"VThreadSketch{k}")
        add("sketch.point", point=[0, 0])
        add("sketch.finish")
    for m, k in VT:
        add("solid.hole", sketch=f"VThreadSketch{k}", thread=f"M{m}", depth="thr_depth", targets=[BODY], name=f"VThread_M{m}_{k}")
        add("timeline.suppress", feature=f"VThread_M{m}_{k}", suppressed=True)     # one at a time: the next size drills the same place
    # the side slit group is drawn with the side D30 dimensions (its screw axis E runs across, not up) and the slit group switched off
    side30 = next(v for key, fam, D, v, hs, ha in rows if key == "side-30")
    for f in FEATS_V[:5]:
        add("timeline.suppress", feature=f, suppressed=True)
    add("parameters.change", changes={n: cell(side30[n]) for n in ("bore", "th", "base_len", "foot_t", "top_w", "h", "h1_off", "l1", "d_base", "e_off", "m_depth", "d2", "d1", "l_cb", "c_slit")})
    # side slit: slit, clearance and counterbore from the top, tapped hole from the slit floor
    box("SideSlit", "top_w / 2 + 1 mm", "th + 2 mm", "c_slit", [0, "-th / 2 - 1 mm", "h - c_slit / 2"])
    cyl("SideClear", "d2", "h1_off + 1 mm", ["e_off", 0, "h"], "Z")
    cyl("SideCbore", "d1", "l_cb + 1 mm", ["e_off", 0, "h1 - l_cb"], "Z")
    add("sketch.create", plane={"origin": ["e_off", 0, "h - c_slit / 2"], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="SideThreadSketch")
    add("sketch.point", point=[0, 0])
    add("sketch.finish")
    for m in ST:
        add("solid.hole", sketch="SideThreadSketch", thread=f"M{m}", depth="m_depth", targets=[BODY], name=f"SideThread_M{m}")
        add("timeline.suppress", feature=f"SideThread_M{m}", suppressed=True)
    add("browser.visibility", items=["Profile", "VThreadSketch1", "VThreadSketch2", "SideThreadSketch"], visible=False)
    res = run(cmds, save=wd / "stage1.sc", workdir=wd)
    ids = {}
    for c, r in zip(cmds, res):
        nm = c["params"].get("name")
        if isinstance(r, dict) and r.get("feature") is not None and nm and c["command"].startswith("solid."): ids[nm] = r["feature"]
    missing = [f for f in FEATS if f not in ids]
    if missing: sys.exit(f"no feature id in the replies for {missing}")
    # ---- configuration table ------------------------------------------------------------------------------------------
    cfg = [{"command": "config.configure", "params": {"params": COLUMNS, "features": FEATS}}]
    for key, fam, D, v, hs, ha in rows:
        vals = {f"param:{k}": (x if k == "part_type" else cell(x)) for k, x in v.items()}
        on = alive(v)
        vals.update({f"suppress:{f}": f not in on for f in FEATS})
        cfg.append({"command": "config.row", "params": {"name": key, "values": vals}})
    # the "Default" row that config.configure makes from the current values is the stage-1 working state, not a catalogue row: drop it before the rules check the rows
    cfg.append({"command": "config.activate", "params": {"row": rows[0][0]}})
    cfg.append({"command": "config.row", "params": {"name": "Default", "delete": True}})
    rules = []
    def rule(rid, name, cond, eff): rules.append({"id": rid, "name": name, "condition": cond, "effect": eff})
    pc = lambda n, op, e: {"type": "parameter", "parameter": n, "operator": op, "expression": str(e)}
    allof = lambda *c: {"type": "all", "conditions": list(c)}
    sup = lambda f, cond: [rule(f"{f}-on", f"{f} on", cond, {"type": "drive_suppression", "feature": ids[f], "value": False}),
                           rule(f"{f}-off", f"{f} off", {"type": "not", "condition": cond}, {"type": "drive_suppression", "feature": ids[f], "value": True})]
    sup("BaseA1", pc("base_n", "eq", 2)); sup("BaseA2", pc("base_n", "eq", 2))
    for i in range(1, 5): sup(f"BaseB{i}", pc("base_n", "eq", 4))
    sup("VSlit", pc("fam", "ne", 1))
    for f in ("VClear1", "VCbore1"): sup(f, pc("fam", "eq", 0))
    for f in ("VClear2", "VCbore2"): sup(f, allof(pc("fam", "eq", 0), pc("screws", "ge", 2)))
    for m, k in VT:
        sup(f"VThread_M{m}_{k}", allof(pc("fam", "ne", 1), pc("msize", "eq", m)) if k == 1 else allof(pc("fam", "eq", 0), pc("screws", "ge", 2), pc("msize", "eq", m)))
    for f in ("SideSlit", "SideClear", "SideCbore"): sup(f, pc("fam", "eq", 1))
    for m in ST: sup(f"SideThread_M{m}", allof(pc("fam", "eq", 1), pc("msize", "eq", m)))
    always = {"type": "always"}
    rule("h-range", "H 10 to 80 mm (S50 p.541 / p.542 tables)", always, {"type": "parameter_range", "parameter": "h", "minimum": "10 mm", "maximum": "80 mm"})
    rule("screws-range", "clamp screws 1 or 2", always, {"type": "parameter_range", "parameter": "screws", "minimum": "1", "maximum": "2"})
    rule("base-holes", "2 or 4 base holes", always, {"type": "parameter_range", "parameter": "base_n", "minimum": "2", "maximum": "4"})
    for key, fam, D, v, hs, ha in rows:
        page = {"csha": "p.540", "thick": "p.542"}.get(fam, "p.541")
        sel = pc("sel", "eq", v["sel"])
        if fam == "csha":
            rule(f"h-{key}", f"{key}: one fixed height ({page})", sel, {"type": "allow_parameter_values", "parameter": "h", "expressions": [f"{hs[0]} mm"]})
            continue
        rule(f"h-{key}", f"{key}: H from the {page} table", allof(sel, pc("alu", "eq", 0)), {"type": "allow_parameter_values", "parameter": "h", "expressions": [f"{x} mm" for x in hs]})
        if ha:
            rule(f"halu-{key}", f"{key}: aluminium types only for the * marked H ({page})", allof(sel, pc("alu", "eq", 1)),
                 {"type": "allow_parameter_values", "parameter": "h", "expressions": [f"{x} mm" for x in ha]})
    from runtime.parametric import limit_rules
    cfg.append({"command": "config.rule", "params": {"rules": limit_rules(rules)}})
    cfg.append({"command": "config.activate", "params": {"row": rows[0][0]}})
    run(cfg, src=wd / "stage1.sc", save=pkg / f"{PKG}.sc", workdir=wd)
    pkgfiles.write_tables(pkg, DATA, [r[0] for r in rows]); pkgfiles.write_toml(pkg, DATA)
    shutil.rmtree(wd, ignore_errors=True)
    return ids

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); a = ap.parse_args()
    ids = build(Path(a.out)); print(f"built {PKG}.sc with {len(ids)} named features")
