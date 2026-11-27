"""Spec check for MISUMI linear shafts: measures the built part with SolidCraft's inspect commands and compares every
dimension with the catalogue value (shaft.py, sources.toml S8 for p.432-433, S30 for p.434-438)."""
from __future__ import annotations
import math
from runtime.check import Rows, run_measure, cyl_groups, find_key
from runtime.sc import slug
from . import shaft as sh

def _planes(faces, axis):
    """Planar faces whose normal is along `axis` (0, 1 or 2): list of centroids."""
    out = []
    for f in faces:
        n = f.get("plane_normal")
        if n and abs(abs(n[axis]) - 1) < 1e-6:
            out.append(f["centroid"])
    return out

def _src(s):
    return "S8" if s.family in ("straight", "T") else "S30"

def check(s, sc, out):
    D, L = s.D, s.L
    page = sh.FAM_PAGE[s.family]
    S = _src(s)
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
    R.eq("one closed body", 1, m["body_count"] if body["closed"] else 0, S)
    total = s.total_length
    R.num("length (X)" if not (s.F or s.T) else "overall length (Y) = F + L + T", total, bb["max"][0] - bb["min"][0], 0.005, f"{S} p.{page} L",
          "1 mm steps" + (f", LKC L+-{s.length_tol:g}" if s.lkc else ""))
    R.num("diameter D (bbox Y)", D, bb["max"][1] - bb["min"][1], 0.005, f"{S} p.{page} D{D}")
    R.num("diameter D (bbox Z)", D, bb["max"][2] - bb["min"][2], 0.005, f"{S} p.{page} D{D}")
    g = cyl_groups(faces)
    R.true(f"cylinder face O{D}", round(D / 2, 3) in g, f"{S} p.{page}")
    gt, f8 = sh.D_TABLE[D][0], sh.D_TABLE[D][1]
    exp_tol = f8 if s.tolerance_class == "f8" else gt
    R.eq(f"D tolerance {s.tolerance_class} upper/lower", exp_tol, s.tol, "S8 p.432 spec table", "echoed into the description")
    R.true("tolerance written in the part description", f"{s.tol[0]:+.3f}" in s.description and f"{s.tol[1]:+.3f}" in s.description, "S8 p.432")
    if s.family in ("PG", "PH"):
        row = sh.FAM_STEP[s.family][D]
        lr = row["L"]
    elif s.family in sh.FAM_TAP:
        lr = sh.FAM_TAP[s.family][D][0]
    else:
        lr = sh.D_TABLE[D][3] if s.tolerance_class == "f8" else sh.D_TABLE[D][2]
    R.true(f"L inside the table range {lr[0]}-{lr[1]}", lr[0] <= L <= lr[1], f"{S} p.{page}")
    if s.family == "straight" and not s.flats:
        R.num("volume = pi (D/2)^2 L", math.pi * (D / 2) ** 2 * L, body["volume_mm3"], 0.0005 * math.pi * (D / 2) ** 2 * L, "derived")
    if s.F or s.T:
        row = sh.FAM_STEP[s.family][D]
        R.true(f"step diameter P{s.P:g} within {row['P'][0]:g}-{row['P'][1]:g}", row["P"][0] <= s.P <= row["P"][1], f"S30 p.{page} P column")
        R.true(f"step cylinder face O{s.P:g}", round(s.P / 2, 3) in g, f"S30 p.{page} P")
        R.true("F within 2 <= F <= P x 4", 2 <= s.F <= 4 * s.P, f"S30 p.{page} F column")
        R.true(f"overall length (Y) {total:g} <= {row['Y']:g}", total <= row["Y"], f"S30 p.{page} (Y) Max.")
        xs = sorted(c[0] for c in _planes(faces, 0))
        R.true(f"left step end face at x = {-s.F:g}", any(abs(x + s.F) < 0.005 for x in xs), f"S30 p.{page} F")
        R.true("shoulder face at x = 0", any(abs(x) < 0.005 for x in xs), f"S30 p.{page} L")
        R.true(f"main body ends at x = {L:g}", any(abs(x - L) < 0.005 for x in xs), f"S30 p.{page} L")
        if s.T:
            R.true(f"right step end face at x = {L + s.T:g}", any(abs(x - L - s.T) < 0.005 for x in xs), f"S30 p.{page} T")
    for t in s.taps:
        sel = [x for x in th if x["designation"] == f"M{t['M']:g}"]
        spans = []
        for x in sel:
            a = x["axis"][0]
            p0 = x["axis_point"][0] + a * x["start"]
            p1 = x["axis_point"][0] + a * x["end"]
            spans.append((min(p0, p1), max(p0, p1)))
        exp = tuple(sorted((t["face"], t["face"] + t["dir"] * t["depth"])))
        R.true(f"{t['label']} end: M{t['M']:g} thread, depth {t['depth']:g}, x {exp[0]:g}..{exp[1]:g}",
               any(abs(a - exp[0]) < 0.02 and abs(b - exp[1]) < 0.02 for a, b in spans), f"{S} p.{page} M{' / N' if len(s.taps) > 1 else ''} selection",
               "tap depth M x 2 (MD: M x 3)")
    for i, f in enumerate(s.flats):
        tag = f"flat {i + 1}"
        ax = 1 if f["axis"] == "Y" else 2
        px = _planes(faces, ax)
        r0 = f["r"]
        cs = [c for c in px if f["x0"] - 0.01 <= c[0] <= f["x1"] + 0.01]
        if f["kind"] == "sc":
            ys = sorted(c[ax] for c in cs)
            R.eq(f"{tag}: wrench flat faces (pair)", 2, len(cs), f"{S} p.{page} SC/WSC/SX")
            if len(ys) == 2:
                R.num(f"{tag}: width across flats W", f["across"], ys[1] - ys[0], 0.005, "S8 p.432 W table")
        else:
            R.eq(f"{tag}: flat face", 1, len(cs), f"{S} p.{page} FC/WFC/LFC")
            if cs:
                R.num(f"{tag}: flat depth H", f["depth"], r0 - cs[0][ax], 0.005, f"{S} p.{page} H table")
        walls = sorted(c[0] for c in _planes(faces, 0) if abs(c[0]) > 0.01 and abs(c[0] - L) > 0.01)
        R.true(f"{tag}: start x = {f['x0']:g}", any(abs(x - f["x0"]) < 0.005 for x in walls) or abs(f["x0"]) < 1e-9, f"{S} p.{page} SC/FC/A")
        R.true(f"{tag}: end x = {f['x1']:g}", any(abs(x - f["x1"]) < 0.005 for x in walls) or abs(f["x1"] - L) < 1e-9, f"{S} p.{page} l1/FC")
    R.eq("part number metadata", s.code, (r[3].get("metadata") or r[3]).get("part_number"), "-")
    R.eq("design part number", s.code, find_key(r[4], "part_number"), "-")
    return R
