"""MISUMI 5 series (slot width 6 mm) extruded brackets: thick (HBLTS5, HBLTS5-4, HBLTSB5, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5,
HBLTVW5), scalene (HBLTF5), thick perpendicularly machined with tabs (HBKTST5, HBKTS5, HBKTSB5), ultra thick (NBLUS5, HBLUS5),
ultra thick with tabs (HBKUS5, HBKUSB5) and eccentric (HBLTH5, HBLTHB5), each with the optional alteration C (M5 taps) or a screw
set (SET, SST, SEU, SSU, SEP, SSP, SEC). Ordering-code parser, catalogue data and native-SolidCraft command builder.

Source (id S40 in sources.toml): MISUMI FA catalogue 2014, "Extruded Brackets - For 1 Slot, For 5 Series (Slot Width 6mm)", pages 2-539
and 2-540, https://in.misumi-ec.com/pdf/fa/2014/p2_539.pdf.
Published: width, plate thickness, arm lengths, hole diameter and hole positions measured from the outer face of the other arm, the 6 wide
and 1 high tabs of the HBK types, material and surface per code. Not drawn (no dimensions printed): the inner-corner web and its ribs,
the tab length, the taps of alteration C and the screw sets (accessory only, written into the description).
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from runtime.table import read_csv, num

class CodeError(ValueError):
    """The ordering code is not valid; the message says why."""

class NotModelled(CodeError):
    """Valid MISUMI grammar that this generator does not build."""

DATA = Path(__file__).resolve().parent.parent / "data"
_P = {_r["name"]: num(_r["value"]) for _r in read_csv(DATA / "params.csv")}
T = _P["thickness"]  # plate thickness of the 5 mm families (the ultra thick types carry foot_t / wall_t in types.csv)
ALTS = {_r["code"]: _r for _r in read_csv(DATA / "alterations.csv")}
RELIEF_D, RELIEF_AT = _P["relief_d"], _P["relief_at"]

def _pos(s): return tuple(num(x) for x in s.split("|"))
TYPES = {_r["type"]: _r for _r in read_csv(DATA / "types.csv")}
# same catalogue pages, valid codes, not drawn here
OTHER = {"HBLFSN5", "HBLFSL5", "HBLFSR5", "HBLFSNK5", "HBLFSNT5", "HBLFSSW5", "HBLFSNF5", "HBLS5", "HBLSS5", "HBLCD5"}

@dataclass
class Bracket:
    code: str
    type: str
    W: float
    foot: float
    wall: float
    foot_holes: tuple
    wall_holes: tuple
    hole_d: float
    material: str
    surface: str
    mass: float
    screw: str
    nut: str
    allowable: float
    square: int
    foot_t: float = 5
    wall_t: float = 5
    wall_t_approx: bool = False
    tab_w: float = 0
    tab_h: float = 0
    hole_x: float | None = None
    perp_k: str = ""
    alt: str = ""
    base_type: str = ""
    family: str = ""

    @property
    def x_hole(self) -> float:
        """Position of the hole centres across the width (the centre line unless the type is eccentric)."""
        return self.W / 2 if self.hole_x is None else self.hole_x

    @property
    def description(self) -> str:
        d = (f"MISUMI extruded bracket {self.base_type} for 5 series (slot width 6 mm) extrusions ({self.family}), {self.square} square, "
             f"{self.W:g} wide, {self.foot_t:g} thick, arms {self.foot:g} x {self.wall:g} mm, "
             f"{len(self.foot_holes) + len(self.wall_holes)} holes O{self.hole_d:g}, {self.material}, {self.surface}, "
             f"catalogue mass {self.mass:g} g, screw {self.screw}, T nut {self.nut}, allowable load {self.allowable:g} N.")
        if self.hole_x is not None:
            d += f" Eccentric: the holes are {self.hole_x:g} from one side and {self.W - self.hole_x:g} from the other."
        if self.tab_w:
            d += (f" Perpendicularly machined, perpendicularity K {self.perp_k}; tabs {self.tab_w:g} wide and {self.tab_h:g} high "
                  "on the bottom of the arms fit the 6 mm slot (length not dimensioned in the catalogue).")
        if self.alt == "C":
            d += " Alteration C: M5 taps on both sides for cover mounting (not drawn; mounting screw HCBM)."
        elif self.alt:
            a = ALTS[self.alt]
            d += f" Alteration {self.alt}: {a['name']} supplied in a set with the bracket (accessory, not drawn)."
            if self.base_type == "HBLTS5":
                d += f" For HBLTS5 the set is screw {a['screw']} and nut {a['nut']}."
            else:
                d += " The catalogue lists the set contents for HBLTS5 only; check the applicable screws and nuts for this bracket."
            if "Black" in self.surface:
                d += " Screws for black anodized brackets are HCBMTB (Trivalent Chromate Black)."
        d += " Generated from the published catalogue dimensions; the inner-corner web with its ribs is not drawn."
        return d

def _bracket(key: str, code: str, alt: str) -> Bracket:
    r = TYPES[key]
    hx = num(r["hole_x"])
    return Bracket(code=code, type=key, W=num(r["width"]), foot=num(r["foot"]), wall=num(r["wall"]),
                   foot_holes=_pos(r["foot_holes"]), wall_holes=_pos(r["wall_holes"]), hole_d=num(r["hole_d"]),
                   material=r["material"], surface=r["surface"], mass=num(r["mass_g"]), screw=r["screw"], nut=r["nut"],
                   allowable=num(r["allowable_n"]), square=num(r["square"]), foot_t=num(r["foot_t"]), wall_t=num(r["wall_t"]),
                   wall_t_approx=r["wall_t_approx"] == "1", tab_w=num(r["tab_w"]), tab_h=num(r["tab_h"]), hole_x=hx,
                   perp_k=r["perp_k"], alt=alt, base_type=key, family=r["family"])

def parse(code: str) -> Bracket:
    c = code.strip().upper()
    toks = c.split("-")
    base, rest = toks[0], toks[1:]
    key = base
    if rest and rest[0] == "4":
        key, rest = base + "-4", rest[1:]
    if key not in TYPES:
        if base in OTHER:
            raise NotModelled(f"{c}: a valid MISUMI 5 series bracket, not drawn here; drawn: {', '.join(t for t in TYPES if '-' not in t)}")
        if base in TYPES:
            raise CodeError(f"{c}: {base} has no -4 version (an M4 screw version exists for HBLTS5 only; the plain code is the M5 one)")
        if base.endswith("6") or base.endswith("8"):
            raise CodeError(f"{c}: only the 5 series (slot width 6 mm) brackets are drawn, e.g. HBLTS5")
        raise CodeError(f"{code!r}: expected a bracket code such as HBLTS5 or HBKUS5; drawn: {', '.join(t for t in TYPES if '-' not in t)}")
    alt = ""
    if rest:
        if len(rest) > 1:
            raise CodeError(f"{c}: one alteration at most ({', '.join(['C', *ALTS])}); the catalogue lists them as alternatives")
        alt = rest[0]
        if alt == "C":
            if TYPES[key]["alt_c"] != "1":
                ok = ", ".join(t for t, r in TYPES.items() if r["alt_c"] == "1")
                raise CodeError(f"{c}: alteration C (M5 taps for cover mounting) is not offered for {key} on the catalogue page; offered for: {ok}")
        elif alt not in ALTS:
            raise CodeError(f"{c}: unknown alteration {alt!r}; the catalogue lists C, {', '.join(ALTS)} (no -5 or other suffix exists)")
    return _bracket(key, c, alt)

def commands(b: Bracket) -> list[dict]:
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    add("component.create", name=b.code)
    add("sketch.create", plane="YZ", name="Profile")
    # L section, y along the foot, z along the wall; the outer faces are y = 0 (wall) and z = 0 (foot)
    add("sketch.line", points=[[0, 0], [b.foot, 0], [b.foot, b.foot_t], [b.wall_t, b.foot_t], [b.wall_t, b.wall], [0, b.wall]], closed=True)
    add("sketch.finish")
    add("solid.extrude", distance=b.W, name="Bracket", body_name=b.code)
    if b.tab_w:
        # tabs for the 6 mm slot on the bottom of both arms: tab_w wide on the centre line, tab_h proud of the outer face;
        # the length is not dimensioned in the catalogue (appearance, approximate): full arm length
        x0 = b.W / 2 - b.tab_w / 2
        add("solid.box", length=b.tab_w, width=b.foot, height=b.tab_h, corner=[x0, 0, -b.tab_h], operation="join",
            targets=[b.code], name="Foot tab (length appearance, approximate)")
        add("solid.box", length=b.tab_w, width=b.tab_h, height=b.wall, corner=[x0, -b.tab_h, 0], operation="join",
            targets=[b.code], name="Wall tab (length appearance, approximate)")
    for i, y in enumerate(b.foot_holes):
        add("solid.cylinder", diameter=b.hole_d, height=b.foot_t + b.tab_h + 2, base=[b.x_hole, y, -b.tab_h - 1], axis="Z", operation="cut",
            targets=[b.code], name=f"Foot hole {i + 1}")
    for i, z in enumerate(b.wall_holes):
        add("solid.cylinder", diameter=b.hole_d, height=b.wall_t + b.tab_h + 2, base=[b.x_hole, -b.tab_h - 1, z], axis="Y", operation="cut",
            targets=[b.code], name=f"Wall hole {i + 1}")
    add("browser.visibility", items=["Profile"], visible=False)
    add("component.metadata.set", component=b.code, part_number=b.code, description=b.description,
        material=f"{b.material}; {b.surface}")
    add("document.metadata.set", values={"part_number": b.code, "description": b.description})
    return cmds

def parse_build(code: str):
    b = parse(code)
    return b, commands(b)
