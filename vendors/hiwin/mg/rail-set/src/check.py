"""Spec check of a HIWIN MGN rail set against the MG Series catalogue (S4, S6 in sources.toml).

`check_mgn` judges the dimensioned bodies and is the original check, unchanged. The model also holds appearance bodies (end
caps, end seals, retainer strips, end screws, nipple, rail screws, caps), so `check_mgn_dimensioned` adjusts the measurement it reads
in one place; `check_mgn_appearance` adds rows for what the appearance work derives from catalogue numbers.
"""
from __future__ import annotations
import re
from runtime.check import Rows, run_measure, cyl_groups, uniq, find_key
from runtime.sc import slug
from runtime.appearance import APPX

# -------------------------------------------------------------------------------------------------
def check_mgn(s, sc, out):
    r_, b_ = s.rail, s.block
    cmds = [{"command": "inspect.measure", "params": {}},
            {"command": "model.faces", "params": {"body": "Rail"}},
            {"command": "model.threads", "params": {}},
            {"command": "inspect.interference", "params": {}},
            {"command": "component.metadata", "params": {"component": s.code}},
            {"command": "document.metadata", "params": {}}]
    r = run_measure(sc, cmds, out, slug(s.code))
    bodies = {b["name"]: b for b in r[0]["bodies"]}
    faces = r[1]["faces"]; th = r[2]["threads"]
    R = Rows()
    rb = bodies["Rail"]["bbox"]
    R.eq("bodies: rail + blocks", 1 + s.n_blocks, len(bodies), "S4 2-4-10 code")
    R.num("rail length", s.rail_length, rb["max"][0] - rb["min"][0], 0.005, "S4 p.85")
    R.num("rail width WR", r_["WR"], rb["max"][1] - rb["min"][1], 0.005, "S4 2-4-19")
    R.num("rail height HR", r_["HR"], rb["max"][2] - rb["min"][2], 0.005, "S4 2-4-19")
    g = cyl_groups(faces)
    xs_exp = [s.end_distance + i * r_["P"] for i in range(s.holes)]
    through = uniq([o[0] for o, a in g.get(round(r_["d"] / 2, 3), [])])
    cb = uniq([o[0] for o, a in g.get(round(r_["D"] / 2, 3), [])])
    R.num("rail through-hole diameter d", r_["d"], r_["d"] if through else None, 0.001, "S4 2-4-19")
    R.num("rail counterbore diameter D", r_["D"], r_["D"] if cb else None, 0.001, "S4 2-4-19")
    R.eq("rail hole count", s.holes, len(through), "S4 p.85 L=(n-1)P+2E")
    for i, (ex, gx) in enumerate(zip(xs_exp, through)):
        if i < 2 or i == len(xs_exp) - 1:
            R.num(f"rail hole {i + 1} position", ex, gx, 0.005, "S4 p.85 E, P")
    if len(through) > 1:
        R.num("rail hole pitch P", r_["P"], (through[-1] - through[0]) / (len(through) - 1), 0.005, "S4 p.85")
    cbfloor = [f for f in faces if f.get("plane_normal") and abs(f["plane_normal"][2] - 1) < 1e-6 and abs(f["centroid"][2] - (r_["HR"] - r_["h"])) < 1e-3]
    R.eq("counterbore depth h (floors at HR-h)", s.holes, len(cbfloor), "S4 2-4-19", f"h={r_['h']}")
    for i in range(s.n_blocks):
        nm = f"Block {i + 1}"; bb = bodies[nm]["bbox"]
        R.num(f"{nm} length L", b_["L"], bb["max"][0] - bb["min"][0], 0.005, "S4 2-4-19")
        R.num(f"{nm} width W", b_["W"], bb["max"][1] - bb["min"][1], 0.005, "S4 2-4-19")
        R.num(f"{nm} top height H", b_["H"], bb["max"][2], 0.005, "S4 2-4-19")
        R.num(f"{nm} bottom H1", b_["H1"], bb["min"][2], 0.005, "S4 2-4-19")
        bt = [t for t in th if t["body"] == nm]
        R.eq(f"{nm} mounting threads", 4, len(bt), "S4 2-4-19")
        if bt:
            ys = uniq([t["axis_point"][1] for t in bt]); xs = uniq([t["axis_point"][0] for t in bt])
            R.num(f"{nm} hole spacing B", b_["B"], ys[-1] - ys[0], 0.005, "S4 2-4-19")
            R.num(f"{nm} hole spacing C", b_["C"], xs[-1] - xs[0], 0.005, "S4 2-4-19")
            R.eq(f"{nm} thread {b_['M']} depth", b_["M_depth"], round(bt[0]["end"] - bt[0]["start"], 3), "S4 2-4-19")
    R.eq("rail/block interference count", 0, r[3]["count"], "-")
    R.eq("part number metadata", s.code, (r[4].get("metadata") or r[4]).get("part_number"), "-")
    R.eq("design part number", s.code, find_key(r[5], "part_number"), "-")
    return R


