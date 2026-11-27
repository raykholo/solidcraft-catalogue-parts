"""MISUMI Economy Series flanged shaft supports (steel, stainless): ordering-code parser, catalogue data and native-SolidCraft command builder.

Series in this generator (every number is a row of data/*.csv with a source id and page, cited in sources.toml):
  std    standard sleeve E-STHRB / E-STHR / E-STHSB / E-STHS / E-STHCB / E-STHC / E-SSTHC and their long sleeve types (...L)   S51 p.534-535
  thick  thickened E-STHRBN / E-STHRN / E-STHCBN / E-STHCN and long sleeve (...NL)                                              S52 p.536
  xend   end mounting E-STHXRB / E-STHXR / E-STHXCB / E-STHXC                                                                    S52 p.533
  slit   flanged with slit E-STHWRB .. E-SSTHWC and long sleeve (...L)                                                          S52 p.538-539
  mr     compact standard / long sleeve E-STHMRB / E-STHMR (a clamp collar with two mounting holes, no flange)                  S52 p.532

Frame: the shaft bore runs along Z; the flange back face is z = 0, the flange is T thick, the sleeve (O D1) runs to z = L (long sleeve:
z = L1). Round flanges are O H; square flanges are a square of side K standing on a corner (vertices on the X / Y axes) with the corners cut so
that the extent across them is H; compact flanges are W (X) by H (Y). The clamp features of the slit types and of E-STHMR sit on +Y: the radial slit
along the Y axis, the clamp screw axis along X at height X above the shaft axis.
"""
from __future__ import annotations
import math
import re
from dataclasses import dataclass
from pathlib import Path
from runtime.table import read_csv, num
from runtime.appearance import APPX

class CodeError(ValueError):
    """The ordering code is not valid; the message says why."""

DATA = Path(__file__).resolve().parent.parent / "data"
NOTNUM = ("source", "page", "status", "M")

def _table(name, keep_m_text=False):
    out = {}
    for r in read_csv(DATA / name):
        row = {k: (v if k in ("source", "page", "status") else (None if v == "" else num(v))) for k, v in r.items()}
        out[int(r["D"])] = row
    return out

TABLES = {"std": _table("dims.csv"), "thick": _table("thick.csv"), "xend": _table("xend.csv"),
          "slit": _table("slit.csv"), "slit_long": _table("slit_long.csv"), "mr": _table("mr.csv")}
TYPES = {r["type"]: r for r in read_csv(DATA / "types.csv")}
CORNER_R_FACTOR = 0.25      # compact flange corner radius = W / 4 (appearance, approximate)
FAMILY_NAME = {"round": "round flanged", "square": "square flanged", "compact": "compact flanged", "collar": "compact clamp"}
SERIES_NAME = {"std": "standard sleeve", "thick": "thickened", "xend": "end mounting", "slit": "flanged with slit", "mr": "compact"}
PAGES = {"std": "p.534-535", "thick": "p.536", "xend": "p.533", "slit": "p.538-539", "mr": "p.532"}
FAMILIES_TEXT = ("E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), "
                 "E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), "
                 "E-STHWRB .. E-SSTHWC and ...L (slit)")

