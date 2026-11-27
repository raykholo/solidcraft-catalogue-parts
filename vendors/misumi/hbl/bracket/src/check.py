"""Spec check for MISUMI 5 series brackets (bracket.py, sources.toml S40)."""
from __future__ import annotations
from runtime.check import Rows, run_measure, uniq, find_key
from runtime.sc import slug
from . import bracket as br

def _holes(faces, axis_idx, d, pos_idx):
    """Centre positions (along pos_idx) of the cylinders of diameter d whose axis is the coordinate axis axis_idx."""
    out = []
    for f in faces:
        c = f.get("cylinder")
        if c and abs(c["radius"] * 2 - d) < 1e-3 and abs(abs(c["axis"][axis_idx]) - 1) < 1e-6:
            out.append(c["origin"][pos_idx])
    return [round(x, 3) for x in uniq(out)]

def check(b, sc, out):
    cmds = [{"command": "inspect.measure", "params": {}},
            {"command": "model.faces", "params": {"body": b.code}},
            {"command": "component.metadata", "params": {"component": b.code}},
            {"command": "document.metadata", "params": {}}]
    r = run_measure(sc, cmds, out, slug(b.code))
    m = r[0]; body = m["bodies"][0]; bb = body["bbox"]
    faces = r[1]["faces"] if isinstance(r[1], dict) else r[1][0]["faces"]
    R = Rows()
    R.eq("one closed body", 1, m["body_count"] if body["closed"] else 0, "S40")
    R.num("width", b.W, bb["max"][0] - bb["min"][0], 0.005, "S40 p.539/540 '14' / '19'")
    R.num("foot length", b.foot, bb["max"][1] - bb["min"][1] - b.tab_h, 0.005, "S40 p.539/540 foot length", "from the wall outer face (the tab is 1 proud of it)" if b.tab_h else "")
    R.num("wall height", b.wall, bb["max"][2] - bb["min"][2] - b.tab_h, 0.005, "S40 p.539/540 wall height", "from the foot outer face (the tab is 1 proud of it)" if b.tab_h else "")
    zs = [f["centroid"][2] for f in faces if f.get("plane_normal") and abs(f["plane_normal"][2] - 1) < 1e-6]
    R.true(f"foot thickness {b.foot_t:g} (foot top face at z = {b.foot_t:g})", any(abs(z - b.foot_t) < 0.005 for z in zs), "S40 p.539/540 '5', '9'")
    ys = [f["centroid"][1] for f in faces if f.get("plane_normal") and abs(f["plane_normal"][1] - 1) < 1e-6]
    if b.wall_t_approx:
        R.true("wall thickness not dimensioned: not checked (appearance, approximate)", True, "-", "equal to the foot")
    else:
        R.true(f"wall thickness {b.wall_t:g} (wall inner face at y = {b.wall_t:g})", any(abs(y - b.wall_t) < 0.005 for y in ys), "S40 p.539/540 '5'")
    if b.tab_w:
        xs = [f["centroid"][0] for f in faces if f.get("plane_normal") and abs(abs(f["plane_normal"][0]) - 1) < 1e-6]
        R.true(f"tab {b.tab_w:g} wide on the centre line (side faces at x = W/2 -+ {b.tab_w / 2:g})",
               any(abs(x - (b.W / 2 - b.tab_w / 2)) < 0.005 for x in xs) and any(abs(x - (b.W / 2 + b.tab_w / 2)) < 0.005 for x in xs),
               "S40 p.539 '6'")
        R.true(f"tabs {b.tab_h:g} proud of the outer faces (faces at z = -{b.tab_h:g} and y = -{b.tab_h:g})",
               any(abs(f["centroid"][2] + b.tab_h) < 0.005 for f in faces if f.get("plane_normal") and abs(f["plane_normal"][2] + 1) < 1e-6) and any(abs(y + b.tab_h) < 0.005 for y in
                   [f["centroid"][1] for f in faces if f.get("plane_normal") and abs(f["plane_normal"][1] + 1) < 1e-6]),
               "S40 p.539 '1'")
    R.eq("foot holes, positions from the wall outer face", [float(x) for x in b.foot_holes], _holes(faces, 2, b.hole_d, 1), "S40 p.539/540 hole positions")
    R.eq("wall holes, positions from the foot outer face", [float(x) for x in b.wall_holes], _holes(faces, 1, b.hole_d, 2), "S40 p.539/540 hole positions")
    cyl = [f["cylinder"] for f in faces if f.get("cylinder")]
    R.true("every hole has the catalogue diameter", bool(cyl) and all(abs(c["radius"] * 2 - b.hole_d) < 1e-3 for c in cyl), "S40 p.539/540 '2-O5.5' (O4.5 for -4)")
    R.true("holes on the width centre line" if b.hole_x is None else f"eccentric holes {b.hole_x:g} from one side, {b.W - b.hole_x:g} from the other",
           all(abs(c["origin"][0] - b.x_hole) < 0.01 for c in cyl), "S40 p.539/540 '7 / 7', '9.5 / 9.5', '5 / 7'")
    R.eq("part number metadata", b.code, (r[2].get("metadata") or r[2]).get("part_number"), "-")
    R.eq("design part number", b.code, find_key(r[3], "part_number"), "-")
    return R
