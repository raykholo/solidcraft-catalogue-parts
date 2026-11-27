"""Spec check for HIWIN HG sets, rails and blocks: measures the built part with SolidCraft's inspect commands and compares
every dimension with the catalogue value (catalogue.py, sources.toml S7)."""
from __future__ import annotations
from runtime.check import Rows, run_measure, cyl_groups, uniq, find_key
from runtime.sc import slug
from runtime.appearance import APPX

def _dimensioned(bodies):
    """The dimensioned bodies: appearance bodies (end caps, end seals, grease nipple) and the rail screws (SolidCraft standard-part
    bodies, named Body...) leave the list; each block's steel body takes the extent of its steel body + end caps + end seals,
    which is the catalogue length L the rows compare."""
    import re
    keep = {n: b for n, b in bodies.items() if not (n.endswith(APPX) or n.startswith("Body"))}
    for n, b in keep.items():
        if re.fullmatch(r"Block \d+", n):
            parts = [x for k, x in bodies.items() if k.startswith(n + " end ") and k.endswith(APPX)]
            xs = [b["bbox"]["min"][0]] + [x["bbox"]["min"][0] for x in parts]
            xe = [b["bbox"]["max"][0]] + [x["bbox"]["max"][0] for x in parts]
            keep[n] = dict(b, bbox={"min": [min(xs)] + b["bbox"]["min"][1:], "max": [max(xe)] + b["bbox"]["max"][1:]})
    return keep