@dataclass
class Support:
    code: str
    type: str
    series: str
    family: str
    long: bool
    D: int
    dims: dict
    material: str
    surface: str

    @property
    def L(self):
        """overall length of the part (back face to sleeve end)"""
        d = self.dims
        return d["L1"] if self.long and d.get("L1") is not None else d["L"]

    @property
    def tol(self):
        return (self.dims["tol_upper"], self.dims["tol_lower"])

    @property
    def wall(self):
        return (self.dims["D1"] - self.D) / 2

    @property
    def hole_d(self):
        """diameter of the flange mounting holes"""
        return self.dims["d"] if self.series in ("xend", "slit") else self.dims["d1"]

    @property
    def screw_z(self):
        """z of the set screw stations (standard / thickened series): from the back face, l (standard), l1 (long); D16 and up have two"""
        d = self.dims
        if not self.long:
            return [d["l"]]
        return [d["l1"]] if self.D == 12 else [d["l1"], 2 * d["l1"]]

    @property
    def description(self) -> str:
        d = self.dims
        tol = f"{self.tol[0]:+.3f}/{self.tol[1]:+.3f} mm"
        kind = f"{FAMILY_NAME[self.family]}, {SERIES_NAME[self.series]}{', long sleeve' if self.long else ''}"
        head = f"MISUMI Economy shaft support {self.type}{self.D} ({kind}), hole D{self.D} H8 ({tol}), "
        tail = f"{self.material}, {self.surface}. Generated from the published catalogue dimensions."
        if self.series in ("std", "thick"):
            sc = len(self.screw_z) * 2
            return head + (f"sleeve O{d['D1']:g} x L={self.L:g}, flange T={d['T']:g}, {sc} x M{d['M']:g} set screw holes (l from the flange back face), " + tail)
        if self.series == "xend":
            return head + (f"sleeve O{d['D1']:g} x L={d['L']:g}, flange T={d['T']:g}, blind hole to l1={d['l1']:g}, mounting screw M{d['M']:g} through O{d['d2']:g} / counterbore O{d['d1']:g} "
                           f"depth l={d['l']:g}, " + tail)
        if self.series == "slit":
            return head + (f"sleeve O{d['D1']:g} x L={d['L']:g}, flange T={d['T']:g}, clamp groove S1={d['S1']:g}, slit {d['S']:g}, clamp screw M{d['M']:g} (one hex socket head cap screw supplied; "
                           "two for the long sleeve, which has two clamp screws at B / 4 and 3 B / 4), " + tail)
        return head + (f"body O{d['H']:g} x L={self.L:g}, clamp groove S={d['S']:g}, clamp screw M{d['M']:g} (one hex socket head cap screw supplied), 2 mounting holes O{d['d1']:g} on P={d['P']:g}, " + tail)

def parse(code: str) -> Support:
    raw = code
    c = code.strip().upper()
    m = re.fullmatch(r"(E-[A-Z]+?)(\d+)", c)
    if not m or m.group(1) not in TYPES:
        raise CodeError(f"{raw!r}: expected <type><D>, e.g. E-STHRB8, with type one of {FAMILIES_TEXT}")
    typ, ds = m.groups()
    D = int(ds)
    t = TYPES[typ]
    series, long = t["series"], t["long"] == "1"
    table = TABLES["slit_long" if (series == "slit" and long) else series]
    page = PAGES[series]
    if D not in table:
        raise CodeError(f"{typ}{D}: hole diameter D must be one of {sorted(table)} ({page})")
    dims = table[D]
    if long and series != "slit" and dims.get("L1") is None:
        ok = sorted(k for k, v in table.items() if v.get("L1") is not None)
        raise CodeError(f"{typ}{D}: the long sleeve type is only applicable to the D marked * in the table: {ok} ({page})")
    if t["not_applicable_d"] and D in {int(x) for x in t["not_applicable_d"].split("|")}:
        raise CodeError(f"{typ} is not applicable when D = {D} ({page} note)")
    return Support(code=c, type=typ, series=series, family=t["family"], long=long, D=D, dims=dims, material=t["material"], surface=t["surface"])

def flange_outline(s: Support):
    """closed polygon of the flange in (x, y); the compact one is a rectangle that gets corner radii afterwards."""
    d = s.dims
    if s.family == "square":
        # K is the side of the square, H the extent across the cut corners (tip to tip along X and Y): the corner flats sit at +-H/2
        t = d["H"] / 2
        e = d["K"] / math.sqrt(2) - t
        pts = []
        for ux, uy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            vx, vy = -uy, ux
            pts.append([t * ux - e * vx, t * uy - e * vy])
            pts.append([t * ux + e * vx, t * uy + e * vy])
        return pts
    w, h = d["W"] / 2, d["H"] / 2
    return [[-w, -h], [w, -h], [w, h], [-w, h]]

