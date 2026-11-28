#!/usr/bin/env python3
"""Build the parametric MISUMI extrusion generator package (hfs-extrusion/): the model hfs-extrusion.sc, tables/*.csv and generator.toml.

The model is drawn ONCE, driven by user parameters (section dimensions, length, end-tap and wrench-hole options). The catalogue rows
(data/profiles.csv, one per profile) become configuration rows; per-profile topology (which sketch/extrusion/tap features exist) is a
suppression column of those rows; the suffix options are drive_suppression rules on parameters. Run through solidcraft-cli:

    SC_CLI=<solidcraft-cli> python3 build.py [--out DIR]
"""
from __future__ import annotations
import argparse, csv, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from vendors.misumi.hfs.extrusion.src import profiles as pr, ext
from runtime.table import read_csv
from lin import Lin, P
import pkgfiles

PKG = "hfs-extrusion"
DATA = HERE.parent / "data"
PROFILES = ["2020", "2040", "4040", "3030"]
SIDES = "RTLB"
CLI = os.environ.get("SC_CLI", "solidcraft-cli")

# ---- user parameters: (name, default expression, unit, comment) ----------------------------------------------------
SECTION = ["w", "h", "corner_r", "tip_r", "mouth", "lip", "cavity", "d0", "floor_half", "depth"]
PARAMS = [("profile", "2020", "", "profile code 2020 / 2040 / 4040 / 3030 (the configuration row)"),
          ("part_type", "HFS5", "text", "catalogue type (HFS5, HFSB5, NFS5, CAF6 ...): material and finish only, no geometry"),
          ("length", "1000", "mm", "extrusion length L"), ("fixed", "0", "", "1 = fixed-length K type (1000 or 4000 only)"),
          ("tap_l", "0", "", "end tapping on the left end (LTP / TPW)"), ("tap_r", "0", "", "end tapping on the right end (RTP / TPW)"),
          ("wl_rows", "0", "", "wrench access holes on the left end: 0..3 (C / W / E)"), ("wl_dir", "0", "", "left holes: 0 horizontal (Y), 1 vertical (Z)"),
          ("wl_shift", "0", "mm", "FL: left holes moved toward the end"),
          ("wr_rows", "0", "", "wrench access holes on the right end: 0..3"), ("wr_dir", "0", "", "right holes: 0 horizontal (Y), 1 vertical (Z)"),
          ("wr_shift", "0", "mm", "FR: right holes moved toward the end"),
          ("wh_h", "10", "mm", "wrench hole H: first hole from the end"), ("wh_j", "20", "mm", "wrench hole J: second hole"),
          ("wh_k", "20", "mm", "wrench hole K: third hole"), ("wh_d", "7.35", "mm", "wrench hole diameter d")]
SEC_PARAMS = [(n, "20", "mm", "section dimension (row of data/profiles.csv)") for n in SECTION]
DERIVED = [("wl_x1", "wh_h - wl_shift"), ("wl_x2", "wl_x1 + wh_j"), ("wl_x3", "wl_x2 + wh_k"),
           ("wr_x1", "length - (wh_h - wr_shift)"), ("wr_x2", "wr_x1 - wh_j"), ("wr_x3", "wr_x2 - wh_k")]
COLUMNS = [n for n, *_ in SEC_PARAMS] + [n for n, *_ in PARAMS]

