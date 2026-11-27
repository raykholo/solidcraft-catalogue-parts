"""MISUMI Economy Series linear bushing housing units, center hole height optional: E-LBHG (single) and E-LBHGW (double): ordering-code
parser, catalogue data and native-SolidCraft command builder.

Source (every number below, id S14 in sources.toml): MISUMI Economy Series catalogue 2025, "Linear Bushing Housing Units, Center Hole Height
Optional, Single / Double" p.491 (printed 04-106), published at
https://th.c.misumi-ec.com/book/THA_EconomySeries_e-catalog2025/files/basic-html/page491.html (page image files/mobile/491.jpg).

Frame: the shaft bore runs along Y (the length T, centred on y = 0), the block is centred on x = 0, the base (datum surface) sits on z = 0.
The bore centre is H above the base (the part number's optional centre height). The built-in linear bushing is NOT drawn: the bore is an
empty plain cylinder at the nominal shaft diameter dr.
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
ROWS = {}
for _r in read_csv(DATA / "housing-g.csv"):
    _d = {k: num(v) for k, v in _r.items() if k not in ("source", "page", "status", "H_choices")}
    _d["H_choices"] = [int(x) for x in _r["H_choices"].split("|")]
    ROWS[_d["dr"]] = _d

CODE = re.compile(r"^(E-LBHGW|E-LBHG)(\d{1,2})-(\d{1,2})$")

@dataclass
class Housing:
    code: str
    type: str
    series: str        # single | double
    dr: int
    H: int             # centre height (the ordering option)
    d: dict

    @property
    def T(self): return self.d["T_double" if self.series == "double" else "T_single"]
    @property
    def T1(self): return self.d["T1_double" if self.series == "double" else "T1_single"]
    @property
    def H1(self): return self.H + self.d["H1_offset"]
    @property
    def hole_points(self):
        return [(sx * self.d["L1"] / 2, sy * self.T1 / 2) for sx in (-1, 1) for sy in (-1, 1)]

    @property
    def description(self) -> str:
        d = self.d
        return (f"MISUMI Economy linear bushing housing unit {self.code}, centre hole height optional, {self.series}, shaft diameter dr {self.dr} mm "
                f"(bore drawn empty at nominal), centre height H {self.H} mm (+-0.05), total height H1 {self.H1:g} mm (0/-0.5), flange width L {d['L']:g} mm "
                f"(centre at L/2 +-0.05), length T {self.T:g} mm, flange thickness S {d['S']:g} mm, body width W {d['W']:g} mm, 4 mounting holes d {d['d']:g} mm "
                f"on L1 {d['L1']:g} x T1 {self.T1:g} mm. Housing aluminium alloy, clear anodized. The built-in bushing and edge chamfers are not drawn; the "
                f"upper corner chamfers C1 {d['C1']:g} mm are {APPX}. Generated from the published catalogue dimensions.")

def parse(code: str) -> Housing:
    raw = code
    m = CODE.match(code.strip().upper())
    if not m:
        raise CodeError(f"{raw!r}: expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40")
    typ, drs, hs = m.groups()
    dr, H = int(drs), int(hs)
    if dr not in ROWS:
        raise CodeError(f"{typ}{dr}-{H}: dr {dr} is not a catalogue size; E-LBHG / E-LBHGW are offered for dr {sorted(ROWS)} (p.491)")
    r = ROWS[dr]
    if H not in r["H_choices"]:
        raise CodeError(f"{typ}{dr}-{H}: centre height H {H} is not offered for dr {dr}; the choices are {r['H_choices']} (p.491)")
    return Housing(f"{typ}{dr}-{H}", typ, "double" if typ == "E-LBHGW" else "single", dr, H, r)

def profile(s: Housing):
    """Cross-section (x, z): flange of width L and thickness S, body of width W up to H1 with the two top corners cut by C1 (45 degrees,
    appearance: the figure shows the chamfered top, C1 is printed)."""
    d = s.d
    L, W, S, H1, c = d["L"], d["W"], d["S"], s.H1, d["C1"]
    return [[-L / 2, 0], [L / 2, 0], [L / 2, S], [W / 2, S], [W / 2, H1 - c], [W / 2 - c, H1], [-W / 2 + c, H1], [-W / 2, H1 - c], [-W / 2, S], [-L / 2, S]]

def commands(s: Housing) -> list[dict]:
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    d = s.d
    T = s.T
    add("component.create", name=s.code)
    add("sketch.create", plane={"origin": [0, T / 2, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Profile")
    add("sketch.line", points=profile(s), closed=True)
    add("sketch.finish")
    add("solid.extrude", distance=T, name="Body", body_name=s.code)
    add("solid.cylinder", diameter=s.dr, height=T + 2, base=[0, -T / 2 - 1, s.H], axis="Y", operation="cut", targets=[s.code], name="Shaft bore")
    for i, (x, y) in enumerate(s.hole_points):
        add("solid.cylinder", diameter=d["d"], height=d["S"] + 2, base=[x, y, -1], axis="Z", operation="cut", targets=[s.code], name=f"Mounting hole {i + 1}")
    add("browser.visibility", items=["Profile"], visible=False)
    add("component.metadata.set", component=s.code, part_number=s.code, description=s.description, material="Aluminum alloy; clear anodized")
    add("document.metadata.set", values={"part_number": s.code, "description": s.description})
    return cmds

def parse_build(code: str):
    s = parse(code)
    return s, commands(s)
