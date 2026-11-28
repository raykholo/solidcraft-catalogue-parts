#!/usr/bin/env python3
"""Build the parametric MISUMI T-nut generator package (hnt-t-nut/): the model hnt-t-nut.sc, tables/*.csv, generator.toml.

A permanent seed owns the body name Nut. Each fixed (E, T) section joins that seed,
then has its own pilot bore and cosmetic threads, picked on that section. Configuration
rows suppress the complete alternative feature chains and the unused thread sizes. Run through solidcraft-cli:

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
    # Entirely inside every section and removed by every pilot bore. Only this feature
    # creates a body; alternative joins never compete for ownership of the name.
    add("solid.cylinder", diameter=P.PILOT[min(SIZES)], height=min(T for E, T in variants),
        base=[w, 0, 0], axis="Z", name="Nut seed", body_name="Nut")
    def features(E, T):
        suffix = vname(E, T)
        return [f"Profile {suffix}", f"Nut {suffix}", f"Pilot bore {suffix}"] + [f"Thread M{m} {suffix}" for m in SIZES]
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
        add("solid.extrude", distance=P.PLAN, name=f"Nut {vname(E, T)}", operation="join", targets=["Nut"])
    def only(key):
        existing = {c["params"].get("name") for c in cmds}
        # Remove dependants before their section, then restore the selected chain.
        for E, T in variants:
            if (E, T) != key:
                for f in reversed(features(E, T)):
                    if f in existing: add("timeline.suppress", feature=f, suppressed=True)
        for f in features(*key):
            if f in existing: add("timeline.suppress", feature=f, suppressed=f.startswith("Thread "))
    for E, T in variants:
        only((E, T))
        add("parameters.change", changes={"T": f"{g(T)} mm"})
        section(E, T)
        suffix = vname(E, T)
        add("solid.cylinder", diameter="pilot", height="T + 2 mm", base=[w, 0, -1], axis="Z", operation="cut", targets=["Nut"], name=f"Pilot bore {suffix}")
        for m in SIZES:
            r = P.PILOT[m] / 2
            add("parameters.change", changes={"pilot": f"{g(P.PILOT[m])} mm"})
            add("solid.thread", face=[w + r, 0, T / 2], designation=f"M{m}", extent="length", length="T", **{"from": [w + r, 0, T]}, name=f"Thread M{m} {suffix}")
            add("timeline.suppress", feature=f"Thread M{m} {suffix}", suppressed=True)
    only(variants[0])
    # Keep threads suppressed until a complete configuration is activated.
    for E, T in variants:
        for m in SIZES:
            add("timeline.suppress", feature=f"Thread M{m} {vname(E, T)}", suppressed=True)
    add("parameters.change", changes={"T": f"{g(variants[0][1])} mm"})
    add("browser.visibility", items=[f"Profile {vname(E, T)}" for E, T in variants], visible=False)
    res = run(cmds, save=wd / "stage1.sc")
    ids = {}
    for c, r in zip(cmds, res):
        nm = c["params"].get("name")
        if c["command"] == "sketch.create": ids[nm] = r["sketch"]
        elif isinstance(r, dict) and r.get("feature") is not None and nm and c["command"].startswith("solid."): ids[nm] = r["feature"]
    sec = [f for E, T in variants for f in features(E, T)]
    cfg = [{"command": "config.configure", "params": {"params": ["T", "pilot"], "features": sec}}]
    for name, t, m, E, T in rows_of_table():
        vals = {"param:T": g(T), "param:pilot": g(P.PILOT[m])}
        for E2, T2 in variants:
            for f in features(E2, T2):
                vals[f"suppress:{f}"] = (E2, T2) != (E, T)
            for k in SIZES:
                vals[f"suppress:Thread M{k} {vname(E2, T2)}"] = (E2, T2) != (E, T) or k != m
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
             "[[template]]", "pattern = '{type: text 3..9 [A-Za-z0-9]}[\\-{m: text 1..5 [0-9.]}]'", "",
             "# a catch-all behind it, so that the script gives the Python 'expected ...' refusal for a code that is not a code", "[[template]]",
             "pattern = '{raw: text 1..128 [A-Za-z0-9._ /-]}'", ""]
    for name, tp, m, E, T in rows_of_table():
        lines += [f'[rows."{name}"]', 'source = "MISUMI FA catalogue S9 (sources.toml), p.559"', 'page = "p.559 table"', 'status = "verified"',
                  'note = "tap drill derived (ISO coarse), edge rounds and flank measured: see the generator README, not guaranteed"', ""]
    (pkg / "generator.toml").write_text("\n".join(lines))
    shutil.rmtree(wd, ignore_errors=True)
    return ids

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); a = ap.parse_args()
    ids = build(Path(a.out)); print(f"built {PKG}.sc with {len(ids)} named features")
