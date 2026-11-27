"""MISUMI Economy Series shaft collars, aluminium: C-SCSAW (slit), C-SCNPAW (split), C-SCSMAW (slit, 2 through fixing holes) and
C-SCSGAW (slit, 2 counterbored fixing holes). Ordering-code parser, catalogue data and native-SolidCraft command builder.

Also (source S21): the compact collars with urethane of p.546 (E-SCSPD, E-PSCSPD, E-SSCSPD: split type, 2 screws), the slit type for bearing inner mount
C-SCSBNAW (p.546), and the slit type with urethane of p.547 (standard E-SCD / E-PSCD / E-SSCD and compact E-SCDJ / E-PSCDJ / E-SSCDJ). The collar pages
of the catalogue end with p.547 (p.548 starts chapter 05, cable carriers). Their tables are in data/bearing.csv and data/urethane.csv.

Source (every number of the C-SCS... collars, id S20 in sources.toml): MISUMI Economy Series catalogue 2025, "Shaft Collars Slit Type / Split Type" p.544
(printed page 04-159) and "Shaft Collars Slit Type, 2 Through Fixing Holes / 2 Counterbored Fixing Holes" p.545 (04-160), published at
https://th.c.misumi-ec.com/book/THA_EconomySeries_e-catalog2025/files/basic-html/page544.html and page545.html (page images
files/mobile/544.jpg, 545.jpg). Published: inner diameter D, width B, outer diameter D1, clamp screw M (coarse), and for the two fixing-hole
types the hole pitch P and the hole sizes. Not printed, so appearance only: the slit width, the position and depth of the clamp screw hole,
the gap between the two halves of the split type, chamfers.
"""
from __future__ import annotations
import re, math
from dataclasses import dataclass
from pathlib import Path
from runtime.appearance import APPX
from runtime.table import read_csv, num

class CodeError(ValueError):
    """The ordering code is not valid; the message says why."""

class NotModelled(CodeError):
    """Valid MISUMI grammar that this prototype does not build."""

DATA = Path(__file__).resolve().parent.parent / "data"
# type -> (kind, material, surface)       p.544 / p.545 spec tables
TYPES = {_r["type"]: (_r["kind"], _r["material"], _r["surface"]) for _r in read_csv(DATA / "types.csv")}
# (type, D, B) -> row of the size tables
SIZES = {}
for _r in read_csv(DATA / "sizes.csv"):
    SIZES[(_r["type"], int(_r["D"]), int(_r["B"]))] = {k: num(_r[k]) for k in ("D1", "M", "P", "S", "d1", "d2", "t")}
TYPE_EXTRA = {_r["type"]: (_r["accessory"], _r["damper"]) for _r in read_csv(DATA / "types.csv")}
_P = {_r["name"]: num(_r["value"]) for _r in read_csv(DATA / "params.csv")}
BORE_TOL = (_P["bore_tol_upper"], _P["bore_tol_lower"])      # "D +0.05 / +0.01 is the tolerance before cutting"
SLIT_W = _P["slit_width"]                                    # appearance
SPLIT_GAP = _P["split_gap"]                                  # appearance

BEARING = [{k: num(_r[k]) for k in ("D", "Ds", "b", "B", "D1", "M")} for _r in read_csv(DATA / "bearing.csv")]
# (family, D) -> row of data/urethane.csv; family: slit (E-SCD, p.547 standard), slit-compact (E-SCDJ, p.547), split-compact (E-SCSPD, p.546)
URE = {(_r["family"], int(_r["D"])): {k: num(_r[k]) for k in ("B", "D1", "B1", "t", "M", "d", "R", "W", "X", "Y", "stainless")} | {"Z": _r["Z"]}
       for _r in read_csv(DATA / "urethane.csv")}
TOL_URE_SLIT = (_P["bore_tol_slit_urethane_upper"], _P["bore_tol_slit_urethane_lower"])   # +0.06/+0.01 (E-SCD note: up to +0.08)
FAMILY = {"E-SCD": "slit", "E-PSCD": "slit", "E-SSCD": "slit", "E-SCDJ": "slit-compact", "E-PSCDJ": "slit-compact", "E-SSCDJ": "slit-compact",
          "E-SCSPD": "split-compact", "E-PSCSPD": "split-compact", "E-SSCSPD": "split-compact"}
