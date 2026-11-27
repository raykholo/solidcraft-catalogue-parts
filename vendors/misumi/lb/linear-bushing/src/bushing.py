"""MISUMI Economy Series linear bushings (E-LB straight, E-LBF / E-LBK round and square flanged): ordering-code parser,
catalogue data and native-SolidCraft command builder.

Second source (id S13): the same catalogue, compact flanged bushings E-LBH / E-LBHZ / E-LBHM p.470 (04-085) and medium p.471 (04-086),
round / square / compact flanged bushings with pilot p.472 to p.477 (04-087 to 04-092) and centre flanged bushings p.478 to p.480
(04-093 to 04-095), page images files/mobile/470.jpg ... 480.jpg.

Source (every number below, id S11 in sources.toml): MISUMI Economy Series catalogue 2025, "Linear Bushings Straight Short" p.464
(printed page 04-079), "Straight Medium" p.465 (04-080), "Round Flanged Linear Bushings" p.466 (04-081) and "Medium" p.467 (04-082),
"Square Flanged Linear Bushings" p.468 (04-083) and "Medium" p.469 (04-084), published at
https://th.c.misumi-ec.com/book/THA_EconomySeries_e-catalog2025/files/basic-html/page464.html ... page469.html (page images
files/mobile/464.jpg ... 469.jpg). The bushing is drawn as a solid of revolution with a plain bore at the nominal diameter dr; the balls,
retainer and seals are not in the catalogue as dimensions and are not drawn.
"""
from __future__ import annotations
import math, re
from dataclasses import dataclass, field
from pathlib import Path
from runtime.appearance import APPX
from runtime.table import read_csv, num

class CodeError(ValueError):
    """The ordering code is not valid; the message says why."""

DATA = Path(__file__).resolve().parent.parent / "data"

def _table(name):
    return {int(r["dr"]): {k: num(v) for k, v in r.items() if k not in ("source", "page", "status")} for r in read_csv(DATA / name)}

TYPES = {r["type"]: r for r in read_csv(DATA / "types.csv")}
SHORT = _table("short.csv")            # p.464
MEDIUM = _table("medium.csv")          # p.465
FL_LONG = _table("flanged_long.csv")   # p.466 / p.468
FL_MED = _table("flanged_medium.csv")  # p.467 / p.469

def _table2(name, keys):
    return {tuple(r[k] if k == "shape" else int(r[k]) for k in keys):
            {k: num(v) for k, v in r.items() if k not in ("source", "page", "status")} | {"page": r["page"].split()[0]}
            for r in read_csv(DATA / name)}

TYPES |= {r["type"]: r for r in read_csv(DATA / "types_ext.csv")}
CP_LONG = _table("compact_long.csv")                                # p.470
CP_MED = _table("compact_medium.csv")                               # p.471
PI_LONG = _table2("pilot_long.csv", ("shape", "dr"))                # p.472 / p.474 / p.476
PI_MED = _table2("pilot_medium.csv", ("shape", "dr"))               # p.473 / p.475 / p.477
CE_LONG = _table2("center_long.csv", ("shape", "dr"))               # p.478 / p.479 / p.480
CE_MED = _table2("center_medium.csv", ("shape", "dr"))              # p.478 / p.479 / p.480

CODE = re.compile(r"^(E-(?:LB[FKH](?:PM|CM|[ZMPC])?|LB))(\d{1,2})(TUU|DMUU|DUU|LUU|UU)$")

