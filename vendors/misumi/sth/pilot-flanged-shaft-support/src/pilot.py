"""MISUMI Economy Series pilot flanged shaft supports E-STHWIRB (round) / E-STHWICB (compact): ordering-code parser, catalogue data and
native-SolidCraft command builder. Every number is a row of data/dims.csv / data/types.csv with a source id and page (S18, p.540).

Frame: the shaft bore runs along Z; z = 0 is the pilot (spigot) end face. The spigot (O D1, h8) is T long, the flange (T thick) follows from
z = T to 2 T, the sleeve (O D1) runs on to z = L1 (overall length). The clamp features sit on +Y: the radial slit along Y over the ring
length B at the sleeve end, the groove S1 wide in front of the ring, the clamp screw along X at height X above the shaft axis, clearance hole
and counterbore on -X, tapped hole on +X. Round flanges are O H with 4 holes on the diameter P (on the axes); compact flanges are W (X) by H (Y)
with 4 holes on F (X) by P1 (Y).
"""
from __future__ import annotations
import math
import re
from dataclasses import dataclass
from pathlib import Path
from runtime.table import read_csv, num

class CodeError(ValueError):
    """The ordering code is not valid; the message says why."""

DATA = Path(__file__).resolve().parent.parent / "data"
PAGE = "p.540"

def _table():
    out = {}
    for r in read_csv(DATA / "dims.csv"):
        out[int(r["D"])] = {k: (v if k in ("source", "page", "status") else (None if v == "" else num(v))) for k, v in r.items()}
    return out

TABLE = _table()
TYPES = {r["type"]: r for r in read_csv(DATA / "types.csv")}
CORNER_R_FACTOR = 0.25      # compact flange corner radius = W / 4 (appearance, approximate)
FAMILY_NAME = {"round": "round flanged", "compact": "compact flanged"}

@dataclass
class Support:
    code: str
    type: str
    family: str
    D: int
    dims: dict
    material: str
    surface: str

    @property
    def L(self):
        """overall length of the part (pilot end face to sleeve end)"""
        return self.dims["L1"]

    @property
    def tol(self):
        return (self.dims["tol_upper"], self.dims["tol_lower"])

    @property
    def wall(self):
        return (self.dims["D1"] - self.D) / 2

    @property
    def description(self) -> str:
        d = self.dims
        tol = f"{self.tol[0]:+.3f}/{self.tol[1]:+.3f} mm"
        return (f"MISUMI Economy shaft support {self.type}{self.D} (pilot flanged, {FAMILY_NAME[self.family]}), hole D{self.D} H8 ({tol}), "
                f"sleeve and pilot O{d['D1']:g} h8, overall length L1={d['L1']:g}, pilot T={d['T']:g} and flange T={d['T']:g}, "
                f"clamp groove S1={d['S1']:g}, slit {d['S']:g}, clamp screw M{d['M']:g} (one hex socket head cap screw supplied), "
                f"{self.material}, {self.surface}. Generated from the published catalogue dimensions.")

def parse(code: str) -> Support:
    raw = code
    c = code.strip().upper()
    m = re.fullmatch(r"(E-[A-Z]+?)(\d+)", c)
    if not m or m.group(1) not in TYPES:
        raise CodeError(f"{raw!r}: expected <type><D>, e.g. E-STHWIRB8, with type one of {', '.join(TYPES)}")
    typ, ds = m.groups()
    D = int(ds)
    if D not in TABLE:
        raise CodeError(f"{typ}{D}: hole diameter D must be one of {sorted(TABLE)} ({PAGE} table)")
    t = TYPES[typ]
    return Support(code=c, type=typ, family=t["family"], D=D, dims=TABLE[D], material=t["material"], surface=t["surface"])

def hole_positions(s: Support):
    d = s.dims
    if s.family == "round":
        r = d["P"] / 2
        return [(r, 0), (0, r), (-r, 0), (0, -r)]
    f, p = d["F"] / 2, d["P1"] / 2
    return [(f, p), (-f, p), (f, -p), (-f, -p)]

