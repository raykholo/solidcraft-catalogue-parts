"""Spec check for MISUMI linear bushings: measures the built part with SolidCraft's inspect commands and compares every
dimension with the catalogue value (bushing.py, sources.toml S11 and S13)."""
from __future__ import annotations
import math
from runtime.check import Rows, run_measure, cyl_groups, find_key
from runtime.sc import slug
from . import bushing as bu

def _xplanes(faces):
    """Planar faces whose normal is along X: list of centroids."""
    out = []
    for f in faces:
        n = f.get("plane_normal")
        if n and abs(abs(n[0]) - 1) < 1e-6:
            out.append(f["centroid"])
    return out

def check(b, sc, out):
    D, L, dr = b.D, b.L, b.dr
    cmds = [{"command": "inspect.measure", "params": {}},
            {"command": "model.faces", "params": {"body": b.code}},
            {"command": "component.metadata", "params": {"component": b.code}},
            {"command": "document.metadata", "params": {}}]
    r = run_measure(sc, cmds, out, slug(b.code))
    m = r[0]; body = m["bodies"][0]; bb = body["bbox"]
    faces = r[1]["faces"] if isinstance(r[1], dict) else r[1][0]["faces"]
    R = Rows()
    pg = b.page or ({"short": "p.464", "medium": "p.465"}.get(b.series) if b.family == "straight" else
                    ("p.466" if b.family == "round" else "p.468") if b.series == "long" else ("p.467" if b.family == "round" else "p.469"))
    S = "S13" if b.page else "S11"
    R.eq("one closed body", 1, m["body_count"] if body["closed"] else 0, S)
    R.num("overall length L (X)", L, bb["max"][0] - bb["min"][0], 0.005, f"{S} {pg} L")
    span = b.flange["H"] if b.flange else D
    spany = b.flange["width"] if b.family == "compact" else span
    R.num("outer extent (bbox Y)" if not b.flange else ("flange width D+6/8/10 (bbox Y)" if b.family == "compact" else "flange extent H (bbox Y)"),
          spany, bb["max"][1] - bb["min"][1], 0.005, f"{S} {pg} " + ("width" if b.family == "compact" else "H" if b.flange else "D"))
    R.num("outer extent (bbox Z)" if not b.flange else "flange extent H (bbox Z)", span, bb["max"][2] - bb["min"][2], 0.005, f"{S} {pg} " + ("H" if b.flange else "D"))
    g = cyl_groups(faces)
    R.true(f"outside cylinder D {D:g}", round(D / 2, 3) in g, f"{S} {pg} D")
    R.true(f"bore cylinder dr {dr}", round(dr / 2, 3) in g, f"{S} {pg} dr")
    R.true("tolerances written in the part description",
           f"{b.D_tol:+.3f}" in b.description and f"{b.dr_tol[1]:+.3f}" in b.description, f"{S} {pg}", "echoed, not drawn")
    if b.family == "straight" and not b.grooves:
        R.num("volume = pi/4 (D^2 - dr^2) L", math.pi / 4 * (D * D - dr * dr) * L, body["volume_mm3"], 1e-4 * math.pi / 4 * D * D * L, "derived")
    if b.grooves:
        gr = b.grooves
        (g1s, g1e), (g2s, g2e) = bu.groove_spans(b)
        R.eq("ring grooves: cylinder faces at D1", 2, len(g.get(round(gr["D1"] / 2, 3), [])), f"{S} {pg} D1")
        xs = sorted(c[0] for c in _xplanes(faces) if 0.01 < c[0] < L - 0.01)
        R.eq("ring groove walls", 4, len(xs), f"{S} {pg} W B")
        if len(xs) == 4:
            R.num("groove width W (first)", gr["W"], xs[1] - xs[0], 0.005, f"{S} {pg} W")
            R.num("groove width W (second)", gr["W"], xs[3] - xs[2], 0.005, f"{S} {pg} W")
            R.num("distance between the grooves B", gr["B"], xs[2] - xs[1], 0.005, f"{S} {pg} B")
    if b.flange:
        f = b.flange
        xp = _xplanes(faces)
        x0 = b.x0
        T = f["T"]
        R.true(f"flange thickness T = {T:g}", any(abs(c[0] - (x0 + T)) < 0.005 and abs(math.hypot(c[1], c[2])) < f["H"] / 2 for c in xp), f"{S} {pg} T")
        if b.layout != "standard":
            R.true(f"flange starts l = {x0:g} from the end of the barrel",
                   any(abs(c[0] - x0) < 0.005 and abs(math.hypot(c[1], c[2])) < f["H"] / 2 for c in xp), f"{S} {pg} l")
        if b.layout == "center":
            R.num("flange centred: l + T/2 = L/2", L / 2, x0 + T / 2, 0.005, f"{S} {pg} l T L", "derived: the printed l, T and L agree")
        if b.family == "round":
            R.true(f"flange cylinder H {f['H']:g}", round(f["H"] / 2, 3) in g, f"{S} {pg} H")
        elif b.family == "compact":
            R.true(f"flange end arcs H {f['H']:g}", round(f["H"] / 2, 3) in g, f"{S} {pg} H")
            flats = [fc for fc in faces if fc.get("plane_normal") and abs(abs(fc["plane_normal"][1]) - 1) < 1e-6]
            R.eq("compact flange flats", 2, len(flats), f"{S} {pg} D+6/8/10")
            R.true("flats at width/2 from the axis", len(flats) == 2 and all(abs(abs(fc["centroid"][1]) - f["width"] / 2) < 0.005 for fc in flats), f"{S} {pg} D+6/8/10")
        else:
            flats = [fc for fc in faces if fc.get("plane_normal") and abs(fc["plane_normal"][0]) < 1e-6
                     and abs(abs(fc["plane_normal"][1]) - math.sqrt(0.5)) < 1e-6]
            R.eq("square flange flats", 4, len(flats), f"{S} {pg} W")
            R.true("flats at W/2 from the axis", len(flats) == 4 and all(abs(math.hypot(fc["centroid"][1], fc["centroid"][2]) - f["W"] / 2) < 0.005 for fc in flats), f"{S} {pg} W")
        centres = bu.hole_centres(b)
        n = len(centres)
        hd = g.get(round(f["d"] / 2, 3), [])
        cbs = g.get(round(f["d1"] / 2, 3), [])
        R.eq(f"{n} mounting holes d {f['d']:g}", n, len(hd), f"{S} {pg} d")
        R.eq(f"{n} counterbores d1 {f['d1']:g}", n + (1 if f["d1"] == dr else 0), len(cbs), f"{S} {pg} d1", "dr 6: the bore has the same radius as d1 6, so it is counted too" if f["d1"] == dr else "")
        near = lambda y, z: any(abs(y - cy) < 0.005 and abs(z - cz) < 0.005 for cy, cz in centres)
        label = "holes at A / F" if b.family == "compact" else "holes on P.C.D."
        R.true(label, len(hd) == n and all(near(o[1], o[2]) for o, _ in hd), f"{S} {pg} " + ("A F" if b.family == "compact" else "P.C.D."))
        xf = bu.cb_face_x(b)
        floor = x0 + f["t"] if b.counterbore == "opposite" else xf - f["t"]
        fl = [c for c in xp if abs(c[0] - floor) < 0.005 and any(abs(c[1] - cy) < 0.05 and abs(c[2] - cz) < 0.05 for cy, cz in centres)]
        R.eq(f"counterbore floors at depth t = {f['t']:g}", n, len(fl), f"{S} {pg} t", "counterbore side: figure reading")
    R.eq("part number metadata", b.code, (r[2].get("metadata") or r[2]).get("part_number"), "-")
    R.eq("design part number", b.code, find_key(r[3], "part_number"), "-")
    return R