def hole_positions(s: Support):
    d = s.dims
    if s.series == "mr":
        return [(d["P"] / 2, 0), (-d["P"] / 2, 0)]
    if s.family in ("round", "square"):
        r = d["P"] / 2
        return [(r, 0), (0, r), (-r, 0), (0, -r)]
    p = d["P1"] / 2
    if d["F"] is None:
        return [(0, p), (0, -p)]
    f = d["F"] / 2
    return [(f, p), (-f, p), (f, -p), (-f, -p)]

def clamp_geometry(s: Support):
    """clamp screw of the slit types and of E-STHMR: (outer radius, z of the screw axis, ring start z, ring length B, groove z0, groove width,
    radial slit width, clearance hole O, counterbore O)"""
    d = s.dims
    if s.series == "mr":
        ro, L = d["H"] / 2, s.L
        t = d["T1"] if s.long else d["T"]
        return dict(ro=ro, zc=L - d["B"] / 2, zcs=[L - d["B"] / 2], ring0=L - d["B"], B=d["B"], g0=t, gw=d["S"], slit=1.5, clear=d["d"], cb=d["R"])
    ro, L = d["D1"] / 2, d["L"]
    # standard sleeve: one clamp screw at B / 2 from the sleeve end; slit long sleeve (p.538 figure, 2-d1): two, at B / 4 and 3 B / 4
    zcs = [L - d["B"] / 4, L - 3 * d["B"] / 4] if s.long else [L - d["B"] / 2]
    return dict(ro=ro, zc=zcs[0], zcs=zcs, ring0=L - d["B"], B=d["B"], g0=L - d["B"] - d["S1"], gw=d["S1"], slit=d["S"], clear=d["d2"], cb=d["d1"])

