#!/usr/bin/env python3
"""Build the parametric MISUMI linear bushing generator package (linear-bushing/): the model linear-bushing.sc, tables/*.csv, generator.toml.

The bushing is modelled ONCE, driven by user parameters (outside diameter, bore, length, flange and hole dimensions, flange position,
groove dimensions, counterbore side, plating). The 178 catalogue rows (rows.py: one per table row and flange shape, from data/*.csv)
become configuration rows; which features exist (revolve profile with or without grooves / round flange, square or compact flange sketch,
axis or compact holes) is a suppression column of those rows; single or double length (blen) is an allowed-values rule per row. Run through
solidcraft-cli:

    SC_CLI=<solidcraft-cli> python3 build.py [--out DIR]
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
import pkgfiles, rows as rw

PKG = "linear-bushing"
CLI = os.environ.get("SC_CLI", "solidcraft-cli")
MM = ("od", "blen", "bore", "fl_h", "fl_t", "hole_d", "cb_d", "cb_t", "pcd", "sq_w", "cp_a", "cp_f", "cp_w", "x0", "g_b", "g_w", "g_d1")
UNITLESS = ("rowno", "kind", "opp", "plated")
COLUMNS = ["rowno", "kind", "od", "blen", "bore", "opp", "plated", "fl_h", "fl_t", "hole_d", "cb_d", "cb_t", "pcd", "sq_w", "cp_a", "cp_f", "cp_w", "x0", "g_b", "g_w", "g_d1"]
COMMENT = {"rowno": "number of the configuration row (the rules name it)", "kind": "0 straight, 1 round flange, 2 round flange with offset, 3 square flange, 4 compact flange (which hole sets exist)", "od": "outside diameter D", "blen": "overall length L (single or double bushing)",
           "bore": "bore at the nominal shaft diameter dr", "opp": "1 = counterbores on the flange face away from the barrel (Z types)",
           "plated": "1 = electroless nickel plated (tolerance text and material only)", "fl_h": "flange diameter H", "fl_t": "flange thickness T",
           "hole_d": "mounting hole d", "cb_d": "counterbore d1", "cb_t": "counterbore depth t", "pcd": "P.C.D. of the 4 holes (round, square flange)",
           "sq_w": "square flange across flats W", "cp_a": "compact flange hole pitch A (along H)", "cp_f": "compact flange hole pitch F (across; 0 = two holes)",
           "cp_w": "compact flange width across the flats", "x0": "x of the flange face nearest the start of the barrel (pilot / centre l)",
           "g_b": "distance B between the two ring grooves", "g_w": "ring groove width W", "g_d1": "ring groove diameter D1"}
DERIVED = [("hr", "pcd / 2", "radius of the holes on the P.C.D."),
           ("ha", "cp_a / 2", "compact flange holes: half of A"), ("he", "cp_f / 2", "compact flange holes: half of F"),
           ("sq_a", "sq_w / sqrt(2)", "square flange stands on its corner: half-diagonal of the flats"),
           ("sq_s", "sqrt(2 * (fl_h / 2) * (fl_h / 2) - sq_a * sq_a)", "square flange: circle H cuts the corner at this offset"),
           ("sq_py", "(sq_a + sq_s) / 2", "square flange corner points"), ("sq_pz", "(sq_a - sq_s) / 2", "square flange corner points"),
           ("cp_e", "cp_w / 2", "compact flange: flats at this distance"), ("cp_s", "sqrt((fl_h / 2 - cp_e) * (fl_h / 2 + cp_e))", "compact flange: end of the flats on circle H")]

def cell(v):
    return f"{v:g}" if isinstance(v, float) else str(v)

def run(cmds, src=None, save=None, workdir=None):
    wd = Path(workdir)
    script = wd / "step.json"; res = wd / "step.res.json"
    script.write_text(json.dumps({"commands": cmds}))
    a = [CLI, "run", str(script), "--results", "--json-out", str(res), "--quiet"]
    if src: a += ["--in", str(src)]
    if save: a += ["--save", str(save)]
    r = subprocess.run(a, capture_output=True, text=True)
    out = json.loads(res.read_text()) if res.exists() else {}
    if r.returncode != 0 or (isinstance(out, dict) and out.get("error")):
        err = out.get("error") if isinstance(out, dict) else out
        done = len(out.get("results", [])) if isinstance(out, dict) else 0
        where = cmds[done] if done < len(cmds) else None
        sys.exit(f"solidcraft-cli failed after {done} commands, at {json.dumps(where)[:600]}:\n{r.stderr[-1500:]}\n{json.dumps(err)[:1500]}")
    return out if isinstance(out, list) else out["results"]

# ---- the geometry: every coordinate an expression over the parameters ----------------------------------------------
R_ = "od / 2"
def profile_pts(kind):
    if kind == "Plain":
        return [[0, 0], ["blen", 0], ["blen", R_], [0, R_]]
    if kind == "Grooved":
        g1s, g1e, g2s, g2e = "(blen - g_b) / 2 - g_w", "(blen - g_b) / 2", "(blen + g_b) / 2", "(blen + g_b) / 2 + g_w"
        r1 = "g_d1 / 2"
        return [[0, 0], ["blen", 0], ["blen", R_], [g2e, R_], [g2e, r1], [g2s, r1], [g2s, R_], [g1e, R_], [g1e, r1], [g1s, r1], [g1s, R_], [0, R_]]
    if kind == "Round0":
        return [[0, 0], ["blen", 0], ["blen", R_], ["fl_t", R_], ["fl_t", "fl_h / 2"], [0, "fl_h / 2"]]
    return [[0, 0], ["blen", 0], ["blen", R_], ["x0 + fl_t", R_], ["x0 + fl_t", "fl_h / 2"], ["x0", "fl_h / 2"], ["x0", R_], [0, R_]]

FLANGE_PLANE = {"origin": ["x0", 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}

def revolve_cmds(kind):
    return [{"command": "sketch.create", "params": {"plane": "XY", "name": f"Profile{kind}"}},
            {"command": "sketch.line", "params": {"points": profile_pts(kind), "closed": True}},
            {"command": "sketch.finish", "params": {}},
            {"command": "solid.revolve", "params": {"axis": "x", "name": f"Revolve{kind}", "body_name": f"Body{kind}"}}]

def points_cmds(pts):
    return [{"command": "sketch.point", "params": {"point": list(v), "id": k}} for k, v in pts.items()]

def square_cmds():
    P = {"ns1": ("sq_py", "-sq_pz"), "ns2": ("sq_pz", "-sq_py"), "ns3": ("-sq_pz", "-sq_py"), "ns4": ("-sq_py", "-sq_pz"),
         "ns5": ("-sq_py", "sq_pz"), "ns6": ("-sq_pz", "sq_py"), "ns7": ("sq_pz", "sq_py"), "ns8": ("sq_py", "sq_pz"),
         "nt1": ("fl_h / 2", 0), "nt2": (0, "-fl_h / 2"), "nt3": ("-fl_h / 2", 0), "nt4": (0, "fl_h / 2")}
    c = [{"command": "sketch.create", "params": {"plane": FLANGE_PLANE, "name": "SquareSketch"}}] + points_cmds(P)
    for a, b in (("ns1", "ns2"), ("ns3", "ns4"), ("ns5", "ns6"), ("ns7", "ns8")):
        c.append({"command": "sketch.line", "params": {"points": [a, b]}})
    for s, t, e in (("ns8", "nt1", "ns1"), ("ns2", "nt2", "ns3"), ("ns4", "nt3", "ns5"), ("ns6", "nt4", "ns7")):
        c.append({"command": "sketch.arc.three_point", "params": {"start": s, "through": t, "end": e}})
    return c + [{"command": "sketch.finish", "params": {}},
                {"command": "solid.extrude", "params": {"distance": "fl_t", "operation": "join", "name": "SquareFlange"}}]

def compact_cmds():
    P = {"nc1": ("cp_e", "-cp_s"), "nc2": ("cp_e", "cp_s"), "nc3": ("-cp_e", "cp_s"), "nc4": ("-cp_e", "-cp_s"),
         "nt1": (0, "fl_h / 2"), "nt2": (0, "-fl_h / 2")}
    c = [{"command": "sketch.create", "params": {"plane": FLANGE_PLANE, "name": "CompactSketch"}}] + points_cmds(P)
    c.append({"command": "sketch.line", "params": {"points": ["nc1", "nc2"]}})
    c.append({"command": "sketch.arc.three_point", "params": {"start": "nc2", "through": "nt1", "end": "nc3"}})
    c.append({"command": "sketch.line", "params": {"points": ["nc3", "nc4"]}})
    c.append({"command": "sketch.arc.three_point", "params": {"start": "nc4", "through": "nt2", "end": "nc1"}})
    return c + [{"command": "sketch.finish", "params": {}},
                {"command": "solid.extrude", "params": {"distance": "fl_t", "operation": "join", "name": "CompactFlange"}}]

def hole_cmd(name, x, y, z):
    return {"command": "solid.hole", "params": {"position": [x, y, z], "diameter": "hole_d", "type": "counterbore", "cb_diameter": "cb_d",
                                                "cb_depth": "cb_t", "depth": "fl_t", "name": name}}

AXIS = [("hr", 0), (0, "hr"), ("-hr", 0), (0, "-hr")]
COMPACT = [("he", "ha"), ("-he", "ha"), ("-he", "-ha"), ("he", "-ha")]

def build(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    pkg = out / PKG; (pkg / "tables").mkdir(parents=True, exist_ok=True)
    wd = Path(tempfile.mkdtemp())
    R = rw.make_rows()
    by = {r["name"]: r for r in R}
    cmds, created = [], []
    def add(c, **kw): cmds.append({"command": c, "params": kw})
    first = R[0]["params"]
    for n in COLUMNS:
        add("parameters.add", name=n, expression=cell(first[n]), unit="mm" if n in MM else "", comment=COMMENT[n])
    for n in ("fl_h", "fl_t", "hole_d", "cb_d", "cb_t", "pcd", "sq_w", "cp_a", "cp_f", "cp_w", "x0", "g_b", "g_w", "g_d1"):
        pass
    for n, e, c in DERIVED:
        add("parameters.add", name=n, expression=e, unit="mm", comment=c)
    add("component.create", name="Linear bushing")

    def state(ref, live):
        """The reference row's values with only the `live` features switched on (everything made so far)."""
        off = [f for f in created if f not in live]
        if off: add("timeline.suppress", features=off, suppressed=True)
        add("parameters.change", changes={n: cell(by[ref]["params"][n]) for n in COLUMNS})
        on = [f for f in created if f in live]
        if on: add("timeline.suppress", features=on, suppressed=False)

    def make(cs, names):
        cmds.extend(cs); created.extend(names)
    ref = {"Plain": "short-6", "Grooved": "medium-6", "Round0": "flanged_long-round-6", "RoundOff": "pilot_long-round-6"}
    for k in rw.REVOLVES:
        state(ref[k], set())
        make(revolve_cmds(k), [f"Profile{k}", f"Revolve{k}"])
    state("flanged_long-square-6", {"ProfilePlain", "RevolvePlain"})
    make(square_cmds(), ["SquareSketch", "SquareFlange"])
    state("compact_long-compact-16", {"ProfilePlain", "RevolvePlain"})
    make(compact_cmds(), ["CompactSketch", "CompactFlange"])
    state("short-6", {"ProfilePlain", "RevolvePlain"})
    add("solid.cylinder", diameter="bore", height="blen + 2", base=[-1, 0, 0], axis="X", operation="cut", name="Bore")
    holes_at = {"Round0": ("flanged_long-round-6", {"ProfileRound0", "RevolveRound0"}), "RoundOff": ("pilot_long-round-6", {"ProfileRoundOff", "RevolveRoundOff"}),
                "Square": ("flanged_long-square-6", {"ProfilePlain", "RevolvePlain", "SquareSketch", "SquareFlange"}),
                "Compact": ("compact_long-compact-16", {"ProfilePlain", "RevolvePlain", "CompactSketch", "CompactFlange"})}
    for v, _k in rw.HOLEVARS:
        pos = COMPACT if v == "Compact" else AXIS
        for side, x in (("Near", "x0 + fl_t"), ("Far", "x0")):
            if v == "RoundOff" and side == "Far": continue
            state(holes_at[v][0], holes_at[v][1])          # the other side's holes are suppressed: their bores would take the face away
            make([hole_cmd(f"Hole{v}{side}{i + 1}", x, y, z) for i, (y, z) in enumerate(pos)], [f"Hole{v}{side}{i}" for i in (1, 2, 3, 4)])
    add("browser.visibility", items=[f"Profile{k}" for k in rw.REVOLVES] + ["SquareSketch", "CompactSketch"], visible=False)
    res = run(cmds, save=wd / "stage1.sc", workdir=wd)
    ids = {}
    for c, r in zip(cmds, res):
        nm = c["params"].get("name")
        if c["command"] == "sketch.create": ids[nm] = r["sketch"]
        elif isinstance(r, dict) and r.get("feature") is not None and nm and c["command"].startswith("solid."): ids[nm] = r["feature"]
    # ---- configuration table: columns, one row per catalogue row, rules ---------------------------------------------
    feats = rw.feature_names()
    cfg = [{"command": "config.configure", "params": {"params": COLUMNS, "features": feats}}]
    for r in R:
        vals = {f"param:{n}": cell(r["params"][n]) for n in COLUMNS}
        vals.update({f"suppress:{f}": f not in r["features"] for f in feats})
        cfg.append({"command": "config.row", "params": {"name": r["name"], "values": vals}})
    rules = []
    def rule(rid, name, cond, eff): rules.append({"id": rid, "name": name, "condition": cond, "effect": eff})
    pc = lambda n, op, e: {"type": "parameter", "parameter": n, "operator": op, "expression": str(e)}
    for r in R:
        k = r["params"]["rowno"]; where = f"{r['name']} ({r['source']} {r['page']})"
        cond = pc("rowno", "eq", k)
        rule(f"len-{k}", f"L of {where}", cond, {"type": "allow_parameter_values", "parameter": "blen", "expressions": [f"{cell(v)} mm" for v in r["lengths"]]})
        rule(f"opp-{k}", f"counterbore side of {where}", cond, {"type": "allow_parameter_values", "parameter": "opp", "expressions": [str(v) for v in r["opp"]]})
        rule(f"plated-{k}", f"plating of {where}", cond, {"type": "allow_parameter_values", "parameter": "plated", "expressions": [str(v) for v in r["plated"]]})
    # the hole sets: ON when the row's kind is this variant and the counterbore side (opp) is this set's; OFF otherwise (suppress-if)
    kinds = dict(rw.HOLEVARS)
    for v, k in rw.HOLEVARS:
        for side, o in (("Near", 0), ("Far", 1)):
            if v == "RoundOff" and side == "Far": continue
            for i in (1, 2, 3, 4):
                n = f"Hole{v}{side}{i}"
                conds = [pc("kind", "eq", k), pc("opp", "eq", o)] + ([pc("cp_f", "gt", "0 mm")] if (v == "Compact" and i in (2, 3)) else [])
                on = {"type": "all", "conditions": conds}
                rule(f"{n}-on", f"{n} on", on, {"type": "drive_suppression", "feature": ids[n], "value": False})
                rule(f"{n}-off", f"{n} off", {"type": "not", "condition": on}, {"type": "drive_suppression", "feature": ids[n], "value": True})
    cfg.append({"command": "config.rule", "params": {"rules": rules}})
    cfg.append({"command": "config.activate", "params": {"row": R[0]["name"]}})
    run(cfg, src=wd / "stage1.sc", save=wd / "stage2.sc", workdir=wd)
    # config.configure made a "Default" row from the current values: it is not a catalogue row, drop it (the table keeps only catalogue rows)
    (wd / "del.json").write_text(json.dumps({"commands": [{"command": "config.row", "params": {"name": "Default", "delete": True}}]}))
    r = subprocess.run([CLI, "run", str(wd / "del.json"), "--in", str(wd / "stage2.sc"), "--save", str(pkg / f"{PKG}.sc"), "--quiet"], capture_output=True, text=True)
    if r.returncode != 0:
        print("note: the Default row stays:", r.stderr[-300:], file=sys.stderr)
        shutil.copy(wd / "stage2.sc", pkg / f"{PKG}.sc")
    pkgfiles.write_tables(pkg, HERE.parent / "data"); pkgfiles.write_toml(pkg, HERE.parent / "data", R)
    shutil.rmtree(wd, ignore_errors=True)
    return ids, R

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); a = ap.parse_args()
    ids, R = build(Path(a.out)); print(f"built {PKG}.sc: {len(R)} rows, {len(ids)} named features")
