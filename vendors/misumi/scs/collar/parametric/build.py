#!/usr/bin/env python3
"""Build the parametric MISUMI shaft-collar generator package (scs-collar/): the model scs-collar.sc, tables/*.csv and generator.toml.

One model for the four bodies (aluminium ring: slit, split, 2 through or 2 counterbored fixing holes; bearing-mount collar with a boss; collar with
a urethane damper disc: slit, compact slit, compact split), drawn ONCE and driven by user parameters. The 102 catalogue rows ((type, D, B) of
data/sizes.csv, D of data/bearing.csv, (family, D) of data/urethane.csv) are configuration rows; the topology is a set of suppression columns of the
rows and the same features are driven by `drive_suppression` rules on unitless parameters (kind, split, fix, msize). A thread designation cannot come
from a parameter, so there is one tapped-hole feature per thread size. The split types cut the ring into two bodies (named `Collar (1)` / `Collar (2)`
by the kernel), and the tapped half of a split urethane collar is `Collar (1)`, as in the Python builder. Run through solidcraft-cli:

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

PKG = "scs-collar"
DATA = HERE.parent / "data"
CLI = os.environ.get("SC_CLI", "solidcraft-cli")
STEEL, DAMPER = "Collar", "Urethane damper"
P = {r["name"]: float(r["value"]) for r in read_csv(DATA / "params.csv")}
SLIT_W, SPLIT_GAP = P["slit_width"], P["split_gap"]
KIND = {"ring": 0, "bearing": 1, "urethane": 2}

# user parameters: (name, default expression, unit, comment); the defaults are the counterbored D30 x 15 ring
PARAMS = [("od", "55", "mm", "outer diameter D1"), ("bore", "30", "mm", "bore D"), ("z0", "0", "mm", "z of the steel part's first face (the urethane damper takes z 0 to t)"),
          ("ring_h", "15", "mm", "ring width: B (ring), b (bearing mount), B1 (urethane)"), ("ht", "15", "mm", "total width of the steel part (B, or B1)"),
          ("boss_dia", "60", "mm", "bearing mount boss diameter Ds"), ("boss_h", "1", "mm", "boss height B - b"),
          ("cut_w", "1", "mm", "slit width, or the gap between the two halves of a split type"),
          ("p_fix", "40", "mm", "fixing hole pitch P"), ("s_fix", "9", "mm", "through hole diameter S (2 through fixing holes)"),
          ("d1f", "9", "mm", "through diameter d1 (counterbored)"), ("d2f", "15", "mm", "counterbore diameter d2"), ("tcb", "8.5", "mm", "counterbore depth t"),
          ("ud", "7", "mm", "urethane types: screw clearance hole d"), ("ur", "6", "mm", "head seat radius R"), ("ux", "20", "mm", "screw offset X from the axis"),
          ("uy", "10", "mm", "head seat floor Y"), ("ure_t", "5", "mm", "urethane damper thickness t"),
          ("kind", "0", "", "0 aluminium ring, 1 bearing inner mount, 2 collar with urethane"), ("split", "0", "", "1 = split type (two halves)"),
          ("fix", "2", "", "fixing holes: 0 none, 1 two through, 2 two counterbored"), ("msize", "6", "", "clamp screw thread size M"),
          ("part_type", "C-SCSGAW", "text", "catalogue type (material and finish only)")]
DERIVED = [("yh1", "-(bore + od) / 4", "mm", "clamp screw axis on the mid-wall radius (ring and bearing mount)"), ("yh2", "(bore + od) / 4", "mm", "second clamp screw (split ring)"),
           ("xh", "(od / 2) * sqrt(1 - ((bore + od) / (2 * od)) * ((bore + od) / (2 * od)))", "mm", "x where that axis meets the outer cylinder"),
           ("zc", "z0 + ring_h / 2", "mm", "z of the clamp screw axes (mid width of the ring part)")]
COLUMNS = [n for n, *_ in PARAMS]
RT = [3, 4, 5, 6]                                   # ring / bearing clamp thread sizes
UA = [3, 4, 5, 6, 8, 10]                            # urethane slit types: tapped half, thread sizes
US = [4, 6]                                         # urethane split type
F_RING = ["Collar", "Boss", "Bore", "Slit"] + [f"RThr_M{m}" for m in RT] + ["FixThru1", "FixThru2", "FixCb1", "FixCb2"] + [f"RThrS_M{m}_{k}" for m in RT for k in (1, 2)]
F_URE = ["Damper", "DamperBore", "UClearA", "UBoxA", "UCylA"] + [f"UThrA_M{m}" for m in UA] + ["UClearB", "UBoxB", "UCylB"] + \
        [f"UThrAs_M{m}" for m in US] + [f"UThrBs_M{m}" for m in US]
FEATS = F_RING + F_URE

from runtime.parametric.process import run_build

def run(cmds, src=None, save=None, workdir=None):
    return run_build(cmds, src, save, workdir, detailed=False, executable=CLI)

def cell(v):
    return f"{v:g}" if isinstance(v, float) else str(v)

INERT = dict(boss_dia=60, boss_h=1, p_fix=40, s_fix=9, d1f=9, d2f=15, tcb=8.5, ud=7, ur=6, ux=20, uy=10, ure_t=5)   # unused-feature values: positive, in range

def rows_of():
    """[(key, values dict)] for every catalogue row."""
    out = []
    mnum = lambda m: int(m[1:])
    for r in read_csv(DATA / "sizes.csv"):
        t, D, B = r["type"], int(r["D"]), int(r["B"])
        v = dict(INERT, od=r["D1"], bore=D, z0=0, ring_h=B, ht=B, cut_w=SPLIT_GAP if t == "C-SCNPAW" else SLIT_W, kind=0, split=int(t == "C-SCNPAW"),
                 fix={"C-SCSMAW": 1, "C-SCSGAW": 2}.get(t, 0), msize=mnum(r["M"]), part_type=t)
        if r["P"]:
            v.update(p_fix=r["P"])
            v.update(s_fix=r["S"]) if t == "C-SCSMAW" else v.update(d1f=r["d1"], d2f=r["d2"], tcb=r["t"])
        out.append((f"{t}-{D}-{B}", v))
    for r in read_csv(DATA / "bearing.csv"):
        D = int(r["D"]); b, B = float(r["b"]), float(r["B"])
        out.append((f"C-SCSBNAW-{D}", dict(INERT, od=r["D1"], bore=D, z0=0, ring_h=r["b"], ht=r["B"], boss_dia=r["Ds"], boss_h=B - b, cut_w=SLIT_W, kind=1, split=0,
                                           fix=0, msize=mnum(r["M"]), part_type="C-SCSBNAW")))
    for r in read_csv(DATA / "urethane.csv"):
        fam, D = r["family"], int(r["D"])
        out.append((f"{fam}-{D}", dict(INERT, od=r["D1"], bore=D, z0=r["t"], ring_h=r["B1"], ht=r["B1"], cut_w=r["W"], ud=r["d"], ur=r["R"], ux=r["X"], uy=r["Y"], ure_t=r["t"],
                                       kind=2, split=int(fam == "split-compact"), fix=0, msize=mnum(r["M"]),
                                       part_type={"slit": "E-SCD", "slit-compact": "E-SCDJ", "split-compact": "E-SCSPD"}[fam])))
    return out

def alive(v):
    kind, split, fix, m = int(v["kind"]), int(v["split"]), int(v["fix"]), int(v["msize"])
    on = {"Collar", "Bore", "Slit"}
    if kind == 1: on.add("Boss")
    if kind != 2 and not split: on.add(f"RThr_M{m}")
    if kind == 0 and split: on |= {f"RThrS_M{m}_1", f"RThrS_M{m}_2"}
    if fix == 1: on |= {"FixThru1", "FixThru2"}
    if fix == 2: on |= {"FixCb1", "FixCb2"}
    if kind == 2:
        on |= {"Damper", "DamperBore", "UClearA", "UBoxA", "UCylA"}
        if split: on |= {"UClearB", "UBoxB", "UCylB", f"UThrAs_M{m}", f"UThrBs_M{m}"}
        else: on.add(f"UThrA_M{m}")
    return on

def build(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    pkg = out / PKG; (pkg / "tables").mkdir(parents=True, exist_ok=True)
    wd = Path(tempfile.mkdtemp())
    rows = rows_of()
    sizes = {(r["type"], int(r["D"]), int(r["B"])): r for r in read_csv(DATA / "sizes.csv")}
    ure = {(r["family"], int(r["D"])): r for r in read_csv(DATA / "urethane.csv")}
    cmds = []
    def add(c, **kw): cmds.append({"command": c, "params": kw})
    # the default state of the model: the counterbored D30 x 15 ring (values of the catalogue row)
    g30 = sizes[("C-SCSGAW", 30, 15)]; m30 = sizes[("C-SCSMAW", 30, 15)]
    dflt = {"od": g30["D1"], "bore": 30, "ring_h": 15, "ht": 15, "p_fix": g30["P"], "s_fix": m30["S"], "d1f": g30["d1"], "d2f": g30["d2"], "tcb": g30["t"]}
    for n, e, u, c in PARAMS:
        add("parameters.add", name=n, expression=str(dflt.get(n, e)), unit=u, comment=c)
    for n, e, u, c in DERIVED:
        add("parameters.add", name=n, expression=e, unit=u, comment=c)
    add("component.create", name="MISUMI shaft collar")
    def cyl(name, dia, height, base, op="cut", targets=None, body=None):
        kw = dict(diameter=dia, height=height, base=base, axis="Z", operation=op, name=name)
        if targets: kw["targets"] = targets
        if body: kw["body_name"] = body
        add("solid.cylinder", **kw)
    def hole(name, **kw):
        add("solid.hole", name=name, targets=[STEEL], **kw)
    def only_suppressed(name):
        add("timeline.suppress", feature=name, suppressed=True)
    # ---- ring state: ring cylinder (and the bearing boss, drawn and switched off), bore, slit / gap, clamp screw holes, fixing holes ------------
    cyl("Collar", "od", "ring_h", [0, 0, "z0"], op="new", body=STEEL)
    cyl("Boss", "boss_dia", "boss_h", [0, 0, "ring_h"], op="join", targets=[STEEL]); only_suppressed("Boss")
    cyl("Bore", "bore", "ht + 2 mm", [0, 0, "z0 - 1 mm"], targets=[STEEL])
    add("solid.box", length="cut_w", width="(1 + split) * (od / 2 + 1 mm)", height="ht + 2 mm", corner=["-cut_w / 2", "-od / 2 - 1 mm", "z0 - 1 mm"],
        operation="cut", targets=[STEEL], name="Slit")
    for m in RT:
        hole(f"RThr_M{m}", position=["xh", "yh1", "zc"], direction=[-1, 0, 0], thread=f"M{m}"); only_suppressed(f"RThr_M{m}")
    for k, sx in ((1, ""), (2, "-")):
        hole(f"FixThru{k}", position=[f"{sx}p_fix / 2", 0, "ht"], diameter="s_fix"); only_suppressed(f"FixThru{k}")
    for k, sx in ((1, ""), (2, "-")):
        hole(f"FixCb{k}", position=[f"{sx}p_fix / 2", 0, "ht"], diameter="d1f", type="counterbore", cb_diameter="d2f", cb_depth="tcb"); only_suppressed(f"FixCb{k}")
    # the split ring: its outer face is cut in two by the gap, and a hole picks the face it sits on, so the two clamp screws of the split type are their own
    # features, drawn in the split state (a hole drawn on the slit ring does not survive the switch to the gap: "the reference no longer exists as it was picked")
    add("parameters.change", changes={"split": "1", "cut_w": cell(SPLIT_GAP)})
    for m in RT:
        for k, y in ((1, "yh1"), (2, "yh2")):
            hole(f"RThrS_M{m}_{k}", position=["xh", y, "zc"], direction=[-1, 0, 0], thread=f"M{m}"); only_suppressed(f"RThrS_M{m}_{k}")
    # ---- urethane state: the standard D30 collar, then its split form ---------------------------------------------------------
    u30 = ure[("slit", 30)]
    def state(u, split):
        return {"od": u["D1"], "bore": u["D"], "z0": u["t"], "ring_h": u["B1"], "ht": u["B1"], "cut_w": u["W"], "ud": u["d"], "ur": u["R"], "ux": u["X"], "uy": u["Y"],
                "ure_t": u["t"], "kind": 2, "split": split, "fix": 0}
    add("parameters.change", changes={k: cell(float(x)) if not isinstance(x, str) else x for k, x in state(u30, 0).items()})
    cyl("Damper", "od", "ure_t", [0, 0, 0], op="new", body=DAMPER)
    cyl("DamperBore", "bore", "ure_t + 2 mm", [0, 0, -1], targets=[DAMPER])
    def seat(k, ya, lo):
        add("solid.cylinder", diameter="ud", height="uy + 1 mm", base=[0, ya, "zc"], axis="X", operation="cut", targets=[STEEL], name=f"UClear{k}")
        add("solid.box", length="od / 2 + 1 mm - uy", width="od / 2 + 1 mm - ux", height="2 * ur", corner=["uy", lo, "zc - ur"], operation="cut", targets=[STEEL], name=f"UBox{k}")
        add("solid.cylinder", diameter="2 * ur", height="od / 2 + 1 mm - uy", base=["uy", ya, "zc"], axis="X", operation="cut", targets=[STEEL], name=f"UCyl{k}")
    seat("A", "-ux", "-od / 2 - 1 mm")
    for m in UA:
        hole(f"UThrA_M{m}", position=["-cut_w / 2", "-ux", "zc"], direction=[-1, 0, 0], thread=f"M{m}"); only_suppressed(f"UThrA_M{m}")
    add("parameters.change", changes={"split": "1"})
    seat("B", "ux", "ux")
    for m in US:
        for tag, ya in (("As", "-ux"), ("Bs", "ux")):
            add("solid.hole", name=f"UThr{tag}_M{m}", targets=[f"{STEEL} (1)"], position=["-cut_w / 2", ya, "zc"], direction=[-1, 0, 0], thread=f"M{m}")
            only_suppressed(f"UThr{tag}_M{m}")
    res = run(cmds, save=wd / "stage1.sc", workdir=wd)
    ids = {}
    for c, r in zip(cmds, res):
        nm = c["params"].get("name")
        if isinstance(r, dict) and r.get("feature") is not None and nm and c["command"].startswith("solid."): ids[nm] = r["feature"]
    missing = [f for f in FEATS if f not in ids]
    if missing: sys.exit(f"no feature id in the replies for {missing}")
    # ---- configuration table --------------------------------------------------------------------------------------------------
    cfg = [{"command": "config.configure", "params": {"params": COLUMNS, "features": FEATS}}]
    for key, v in rows:
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
    def sup(f, cond):
        rule(f"{f}-on", f"{f} on", cond, {"type": "drive_suppression", "feature": ids[f], "value": False})
        rule(f"{f}-off", f"{f} off", {"type": "not", "condition": cond}, {"type": "drive_suppression", "feature": ids[f], "value": True})
    sup("Boss", pc("kind", "eq", 1))
    for m in RT:
        sup(f"RThr_M{m}", allof(pc("kind", "ne", 2), pc("split", "eq", 0), pc("msize", "eq", m)))
        for k in (1, 2): sup(f"RThrS_M{m}_{k}", allof(pc("kind", "eq", 0), pc("split", "eq", 1), pc("msize", "eq", m)))
    for f in ("FixThru1", "FixThru2"): sup(f, pc("fix", "eq", 1))
    for f in ("FixCb1", "FixCb2"): sup(f, pc("fix", "eq", 2))
    for f in ("Damper", "DamperBore", "UClearA", "UBoxA", "UCylA"): sup(f, pc("kind", "eq", 2))
    for f in ("UClearB", "UBoxB", "UCylB"): sup(f, allof(pc("kind", "eq", 2), pc("split", "eq", 1)))
    for m in UA: sup(f"UThrA_M{m}", allof(pc("kind", "eq", 2), pc("split", "eq", 0), pc("msize", "eq", m)))
    for m in US:
        for tag in ("As", "Bs"): sup(f"UThr{tag}_M{m}", allof(pc("kind", "eq", 2), pc("split", "eq", 1), pc("msize", "eq", m)))
    always = {"type": "always"}
    rule("kind-range", "kind 0 to 2", always, {"type": "parameter_range", "parameter": "kind", "minimum": "0", "maximum": "2"})
    rule("split-range", "split 0 or 1", always, {"type": "parameter_range", "parameter": "split", "minimum": "0", "maximum": "1"})
    rule("fix-range", "fixing holes 0 to 2", always, {"type": "parameter_range", "parameter": "fix", "minimum": "0", "maximum": "2"})
    cfg.append({"command": "config.rule", "params": {"rules": rules}})
    cfg.append({"command": "config.activate", "params": {"row": rows[0][0]}})
    run(cfg, src=wd / "stage1.sc", save=pkg / f"{PKG}.sc", workdir=wd)
    pkgfiles.write_tables(pkg, DATA); pkgfiles.write_toml(pkg, DATA)
    shutil.rmtree(wd, ignore_errors=True)
    return ids

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); a = ap.parse_args()
    ids = build(Path(a.out)); print(f"built {PKG}.sc with {len(ids)} named features")
