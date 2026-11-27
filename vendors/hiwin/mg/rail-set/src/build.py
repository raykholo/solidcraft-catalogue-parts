"""Native-SolidCraft builder for a HIWIN MGN set (rail + blocks), from catalogue.py's parsed code.

Two kinds of content, kept apart in the model, the body names and the part description:

DIMENSIONED (catalogue values, S4 table 2-4-19 (1) and p.85): rail WR x HR with the counterbored holes at pitch P and
end distance E; block outline W x L x (H - H1), L1 steel body, L with end caps and end seals, the four mounting
threads M x depth at B x C; lube hole diameter Gn at H2 below the block top (MGN7/9/12) or the grease nipple M3 / G
(MGN15); L Max = L plus the end-seal lip and screw heads.

APPEARANCE (approximate, not a catalogue dimension): every body whose name ends in "(appearance, approximate)", and
on the rail the top chamfers and the two side ball grooves (cut into "Rail" by features named "... (appearance,
approximate)"). The shapes are read from HIWIN's published drawings and photo (sources.toml rows 35-44); the sizes of
chamfers, groove radius, end cap / end seal split, retainer strips and end screws are estimates.
"""
from __future__ import annotations
from . import catalogue as mgn
from runtime.appearance import APPX

BLOCK_GAP = 10.0    # mm between neighbouring blocks on one rail: an illustration choice, not a catalogue value

LOOK = mgn.LOOK     # L Max, H2, Gn, G per block: data/blocks.csv (S4 p.88)
# Appearance colours (SolidCraft appearance library names). HIWIN's published MG photo shows green end caps and red
# end seals, metal block and rail.
CAP_LOOK, SEAL_LOOK = "ABS - Green", "ABS - Red"

# Photoreal finishes (appearance only), by SolidCraft appearance-library entry: `appearance.assign appearance=<id>` resolves to the
# entry's own colour and pbr, so nothing is tuned by eye here. Roughness is the ground / satin difference: ground top, side and raceway
# faces 0.12-0.16, satin body 0.36-0.4. Where the library has no entry (green / red plastics, black oxide) the look keeps a library
# name and gives colour + pbr {metallic, roughness, dielectric_ior} itself.
def lib(id):
    return dict(appearance=id)
def pbr(color, metallic, roughness, name):
    return dict(color=color, name=name, pbr=dict(metallic=metallic, roughness=roughness, dielectric_ior=1.5))
RAIL_BODY    = lib("Steel - Satin PBR")                        # library entry, roughness 0.4 (no starter.* satin carbon steel)
RAIL_GROUND  = lib("starter.metal.carbon-steel-polished")      # "Metal - Polished Carbon Steel", roughness 0.16
RACEWAY      = lib("starter.metal.silver-cool")                # "Metal - Cool Reflective Silver", roughness 0.12
BLOCK_BODY, BLOCK_GROUND = RAIL_BODY, RAIL_GROUND
STAINLESS    = lib("starter.metal.stainless-soft-satin")       # "Metal - Soft Satin Stainless", roughness 0.36
STAINLESS_RAIL, STAINLESS_GROUND = STAINLESS, RACEWAY          # ground stainless: silver-cool, the smoothest stainless-looking entry
INSERT_LOOK  = lib("starter.plastic.tpu-matte-black")          # "Plastic - Matte Black TPU"
BRASS        = lib("starter.metal.brass-champagne")            # "Metal - Champagne Satin Brass"
BASE_PLATE   = lib("starter.metal.aluminum-bead-blast")        # shots-only base plate
BLACK_OXIDE  = pbr("#232427", 0.9, 0.45, "Steel - Black oxide (appearance, approximate)")   # no starter.* black-oxide steel
CAP_PBR      = pbr("#349650", 0.0, 0.45, CAP_LOOK)               # no starter.* green plastic: library "ABS - Green" + pbr
SEAL_PBR     = pbr("#c42828", 0.0, 0.55, SEAL_LOOK)              # no starter.* red plastic: library "ABS - Red" + pbr
# what appearance.chain reads back (name, roughness) per finish; check.py compares per face
READBACK = {"satin": ("Steel - Satin PBR", 0.4), "ground": ("Metal - Polished Carbon Steel", 0.16), "raceway": ("Metal - Cool Reflective Silver", 0.12),
            "ss_satin": ("Metal - Soft Satin Stainless", 0.36), "ss_ground": ("Metal - Cool Reflective Silver", 0.12),
            "ss_raceway": ("Metal - Cool Reflective Silver", 0.12)}

