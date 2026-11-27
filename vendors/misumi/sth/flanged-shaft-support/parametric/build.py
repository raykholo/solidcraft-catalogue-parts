#!/usr/bin/env python3
"""Build the parametric MISUMI flanged shaft support package (flanged-shaft-support/): the model, tables/*.csv, generator.toml.

ONE model for all five series (standard sleeve, thickened, end mounting, flanged with slit, compact clamp collar) and their long
sleeve types. The body is the sleeve cylinder (the collar body for E-STHMR); the flange is one of three sketches (circle, cut-corner
square, filleted rectangle), each its own feature; the shaft bore is through or blind; the mounting holes are a round / square set, a
compact set of four or of two, or the collar's two; the set screws are one thread feature per size, station and screw; the clamp is a
groove, a slit and one or two screws (clearance hole, counterbore, one thread feature per size). A configuration row gives every
dimension (a cell is a number or an expression over the other parameters) and which of those features exist: one row per geometry,
(series, shape, long sleeve, D); the types of one geometry (black oxide, nickel, stainless) share a row.

    SC_CLI=<solidcraft-cli> python3 build.py [--out DIR]
"""
from __future__ import annotations
import argparse, os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime.table import read_csv, num
from runtime.parametric.build import Spec, Unit, Row, build_model
import pkgfiles

PKG = "flanged-shaft-support"
DATA = HERE.parent / "data"
CLI = os.environ.get("SC_CLI", "solidcraft-cli")
SS_SIZES = [3, 4, 5, 6, 8]                 # set screw sizes (standard and thickened): one thread feature per size, station and screw
CL_SIZES = [4, 5, 6, 8, 10]                # clamp screw sizes (slit and collar types): one thread feature per size and screw
TABLES = {"std": "dims", "thick": "thick", "xend": "xend", "slit": "slit", "slit_long": "slit_long", "mr": "mr"}

# name, default (a valid value for every feature, so that all of them can be drawn once), unit, comment
PARAMS = [("bore", "12", "mm", "shaft hole diameter D (H8)"), ("body_d", "32", "mm", "sleeve outside diameter D1 (collar: body diameter H)"),
          ("fl_d", "52", "mm", "flange diameter H (round), extent across the cut corners H (square), height H (compact)"), ("fl_t", "6", "mm", "flange thickness T"),
          ("len", "60", "mm", "overall length (L, or L1 of a long sleeve)"), ("mh_d", "4.5", "mm", "mounting hole diameter"),
          ("mh_h", "8", "mm", "mounting hole cut height (flange T + 2; the collar's holes run through the body)"),
          ("pcd", "100", "mm", "round / square flange and collar: hole circle diameter P"), ("sq_k", "40", "mm", "square flange side K"),
          ("cw", "34", "mm", "compact flange width W"), ("cp1", "35", "mm", "compact flange hole spacing P1 (Y)"), ("cf", "25", "mm", "compact flange hole spacing F (X)"),
          ("x_l1", "11", "mm", "end mounting: blind bore starts at l1"), ("x_l", "6.5", "mm", "end mounting: counterbore depth l"),
          ("x_d1", "11", "mm", "end mounting: counterbore diameter d1"), ("x_d2", "6.6", "mm", "end mounting: screw hole diameter d2"),
          ("mr_cb", "9.5", "mm", "collar: mounting hole counterbore diameter d2"),
          ("ss_z1", "12", "mm", "set screw station 1, from the flange back face (l, or l1 of a long sleeve)"), ("ss_z2", "30", "mm", "set screw station 2 (2 x l1)"),
          ("cl_b", "36", "mm", "ring length B"), ("cl_g0", "22.5", "mm", "groove start z"), ("cl_s1", "1.5", "mm", "groove width (S1; collar: S)"),
          ("cl_slit", "1.5", "mm", "slit width S (collar: 1.5 from the figure)"), ("cl_x", "11", "mm", "clamp screw height X above the shaft axis"),
          ("cl_y", "4", "mm", "counterbore floor Y from the slit centre"), ("cl_clear", "5.6", "mm", "clamp screw clearance hole"),
          ("cl_cb", "9", "mm", "clamp screw counterbore"), ("cl_z1", "51", "mm", "clamp screw 1 axis z"), ("cl_z2", "33", "mm", "clamp screw 2 axis z (slit long sleeve)")]