# -------------------------------------------------------------------------------------------------
# HIWIN MGN with appearance: check_mgn above is unchanged and judges the DIMENSIONED bodies. The model now also holds
# appearance bodies (end caps, end seals, retainer strips, end screws, nipple, rail screws), so the measurement check_mgn
# sees is adjusted in one place: appearance and screw bodies leave the body list, and each block's steel body takes the
# length of its steel body + end caps + end seals (the catalogue's L, which is what the row compares).
def _is_appearance(name):
        return name.endswith(APPX) or name.startswith("Body")

def check_mgn_dimensioned(s, sc, out):
    import re
    real = run_measure
    def wrapped(sc_path, cmds, out_dir, name):
        res = real(sc_path, cmds, out_dir, name)
        bodies = res[0]["bodies"]
        keep = []
        for b in bodies:
            if _is_appearance(b["name"]):
                continue
            keep.append(b)
        for b in keep:
            m = re.fullmatch(r"Block \d+", b["name"])
            if m:
                parts = [x for x in bodies if x["name"].startswith(b["name"] + " ") and re.search(r"end (cap|seal) ", x["name"])]
                xs = [b["bbox"]["min"][0]] + [x["bbox"]["min"][0] for x in parts]
                xe = [b["bbox"]["max"][0]] + [x["bbox"]["max"][0] for x in parts]
                b["bbox"] = {"min": [min(xs)] + b["bbox"]["min"][1:], "max": [max(xe)] + b["bbox"]["max"][1:]}
        res[0]["bodies"] = keep; res[0]["body_count"] = len(keep)
        return res
    globals()["run_measure"] = wrapped
    try:
        return check_mgn(s, sc, out)
    finally:
        globals()["run_measure"] = real

