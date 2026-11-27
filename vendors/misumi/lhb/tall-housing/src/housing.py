"""MISUMI Economy Series linear bushing housing units with dowel holes, tall blocks: E-LBHS (single, medium, medium long, long) and
E-LBHSW (double): ordering-code parser, catalogue data and native-SolidCraft command builder.

Source (every number below, id S14 in sources.toml): MISUMI Economy Series catalogue 2025, "Linear Bushing Housing Units with Dowel Holes -
Tall Blocks, Single" p.488 (printed 04-103), "... Double" p.489 (04-104), "... Medium / Medium Long / Long" p.490 (04-105), published at
https://th.c.misumi-ec.com/book/THA_EconomySeries_e-catalog2025/files/basic-html/page488.html ... page490.html (page images
files/mobile/488.jpg ... 490.jpg).

Frame: the shaft bore runs along Y (the length L, centred on y = 0), the block is centred on x = 0 (width W), the base (datum surface) sits on
z = 0 and the top face on z = H. The bore centre is h ABOVE the base (z = h). The built-in linear bushing is NOT drawn: the bore is an empty
plain cylinder at the nominal shaft diameter dr.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from runtime.table import read_csv, num
from runtime.appearance import APPX

class CodeError(ValueError):
    """The ordering code is not valid; the message says why."""

DATA = Path(__file__).resolve().parent.parent / "data"

def _rows(name):
    return [{k: num(v) for k, v in r.items() if k not in ("source", "page", "status")} for r in read_csv(DATA / name)]

BLOCKS = {(r["series"], r["dr"]): r for r in _rows("blocks.csv")}      # p.488 / p.489 / p.490
DOWEL = {(r["series"], r["dr"]): r for r in _rows("dowel.csv")}        # dowel hole tables of the same pages

SUFFIX = {"": "single", "D": "medium", "S": "medlong", "L": "long"}
LABEL = {"single": "single", "double": "double", "medium": "medium", "medlong": "medium long", "long": "long"}
PAGE = {"single": "p.488", "double": "p.489", "medium": "p.490", "medlong": "p.490", "long": "p.490"}

def offered(series):
    return sorted(dr for (s, dr) in BLOCKS if s == series)

CODE = re.compile(r"^(E-LBHSW|E-LBHS)(\d{1,2})([DSL]?)(?:-(P))?$")

# appearance (not in the catalogue): x of the vertical M1 holes as a fraction of W (from the centre line)
M1_X_FRAC = -0.35

@dataclass
class Housing:
    code: str
    type: str
    series: str            # single | double | medium | medlong | long
    dr: int
    dowel: bool
    d: dict                # the catalogue row
    dw: dict | None        # the dowel table row (None without dowel holes)

    @property
    def L(self): return self.d["L"]
    @property
    def H(self): return self.d["H"]
    @property
    def dr_tol(self): return (self.d["dr_tol_upper"], self.d["dr_tol_lower"])
    @property
    def m1_points(self):
        """2-M1: two vertical tapped holes in the top face, L1 apart; x = +-0.35 W on a diagonal (appearance: the diagonal keeps them clear of
        the dowel holes of the single housing, which sit on the other diagonal)."""
        x = abs(M1_X_FRAC) * self.d["W"]
        return [(x, -self.d["L1"] / 2), (-x, self.d["L1"] / 2)]
    @property
    def m2_ys(self):
        """2-M2 (3-M2 on the Long type): horizontal tapped holes from the +X face, L2 apart (middle hole of the long type: appearance)."""
        h = self.d["L2"] / 2
        return [-h, 0.0, h] if self.series == "long" else [-h, h]
    @property
    def dowel_positions(self):
        """Single: diagonal pair (-F/2, -E/2), (F/2, E/2) from the E / F dowel table; double / long: on the centre line, E apart.
        Read from the figures; E and F are printed, the orientation of the diagonal and x = 0 are not."""
        e = self.dw["E"] / 2
        if self.series == "single":
            f = self.dw["F"] / 2
            return [(-f, -e), (f, e)]
        return [(0.0, -e), (0.0, e)]

    @property
    def description(self) -> str:
        d = self.d
        s = (f"MISUMI Economy linear bushing housing unit {self.code}, tall block with dowel holes, {LABEL[self.series]}, shaft diameter dr {self.dr} mm "
             f"({self.dr_tol[0]:+.3f}/{self.dr_tol[1]:+.3f} mm as printed, bore drawn empty at nominal), L {self.L:g} mm, L1 {d['L1']:g} mm, "
             f"L2 {d['L2']:g} mm (+-0.5), W {d['W']:g} mm, H {d['H']:g} mm, h {d['h']:g} mm (+-0.05), "
             f"2 x {d['M1']} (effective length {d['M1_eff']:g} mm) and {len(self.m2_ys)} x {d['M2']} (effective length {d['M2_eff']:g} mm) tapped holes, "
             f"counterbore {d['d1']:g} x {d['t']:g} mm")
        if self.dowel:
            s += f", 2 dowel holes P {self.dw['P']:g} mm x {self.dw['l2']:g} deep (positions {APPX})"
        return s + ". Housing aluminium alloy, clear anodized. The built-in bushing, grease nipple and edge chamfers are not drawn. Generated from the published catalogue dimensions."

def parse(code: str) -> Housing:
    raw = code
    m = CODE.match(code.strip().upper())
    if not m:
        raise CodeError(f"{raw!r}: expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or "
                        "E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P")
    typ, drs, ln, p = m.groups()
    dr = int(drs)
    dowel = p == "P"
    code = typ + drs + ln + ("-P" if dowel else "")
    if typ == "E-LBHSW":
        if ln:
            raise CodeError(f"{raw!r}: the double housing E-LBHSW has no length suffix (p.489)")
        series = "double"
    else:
        series = SUFFIX[ln]
    if (series, dr) not in BLOCKS:
        what = {"single": "the tall single housing E-LBHS (p.488)", "double": "the tall double housing E-LBHSW (p.489)",
                "medium": "the medium housing E-LBHS..D (p.490)", "medlong": "the medium long housing E-LBHS..S (p.490)",
                "long": "the long housing E-LBHS..L (p.490)"}[series]
        raise CodeError(f"{code}: {what} is offered for dr {offered(series)} only")
    dw = None
    if dowel:
        if series in ("medium", "medlong"):
            raise CodeError(f"{code}: dowel holes are available on the long type only (p.490), not on the {LABEL[series]} housing")
        if (series, dr) not in DOWEL:
            lo = {"single": "dr 8 and up (p.488)", "double": "dr 8 and up (p.489)", "long": "dr 16 and up (p.490)"}[series]
            raise CodeError(f"{code}: no dowel hole version for dr {dr}: the {LABEL[series]} housing has dowel holes for {lo}")
        dw = DOWEL[(series, dr)]
    return Housing(code, typ, series, dr, dowel, BLOCKS[(series, dr)], dw)

def profile(s: Housing):
    W, H = s.d["W"], s.d["H"]
    return [[-W / 2, 0], [W / 2, 0], [W / 2, H], [-W / 2, H]]

def commands(s: Housing) -> list[dict]:
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    d = s.d
    H, W, L = d["H"], d["W"], s.L
    add("component.create", name=s.code)
    add("sketch.create", plane={"origin": [0, L / 2, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Profile")
    add("sketch.line", points=profile(s), closed=True)
    add("sketch.finish")
    add("solid.extrude", distance=L, name="Body", body_name=s.code)
    add("solid.cylinder", diameter=s.dr, height=L + 2, base=[0, -L / 2 - 1, d["h"]], axis="Y", operation="cut", targets=[s.code], name="Shaft bore")
    # 2-M1: vertical tapped holes in the top face
    add("sketch.create", plane={"origin": [0, 0, H], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="M1 sketch")
    for x, y in s.m1_points:
        add("sketch.point", point=[x, y])
    add("sketch.finish")
    add("solid.hole", sketch="M1 sketch", thread=d["M1"], depth=d["M1_eff"], targets=[s.code], name="Thread M1")
    # 2-M2 (3-M2): horizontal tapped holes from the +X face at l below the top face
    add("sketch.create", plane={"origin": [W / 2, 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}, name="M2 sketch")
    for y in s.m2_ys:
        add("sketch.point", point=[y, H - d["l"]])
    add("sketch.finish")
    add("solid.hole", sketch="M2 sketch", thread=d["M2"], depth=d["M2_eff"], targets=[s.code], name="Thread M2")
    # counterbores d1 x t from the -X face, coaxial with M2
    for i, y in enumerate(s.m2_ys):
        add("solid.cylinder", diameter=d["d1"], height=d["t"] + 1, base=[-W / 2 - 1, y, H - d["l"]], axis="X", operation="cut", targets=[s.code],
            name=f"Counterbore {i + 1} {APPX}")
    if s.dowel:
        for i, (x, y) in enumerate(s.dowel_positions):
            add("solid.cylinder", diameter=s.dw["P"], height=s.dw["l2"] + 1, base=[x, y, H - s.dw["l2"]], axis="Z", operation="cut", targets=[s.code],
                name=f"Dowel hole {i + 1} {APPX}")
    add("browser.visibility", items=["Profile", "M1 sketch", "M2 sketch"], visible=False)
    add("component.metadata.set", component=s.code, part_number=s.code, description=s.description, material="Aluminum alloy; clear anodized")
    add("document.metadata.set", values={"part_number": s.code, "description": s.description})
    return cmds

def parse_build(code: str):
    s = parse(code)
    return s, commands(s)
