"""Native-SolidCraft builder for a HIWIN EG set, rail or block, from catalogue.py's parsed code.

DIMENSIONED (catalogue values): rail = WR x HR box with the mounting holes at pitch P (EGR: counterbore from the top; the
bottom-mounted T rail is not drawn); each block = steel body W x L1 x (H - H1) with the rail channel cut out and its two (S block) or four (C block) mounting holes at
B (x C) (A: tapped from the top; B: through holes), plus end caps and end seals that bring it to the catalogue length L
(L1 and L are both catalogue columns, S15 p.57-59). The catalogue does not publish the ball-groove profile or the flange outline.

APPEARANCE (approximate, every such body or feature is named "... (appearance, approximate)"): rail top chamfers and one ball
groove per rail side, block top chamfers, end cap / end seal split, grease nipple, and the PBR looks (ground raceway and top faces,
satin body, black plastic, brass nipple, black-oxide rail screws). Sizes are estimates scaled from the catalogue envelope.
"""
from __future__ import annotations
from . import catalogue as eg
from runtime.appearance import APPX

BLOCK_GAP = eg.BLOCK_GAP

# Photoreal finishes (appearance only), by SolidCraft appearance-library entry: `appearance.assign appearance=<id>` resolves to the
# entry's own colour and pbr, so nothing is tuned by eye here. Roughness is the ground / satin difference: ground top, side and raceway
# faces 0.12-0.16, satin body 0.36-0.4. Where the library has no entry (black oxide) the look keeps a name and gives colour + pbr itself.
def lib(id):
    return dict(appearance=id)
def pbr(color, metallic, roughness, name):
    return dict(color=color, name=name, pbr=dict(metallic=metallic, roughness=roughness, dielectric_ior=1.5))
RAIL_BODY    = lib("Steel - Satin PBR")                        # library entry, roughness 0.4 (no starter.* satin carbon steel)
RAIL_GROUND  = lib("starter.metal.carbon-steel-polished")      # "Metal - Polished Carbon Steel", roughness 0.16
RACEWAY      = lib("starter.metal.silver-cool")                # "Metal - Cool Reflective Silver", roughness 0.12
BLOCK_BODY, BLOCK_GROUND = RAIL_BODY, RAIL_GROUND
SS_BODY      = lib("starter.metal.stainless-soft-satin")       # "Metal - Soft Satin Stainless", roughness 0.36
SS_GROUND    = RACEWAY                                         # ground stainless: silver-cool, the smoothest stainless-looking entry
CAP_LOOK     = lib("starter.plastic.abs-charcoal")             # black end caps are an appearance choice: "Plastic - Charcoal ABS"
SEAL_LOOK    = lib("starter.plastic.tpu-matte-black")          # end seals: "Plastic - Matte Black TPU"
BRASS        = lib("starter.metal.brass-champagne")            # "Metal - Champagne Satin Brass"
BASE_PLATE   = lib("starter.metal.aluminum-bead-blast")        # shots-only base plate
BLACK_OXIDE  = pbr("#232427", 0.9, 0.45, "Steel - Black oxide (appearance, approximate)")   # no starter.* black-oxide steel
# what appearance.chain reads back (name, roughness) per finish; check.py compares per face
READBACK = {"satin": ("Steel - Satin PBR", 0.4), "ground": ("Metal - Polished Carbon Steel", 0.16), "raceway": ("Metal - Cool Reflective Silver", 0.12),
            "ss_satin": ("Metal - Soft Satin Stainless", 0.36), "ss_ground": ("Metal - Cool Reflective Silver", 0.12),
            "ss_raceway": ("Metal - Cool Reflective Silver", 0.12)}


def appearance_sizes(s: eg.EgSet) -> dict:
    """Every estimated size, in one place (approximate, scaled from the catalogue envelope)."""
    r, b = s.rail, s.block
    out = dict(rail_chamfer=round(0.02 * r["WR"], 3), groove_r=round(r["WR"] / 16, 3), groove_z=round(0.62 * r["HR"], 3))
    if b:
        end = (b["L"] - b["L1"]) / 2                       # catalogue: L - L1 split over both ends (dimensioned)
        seal = round(0.25 * end, 2)
        out.update(block_chamfer=round(0.02 * b["W"], 3), end=end, seal=seal, cap=round(end - seal, 2), inset=0.5,
                   nip_d=round(0.1 * b["W"], 2), nip_l=round(0.1 * b["W"], 2))
    return out

def parse_build(code: str, appearance: bool = True):
    s = eg.parse(code)
    return s, commands(s, appearance)