# Bolt caps for the rail mounting holes: S4 p.82, Table 2-4-9 lists them for MGN12 and MGN15 only (O6.15, thickness 1.2)
# and says they are included with the rail package; the model number has no symbol for them. So they are a default-off
# option here: `caps=True` in the API, `--caps` on gen / check, or SC_MGN_CAPS=1 in the environment.
CAP_SIZES = mgn.CAP_SIZES   # data/caps.csv (S4 p.82 Table 2-4-9)

def parse_build(code: str, appearance: bool = True, screws: bool = True, caps=None, base_plate: bool = False):
    import os
    s = mgn.parse(code)
    if caps is None:      # from SC_MGN_CAPS: sizes without caps in the catalogue are built without
        caps = os.environ.get("SC_MGN_CAPS", "") not in ("", "0") and s.size in CAP_SIZES
    if caps and s.size not in CAP_SIZES:
        raise ValueError(f"MGN{s.size}: the catalogue lists bolt caps for MGN12 and MGN15 only (S4 Table 2-4-9)")
    return s, commands(s, appearance=appearance, screws=screws, caps=caps, base_plate=base_plate)

def look(s: mgn.MgnSet) -> dict:
    return LOOK[(s.size, s.block_type)]

def appearance_sizes(s: mgn.MgnSet) -> dict:
    """Every estimated size, in one place (approximate, scaled from the catalogue envelope)."""
    r, b = s.rail, s.block
    end = (b["L"] - b["L1"]) / 2                 # catalogue: L - L1 split over both ends (dimensioned)
    seal = round(0.3 * end, 2)                   # approximate split of each end into cap + seal
    return dict(
        rail_chamfer=round(0.025 * r["WR"], 3),
        groove_r=round(r["WR"] / 16, 3), groove_z=round(0.62 * r["HR"], 3),
        block_chamfer=round(0.03 * b["W"], 3),
        end=end, seal=seal, cap=round(end - seal, 2), inset=0.3,
        lip=round((look(s)["Lmax"] - b["L"]) / 2, 3),     # catalogue: (L Max - L) / 2 per end
        screw_d=round(0.075 * b["W"], 3), screw_dz=round(0.17 * b["H"], 3),
        retainer_w=1.0, retainer_t=0.4,
    )

def description(s: mgn.MgnSet, appearance: bool = True, screws: bool = True, caps: bool = False) -> str:
    k = look(s); a = appearance_sizes(s); r, b = s.rail, s.block
    lube = (f"grease nipple M3, projection G {k['G']:g} mm, on the +X end of each block" if k["G"]
            else f"lube hole O{k['Gn']:g} at {k['H2']:g} mm below the block top, in both end faces")
    txt = (f"HIWIN MGN{s.size}{s.block_type} linear guide set: rail MGNR{s.size} L={s.rail_length:g} mm "
           f"({s.holes} holes, end distance {s.end_distance:g} mm) with {s.n_blocks} block(s).\n"
           f"DIMENSIONED (catalogue values, HIWIN MG Series catalogue G99TE24-2410): rail {r['WR']} x {r['HR']} mm, "
           f"counterbored holes O{r['D']:g} x {r['h']:g} deep, through O{r['d']:g}, pitch {r['P']:g}; block {b['W']} wide, "
           f"{b['L']} long with end seals (steel body {b['L1']}), H {b['H']}, H1 {b['H1']}, four {b['M']}x{b['M_depth']:g} threads "
           f"at B {b['B']} x C {b['C']}; {lube}; L Max {k['Lmax']:g} mm. The 10 mm gap between blocks is an illustration choice.")
    if appearance:
        txt += (f"\nAPPEARANCE (approximate, not a catalogue dimension; shapes from HIWIN's published drawings and photo): "
                f"rail top chamfers ({a['rail_chamfer']:g} mm) and two side ball grooves (radius {a['groove_r']:g} mm, a circular "
                f"approximation of the groove, which the catalogue does not dimension); block top chamfers; a black top insert 0.2 mm deep between the mounting holes (HIWIN's photo shows a black middle band between metal ends); plastic end caps "
                f"({a['cap']:g} mm) and end seals ({a['seal']:g} mm) per end, the cap / seal split is an estimate; retainer strips; "
                f"two cross-head end screws per end; the grease nipple shape. All these bodies are named '{APPX}'.")
        if caps:
            txt += (f" Bolt caps in the rail holes: catalogue O{CAP_SIZES[s.size]['D']:g} x {CAP_SIZES[s.size]['H']:g} thick "
                    f"(Table 2-4-9, a press fit), modelled flush at the counterbore diameter.")
        if screws:
            txt += f" Rail screws: ISO 4762 {r['bolt']} from SolidCraft's standard parts (the catalogue gives the bolt size, not the screw model)."
    return txt

