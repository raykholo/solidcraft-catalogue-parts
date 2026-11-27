#!/usr/bin/env python3
"""Build the parametric MISUMI flanged shaft support with positioning (dowel) holes package (dowel-flanged-shaft-support/): the model, tables/*.csv, generator.toml.

The support is drawn ONCE: the sleeve cylinder, the round flange, the two flat cuts of the compact flange (suppressed on the round one), the
shaft bore, the four mounting holes and the two positioning holes (their positions differ by shape: one feature set per shape, the other
suppressed), and the clamp (groove, slit, clearance hole, counterbore, one thread feature per screw size). Every number is a column of the
configuration table; one row per (shape, D) of data/dims.csv.

    SC_CLI=<solidcraft-cli> python3 build.py [--out DIR]
"""
from __future__ import annotations
import argparse, os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime.table import read_csv
from runtime.parametric_build import Spec, Unit, Row, build_model
import pkgfiles

PKG = "dowel-flanged-shaft-support"
DATA = HERE.parent / "data"
CLI = os.environ.get("SC_CLI", "solidcraft-cli")
SIZES = [5, 6]                             # clamp screw sizes of the table: one thread feature each (a designation cannot be a parameter)

PARAMS = [("bore", "12", "mm", "shaft hole diameter D (H8)"), ("body_d", "32", "mm", "sleeve outside diameter D1"),
          ("fl_d", "52", "mm", "flange diameter H (round) / the circle the compact flange is cut from"), ("fl_t", "6", "mm", "flange thickness T"),
          ("len", "22", "mm", "overall length L (flange back face to sleeve end)"), ("mh_d", "4.5", "mm", "mounting hole diameter d"),
          ("pcd", "42", "mm", "round flange: hole circle diameter P (compact: dowel hole spacing)"), ("cw", "34", "mm", "compact flange width W (flat to flat)"),
          ("cp1", "35", "mm", "compact flange hole spacing P1 (Y)"), ("cf", "25", "mm", "compact flange hole spacing F (X)"),
          ("dw_d", "4", "mm", "positioning hole diameter Q (H8)"),
          ("cl_b", "10", "mm", "ring length B"), ("cl_s1", "1.5", "mm", "groove width S1"), ("cl_slit", "1.5", "mm", "slit width S"),
          ("cl_x", "11", "mm", "clamp screw height X above the shaft axis"), ("cl_y", "4", "mm", "counterbore floor Y from the slit centre"),
          ("cl_clear", "5.6", "mm", "clamp screw clearance hole d2"), ("cl_cb", "9", "mm", "clamp screw counterbore d1")]
DERIVED = [("cl_ro", "body_d / 2", "mm", "sleeve outer radius"), ("cl_xo", "sqrt(cl_ro ^ 2 - cl_x ^ 2)", "mm", "x where the clamp axis meets the sleeve"),
           ("cl_ring0", "len - cl_b", "mm", "ring start z"), ("cl_g0", "len - cl_b - cl_s1", "mm", "groove start z"),
           ("cl_z1", "len - cl_b / 2", "mm", "z of the clamp screw axis")]