def description(s: eg.EgSet) -> str:
    r = s.rail
    parts = []
    if s.kind in ("set", "rail"):
        parts.append(f"rail EGR{s.size}{s.rail_mount} L={s.rail_length:g} mm ({s.holes} holes, end distance {s.end_distance:g} mm, "
                     "counterbored from the top)")
    if s.kind in ("set", "block"):
        b = s.block
        parts.append(f"{s.n_blocks} block(s) {s.series}{s.size}{s.load}{s.mount}")
    head = "HIWIN EG linear guideway " + {"set": "set", "rail": "rail", "block": "block"}[s.kind] + ": " + " with ".join(parts) + "."
    env = (f" Rail drawn as the catalogue envelope {r['WR']} x {r['HR']} mm" if s.kind != "block" else "")
    if s.kind != "rail":
        b = s.block
        env += (("; " if env else " ") + f"block as the envelope {b['W']} x {b['L']} x {b['H'] - b['H1']:g} mm with the rail channel cut out")
    txt = head + env + " (the catalogue gives no ball-groove profile). Generated from the published catalogue dimensions."
    if s.kind != "rail":
        b = s.block
        txt += (f" Blocks are the steel body L1 {b['L1']:g} mm plus end caps and end seals to the catalogue length L {b['L']:g} mm.")
    a = appearance_sizes(s)
    txt += (f"\nAPPEARANCE (approximate, not a catalogue dimension): PBR steel looks with ground top and raceway faces, rail top chamfers "
            f"({a['rail_chamfer']:g} mm) and one circular ball groove per rail side (radius {a['groove_r']:g} mm)"
            + ("" if s.kind == "rail" else f", block top chamfers, black plastic end caps ({a['cap']:g} mm) and end seals ({a['seal']:g} mm) per end "
               "(the cap / seal split is an estimate), a brass grease nipple on the +X end") + ". All these bodies and features are named '" + APPX + "'.")
    return txt

def block_centres(s: eg.EgSet) -> list[float]:
    L = s.block["L"]
    if s.kind == "block":
        return [0.0]
    mid = s.rail_length / 2
    if s.n_blocks == 1:
        return [mid]
    span = (s.n_blocks - 1) * (L + BLOCK_GAP)
    return [mid - span / 2 + i * (L + BLOCK_GAP) for i in range(s.n_blocks)]

