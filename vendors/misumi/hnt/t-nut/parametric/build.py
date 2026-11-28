#!/usr/bin/env python3
"""Build the parametric MISUMI T-nut generator package (hnt-t-nut/): the model hnt-t-nut.sc, tables/*.csv, generator.toml.

The nut is drawn ONCE: the section (10 wide plan, 5.8 neck, flank, E and T per type), the pilot bore (tap drill) and one cosmetic thread
feature per size M3 / M4 / M5 (a thread designation cannot come from a parameter). The configuration rows are the valid (type, M) pairs of
data/types.csv: each sets the parameters E, T and pilot and suppresses the thread features of the other sizes. Run through solidcraft-cli:

    SC_CLI=<solidcraft-cli> python3 build.py [--out DIR]
"""
from __future__ import annotations
import argparse, csv, importlib, shutil, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime.table import read_csv
from runtime.parametric import cli

nt = importlib.import_module("vendors.misumi.hnt.t-nut.src.nut")
PKG = "hnt-t-nut"
DATA = HERE.parent / "data"
SIZES = sorted(nt.PILOT)           # 3, 4, 5

def g(v): return f"{v:g}"

def run(cmds, src=None, save=None):
    res, err = cli(cmds, src=src, save=save)
    if err: sys.exit(f"solidcraft-cli failed: {err}")
    return res

from runtime.parametric.kit import write_csv

def rows_of_table():
    """(configuration row name, type, m, E, T) for every valid (type, M) pair."""
    out = []
    for t, (kind, mat, surf, Ms, E, T) in nt.TYPES.items():
        for m in Ms: out.append((f"{t}-{m}", t, int(m), E, T))
    return out