PAGE = {"slit": "p.547 standard type", "slit-compact": "p.547 compact type", "split-compact": "p.546"}
RING_TYPES = ("C-SCSAW", "C-SCNPAW", "C-SCSMAW", "C-SCSGAW")
CODE = re.compile(r"^(C-SCSAW|C-SCNPAW|C-SCSMAW|C-SCSGAW)(\d{1,2})-(\d{1,2})$")
CODE_BEAR = re.compile(r"^(C-SCSBNAW)(\d{1,2})-(\d{1,2})$")
CODE_URE = re.compile(r"^(E-(?:P|S)?(?:SCSPD|SCD))(\d{1,2})$")          # D only: E-SCSPD6, E-SCD12
CODE_UREJ = re.compile(r"^(E-(?:P|S)?SCDJ)(\d{1,2})-(\d{1,2})$")      # D and B selection: E-SCDJ12-10

@dataclass
class Collar:
    code: str
    type: str
    kind: str
    D: int
    B: int
    D1: float
    M: str
    material: str
    surface: str
    P: float | None = None
    S: float | None = None       # C-SCSMAW: through-hole diameter
    d1: float | None = None      # C-SCSGAW: through-hole diameter
    d2: float | None = None      # C-SCSGAW: counterbore diameter
    t: float | None = None       # C-SCSGAW: counterbore depth

    @property
    def split(self) -> bool:
        return self.type == "C-SCNPAW"

    @property
    def clamp_y(self) -> float:
        """Radial position of the clamp screw axis: mid-wall (appearance)."""
        return -(self.D + self.D1) / 4

    @property
    def description(self) -> str:
        d = (f"MISUMI Economy Series shaft collar {self.type}{self.D}-{self.B} ({self.kind}), I.D. D={self.D} mm "
             f"(+{BORE_TOL[0]:.2f}/+{BORE_TOL[1]:.2f} is the tolerance before cutting; drawn at the nominal diameter), width B={self.B} mm, "
             f"O.D. D1={self.D1:g} mm, clamp screw {self.M}, {self.material}, {self.surface.lower()}")
        if self.P is not None:
            d += f", 2 fixing holes on pitch P={self.P:g} mm"
            if self.type == "C-SCSMAW":
                d += f", through holes diameter {self.S:g} mm"
            else:
                d += f", through diameter {self.d1:g} mm, counterbore diameter {self.d2:g} mm depth {self.t:g} mm"
        return d + f". Generated from the published catalogue dimensions; slit, clamp screw position and chamfers are {APPX}."

@dataclass
class Bearing:
    """C-SCSBNAW: slit collar for a bearing inner ring: ring D1 x width b with a boss of diameter Ds, total width B (p.546)."""
    code: str
    type: str
    kind: str
    D: int
    Ds: int
    b: float
    B: float
    D1: float
    M: str
    material: str
    surface: str

    @property
    def clamp_y(self) -> float:
        return -(self.D + self.D1) / 4

    @property
    def description(self) -> str:
        return (f"MISUMI Economy Series shaft collar {self.code} ({self.kind}), I.D. D={self.D} mm "
                f"(+{BORE_TOL[0]:.2f}/+{BORE_TOL[1]:.2f} is the tolerance before cutting; drawn at the nominal diameter), boss diameter Ds={self.Ds} mm, "
                f"ring width b={self.b:g} mm, total width B={self.B:g} mm, O.D. D1={self.D1:g} mm, clamp screw {self.M}, {self.material}, "
                f"{self.surface.lower()}. Generated from the published catalogue dimensions; slit, clamp screw position and chamfers are {APPX}.")

