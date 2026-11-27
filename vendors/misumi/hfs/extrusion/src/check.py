"""Spec check for the MISUMI extrusions (5 series 2020/2040/4040, 6 series 3030): measures the built part with
SolidCraft's inspect commands and compares every dimension with the catalogue value (sources.toml ids).

Section properties against the printed table (sources.toml rows 1900-1999): the cross-section area is the end-face area measured
by SolidCraft; the polar moment Ix + Iy comes from SolidCraft's inertia tensor (component.properties, plain codes only); Ix and Iy
separately are computed from the profile geometry (profiles.expected_moments), because SolidCraft's tensor of a long bar carries the
A L^2 / 12 term, which swamps a section moment of a few 10^3 mm4. The catalogue prints area to 3 significant figures and moments to
3, so the area band is 0.3 % (never below half a unit of the last printed digit) and the moment band 1 %."""
from __future__ import annotations
import json, math
from runtime.check import Rows, run_measure, cyl_groups, uniq, find_key
from runtime.sc import slug
from . import ext, profiles as pr

ASSUMED_DENSITY = 2.71   # g/cm3: aluminium extrusion alloys (A6063, A6N01); implied by the printed mass/area pairs, see sources.toml

def _dist(B, p, q):
    return {"command": "inspect.measure", "params": {"items": [{"type": "face", "body": B, "point": p}, {"type": "face", "body": B, "point": q}]}}

