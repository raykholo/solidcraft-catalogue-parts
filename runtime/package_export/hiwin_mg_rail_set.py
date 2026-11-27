"""hiwin.mg.rail-set as a generator package: the MGN7 / 9 / 12 / 15 miniature rail with N blocks (S4, sections 2-4-10, 2-4-17, 2-4-19).

Everything the Python generator computes from the code is said in variables, rules and steps: the hole count and end distance
(L = (n - 1) P + 2 E), the block centres, the appearance sizes (with Python's own round-half-even), the part description. The rail
holes are one `solid.pattern.rectangular`; the two grooves, the four mounting points, the two screws and two retainer strips of a block are
`repeat` steps; the rail caps are a `repeat` step. A group of commands that repeats (a block) cannot be a `repeat`, so the four possible
blocks are four copies of the block steps, each under `when n_blocks > i` (spec gap 6). The two lists a command takes as one array (the
rail screw positions, the cap body names) are built by `x-lists` (spec gap 13).

The tables are data/rails.csv (with the cap size of data/caps.csv and the two halves of the bolt designation as derived columns) and
data/blocks.csv (blank lube / nipple cells as 0)."""
from __future__ import annotations
from runtime.table import read_csv, num
from . import table

APPX = "(appearance, approximate)"
BLOCK_GAP = 10
MAXBLOCKS = 4

def code_with_options(code, opts):
    """`MGN12H2R300Z0C caps` in codes.txt: the build option `caps` (bolt caps in the rail holes) is a trailing word of the package code,
    because a package takes nothing but the code."""
    return code + (" caps" if opts.get("caps") else "")

def python_args(code):
    """The inverse for tools/package-equiv's sweep: a package code -> (code, options) for the Python generator."""
    return (code[:-5], {"caps": True}) if code.endswith(" caps") else (code, {})

# ---- the catalogue tables ---------------------------------------------------------------------------------------------
def _n(v):
    return 0.0 if v is None else float(v)

def tables(gen):
    data = gen.dir / "data"
    rails, blocks, caps = read_csv(data / "rails.csv"), read_csv(data / "blocks.csv"), {r["size"]: r for r in read_csv(data / "caps.csv")}
    rrows = []
    for r in rails:
        mth, _, ln = r["bolt"].partition("x")
        c = caps.get(r["size"])
        page = r["page"] + (f"; {c['page']} (cap_d, cap_h)" if c else "")
        rrows.append([r["size"], num(r["WR"]), num(r["HR"]), num(r["D"]), num(r["h"]), num(r["d"]), num(r["P"]), num(r["Es"]), num(r["max_std"]),
                      num(r["max_len"]), r["bolt"], mth, num(ln), num(c["D"]) if c else 0, num(c["H"]) if c else 0, r["source"], page, r["status"],
                      "bolt_m and bolt_len are the two halves of bolt; cap_d and cap_h are the row of data/caps.csv for this size (0 = the catalogue lists no "
                      "bolt caps); both derived by tools/export-package"])
    rh = ["size", "WR", "HR", "D", "h", "d", "P", "Es", "max_std", "max_len", "bolt", "bolt_m", "bolt_len", "cap_d", "cap_h", "source", "page", "status", "note"]
    rt = {c: "number" for c in rh}
    rt.update(size="text", bolt="text", bolt_m="text", source="text", page="text", status="text", note="text")
    brows = []
    for r in blocks:
        brows.append([r["size"], r["block"], *(num(r[c]) for c in ("H", "H1", "N", "W", "B", "C", "L1", "L")), r["M"], num(r["M_depth"]),
                      *(_n(num(r[c])) for c in ("Lmax", "H2", "Gn", "G")), r["source"], r["page"], r["status"],
                      "Gn and G are 0 where the cell of data/blocks.csv is blank (the catalogue has a lube hole or a grease nipple, not both)"])
    bh = ["size", "block", "H", "H1", "N", "W", "B", "C", "L1", "L", "M", "M_depth", "Lmax", "H2", "Gn", "G", "source", "page", "status", "note"]
    bt = {c: "number" for c in bh}
    bt.update(size="text", block="text", M="text", source="text", page="text", status="text", note="text")
    return {"rails": table(rt, ["size"], rh, rrows), "blocks": table(bt, ["size", "block"], bh, brows)}

