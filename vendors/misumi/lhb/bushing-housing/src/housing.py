"""MISUMI Economy Series linear bushing housing units, wide blocks: E-LBHN (single / medium) and E-LBHNW (double / medium long / long),
with or without dowel holes: ordering-code parser, catalogue data and native-SolidCraft command builder.

Source (every number below, id S12 in sources.toml): MISUMI Economy Series catalogue 2025, "Linear Bushing Housing Units - Wide Blocks,
Single / Medium" p.485 (printed 04-100) and "Double / Medium Long / Long" p.486 (figures, 04-101) and p.487 (tables, 04-102), published at
https://th.c.misumi-ec.com/book/THA_EconomySeries_e-catalog2025/files/basic-html/page485.html ... page487.html (page images
files/mobile/485.jpg ... 487.jpg).

Frame: the shaft bore runs along Y (the length L, centred on y = 0), the block is centred on x = 0 (width W), the base sits on z = 0 and the top
face on z = H. The bore centre is h below the top face (z = H - h). The built-in linear bushing is NOT drawn: the bore is an empty plain
cylinder at the nominal shaft diameter dr (the catalogue gives no inner dimensions of the bushing, only the outer unit).
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path
from runtime.table import read_csv, num
from runtime.appearance import APPX

class CodeError(ValueError):
    """The ordering code is not valid; the message says why."""

DATA = Path(__file__).resolve().parent.parent / "data"
TYPES = {r["type"]: r for r in read_csv(DATA / "types.csv")}

def _table(name):
    return {int(r["dr"]): {k: num(v) for k, v in r.items() if k not in ("source", "page", "status")} for r in read_csv(DATA / name)}

SINGLE = _table("single.csv")    # p.485
DOUBLE = _table("double.csv")    # p.486 / p.487

CODE = re.compile(r"^(E-LBHNW|E-LBHN)(\d{1,2})([DL]?)(?:-(P))?$")

# appearance (not in the catalogue): step of the lower body wall behind the wide top shoulders, half foot width as a fraction of W
WALL_STEP = 1.0
FOOT_FRAC = 0.16

@dataclass
class Housing:
    code: str
    type: str
    series: str            # single | medium | double | medlong | long
    dr: int
    dowel: bool
    d: dict                # the catalogue row
    L: float
    L1: float
    dr_tol: tuple          # (upper, lower)
    notes: list = field(default_factory=list)

    @property
    def H(self): return self.d["H"]
    @property
    def n_holes(self): return 6 if self.series == "long" else 4
    @property
    def hole_ys(self):
        h = self.L1 / 2
        return [-h, 0.0, h] if self.series == "long" else [-h, h]
    @property
    def dowel_positions(self):
        """Dowel holes: on the mounting-hole rows at the middle of the length (single, medium, double), on the centre line at the end
        mounting holes (medium long, long): read from the figures of p.485 / p.486; no coordinates are printed."""
        d = self.d
        if self.series in ("single", "medium", "double"):
            return [(-d["W1"] / 2, 0.0), (d["W1"] / 2, 0.0)]
        return [(0.0, -self.L1 / 2), (0.0, self.L1 / 2)]

    @property
    def label(self):
        return {"single": "single", "medium": "medium", "double": "double", "medlong": "medium long", "long": "long"}[self.series]

    @property
    def description(self) -> str:
        d = self.d
        s = (f"MISUMI Economy linear bushing housing unit {self.code}, wide block, {self.label}, shaft diameter dr {self.dr} mm "
             f"({self.dr_tol[0]:+.3f}/{self.dr_tol[1]:+.3f} mm as printed, bore drawn empty at nominal), L {self.L:g} mm (+-{d['L_tol']:g}), "
             f"L1 {self.L1:g} mm, W {d['W']:g} mm, H {d['H']:g} mm, h {d['h']:g} mm (+-{d['h_tol']:g}), {self.n_holes} mounting holes "
             f"{d['M']} (pilot d {d['d']:g} mm, thread depth {d['l']:g} mm)")
        if self.dowel:
            s += f", 2 dowel holes P {d['P']:g} mm x {d['l2']:g} deep (positions {APPX})"
        return s + ". Housing aluminium alloy, clear anodized. The built-in bushing, grease nipple hole and edge chamfers are not drawn. Generated from the published catalogue dimensions."

def parse(code: str) -> Housing:
    raw = code
    m = CODE.match(code.strip().upper())
    if not m:
        raise CodeError(f"{raw!r}: expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW "
                        "(double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L")
    typ, drs, ln, p = m.groups()
    dr = int(drs)
    dowel = p == "P"
    code = typ + drs + ln + ("-P" if dowel else "")
    if typ == "E-LBHN":
        if ln == "L":
            raise CodeError("E-LBHN has Single (no suffix) and Medium (D) only; the Long length L belongs to E-LBHNW (p.485)")
        if dr not in SINGLE:
            raise CodeError(f"E-LBHN{dr}: the wide single housing is offered for dr {sorted(SINGLE)} (p.485)")
        r = SINGLE[dr]
        if ln == "D":
            if r["L_medium"] is None:
                raise CodeError(f"E-LBHN{dr}D: the medium housing is offered for dr {sorted(k for k, v in SINGLE.items() if v['L_medium'])} "
                                "only; dr 13, 35, 40 and 50 are single only (p.485)")
            series, L, L1, tol = "medium", r["L_medium"], r["L1_medium"], (r["dr_tol_medium_upper"], r["dr_tol_medium_lower"])
        else:
            series, L, L1, tol = "single", r["L_single"], r["L1_single"], (r["dr_tol_single_upper"], r["dr_tol_single_lower"])
    else:
        if dr not in DOUBLE:
            raise CodeError(f"E-LBHNW{dr}: the wide double housing is offered for dr {sorted(DOUBLE)} (p.487)")
        r = DOUBLE[dr]
        if ln == "D":
            if r["L_medlong"] is None:
                raise CodeError(f"E-LBHNW{dr}D: the medium long housing is offered for dr {sorted(k for k, v in DOUBLE.items() if v['L_medlong'])} (p.487)")
            series, L, L1, tol = "medlong", r["L_medlong"], r["L1_medlong"], (0, r["dr_tol_medlong"])
        elif ln == "L":
            if r["L_long"] is None:
                raise CodeError(f"E-LBHNW{dr}L: the long housing is offered for dr {sorted(k for k, v in DOUBLE.items() if v['L_long'])} (p.487)")
            series, L, L1, tol = "long", r["L_long"], r["L1_long"], (0, r["dr_tol_long"])
        else:
            series, L, L1, tol = "double", r["L_double"], r["L1_double"], (0, r["dr_tol_double"])
    if dowel and r["P"] is None:
        raise CodeError(f"{typ}{dr}: dr {dr} has no dowel hole version, the dowel hole table starts at dr 8 (p.485 / p.487)")
    return Housing(code, typ, series, dr, dowel, r, L, L1, tol)

def profile(s: Housing):
    """Cross-section (x, z): wide shoulders of height H2 on top (width W), the body below narrower by WALL_STEP, down to the chamfered
    foot at H - H1 (H1 is measured from the top face, figure p.485). Only W, H, H1, H2 are catalogue values."""
    d = s.d
    H, W = d["H"], d["W"]
    wl = W / 2 - WALL_STEP
    zf = H - d["H1"]
    f = FOOT_FRAC * W
    return [[-f, 0], [f, 0], [wl, zf], [wl, H - d["H2"]], [W / 2, H - d["H2"]], [W / 2, H], [-W / 2, H], [-W / 2, H - d["H2"]],
            [-wl, H - d["H2"]], [-wl, zf]]

def hole_points(s: Housing):
    return [(sx * s.d["W1"] / 2, y) for sx in (-1, 1) for y in s.hole_ys]

def commands(s: Housing) -> list[dict]:
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    d = s.d
    H = d["H"]
    add("component.create", name=s.code)
    add("sketch.create", plane={"origin": [0, s.L / 2, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Profile")
    add("sketch.line", points=profile(s), closed=True)
    add("sketch.finish")
    add("solid.extrude", distance=s.L, name="Body", body_name=s.code)
    add("solid.cylinder", diameter=s.dr, height=s.L + 2, base=[0, -s.L / 2 - 1, H - d["h"]], axis="Y", operation="cut", targets=[s.code],
        name="Shaft bore")
    pts = hole_points(s)
    add("sketch.create", plane={"origin": [0, 0, H], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="Thread sketch")
    for x, y in pts:
        add("sketch.point", point=[x, y])
    add("sketch.finish")
    add("solid.hole", sketch="Thread sketch", thread=d["M"], depth=d["l"], targets=[s.code], name="Mounting thread")
    for i, (x, y) in enumerate(pts):   # the pilot diameter d continues from the thread depth l down through the base
        add("solid.cylinder", diameter=d["d"], height=H - d["l"] + 1, base=[x, y, -1], axis="Z", operation="cut", targets=[s.code],
            name=f"Pilot hole {i + 1}")
    if s.dowel:
        for i, (x, y) in enumerate(s.dowel_positions):
            add("solid.cylinder", diameter=d["P"], height=d["l2"] + 1, base=[x, y, H - d["l2"]], axis="Z", operation="cut", targets=[s.code],
                name=f"Dowel hole {i + 1} {APPX}")
    add("browser.visibility", items=["Profile", "Thread sketch"], visible=False)
    add("component.metadata.set", component=s.code, part_number=s.code, description=s.description, material="Aluminum alloy; clear anodized")
    add("document.metadata.set", values={"part_number": s.code, "description": s.description})
    return cmds

def parse_build(code: str):
    s = parse(code)
    return s, commands(s)