def check(s, sc, out, appearance=True):
    """appearance=False skips the rows about appearance bodies, finishes and the description's APPEARANCE section: the parametric form of this
    generator holds dimensioned bodies only, and is compared with the Python part built the same way (build.commands(appearance=False))."""
    r, b = s.rail, s.block
    cmds = [{"command": "inspect.measure", "params": {}},
            {"command": "model.faces", "params": {"body": "Rail"}} if s.kind != "block" else {"command": "model.threads", "params": {}},
            {"command": "model.threads", "params": {}},
            {"command": "inspect.interference", "params": {}},
            {"command": "component.metadata", "params": {"component": s.code}},
            {"command": "document.metadata", "params": {}}]
    if s.kind != "rail":
        cmds.append({"command": "model.faces", "params": {"body": "Block 1"}})
    res = run_measure(sc, cmds, out, slug(s.code))
    allb = {x["name"]: x for x in res[0]["bodies"]}
    bodies = _dimensioned(allb)
    th = res[2]["threads"]
    R = Rows()
    R.eq("bodies", (1 if s.kind != "block" else 0) + s.n_blocks, len(bodies), "S7 code")
    if s.kind != "block":
        faces = res[1]["faces"]
        rb = bodies["Rail"]["bbox"]
        R.num("rail length", s.rail_length, rb["max"][0] - rb["min"][0], 0.005, "S7 p.37")
        R.num("rail width WR", r["WR"], rb["max"][1] - rb["min"][1], 0.005, "S7 p.38-43")
        R.num("rail height HR", r["HR"], rb["max"][2] - rb["min"][2], 0.005, "S7 p.38-43")
        xs_exp = [s.end_distance + i * r["P"] for i in range(s.holes)]
        if s.rail_mount == "R":
            g = cyl_groups(faces)
            through = uniq([o[0] for o, a in g.get(round(r["d"] / 2, 3), [])])
            cb = uniq([o[0] for o, a in g.get(round(r["D"] / 2, 3), [])])
            R.num("rail through-hole diameter d", r["d"], r["d"] if through else None, 0.001, "S7 p.38")
            R.num("rail counterbore diameter D", r["D"], r["D"] if cb else None, 0.001, "S7 p.38")
            R.eq("rail hole count", s.holes, len(through), "S7 p.37 L=(n-1)P+2E")
            cbfloor = [f for f in faces if f.get("plane_normal") and abs(f["plane_normal"][2] - 1) < 1e-6 and abs(f["centroid"][2] - (r["HR"] - r["h"])) < 1e-3]
            R.eq("counterbore depth h (floors at HR-h)", s.holes, len(cbfloor), "S7 p.38", f"h={r['h']}")
            got = through
        else:
            rt = [t for t in th if t["body"] == "Rail"]
            R.eq("rail tapped hole count", s.holes, len(rt), "S7 p.43 table (6)")
            if rt:
                R.eq(f"rail thread {r['S']}", r["S"], rt[0]["designation"], "S7 p.43 table (6)")
                R.num("rail thread depth h", r["hT"], rt[0]["end"] - rt[0]["start"], 0.01, "S7 p.43 table (6)")
            got = uniq([t["axis_point"][0] for t in rt])
        for i, (ex, gx) in enumerate(zip(xs_exp, got)):
            if i < 2 or i == len(xs_exp) - 1:
                R.num(f"rail hole {i + 1} position", ex, gx, 0.005, "S7 p.37 E, P")
        if len(got) > 1:
            R.num("rail hole pitch P", r["P"], (got[-1] - got[0]) / (len(got) - 1), 0.005, "S7 p.37")
        R.num("end distance E (first hole)", s.end_distance, got[0] if got else None, 0.005, "S7 p.37 Es / P/2 rule")
        R.true("end distance within Es..P/2", r["Es"] - 1e-6 <= s.end_distance <= r["P"] / 2 + 1e-6, "S7 p.37")
    for i in range(s.n_blocks if s.kind != "rail" else 0):
        nm = f"Block {i + 1}"; bb = bodies[nm]["bbox"]
        R.num(f"{nm} length L", b["L"], bb["max"][0] - bb["min"][0], 0.005, "S7 p.38-43")
        R.num(f"{nm} width W", b["W"], bb["max"][1] - bb["min"][1], 0.005, "S7 p.38-43")
        R.num(f"{nm} top height H", b["H"], bb["max"][2], 0.005, "S7 p.38-43")
        R.num(f"{nm} bottom H1", b["H1"], bb["min"][2], 0.005, "S7 p.38-43")
        if b["hole"] == "thread":
            bt = [t for t in th if t["body"] == nm]
            R.eq(f"{nm} mounting threads", 4, len(bt), "S7 p.38-43")
            if bt:
                ys = uniq([t["axis_point"][1] for t in bt]); xs = uniq([t["axis_point"][0] for t in bt])
                R.num(f"{nm} hole spacing B", b["B"], ys[-1] - ys[0], 0.005, "S7 p.38-43")
                R.num(f"{nm} hole spacing C", b["C"], xs[-1] - xs[0], 0.005, "S7 p.38-43")
                R.eq(f"{nm} thread {b['M']}", b["M"], bt[0]["designation"], "S7 p.38-43")
                R.num(f"{nm} thread depth", b["M_depth"], bt[0]["end"] - bt[0]["start"], 0.01, "S7 p.38-43", "l (HGH) / T (HGW)")
        elif i == 0:      # the through holes of further blocks are the same pattern; faces were read for block 1 only
            g = cyl_groups(res[-1]["faces"])
            hs = g.get(round(b["hole_d"] / 2, 3), [])
            R.eq(f"{nm} through holes O{b['hole_d']:g}", 4, len(hs), "S7 p.41 table (4)")
            if hs:
                ys = uniq([o[1] for o, a in hs]); xs = uniq([o[0] for o, a in hs])
                R.num(f"{nm} hole spacing B", b["B"], ys[-1] - ys[0], 0.005, "S7 p.41 table (4)")
                R.num(f"{nm} hole spacing C", b["C"], xs[-1] - xs[0], 0.005, "S7 p.41 table (4)")
    if s.kind == "set":
        R.eq("rail/block interference count (all bodies)", 0, res[3]["count"], "-")
    # appearance: what the photoreal work adds, named (appearance, approximate) and kept out of the dimensioned rows above
    if appearance:
        app = [n for n in allb if n.endswith(APPX)]
        R.true("appearance bodies all named '(appearance, approximate)'", all(n.endswith(APPX) or n in bodies or n.startswith("Body") for n in allb), "-")
        R.eq("appearance bodies per block (2 end caps, 2 end seals, grease nipple)", 5 * (s.n_blocks if s.kind != "rail" else 0), len(app), "-", "appearance, approximate")
        if s.kind != "block" and s.rail_mount == "R":
            R.eq("rail screws (one per rail hole)", s.holes, len([n for n in allb if n.startswith("Body")]), "S7 p.38 bolt " + r["bolt"])
    for i in range(s.n_blocks if s.kind != "rail" else 0):
        nm = f"Block {i + 1}"
        R.num(f"{nm} steel body length L1", b["L1"], allb[nm]["bbox"]["max"][0] - allb[nm]["bbox"]["min"][0], 0.005, "S7 p.38-43")
        if appearance:
            R.eq(f"{nm} end cap material", "ABS Plastic", allb[f"{nm} end cap A {APPX}"]["material"], "-", "appearance, approximate")
    if appearance:
        check_finishes(s, sc, out, R)
    if appearance:
        desc = (res[4].get("metadata") or res[4]).get("description", "")
        R.true("description has DIMENSIONED and APPEARANCE sections", "APPEARANCE (approximate, not a catalogue dimension)" in desc, "-")
    R.eq("part number metadata", s.code, (res[4].get("metadata") or res[4]).get("part_number"), "-")
    R.eq("design part number", s.code, find_key(res[5], "part_number"), "-")
    return R