def sketch_cmds(p: pr.Profile, tag: str):
    """Section sketch of profile `p` on the YZ plane, every slot / outline coordinate an expression over w, h, mouth, lip, cavity, d0,
    floor_half, depth; voids and bores are the drawing's fixed numbers."""
    hx, hy = P("w") * 0.5, P("h") * 0.5
    frame = {"R": ((1, 0), (0, 1), (hx, 0), hy), "T": ((0, 1), (-1, 0), (0, hy), hx),
             "L": ((-1, 0), (0, -1), (-hx, 0), hy), "B": ((0, -1), (1, 0), (0, -hy), hx)}
    m, wc, f = P("mouth") * 0.5, P("cavity") * 0.5, P("floor_half")
    slot = [(-m, 0, "mouth"), (-m, P("lip"), ""), (-wc, P("lip"), ""), (-wc, P("d0"), ""), (-f, P("depth"), ""), (f, P("depth"), ""),
            (wc, P("d0"), ""), (wc, P("lip"), ""), (m, P("lip"), ""), (m, 0, "mouth")]
    pts = []
    for side in SIDES:
        n, t, c, half = frame[side]
        L = lambda a, b: Lin.of(a) if not isinstance(a, Lin) else a
        pts.append(((c[0] if isinstance(c[0], Lin) else Lin.of(c[0])) - half * t[0], (c[1] if isinstance(c[1], Lin) else Lin.of(c[1])) - half * t[1], "corner"))
        for off in sorted(p.slots.get(side, [])):
            for u, v, tag_ in slot:
                uu = Lin.of(u) + off; vv = Lin.of(v)
                cx = c[0] if isinstance(c[0], Lin) else Lin.of(c[0]); cy = c[1] if isinstance(c[1], Lin) else Lin.of(c[1])
                pts.append((cx + uu * t[0] - vv * n[0], cy + uu * t[1] - vv * n[1], tag_))
    n = len(pts)
    cmds = []
    def add(c, **kw): cmds.append({"command": c, "params": kw})
    add("sketch.create", plane="YZ", name=f"Profile{tag}")
    add("sketch.line", points=[[x.value(), y.value()] for x, y, _ in pts], closed=True)
    corner = [f"l{(i - 1) % n + 1}.end" for i in range(n) if pts[i][2] == "corner"]
    mouth = [f"l{(i - 1) % n + 1}.end" for i in range(n) if pts[i][2] == "mouth"]
    add("sketch.fillet", points=corner, radius="corner_r")
    add("sketch.fillet", points=mouth, radius="tip_r")
    for v in p.voids:
        if any(isinstance(it, pr.Arc) for it in v):
            for kind, s in ext._void_runs(v):
                if kind == "line": add("sketch.line", points=[[x, y] for x, y in s])
                else: add("sketch.arc.three_point", start=list(s.a), through=list(s.t), end=list(s.b))
        else:
            add("sketch.line", points=[[x, y] for x, y in v], closed=True)
    for bx, by, d in p.bores:
        add("sketch.circle.center", center=[bx, by], diameter=d)
    add("sketch.finish")
    add("solid.extrude", distance="length", name=f"Extrusion{tag}", body_name=f"Extrusion{tag}")
    return cmds

def tap_points(p: pr.Profile):
    """(index, y, z) of the point on each tapped bore's cylinder face (as ext.commands does)."""
    out = []
    for bi, (bx, by, d) in enumerate(pr.all_bores(p)):
        if p.arc_bores:
            ux, uy = (1 if bx > 0 else -1) / 2 ** 0.5, (1 if by > 0 else -1) / 2 ** 0.5
        else:
            ux, uy = 1.0, 0.0
        if p.key == "3030" and d != 6.8:
            continue
        out.append((bi + 1, bx + ux * d / 2, by + uy * d / 2))
    return out

from runtime.parametric.process import run_build

def run(cmds, src=None, save=None, workdir=None):
    return run_build(cmds, src, save, workdir, detailed=False, executable=CLI)

def cell(v):
    return f"{v:g}" if isinstance(v, float) else str(v)