def check_mgn_appearance(s, sc, out, R=None):
    """Rows for what the appearance work adds: catalogue-derived ones (L Max, lube hole, nipple) and the appearance ones."""
    from .build import APPX, look, appearance_sizes, CAP_LOOK, SEAL_LOOK
    k = look(s); a = appearance_sizes(s); b_ = s.block; r_ = s.rail
    cmds = [{"command": "inspect.measure", "params": {}},
            {"command": "model.faces", "params": {"body": "Rail"}},
            {"command": "inspect.interference", "params": {}},
            {"command": "appearance.list", "params": {}},
            {"command": "component.metadata", "params": {"component": s.code}}]
    for i in range(s.n_blocks):
        cmds.append({"command": "model.faces", "params": {"body": f"Block {i + 1} end cap A {APPX}"}})
        cmds.append({"command": "appearance.list", "params": {"body": f"Block {i + 1} end cap A {APPX}"}})
        cmds.append({"command": "appearance.list", "params": {"body": f"Block {i + 1} end seal A {APPX}"}})
    r = run_measure(sc, cmds, out, slug(s.code) + ".look")
    bodies = {b["name"]: b for b in r[0]["bodies"]}
    R = R or Rows()
    app = [n for n in bodies if n.endswith(APPX) and not n.startswith("Rail cap ")]
    capn = [n for n in bodies if n.startswith("Rail cap ")]
    screws = [n for n in bodies if n.startswith("Body")]
    R.true("appearance bodies all named '(appearance, approximate)'", all(n.endswith(APPX) for n in bodies if n != "Rail" and not n.startswith(("Block ", "Body")) or n.startswith("Block ") and n.count(" ") > 1), "-")
    per_block = 2 + 2 + 2 + 4 + 1 + (1 if k["G"] else 0)     # + the top insert
    R.eq("appearance bodies per block (2 caps, 2 seals, 2 retainers, 4 end screws" + (", nipple)" if k["G"] else ")"), per_block * s.n_blocks, len(app), "-")
    R.eq("rail screws (one per rail hole)", s.holes, len(screws), "S4 2-4-19 bolt " + r_["bolt"])
    if capn:
        from .build import CAP_SIZES
        cs = CAP_SIZES[s.size]
        R.eq("rail hole caps (one per hole)", s.holes, len(capn), "S4 Table 2-4-9")
        zs = [(bodies[n]["bbox"]["min"][2], bodies[n]["bbox"]["max"][2]) for n in capn]
        R.num("rail hole cap thickness H", cs["H"], max(z[1] - z[0] for z in zs), 0.005, "S4 Table 2-4-9", "diameter = counterbore D (cap O6.15 is a press fit)")
        R.num("rail hole caps flush with the rail top", r_["HR"], min(z[1] for z in zs), 0.005, "S4 Table 2-4-9")
    for i in range(s.n_blocks):
        nm = f"Block {i + 1}"
        ti = bodies[f"{nm} top insert {APPX}"]["bbox"]
        R.num(f"{nm} top insert flush with block top H", b_["H"], ti["max"][2], 0.005, "S4 2-4-19", "appearance, approximate")
        steel = bodies[nm]["bbox"]
        parts = [bodies[n]["bbox"] for n in bodies if n.startswith(nm + " end ") and ("cap" in n or "seal" in n)]
        lo = min([steel["min"][0]] + [p["min"][0] for p in parts]); hi = max([steel["max"][0]] + [p["max"][0] for p in parts])
        R.num(f"{nm} steel body length L1", b_["L1"], steel["max"][0] - steel["min"][0], 0.005, "S4 2-4-19")
        R.num(f"{nm} body + end caps + end seals = L", b_["L"], hi - lo, 0.005, "S4 2-4-19")
        sc_ = [bodies[n]["bbox"] for n in bodies if n.startswith(nm + " end screw ")]
        R.num(f"{nm} overall with end screws = L Max", k["Lmax"], max(p["max"][0] for p in sc_) - min(p["min"][0] for p in sc_), 0.005, "S4 2-4-19 L Max")
        if k["G"]:
            nn = bodies[f"{nm} grease nipple {APPX}"]["bbox"]
            R.num(f"{nm} grease nipple projection G", k["G"], nn["max"][0] - nn["min"][0], 0.005, "S4 2-4-19 G", "from the end-seal face")
            R.num(f"{nm} grease nipple height H2 below top", k["H2"], b_["H"] - (nn["max"][2] + nn["min"][2]) / 2, 0.005, "S4 2-4-19 H2")
        else:
            f = r[5 + 3 * i]["faces"]; g = cyl_groups(f).get(round(k["Gn"] / 2, 3), [])
            R.num(f"{nm} lube hole diameter Gn", k["Gn"], k["Gn"] if g else None, 0.001, "S4 2-4-19 Gn")
            R.num(f"{nm} lube hole height H2 below top", k["H2"], b_["H"] - g[0][0][2] if g else None, 0.005, "S4 2-4-19 H2")
        cap = r[6 + 3 * i]["body"]["appearance"]; seal = r[7 + 3 * i]["body"]["appearance"]
        R.eq(f"{nm} end cap appearance", CAP_LOOK, cap["name"], "photo", "appearance, approximate")
        R.eq(f"{nm} end seal appearance", SEAL_LOOK, seal["name"], "photo", "appearance, approximate")
        R.eq(f"{nm} end cap material", "ABS Plastic", bodies[f"{nm} end cap A {APPX}"]["material"], "-", "appearance, approximate")
    grooves = cyl_groups(r[1]["faces"]).get(a["groove_r"], [])
    R.eq("rail side ball grooves (2, one per side)", 2, len(uniq([round(o[1], 3) for o, a in grooves])), "S4 p.76 drawing", "appearance, approximate")
    R.true("rail material assigned", bodies["Rail"]["material"] in ("Steel", "Stainless Steel"), "-")
    R.eq("rail/block/screw interference count (all bodies)", 0, r[2]["count"], "-")
    desc = (r[4].get("metadata") or r[4]).get("description", "")
    R.true("description has DIMENSIONED and APPEARANCE sections", "DIMENSIONED" in desc and "approximate, not a catalogue dimension" in desc, "-")
    return R

def check(part, sc, out):
    R = check_mgn_dimensioned(part, sc, out)
    check_mgn_appearance(part, sc, out, R)
    check_finishes(part, sc, out, R)
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
    bodies = (["Rail"] if getattr(s, "kind", "set") != "block" else []) + ([f"Block {i + 1}" for i in range(s.n_blocks)] if getattr(s, "kind", "set") != "rail" else [])
    res = run_measure(sc, [{"command": "model.faces", "params": {"body": bd}} for bd in bodies], out, slug(s.code) + ".finish")
    centres = block_centres(s) if getattr(s, "kind", "set") != "rail" else []
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
