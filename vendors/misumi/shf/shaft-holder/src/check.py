"""Spec check for MISUMI shaft supports: measures the built part with SolidCraft's inspect commands and compares every dimension with the
catalogue value (holder.py, sources.toml S50). C-SHA's parenthesised reference values (H1, S, L, B, W) are not checked."""
from __future__ import annotations
from runtime.check import Rows, run_measure, find_key
from runtime.sc import slug

def _cyl(faces, radius, axis_idx):
    """origins of cylindrical faces of this radius whose axis is along `axis_idx`"""
    out = []
    for f in faces:
        c = f.get("cylinder")
        if c and abs(c["radius"] - radius) < 5e-4 and abs(abs(c["axis"][axis_idx]) - 1) < 1e-6:
            out.append(c["origin"])
    return out

def _planes(faces, axis_idx):
    return [f["centroid"] for f in faces if f.get("plane_normal") and abs(abs(f["plane_normal"][axis_idx]) - 1) < 1e-6]

def _has(vals, target, tol=0.005):
    return any(abs(v - target) < tol for v in vals)

def check(s, sc, out):
    d = s.dims
    cmds = [{"command": "inspect.measure", "params": {}},
            {"command": "model.faces", "params": {"body": s.code}},
            {"command": "model.threads", "params": {}},
            {"command": "component.metadata", "params": {"component": s.code}},
            {"command": "document.metadata", "params": {}}]
    r = run_measure(sc, cmds, out, slug(s.code))
    m = r[0]; body = m["bodies"][0]; bb = body["bbox"]
    faces = r[1]["faces"] if isinstance(r[1], dict) else r[1][0]["faces"]
    th = r[2]["threads"]
    R = Rows()
    pg = "p.540" if s.family == "csha" else ("p.542" if s.family == "thick" else "p.541")
    R.eq("one closed body", 1, m["body_count"] if body["closed"] else 0, "S50")
    R.num("thickness T (bbox Y)", d["T"], bb["max"][1] - bb["min"][1], 0.005, f"S50 {pg} T")
    # bore of diameter D at height H, centred on the width
    bore = _cyl(faces, s.D / 2, 1)
    R.true(f"shaft bore O{s.D} (axis along Y)", bool(bore), f"S50 {pg} D")
    R.true(f"bore centre height H = {s.H:g}", bool(bore) and all(abs(o[2] - s.H) < 0.005 and abs(o[0]) < 0.005 for o in bore), f"S50 {pg} H",
           "H +-0.02" if s.family != "csha" else "")
    if s.family != "csha":
        R.eq("D tolerance (H8) upper/lower", s.tol, (TOL_OF(s.D)), "S50 p.541/542 DH8", "echoed into the description")
        R.true("tolerance written in the part description", f"{s.tol[0]:+.3f}" in s.description and f"{s.tol[1]:+.3f}" in s.description, "S50")
        R.num("overall length L (bbox X)", d["L"], bb["max"][0] - bb["min"][0], 0.005, f"S50 {pg} L")
        R.num("overall height H1 = H + offset (bbox Z)", s.H1, bb["max"][2] - bb["min"][2], 0.005, f"S50 {pg} H1", f"H1 = H+{d['h1_off']}")
        top = [c for c in _planes(faces, 2) if abs(c[2] - d["S"]) < 0.005]
        R.true(f"foot thickness S = {d['S']:g}", bool(top), f"S50 {pg} S")
        wx = _planes(faces, 0)
        R.true(f"top width W = {d['W']:g}", _has([c[0] for c in wx], d["W"] / 2) and _has([c[0] for c in wx], -d["W"] / 2), f"S50 {pg} W")
    else:
        R.eq("D tolerance class", "H7", s.tolerance_class, "S50 p.540", "tolerance value not printed; class only")
    # base holes
    hx = [o for o in _cyl(faces, d["d"] / 2, 2) if abs(o[0]) > 0.01 and abs(o[0]) > d["L1"] / 2 - 0.01]   # drop the vertical screw hole of the side-slit types
    pitch = {round(o[0], 3) for o in hx}
    R.true(f"base holes O{d['d']:g} at +-L1/2 (L1 = {d['L1']:g})", pitch == {round(d["L1"] / 2, 3), round(-d["L1"] / 2, 3)}, f"S50 {pg} L1, d")
    if s.family != "csha":
        R.eq("number of base holes", d["base_holes"], len({(round(o[0], 3), round(o[1], 3)) for o in hx}), f"S50 {pg} 2-d / 4-d")
    # slit and clamp screw
    if s.family in ("slit", "thick"):
        wall = d["W"] / 2 - d["C"] / 2
        xs = [c[0] for c in _planes(faces, 0)]
        R.true(f"slit width C = {d['C']:g}", _has(xs, d["C"] / 2) and _has(xs, -d["C"] / 2), f"S50 {pg} C")
        sel = [t for t in th if t["designation"] == f"M{d['M']}"]
        R.eq(f"clamp thread M{d['M']} count", d["screws"], len(sel), f"S50 {pg} M", "2 screws for D30-50 thickened" if d["screws"] == 2 else "")
        for t in sel:
            R.num("thread length", d["m_depth"] or wall, abs(t["end"] - t["start"]), 0.01, f"S50 {pg} M", "through" if not d["m_depth"] else "Depth")
            R.num("thread axis height H + E", s.H + d["E"], t["axis_point"][2], 0.005, f"S50 {pg} E")
        c2 = _cyl(faces, d["d2"] / 2, 0)
        R.true(f"screw clearance hole O{d['d2']:g} at H + E", any(abs(o[2] - s.H - d["E"]) < 0.005 for o in c2), f"S50 {pg} d2")
        c1 = _cyl(faces, d["d1"] / 2, 0)
        R.true(f"counterbore O{d['d1']:g} at H + E", any(abs(o[2] - s.H - d["E"]) < 0.005 for o in c1), f"S50 {pg} d1")
        R.true(f"counterbore depth l = {d['l']:g}", _has(xs, -d["W"] / 2 + d["l"]), f"S50 {pg} l")
    elif s.family == "side":
        zs = [c[2] for c in _planes(faces, 2)]
        R.true(f"slit width C = {d['C']:g}", _has(zs, s.H + d["C"] / 2) and _has(zs, s.H - d["C"] / 2), f"S50 {pg} C")
        sel = [t for t in th if t["designation"] == f"M{d['M']}"]
        R.eq(f"clamp thread M{d['M']} count", 1, len(sel), f"S50 {pg} M")
        for t in sel:
            R.num("thread depth", d["m_depth"], abs(t["end"] - t["start"]), 0.01, f"S50 {pg} M", "Depth")
            R.num("thread axis offset E from the bore centre", d["E"], t["axis_point"][0], 0.005, f"S50 {pg} E")
        R.true(f"screw clearance hole O{d['d2']:g} at E", any(abs(o[0] - d["E"]) < 0.005 for o in _cyl(faces, d["d2"] / 2, 2)), f"S50 {pg} d2")
        R.true(f"counterbore O{d['d1']:g} at E", any(abs(o[0] - d["E"]) < 0.005 for o in _cyl(faces, d["d1"] / 2, 2)), f"S50 {pg} d1")
        R.true(f"counterbore depth l = {d['l']:g}", _has(zs, s.H1 - d["l"]), f"S50 {pg} l")
    R.eq("part number metadata", s.code, (r[3].get("metadata") or r[3]).get("part_number"), "-")
    R.eq("design part number", s.code, find_key(r[4], "part_number"), "-")
    return R

def TOL_OF(D):
    from . import holder
    return holder.TOL[D]
