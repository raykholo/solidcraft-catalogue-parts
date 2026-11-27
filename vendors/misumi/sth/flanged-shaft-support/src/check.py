"""Spec check for MISUMI flanged shaft supports: measures the built part with SolidCraft's inspect commands and compares every dimension
with the catalogue value (support.py, sources.toml S51 / S52). Appearance (compact flange corner radius, E-STHMR counterbore depth, the
position of the set screws about the axis) is not checked."""
from __future__ import annotations
import math
from runtime.check import Rows, run_measure, find_key
from runtime.sc import slug
from . import support

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
    R.num("overall length (bbox Z)", s.L, bb["max"][2] - bb["min"][2], 0.005, src + " L" + (" / L1" if s.long else ""))
    zs = [c[2] for c in _planes(faces, 2)]
    xs = [c[0] for c in _planes(faces, 0)]
    if s.series != "mr":
        R.true(f"flange thickness T = {d['T']:g}", _has(zs, d["T"]), src + " T")
    # shaft hole
    R.true(f"shaft hole O{s.D} (axis along Z, on the axis)", _on_axis(_cyl(faces, s.D / 2, 2)), src + " D")
    R.eq("D tolerance (H8) upper/lower", (d["tol_upper"], d["tol_lower"]), s.tol, src + " DH8", "echoed into the description")
    R.true("tolerance written in the part description", f"{s.tol[0]:+.3f}" in s.description and f"{s.tol[1]:+.3f}" in s.description, src + " DH8")
    wx, wy = bb["max"][0] - bb["min"][0], bb["max"][1] - bb["min"][1]
    if s.series == "mr":
        R.num("body diameter H (bbox X)", d["H"], wx, 0.005, src + " H")
        R.num("body diameter H (bbox Y)", d["H"], wy, 0.005, src + " H")
        R.true(f"body cylinder O{d['H']:g}", _on_axis(_cyl(faces, d["H"] / 2, 2)), src + " H")
        R.num("L = T + S + B (printed numbers)", d["T1"] + d["S"] + d["B"] if s.long else d["T"] + d["S"] + d["B"], s.L, 1e-9, src, "derived from the table")
    else:
        R.true(f"sleeve outside diameter D1 = {d['D1']:g}", _on_axis(_cyl(faces, d["D1"] / 2, 2)), src + " D1")
        R.num("Thickness (N) = (D1 - D) / 2", d["N"], s.wall, 1e-9, src + " N, D1, D", "derived from the table: N is the sleeve wall")
        # flange outline
        if s.family == "round":
            R.num("flange diameter H (bbox X)", d["H"], wx, 0.005, src + " H")
            R.num("flange diameter H (bbox Y)", d["H"], wy, 0.005, src + " H")
            R.true(f"flange cylinder O{d['H']:g}", bool(_cyl(faces, d["H"] / 2, 2)), src + " H")
        elif s.family == "square":
            ext = d["H"]
            R.num("square flange extent across the cut corners (bbox X)", ext, wx, 0.005, src + " H, K", "labelled: H is the extent across the cut corners")
            R.num("square flange extent across the cut corners (bbox Y)", ext, wy, 0.005, src + " H, K", "labelled: H is the extent across the cut corners")
        else:
            R.num("compact flange width W (bbox X)", d["W"], wx, 0.005, src + " W")
            R.num("compact flange height H (bbox Y)", d["H"], wy, 0.005, src + " H")
    # mounting holes
    pos = support.hole_positions(s)
    hd = s.hole_d
    got = {(round(o[0], 3), round(o[1], 3)) for o in _cyl(faces, hd / 2, 2)}
    names = {"round": "P", "square": "P", "compact": "P1" + ("" if d.get("F") is None else ", F"), "collar": "P"}
    R.eq(f"mounting holes O{hd:g}: count", len(pos), len(got), src + " 4-d / 2-d / 2-Hole / 4-Hole")
    R.true(f"mounting hole positions ({names[s.family]})", got == {(round(x, 3), round(y, 3)) for x, y in pos}, src + " " + names[s.family])
    if s.series == "mr":
        # (the shaft bore itself may have the same diameter, D8 = d2 8: leave the cylinders on the axis out)
        cb = {(round(o[0], 3), round(o[1], 3)) for o in _cyl(faces, d["d2"] / 2, 2) if abs(o[0]) > 0.005 or abs(o[1]) > 0.005}
        R.true(f"counterbore diameter d2 = {d['d2']:g} at the mounting holes (depth is appearance)", cb == got, src + " d2")
    # set screws
    if s.series in ("std", "thick"):
        sel = [t for t in th if t["designation"] == f"M{d['M']:g}"]
        R.eq(f"set screw thread M{d['M']:g} count", 2 * len(s.screw_z), len(sel), src + " 2-M / 4-M, M")
        for t in sel:
            # the thread is measured to the curved outer surface, so it exceeds the wall by at most the sagitta of the screw radius on the outer surface and on the bore
            sag = d["D1"] / 2 - math.sqrt((d["D1"] / 2) ** 2 - (d["M"] / 2) ** 2)
            ln = abs(t["end"] - t["start"])
            R.true(f"set screw thread length from the wall {s.wall:g} up to wall + {2 * sag:.3f} (got {ln:.3f})", s.wall - 0.01 <= ln <= s.wall + 2 * sag + 0.01,
                   src + " D1, D", "wall = (D1 - D) / 2, measured to the cylindrical surface")
        got_z = sorted(round(t["axis_point"][2], 3) for t in sel)
        want_z = sorted(round(z, 3) for z in s.screw_z for _ in (0, 1))
        R.true(f"set screw positions from the flange back face: {sorted(set(s.screw_z))}", got_z == want_z, src + (" l1" if s.long else " l"),
               "measured: " + ", ".join(f"{z:g}" for z in got_z))
    # end mounting
    if s.series == "xend":
        R.num("bore depth E = L - l1 (printed numbers)", d["E"], d["L"] - d["l1"], 1e-9, src + " E, l1, L", "derived from the table")
        R.true(f"blind bore floor at l1 = {d['l1']:g} from the flange face", _has(zs, d["l1"]), src + " l1")
        R.true(f"counterbore floor at l = {d['l']:g} from the flange face", _has(zs, d["l"]), src + " l")
        R.true(f"mounting screw hole O{d['d2']:g} (d2) on the axis", _on_axis(_cyl(faces, d["d2"] / 2, 2)), src + " d2")
        R.true(f"mounting screw counterbore O{d['d1']:g} (d1) on the axis", _on_axis(_cyl(faces, d["d1"] / 2, 2)), src + " d1")
    # clamp
    if s.series in ("slit", "mr"):
        g = support.clamp_geometry(s)
        R.true(f"groove: start z = {g['g0']:g}", _has(zs, g["g0"]), src + (" B, S1, L" if s.series == "slit" else " T, S"), "depth is not printed")
        R.true(f"groove: width {g['gw']:g} (end z = {g['g0'] + g['gw']:g}, ring B = {g['B']:g} to the end)", _has(zs, g["g0"] + g["gw"]), src + " B, S1" if s.series == "slit" else src + " S, B")
        R.true(f"radial slit width {g['slit']:g}", _has(xs, g["slit"] / 2) and _has(xs, -g["slit"] / 2), src + (" S" if s.series == "slit" else " 1.5 (figure)"))
        R.true(f"clamp screw counterbore floor Y = {d['Y']:g} from the slit centre", _has(xs, -d["Y"]), src + " Y")
        for rad, label, col in ((g["clear"], "clearance hole", "d2" if s.series == "slit" else "d"), (g["cb"], "counterbore", "d1" if s.series == "slit" else "R")):
            o = _cyl(faces, rad / 2, 0)
            R.true(f"clamp screw {label} O{rad:g} on the clamp axis (y = X = {d['X']:g}, z = {g['zc']:g})",
                   all(any(abs(c[1] - d["X"]) < 0.005 and abs(c[2] - zc) < 0.005 for c in o) for zc in g["zcs"]), src + f" {col}, X, B")
        sel = [t for t in th if t["designation"] == f"M{d['M']:g}"]
        R.eq(f"clamp screw thread M{d['M']:g} count", len(g["zcs"]), len(sel), src + " M")
        R.true(f"clamp screw thread axes at y = X = {d['X']:g}, z = {', '.join(f'{z:g}' for z in g['zcs'])} (B / 2, or B / 4 and 3 B / 4 on the slit long sleeve)",
               all(abs(t["axis_point"][1] - d["X"]) < 0.005 for t in sel) and sorted(round(t["axis_point"][2], 3) for t in sel) == sorted(round(z, 3) for z in g["zcs"]), src + " X, B")
    R.eq("part number metadata", s.code, (r[3].get("metadata") or r[3]).get("part_number"), "-")
    R.eq("design part number", s.code, find_key(r[4], "part_number"), "-")
    return R