@dataclass
class Urethane:
    """E-SCD / E-SCDJ / E-SCSPD families (p.546, p.547): a steel collar of width B1 with a urethane damper disc of thickness t on one face."""
    code: str
    type: str
    family: str
    kind: str
    D: int
    B: float
    D1: float
    B1: float
    t: float
    M: str
    d: float
    R: float
    W: float
    X: float
    Y: float
    Z: str
    material: str
    surface: str
    accessory: str
    damper: str

    @property
    def split(self) -> bool:
        return self.family == "split-compact"

    @property
    def tol(self) -> tuple:
        return BORE_TOL if self.family == "split-compact" else TOL_URE_SLIT

    @property
    def zc(self) -> float:
        """z of the clamp screw axes: the middle of the steel width B1 (the damper takes z 0..t)."""
        return self.t + self.B1 / 2

    @property
    def description(self) -> str:
        return (f"MISUMI Economy Series shaft collar {self.code} ({self.kind}), I.D. D={self.D} mm "
                f"(+{self.tol[0]:.2f}/+{self.tol[1]:.2f} is the tolerance before cutting; drawn at the nominal diameter), width B={self.B:g} mm "
                f"(steel B1={self.B1:g} mm plus urethane damper t={self.t:g} mm), O.D. D1={self.D1:g} mm (printed +-0.1), clamp screw {self.M} "
                f"(clearance hole d={self.d:g} mm in the other half, head seat 2xR={2 * self.R:g} mm wide from Y={self.Y:g} mm, slit/gap W={self.W:g} mm), "
                f"{'2 screws' if self.split else '1 screw'} at X={self.X:g} mm from the axis, {self.material}, {self.surface.lower()}; "
                f"damper: {self.damper}; accessories: {self.accessory}. Generated from the published catalogue dimensions; "
                f"the damper's look, chamfers, the screws and the (Z) reference notch are {APPX}.")

def _ure(typ: str, D: int, B_sel, raw: str, c: str) -> Urethane:
    fam = FAMILY[typ]
    Dl = sorted(d for f, d in URE if f == fam)
    pg = PAGE[fam]
    if D not in Dl:
        raise CodeError(f"{typ} is offered for D in {', '.join(map(str, Dl))} mm, not {D} ({pg} table)")
    r = URE[(fam, D)]
    if fam == "slit-compact":
        if B_sel != r["B"]:
            raise CodeError(f"{typ}{D} is offered in width B = {r['B']:g} mm only, not {B_sel} ({pg} table, B selection)")
    elif B_sel is not None:
        raise CodeError(f"{raw!r}: {typ} has no width suffix (B follows from D); write {typ}{D} ({pg})")
    if typ.startswith("E-SS") and not r["stainless"]:
        sd = sorted(d for (f, d), v in URE.items() if f == fam and v["stainless"])
        raise CodeError(f"{typ} (stainless steel) is only available for D in {', '.join(map(str, sd))} mm, not {D} ({pg} note)")
    if fam == "slit" and D == 4 and typ != "E-PSCD":
        raise CodeError(f"{typ}4: for D = 4 only the electroless nickel plated E-PSCD4 is available (p.547 note)")
    kind, mat, surf = TYPES[typ]
    return Urethane(code=c, type=typ, family=fam, kind=kind, D=D, B=r["B"], D1=r["D1"], B1=r["B1"], t=r["t"], M=r["M"], d=r["d"], R=r["R"],
                    W=r["W"], X=r["X"], Y=r["Y"], Z=r["Z"], material=mat, surface=surf, accessory=TYPE_EXTRA[typ][0], damper=TYPE_EXTRA[typ][1])

