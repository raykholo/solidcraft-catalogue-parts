"""MISUMI pre-assembly insertion nuts for 5 series (slot width 6 mm) aluminium extrusions: HNTT5, HNTTV5, HNTTZ5, HNTTSN5,
HNTTSS5. Ordering-code parser, catalogue data and native-SolidCraft command builder.

Source (id S9 in sources.toml): MISUMI FA catalogue 2014, "Pre-Assembly Insertion Nuts / Stoppers for Aluminum Extrusions -
Standard, For 5 Series (Slot Width 6mm)", page 2-559, https://in.misumi-ec.com/pdf/fa/2014/p2_559.pdf (and the overview p.2-557).
Published: plan 10 x 10, side width 5.8, E and T per type, thread M, ordering "HNTT5 - M", default M5 when M is omitted, reference
tightening torque. Measured from the vector side view of the same drawing (sources.toml): the flank from the 5.8 mm bottom to the 10 mm body.
"""
from __future__ import annotations
import re
from dataclasses import dataclass

class CodeError(ValueError):
    """The ordering code is not valid; the message says why."""

class NotModelled(CodeError):
    """Valid MISUMI grammar that this prototype does not build."""

# Tables live in data/*.csv (every row cites sources.toml; S9 p.559).
from pathlib import Path
from runtime.table import read_csv, num
DATA = Path(__file__).resolve().parent.parent / "data"
# type -> (description, material, surface, allowed M, E, T)   p.2-559 table
TYPES = {_r["type"]: (_r["kind"], _r["material"], _r["surface"], tuple(num(m) for m in _r["allowed_m"].split("|")), num(_r["E"]), num(_r["T"]))
         for _r in read_csv(DATA / "types.csv")}
_P = {_r["name"]: num(_r["value"]) for _r in read_csv(DATA / "params.csv")}
OTHER = {"HNTU5", "HNTUV5", "HNTUZ5", "SHNTU5", "HNTTBS5", "HNTJ5", "HNTE5", "SHNTE5", "HNST5", "SHNST5"}
TORQUE_M5 = _P["torque_m5"]

PLAN = _P["plan"]
NECK = _P["neck"]
# flank from the 5.8 bottom to the 10 body: height of the flank (measured on the drawing, about 35 degrees from the nut axis)
FLANK_H = _P["flank_h"]
DEFAULT_M = _P["default_m"]
# edge rounds seen on the side view, none dimensioned: appearance, approximate (sources.toml row 2001)
R_BOTTOM, R_FLANK_TOP, R_EDGE = _P["round_bottom"], _P["round_flank_top"], _P["round_edge"]
# tap drill (pilot bore) per thread: ISO coarse tap drill, status "derived" (sources.toml row 2000)
PILOT = {int(num(_r["m"])): num(_r["pilot"]) for _r in read_csv(DATA / "tap.csv")}

CODE = re.compile(r"^(S?HNT[A-Z]*5)(?:-(\d+(?:\.\d)?))?$")

@dataclass
class Nut:
    code: str
    type: str
    kind: str
    material: str
    surface: str
    M: int
    E: float
    T: float
    notes: list

    @property
    def description(self) -> str:
        d = (f"MISUMI pre-assembly insertion nut {self.type} ({self.kind}) for 5 series (slot width 6 mm) extrusions, M{self.M}, "
             f"{PLAN:g} x {PLAN:g} mm plan, E={self.E:g}, T={self.T:g}, {self.material}")
        if self.surface != "-":
            d += f", {self.surface}"
        if self.M == 5:
            d += f", reference tightening torque {TORQUE_M5:g} N m"
        return d + ". Generated from the published catalogue dimensions; the flank profile and the edge rounds are measured from the drawing; the tap drill is the ISO coarse one."