def clear_x(e):
    """An x where no tap or wrench hole touches, to probe the plain section."""
    busy = []
    if "L" in e.end_tap: busy.append((0, e.spec.tap[1] + 1))
    if "R" in e.end_tap: busy.append((e.length - e.spec.tap[1] - 1, e.length))
    for s in e.wrench:
        for x in ext.wrench_positions(e, s): busy.append((x - e.wrench_d / 2 - 1, x + e.wrench_d / 2 + 1))
    for step in range(int(e.length)):
        c = e.length / 2 + (step // 2 + 1) * (1 if step % 2 else -1) * 1.0
        if 0 < c < e.length and not any(a <= c <= b for a, b in busy):
            return c
    return e.length / 2

def _w(x, p):      # sketch point -> world point at length position x
    return [x, p[0], p[1]]

def probes(e, x):
    """(label, spec, source id, command) distance probes at length position x."""
    sp = e.spec; s = sp.slot; B = e.code
    out = []
    side = "T"; off = sp.slots[side][0]
    sp_ = lambda sd, o, u, v: _w(x, pr.slot_point(sp, sd, o, u, v))
    m, w = s.mouth / 2, s.cavity / 2
    src = sp.page
    out.append(("slot mouth width", s.mouth, f"{src} '{s.mouth:g}'", _dist(B, sp_(side, off, -m, s.lip / 2), sp_(side, off, m, s.lip / 2))))
    out.append(("slot cavity width", s.cavity, f"{src} '{s.cavity:g}'", _dist(B, sp_(side, off, -w, (s.lip + s.d0) / 2), sp_(side, off, w, (s.lip + s.d0) / 2))))
    out.append(("lip thickness", s.lip, f"{src} '{s.lip:g}'", _dist(B, sp_(side, off, m + 1.5, 0.0), sp_(side, off, m + 1.5, s.lip))))
    if sp.key == "4040":
        # bore block 8 wide: left slot floor (x = -14, slot at y = +10) to the block's inner face x = -6
        out.append(("bore block width (slot floor to inner face)", 8.0, f"{src} '8'",
                    _dist(B, sp_("L", -10.0, 0.0, s.depth), _w(x, (-6.0, 11.0)))))
        # web: the slot flank x + y = fc (arm frame, fc = w/2 - depth + 10 - floor_half) to the void's diagonal x + y = fc - 1.5 * sqrt(2), 1.5 labelled
        fc = sp.w / 2 - s.depth + 10.0 - s.floor_half
        d0 = pr.WEB * math.sqrt(2) / 2
        out.append(("web thickness (flank to void)", pr.WEB, f"{src} '1.5'", _dist(B, _w(x, (15.5, fc - 15.5)), _w(x, (15.5 - d0, fc - 15.5 - d0)))))
    elif sp.key == "2040":
        out.append(("bore block width (slot floor to floor)", sp.w - 2 * s.depth, f"{src} '8'",
                    _dist(B, sp_("R", 10.0, 0.0, s.depth), sp_("L", -10.0, 0.0, s.depth))))
    else:
        out.append(("core width (slot floor to floor)", sp.h - 2 * s.depth, f"{src} core",
                    _dist(B, sp_("T", off, 0.0, s.depth), sp_("B", sp.slots["B"][0], 0.0, s.depth))))
    return out

def check(e, sc, out):
    sp = e.spec; s = sp.slot; B = e.code; L = e.length; src = sp.page
    x = clear_x(e)
    pb = probes(e, x)
    endpt = [0, sp.w / 2 - 2.0, sp.h / 2 - s.lip / 2]
    cmds = [{"command": "inspect.measure", "params": {}},
            {"command": "model.faces", "params": {"body": B}},
            {"command": "model.threads", "params": {}},
            {"command": "inspect.measure", "params": {"items": [{"type": "face", "body": B, "point": endpt}]}},
            {"command": "component.metadata", "params": {"component": B}},
            {"command": "document.metadata", "params": {}}] + [c for *_, c in pb] + [
            {"command": "component.properties", "params": {"component": B}}]
    r = run_measure(sc, cmds, out, slug(e.code))
    m = r[0]
    faces = r[1]["faces"] if isinstance(r[1], dict) else r[1][0]["faces"]
    th = r[2]["threads"]
    endface = r[3]["items"][0]["area_mm2"]
    cm, dm = r[4], r[5]
    R = Rows()
    body = m["bodies"][0]; bb = body["bbox"]
    R.eq("one closed body", 1, m["body_count"] if body["closed"] else 0, src)
    R.num("overall width (Y)", sp.w, bb["max"][1] - bb["min"][1], 0.005, f"{src} '{sp.w:g}'")
    R.num("overall height (Z)", sp.h, bb["max"][2] - bb["min"][2], 0.005, f"{src} '{sp.h:g}'")
    R.num("length (X)", L, bb["max"][0] - bb["min"][0], 0.005, f"{src} L range", f"spec tol +-{e.tolerance}")
    props = r[6 + len(pb)]
    for (label, spec, sid, _), res in zip(pb, r[6:6 + len(pb)]):
        R.num(label, spec, res["distance_mm"], 0.005, sid)
    # slot depth: the planar floor face of the first top slot against the outer face (from model.faces)
    fp = pr.slot_point(sp, "T", sp.slots["T"][0], 0.0, s.depth)
    fl = [f for f in faces if f.get("plane_normal") and abs(f["plane_normal"][2] - 1) < 1e-6 and abs(f["centroid"][1] - fp[0]) < 0.01 and abs(f["centroid"][2] - fp[1]) < 0.01]
    R.num("slot depth (outer face to floor)", s.depth, (sp.h / 2 - fl[0]["centroid"][2]) if fl else None, 0.005, f"{src} depth '{s.depth:g}'")
    ea = pr.expected_area(sp)
    R.num("cross-section area vs drawing", ea, endface, 0.001 * ea, f"{src} drawing", "area from the dimensions")
    pa = sp.published_area
    tsrc = ("S22" if sp.series == 5 else "S23") + " " + src.split(" ", 1)[1]      # the product table: S22 p.529-530, S23 p.571
    R.num(f"cross-section area vs published {pa:g}", pa, endface, max(0.003 * pa, 0.5), tsrc,
          "published to 3 figures: band 0.3 % of the value, never below half a unit (0.5 mm2)")
    pm = sp.published_mass
    half = 0.05 if abs(pm * 10 - round(pm * 10)) < 1e-9 else 0.005
    R.num(f"mass per metre vs published {pm:g} kg/m", pm, endface * ASSUMED_DENSITY * 1e-3, half, tsrc,
          f"area x {ASSUMED_DENSITY:g} g/cm3 (aluminium extrusion alloy, not printed); band is half a unit of the printed digit")
    ix, iy = pr.expected_moments(sp)
    got = sorted((ix, iy)); pub = sorted(sp.published_i)
    for lab, g_, p_ in (("smaller", got[0], pub[0]), ("larger", got[1], pub[1])):
        R.num(f"moment of inertia ({lab}) of the profile vs published", p_, g_, 0.01 * p_, tsrc,
              "computed from the profile geometry (sources.toml 1900-1999); 1 % band, the table prints 3 figures")
    if not e.end_tap and not e.wrench:
        tot = props.get("total", props) if isinstance(props, dict) else {}
        tens = tot.get("inertia_g_mm2")
        vol, mass = body["volume_mm3"], body.get("mass_g") or m["total"].get("mass_g")
        polar = tens[0][0] * vol / (mass * L) if tens and mass else None
        R.num("polar moment Ix + Iy vs published (SolidCraft inertia tensor)", sum(pub), polar, 0.01 * sum(pub), tsrc,
              "I_xx / (rho L) from component.properties; mesh integral, planar faces exact, bores within 0.1 %")
    g = cyl_groups(faces)
    for bx, by, d in pr.all_bores(sp):
        hits = [(o, a) for (o, a) in g.get(round(d / 2, 3), []) if abs(o[1] - bx) < 0.01 and abs(o[2] - by) < 0.01]
        R.true(f"bore O{d:g} at ({bx:g}, {by:g})", len(hits) >= 1, src)
    n_bore = {}
    for _, _, d in pr.all_bores(sp):
        n_bore[round(d / 2, 3)] = n_bore.get(round(d / 2, 3), 0) + 1
    for rr, cnt in sorted(n_bore.items()):
        got_n = len({(round(o[1], 2), round(o[2], 2)) for o, a in g.get(rr, []) if abs(abs(a[0]) - 1) < 1e-6})
        R.eq(f"bores O{2 * rr:g} (count)", cnt, got_n, src)
    R.eq(f"outer corners R{sp.corner_r:g} (count)", 4, len([1 for o, a in g.get(round(sp.corner_r, 3), []) if abs(abs(a[0]) - 1) < 1e-6]), src, f"'4-R{sp.corner_r:g}'")
    n_tips = 2 * sum(len(v) for v in sp.slots.values())
    R.at_least(f"lip-tip rounds R{s.tip_r:g} (count)", n_tips, len(g.get(round(s.tip_r, 3), [])), f"{src} drawing", "approximate on the 6 series" if sp.series == 6 else "measured")
    if not e.end_tap and not e.wrench:
        R.num("volume = area x L", ea * L, body["volume_mm3"], 0.001 * L * 2, "derived")
    thread, depth = sp.tap
    tapped = [b for b in pr.all_bores(sp) if not (sp.key == "3030" and b[2] != 6.8)]
    if e.end_tap:
        # the modelled hole of a tapped end is the printed pilot bore (the ISO tap drill), the thread on it is cosmetic: sources.toml row 1905
        for bx, by, d in tapped:
            dia = [2 * rr for rr, lst in g.items() for (o, a) in lst if abs(o[1] - bx) < 0.01 and abs(o[2] - by) < 0.01 and abs(abs(a[0]) - 1) < 1e-6]
            R.num(f"tapped bore ({bx:g}, {by:g}): diameter of the {thread} thread's hole = printed pilot bore", d, dia[0] if dia else None, 0.005,
                  f"{'S1' if sp.series == 5 else 'S10'} drawing, S2 p.757", "tap drill, not the nominal thread diameter")
    for side in e.end_tap:
        sel =[t for t in th if (t["start"] < 1 if side == "L" else t["end"] > L - 1) and t["designation"] == thread]
        R.eq(f"tap {side}: {thread} threads present", len(tapped), len(sel), "S2 p.757", f"{len(tapped)} tapped hole(s) per end")
        if sel:
            lens = [t["end"] - t["start"] for t in sel]
            if side in e.wrench:
                R.true(f"tap {side}: depth <= {depth:g} (wrench hole interrupts)", max(lens) <= depth + 0.01, "S2 p.757", f"{max(lens):.2f}")
            else:
                R.num(f"tap {side}: depth", depth, max(lens), 0.01, f"S2 p.757 '{thread} Depth {depth:g}'")
    for side in e.wrench:
        xs = ext.wrench_positions(e, side)
        d = e.wrench_d
        axis = (0, 1, 0) if e.wrench[side]["orient"] == "H" else (0, 0, 1)
        hs = [(o, a) for (o, a) in g.get(round(d / 2, 3), []) if abs(abs(a[1]) - axis[1]) < 1e-6 and abs(abs(a[2]) - axis[2]) < 1e-6]
        R.num(f"wrench {side}: diameter", d, d if hs else None, 0.001, "S3 p.759 'd'")
        got_x = uniq([o[0] for o, a in hs])
        R.eq(f"wrench {side}: hole count", len(xs), len(got_x), "S3 p.759 rows")
        for i, (sx, gx) in enumerate(zip(sorted(xs), got_x)):
            R.num(f"wrench {side}: hole {i + 1} position", sx, gx, 0.005, "S3 p.759 H/J/K from the end")
    R.eq("part number metadata", e.code, (cm.get("metadata") or cm).get("part_number"), "-")
    R.eq("design part number", e.code, find_key(dm, "part_number"), "-")
    return R