def build(out: Path):
    pkg = out / PKG; (pkg / "tables").mkdir(parents=True, exist_ok=True)
    wd = Path(tempfile.mkdtemp())
    P = nt
    cmds = []
    def add(c, **kw): cmds.append({"command": c, "params": kw})
    for n, e, u, c in [("T", "4.1", "mm", "total thickness T (p.559 table, per type)"), ("pilot", "4.2", "mm", "tap drill (pilot bore) of the thread size")]:
        add("parameters.add", name=n, expression=e, unit=u, comment=c)
    add("component.create", name="HNT T-nut")
    b, w, fh = P.NECK / 2, P.PLAN / 2, P.FLANK_H
    # The shoulder height E takes two values (3.3 and 3.5) and the R1.0 round is sized so that the two rounds of the flank exactly consume
    # the land: SolidCraft 0.50.0 refuses a parameter change between such sketches ("would flip the sketch over"), so each E has its own
    # section (feature set), and the rows suppress the other one (the per-row choice between alternative features).
    variants = sorted({(E, T) for _, _, _, E, T in rows_of_table()})
    vname = lambda E, T: f"E{g(E)} T{g(T)}"
    def section(E, T):
        pts = [[-b, 0], [b, 0], [w, fh], [w, E], [b, E], [b, T], [-b, T], [-b, E], [-w, E], [-w, fh]]
        ref = lambda *idx: [f"l{i % 10 or 10}.end" for i in idx]
        class N: pass
        n = N(); n.E = E
        add("sketch.create", plane="YZ", name=f"Profile {vname(E, T)}")
        add("sketch.line", points=pts, closed=True)
        add("sketch.fillet", points=ref(0, 1), radius=P.R_BOTTOM)
        add("sketch.fillet", points=ref(2, 9), radius=P.flank_top_radius(n))
        add("sketch.fillet", points=ref(3, 8, 5, 6), radius=P.R_EDGE)
        add("sketch.finish")
        add("solid.extrude", distance=P.PLAN, name=f"Nut {vname(E, T)}", body_name="Nut")
    def only(key):
        for E, T in variants:
            for f in (f"Profile {vname(E, T)}", f"Nut {vname(E, T)}"):
                if any(c["params"].get("name") == f for c in cmds): add("timeline.suppress", feature=f, suppressed=((E, T) != key))
    for i, (E, T) in enumerate(variants):
        only((E, T)); section(E, T)
    only(variants[0])
    add("parameters.change", changes={"T": f"{g(variants[0][1])} mm"})
    add("solid.cylinder", diameter="pilot", height="T + 2 mm", base=[w, 0, -1], axis="Z", operation="cut", targets=["Nut"], name="Pilot bore")
    add("browser.visibility", items=[f"Profile {vname(E, T)}" for E, T in variants], visible=False)
    for m in SIZES:                  # one thread feature per size, each created on a representative row, then suppressed
        r = P.PILOT[m] / 2
        add("parameters.change", changes={"pilot": f"{g(P.PILOT[m])} mm"})
        add("solid.thread", face=[w + r, 0, variants[0][1] / 2], designation=f"M{m}", extent="length", length="T", **{"from": [w + r, 0, variants[0][1]]}, name=f"Thread M{m}")
        add("timeline.suppress", feature=f"Thread M{m}", suppressed=True)
    res = run(cmds, save=wd / "stage1.sc")
    ids = {}
    for c, r in zip(cmds, res):
        nm = c["params"].get("name")
        if c["command"] == "sketch.create": ids[nm] = r["sketch"]
        elif isinstance(r, dict) and r.get("feature") is not None and nm and c["command"].startswith("solid."): ids[nm] = r["feature"]
    sec = [f"{pre} {vname(E, T)}" for E, T in variants for pre in ("Profile", "Nut")]
    cfg = [{"command": "config.configure", "params": {"params": ["T", "pilot"], "features": sec + [f"Thread M{m}" for m in SIZES]}}]
    for name, t, m, E, T in rows_of_table():
        vals = {"param:T": g(T), "param:pilot": g(P.PILOT[m])}
        for k in SIZES: vals[f"suppress:Thread M{k}"] = (k != m)
        for E2, T2 in variants:
            for pre in ("Profile", "Nut"): vals[f"suppress:{pre} {vname(E2, T2)}"] = (E2, T2) != (E, T)
        cfg.append({"command": "config.row", "params": {"name": name, "values": vals}})
    cfg.append({"command": "config.activate", "params": {"row": "HNTT5-5"}})
    run(cfg, src=wd / "stage1.sc", save=pkg / f"{PKG}.sc")
    # tables (the single source of every number is data/*.csv) and the manifest
    t = pkg / "tables"
    for f in ("params", "tap", "types"): shutil.copy(DATA / f"{f}.csv", t / f"{f}.csv")
    other = "|".join(sorted(P.OTHER))
    with open(t / "params.csv", "a", newline="") as f:
        csv.writer(f, lineterminator="\n").writerows([["types", "|".join(P.TYPES), "", "S9", "p.559 table", "labelled"],
                                                      ["other_types", other, "", "S9", "p.557 overview", "labelled"]])
    lines = ['format = "solidcraft-generator/2"', f'id = "{PKG}"', 'name = "MISUMI 5 series pre-assembly T-nuts (HNTT family)"', 'license = "CC0-1.0"',
             f'model = "{PKG}.sc"', "", "[parameters]", 'type = { type = "text", default = "HNTT5" }', 'm = { type = "text", default = "5" }', "",
             "[[template]]", "pattern = '{type}[\\-{m}]'", "",
             "# a catch-all behind it, so that the script gives the Python 'expected ...' refusal for a code that is not a code", "[[template]]",
             "pattern = '{raw}'", ""]
    for name, tp, m, E, T in rows_of_table():
        lines += [f'[rows."{name}"]', 'source = "MISUMI FA catalogue S9 (sources.toml), p.559"', 'page = "p.559 table"', 'status = "verified"',
                  'note = "tap drill derived (ISO coarse), edge rounds and flank measured: see the generator README, not guaranteed"', ""]
    from runtime.parametric.manifest import write_manifest
    write_manifest((pkg / "generator.toml"), "\n".join(lines), {'type': {'type': 'text', 'min': 3, 'max': 9, 'escape': '[A-Za-z0-9]'}, 'm': {'type': 'text', 'min': 1, 'max': 5, 'escape': '[0-9.]'}, 'raw': {'type': 'text', 'min': 1, 'max': 128, 'escape': '[A-Za-z0-9._ /-]'}})
    shutil.rmtree(wd, ignore_errors=True)
    return ids

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); a = ap.parse_args()
    ids = build(Path(a.out)); print(f"built {PKG}.sc with {len(ids)} named features")