def parse(code: str) -> Nut:
    c = code.strip().upper()
    m = CODE.match(c)
    if not m:
        raise CodeError(f"{code!r}: expected <type>-<M>, e.g. HNTT5-4 (types: {', '.join(TYPES)})")
    typ, ms = m.groups()
    if typ not in TYPES:
        if typ in OTHER:
            raise NotModelled(f"{typ}: a valid 5 series nut, not drawn here; drawn: {', '.join(TYPES)}")
        raise CodeError(f"unknown nut type {typ!r}; drawn: {', '.join(TYPES)}")
    kind, mat, surf, Ms, E, T = TYPES[typ]
    notes = []
    if ms is None:
        M = DEFAULT_M
        notes.append("M omitted: M5 is selected automatically (catalogue note)")
        c = f"{typ}-{M}"
    else:
        if "." in ms or int(ms) not in Ms:
            raise CodeError(f"{typ} is offered in " + ", ".join(f"M{x}" for x in Ms) + f", not M{ms}")
        M = int(ms)
    return Nut(code=c, type=typ, kind=kind, material=mat, surface=surf, M=M, E=E, T=T, notes=notes)

def section(n: Nut):
    """Cross-section across the slot (y = across, z = height from the bottom face), closed, CCW: bottom 5.8 wide, 45-ish flank to 10 wide
    at FLANK_H, 10 wide up to E, a 5.8 wide neck up to T."""
    b, w = NECK / 2, PLAN / 2
    return [(-b, 0.0), (b, 0.0), (w, FLANK_H), (w, n.E), (b, n.E), (b, n.T), (-b, n.T), (-b, n.E), (-w, n.E), (-w, FLANK_H)]

def flank_top_radius(n: Nut) -> float:
    """The drawn R1.0 round between the flank and the 10 wide body ends about at E - R0.2 on the E 3.5 nut; on the E 3.3 types the land
    is shorter, so the radius is reduced to keep the two rounds from overlapping."""
    import math
    t_max = n.E - R_EDGE - FLANK_H
    return min(R_FLANK_TOP, t_max / math.tan(math.radians(17.5)))

def commands(n: Nut) -> list[dict]:
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    add("component.create", name=n.code)
    add("sketch.create", plane="YZ", name="Profile")
    add("sketch.line", points=[[y, z] for y, z in section(n)], closed=True)
    # section corners p0..p9 -> l{i}.end is p{i} (p0 is l10.end); rounds are appearance only (row 2001)
    ref = lambda *idx: [f"l{i % 10 or 10}.end" for i in idx]
    add("sketch.fillet", points=ref(0, 1), radius=R_BOTTOM)
    add("sketch.fillet", points=ref(2, 9), radius=flank_top_radius(n))
    add("sketch.fillet", points=ref(3, 8, 5, 6), radius=R_EDGE)
    add("sketch.finish")
    add("solid.extrude", distance=PLAN, name="Nut", body_name=n.code)
    # Tapped hole (repo convention, sources.toml row 2000): the modelled hole is the tap drill (pilot bore), never the nominal diameter;
    # the thread is a cosmetic solid.thread of the nominal size laid on it, through the whole thickness T.
    r = PILOT[n.M] / 2
    add("solid.cylinder", diameter=PILOT[n.M], height=n.T + 2, base=[PLAN / 2, 0, -1], axis="Z", operation="cut",
        targets=[n.code], name=f"Pilot bore O{PILOT[n.M]:g}")
    add("solid.thread", face=[PLAN / 2 + r, 0, n.T / 2], designation=f"M{n.M}", extent="length", length=n.T,
        **{"from": [PLAN / 2 + r, 0, n.T]}, name=f"Thread M{n.M}")
    add("browser.visibility", items=["Profile"], visible=False)
    add("component.metadata.set", component=n.code, part_number=n.code, description=n.description,
        material=f"{n.material}" + ("" if n.surface == "-" else f"; {n.surface}"))
    add("document.metadata.set", values={"part_number": n.code, "description": n.description})
    return cmds

def parse_build(code: str):
    n = parse(code)
    return n, commands(n)
