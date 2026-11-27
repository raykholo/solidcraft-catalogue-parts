"""Spec check for the MISUMI centre-hole-height-optional housing units E-LBHG / E-LBHGW: measures the built part with SolidCraft's inspect
commands and compares every catalogue dimension (housing.py, sources.toml S14). The upper corner chamfer (C1) is appearance and not checked."""
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

def check(s, sc, out):
    d = s.d
    cmds = [{"command": "inspect.measure", "params": {}},
            {"command": "model.faces", "params": {"body": s.code}},
            {"command": "component.metadata", "params": {"component": s.code}},
            {"command": "document.metadata", "params": {}}]
    r = run_measure(sc, cmds, out, slug(s.code))
    m = r[0]; body = m["bodies"][0]; bb = body["bbox"]
    faces = r[1]["faces"] if isinstance(r[1], dict) else r[1][0]["faces"]
    R = Rows()
    R.eq("one closed body", 1, m["body_count"] if body["closed"] else 0, "S14")
    R.num("flange width L (bbox X)", d["L"], bb["max"][0] - bb["min"][0], 0.005, "S14 p.491 L")
    R.num("length T (bbox Y)", s.T, bb["max"][1] - bb["min"][1], 0.005, "S14 p.491 T")
    R.num(f"total height H1 = H + {d['H1_offset']:g} (bbox Z)", s.H1, bb["max"][2] - bb["min"][2], 0.005, "S14 p.491 H1", "tolerance 0 / -0.5")
    bore = _cyl(faces, s.dr / 2, 1)
    R.true(f"shaft bore dr {s.dr} (axis along Y)", bool(bore), "S14 p.491 dr", "nominal")
    R.true(f"bore axis H = {s.H} above the base, centred at L/2",
           bool(bore) and all(abs(o[2] - s.H) < 0.005 and abs(o[0]) < 0.005 for o in bore), "S14 p.491 H, L/2", "H +-0.05, L/2 +-0.05")
    zs = [c[2] for c in _planes(faces, 2)]
    R.true(f"flange thickness S = {d['S']:g}", any(abs(z - d["S"]) < 0.005 for z in zs), "S14 p.491 S")
    xs = [c[0] for c in _planes(faces, 0)]
    R.true(f"body width W = {d['W']:g}", any(abs(x - d["W"] / 2) < 0.005 for x in xs) and any(abs(x + d["W"] / 2) < 0.005 for x in xs), "S14 p.491 W")
    holes = {(round(o[0], 3), round(o[1], 3)) for o in _cyl(faces, d["d"] / 2, 2)}
    want = {(round(x, 3), round(y, 3)) for x, y in s.hole_points}
    R.true(f"4 mounting holes d {d['d']:g} on L1 = {d['L1']:g} x T1 = {s.T1:g}", holes == want, "S14 p.491 4-d, L1, T1", "through the flange")
    R.true("tolerances written in the part description", "+-0.05" in s.description and "0/-0.5" in s.description, "S14 p.491", "echoed, not drawn")
    R.eq("part number metadata", s.code, (r[2].get("metadata") or r[2]).get("part_number"), "-")
    R.eq("design part number", s.code, find_key(r[3], "part_number"), "-")
    return R