@dataclass
class Bushing:
    code: str
    type: str
    family: str            # straight | round | square
    series: str            # short | medium | long
    dr: int
    D: float
    D_tol: float           # lower deviation (upper is 0)
    L: float
    L_tol: tuple           # (upper, lower)
    dr_tol: tuple          # (upper, lower)
    plated: bool = False
    double: bool = False
    counterbore: str = "-"
    layout: str = "standard"        # standard | pilot | center (where the flange sits along the barrel)
    x0: float = 0.0                 # x of the flange face nearest the start of the barrel (the distance l for pilot / centre)
    page: str = ""                  # catalogue page of the table the row came from (new series; the first series derive it)
    grooves: dict | None = None     # B, B_tol, W, D1
    flange: dict | None = None      # H, T, d, d1, t, pcd, W
    notes: list = field(default_factory=list)

    @property
    def suffix(self): return self.code[len(self.type) + len(str(self.dr)):]

    @property
    def description(self) -> str:
        d = (f"MISUMI Economy linear bushing {self.type}{self.dr}{self.suffix}, shaft diameter dr {self.dr} mm "
             f"({self.dr_tol[0]:+.3f}/{self.dr_tol[1]:+.3f} mm, drawn at nominal), outside diameter D {self.D:g} mm "
             f"(0/{self.D_tol:+.3f} mm), overall length L {self.L:g} mm ({self.L_tol[0]:+.2g}/{self.L_tol[1]:+.2g} mm)")
        if self.grooves:
            g = self.grooves
            d += f", two ring grooves W {g['W']:g} mm wide on D1 {g['D1']:g} mm, B {g['B']:g} mm apart"
        if self.flange:
            f = self.flange
            if self.family == "compact":
                holes = (f"{len(hole_centres(self))} counterbored holes d {f['d']:g} / d1 {f['d1']:g} x {f['t']:g} deep, "
                         f"A {f['A']:g} mm apart along H" + (f" and F {f['F']:g} mm across" if f.get("F") else ""))
                d += f", compact flange H {f['H']:g} mm long, {f['width']:g} mm across two flats, T {f['T']:g} mm, " + holes
            else:
                d += (f", {self.family} flange H {f['H']:g} mm" + (f" (W {f['W']:g} mm across flats)" if self.family == "square" else "")
                      + f", T {f['T']:g} mm, 4 counterbored holes d {f['d']:g} / d1 {f['d1']:g} x {f['t']:g} deep on P.C.D. {f['pcd']:g} mm")
            if self.layout == "pilot":
                d += f", pilot l {self.x0:g} mm from the end to the flange"
            elif self.layout == "center":
                d += f", flange centred, l {self.x0:g} mm from each end to the flange"
        d += ". Case equivalent to SUJ2, 58HRC~" + (", electroless nickel plated" if self.plated else "")
        return d + f". Balls, retainer and seals {APPX}: not drawn. Generated from the published catalogue dimensions."

def parse(code: str) -> Bushing:
    raw = code
    m = CODE.match(code.strip().upper())
    if not m and re.match(r"^E-LB[FKH]?S\d", code.strip().upper()):
        raise CodeError(f"{raw!r}: stainless steel linear bushings (representative type E-LBHS) are only mentioned on p.470; "
                        "the catalogue prints no dimension table for them, so they are not covered")
    if not m:
        raise CodeError(f"{raw!r}: expected <type><dr><suffix>, type E-LB, E-LBF, E-LBFZ, E-LBFM, E-LBK, E-LBKZ or E-LBKM, "
                        "suffix TUU (short), DUU / DMUU (medium) or UU / LUU (flanged single / double), e.g. E-LB10TUU, E-LBF20LUU; "
                        "the compact, pilot and centre types add H, P and C: E-LBH, E-LBHZ, E-LBHM, E-LBFP, E-LBKPM, E-LBHC, ...")
    typ, drs, suf = m.groups()
    dr = int(drs)
    code = typ + drs + suf
    fam = TYPES[typ]["family"]
    plated = TYPES[typ]["plated"] == "yes" or suf == "DMUU"
    cb = TYPES[typ]["counterbore"]
    layout = TYPES[typ].get("layout", "standard")
    if fam == "compact" or layout != "standard":
        return _parse_ext(code, typ, dr, suf, fam, layout, plated, cb)
    if fam == "straight":
        if suf in ("UU", "LUU"):
            raise CodeError(f"{typ} is the straight bushing: its suffix is TUU (short), DUU or DMUU (medium), not {suf}")
        if suf == "TUU":
            if dr not in SHORT:
                raise CodeError(f"{typ}{dr}TUU: the short straight bushing is offered for dr {sorted(SHORT)} (p.464)")
            r = SHORT[dr]
            return Bushing(code, typ, fam, "short", dr, r["D"], r["D_tol"], r["L"], (0, r["L_tol"]), (0, r["dr_tol"]))
        if dr not in MEDIUM:
            raise CodeError(f"{typ}{dr}{suf}: the medium straight bushing is offered for dr {sorted(MEDIUM)} (p.465)")
        r = MEDIUM[dr]
        return Bushing(code, typ, fam, "medium", dr, r["D"], r["D_tol_ni"] if plated else r["D_tol"], r["L"], (0, r["L_tol"]),
                       (0, r["dr_tol"]), plated=plated,
                       grooves=dict(B=r["B"], B_tol=r["B_tol"], W=r["W"], D1=r["D1"]))
    # flanged
    if suf == "TUU":
        raise CodeError(f"{typ} has no short (TUU) version: flanged bushings end in UU / LUU (long) or DUU / DMUU (medium)")
    if suf in ("UU", "LUU"):
        if dr not in FL_LONG:
            raise CodeError(f"{typ}{dr}{suf}: flanged bushings are offered for dr {sorted(FL_LONG)} (p.466 / p.468)")
        if dr > 30 and typ.endswith("Z"):
            raise CodeError(f"{typ}{dr}: the opposite-counterbore type {typ} is offered for dr 6-30; dr 35, 40, 50 only as "
                            f"{typ[:-1]} and {typ[:-1]}M (p.466 / p.468)")
        r = FL_LONG[dr]
        dbl = suf == "LUU"
        tol = r["D_tol_double_ni" if dbl else "D_tol_single_ni"] if plated else r["D_tol_double" if dbl else "D_tol_single"]
        fl = dict(H=r["H"], T=r["T"], d=r["d"], d1=r["d1"], t=r["t"], pcd=r["pcd"], W=r["W"])
        return Bushing(code, typ, fam, "long", dr, r["D"], tol, r["L_double"] if dbl else r["L_single"], (r["L_tol"], -r["L_tol"]),
                       (r["dr_tol_upper"], r["dr_tol_lower"]), plated=plated, double=dbl, counterbore=cb, flange=fl)
    # medium flanged: DUU / DMUU, plain type only (plating is the M of DMUU)
    if typ[-1] in "ZM":
        raise CodeError(f"{typ}: the medium flanged bushing is ordered as {typ[:-1]}<dr>DUU, or {typ[:-1]}<dr>DMUU for electroless "
                        "nickel plating (p.467 / p.469); the Z and M type letters belong to the UU / LUU bushings")
    if dr not in FL_MED:
        raise CodeError(f"{typ}{dr}{suf}: the medium flanged bushing is offered for dr {sorted(FL_MED)} (p.467 / p.469)")
    r = FL_MED[dr]
    fl = dict(H=r["H"], T=r["T"], d=r["d"], d1=r["d1"], t=r["t"], pcd=r["pcd"], W=r["W"])
    return Bushing(code, typ, fam, "medium", dr, r["D"], r["D_tol_ni"] if plated else r["D_tol"], r["L"], (r["L_tol"], -r["L_tol"]),
                   (0, r["dr_tol"]), plated=plated, counterbore=cb, flange=fl)

