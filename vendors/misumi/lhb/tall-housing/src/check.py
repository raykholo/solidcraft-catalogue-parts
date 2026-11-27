"""Spec check for the MISUMI tall block linear bushing housing units: measures the built part with SolidCraft's inspect commands and
compares every catalogue dimension (housing.py, sources.toml S14). Appearance features (which side carries which hole, the x offset of the
M1 holes, dowel hole positions) are not dimension-checked beyond what the tables print."""
from __future__ import annotations
from runtime.check import Rows, run_measure, find_key
from runtime.sc import slug

def _cyl(faces, radius, axis_idx):
    out = []
    for f in faces:
        c = f.get("cylinder")
        if c and abs(c["radius"] - radius) < 5e-4 and abs(abs(c["axis"][axis_idx]) - 1) < 1e-6:
            out.append(c["origin"])
    return out

def _planes(faces, axis_idx):
    return [f["centroid"] for f in faces if f.get("plane_normal") and abs(abs(f["plane_normal"][axis_idx]) - 1) < 1e-6]

def _near(vals, want, tol=0.01):
    return any(abs(v - want) < tol for v in vals)

def check(s, sc, out):
    d = s.d
    H, W, L = d["H"], d["W"], s.L
    cmds = [{"command": "inspect.measure", "params": {}},
            {"command": "model.faces", "params": {"body": s.code}},
            {"command": "model.threads", "params": {}},
            {"command": "component.metadata", "params": {"component": s.code}},
            {"command": "document.metadata", "params": {}}]
    r = run_measure(sc, cmds, out, slug(s.code))
    m = r[0]; body = m["bodies"][0]; bb = body["bbox"]
    faces = r[1]["faces"] if isinstance(r[1], dict) else r[1][0]["faces"]
    th = r[2]["threads"]
    pg = {"single": "p.488", "double": "p.489"}.get(s.series, "p.490")
    R = Rows()
    R.eq("one closed body", 1, m["body_count"] if body["closed"] else 0, "S14")
    R.num("overall length L (bbox Y)", L, bb["max"][1] - bb["min"][1], 0.005, f"S14 {pg} L")
    R.num("width W (bbox X)", W, bb["max"][0] - bb["min"][0], 0.005, f"S14 {pg} W")
    R.num("height H (bbox Z)", H, bb["max"][2] - bb["min"][2], 0.005, f"S14 {pg} H")
    bore = _cyl(faces, s.dr / 2, 1)
    R.true(f"shaft bore dr {s.dr} (axis along Y)", bool(bore), f"S14 {pg} dr", "nominal, tolerance echoed in the description")
    R.true(f"bore axis h = {d['h']:g} above the base", bool(bore) and all(abs(o[2] - d["h"]) < 0.005 and abs(o[0]) < 0.005 for o in bore),
           f"S14 {pg} h", "h +-0.05")
    # 2-M1: vertical (axis Z), depth = effective length, L1 apart, starting at the top face
    m1 = [t for t in th if abs(abs(t["axis"][2]) - 1) < 1e-6]
    R.eq(f"2 vertical threads {d['M1']} (M1)", 2, len([t for t in m1 if t["designation"] == d["M1"]]), f"S14 {pg} 2-M1")
    R.true(f"M1 holes L1 = {d['L1']:g} apart",
           len(m1) == 2 and abs(abs(m1[0]["axis_point"][1] - m1[1]["axis_point"][1]) - d["L1"]) < 0.01, f"S14 {pg} L1", "x offset is appearance")
    R.true(f"M1 effective length {d['M1_eff']:g} from the top face",
           bool(m1) and all(abs(abs(t["end"] - t["start"]) - d["M1_eff"]) < 0.01 and abs(t["axis_point"][2] + t["end"] - H) < 0.01 for t in m1),
           f"S14 {pg} M1 (effective length)")
    # 2-M2 (3-M2 long): horizontal (axis X), effective length, L2 apart, at l below the top face, from the +X face
    m2 = [t for t in th if abs(abs(t["axis"][0]) - 1) < 1e-6]
    n2 = 3 if s.series == "long" else 2
    R.eq(f"{n2} horizontal threads {d['M2']} (M2)", n2, len([t for t in m2 if t["designation"] == d["M2"]]),
         f"S14 {pg} {n2}-M2", "3-M2 on the long type" if n2 == 3 else "")
    ys = sorted(t["axis_point"][1] for t in m2)
    R.true(f"M2 holes L2 = {d['L2']:g} apart", len(ys) == n2 and abs((ys[-1] - ys[0]) - d["L2"]) < 0.01 and all(abs(y) < d["L2"] / 2 + 0.01 for y in ys),
           f"S14 {pg} L2", "middle hole of the long type at mid-length is appearance")
    R.true(f"M2 effective length {d['M2_eff']:g}, l = {d['l']:g} below the top face",
           bool(m2) and all(abs(abs(t["end"] - t["start"]) - d["M2_eff"]) < 0.01 and abs(t["axis_point"][2] - (H - d["l"])) < 0.01 for t in m2),
           f"S14 {pg} M2, l", "drawn from the +X face (appearance)")
    # counterbores d1 x t
    cb = [o for o in _cyl(faces, d["d1"] / 2, 0)]
    R.true(f"{len(ys)} counterbores d1 = {d['d1']:g}", len(cb) >= n2, f"S14 {pg} d1 x t", "side and coaxial placement are appearance")
    xs = [c[0] for c in _planes(faces, 0)]
    R.true(f"counterbore depth t = {d['t']:g}", _near(xs, -W / 2 + d["t"]), f"S14 {pg} d1 x t")
    # dowel holes
    if s.dowel:
        dw = s.dw
        pos = s.dowel_positions
        got = [o for o in _cyl(faces, dw["P"] / 2, 2) if any(abs(o[0] - x) < 0.01 and abs(o[1] - y) < 0.01 for x, y in pos)]
        R.eq(f"2 dowel holes P {dw['P']:g}", 2, len(got), f"S14 {pg} dowel table", "positions are appearance")
        zs = [c[2] for c in _planes(faces, 2)]
        R.true(f"dowel hole depth l2 = {dw['l2']:g}", _near(zs, H - dw["l2"]), f"S14 {pg} dowel table")
        R.true(f"dowel holes E = {dw['E']:g} apart along L", len(got) == 2 and abs(abs(got[0][1] - got[1][1]) - dw["E"]) < 0.01, f"S14 {pg} dowel table E")
        if s.series == "single":
            R.true(f"dowel holes F = {dw['F']:g} apart across W", len(got) == 2 and abs(abs(got[0][0] - got[1][0]) - dw["F"]) < 0.01, f"S14 {pg} dowel table F")
    R.true("tolerances written in the part description", f"{s.dr_tol[0]:+.3f}/{s.dr_tol[1]:+.3f}" in s.description, f"S14 {pg}", "echoed, not drawn")
    R.eq("part number metadata", s.code, (r[3].get("metadata") or r[3]).get("part_number"), "-")
    R.eq("design part number", s.code, find_key(r[4], "part_number"), "-")
    return R