DERIVED = [("wall", "(body_d - bore) / 2", "mm", "sleeve wall (the set screw hole depth)"), ("cl_ro", "body_d / 2", "mm", "outer radius at the clamp"),
           ("cl_xo", "sqrt(cl_ro ^ 2 - cl_x ^ 2)", "mm", "x where the clamp axis meets the outside"), ("cl_ring0", "len - cl_b", "mm", "ring start z"),
           ("sq_t", "fl_d / 2", "mm", "square flange: corner flat distance"), ("sq_e", "sq_k / sqrt(2) - fl_d / 2", "mm", "square flange: half of a corner flat")]

def units():
    U = []
    c = lambda cmd, **kw: {"command": cmd, "params": kw}
    def one(cmds, *names, temp=False): U.append(Unit(cmds, list(names), temp))
    one([c("solid.cylinder", diameter="body_d", height="len", base=[0, 0, 0], axis="Z", operation="new", body_name="Body", name="Sleeve")], "Sleeve")
    one([c("sketch.create", plane="XY", name="Flange round sketch"), c("sketch.circle.center", center=[0, 0], diameter="fl_d"), c("sketch.finish"),
         c("solid.extrude", distance="fl_t", operation="join", name="Flange round")], "Flange round sketch", "Flange round")
    sq = [["sq_t", "-sq_e"], ["sq_t", "sq_e"], ["sq_e", "sq_t"], ["-sq_e", "sq_t"], ["-sq_t", "sq_e"], ["-sq_t", "-sq_e"], ["-sq_e", "-sq_t"], ["sq_e", "-sq_t"]]
    one([c("sketch.create", plane="XY", name="Flange square sketch"), c("sketch.line", points=sq, closed=True), c("sketch.finish"),
         c("solid.extrude", distance="fl_t", operation="join", name="Flange square")], "Flange square sketch", "Flange square")
    one([c("sketch.create", plane="XY", name="Flange compact sketch"),
         c("sketch.line", points=[["-cw / 2", "-fl_d / 2"], ["cw / 2", "-fl_d / 2"], ["cw / 2", "fl_d / 2"], ["-cw / 2", "fl_d / 2"]], closed=True),
         c("sketch.fillet", points=[f"l{i}.end" for i in range(1, 5)], radius="cw * 0.25"), c("sketch.finish"),
         c("solid.extrude", distance="fl_t", operation="join", name="Flange compact")], "Flange compact sketch", "Flange compact")
    one([c("solid.cylinder", diameter="bore", height="len + 2", base=[0, 0, -1], axis="Z", operation="cut", name="Shaft hole")], "Shaft hole")
    one([c("solid.cylinder", diameter="bore", height="len - x_l1 + 1", base=[0, 0, "x_l1"], axis="Z", operation="cut", name="Shaft hole blind")], "Shaft hole blind")
    one([c("solid.cylinder", diameter="x_d2", height="x_l1 + 2", base=[0, 0, -1], axis="Z", operation="cut", name="Mounting screw hole")], "Mounting screw hole")
    one([c("solid.cylinder", diameter="x_d1", height="x_l + 1", base=[0, 0, -1], axis="Z", operation="cut", name="Mounting screw counterbore")], "Mounting screw counterbore")
    holes = {"Round": [("pcd / 2", 0), (0, "pcd / 2"), ("-pcd / 2", 0), (0, "-pcd / 2")],
             "Compact4": [("cf / 2", "cp1 / 2"), ("-cf / 2", "cp1 / 2"), ("cf / 2", "-cp1 / 2"), ("-cf / 2", "-cp1 / 2")],
             "Compact2": [(0, "cp1 / 2"), (0, "-cp1 / 2")]}
    for kind, pts in holes.items():
        for i, (x, y) in enumerate(pts, 1):
            one([c("solid.cylinder", diameter="mh_d", height="mh_h", base=[x, y, -1], axis="Z", operation="cut", name=f"Mounting hole {kind} {i}")], f"Mounting hole {kind} {i}")
    for i, x in enumerate(("pcd / 2", "-pcd / 2"), 1):          # the collar's counterbores: diameter printed, depth drawn B (appearance)
        one([c("solid.cylinder", diameter="mr_cb", height="cl_b + 1", base=[x, 0, "len - cl_b"], axis="Z", operation="cut", name=f"Collar counterbore {i}")], f"Collar counterbore {i}")
    # set screws: 2 per station, 90 degrees apart (+X and +Y); one feature per size so the thread designation is a literal
    for m in SS_SIZES:
        for st in (1, 2):
            for j, (pos, dr) in enumerate(((["cl_ro", 0, f"ss_z{st}"], [-1, 0, 0]), ([0, "cl_ro", f"ss_z{st}"], [0, -1, 0])), 1):
                one([c("solid.hole", position=pos, direction=dr, thread=f"M{m}", depth="wall", name=f"Set screw M{m} station {st} screw {j}")],
                    f"Set screw M{m} station {st} screw {j}", temp=True)
    one([c("solid.box", length="2 * cl_ro + 2", width="cl_ro + 1 + bore / 2", height="cl_s1", corner=["-cl_ro - 1", "-bore / 2", "cl_g0"], operation="cut", name="Groove")], "Groove")
    one([c("solid.box", length="cl_slit", width="cl_ro + 1", height="cl_b + 1", corner=["-cl_slit / 2", 0, "cl_ring0"], operation="cut", name="Slit")], "Slit")
    for n in (1, 2):
        one([c("solid.cylinder", diameter="cl_clear", height="cl_xo + 1", base=["-cl_xo - 1", "cl_x", f"cl_z{n}"], axis="X", operation="cut", name=f"Clamp screw {n} clearance hole")],
            f"Clamp screw {n} clearance hole")
        one([c("solid.cylinder", diameter="cl_cb", height="cl_xo + 1 - cl_y", base=["-cl_xo - 1", "cl_x", f"cl_z{n}"], axis="X", operation="cut", name=f"Clamp screw {n} counterbore")],
            f"Clamp screw {n} counterbore")
        for m in CL_SIZES:
            one([c("solid.hole", position=["cl_xo", "cl_x", f"cl_z{n}"], direction=[-1, 0, 0], thread=f"M{m}", depth="cl_xo - cl_slit / 2", name=f"Clamp screw {n} thread M{m}")],
                f"Clamp screw {n} thread M{m}", temp=True)
    return U