def commands(s: eg.EgSet, appearance: bool = True) -> list[dict]:
    """The SolidCraft command list. appearance=False builds the dimensioned bodies only (rail, blocks, holes): no chamfers, grooves,
    end caps and seals, nipple, rail screws, materials or looks. The parametric form of this generator is compared with that."""
    r = s.rail
    a = appearance_sizes(s)
    ss = s.material == "stainless steel"
    rail_body, rail_ground = (SS_BODY, SS_GROUND) if ss else (RAIL_BODY, RAIL_GROUND)
    block_body, block_ground = (SS_BODY, SS_GROUND) if ss else (BLOCK_BODY, BLOCK_GROUND)
    steel = "Stainless Steel" if ss else "Steel"
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    add("component.create", name=s.code)
    hidden = []
    if s.kind in ("set", "rail"):
        add("solid.box", length=s.rail_length, width=r["WR"], height=r["HR"], corner=[0, -r["WR"] / 2, 0],
            operation="new", body_name="Rail", name="Rail")
        add("sketch.create", plane={"origin": [0, 0, r["HR"]], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="Rail hole")
        add("sketch.point", point=[s.end_distance, 0])
        add("sketch.finish")
        add("solid.hole", sketch="Rail hole", diameter=r["d"], type="counterbore", cb_diameter=r["D"],
            cb_depth=r["h"], name="Rail hole 1")
        hidden.append("Rail hole")
        if s.holes > 1:
            add("solid.pattern.rectangular", features=["Rail hole 1"], dir1=[1, 0, 0], count1=s.holes,
                spacing1=r["P"], name="Rail holes")
        if appearance:
            add("solid.chamfer", edges=[[s.rail_length / 2, sy * r["WR"] / 2, r["HR"]] for sy in (-1, 1)],
                distance=a["rail_chamfer"], body="Rail", name=f"Rail top chamfers {APPX}")
            for sy, side in ((-1, "left"), (1, "right")):
                add("solid.cylinder", radius=a["groove_r"], height=s.rail_length, base=[0, sy * r["WR"] / 2, a["groove_z"]],
                    axis="X", operation="cut", targets=["Rail"], name=f"Rail ball groove {side} {APPX}")
            add("material.assign", bodies=["Rail"], material=steel)
            add("appearance.assign", bodies=["Rail"], **rail_body)
            # ground faces: the top, and the side faces above and below the ball groove; the groove is the raceway
            hr, wr = r["HR"], r["WR"]
            xf = s.end_distance + r["P"] / 2 if s.holes > 1 else s.end_distance
            add("appearance.assign", body="Rail", **rail_ground, faces=[[xf, (r["D"] / 2 + wr / 2) / 2, hr]] +
                [[xf, sy * wr / 2, hr * z] for sy in (-1, 1) for z in (0.25, 0.88)])
            add("appearance.assign", body="Rail", **RACEWAY, faces=[[xf, sy * (wr / 2 - a["groove_r"]), a["groove_z"]] for sy in (-1, 1)])
            if True:        # black-oxide ISO 4762 screws in the counterbored holes (all EGR rails are top-mounted)
                size, ln = r["bolt"].split("x")
                add("parts.insert", family="socket_head_cap_screw", size=size, length=float(ln),
                    at=[[s.end_distance + j * r["P"] + r["d"] / 2, 0, r["HR"] - r["h"] - 0.5] for j in range(s.holes)], name=f"Rail screws {r['bolt']}")
                add("appearance.assign", components=[f"Rail screws {r['bolt']}"], **BLACK_OXIDE)
    if s.kind in ("set", "block"):
        b = s.block
        for i, cx in enumerate(block_centres(s)):
            nm = f"Block {i + 1}"
            x0 = cx - b["L1"] / 2                                    # steel body (dimensioned: L1)
            add("solid.box", length=b["L1"], width=b["W"], height=b["H"] - b["H1"],
                corner=[x0, -b["W"] / 2, b["H1"]], operation="new", body_name=nm, name=nm)
            if appearance:
                add("solid.chamfer", edges=[[cx, sy * b["W"] / 2, b["H"]] for sy in (-1, 1)], distance=a["block_chamfer"],
                    body=nm, name=f"{nm} top chamfers {APPX}")
            add("solid.box", length=b["L1"] + 2, width=r["WR"], height=r["HR"] - b["H1"],
                corner=[x0 - 1, -r["WR"] / 2, b["H1"]], operation="cut", targets=[nm], name=f"{nm} channel")
            add("sketch.create", plane={"origin": [0, 0, b["H"]], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name=f"{nm} holes")
            for dx in ((-b["C"] / 2, b["C"] / 2) if b["C"] else (0.0,)):      # S block: one row of two holes
                for dy in (-b["B"] / 2, b["B"] / 2):
                    add("sketch.point", point=[cx + dx, dy])
            add("sketch.finish")
            if b["hole"] == "thread":
                add("solid.hole", sketch=f"{nm} holes", thread=b["M"], depth=b["M_depth"], targets=[nm], name=f"{nm} mounting threads")
            else:
                add("solid.hole", sketch=f"{nm} holes", diameter=b["hole_d"], targets=[nm], name=f"{nm} mounting holes")
            hidden.append(f"{nm} holes")
            if appearance:
                # ---- APPEARANCE: end caps and end seals (together they bring the block to the catalogue length L), grease nipple
                ins = a["inset"]; wc = b["W"] - 2 * ins; hc = b["H"] - b["H1"] - 2 * ins
                caps, seals = [], []
                for end, sx in (("A", -1), ("B", 1)):
                    for part, t, off, group in (("end cap", a["cap"], 0.0, caps), ("end seal", a["seal"], a["cap"], seals)):
                        xa = cx + b["L1"] / 2 + off if sx > 0 else cx - b["L1"] / 2 - off - t
                        bn = f"{nm} {part} {end} {APPX}"
                        add("solid.box", length=t, width=wc, height=hc, corner=[xa, -wc / 2, b["H1"] + ins], operation="new", body_name=bn, name=bn)
                        add("solid.box", length=t + 2, width=r["WR"], height=r["HR"] - b["H1"],
                            corner=[xa - 1, -r["WR"] / 2, b["H1"]], operation="cut", targets=[bn], name=f"{bn} channel")
                        group.append(bn)
                nn = f"{nm} grease nipple {APPX}"
                face = cx + b["L"] / 2                                   # outer face of the +X end seal (dimensioned: L)
                zn = (r["HR"] + b["H"]) / 2
                add("solid.cylinder", diameter=a["nip_d"], height=a["nip_l"] * 0.6, base=[face, 0, zn], axis="X", operation="new", body_name=nn, name=nn)
                add("solid.cylinder", diameter=a["nip_d"] * 0.7, height=a["nip_l"] * 0.4, base=[face + a["nip_l"] * 0.6, 0, zn], axis="X",
                    operation="join", targets=[nn], name=f"{nn} head")
                add("material.assign", bodies=[nm], material=steel)
                add("appearance.assign", bodies=[nm], **block_body)
                add("appearance.assign", body=nm, faces=[[cx, 0, b["H"]]] + [[cx, sy * b["W"] / 2, (b["H"] + b["H1"]) / 2] for sy in (-1, 1)],
                    **block_ground)
                add("appearance.assign", body=nm, faces=[[cx, 0, r["HR"]]] + [[cx, sy * r["WR"] / 2, (b["H1"] + r["HR"]) / 2] for sy in (-1, 1)], **RACEWAY)
                add("material.assign", bodies=caps + seals, material="ABS Plastic")
                add("appearance.assign", bodies=caps, **CAP_LOOK)
                add("appearance.assign", bodies=seals, **SEAL_LOOK)
                add("appearance.assign", bodies=[nn], **BRASS)
                add("material.assign", bodies=[nn], material="Brass")
    add("browser.visibility", items=hidden, visible=False)
    add("component.metadata.set", component=s.code, part_number=s.code, description=description(s), material=s.material)
    add("document.metadata.set", values={"part_number": s.code, "description": description(s)})
    return cmds