def block_centres(s: mgn.MgnSet) -> list[float]:
    L = s.block["L"]; mid = s.rail_length / 2
    if s.n_blocks == 1:
        return [mid]
    span = (s.n_blocks - 1) * (L + BLOCK_GAP)
    return [mid - span / 2 + i * (L + BLOCK_GAP) for i in range(s.n_blocks)]

def commands(s: mgn.MgnSet, appearance: bool = True, screws: bool = True, caps: bool = False, base_plate: bool = False) -> list[dict]:
    r, b = s.rail, s.block
    a = appearance_sizes(s); k = look(s)
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    ss = s.material == "stainless"
    rail_body, rail_ground = (STAINLESS_RAIL, STAINLESS_GROUND) if ss else (RAIL_BODY, RAIL_GROUND)
    block_body, block_ground = (STAINLESS, STAINLESS_GROUND) if ss else (BLOCK_BODY, BLOCK_GROUND)
    add("component.create", name=s.code)
    # ---- DIMENSIONED: rail along +X from x=0, centred on Y, bottom at z=0
    add("solid.box", length=s.rail_length, width=r["WR"], height=r["HR"], corner=[0, -r["WR"] / 2, 0],
        operation="new", body_name="Rail", name="Rail")
    if appearance:
        add("solid.chamfer", edges=[[s.rail_length / 2, sy * r["WR"] / 2, r["HR"]] for sy in (-1, 1)],
            distance=a["rail_chamfer"], body="Rail", name=f"Rail top chamfers {APPX}")
    add("sketch.create", plane={"origin": [0, 0, r["HR"]], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="Rail hole")
    add("sketch.point", point=[s.end_distance, 0])
    add("sketch.finish")
    add("solid.hole", sketch="Rail hole", diameter=r["d"], type="counterbore", cb_diameter=r["D"],
        cb_depth=r["h"], name="Rail hole 1")
    if s.holes > 1:
        add("solid.pattern.rectangular", features=["Rail hole 1"], dir1=[1, 0, 0], count1=s.holes,
            spacing1=r["P"], name="Rail holes")
    if appearance:
        for sy, side in ((-1, "left"), (1, "right")):
            add("solid.cylinder", radius=a["groove_r"], height=s.rail_length, base=[0, sy * r["WR"] / 2, a["groove_z"]],
                axis="X", operation="cut", targets=["Rail"], name=f"Rail ball groove {side} {APPX}")
    # ---- blocks
    for i, cx in enumerate(block_centres(s)):
        nm = f"Block {i + 1}"
        x0, x1 = cx - b["L1"] / 2, cx + b["L1"] / 2          # steel body (dimensioned: L1)
        add("solid.box", length=b["L1"], width=b["W"], height=b["H"] - b["H1"],
            corner=[x0, -b["W"] / 2, b["H1"]], operation="new", body_name=nm, name=nm)
        if appearance:
            add("solid.chamfer", edges=[[cx, sy * b["W"] / 2, b["H"]] for sy in (-1, 1)], distance=a["block_chamfer"],
                body=nm, name=f"{nm} top chamfers {APPX}")
        add("solid.box", length=b["L1"] + 2, width=r["WR"], height=r["HR"] - b["H1"],
            corner=[x0 - 1, -r["WR"] / 2, b["H1"]], operation="cut", targets=[nm], name=f"{nm} channel")
        add("sketch.create", plane={"origin": [0, 0, b["H"]], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name=f"{nm} holes")
        for dx in (-b["C"] / 2, b["C"] / 2):
            for dy in (-b["B"] / 2, b["B"] / 2):
                add("sketch.point", point=[cx + dx, dy])
        add("sketch.finish")
        add("solid.hole", sketch=f"{nm} holes", thread=b["M"], depth=b["M_depth"], targets=[nm], name=f"{nm} mounting threads")
        if not appearance:
            continue
        # ---- APPEARANCE: end caps, end seals, lube hole / nipple, end screws, retainer strips
        bx = max(b["C"] / 2 - 3.0, 1.0); by = b["W"] / 2 - a["block_chamfer"]; ti = 0.2
        tn = f"{nm} top insert {APPX}"
        add("solid.box", length=2 * bx, width=2 * by, height=ti + 1, corner=[cx - bx, -by, b["H"] - ti], operation="cut", targets=[nm], name=f"{nm} top pocket {APPX}")
        add("solid.box", length=2 * bx, width=2 * by, height=ti, corner=[cx - bx, -by, b["H"] - ti], operation="new", body_name=tn, name=tn)
        ins = a["inset"]; wc = b["W"] - 2 * ins; hc = b["H"] - b["H1"] - 2 * ins
        bodies = {"cap": [], "seal": [], "screw": [], "retainer": [], "nipple": [], "insert": [tn]}
        for end, sx in (("A", -1), ("B", 1)):
            for part, t, off in (("end cap", a["cap"], 0.0), ("end seal", a["seal"], a["cap"])):
                xa = cx + b["L1"] / 2 + off if sx > 0 else cx - b["L1"] / 2 - off - t
                bn = f"{nm} {part} {end} {APPX}"
                add("solid.box", length=t, width=wc, height=hc, corner=[xa, -wc / 2, b["H1"] + ins],
                    operation="new", body_name=bn, name=bn)
                add("solid.box", length=t + 2, width=r["WR"], height=r["HR"] - b["H1"],
                    corner=[xa - 1, -r["WR"] / 2, b["H1"]], operation="cut", targets=[bn], name=f"{bn} channel")
                bodies["cap" if part == "end cap" else "seal"].append(bn)
            face = cx + sx * b["L"] / 2                            # outer face of the end seal (dimensioned: L)
            zl = b["H"] - k["H2"]
            if k["Gn"]:                                            # lube hole Gn at H2 (dimensioned)
                add("solid.cylinder", diameter=k["Gn"], height=a["end"], base=[face - (a["end"] if sx > 0 else 0), 0, zl],
                    axis="X", operation="cut", targets=[bodies["cap"][-1], bodies["seal"][-1]], name=f"{nm} lube hole {end}")
            elif k["G"] and sx > 0:                                # grease nipple M3, projection G (dimensioned)
                nn = f"{nm} grease nipple {APPX}"
                add("solid.cylinder", diameter=3.0, height=k["G"] * 0.6, base=[face, 0, zl], axis="X",
                    operation="new", body_name=nn, name=nn)
                add("solid.cylinder", diameter=2.2, height=k["G"] * 0.4, base=[face + k["G"] * 0.6, 0, zl], axis="X",
                    operation="join", targets=[nn], name=f"{nn} head")
                bodies["nipple"].append(nn)
            for sy in (-1, 1):                                     # cross-head screws, lip = (L Max - L) / 2 (dimensioned)
                sn = f"{nm} end screw {end}{'+' if sy > 0 else '-'} {APPX}"
                add("solid.cylinder", diameter=a["screw_d"], height=a["lip"], base=[face if sx > 0 else face - a["lip"], sy * b["B"] / 2, b["H"] - a["screw_dz"]],
                    axis="X", operation="new", body_name=sn, name=sn)
                bodies["screw"].append(sn)
        for sy in (-1, 1):                                         # retainer strips under the block, beside the rail
            rn = f"{nm} retainer strip {'right' if sy > 0 else 'left'} {APPX}"
            y0 = r["WR"] / 2 if sy > 0 else -r["WR"] / 2 - a["retainer_w"]
            add("solid.box", length=b["L1"], width=a["retainer_w"], height=a["retainer_t"], corner=[x0, y0, b["H1"] - a["retainer_t"]],
                operation="new", body_name=rn, name=rn)
            bodies["retainer"].append(rn)
        add("material.assign", bodies=[nm], material="Stainless Steel" if ss else "Steel")
        add("appearance.assign", bodies=[nm], **block_body)
        # ground top and side faces, and the raceway faces of the rail channel, are smoother than the satin body
        add("appearance.assign", body=nm, faces=[[cx + sx * b["C"] / 2, 0, b["H"]] for sx in (-1, 1)] + [[cx, sy * b["W"] / 2, (b["H"] + b["H1"]) / 2] for sy in (-1, 1)],
            **block_ground)
        add("appearance.assign", body=nm, faces=[[cx, 0, r["HR"]]] + [[cx, sy * r["WR"] / 2, (b["H1"] + r["HR"]) / 2] for sy in (-1, 1)], **RACEWAY)
        add("material.assign", bodies=bodies["cap"] + bodies["seal"], material="ABS Plastic")
        add("appearance.assign", bodies=bodies["insert"], **INSERT_LOOK)
        add("material.assign", bodies=bodies["insert"], material="Steel")
        add("appearance.assign", bodies=bodies["cap"], **CAP_PBR)
        add("appearance.assign", bodies=bodies["seal"], **SEAL_PBR)
        add("appearance.assign", bodies=bodies["screw"], **BLACK_OXIDE)       # cross-head end screws: black oxide
        if bodies["nipple"]:
            add("appearance.assign", bodies=bodies["nipple"], **BRASS)        # grease nipple: brass
        add("appearance.assign", bodies=bodies["retainer"], **STAINLESS)      # retainer strips: stainless
        add("material.assign", bodies=bodies["screw"] + bodies["nipple"] + bodies["retainer"], material="Stainless Steel")
    if appearance:
        add("material.assign", bodies=["Rail"], material="Stainless Steel" if ss else "Steel")
        add("appearance.assign", bodies=["Rail"], **rail_body)
        # ground faces: the top, the side faces above and below the ball groove; the groove itself is the raceway
        hr, wr = r["HR"], r["WR"]
        xf = s.end_distance + r["P"] / 2 if s.holes > 1 else s.end_distance
        add("appearance.assign", body="Rail", **rail_ground, faces=[[xf, (r["D"] / 2 + wr / 2) / 2, hr]] +
            [[xf, sy * wr / 2, hr * z] for sy in (-1, 1) for z in (0.25, 0.88)])
        add("appearance.assign", body="Rail", **RACEWAY, faces=[[xf, sy * (wr / 2 - a["groove_r"]), a["groove_z"]] for sy in (-1, 1)])
    if appearance and screws:
        size, ln = r["bolt"].split("x")
        add("parts.insert", family="socket_head_cap_screw", size=size, length=float(ln),
            at=[[s.end_distance + j * r["P"] + r["d"] / 2, 0, r["HR"] - r["h"] - 0.5] for j in range(s.holes)], name=f"Rail screws {r['bolt']}")
        add("appearance.assign", components=[f"Rail screws {r['bolt']}"], **BLACK_OXIDE)
    if appearance and caps:
        cd, ch = CAP_SIZES[s.size]["D"], CAP_SIZES[s.size]["H"]
        names = []
        for j in range(s.holes):
            cn = f"Rail cap {j + 1} {APPX}"
            # flush in the counterbore: thickness H from the catalogue, diameter = counterbore D (the catalogue O6.15 is a press fit)
            add("solid.cylinder", diameter=r["D"], height=ch, base=[s.end_distance + j * r["P"], 0, r["HR"] - ch], axis="Z",
                operation="new", body_name=cn, name=cn)
            names.append(cn)
        add("material.assign", bodies=names, material="ABS Plastic")
        add("appearance.assign", bodies=names, **CAP_PBR)
    if base_plate:   # screenshots only: never part of the generated part (build_commands default False)
        ln = float(r["bolt"].split("x")[1]); th = ln + 3
        add("solid.box", length=s.rail_length + 30, width=r["WR"] + 50, height=th, corner=[-15, -(r["WR"] + 50) / 2, -th],
            operation="new", body_name="Base plate (screenshot only)", name="Base plate (screenshot only)")
        add("appearance.assign", bodies=["Base plate (screenshot only)"], **BASE_PLATE)
    add("browser.visibility", items=["Rail hole"] + [f"Block {i + 1} holes" for i in range(s.n_blocks)], visible=False)
    add("component.metadata.set", component=s.code, part_number=s.code, description=description(s, appearance, screws, caps),
        material=f"{s.material}")
    add("document.metadata.set", values={"part_number": s.code, "description": description(s, appearance, screws, caps)})
    return cmds