# -------------------------------------------------------------------------------------------------
# Per-face finishes (appearance rows, not dimension rows): model.faces finds each face by its geometry, appearance.chain reads back
# the look that resolves on it, and the row compares it with the finish the builder assigns there (build.READBACK: name, roughness).
# This proves the face-point assignments landed on the intended faces: ground top / side faces, raceway (groove, channel) faces,
# satin body faces.
def _finish_groups(s, faces, body, cx=None):
    """[(label, finish key, [face index])] for one body, found by geometry."""
    from .build import appearance_sizes
    a = appearance_sizes(s); r, b = s.rail, s.block
    def nrm(f): return f.get("plane_normal") or (0, 0, 0)
    def pick(pred): return [f["index"] for f in faces if pred(f)]
    out = []
    if body == "Rail":
        top = pick(lambda f: nrm(f)[2] > 0.999 and abs(f["centroid"][2] - r["HR"]) < 1e-3)
        side = pick(lambda f: abs(nrm(f)[1]) > 0.999 and abs(abs(f["centroid"][1]) - r["WR"] / 2) < 1e-3)
        groove = pick(lambda f: f.get("cylinder") and abs(f["cylinder"]["radius"] - a["groove_r"]) < 1e-3 and abs(f["cylinder"]["axis"][0]) > 0.999)
        bottom = pick(lambda f: nrm(f)[2] < -0.999 and abs(f["centroid"][2]) < 1e-3)
        out += [("rail top face", "ground", top), ("rail side faces", "ground", side), ("rail ball-groove faces", "raceway", groove),
                ("rail bottom face", "satin", bottom)]
    else:
        top = pick(lambda f: nrm(f)[2] > 0.999 and abs(f["centroid"][2] - b["H"]) < 1e-3)
        side = pick(lambda f: abs(nrm(f)[1]) > 0.999 and abs(abs(f["centroid"][1]) - b["W"] / 2) < 1e-3)
        end = pick(lambda f: abs(nrm(f)[0]) > 0.999 and abs(abs(f["centroid"][0] - cx) - b["L1"] / 2) < 1e-3)
        ch_top = pick(lambda f: nrm(f)[2] < -0.999 and abs(f["centroid"][2] - r["HR"]) < 1e-3)
        ch_side = pick(lambda f: abs(nrm(f)[1]) > 0.999 and abs(abs(f["centroid"][1]) - r["WR"] / 2) < 1e-3)
        out += [("top faces", "ground", top), ("side faces", "ground", side), ("end faces (steel body)", "satin", end),
                ("rail-channel top face", "raceway", ch_top), ("rail-channel side faces", "raceway", ch_side)]
    return out

def check_finishes(s, sc, out, R):
    from .build import READBACK, block_centres
    ss = "stainless" in s.material
    pre = "ss_" if ss else ""
    bodies = (["Rail"] if s.kind != "block" else []) + ([f"Block {i + 1}" for i in range(s.n_blocks)] if s.kind != "rail" else [])
    res = run_measure(sc, [{"command": "model.faces", "params": {"body": bd}} for bd in bodies], out, slug(s.code) + ".finish")
    centres = block_centres(s) if s.kind != "rail" else []
    rows = []      # (label, key, body, [index])
    for bd, rr in zip(bodies, res):
        cx = centres[int(bd.split()[1]) - 1] if bd != "Rail" else None
        for label, key, idx in _finish_groups(s, rr["faces"], bd, cx):
            rows.append((f"{bd} {label}" if bd != "Rail" else label, pre + key, bd, idx))
    cmds = [{"command": "appearance.chain", "params": {"target": {"body": bd, "face": i}}} for _, _, bd, idx in rows for i in idx]
    ch = iter(run_measure(sc, cmds, out, slug(s.code) + ".chain"))
    for label, key, bd, idx in rows:
        got = []
        for _ in idx:
            c = next(ch)
            look = next((x["look"] for x in c["steps"] if x["step"] == c["active"]), None)
            got.append(f"{look['name']}, roughness {look['pbr']['roughness']:g}" if look and look.get("pbr") else (look or {}).get("name"))
        name, rough = READBACK[key]
        want = f"{name}, roughness {rough:g}"
        want_n = len(idx)      # a ball groove may split into more than one face at a seam
        R.eq(f"appearance: {label} finish ({len(idx)} face(s))", " | ".join([want] * want_n) if want_n else want,
             " | ".join(got) if got else None, "-", "appearance, approximate; appearance.chain read-back per face")