def parse(code: str):
    raw = code
    c = code.strip().upper()
    mb = CODE_BEAR.match(c)
    if mb:
        typ, ds, dss = mb.groups()
        D, Ds = int(ds), int(dss)
        Dl = [r["D"] for r in BEARING]
        if D not in Dl:
            raise CodeError(f"{typ} is offered for I.D. D in {', '.join(map(str, Dl))} mm, not {D} (p.546 table)")
        r = next(r for r in BEARING if r["D"] == D)
        if Ds != r["Ds"]:
            raise CodeError(f"{typ}{D} is offered with selection Ds = {r['Ds']} mm only, not {Ds} (p.546 table; the ordering example is C-SCSBNAW12-16)")
        kind, mat, surf = TYPES[typ]
        return Bearing(code=c, type=typ, kind=kind, D=D, Ds=Ds, b=r["b"], B=r["B"], D1=r["D1"], M=r["M"], material=mat, surface=surf)
    mu = CODE_URE.match(c)
    if mu:
        return _ure(mu.group(1), int(mu.group(2)), None, raw, c)
    mj = CODE_UREJ.match(c)
    if mj:
        return _ure(mj.group(1), int(mj.group(2)), int(mj.group(3)), raw, c)
    if re.match(r"^E-(?:P|S)?SCDJ\d{1,2}$", c):
        raise CodeError(f"{raw!r}: the compact slit type needs the width selection, <type><D>-<B>, e.g. E-SCDJ12-10 (p.547)")
    m = CODE.match(c)
    if not m:
        raise CodeError(f"{raw!r}: expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: {', '.join(RING_TYPES)}); "
                        f"C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms")
    typ, ds, bs = m.groups()
    D, B = int(ds), int(bs)
    Ds = sorted({k[1] for k in SIZES if k[0] == typ})
    if D not in Ds:
        raise CodeError(f"{typ} is offered for I.D. D in {', '.join(map(str, Ds))} mm, not {D} (p.{'545' if typ in ('C-SCSMAW', 'C-SCSGAW') else '544'} table)")
    Bs = sorted(k[2] for k in SIZES if k[0] == typ and k[1] == D)
    if (typ, D, B) not in SIZES:
        raise CodeError(f"{typ}{D} is offered in width B = {', '.join(map(str, Bs))} mm, not {B} (p.{'545' if typ in ('C-SCSMAW', 'C-SCSGAW') else '544'} table)")
    r = SIZES[(typ, D, B)]
    kind, mat, surf = TYPES[typ]
    return Collar(code=c, type=typ, kind=kind, D=D, B=B, D1=r["D1"], M=r["M"], material=mat, surface=surf,
                  P=r["P"], S=r["S"], d1=r["d1"], d2=r["d2"], t=r["t"])

def _ring_commands(s: Collar) -> list[dict]:
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    D, B, D1 = s.D, s.B, s.D1
    add("component.create", name=s.code)
    add("solid.cylinder", diameter=D1, height=B, base=[0, 0, 0], axis="Z", operation="new", body_name=s.code, name="Ring")
    add("solid.cylinder", diameter=D, height=B, base=[0, 0, 0], axis="Z", operation="cut", targets=[s.code], name="Bore")
    yh = s.clamp_y
    if s.split:
        add("solid.box", length=SPLIT_GAP, width=D1 + 2, height=B + 2, corner=[-SPLIT_GAP / 2, -D1 / 2 - 1, -1],
            operation="cut", targets=[s.code], name=f"Split gap {APPX}")
        for sy in (1, -1):
            xh = math.sqrt((D1 / 2) ** 2 - yh ** 2)
            add("solid.hole", position=[xh, sy * yh, B / 2], direction=[-1, 0, 0], thread=s.M, targets=[s.code],
                name=f"Clamp screw hole {sy:+d} {s.M} {APPX}")
    else:
        add("solid.box", length=SLIT_W, width=D1 / 2 + 1, height=B + 2, corner=[-SLIT_W / 2, -D1 / 2 - 1, -1],
            operation="cut", targets=[s.code], name=f"Slit {APPX}")
        xh = math.sqrt((D1 / 2) ** 2 - yh ** 2)
        add("solid.hole", position=[xh, yh, B / 2], direction=[-1, 0, 0], thread=s.M, targets=[s.code],
            name=f"Clamp screw hole {s.M} {APPX}")
    if s.type == "C-SCSMAW":
        for sx in (1, -1):
            add("solid.hole", position=[sx * s.P / 2, 0, B], diameter=s.S, targets=[s.code], name=f"Fixing hole {'+' if sx > 0 else '-'}")
    elif s.type == "C-SCSGAW":
        for sx in (1, -1):
            add("solid.hole", position=[sx * s.P / 2, 0, B], diameter=s.d1, type="counterbore", cb_diameter=s.d2, cb_depth=s.t,
                targets=[s.code], name=f"Counterbored fixing hole {'+' if sx > 0 else '-'}")
    add("component.metadata.set", component=s.code, part_number=s.code, description=s.description,
        material=f"{s.material}; {s.surface}")
    add("document.metadata.set", values={"part_number": s.code, "description": s.description})
    return cmds