def units():
    U = []
    c = lambda cmd, **kw: {"command": cmd, "params": kw}
    U.append(Unit([c("solid.cylinder", diameter="body_d", height="len", base=[0, 0, 0], axis="Z", operation="new", body_name="Body", name="Sleeve")], ["Sleeve"]))
    U.append(Unit([c("sketch.create", plane="XY", name="Flange sketch"), c("sketch.circle.center", center=[0, 0], diameter="fl_d"), c("sketch.finish"),
                   c("solid.extrude", distance="fl_t", operation="join", name="Flange")], ["Flange sketch", "Flange"]))
    # the compact flange is the round flange cut to the width W by two flat sides (appearance, approximate: read from the figure)
    U.append(Unit([c("solid.box", length="fl_d / 2 + 1 - cw / 2", width="fl_d + 2", height="fl_t + 2", corner=["cw / 2", "-fl_d / 2 - 1", -1], operation="cut", name="Flange flat side +X")],
                  ["Flange flat side +X"]))
    U.append(Unit([c("solid.box", length="fl_d / 2 + 1 - cw / 2", width="fl_d + 2", height="fl_t + 2", corner=["-fl_d / 2 - 1", "-fl_d / 2 - 1", -1], operation="cut", name="Flange flat side -X")],
                  ["Flange flat side -X"]))
    U.append(Unit([c("solid.cylinder", diameter="bore", height="len + 2", base=[0, 0, -1], axis="Z", operation="cut", name="Shaft hole")], ["Shaft hole"]))
    holes = {"Round": [("pcd / 2", 0), (0, "pcd / 2"), ("-pcd / 2", 0), (0, "-pcd / 2")],
             "Compact": [("cf / 2", "cp1 / 2"), ("-cf / 2", "cp1 / 2"), ("cf / 2", "-cp1 / 2"), ("-cf / 2", "-cp1 / 2")]}
    for kind, pts in holes.items():
        for i, (x, y) in enumerate(pts, 1):
            U.append(Unit([c("solid.cylinder", diameter="mh_d", height="fl_t + 2", base=[x, y, -1], axis="Z", operation="cut", name=f"Mounting hole {kind} {i}")],
                          [f"Mounting hole {kind} {i}"]))
    dowels = {"Round": [("pcd / 2 / sqrt(2)", "pcd / 2 / sqrt(2)"), ("-pcd / 2 / sqrt(2)", "-pcd / 2 / sqrt(2)")], "Compact": [(0, "pcd / 2"), (0, "-pcd / 2")]}
    for kind, pts in dowels.items():
        for i, (x, y) in enumerate(pts, 1):
            U.append(Unit([c("solid.cylinder", diameter="dw_d", height="fl_t + 2", base=[x, y, -1], axis="Z", operation="cut", name=f"Positioning hole {kind} {i}")],
                          [f"Positioning hole {kind} {i}"]))
    U.append(Unit([c("solid.box", length="2 * cl_ro + 2", width="cl_ro + 1 + bore / 2", height="cl_s1", corner=["-cl_ro - 1", "-bore / 2", "cl_g0"], operation="cut", name="Groove")], ["Groove"]))
    U.append(Unit([c("solid.box", length="cl_slit", width="cl_ro + 1", height="cl_b + 1", corner=["-cl_slit / 2", 0, "cl_ring0"], operation="cut", name="Slit")], ["Slit"]))
    U.append(Unit([c("solid.cylinder", diameter="cl_clear", height="cl_xo + 1", base=["-cl_xo - 1", "cl_x", "cl_z1"], axis="X", operation="cut", name="Clamp screw clearance hole")],
                  ["Clamp screw clearance hole"]))
    U.append(Unit([c("solid.cylinder", diameter="cl_cb", height="cl_xo + 1 - cl_y", base=["-cl_xo - 1", "cl_x", "cl_z1"], axis="X", operation="cut", name="Clamp screw counterbore")],
                  ["Clamp screw counterbore"]))
    for m in SIZES:
        U.append(Unit([c("solid.hole", position=["cl_xo", "cl_x", "cl_z1"], direction=[-1, 0, 0], thread=f"M{m}", depth="cl_xo - cl_slit / 2", name=f"Clamp screw thread M{m}")],
                      [f"Clamp screw thread M{m}"], temp=True))
    return U

def rows():
    out = {}
    names = [n for u in units() for n in u.names]
    for family in ("round", "compact"):
        other = "compact" if family == "round" else "round"
        for d in read_csv(DATA / "dims.csv"):
            f = lambda k: d[k]
            cells = dict(bore=f("D"), body_d=f("D1"), fl_d=f("H"), fl_t=f("T"), len=f("L"), mh_d=f("d"), pcd=f("P"), cw=f("W"), cp1=f("P1"), cf=f("F"), dw_d=f("Q"),
                         cl_b=f("B"), cl_s1=f("S1"), cl_slit=f("S"), cl_x=f("X"), cl_y=f("Y"), cl_clear=f("d2"), cl_cb=f("d1"))
            sup = {n for n in names if n.lower().startswith(("mounting hole " + other, "positioning hole " + other))}
            if family == "round":
                sup |= {"Flange flat side +X", "Flange flat side -X"}
            sup |= {f"Clamp screw thread M{m}" for m in SIZES if str(m) != d["M"]}
            out[f"{family}-{d['D']}"] = Row(cells, sup)
    return out

def spec():
    return Spec(PKG, PARAMS, DERIVED, units(), rows(), None, "Flanged shaft support with positioning holes")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); a = ap.parse_args()
    sp = spec(); pkg = Path(a.out) / PKG
    ids = build_model(sp, pkg, CLI)
    pkgfiles.write_tables(pkg, DATA); pkgfiles.write_toml(pkg, DATA, list(sp.rows))
    print(f"built {PKG}.sc with {len(ids)} named features")
