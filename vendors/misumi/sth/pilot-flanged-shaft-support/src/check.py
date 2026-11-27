"""Spec check for MISUMI pilot flanged shaft supports: measures the built part with SolidCraft's inspect commands and compares every dimension
with the catalogue value (pilot.py, sources.toml S18). Appearance (compact flange corner radius, groove depth, slit stub) is not checked."""
from __future__ import annotations
from runtime.check import Rows, run_measure, find_key
from runtime.sc import slug
from . import pilot

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

def _on_axis(origins):
    return any(abs(o[0]) < 0.005 and abs(o[1]) < 0.005 for o in origins)

def check(s, sc, out):
    d = s.dims
    src = d["source"] + " " + d["page"]
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
    R.eq("one closed body", 1, m["body_count"] if body["closed"] else 0, src)
    R.num("overall length L1 (bbox Z, pilot face to sleeve end)", d["L1"], bb["max"][2] - bb["min"][2], 0.005, src + " L1")
    R.num("pilot face at z = 0", 0.0, bb["min"][2], 0.005, src + " L1, T")
    zs = [c[2] for c in _planes(faces, 2)]
    xs = [c[0] for c in _planes(faces, 0)]
    T = d["T"]
    R.true(f"pilot length T = {T:g} (flange back face at z = T)", _has(zs, T), src + " T")
    R.true(f"flange thickness T = {T:g} (flange front face at z = 2 T)", _has(zs, 2 * T), src + " T")
    R.true(f"shaft hole O{s.D} (axis along Z, on the axis)", _on_axis(_cyl(faces, s.D / 2, 2)), src + " D")
    R.eq("D tolerance (H8) upper/lower", (d["tol_upper"], d["tol_lower"]), s.tol, src + " DH8", "echoed into the description")
    R.true("tolerance written in the part description", f"{s.tol[0]:+.3f}" in s.description and f"{s.tol[1]:+.3f}" in s.description, src + " DH8")
    R.true(f"pilot and sleeve outside diameter D1 = {d['D1']:g} (h8)", _on_axis(_cyl(faces, d["D1"] / 2, 2)), src + " D1")
    R.num("Thickness (N) = (D1 - D) / 2", d["N"], s.wall, 1e-9, src + " N, D1, D", "derived from the table: N is the sleeve wall")
    wx, wy = bb["max"][0] - bb["min"][0], bb["max"][1] - bb["min"][1]
    if s.family == "round":
        R.num("flange diameter H (bbox X)", d["H"], wx, 0.005, src + " H")
        R.num("flange diameter H (bbox Y)", d["H"], wy, 0.005, src + " H")
        R.true(f"flange cylinder O{d['H']:g}", bool(_cyl(faces, d["H"] / 2, 2)), src + " H")
    else:
        R.num("compact flange width W (bbox X)", d["W"], wx, 0.005, src + " W")
        R.num("compact flange height H (bbox Y)", d["H"], wy, 0.005, src + " H")
    pos = pilot.hole_positions(s)
    got = {(round(o[0], 3), round(o[1], 3)) for o in _cyl(faces, d["d"] / 2, 2)}
    R.eq(f"mounting holes O{d['d']:g}: count", 4, len(got), src + " 4-d")
    R.true("mounting hole positions (" + ("P" if s.family == "round" else "F, P1") + ")",
           got == {(round(x, 3), round(y, 3)) for x, y in pos}, src + (" P" if s.family == "round" else " P1, F"))
    # clamp
    g = pilot.clamp_geometry(s)
    R.true(f"groove: start z = {g['g0']:g} (L1 - B - S1)", _has(zs, g["g0"]), src + " L1, B, S1", "depth is not printed")
    R.true(f"groove: width S1 = {g['gw']:g} (end z = {g['g0'] + g['gw']:g}, ring B = {g['B']:g} to the sleeve end)", _has(zs, g["g0"] + g["gw"]), src + " B, S1")
    R.true(f"radial slit width S = {g['slit']:g}", _has(xs, g["slit"] / 2) and _has(xs, -g["slit"] / 2), src + " S")
    R.true(f"clamp screw counterbore floor Y = {d['Y']:g} from the slit centre", _has(xs, -d["Y"]), src + " Y")
    for rad, label, col in ((g["clear"], "clearance hole", "d2"), (g["cb"], "counterbore", "d1")):
        o = _cyl(faces, rad / 2, 0)
        R.true(f"clamp screw {label} O{rad:g} on the clamp axis (y = X = {d['X']:g}, z = {g['zc']:g})",
               any(abs(c[1] - d["X"]) < 0.005 and abs(c[2] - g["zc"]) < 0.005 for c in o), src + f" {col}, X, B")
    sel = [t for t in th if t["designation"] == f"M{d['M']:g}"]
    R.eq(f"clamp screw thread M{d['M']:g} count", 1, len(sel), src + " M")
    R.true(f"clamp screw thread axis at y = X = {d['X']:g}, z = {g['zc']:g} (B / 2 from the sleeve end)",
           all(abs(t["axis_point"][1] - d["X"]) < 0.005 and abs(t["axis_point"][2] - g["zc"]) < 0.005 for t in sel), src + " X, B")
    R.eq("part number metadata", s.code, (r[3].get("metadata") or r[3]).get("part_number"), "-")
    R.eq("design part number", s.code, find_key(r[4], "part_number"), "-")
    return R
