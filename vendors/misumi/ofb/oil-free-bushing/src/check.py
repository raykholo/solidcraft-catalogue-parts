"""Spec check for MISUMI oil free bushings: measures the built part with SolidCraft's inspect commands and compares every dimension
with the catalogue value (oilfree.py, sources.toml S16)."""
from __future__ import annotations
import math
from runtime.check import Rows, run_measure, cyl_groups, find_key
from runtime.sc import slug
from . import oilfree as ob

def _xplanes(faces):
    """Planar faces whose normal is along X: list of centroids."""
    out = []
    for f in faces:
        n = f.get("plane_normal")
        if n and abs(abs(n[0]) - 1) < 1e-6:
            out.append(f["centroid"])
    return out

def check(b, sc, out):
    D, L, d = b.D, b.L, b.d
    f = b.flange
    cmds = [{"command": "inspect.measure", "params": {}},
            {"command": "model.faces", "params": {"body": b.code}},
            {"command": "component.metadata", "params": {"component": b.code}},
            {"command": "document.metadata", "params": {}}]
    r = run_measure(sc, cmds, out, slug(b.code))
    m = r[0]; body = m["bodies"][0]; bb = body["bbox"]
    faces = r[1]["faces"] if isinstance(r[1], dict) else r[1][0]["faces"]
    S, pg = "S16", b.page
    R = Rows()
    R.eq("one closed body", 1, m["body_count"] if body["closed"] else 0, S)
    R.num("overall length L (X)", L, bb["max"][0] - bb["min"][0], 0.005, f"{S} {pg} L")
    spany = f["width"] if b.family == "compact" else (f["H"] if f else D)
    spanz = f["H"] if f else D
    R.num("outer extent (bbox Y)" if not f else ("flange width D+6 (bbox Y)" if b.family == "compact" else "flange extent H (bbox Y)"),
          spany, bb["max"][1] - bb["min"][1], 0.005, f"{S} {pg} " + ("D+6" if b.family == "compact" else "H" if f else "D"))
    R.num("outer extent (bbox Z)" if not f else "flange extent H (bbox Z)", spanz, bb["max"][2] - bb["min"][2], 0.005, f"{S} {pg} " + ("H" if f else "D"))
    g = cyl_groups(faces)
    R.true(f"outside cylinder D {D:g}", round(D / 2, 3) in g, f"{S} {pg} D")
    R.true(f"bore cylinder d {d}", round(d / 2, 3) in g, f"{S} {pg} d")
    if b.N:
        R.num("wall thickness N = (D - d) / 2", b.N, (D - d) / 2, 1e-6, f"{S} {pg} N", "derived: the printed N, D and d agree")
    R.true("tolerances written in the part description",
           f"{b.bore_tol[0]:+.3f}" in b.description and f"{b.bore_tol[1]:+.3f}" in b.description and b.od_class in b.description,
           f"{S} {pg}", "echoed, not drawn")
    if b.family == "straight":
        R.num("volume = pi/4 (D^2 - d^2) L", math.pi / 4 * (D * D - d * d) * L, body["volume_mm3"], 1e-4 * math.pi / 4 * D * D * L, "derived")
    if b.family in ("shouldered", "thrust"):
        t = f["t"]
        R.true(f"flange cylinder H {f['H']:g}", round(f["H"] / 2, 3) in g, f"{S} {pg} H")
        xp = _xplanes(faces)
        R.true(f"flange thickness t = {t:g}", any(abs(c[0] - t) < 0.005 and abs(math.hypot(c[1], c[2])) < f["H"] / 2 for c in xp), f"{S} {pg} t")
        R.num("volume = pi/4 ((D^2 - d^2) L + (H^2 - D^2) t)", math.pi / 4 * ((D * D - d * d) * L + (f["H"] ** 2 - D * D) * t), body["volume_mm3"],
              1e-4 * math.pi / 4 * f["H"] ** 2 * L, "derived")
    if b.family in ("round", "square", "compact"):
        T = f["T"]
        xp = _xplanes(faces)
        R.true(f"flange thickness T = {T:g}", any(abs(c[0] - T) < 0.005 and abs(math.hypot(c[1], c[2])) < f["H"] / 2 for c in xp), f"{S} {pg} T")
        if b.family == "round":
            R.true(f"flange cylinder H {f['H']:g}", round(f["H"] / 2, 3) in g, f"{S} {pg} H")
        elif b.family == "compact":
            R.true(f"flange end arcs H {f['H']:g}", round(f["H"] / 2, 3) in g, f"{S} {pg} H")
            flats = [fc for fc in faces if fc.get("plane_normal") and abs(abs(fc["plane_normal"][1]) - 1) < 1e-6]
            R.eq("compact flange flats", 2, len(flats), f"{S} {pg} D+6")
            R.true("flats at (D+6)/2 from the axis", len(flats) == 2 and all(abs(abs(fc["centroid"][1]) - f["width"] / 2) < 0.005 for fc in flats), f"{S} {pg} D+6")
        else:
            flats = [fc for fc in faces if fc.get("plane_normal") and abs(fc["plane_normal"][0]) < 1e-6
                     and abs(abs(fc["plane_normal"][1]) - math.sqrt(0.5)) < 1e-6]
            R.eq("square flange flats", 4, len(flats), f"{S} {pg} W")
            R.true("flats at W/2 from the axis", len(flats) == 4 and all(abs(math.hypot(fc["centroid"][1], fc["centroid"][2]) - f["W"] / 2) < 0.005 for fc in flats), f"{S} {pg} W")
        centres = ob.hole_centres(b)
        n = len(centres)
        hd = g.get(round(f["d1"] / 2, 3), [])
        cbs = g.get(round(f["d2"] / 2, 3), [])
        R.eq(f"{n} mounting holes d1 {f['d1']:g}", n, len(hd), f"{S} {pg} d1")
        R.eq(f"{n} counterbores d2 {f['d2']:g}", n + (1 if f["d2"] == d else 0), len(cbs), f"{S} {pg} d2",
             "d 6: the bore has the same radius as d2 6, so it is counted too" if f["d2"] == d else "")
        near = lambda y, z: any(abs(y - cy) < 0.005 and abs(z - cz) < 0.005 for cy, cz in centres)
        label = "holes at A / F" if b.family == "compact" else "holes on P.C.D."
        R.true(label, len(hd) == n and all(near(o[1], o[2]) for o, _ in hd), f"{S} {pg} " + ("A F" if b.family == "compact" else "P.C.D."))
        fl = [c for c in xp if abs(c[0] - f["t"]) < 0.005 and any(abs(c[1] - cy) < 0.05 and abs(c[2] - cz) < 0.05 for cy, cz in centres)]
        R.eq(f"counterbore floors at depth t = {f['t']:g}", n, len(fl), f"{S} {pg} t", "counterbore on the outer flange face: figure reading")
    R.eq("part number metadata", b.code, (r[2].get("metadata") or r[2]).get("part_number"), "-")
    R.eq("design part number", b.code, find_key(r[3], "part_number"), "-")
    return R
