#!/usr/bin/env python3
"""Build the parametric MISUMI oil free bushing generator package (oil-free-bushing/): the model oil-free-bushing.sc, tables/*.csv, generator.toml.

The bushing is modelled ONCE, driven by user parameters (outside diameter, bore, length, flange and hole dimensions). The 159 catalogue rows
(rows.py: one per type and table row, from data/*.csv) become configuration rows; which features exist (plain revolve or revolve with
shoulder, square or compact flange sketch, axis or compact holes) is a suppression column of those rows; the length L is the free parameter and
the row's printed lengths are its allowed values (a rule per row). Run through solidcraft-cli:

    SC_CLI=<solidcraft-cli> python3 build.py [--out DIR]
"""
from __future__ import annotations
import argparse, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
import pkgfiles, rows as rw

PKG = "oil-free-bushing"
CLI = os.environ.get("SC_CLI", "solidcraft-cli")
MM = ("od", "blen", "bore", "fl_h", "fl_t", "hole_d", "cb_d", "cb_t", "pcd", "sq_w", "cp_a", "cp_f", "cp_w")
COLUMNS = ["rowno", "od", "blen", "bore", "fl_h", "fl_t", "hole_d", "cb_d", "cb_t", "pcd", "sq_w", "cp_a", "cp_f", "cp_w"]
COMMENT = {"rowno": "number of the configuration row (the rules name it)", "od": "outside diameter D", "blen": "overall length L (free: one of the printed lengths of the row)",
           "bore": "bore at the nominal inside diameter d", "fl_h": "flange diameter H", "fl_t": "flange thickness (shouldered, thrust: t; flanged: T)",
           "hole_d": "mounting hole d1", "cb_d": "counterbore d2", "cb_t": "counterbore depth t", "pcd": "P.C.D. of the holes (round flange)",
           "sq_w": "square flange across flats W", "cp_a": "compact flange hole pitch A (along H)",
           "cp_f": "second hole pitch F (round, compact flange); 0 = two holes", "cp_w": "compact flange width across the flats (D + 6)"}
DERIVED = [("hr", "pcd / 2", "radius of the holes on the P.C.D."), ("ha", "cp_a / 2", "compact flange holes: half of A"), ("he", "cp_f / 2", "compact flange holes: half of F"),
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
    return [[0, 0], ["blen", 0], ["blen", R_], ["fl_t", R_], ["fl_t", "fl_h / 2"], [0, "fl_h / 2"]]

FLANGE_PLANE = "YZ"

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

def hole_cmd(name, y, z):
    return {"command": "solid.hole", "params": {"position": [0, y, z], "diameter": "hole_d", "type": "counterbore", "cb_diameter": "cb_d",
                                                "cb_depth": "cb_t", "depth": "fl_t", "name": name}}

AXIS = [("hr", 0), (0, "hr"), ("-hr", 0), (0, "-hr")]
COMPACT = [("he", "ha"), ("-he", "ha"), ("-he", "-ha"), ("he", "-ha")]

def build(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    pkg = out / PKG; (pkg / "tables").mkdir(parents=True, exist_ok=True)
    wd = Path(tempfile.mkdtemp())
    R, skipped = rw.make_rows()
    by = {r["name"]: r for r in R}
    cmds, created = [], []
    def add(c, **kw): cmds.append({"command": c, "params": kw})
    first = R[0]["params"]
    for n in COLUMNS:
        add("parameters.add", name=n, expression=cell(first[n]), unit="mm" if n in MM else "", comment=COMMENT[n])
    for n, e, c in DERIVED:
        add("parameters.add", name=n, expression=e, unit="mm", comment=c)
    add("component.create", name="Oil free bushing")

    def state(ref, live):
        """The reference row's values with only the `live` features switched on (everything made so far)."""
        off = [f for f in created if f not in live]
        if off: add("timeline.suppress", features=off, suppressed=True)
        add("parameters.change", changes={n: cell(by[ref]["params"][n]) for n in COLUMNS})
        on = [f for f in created if f in live]
        if on: add("timeline.suppress", features=on, suppressed=False)

    def make(cs, names):
        cmds.extend(cs); created.extend(names)
    ref = {"Plain": "C-MUBZ-5", "Flange": "C-MUFZ-5"}
    for k in rw.REVOLVES:
        state(ref[k], set())
        make(revolve_cmds(k), [f"Profile{k}", f"Revolve{k}"])
    state("C-MUTSZ-16", {"ProfilePlain", "RevolvePlain"})
    make(square_cmds(), ["SquareSketch", "SquareFlange"])
    state("C-MUTNZ-16", {"ProfilePlain", "RevolvePlain"})
    make(compact_cmds(), ["CompactSketch", "CompactFlange"])
    state("C-MUBZ-5", {"ProfilePlain", "RevolvePlain"})
    add("solid.cylinder", diameter="bore", height="blen + 2", base=[-1, 0, 0], axis="X", operation="cut", name="Bore")
    holes_at = {"Round": ("C-MUTZ-16", {"ProfileFlange", "RevolveFlange"}), "Square": ("C-MUTSZ-16", {"ProfilePlain", "RevolvePlain", "SquareSketch", "SquareFlange"}),
                "Compact": ("C-MUTNZ-16", {"ProfilePlain", "RevolvePlain", "CompactSketch", "CompactFlange"})}
    for v in rw.HOLEVARS:
        state(holes_at[v][0], holes_at[v][1])
        pos = COMPACT if v == "Compact" else AXIS
        make([hole_cmd(f"Hole{v}{i + 1}", y, z) for i, (y, z) in enumerate(pos)], [f"Hole{v}{i}" for i in (1, 2, 3, 4)])
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
        rule(f"len-{k}", f"printed L of {where}", pc("rowno", "eq", k),
             {"type": "allow_parameter_values", "parameter": "blen", "expressions": [f"{cell(v)} mm" for v in r["lengths"]]})
    for n in ("HoleRound1", "HoleRound3", "HoleCompact2", "HoleCompact3"):
        if n in ids:
            rule(f"{n}-off", f"{n} off when F is 0 (two holes)", pc("cp_f", "eq", "0 mm"), {"type": "drive_suppression", "feature": ids[n], "value": True})
        else:
            print(f"warning: no feature id for {n}: the F = 0 suppression rule is left to the row columns", file=sys.stderr)
    cfg.append({"command": "config.rule", "params": {"rules": rules}})
    cfg.append({"command": "config.activate", "params": {"row": R[0]["name"]}})
    run(cfg, src=wd / "stage1.sc", save=wd / "stage2.sc", workdir=wd)
    # config.configure made a "Default" row from the current values: it is not a catalogue row, drop it (the table keeps only catalogue rows)
    (wd / "del.json").write_text(json.dumps({"commands": [{"command": "config.row", "params": {"name": "Default", "delete": True}}]}))
    r = subprocess.run([CLI, "run", str(wd / "del.json"), "--in", str(wd / "stage2.sc"), "--save", str(pkg / f"{PKG}.sc"), "--quiet"], capture_output=True, text=True)
    if r.returncode != 0:
        print("note: the Default row stays:", r.stderr[-300:], file=sys.stderr)
        shutil.copy(wd / "stage2.sc", pkg / f"{PKG}.sc")
    pkgfiles.write_tables(pkg, HERE.parent / "data", R); pkgfiles.write_toml(pkg, R)
    shutil.rmtree(wd, ignore_errors=True)
    return ids, R

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); a = ap.parse_args()
    ids, R = build(Path(a.out)); print(f"built {PKG}.sc: {len(R)} rows, {len(ids)} named features")