def _flange_of(r, fam):
    fl = dict(H=r["H"], T=r["T"], d=r["d"], d1=r["d1"], t=r["t"])
    if fam == "compact":
        fl.update(A=r["A"], F=r["F"], width=r["width"])
    else:
        fl.update(pcd=r["pcd"])
        if fam == "square":
            fl["W"] = r["W"]
    return fl

def _parse_ext(code, typ, dr, suf, fam, layout, plated, cb):
    """Compact flanged (p.470-471), flanged with pilot (p.472-477) and centre flanged (p.478-480) bushings."""
    base = typ[:-1] if typ.endswith("M") else typ        # E-LBHM -> E-LBH, E-LBFPM -> E-LBFP, E-LBFCM -> E-LBFC
    if suf == "TUU":
        raise CodeError(f"{typ} has no short (TUU) version")
    name = f"{typ}{dr}{suf}"
    if layout == "standard":                              # compact E-LBH / E-LBHZ / E-LBHM
        if suf in ("UU", "LUU"):
            if dr not in CP_LONG:
                raise CodeError(f"{name}: compact flanged bushings are offered for dr {sorted(CP_LONG)} (p.470)")
            if typ == "E-LBHZ" and dr > 30:
                raise CodeError(f"{name}: the opposite-counterbore type E-LBHZ is offered for dr 6-30 (p.470)")
            if dr == 5 and typ != "E-LBH":
                raise CodeError(f"{name}: dr 5 is offered only as the plain E-LBH5UU (p.470)")
            r = CP_LONG[dr]
            dbl = suf == "LUU"
            if dbl and r["L_double"] is None:
                raise CodeError(f"{name}: dr 5 is offered as a single bushing (UU) only (p.470)")
            tol = r["D_tol_double_ni" if dbl else "D_tol_single_ni"] if plated else r["D_tol_double" if dbl else "D_tol_single"]
            return Bushing(code, typ, fam, "long", dr, r["D"], tol, r["L_double"] if dbl else r["L_single"], (r["L_tol"], -r["L_tol"]),
                           (r["dr_tol_upper"], r["dr_tol_lower"]), plated=plated, double=dbl, counterbore=cb,
                           flange=_flange_of(r, fam), page="p.470")
        if typ != "E-LBH":
            raise CodeError(f"{typ}: the medium compact flanged bushing is ordered as E-LBH<dr>DUU, or E-LBH<dr>DMUU for electroless "
                            "nickel plating (p.471); the Z and M type letters belong to the UU / LUU bushings")
        if dr not in CP_MED:
            raise CodeError(f"{name}: the medium compact flanged bushing is offered for dr {sorted(CP_MED)} (p.471)")
        r = CP_MED[dr]
        return Bushing(code, typ, fam, "medium", dr, r["D"], r["D_tol_ni"] if plated else r["D_tol"], r["L"], (r["L_tol"], -r["L_tol"]),
                       (0, r["dr_tol"]), plated=plated, counterbore=cb, flange=_flange_of(r, fam), page="p.471")
    if layout == "pilot":
        if suf in ("UU", "LUU"):
            r = PI_LONG.get((fam, dr))
            if r is None:
                raise CodeError(f"{name}: flanged bushings with pilot are offered for dr {sorted(k[1] for k in PI_LONG if k[0] == fam)} "
                                f"({'/'.join(sorted({v['page'] for k, v in PI_LONG.items() if k[0] == fam}))})")
            dbl = suf == "LUU"
            return Bushing(code, typ, fam, "long", dr, r["D"], r["D_tol_ni"] if plated else r["D_tol"],
                           r["L_double"] if dbl else r["L_single"], (r["L_tol"], -r["L_tol"]),
                           (0, r["dr_tol_double" if dbl else "dr_tol_single"]), plated=plated, double=dbl, counterbore=cb,
                           flange=_flange_of(r, fam), layout="pilot", x0=r["l"], page=r["page"])
        if suf == "DUU" or (suf == "DMUU" and typ.endswith("M")):
            raise CodeError(f"{typ}: the medium bushing with pilot is ordered as {base}<dr>DMUU only (the case is always nickel "
                            "plated; no DUU, no M type letter on the medium series)")
        r = PI_MED.get((fam, dr))
        if r is None:
            raise CodeError(f"{name}: the medium bushing with pilot is offered for dr {sorted(k[1] for k in PI_MED if k[0] == fam)} "
                            f"({'/'.join(sorted({v['page'] for k, v in PI_MED.items() if k[0] == fam}))})")
        return Bushing(code, typ, fam, "medium", dr, r["D"], r["D_tol_ni"], r["L"], (r["L_tol"], -r["L_tol"]), (0, r["dr_tol"]),
                       plated=True, counterbore=cb, flange=_flange_of(r, fam), layout="pilot", x0=r["l"], page=r["page"])
    # centre flanged
    if suf in ("UU", "DUU"):
        raise CodeError(f"{typ}: the centre flanged bushing is a double bushing: LUU (long) or DMUU (medium, plain type {base} only), not {suf}")
    if suf == "LUU":
        r = CE_LONG.get((fam, dr))
        if r is None:
            raise CodeError(f"{name}: centre flanged bushings are offered for dr {sorted(k[1] for k in CE_LONG if k[0] == fam)} "
                            f"({'/'.join(sorted({v['page'] for k, v in CE_LONG.items() if k[0] == fam}))})")
        return Bushing(code, typ, fam, "long", dr, r["D"], r["D_tol_ni"] if plated else r["D_tol"], r["L"], (r["L_tol"], -r["L_tol"]),
                       (0, r["dr_tol"]), plated=plated, double=True, counterbore=cb, flange=_flange_of(r, fam),
                       layout="center", x0=r["l"], page=r["page"])
    if typ.endswith("M"):
        raise CodeError(f"{typ}: the medium centre flanged bushing is ordered as {base}<dr>DMUU (nickel plated by the DMUU suffix), "
                        "not with the M type letter")
    r = CE_MED.get((fam, dr))
    if r is None:
        raise CodeError(f"{name}: the medium centre flanged bushing is offered for dr {sorted(k[1] for k in CE_MED if k[0] == fam)} "
                        f"({'/'.join(sorted({v['page'] for k, v in CE_MED.items() if k[0] == fam}))})")
    return Bushing(code, typ, fam, "medium", dr, r["D"], r["D_tol_ni"], r["L"], (r["L_tol"], -r["L_tol"]), (0, r["dr_tol"]),
                   plated=True, counterbore=cb, flange=_flange_of(r, fam), layout="center", x0=r["l"], page=r["page"])