def clamp_geometry(s: Support):
    """clamp screw: outer radius, z of the screw axis, ring start z, ring length B, groove z0, groove width, radial slit width, clearance hole, counterbore"""
    d = s.dims
    L = d["L1"]
    return dict(ro=d["D1"] / 2, zc=L - d["B"] / 2, ring0=L - d["B"], B=d["B"], g0=L - d["B"] - d["S1"], gw=d["S1"], slit=d["S"], clear=d["d2"], cb=d["d1"])

def commands(s: Support) -> list[dict]:
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    d, D, L, T = s.dims, s.D, s.dims["L1"], s.dims["T"]
    add("component.create", name=s.code)
    add("sketch.create", plane={"origin": [0, 0, T], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="Flange")
    if s.family == "round":
        add("sketch.circle.center", center=[0, 0], diameter=d["H"])
    else:
        w, h = d["W"] / 2, d["H"] / 2
        add("sketch.line", points=[[-w, -h], [w, -h], [w, h], [-w, h]], closed=True)
        add("sketch.fillet", points=[f"l{i}.end" for i in range(1, 5)], radius=d["W"] * CORNER_R_FACTOR)
    add("sketch.finish")
    add("solid.extrude", distance=T, name="Flange", body_name=s.code)
    add("solid.cylinder", diameter=d["D1"], height=L, base=[0, 0, 0], axis="Z", operation="join", targets=[s.code], name="Pilot and sleeve")
    add("solid.cylinder", diameter=D, height=L + 2, base=[0, 0, -1], axis="Z", operation="cut", targets=[s.code], name="Shaft hole")
    for i, (x, y) in enumerate(hole_positions(s), 1):
        add("solid.cylinder", diameter=d["d"], height=T + 2, base=[x, y, T - 1], axis="Z", operation="cut", targets=[s.code], name=f"Mounting hole {i}")
    clamp(add, s)
    add("browser.visibility", items=["Flange"], visible=False)
    add("component.metadata.set", component=s.code, part_number=s.code, description=s.description, material=f"{s.material}; {s.surface}")
    add("document.metadata.set", values={"part_number": s.code, "description": s.description})
    return cmds

def clamp(add, s: Support):
    """groove (width and position printed, depth to the bottom of the bore read from the figure), radial slit on +Y over the ring, and the
    clamp screw along X: clearance hole and counterbore on -X (the counterbore floor Y from the slit centre), tapped hole on +X"""
    d, D = s.dims, s.D
    g = clamp_geometry(s)
    ro = g["ro"]
    add("solid.box", length=2 * ro + 2, width=ro + 1 + D / 2, height=g["gw"], corner=[-ro - 1, -D / 2, g["g0"]], operation="cut", targets=[s.code], name="Groove")
    add("solid.box", length=g["slit"], width=ro + 1, height=g["B"] + 1, corner=[-g["slit"] / 2, 0, g["ring0"]], operation="cut", targets=[s.code], name="Slit")
    xo = math.sqrt(ro ** 2 - d["X"] ** 2)
    base = [-xo - 1, d["X"], g["zc"]]
    add("solid.cylinder", diameter=g["clear"], height=xo + 1, base=base, axis="X", operation="cut", targets=[s.code], name="Clamp screw clearance hole")
    add("solid.cylinder", diameter=g["cb"], height=xo + 1 - d["Y"], base=base, axis="X", operation="cut", targets=[s.code], name="Clamp screw counterbore")
    add("solid.hole", position=[xo, d["X"], g["zc"]], direction=[-1, 0, 0], thread=f"M{d['M']:g}", depth=xo - g["slit"] / 2, targets=[s.code], name="Clamp screw thread")

def parse_build(code: str):
    s = parse(code)
    return s, commands(s)