def commands(s: Support) -> list[dict]:
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    d = s.dims
    D, L = s.D, s.L
    add("component.create", name=s.code)
    if s.series == "mr":
        body_cylinder(add, s)
    else:
        D1, T = d["D1"], d["T"]
        add("sketch.create", plane={"origin": [0, 0, 0], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="Flange")
        if s.family == "round":
            add("sketch.circle.center", center=[0, 0], diameter=d["H"])
        else:
            add("sketch.line", points=flange_outline(s), closed=True)
            if s.family == "compact":
                add("sketch.fillet", points=[f"l{i}.end" for i in range(1, 5)], radius=d["W"] * CORNER_R_FACTOR)
        add("sketch.finish")
        add("solid.extrude", distance=T, name="Flange", body_name=s.code)
        add("solid.cylinder", diameter=D1, height=L, base=[0, 0, 0], axis="Z", operation="join", targets=[s.code], name="Sleeve")
        if s.series == "xend":
            add("solid.cylinder", diameter=D, height=L - d["l1"] + 1, base=[0, 0, d["l1"]], axis="Z", operation="cut", targets=[s.code], name="Shaft hole (blind)")
            add("solid.cylinder", diameter=d["d2"], height=d["l1"] + 2, base=[0, 0, -1], axis="Z", operation="cut", targets=[s.code], name="Mounting screw hole")
            add("solid.cylinder", diameter=d["d1"], height=d["l"] + 1, base=[0, 0, -1], axis="Z", operation="cut", targets=[s.code], name="Mounting screw counterbore")
        else:
            add("solid.cylinder", diameter=D, height=L + 2, base=[0, 0, -1], axis="Z", operation="cut", targets=[s.code], name="Shaft hole")
        for i, (x, y) in enumerate(hole_positions(s), 1):
            add("solid.cylinder", diameter=s.hole_d, height=T + 2, base=[x, y, -1], axis="Z", operation="cut", targets=[s.code], name=f"Mounting hole {i}")
    if s.series in ("std", "thick"):
        set_screws(add, s)
    if s.series in ("slit", "mr"):
        clamp(add, s)
    if s.series != "mr":
        add("browser.visibility", items=["Flange"], visible=False)
    add("component.metadata.set", component=s.code, part_number=s.code, description=s.description, material=f"{s.material}; {s.surface}")
    add("document.metadata.set", values={"part_number": s.code, "description": s.description})
    return cmds

def body_cylinder(add, s: Support):
    """E-STHMR: the body is a plain cylinder O H x L with the shaft bore and the two counterbored mounting holes on P"""
    d, D, L = s.dims, s.D, s.L
    add("solid.cylinder", diameter=d["H"], height=L, base=[0, 0, 0], axis="Z", operation="new", body_name=s.code, name="Body")
    add("solid.cylinder", diameter=D, height=L + 2, base=[0, 0, -1], axis="Z", operation="cut", targets=[s.code], name="Shaft hole")
    for i, (x, y) in enumerate(hole_positions(s), 1):
        add("solid.cylinder", diameter=d["d1"], height=L + 2, base=[x, y, -1], axis="Z", operation="cut", targets=[s.code], name=f"Mounting hole {i}")
        # the counterbore diameter d2 is printed, its depth is not: drawn B deep from the clamp end (appearance)
        add("solid.cylinder", diameter=d["d2"], height=d["B"] + 1, base=[x, y, L - d["B"]], axis="Z", operation="cut", targets=[s.code], name=f"Counterbore {i} {APPX}")

def set_screws(add, s: Support):
    """2 set screw holes 90 degrees apart at every station (the angular position about the axis is not dimensioned)"""
    d = s.dims
    D1 = d["D1"]
    k = 0
    for z in s.screw_z:
        for origin, xd, yd in (([D1 / 2, 0, z], [0, 1, 0], [0, 0, 1]), ([0, D1 / 2, z], [0, 0, 1], [1, 0, 0])):
            k += 1
            add("sketch.create", plane={"origin": origin, "x_dir": xd, "y_dir": yd}, name=f"Set screw {k} sketch")
            add("sketch.point", point=[0, 0])
            add("sketch.finish")
            add("solid.hole", sketch=f"Set screw {k} sketch", thread=f"M{d['M']:g}", depth=s.wall, targets=[s.code], name=f"Set screw {k} thread")

def clamp(add, s: Support):
    """groove (width and position printed, depth to the bottom of the bore read from the figure), radial slit on +Y over the ring, and the
    clamp screw along X: clearance hole and counterbore on -X (the counterbore floor Y from the slit centre), tapped hole on +X"""
    d, D = s.dims, s.D
    g = clamp_geometry(s)
    ro = g["ro"]
    add("solid.box", length=2 * ro + 2, width=ro + 1 + D / 2, height=g["gw"], corner=[-ro - 1, -D / 2, g["g0"]], operation="cut", targets=[s.code], name="Groove")
    add("solid.box", length=g["slit"], width=ro + 1, height=g["B"] + 1, corner=[-g["slit"] / 2, 0, g["ring0"]], operation="cut", targets=[s.code], name="Slit")
    xo = math.sqrt(ro ** 2 - d["X"] ** 2)
    for n, zc in enumerate(g["zcs"], 1):
        sfx = f" {n}" if len(g["zcs"]) > 1 else ""
        base = [-xo - 1, d["X"], zc]
        add("solid.cylinder", diameter=g["clear"], height=xo + 1, base=base, axis="X", operation="cut", targets=[s.code], name=f"Clamp screw{sfx} clearance hole")
        add("solid.cylinder", diameter=g["cb"], height=xo + 1 - d["Y"], base=base, axis="X", operation="cut", targets=[s.code], name=f"Clamp screw{sfx} counterbore")
        add("solid.hole", position=[xo, d["X"], zc], direction=[-1, 0, 0], thread=f"M{d['M']:g}", depth=xo - g["slit"] / 2, targets=[s.code], name=f"Clamp screw{sfx} thread")

def parse_build(code: str):
    s = parse(code)
    return s, commands(s)