def hole_centres(b: Bushing):
    """(y, z) of the mounting holes: on the P.C.D. for round and square flanges; for the compact flange A apart along Z (the long
    axis of H) and, from dr 16, F apart along Y."""
    f = b.flange
    if b.family == "compact":
        a = f["A"] / 2
        if f.get("F"):
            e = f["F"] / 2
            return [(e, a), (-e, a), (-e, -a), (e, -a)]
        return [(0, a), (0, -a)]
    r = f["pcd"] / 2
    return [(r, 0), (0, r), (-r, 0), (0, -r)]

def groove_spans(b: Bushing):
    """x ranges of the two ring grooves: W wide, B apart (clear distance between them), centred on the length."""
    g = b.grooves
    a1 = (b.L - g["B"]) / 2
    a2 = (b.L + g["B"]) / 2
    return (a1 - g["W"], a1), (a2, a2 + g["W"])

def cb_face_x(b: Bushing) -> float:
    """x of the flange face that carries the counterbores: the barrel side (x0 + T) as standard, the other face (x0) for Z."""
    return b.x0 if b.counterbore == "opposite" else b.x0 + b.flange["T"]

def commands(b: Bushing) -> list[dict]:
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    D, L, R = b.D, b.L, b.D / 2
    add("component.create", name=b.code)
    pts = [[0, 0], [L, 0], [L, R]]
    if b.grooves:
        (g1s, g1e), (g2s, g2e) = groove_spans(b)
        r1 = b.grooves["D1"] / 2
        pts += [[g2e, R], [g2e, r1], [g2s, r1], [g2s, R], [g1e, R], [g1e, r1], [g1s, r1], [g1s, R]]
    if b.family == "round":
        f = b.flange
        x0 = b.x0
        pts += [[x0 + f["T"], R], [x0 + f["T"], f["H"] / 2], [x0, f["H"] / 2]]
        if x0 > 0:
            pts += [[x0, R], [0, R]]
    else:
        pts += [[0, R]]
    add("sketch.create", plane="XY", name="Profile")
    add("sketch.line", points=pts, closed=True)
    add("sketch.finish")
    add("solid.revolve", axis="x", name="Body", body_name=b.code)
    flange_plane = "YZ" if b.x0 == 0 else {"origin": [b.x0, 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}
    if b.family == "compact":
        f = b.flange
        e, Rh = f["width"] / 2, f["H"] / 2          # flats e from the axis along Y, circle H clipping the ends along Z
        s = math.sqrt(Rh * Rh - e * e)
        add("sketch.create", plane=flange_plane, name="Flange")
        add("sketch.line", points=[[e, -s], [e, s]])
        add("sketch.arc.three_point", start=[e, s], through=[0, Rh], end=[-e, s])
        add("sketch.line", points=[[-e, s], [-e, -s]])
        add("sketch.arc.three_point", start=[-e, -s], through=[0, -Rh], end=[e, -s])
        add("sketch.finish")
        add("solid.extrude", distance=f["T"], operation="join", targets=[b.code], name="Compact flange")
    if b.family == "square":
        f = b.flange
        a = f["W"] / math.sqrt(2)           # the square stands on its corner: vertices on the axes, clipped by the circle H
        Rh = f["H"] / 2
        s = math.sqrt(2 * Rh * Rh - a * a)
        py, pz = (a + s) / 2, (a - s) / 2
        add("sketch.create", plane=flange_plane, name="Flange")
        for p, q in [((py, -pz), (pz, -py)), ((-pz, -py), (-py, -pz)), ((-py, pz), (-pz, py)), ((pz, py), (py, pz))]:
            add("sketch.line", points=[list(p), list(q)])
        for p, t, q in [((py, pz), (Rh, 0), (py, -pz)), ((pz, -py), (0, -Rh), (-pz, -py)), ((-py, -pz), (-Rh, 0), (-py, pz)),
                        ((-pz, py), (0, Rh), (pz, py))]:
            add("sketch.arc.three_point", start=list(p), through=list(t), end=list(q))
        add("sketch.finish")
        add("solid.extrude", distance=f["T"], operation="join", targets=[b.code], name="Square flange")
    add("solid.cylinder", diameter=b.dr, height=L + 2, base=[-1, 0, 0], axis="X", operation="cut", targets=[b.code], name="Bore")
    if b.flange:
        f = b.flange
        x = cb_face_x(b)
        for i, (y, z) in enumerate(hole_centres(b)):
            add("solid.hole", position=[x, y, z], diameter=f["d"], type="counterbore", cb_diameter=f["d1"], cb_depth=f["t"],
                depth=f["T"], targets=[b.code], name=f"Mounting hole {i + 1}")
    add("component.metadata.set", component=b.code, part_number=b.code, description=b.description,
        material="Case equivalent to SUJ2, 58HRC~" + ("; electroless nickel plating" if b.plated else ""))
    add("document.metadata.set", values={"part_number": b.code, "description": b.description})
    return cmds

def parse_build(code: str):
    b = parse(code)
    return b, commands(b)