# ---- expressions ------------------------------------------------------------------------------------------------------
def rnd(name, x, digits):
    """Python's round(x, digits) (half to even) as two variables: the spec has `round(x)` to a whole number only."""
    k = 10 ** digits
    return [{"name": name + "_t", "expr": f"({x}) * {k}"},
            {"name": name, "expr": f"(floor({name}_t) + ({name}_t - floor({name}_t) > 0.5 || ({name}_t - floor({name}_t) == 0.5 && floor({name}_t) % 2 == 1) ? 1 : 0)) / {k}"}]

def lit(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

def e(x):
    return ("e", x)

def cat(prefix, parts):
    """A long text as variables of at most 480 characters each, then one concat: the expression language has a 512 character limit."""
    chunks, cur, size = [], [], 0
    for p in parts:
        t = lit(p) if isinstance(p, str) else p[1]
        if cur and size + len(t) > 460:
            chunks.append(cur); cur, size = [], 0
        cur.append(t); size += len(t) + 2
    chunks.append(cur)
    vs = [{"name": f"{prefix}{i}", "expr": "concat(" + ", ".join(c) + ")"} for i, c in enumerate(chunks)]
    vs.append({"name": prefix, "expr": "concat(" + ", ".join(v["name"] for v in vs) + ")"})
    return vs

# ---- the description (build.description, with every appearance part and the screws) ------------------------------------
def description():
    p1 = ["HIWIN MGN", e("size"), e("block"), " linear guide set: rail MGNR", e("size"), " L=", e("length"), " mm (", e("holes"),
          " holes, end distance ", e("end_d"), " mm) with ", e("n_blocks"), " block(s).\nDIMENSIONED (catalogue values, HIWIN MG Series catalogue G99TE24-2410): rail ",
          e("r.WR"), " x ", e("r.HR"), " mm, counterbored holes O", e("r.D"), " x ", e("r.h"), " deep, through O", e("r.d"), ", pitch ", e("r.P"),
          "; block ", e("b.W"), " wide, ", e("b.L"), " long with end seals (steel body ", e("b.L1"), "), H ", e("b.H"), ", H1 ", e("b.H1"),
          ", four ", e("b.M"), "x", e("b.M_depth"), " threads at B ", e("b.B"), " x C ", e("b.C"), "; ", e("lube"), "; L Max ", e("b.Lmax"),
          " mm. The 10 mm gap between blocks is an illustration choice."]
    p2 = ["\nAPPEARANCE (approximate, not a catalogue dimension; shapes from HIWIN's published drawings and photo): rail top chamfers (", e("rch"),
          " mm) and two side ball grooves (radius ", e("grr"), " mm, a circular approximation of the groove, which the catalogue does not dimension); "
          "block top chamfers; a black top insert 0.2 mm deep between the mounting holes (HIWIN's photo shows a black middle band between metal ends); "
          "plastic end caps (", e("capw"), " mm) and end seals (", e("seal"), " mm) per end, the cap / seal split is an estimate; retainer strips; "
          "two cross-head end screws per end; the grease nipple shape. All these bodies are named '" + APPX + "'.",
          e('caps == "caps" ? concat(" Bolt caps in the rail holes: catalogue O", r.cap_d, " x ", r.cap_h, " thick (Table 2-4-9, a press fit), modelled flush at the counterbore diameter.") : ""'),
          " Rail screws: ISO 4762 ", e("r.bolt"), " from SolidCraft's standard parts (the catalogue gives the bolt size, not the screw model)."]
    return cat("desc", p1 + p2)

# ---- steps ------------------------------------------------------------------------------------------------------------
def S(command, params=None, when=None, repeat=None):
    s = {"command": command}
    if params is not None: s["params"] = params
    if when: s["when"] = when
    if repeat: s["repeat"] = {"var": repeat[0], "count": repeat[1], "max": repeat[2]}
    return s

def T(x):
    return "${" + x + "}"

BLACK_OXIDE = {"color": "#232427", "name": "Steel - Black oxide " + APPX, "pbr": {"metallic": 0.9, "roughness": 0.45, "dielectric_ior": 1.5}}
CAP_PBR = {"color": "#349650", "name": "ABS - Green", "pbr": {"metallic": 0.0, "roughness": 0.45, "dielectric_ior": 1.5}}
SEAL_PBR = {"color": "#c42828", "name": "ABS - Red", "pbr": {"metallic": 0.0, "roughness": 0.55, "dielectric_ior": 1.5}}
INSERT_LOOK = {"appearance": "starter.plastic.tpu-matte-black"}
BRASS = {"appearance": "starter.metal.brass-champagne"}
STAINLESS = {"appearance": "starter.metal.stainless-soft-satin"}
RACEWAY = {"appearance": "starter.metal.silver-cool"}
PLANE = lambda z: {"origin": [0, 0, T(z)], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}

def block_steps(i):
    nm, cx, w = f"Block {i + 1}", f"cx{i}", f"n_blocks > {i}"
    x0 = f"{cx} - b.L1 / 2"
    A = APPX
    st = []
    add = lambda *a, **k: st.append(S(*a, when=k.pop("when", w), **k))
    add("solid.box", {"length": T("b.L1"), "width": T("b.W"), "height": T("b.H - b.H1"), "corner": [T(x0), T("-b.W / 2"), T("b.H1")],
                      "operation": "new", "body_name": nm, "name": nm})
    add("solid.chamfer", {"edges": [[T(cx), T("-b.W / 2"), T("b.H")], [T(cx), T("b.W / 2"), T("b.H")]], "distance": T("bch"), "body": nm, "name": f"{nm} top chamfers {A}"})
    add("solid.box", {"length": T("b.L1 + 2"), "width": T("r.WR"), "height": T("r.HR - b.H1"), "corner": [T(x0 + " - 1"), T("-r.WR / 2"), T("b.H1")],
                      "operation": "cut", "targets": [nm], "name": f"{nm} channel"})
    add("sketch.create", {"plane": PLANE("b.H"), "name": f"{nm} holes"})
    add("sketch.point", {"point": [T(f"{cx} + (floor(k / 2) * 2 - 1) * b.C / 2"), T("((k % 2) * 2 - 1) * b.B / 2")]}, repeat=("k", "4", 4))
    add("sketch.finish", {})
    add("solid.hole", {"sketch": f"{nm} holes", "thread": T("b.M"), "depth": T("b.M_depth"), "targets": [nm], "name": f"{nm} mounting threads"})
    tn = f"{nm} top insert {A}"
    add("solid.box", {"length": T("2 * bx"), "width": T("2 * by"), "height": T("0.2 + 1"), "corner": [T(f"{cx} - bx"), T("-by"), T("b.H - 0.2")],
                      "operation": "cut", "targets": [nm], "name": f"{nm} top pocket {A}"})
    add("solid.box", {"length": T("2 * bx"), "width": T("2 * by"), "height": 0.2, "corner": [T(f"{cx} - bx"), T("-by"), T("b.H - 0.2")],
                      "operation": "new", "body_name": tn, "name": tn})
    caps, seals, screws = [], [], []
    for end, sx in (("A", -1), ("B", 1)):
        for part, t, off in (("end cap", "capw", "0"), ("end seal", "seal", "capw")):
            bn = f"{nm} {part} {end} {A}"
            xa = f"{cx} + b.L1 / 2 + {off}" if sx > 0 else f"{cx} - b.L1 / 2 - {off} - {t}"
            add("solid.box", {"length": T(t), "width": T("wc"), "height": T("hc"), "corner": [T(xa), T("-wc / 2"), T("b.H1 + 0.3")],
                              "operation": "new", "body_name": bn, "name": bn})
            add("solid.box", {"length": T(f"{t} + 2"), "width": T("r.WR"), "height": T("r.HR - b.H1"), "corner": [T(xa + " - 1"), T("-r.WR / 2"), T("b.H1")],
                              "operation": "cut", "targets": [bn], "name": f"{bn} channel"})
            (caps if part == "end cap" else seals).append(bn)
        face = f"{cx} + {sx} * b.L / 2"
        add("solid.cylinder", {"diameter": T("b.Gn"), "height": T("endw"), "base": [T(face + (" - endw" if sx > 0 else "")), 0, T("zl")], "axis": "X",
                               "operation": "cut", "targets": [caps[-1], seals[-1]], "name": f"{nm} lube hole {end}"}, when=w + " && b.Gn > 0")
        if sx > 0:
            nn = f"{nm} grease nipple {A}"
            nw = w + " && b.Gn == 0 && b.G > 0"
            add("solid.cylinder", {"diameter": 3, "height": T("b.G * 0.6"), "base": [T(face), 0, T("zl")], "axis": "X", "operation": "new", "body_name": nn, "name": nn}, when=nw)
            add("solid.cylinder", {"diameter": 2.2, "height": T("b.G * 0.4"), "base": [T(face + " + b.G * 0.6"), 0, T("zl")], "axis": "X", "operation": "join",
                                   "targets": [nn], "name": f"{nn} head"}, when=nw)
        sn = f"{nm} end screw {end}" + '${k == 0 ? "-" : "+"} ' + A
        add("solid.cylinder", {"diameter": T("scd"), "height": T("lip"), "base": [T(face if sx > 0 else face + " - lip"), T("(2 * k - 1) * b.B / 2"), T("b.H - scz")],
                               "axis": "X", "operation": "new", "body_name": sn, "name": sn}, repeat=("k", "2", 2))
        screws += [f"{nm} end screw {end}- {A}", f"{nm} end screw {end}+ {A}"]
    rn = f"{nm} retainer strip " + '${k == 1 ? "right" : "left"} ' + A
    add("solid.box", {"length": T("b.L1"), "width": 1.0, "height": 0.4, "corner": [T(x0), T("k == 1 ? r.WR / 2 : -r.WR / 2 - 1.0"), T("b.H1 - 0.4")],
                      "operation": "new", "body_name": rn, "name": rn}, repeat=("k", "2", 2))
    ret = [f"{nm} retainer strip left {A}", f"{nm} retainer strip right {A}"]
    nip = [f"{nm} grease nipple {A}"]
    nipw = w + " && b.Gn == 0 && b.G > 0"
    add("material.assign", {"bodies": [nm], "material": T("matname")})
    add("appearance.assign", {"bodies": [nm], "appearance": T("rail_app")})
    add("appearance.assign", {"body": nm, "faces": [[T(f"{cx} - b.C / 2"), 0, T("b.H")], [T(f"{cx} + b.C / 2"), 0, T("b.H")],
                                                     [T(cx), T("-b.W / 2"), T("(b.H + b.H1) / 2")], [T(cx), T("b.W / 2"), T("(b.H + b.H1) / 2")]], "appearance": T("ground_app")})
    add("appearance.assign", {"body": nm, "faces": [[T(cx), 0, T("r.HR")], [T(cx), T("-r.WR / 2"), T("(b.H1 + r.HR) / 2")], [T(cx), T("r.WR / 2"), T("(b.H1 + r.HR) / 2")]], **RACEWAY})
    add("material.assign", {"bodies": caps + seals, "material": "ABS Plastic"})
    add("appearance.assign", {"bodies": [tn], **INSERT_LOOK})
    add("material.assign", {"bodies": [tn], "material": "Steel"})
    add("appearance.assign", {"bodies": caps, **CAP_PBR})
    add("appearance.assign", {"bodies": seals, **SEAL_PBR})
    add("appearance.assign", {"bodies": screws, **BLACK_OXIDE})
    add("appearance.assign", {"bodies": nip, **BRASS}, when=nipw)
    add("appearance.assign", {"bodies": ret, **STAINLESS})
    add("material.assign", {"bodies": screws + nip + ret, "material": "Stainless Steel"}, when=nipw)
    add("material.assign", {"bodies": screws + ret, "material": "Stainless Steel"}, when=w + " && !(b.Gn == 0 && b.G > 0)")
    return st

def describe(gen):
    rails = read_csv(gen.dir / "data" / "rails.csv")
    blocks = read_csv(gen.dir / "data" / "blocks.csv")
    # the end-distance loop of catalogue.holes_for never runs for these tables: n = floor((L - 2 Es) / P) + 1 gives Es <= E < Es + P / 2
    # already, and the loop needs E >= Es + P / 2
    for r in rails:
        assert num(r["P"]) / 2 + num(r["Es"]) > num(r["Es"]) and float(num(r["P"])) > 0
    assert len(blocks) == 8
    vars_ = [
        {"name": "holes", "expr": "floor((length - 2 * r.Es) / r.P) + 1"},
        {"name": "end_d", "expr": "(length - (holes - 1) * r.P) / 2"},
        {"name": "end_txt", "expr": "fmt(end_d, 2)"},
        {"name": "mat", "expr": 'material == "M" ? "stainless" : (material == "HC" ? "carbon steel + hard chrome" : (material == "NC" ? "carbon steel + coating" : "carbon steel"))'},
        {"name": "ss", "expr": 'material == "M"'},
        {"name": "matname", "expr": 'ss ? "Stainless Steel" : "Steel"'},
        {"name": "rail_app", "expr": 'ss ? "starter.metal.stainless-soft-satin" : "Steel - Satin PBR"'},
        {"name": "ground_app", "expr": 'ss ? "starter.metal.silver-cool" : "starter.metal.carbon-steel-polished"'},
        {"name": "code", "expr": 'caps == "" ? code_in : concat("MGN", size, block, eblock, n_blocks, "R", length, erail, preload, precision, material, rails)'},
        {"name": "endw", "expr": "(b.L - b.L1) / 2"},
    ]
    vars_ += rnd("seal", "0.3 * endw", 2) + rnd("capw", "endw - seal", 2) + rnd("lip", "(b.Lmax - b.L) / 2", 3)
    vars_ += rnd("rch", "0.025 * r.WR", 3) + rnd("grr", "r.WR / 16", 3) + rnd("grz", "0.62 * r.HR", 3) + rnd("bch", "0.03 * b.W", 3)
    vars_ += rnd("scd", "0.075 * b.W", 3) + rnd("scz", "0.17 * b.H", 3)
    vars_ += [
        {"name": "wc", "expr": "b.W - 2 * 0.3"}, {"name": "hc", "expr": "b.H - b.H1 - 2 * 0.3"},
        {"name": "bx", "expr": "max(b.C / 2 - 3.0, 1.0)"}, {"name": "by", "expr": "b.W / 2 - bch"},
        {"name": "zl", "expr": "b.H - b.H2"},
        {"name": "xf", "expr": "holes > 1 ? end_d + r.P / 2 : end_d"},
        {"name": "span", "expr": f"(n_blocks - 1) * (b.L + {BLOCK_GAP})"},
    ]
    vars_ += [{"name": f"cx{i}", "expr": f"length / 2 - span / 2 + {i} * (b.L + {BLOCK_GAP})"} for i in range(MAXBLOCKS)]
    vars_.append({"name": "lube", "expr": 'b.G > 0 ? concat("grease nipple M3, projection G ", b.G, " mm, on the +X end of each block") : '
                                          'concat("lube hole O", b.Gn, " at ", b.H2, " mm below the block top, in both end faces")'})
    vars_ += description()

    steps = [
        S("solid.box", {"length": T("length"), "width": T("r.WR"), "height": T("r.HR"), "corner": [0, T("-r.WR / 2"), 0], "operation": "new", "body_name": "Rail", "name": "Rail"}),
        S("solid.chamfer", {"edges": [[T("length / 2"), T("-r.WR / 2"), T("r.HR")], [T("length / 2"), T("r.WR / 2"), T("r.HR")]], "distance": T("rch"), "body": "Rail",
                            "name": f"Rail top chamfers {APPX}"}),
        S("sketch.create", {"plane": PLANE("r.HR"), "name": "Rail hole"}),
        S("sketch.point", {"point": [T("end_d"), 0]}),
        S("sketch.finish", {}),
        S("solid.hole", {"sketch": "Rail hole", "diameter": T("r.d"), "type": "counterbore", "cb_diameter": T("r.D"), "cb_depth": T("r.h"), "name": "Rail hole 1"}),
        S("solid.pattern.rectangular", {"features": ["Rail hole 1"], "dir1": [1, 0, 0], "count1": T("holes"), "spacing1": T("r.P"), "name": "Rail holes"}, when="holes > 1"),
        S("solid.cylinder", {"radius": T("grr"), "height": T("length"), "base": [0, T("(2 * i - 1) * r.WR / 2"), T("grz")], "axis": "X", "operation": "cut", "targets": ["Rail"],
                             "name": '${"Rail ball groove " + (i == 0 ? "left" : "right")} ' + APPX}, repeat=("i", "2", 2)),
    ]
    for i in range(MAXBLOCKS):
        steps += block_steps(i)
    steps += [
        S("material.assign", {"bodies": ["Rail"], "material": T("matname")}),
        S("appearance.assign", {"bodies": ["Rail"], "appearance": T("rail_app")}),
        S("appearance.assign", {"body": "Rail", "appearance": T("ground_app"),
                                "faces": [[T("xf"), T("(r.D / 2 + r.WR / 2) / 2"), T("r.HR")], [T("xf"), T("-r.WR / 2"), T("r.HR * 0.25")], [T("xf"), T("-r.WR / 2"), T("r.HR * 0.88")],
                                          [T("xf"), T("r.WR / 2"), T("r.HR * 0.25")], [T("xf"), T("r.WR / 2"), T("r.HR * 0.88")]]}),
        S("appearance.assign", {"body": "Rail", **RACEWAY, "faces": [[T("xf"), T("-(r.WR / 2 - grr)"), T("grz")], [T("xf"), T("r.WR / 2 - grr"), T("grz")]]}),
        S("parts.insert", {"family": "socket_head_cap_screw", "size": T("r.bolt_m"), "length": T("r.bolt_len"), "at": T("screw_at"), "name": "Rail screws ${r.bolt}"}),
        S("appearance.assign", {"components": ["Rail screws ${r.bolt}"], **BLACK_OXIDE}),
        S("solid.cylinder", {"diameter": T("r.D"), "height": T("r.cap_h"), "base": [T("end_d + j * r.P"), 0, T("r.HR - r.cap_h")], "axis": "Z", "operation": "new",
                             "body_name": "Rail cap ${j + 1} " + APPX, "name": "Rail cap ${j + 1} " + APPX}, when='caps == "caps"', repeat=("j", "holes", 128)),
        S("material.assign", {"bodies": T("cap_names"), "material": "ABS Plastic"}, when='caps == "caps"'),
        S("appearance.assign", {"bodies": T("cap_names"), **CAP_PBR}, when='caps == "caps"'),
    ]
    for n in range(1, MAXBLOCKS + 1):
        steps.append(S("browser.visibility", {"items": ["Rail hole"] + [f"Block {k + 1} holes" for k in range(n)], "visible": False}, when=f"n_blocks == {n}"))
    steps += [
        S("component.metadata.set", {"component": T("code"), "part_number": T("code"), "description": T("desc"), "material": T("mat")}),
        S("document.metadata.set", {"values": {"part_number": T("code"), "description": T("desc")}}),
    ]

    sp = {"optional": [{"lit": " "}]}
    def opt(field, values, default=""):
        return {"optional": [sp, {"field": field, "enum": values}], "default": {field: default}}
    def alt(with_precision):
        t = [{"lit": "MGN"}, sp, {"field": "size", "enum": ["7", "9", "12", "15"]}, sp, {"field": "block", "enum": ["C", "H"]}, opt("eblock", ["E"]), sp,
             {"field": "n_blocks", "int": {"min": 0, "max": 99999}}, sp, {"lit": "R"}, sp, {"field": "length", "int": {"min": 0, "max": 99999}},
             opt("erail", ["E"]), opt("preload", ["ZF", "Z0", "Z1"])]
        # `HC` is a material, but the first alternative would read its H as a precision and stop: the second alternative has no precision
        # (a `chars` token of length 0 sets the field to "")
        t.append(opt("precision", ["C", "H", "P"]) if with_precision else {"field": "precision", "chars": "digits", "min_len": 0, "max_len": 0})
        t += [opt("material", ["M", "HC", "NC"]), opt("rails", ["I", "II", "III", "IIII"]), opt("caps", ["caps"])]
        return t
    pkg = {
        "grammar": {"alternatives": [alt(True), alt(False)],
                    "refuse": "{code}: expected MGN<size 7, 9, 12 or 15><C or H><blocks>R<rail length in mm>, e.g. MGN12H2R300Z0C (optional: E, preload ZF / Z0 / Z1, precision C / H / P, material M / HC / NC, rails I to IIII, ` caps`)"},
        "tables": tables(gen),
        "lookups": [{"table": "rails", "as": "r", "key": {"size": "size"}},
                    {"table": "blocks", "as": "b", "key": {"size": "size", "block": "block"}}],
        "vars": vars_,
        "rules": [
            {"when": "length > r.max_len", "refuse": "MGNR{size} max single length is {r.max_len} mm"},
            {"when": "holes < 1 || end_d < r.Es - 0.000000001", "refuse": "rail length {length} leaves end distance {end_txt} < {r.Es} mm (L = (n - 1) P + 2 E, E at least Es)"},
            {"when": "n_blocks < 1 || n_blocks > 4", "refuse": "{n_blocks} blocks: this generator draws 1 to 4 blocks on a rail"},
            {"when": 'caps == "caps" && r.cap_d == 0', "refuse": "MGN{size}: the catalogue lists bolt caps for MGN12 and MGN15 only (S4 Table 2-4-9)"},
        ],
        "x-lists": [
            {"name": "screw_at", "repeat": {"var": "j", "count": "holes", "max": 128}, "each": [T("end_d + j * r.P + r.d / 2"), 0, T("r.HR - r.h - 0.5")]},
            {"name": "cap_names", "repeat": {"var": "j", "count": "holes", "max": 128}, "each": "Rail cap ${j + 1} " + APPX},
        ],
        "steps": steps,
        "insert": {"component": "${code}"},
    }
    return {"package": pkg, "dimension_vars": ["holes", "end_d", "seal", "capw", "lip"]}

def sweep(rng, n):
    """Codes for tools/package-equiv beyond codes.txt: every size and block, 1 to 4 blocks, lengths from two end distances to past the limit,
    the optional letters, the caps suffix, one space between the parts, and junk."""
    from runtime.table import read_csv as rc
    import pathlib
    rows = {r["size"]: r for r in rc(pathlib.Path(__file__).resolve().parents[2] / "vendors/hiwin/mg/rail-set/data/rails.csv")}
    out = []
    pre, prec, mat, rl = ["", "ZF", "Z0", "Z1"], ["", "C", "H", "P"], ["", "M", "HC", "NC"], ["", "I", "II", "III", "IIII"]
    for size, r in rows.items():
        es, mx = float(r["Es"]), float(r["max_len"])
        for blk in "CH":
            for nb in range(1, 5):
                for L in sorted({int(2 * es), int(2 * es) + 1, 40 if 40 >= 2 * es else int(2 * es), 100, 195, 300, 1000, int(mx) - 1, int(mx), int(mx) + 1}):
                    out.append(f"MGN{size}{blk}{nb}R{L}")
    for _ in range(max(n, 0)):
        size = rng.choice(list(rows)); es, mx = float(rows[size]["Es"]), float(rows[size]["max_len"])
        L = rng.randint(int(2 * es), int(mx) + 20)
        parts = ["MGN", size, rng.choice("CH"), rng.choice(["", "E"]), str(rng.randint(1, 4)), "R", str(L), rng.choice(["", "E"]), rng.choice(pre), rng.choice(prec),
                 rng.choice(mat), rng.choice(rl)]
        code = ("MGN" + size + parts[2] + parts[3] + parts[4] + "R" + str(L) + "".join(parts[7:]))
        if rng.random() < 0.2:
            code = " ".join(x for x in parts if x)
        if rng.random() < 0.25 and " " not in code:
            code += " caps"
        out.append(code)
    out += ["MGN12", "MGN12H", "MGNR12", "MGW12H2R300", "MGN13H2R300", "MGN12X2R300", "MGN12H2R300Q", "MGN12H2R3.5", "MGN12H2R", "MGN12H2R300 caps caps",
            "MGN12H2R300Z9", "MGN12H2R300IIIII", "MGN7C1R600", "MGN7C1R601", "MGN7C1R700", "MGN7C1R700 caps", "MGN9C1R195ZFH caps", "MGN15H1R200Z0C caps", "MGN12H2R300Z0C caps",
            "MGN7C1R100 caps", "MGN9H1R100 caps", "MGN12H2R300HC", "MGN12H2R300 H C", "MGN12H2R300HHC", "MGN12H2R300CHC", "MGN12H2R300NC", "MGN12H2R300PM", "MGN12H2R300Z1PMII"]
    return out