def _bearing_commands(s: Bearing) -> list[dict]:
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    add("component.create", name=s.code)
    add("solid.cylinder", diameter=s.D1, height=s.b, base=[0, 0, 0], axis="Z", operation="new", body_name=s.code, name="Ring")
    add("solid.cylinder", diameter=s.Ds, height=s.B - s.b, base=[0, 0, s.b], axis="Z", operation="join", targets=[s.code], name="Boss")
    add("solid.cylinder", diameter=s.D, height=s.B + 2, base=[0, 0, -1], axis="Z", operation="cut", targets=[s.code], name="Bore")
    add("solid.box", length=SLIT_W, width=s.D1 / 2 + 1, height=s.B + 2, corner=[-SLIT_W / 2, -s.D1 / 2 - 1, -1],
        operation="cut", targets=[s.code], name=f"Slit {APPX}")
    xh = math.sqrt((s.D1 / 2) ** 2 - s.clamp_y ** 2)
    add("solid.hole", position=[xh, s.clamp_y, s.b / 2], direction=[-1, 0, 0], thread=s.M, targets=[s.code], name=f"Clamp screw hole {s.M} {APPX}")
    add("component.metadata.set", component=s.code, part_number=s.code, description=s.description, material=f"{s.material}; {s.surface}")
    add("document.metadata.set", values={"part_number": s.code, "description": s.description})
    return cmds

def _urethane_commands(s: Urethane) -> list[dict]:
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    D1, D, t, zc, gap = s.D1, s.D, s.t, s.zc, s.W
    steel, damper = s.code, "Urethane damper"
    add("component.create", name=s.code)
    add("solid.cylinder", diameter=D1, height=s.B1, base=[0, 0, t], axis="Z", operation="new", body_name=steel, name="Collar")
    add("solid.cylinder", diameter=D, height=s.B1 + 2, base=[0, 0, t - 1], axis="Z", operation="cut", targets=[steel], name="Bore")
    # the damper: a disc of thickness t on the face z = 0 (hatched strip of the side view), bore D
    add("solid.cylinder", diameter=D1, height=t, base=[0, 0, 0], axis="Z", operation="new", body_name=damper, name=f"{damper} {APPX}")
    add("solid.cylinder", diameter=D, height=t + 2, base=[0, 0, -1], axis="Z", operation="cut", targets=[damper], name=f"{damper} bore")
    if s.split:
        add("solid.box", length=gap, width=D1 + 2, height=s.B1 + 2, corner=[-gap / 2, -D1 / 2 - 1, t - 1], operation="cut", targets=[steel], name="Split gap W")
        ys = (1, -1)
    else:
        add("solid.box", length=gap, width=D1 / 2 + 1, height=s.B1 + 2, corner=[-gap / 2, -D1 / 2 - 1, t - 1], operation="cut", targets=[steel], name="Slit W")
        ys = (-1,)
    for sy in ys:
        ya = sy * s.X
        tag = f"{sy:+d}" if s.split else ""
        # left half: tapped M, from the slit face outwards
        add("solid.hole", position=[-gap / 2, ya, zc], direction=[-1, 0, 0], thread=s.M, targets=[f"{steel} (1)" if s.split else steel], name=f"Clamp screw thread {s.M} {tag}".strip())
        # right half: clearance hole d from the slit to the floor of the head seat (at x = Y), then the seat of width 2R, open to the outside
        add("solid.cylinder", diameter=s.d, height=s.Y + 1, base=[0, ya, zc], axis="X", operation="cut", targets=[steel], name=f"Clearance hole d {tag}".strip())
        lo, hi = (-D1 / 2 - 1, ya) if sy < 0 else (ya, D1 / 2 + 1)
        add("solid.box", length=D1 / 2 + 1 - s.Y, width=hi - lo, height=2 * s.R, corner=[s.Y, lo, zc - s.R], operation="cut", targets=[steel],
            name=f"Head seat slot {tag}".strip())
        add("solid.cylinder", diameter=2 * s.R, height=D1 / 2 + 1 - s.Y, base=[s.Y, ya, zc], axis="X", operation="cut", targets=[steel], name=f"Head seat R {tag}".strip())
    add("component.metadata.set", component=s.code, part_number=s.code, description=s.description, material=f"{s.material}; {s.surface}; damper {s.damper}")
    add("document.metadata.set", values={"part_number": s.code, "description": s.description})
    return cmds

def commands(s) -> list[dict]:
    if isinstance(s, Bearing):
        return _bearing_commands(s)
    if isinstance(s, Urethane):
        return _urethane_commands(s)
    return _ring_commands(s)

def parse_build(code: str):
    s = parse(code)
    return s, commands(s)
