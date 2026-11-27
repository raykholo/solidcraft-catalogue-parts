"""Spec check for MISUMI linear bushing housing units: measures the built part with SolidCraft's inspect commands and compares every
catalogue dimension (housing.py, sources.toml S12). Appearance features (cross-section wall step and foot, dowel hole positions) are not
dimension-checked."""
from __future__ import annotations
from runtime.check import Rows, run_measure, find_key, uniq
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
    H, W = d["H"], d["W"]
    cmds = [{"command": "inspect.measure", "params": {}},
            {"command": "model.faces", "params": {"body": s.code}},
            {"command": "model.threads", "params": {}},
            {"command": "component.metadata", "params": {"component": s.code}},
            {"command": "document.metadata", "params": {}}]
    r = run_measure(sc, cmds, out, slug(s.code))
    m = r[0]; body = m["bodies"][0]; bb = body["bbox"]
    faces = r[1]["faces"] if isinstance(r[1], dict) else r[1][0]["faces"]
    th = [t for t in r[2]["threads"] if t["designation"] == d["M"]]
    R = Rows()
    pg = "p.485" if s.series in ("single", "medium") else "p.487"
    R.eq("one closed body", 1, m["body_count"] if body["closed"] else 0, "S12")
    R.num("overall length L (bbox Y)", s.L, bb["max"][1] - bb["min"][1], 0.005, f"S12 {pg} L")
    R.num("width W (bbox X)", W, bb["max"][0] - bb["min"][0], 0.005, f"S12 {pg} W")
    R.num("height H (bbox Z)", H, bb["max"][2] - bb["min"][2], 0.005, f"S12 {pg} H")
    bore = _cyl(faces, s.dr / 2, 1)
    R.true(f"shaft bore dr {s.dr} (axis along Y)", bool(bore), f"S12 {pg} dr", "nominal, tolerance echoed in the description")
    R.true(f"bore axis h = {d['h']:g} below the top face", bool(bore) and all(abs(o[2] - (H - d["h"])) < 0.005 and abs(o[0]) < 0.005 for o in bore),
           f"S12 {pg} h", f"h +-{d['h_tol']:g}")
    R.true(f"shoulder height H2 = {d['H2']:g}", any(abs(c[2] - (H - d["H2"])) < 0.005 for c in _planes(faces, 2)), f"S12 {pg} H2")
    wl = W / 2 - 1.0
    walls = [c for c in _planes(faces, 0) if abs(abs(c[0]) - wl) < 0.005]
    R.true(f"H1 = {d['H1']:g} from the top face (lower end of the body wall)",
           bool(walls) and all(abs(c[2] - (H - (d["H1"] + d["H2"]) / 2)) < 0.01 for c in walls), f"S12 {pg} H1",
           "wall step 1 mm is appearance; checked through the wall plane centre")
    # mounting holes: thread M, depth l, on W1 x L1
    pos = {(round(t["axis_point"][0], 3), round(t["axis_point"][1], 3)) for t in th}
    want = {(round(sx * d["W1"] / 2, 3), round(y, 3)) for sx in (-1, 1) for y in s.hole_ys}
    R.eq(f"{s.n_holes} mounting threads {d['M']}", s.n_holes, len(th), f"S12 {pg} 4-M" if s.n_holes == 4 else f"S12 {pg} 6-M", "6 holes on the Long type" if s.n_holes == 6 else "")
    R.true(f"threads on W1 = {d['W1']:g} and L1 = {s.L1:g}", pos == want, f"S12 {pg} W1, L1")
    for t in th[:1]:
        R.num("thread depth l", d["l"], abs(t["end"] - t["start"]), 0.01, f"S12 {pg} l")
        R.num("thread starts at the top face", H, t["axis_point"][2] + t["end"], 0.01, f"S12 {pg} l")
    pil = {(round(o[0], 3), round(o[1], 3)) for o in _cyl(faces, d["d"] / 2, 2)}
    R.true(f"pilot hole d {d['d']:g} at every mounting hole", want <= pil, f"S12 {pg} d", "drawn through the base (read from the figure)")
    # dowel holes
    if s.dowel:
        dw = [o for o in _cyl(faces, d["P"] / 2, 2) if (round(o[0], 3), round(o[1], 3)) not in want]   # not the mounting-hole bores (M6 core is also 5 mm)
        R.eq(f"2 dowel holes P {d['P']:g}", 2, len(dw), "S12 dowel hole table", "positions are appearance")
        floors = [c for c in _planes(faces, 2) if abs(c[2] - (H - d["l2"])) < 0.005]
        R.eq(f"dowel hole depth l2 = {d['l2']:g}", 2, len(floors), "S12 dowel hole table")
    else:
        R.eq("no dowel holes", 0, len([o for o in _cyl(faces, d["P"] / 2, 2) if (round(o[0], 3), round(o[1], 3)) not in want]) if d["P"] else 0, "S12", "")
    R.true("tolerances written in the part description", f"{s.dr_tol[0]:+.3f}/{s.dr_tol[1]:+.3f}" in s.description and f"+-{d['L_tol']:g}" in s.description, f"S12 {pg}",
           "echoed, not drawn")
    R.eq("part number metadata", s.code, (r[3].get("metadata") or r[3]).get("part_number"), "-")
    R.eq("design part number", s.code, find_key(r[4], "part_number"), "-")
    return R
