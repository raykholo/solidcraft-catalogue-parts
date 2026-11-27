"""Spec check for MISUMI shaft collars: measures the built part with SolidCraft's inspect commands and compares every
dimension with the catalogue value (collar.py, sources.toml S20)."""
from __future__ import annotations
import math
from runtime.check import Rows, run_measure, cyl_groups, find_key
from runtime.sc import slug
from . import collar as co

def _faces_of(reply):
    return reply["faces"] if isinstance(reply, dict) else reply[0]["faces"]

def _check_ring(s, sc, out):
    # the split type is two bodies (the two halves); the other types are one
    r0 = run_measure(sc, [{"command": "inspect.measure", "params": {}}], out, slug(s.code) + ".pre")[0]
    names = [b["name"] for b in r0["bodies"]]
    cmds = [{"command": "inspect.measure", "params": {}},
            {"command": "model.threads", "params": {}},
            {"command": "component.metadata", "params": {"component": s.code}},
            {"command": "document.metadata", "params": {}}]
    cmds += [{"command": "model.faces", "params": {"body": n}} for n in names]
    r = run_measure(sc, cmds, out, slug(s.code))
    m = r[0]; bodies = m["bodies"]
    th = r[1]["threads"]
    faces = [f for rep in r[4:] for f in _faces_of(rep)]
    lo = [min(b["bbox"]["min"][i] for b in bodies) for i in range(3)]
    hi = [max(b["bbox"]["max"][i] for b in bodies) for i in range(3)]
    R = Rows()
    want = 2 if s.split else 1
    R.eq(f"{want} closed body" + ("" if want == 1 else " (the two halves)"), want, sum(1 for b in bodies if b["closed"]), "S20",
         "split type = two halves" if s.split else "")
    R.num("width B (Z)", s.B, hi[2] - lo[2], 0.005, f"S20 p.{544 if s.type in ('C-SCSAW', 'C-SCNPAW') else 545} width B")
    R.num("outer diameter D1 (X)", s.D1, hi[0] - lo[0], 0.01, "S20 table D1")
    # the slit / split gap (appearance) trims the outer circle at the bottom by a few thousandths
    y_exp = 2 * math.sqrt((s.D1 / 2) ** 2 - (co.SPLIT_GAP / 2) ** 2) if s.split else s.D1 / 2 + math.sqrt((s.D1 / 2) ** 2 - (co.SLIT_W / 2) ** 2)
    R.num("outer diameter D1 (Y)", y_exp, hi[1] - lo[1], 0.005, "S20 table D1", "slit / gap chord removed")
    g = cyl_groups(faces)
    R.true(f"outer cylinder face O{s.D1:g}", round(s.D1 / 2, 3) in g, "S20 table D1")
    R.true(f"bore cylinder face I.D. {s.D}", round(s.D / 2, 3) in g, "S20 table I.D. D", f"nominal; +{co.BORE_TOL[0]:.2f}/+{co.BORE_TOL[1]:.2f} is the tolerance before cutting")
    R.true("bore tolerance written in the part description", "+0.05/+0.01" in s.description, "S20 p.544 note")
    R.true("D1 larger than D", s.D1 > s.D, "derived")
    sel = [t for t in th if t["designation"] == s.M]
    R.true(f"clamp screw thread {s.M} present", len(sel) >= (2 if s.split else 1), "S20 table M (coarse)", "position and depth are appearance")
    R.true("no other thread", len(sel) == len(th), "S20 table M (coarse)")
    if s.type == "C-SCSMAW":
        rr = round(s.S / 2, 3)
        xs = sorted(round(o[0], 3) for o, _ in g.get(rr, []) if abs(o[0]) > 0.01)
        R.true(f"2 fixing through holes diameter S = {s.S:g}", len(set(xs)) == 2, "S20 p.545 S")
        R.num("hole pitch P", s.P, (xs[-1] - xs[0]) if len(xs) >= 2 else None, 0.005, "S20 p.545 P")
        R.true("holes are axial (along Z)", all(abs(abs(a[2]) - 1) < 1e-6 for _, a in g.get(rr, [])), "S20 p.545")
        R.true("holes clear the bore and the outer diameter", s.P / 2 - s.S / 2 > s.D / 2 and s.P / 2 + s.S / 2 < s.D1 / 2, "derived from P, S, D, D1")
    if s.type == "C-SCSGAW":
        r1, r2 = round(s.d1 / 2, 3), round(s.d2 / 2, 3)
        x1 = sorted(round(o[0], 3) for o, _ in g.get(r1, []) if abs(o[0]) > 0.01)
        x2 = sorted(round(o[0], 3) for o, _ in g.get(r2, []) if abs(o[0]) > 0.01)
        R.true(f"2 through holes diameter d1 = {s.d1:g}", len(set(x1)) == 2, "S20 p.545 d1")
        R.true(f"2 counterbores diameter d2 = {s.d2:g}", len(set(x2)) == 2, "S20 p.545 d2")
        R.num("hole pitch P", s.P, (x1[-1] - x1[0]) if len(x1) >= 2 else None, 0.005, "S20 p.545 P")
        floors = [f for f in faces if f.get("plane_normal") and abs(f["plane_normal"][2] - 1) < 1e-6 and abs(f["centroid"][2] - (s.B - s.t)) < 0.005]
        R.eq(f"counterbore floors at B - t = {s.B - s.t:g}", 2, len(floors), "S20 p.545 t", f"t = {s.t:g}")
        R.true("counterbores clear the outer diameter", s.P / 2 + s.d2 / 2 <= s.D1 / 2 + 1e-9, "derived from P, d2, D1")
    R.eq("part number metadata", s.code, (r[2].get("metadata") or r[2]).get("part_number"), "-")
    R.eq("design part number", s.code, find_key(r[3], "part_number"), "-")
    return R