def build(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    pkg = out / PKG; (pkg / "tables").mkdir(parents=True, exist_ok=True)
    wd = Path(tempfile.mkdtemp())
    rows = {r["key"]: r for r in read_csv(DATA / "profiles.csv")}
    base = rows["2020"]
    cmds, names = [], []
    def add(c, **kw): cmds.append({"command": c, "params": kw})
    for n, e, u, c in SEC_PARAMS + PARAMS:
        e = {"w": base["w"], "h": base["h"], "corner_r": base["corner_r"], "tip_r": base["tip_r"], "mouth": base["mouth"], "lip": base["lip"],
             "cavity": base["cavity"], "d0": base["d0"], "floor_half": base["floor_half"], "depth": base["depth"]}.get(n, e)
        add("parameters.add", name=n, expression=str(e), unit=u, comment=c)
    for n, e in DERIVED:
        add("parameters.add", name=n, expression=e, unit="mm", comment="derived wrench hole position from the left end (x)")
    add("component.create", name="HFS extrusion")
    def only(key, existing):
        """Suppress the profile features of every other (already drawn) profile and set the section parameters to this row: the sketch
        points are expressions, so they take the row's values while it is drawn (and a suppressed sketch is not rebuilt)."""
        for other in existing:
            for f in (f"Profile{other}", f"Extrusion{other}"):
                add("timeline.suppress", feature=f, suppressed=(other != key))
        add("parameters.change", changes={n: str(rows[key][n]) for n in SECTION})
    for i, key in enumerate(PROFILES):
        only(key, PROFILES[:i])
        cmds.extend(sketch_cmds(pr.P[key], key))
    # cosmetic end threads per profile, bore and end; created with only that profile's extrusion live
    for key in PROFILES:
        only(key, PROFILES)
        p = pr.P[key]
        thread, depth = p.tap
        for side in "LR":
            for bi, py, pz in tap_points(p):
                x_face = 0.5 if side == "L" else 1000 - 0.5
                add("solid.thread", face=[x_face, py, pz], designation=thread, extent="length", length=depth,
                    **{"from": [0.0 if side == "L" else 1000.0, py, pz]}, name=f"Tap{side}{key}_{bi}")
        for side in "LR":
            for bi, py, pz in tap_points(p):
                add("timeline.suppress", feature=f"Tap{side}{key}_{bi}", suppressed=True)
    only("2020", PROFILES)         # the saved source state is the 2020 row
    # wrench access holes: 2 sides x 3 rows x 2 directions (cylinder axis cannot be a parameter), cut through the whole section
    for side, S in (("L", "wl"), ("R", "wr")):
        for i in (1, 2, 3):
            for d, (axis, mk) in enumerate((("Y", lambda x: [x, -50, 0]), ("Z", lambda x: [x, 0, -50]))):
                add("solid.cylinder", diameter="wh_d", height=100, base=mk(f"{S}_x{i}"), axis=axis, operation="cut",
                    name=f"Wrench{side}{i}{'HV'[d]}")
                add("timeline.suppress", feature=f"Wrench{side}{i}{'HV'[d]}", suppressed=True)
    add("browser.visibility", items=["Profile" + k for k in PROFILES], visible=False)
    res = run(cmds, save=wd / "stage1.sc", workdir=wd)
    # feature ids by name, from the creating commands' replies
    ids = {}
    for c, r in zip(cmds, res):
        nm = c["params"].get("name")
        if c["command"] == "sketch.create": ids[nm] = r["sketch"]
        elif isinstance(r, dict) and r.get("feature") is not None and nm and c["command"].startswith("solid."): ids[nm] = r["feature"]
    # ---- configuration table: columns, one row per profile, rules --------------------------------------------------
    feats = [f"{pre}{k}" for k in PROFILES for pre in ("Profile", "Extrusion")] + sorted(
        n for n in ids if n.startswith("Tap") or n.startswith("Wrench"))
    cfg = [{"command": "config.configure", "params": {"params": COLUMNS, "features": feats}}]
    for key in PROFILES:
        r = rows[key]; p = pr.P[key]
        vals = {f"param:{n}": cell(r[n]) for n in SECTION}
        vals.update({"param:profile": key, "param:part_type": "HFS6" if key == "3030" else "HFS5", "param:length": "1000", "param:fixed": "0", "param:tap_l": "0", "param:tap_r": "0",
                     "param:wl_rows": "0", "param:wl_dir": "0", "param:wl_shift": "0", "param:wr_rows": "0", "param:wr_dir": "0",
                     "param:wr_shift": "0", "param:wh_h": r["wrench_h"], "param:wh_j": r["wrench_j"], "param:wh_k": r["wrench_k"],
                     "param:wh_d": r["wrench_d"].split("|")[-1]})
        for k2 in PROFILES:
            on = k2 == key
            vals[f"suppress:Profile{k2}"] = not on; vals[f"suppress:Extrusion{k2}"] = not on
        for n in ids:
            if n.startswith("Tap"):
                vals[f"suppress:{n}"] = True
            if n.startswith("Wrench"):
                vals[f"suppress:{n}"] = True
        cfg.append({"command": "config.row", "params": {"name": key, "values": vals}})
    rules = []
    def rule(rid, name, cond, eff): rules.append({"id": rid, "name": name, "condition": cond, "effect": eff})
    pc = lambda n, op, e: {"type": "parameter", "parameter": n, "operator": op, "expression": str(e)}
    always = {"type": "always"}
    rule("length-range", "Length 50 to 4000 mm (S1 p.529, S10 p.571)", always, {"type": "parameter_range", "parameter": "length", "minimum": "50 mm", "maximum": "4000 mm"})
    rule("fixed-lengths", "K types: 1000 or 4000 mm only (S1 p.529)", pc("fixed", "eq", 1), {"type": "allow_parameter_values", "parameter": "length", "expressions": ["1000 mm", "4000 mm"]})
    rule("d-6series", "6 series wrench hole d 5 or 8 (S3 p.759)", pc("profile", "eq", 3030), {"type": "allow_parameter_values", "parameter": "wh_d", "expressions": ["5 mm", "8 mm"]})
    rule("d-5series", "5 series wrench hole d 7.35 (S3 p.759)", pc("profile", "ne", 3030), {"type": "allow_parameter_values", "parameter": "wh_d", "expressions": ["7.35 mm"]})
    for n in ("wl_rows", "wr_rows"):
        rule(f"{n}-range", f"{n} 0 to 3", always, {"type": "parameter_range", "parameter": n, "minimum": "0", "maximum": "3"})
    for n, fid in ids.items():
        if n.startswith("Wrench"):
            side, i, d = n[6], int(n[7]), n[8]
            S = "wl" if side == "L" else "wr"
            dv = 0 if d == "H" else 1
            on = {"type": "all", "conditions": [pc(f"{S}_rows", "ge", i), pc(f"{S}_dir", "eq", dv)]}
            off = {"type": "not", "condition": on}
            rule(f"{n}-on", f"{n} on", on, {"type": "drive_suppression", "feature": fid, "value": False})
            rule(f"{n}-off", f"{n} off", off, {"type": "drive_suppression", "feature": fid, "value": True})
        elif n.startswith("Tap"):
            side, key = n[3], n[4:8]
            tp = "tap_l" if side == "L" else "tap_r"
            on = {"type": "all", "conditions": [pc(tp, "eq", 1), pc("profile", "eq", key)]}
            rule(f"{n}-on", f"{n} on", on, {"type": "drive_suppression", "feature": fid, "value": False})
            rule(f"{n}-off", f"{n} off", {"type": "not", "condition": on}, {"type": "drive_suppression", "feature": fid, "value": True})
    from runtime.parametric import limit_rules
    cfg.append({"command": "config.rule", "params": {"rules": limit_rules(rules)}})
    cfg.append({"command": "config.activate", "params": {"row": "2020"}})
    run(cfg, src=wd / "stage1.sc", save=pkg / f"{PKG}.sc", workdir=wd)
    pkgfiles.write_tables(pkg, DATA); pkgfiles.write_toml(pkg, DATA)
    shutil.rmtree(wd, ignore_errors=True)
    return ids

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); a = ap.parse_args()
    ids = build(Path(a.out)); print(f"built {PKG}.sc with {len(ids)} named features")
