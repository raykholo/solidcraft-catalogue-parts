"""MISUMI Economy Series shaft supports (T-shaped with slit E-SHSTB/M/A, with side slit E-SHWTB/A, thickened E-SHSTBN/MN, and the
T-shaped aluminium C-SHA): ordering-code parser, catalogue data and native-SolidCraft command builder.

Source (every number, id S50 in sources.toml): MISUMI Economy Series catalogue 2025, p.540 (C-SHA, printed 04-155), p.541 (E-SHST /
E-SHWT, 04-156), p.542 (E-SHSTBN / E-SHSTMN, 04-157), published at
https://th.c.misumi-ec.com/book/THA_EconomySeries_e-catalog2025/files/basic-html/page540.html ... page542.html.

Frame: the shaft bore runs along Y, its centre at x = 0, z = H; the foot sits on z = 0; thickness T is centred on y = 0.
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
TOL = {int(r["D"]): (num(r["upper"]), num(r["lower"])) for r in read_csv(DATA / "tolerance.csv")}

def _lst(s):
    return [int(x) for x in s.split("|")] if s else []

DIMS = {}
for _r in read_csv(DATA / "dims.csv"):
    DIMS[(_r["family"], int(_r["D"]))] = {k: (v if k in ("family", "source", "page", "status") else (_lst(v) if k in ("h_all", "h_alu") else num(v)))
                                           for k, v in _r.items()}
CSHA = {int(_r["D"]): {k: num(v) for k, v in _r.items()} for _r in read_csv(DATA / "csha.csv")}

CODE = re.compile(r"^(E-SHSTBN|E-SHSTMN|E-SHSTB|E-SHSTM|E-SHSTA|E-SHWTB|E-SHWTA|C-SHA)(\d{1,2})(?:-(\d+))?$")
H_TOL = 0.02          # H +-0.02, printed on p.541 / p.542

@dataclass
class Holder:
    code: str
    type: str
    family: str
    D: int
    H: float
    dims: dict
    tol: tuple
    tolerance_class: str
    material: str
    surface: str
    accessory: str
    notes: list = field(default_factory=list)

    @property
    def H1(self):
        return self.H + self.dims["h1_off"] if self.family != "csha" else self.dims["H1_ref"]

    @property
    def description(self) -> str:
        d = self.dims
        if self.family == "csha":
            return (f"MISUMI Economy shaft support {self.type}{self.D}, hole D{self.D} tolerance H7, height H={self.H:g} mm, T={d['T']:g}, "
                    f"hole pitch L1={d['L1']:g}, M{d['M']} clamp screw, {self.material}, {self.surface}. Overall H1, S, L, B, W are catalogue reference values (+-0.5 mm). "
                    "Corners are not rounded here (not dimensioned); slit and screw hole are approximate.")
        kind = {"slit": "T-shaped with slit", "side": "T-shaped with side slit", "thick": "thickened T-shaped with slit"}[self.family]
        return (f"MISUMI Economy shaft support {self.type}{self.D}-{self.H:g} ({kind}), hole D{self.D} H8 ({self.tol[0]:+.3f}/{self.tol[1]:+.3f} mm), "
                f"height H={self.H:g} mm (+-{H_TOL:g}), {self.material}, {self.surface}, M{d['M']} clamp screw "
                f"({'through' if not d['m_depth'] else 'depth ' + str(d['m_depth'])}). Slit width C={d['C']:g}. Generated from the published catalogue dimensions.")

def parse(code: str) -> Holder:
    raw = code
    c = code.strip().upper()
    m = CODE.match(c)
    if not m:
        raise CodeError(f"{raw!r}: expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN "
                        "(e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10)")
    typ, ds, hs = m.groups()
    D = int(ds)
    t = TYPES[typ]
    fam = t["family"]
    if fam == "csha":
        if hs is not None:
            raise CodeError("C-SHA has one fixed height per hole diameter (no H in the part number): C-SHA10")
        if D not in CSHA:
            raise CodeError(f"C-SHA is listed for hole D {sorted(CSHA)}, not {D} (p.540)")
        r = CSHA[D]
        return Holder(code=c, type=typ, family=fam, D=D, H=r["H"], dims=r, tol=(None, None), tolerance_class="H7", material=t["material"],
                      surface=t["surface"], accessory=t["accessory"])
    page = 542 if fam == "thick" else 541
    if (fam, D) not in DIMS:
        sizes = sorted(k[1] for k in DIMS if k[0] == fam)
        raise CodeError(f"{typ} is not listed for D{D}: catalogue sizes are {sizes} (p.{page})")
    d = DIMS[(fam, D)]
    if hs is None:
        raise CodeError(f"{typ}{D} needs its height: {typ}{D}-<H> with H from {d['h_all']} (p.{page})")
    H = int(hs)
    if H not in d["h_all"]:
        raise CodeError(f"height {H} is not offered for {typ}{D}: H = {d['h_all']} (p.{page})")
    if typ == "E-SHSTB" and D == 15 and H == 25:
        raise CodeError("E-SHSTB15 is not available with H = 25 (p.541 note)")
    if typ == "E-SHSTMN" and not d["mn_ok"]:
        raise CodeError(f"E-SHSTMN is not applicable to the * marked D{D} (p.542 note)")
    if typ in ("E-SHSTA", "E-SHWTA") and H not in d["h_alu"]:
        ok = f"only H = {d['h_alu']}" if d["h_alu"] else "no height"
        raise CodeError(f"the aluminium type {typ} is applicable only to * marked dimensions: for D{D} {ok} (p.541)")
    return Holder(code=c, type=typ, family=fam, D=D, H=float(H), dims=d, tol=TOL[D], tolerance_class="H8", material=t["material"],
                  surface=t["surface"], accessory=t["accessory"])

def _csha_commands(s, add):
    d = s.dims
    D, H, T = s.D, s.H, d["T"]
    L, S, W, H1 = d["L_ref"], d["S_ref"], d["W_ref"], d["H1_ref"]
    add("sketch.create", plane={"origin": [0, T / 2, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Profile")
    add("sketch.line", points=[[-L / 2, 0], [L / 2, 0], [L / 2, S], [W / 2, S], [W / 2, H1], [-W / 2, H1], [-W / 2, S], [-L / 2, S]], closed=True)
    add("sketch.finish")
    add("solid.extrude", distance=T, name="Body", body_name=s.code)
    add("solid.cylinder", diameter=D, height=T + 2, base=[0, -T / 2 - 1, H], axis="Y", operation="cut", targets=[s.code], name="Shaft hole")
    for sx in (-1, 1):
        add("solid.cylinder", diameter=d["d"], height=S + 2, base=[sx * d["L1"] / 2, 0, -1], axis="Z", operation="cut", targets=[s.code], name=f"Mounting hole {sx:+d}")
    # slit and clamp screw: approximate (their size and position are not printed)
    add("solid.box", length=2, width=T + 2, height=H1 - H + 1, corner=[-1, -T / 2 - 1, H], operation="cut", targets=[s.code], name=f"Slit {APPX}")
    zs = H + (H1 - H) / 2
    add("sketch.create", plane={"origin": [1, 0, zs], "x_dir": [0, 0, 1], "y_dir": [0, 1, 0]}, name="Clamp screw sketch")
    add("sketch.point", point=[0, 0])
    add("sketch.finish")
    add("solid.hole", sketch="Clamp screw sketch", thread=f"M{d['M']}", depth=W / 2 - 1, targets=[s.code], name=f"Clamp screw thread {APPX}")

def commands(s: Holder) -> list[dict]:
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    add("component.create", name=s.code)
    if s.family == "csha":
        _csha_commands(s, add)
    else:
        d = s.dims
        D, H, T, L, S, W, H1 = s.D, s.H, d["T"], d["L"], d["S"], d["W"], s.H1
        add("sketch.create", plane={"origin": [0, T / 2, 0], "x_dir": [1, 0, 0], "y_dir": [0, 0, 1]}, name="Profile")
        add("sketch.line", points=[[-L / 2, 0], [L / 2, 0], [L / 2, S], [W / 2, S], [W / 2, H1], [-W / 2, H1], [-W / 2, S], [-L / 2, S]], closed=True)
        add("sketch.finish")
        add("solid.extrude", distance=T, name="Body", body_name=s.code)
        add("solid.cylinder", diameter=D, height=T + 2, base=[0, -T / 2 - 1, H], axis="Y", operation="cut", targets=[s.code], name="Shaft hole")
        ys = [0.0] if d["base_holes"] == 2 else [-T / 4, T / 4]
        for sx in (-1, 1):
            for y in ys:
                add("solid.cylinder", diameter=d["d"], height=S + 2, base=[sx * d["L1"] / 2, y, -1], axis="Z", operation="cut", targets=[s.code],
                    name=f"Mounting hole {sx:+d} {y:+g}")
        C, E = d["C"], d["E"]
        mdepth = d["m_depth"]
        sy = [0.0] if d["screws"] == 1 else [-T / 4, T / 4]
        if s.family in ("slit", "thick"):
            add("solid.box", length=C, width=T + 2, height=H1 - H + 1, corner=[-C / 2, -T / 2 - 1, H], operation="cut", targets=[s.code], name="Slit")
            zs = H + E
            wall = W / 2 - C / 2
            for y in sy:
                add("solid.cylinder", diameter=d["d2"], height=wall + 1, base=[-W / 2 - 1, y, zs], axis="X", operation="cut", targets=[s.code], name=f"Screw clearance hole {y:+g}")
                add("solid.cylinder", diameter=d["d1"], height=d["l"] + 1, base=[-W / 2 - 1, y, zs], axis="X", operation="cut", targets=[s.code], name=f"Screw counterbore {y:+g}")
                add("sketch.create", plane={"origin": [C / 2, y, zs], "x_dir": [0, 0, 1], "y_dir": [0, 1, 0]}, name=f"Screw thread sketch {y:+g}")
                add("sketch.point", point=[0, 0])
                add("sketch.finish")
                add("solid.hole", sketch=f"Screw thread sketch {y:+g}", thread=f"M{d['M']}", depth=mdepth or wall, targets=[s.code], name=f"Clamp thread {y:+g}")
        else:
            add("solid.box", length=W / 2 + 1, width=T + 2, height=C, corner=[0, -T / 2 - 1, H - C / 2], operation="cut", targets=[s.code], name="Side slit")
            add("solid.cylinder", diameter=d["d2"], height=H1 - H + 1, base=[E, 0, H], axis="Z", operation="cut", targets=[s.code], name="Screw clearance hole")
            add("solid.cylinder", diameter=d["d1"], height=d["l"] + 1, base=[E, 0, H1 - d["l"]], axis="Z", operation="cut", targets=[s.code], name="Screw counterbore")
            add("sketch.create", plane={"origin": [E, 0, H - C / 2], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="Screw thread sketch")
            add("sketch.point", point=[0, 0])
            add("sketch.finish")
            add("solid.hole", sketch="Screw thread sketch", thread=f"M{d['M']}", depth=mdepth, targets=[s.code], name="Clamp thread")
    add("browser.visibility", items=["Profile"], visible=False)
    add("component.metadata.set", component=s.code, part_number=s.code, description=s.description, material=f"{s.material}; {s.surface}")
    add("document.metadata.set", values={"part_number": s.code, "description": s.description})
    return cmds

def parse_build(code: str):
    s = parse(code)
    return s, commands(s)