def tables():
    return {k: {int(r["D"]): {c: (None if v == "" else num(v)) for c, v in r.items()} for r in read_csv(DATA / f"{f}.csv")} for k, f in TABLES.items()}

def row_key(series, family, long, D):
    return f"{series}-{family}-{'long-' if long else ''}{D}"

def geometry():
    """(series, family, long) -> the sizes D that some type of that geometry is sold in (every type of a geometry has its own not-applicable sizes)"""
    out = {}
    for t in read_csv(DATA / "types.csv"):
        na = {int(x) for x in t["not_applicable_d"].split("|") if x}
        out.setdefault((t["series"], t["family"], t["long"] == "1"), []).append(na)
    return out

def rows():
    T = tables(); out = {}
    names = [n for u in units() for n in u.names]
    for (series, family, long), nas in geometry().items():
        table = T["slit_long" if (series == "slit" and long) else series]
        for D, d in table.items():
            if long and series != "slit" and d.get("L1") is None:
                continue
            if all(D in na for na in nas):
                continue                    # no type of this geometry is sold in this size: no row
            z = dict.fromkeys([p[0] for p in PARAMS], 0)
            on = set()                      # features that exist in this row
            L = d["L1"] if long and d.get("L1") is not None else d["L"]
            z.update(bore=D, len=L)
            if series == "mr":
                z.update(body_d=d["H"], fl_d=d["H"], fl_t=d["T1"] if long else d["T"], mh_d=d["d1"], mh_h="len + 2", pcd=d["P"], mr_cb=d["d2"])
                on |= {"Sleeve", "Shaft hole", "Mounting hole Round 1", "Mounting hole Round 3", "Collar counterbore 1", "Collar counterbore 2"}
            else:
                z.update(body_d=d["D1"], fl_d=d["H"], fl_t=d["T"], mh_d=d["d"] if series in ("xend", "slit") else d["d1"], mh_h="fl_t + 2")
                on |= {"Sleeve", {"round": "Flange round", "square": "Flange square", "compact": "Flange compact"}[family]}
                on |= {{"round": "Flange round sketch", "square": "Flange square sketch", "compact": "Flange compact sketch"}[family]}
                if family in ("round", "square"):
                    z.update(pcd=d["P"]); on |= {f"Mounting hole Round {i}" for i in (1, 2, 3, 4)}
                    if family == "square": z.update(sq_k=d["K"])
                else:
                    z.update(cw=d["W"], cp1=d["P1"])
                    if d["F"] is None: on |= {"Mounting hole Compact2 1", "Mounting hole Compact2 2"}
                    else: z.update(cf=d["F"]); on |= {f"Mounting hole Compact4 {i}" for i in (1, 2, 3, 4)}
                if series == "xend":
                    z.update(x_l1=d["l1"], x_l=d["l"], x_d1=d["d1"], x_d2=d["d2"]); on |= {"Shaft hole blind", "Mounting screw hole", "Mounting screw counterbore"}
                else:
                    on.add("Shaft hole")
                if series in ("std", "thick"):
                    st = [d["l"]] if not long else ([d["l1"]] if D == 12 else [d["l1"], 2 * d["l1"]])
                    z.update(ss_z1=st[0], ss_z2="2 * ss_z1" if len(st) == 2 else 0)
                    for k in range(len(st)):
                        for j in (1, 2): on.add(f"Set screw M{d['M']:g} station {k + 1} screw {j}")
            if series in ("slit", "mr"):
                z.update(cl_b=d["B"], cl_x=d["X"], cl_y=d["Y"], cl_z1="len - cl_b / 2")
                if series == "slit":
                    z.update(cl_g0="len - cl_b - cl_s1", cl_s1=d["S1"], cl_slit=d["S"], cl_clear=d["d2"], cl_cb=d["d1"])
                    if long: z.update(cl_z1="len - cl_b / 4", cl_z2="len - 3 * cl_b / 4")
                else:
                    z.update(cl_g0=d["T1"] if long else d["T"], cl_s1=d["S"], cl_slit=1.5, cl_clear=d["d"], cl_cb=d["R"])
                on |= {"Groove", "Slit", "Clamp screw 1 clearance hole", "Clamp screw 1 counterbore", f"Clamp screw 1 thread M{d['M']:g}"}
                if series == "slit" and long:
                    on |= {"Clamp screw 2 clearance hole", "Clamp screw 2 counterbore", f"Clamp screw 2 thread M{d['M']:g}"}
            out[row_key(series, family, long, D)] = Row(z, {n for n in names if n not in on})
    return out

def spec():
    return Spec(PKG, PARAMS, DERIVED, units(), rows(), None, "Flanged shaft support", first_values=False)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); a = ap.parse_args()
    sp = spec(); pkg = Path(a.out) / PKG
    ids = build_model(sp, pkg, CLI)
    pkgfiles.write_tables(pkg, DATA); pkgfiles.write_toml(pkg, DATA, list(sp.rows))
    print(f"built {PKG}.sc with {len(ids)} named features and {len(sp.rows)} rows")