def _measure(s, sc, out):
    r0 = run_measure(sc, [{"command": "inspect.measure", "params": {}}], out, slug(s.code) + ".pre")[0]
    names = [b["name"] for b in r0["bodies"]]
    cmds = [{"command": "inspect.measure", "params": {}},
            {"command": "model.threads", "params": {}},
            {"command": "component.metadata", "params": {"component": s.code}},
            {"command": "document.metadata", "params": {}}]
    cmds += [{"command": "model.faces", "params": {"body": n}} for n in names]
    r = run_measure(sc, cmds, out, slug(s.code))
    faces = [f for rep in r[4:] for f in _faces_of(rep)]
    return r, r[0]["bodies"], r[1]["threads"], faces

def _planes_x(faces):
    """centroid x of every plane whose normal is along X"""
    return [f["centroid"][0] for f in faces if f.get("plane_normal") and abs(abs(f["plane_normal"][0]) - 1) < 1e-6]

def _x_cyls(g, radius):
    """(y, z) of the axis of every cylinder of that radius whose axis is along X, rounded"""
    return sorted({(round(o[1], 3), round(o[2], 3)) for o, a in g.get(round(radius, 3), []) if abs(abs(a[0]) - 1) < 1e-6})

def _check_bearing(s, sc, out):
    r, bodies, th, faces = _measure(s, sc, out)
    lo = [min(b["bbox"]["min"][i] for b in bodies) for i in range(3)]
    hi = [max(b["bbox"]["max"][i] for b in bodies) for i in range(3)]
    R = Rows()
    R.eq("1 closed body", 1, sum(1 for b in bodies if b["closed"]), "S21")
    R.num("total width B (Z)", s.B, hi[2] - lo[2], 0.005, "S21 p.546 width B")
    R.num("outer diameter D1 (X)", s.D1, hi[0] - lo[0], 0.01, "S21 p.546 table D1")
    R.num("outer diameter D1 (Y)", s.D1 / 2 + math.sqrt((s.D1 / 2) ** 2 - (co.SLIT_W / 2) ** 2), hi[1] - lo[1], 0.005, "S21 p.546 table D1", "slit chord removed")
    g = cyl_groups(faces)
    R.true(f"outer cylinder face O{s.D1:g}", round(s.D1 / 2, 3) in g, "S21 p.546 table D1")
    R.true(f"boss cylinder face Ds {s.Ds}", round(s.Ds / 2, 3) in g, "S21 p.546 table Ds")
    R.true(f"bore cylinder face I.D. {s.D}", round(s.D / 2, 3) in g, "S21 p.546 table I.D. D", f"nominal; +{co.BORE_TOL[0]:.2f}/+{co.BORE_TOL[1]:.2f} is the tolerance before cutting")
    R.true("bore tolerance written in the part description", "+0.05/+0.01" in s.description, "S21 p.546 note")
    cz = [f["centroid"][2] for f in faces if f.get("plane_normal") and abs(abs(f["plane_normal"][2]) - 1) < 1e-6]
    R.true(f"shoulder face at ring width b = {s.b:g}", any(abs(z - s.b) < 0.005 for z in cz), "S21 p.546 b")
    R.true(f"boss end face at B = {s.B:g}", any(abs(z - s.B) < 0.005 for z in cz), "S21 p.546 B")
    R.true("Ds larger than D, smaller than D1", s.D < s.Ds < s.D1, "derived")
    sel = [t for t in th if t["designation"] == s.M]
    R.true(f"clamp screw thread {s.M} present", len(sel) >= 1, "S21 p.546 table M (coarse)", "position and depth are appearance")
    R.true("no other thread", len(sel) == len(th), "S21 p.546 table M (coarse)")
    R.eq("part number metadata", s.code, (r[2].get("metadata") or r[2]).get("part_number"), "-")
    R.eq("design part number", s.code, find_key(r[3], "part_number"), "-")
    return R

def _check_urethane(s, sc, out):
    r, bodies, th, faces = _measure(s, sc, out)
    pg = co.PAGE[s.family]
    src = f"S21 {pg}"
    lo = [min(b["bbox"]["min"][i] for b in bodies) for i in range(3)]
    hi = [max(b["bbox"]["max"][i] for b in bodies) for i in range(3)]
    dmp = [b for b in bodies if b["name"].startswith("Urethane damper")]
    stl = [b for b in bodies if not b["name"].startswith("Urethane damper")]
    n = 2 if s.split else 1
    R = Rows()
    R.eq(f"{n} steel part(s) + 1 urethane damper, all closed", n + 1, sum(1 for b in bodies if b["closed"]), "S21", "split type = two halves" if s.split else "")
    R.eq("steel bodies", n, len(stl), "S21")
    R.num("total width B (Z)", s.B, hi[2] - lo[2], 0.005, src + " B")
    R.num("damper thickness t", s.t, (dmp[0]["bbox"]["max"][2] - dmp[0]["bbox"]["min"][2]) if dmp else None, 0.005, src + " t")
    R.num("steel width B1", s.B1, (max(b["bbox"]["max"][2] for b in stl) - min(b["bbox"]["min"][2] for b in stl)) if stl else None, 0.005, src + " B1")
    R.num("B - B1 = t", s.t, s.B - s.B1, 1e-9, src, "derived: printed B, B1, t agree")
    R.num("outer diameter D1 (X)", s.D1, hi[0] - lo[0], 0.01, src + " D1")
    R.num("outer diameter D1 (Y)", s.D1, hi[1] - lo[1], 0.01, src + " D1", "the damper disc is a full ring")
    g = cyl_groups(faces)
    R.true(f"outer cylinder face O{s.D1:g}", round(s.D1 / 2, 3) in g, src + " D1")
    R.true(f"bore cylinder face I.D. {s.D}", round(s.D / 2, 3) in g, src + " I.D. D", f"nominal; +{s.tol[0]:.2f}/+{s.tol[1]:.2f} is the tolerance before cutting")
    R.true("bore tolerance written in the part description", f"+{s.tol[0]:.2f}/+{s.tol[1]:.2f}" in s.description, src + " D tolerance")
    xs = _planes_x(faces)
    pos = [x for x in xs if x > 1e-9]; neg = [x for x in xs if x < -1e-9]
    R.num("slit / gap width W", s.W, (min(pos) - max(neg)) if pos and neg else None, 0.005, src + " W")
    R.true(f"head seat floor face(s) at Y = {s.Y:g}", sum(1 for x in xs if abs(x - s.Y) < 0.005) >= n, src + " Y", "flat floor of the head seat")
    ys = sorted({-s.X} | ({s.X} if s.split else set()))
    want = [(round(y, 3), round(s.zc, 3)) for y in ys]
    R.eq(f"clearance hole d = {s.d:g} axes at y = {', '.join(f'{v:g}' for v in ys)} (X), z = {s.zc:g}", want, _x_cyls(g, s.d / 2), src + " d, X", "z: appearance (centred on B1)")
    R.eq(f"head seat radius R = {s.R:g} on the same axes", want, _x_cyls(g, s.R), src + " R")
    R.true(f"head seat 2R = {2 * s.R:g} within B1, floor beyond the slit", 2 * s.R <= s.B1 and s.Y > s.W / 2, "derived")
    sel = [t for t in th if t["designation"] == s.M]
    R.true(f"clamp screw thread {s.M} present", len(sel) >= n, src + " M (coarse)", "tapped half and length are appearance")
    R.true("no other thread", len(sel) == len(th), src + " M (coarse)")
    R.eq("part number metadata", s.code, (r[2].get("metadata") or r[2]).get("part_number"), "-")
    R.eq("design part number", s.code, find_key(r[3], "part_number"), "-")
    return R

def check(s, sc, out):
    if isinstance(s, co.Bearing):
        return _check_bearing(s, sc, out)
    if isinstance(s, co.Urethane):
        return _check_urethane(s, sc, out)
    return _check_ring(s, sc, out)
