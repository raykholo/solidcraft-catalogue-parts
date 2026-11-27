"""MISUMI Economy Series oil free bushings (copper alloy and special brass): ordering-code parser, catalogue data and native-SolidCraft
command builder.

Source (every number, id S16 in sources.toml): MISUMI Economy Series catalogue 2025, "Oil Free Bushings Copper Alloy, Straight /
Shouldered" p.514 (printed page 04-129), "Copper Alloy Flanged" p.515 (04-130), "Copper Alloy Thrust Type" p.516 (04-131) and "Special
Brass Oil Free Bushings Straight / Shouldered" p.519 (04-134), "Round Flanged / Compact Flanged" p.520 (04-135), published at
https://th.c.misumi-ec.com/book/THA_EconomySeries_e-catalog2025/files/basic-html/page514.html ... page520.html (page images
files/mobile/514.jpg ... 520.jpg). The bushing is a solid of revolution with a plain bore at the nominal diameter d; the solid lubricant
plugs, chamfers and the rotation stopper screw are not drawn (the catalogue gives no dimensions for them).

Ordering code: <type><d>-<L>, e.g. C-MUFZ5-10 (the catalogue's own example), E-SHTZ25-35.
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

def _rows(name):
    return {int(r["dr"]): {k: (v if k == "lengths" else num(v)) for k, v in r.items() if k not in ("source", "page", "status")}
            for r in read_csv(DATA / name)}

TYPES = {r["type"]: r for r in read_csv(DATA / "types.csv")}
TABLES = {n: _rows(n + ".csv") for n in ("copper_straight", "copper_shouldered", "copper_flanged", "thrust",
                                          "brass_straight", "brass_shouldered", "brass_flanged")}
PARAMS = {r["key"]: num(r["value"]) for r in read_csv(DATA / "params.csv")}
PAGE = {"copper_straight": "p.514", "copper_shouldered": "p.514", "copper_flanged": "p.515", "thrust": "p.516",
        "brass_straight": "p.519", "brass_shouldered": "p.519", "brass_flanged": "p.520"}

CODE = re.compile(r"^(C-MU(?:BZU?|FZU?|TZ|TSZ|TNZ)|E-SH(?:BZ|FZ|TZ|TNZ)|E-MUGZ)(\d{1,3})-(\d{1,3})$")
KNOWN_UNMODELLED = re.compile(r"^(E-MU(?:SZ|KZ|CZ|CTZ|IZ|ITZ)|C-MUIZ|E-M[JGX][BF]Z)")

def offered_lengths(tokens: str, thin: bool = False, square: bool = False) -> list[int]:
    """The L values the catalogue row offers: `(n)` is printed in brackets for the standard wall type only (straight, shouldered) or for
    the round and compact flanges only (flanged), `n*` for the thin wall type only."""
    out = []
    for t in tokens.split():
        if t.startswith("("):
            if thin or square:
                continue
        elif t.endswith("*"):
            if not thin:
                continue
        out.append(int(t.strip("()*")))
    return out

@dataclass
class Part:
    code: str
    type: str
    family: str            # straight | shouldered | round | square | compact | thrust
    wall: str              # standard | thin
    material: str
    d: int                 # nominal bore (I.D.)
    L: float
    D: float
    bore_class: str
    od_class: str
    bore_tol: tuple        # (upper, lower)
    L_tol: tuple
    page: str
    N: float | None = None           # wall thickness (straight, shouldered)
    flange: dict | None = None       # H, t (shouldered, thrust); H, T, t, d1, d2, pcd, W, F, A (flanged)
    notes: list = field(default_factory=list)

    @property
    def description(self) -> str:
        fam = {"straight": "straight", "shouldered": "shouldered", "round": "round flanged", "square": "square flanged",
               "compact": "compact flanged", "thrust": "thrust type"}[self.family]
        d = (f"MISUMI Economy oil free bushing {self.code}, {fam}{', thin wall' if self.wall == 'thin' else ''}, I.D. d {self.d} mm "
             f"({self.bore_class} {self.bore_tol[0]:+.3f}/{self.bore_tol[1]:+.3f} mm, drawn at nominal), O.D. D {self.D:g} mm "
             f"({self.od_class}), overall length L {self.L:g} mm ({self.L_tol[0]:+.1f}/{self.L_tol[1]:+.1f} mm)")
        if self.N:
            d += f", wall N {self.N:g} mm"
        f = self.flange
        if f:
            if self.family in ("shouldered", "thrust"):
                d += f", flange H {f['H']:g} mm x t {f['t']:g} mm" + (f" (0/{PARAMS['thrust_t_tol_lower']:+.2f} mm)" if self.family == "thrust" else "")
            else:
                n = len(hole_centres(self))
                d += f", {self.family} flange H {f['H']:g} mm, T {f['T']:g} mm (0/{PARAMS['T_tol_lower']:+.1f} mm)"
                if self.family == "square":
                    d += f", W {f['W']:g} mm across flats"
                if self.family == "compact":
                    d += f", {f['width']:g} mm across two flats (D + 6)"
                d += f", {n} counterbored holes d1 {f['d1']:g} / d2 {f['d2']:g} x {f['t']:g} deep"
                d += (f" on P.C.D. {f['pcd']:g} mm" if self.family != "compact" else f", A {f['A']:g} mm apart along H" +
                      (f" and F {f['F']:g} mm across" if f.get("F") else ""))
        d += f". {self.material}. Solid lubricant plugs, chamfers and rotation stopper screw {APPX}: not drawn."
        return d + " Generated from the published catalogue dimensions."

def parse(code: str) -> Part:
    raw = code
    s = code.strip().upper()
    m = CODE.match(s)
    if not m:
        if KNOWN_UNMODELLED.match(s):
            raise CodeError(f"{raw!r}: this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the "
                            "resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520)")
        raise CodeError(f"{raw!r}: expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, "
                        "E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35")
    typ, ds, ls = m.groups()
    d, L = int(ds), int(ls)
    t = TYPES[typ]
    tab = TABLES[t["table"]]
    pg = PAGE[t["table"]]
    thin = t["wall"] == "thin"
    fam = t["family"]
    name = f"{typ}{d}-{L}"
    if d not in tab:
        offer = sorted(tab)
        if thin:
            offer = [k for k in offer if tab[k].get("D_thin")]
        raise CodeError(f"{name}: {typ} is offered for I.D. d {offer} ({pg})")
    r = tab[d]
    if thin and not r.get("D_thin"):
        raise CodeError(f"{name}: the thin wall type {typ} is not offered for d {d}; thin wall d is "
                        f"{sorted(k for k in tab if tab[k].get('D_thin'))} ({pg})")
    ok = offered_lengths(r["lengths"], thin=thin, square=fam == "square")
    if L not in ok:
        why = ""
        if fam == "square" and L in offered_lengths(r["lengths"]):
            why = f" (L {L} is printed in brackets: round and compact flanges only, not the square flange)"
        elif fam in ("straight", "shouldered") and L in offered_lengths(r["lengths"], thin=not thin):
            why = f" (L {L} is printed for the {'standard' if thin else 'thin'} wall type only)"
        raise CodeError(f"{name}: {typ}{d} is offered in L {ok}{why} ({pg})")
    bore_tol = (r["bore_tol_upper"], r["bore_tol_lower"])
    L_tol = (PARAMS["L_tol_upper"], PARAMS["L_tol_lower"])
    kw = dict(code=name, type=typ, family=fam, wall=t["wall"], material=t["material"], d=d, L=L, bore_class=t["bore_class"],
              od_class=t["od_class"], bore_tol=bore_tol, L_tol=L_tol, page=pg)
    if fam == "straight":
        return Part(**kw, D=r["D_thin"] if thin else r["D"], N=r["N_thin"] if thin else r["N"])
    if fam == "shouldered":
        if thin:
            return Part(**kw, D=r["D_thin"], N=r["N_thin"], flange=dict(H=r["H_thin"], t=r["t_thin"]))
        return Part(**kw, D=r["D"], N=r["N"], flange=dict(H=r["H"], t=r["t"]))
    if fam == "thrust":
        return Part(**kw, D=r["D"], flange=dict(H=r["H"], t=r["t"]))
    # flanged: round / square / compact
    fl = dict(H=r["H"], T=r["T"], t=r["t"], d1=r["d1"], d2=r["d2"], pcd=r["pcd"], A=r["A"], F=r.get("F"))
    if fam == "square":
        fl["W"] = r["W"]
    if fam == "compact":
        fl["width"] = r["D"] + PARAMS["compact_flat_extra"]
    return Part(**kw, D=r["D"], flange=fl)

def hole_centres(b: Part):
    """(y, z) of the mounting holes. Round: 2 holes on the Z axis for d 6-13 (F empty), 4 on the axes from d 16, on P.C.D. Square: 4 holes on
    the axes (the square stands on its corner). Compact: A apart along Z and, from d 16, F apart along Y."""
    f = b.flange
    if b.family == "compact":
        a = f["A"] / 2
        if f.get("F"):
            e = f["F"] / 2
            return [(e, a), (-e, a), (-e, -a), (e, -a)]
        return [(0, a), (0, -a)]
    r = f["pcd"] / 2
    if b.family == "round" and not f.get("F"):
        return [(0, r), (0, -r)]
    return [(r, 0), (0, r), (-r, 0), (0, -r)]

def commands(b: Part) -> list[dict]:
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    D, L, R = b.D, b.L, b.D / 2
    add("component.create", name=b.code)
    f = b.flange
    if b.family in ("shouldered", "thrust", "round"):
        fl = f["t"] if b.family != "round" else f["T"]
        pts = [[0, 0], [L, 0], [L, R], [fl, R], [fl, f["H"] / 2], [0, f["H"] / 2]]
    else:
        pts = [[0, 0], [L, 0], [L, R], [0, R]]
    add("sketch.create", plane="XY", name="Profile")
    add("sketch.line", points=pts, closed=True)
    add("sketch.finish")
    add("solid.revolve", axis="x", name="Body", body_name=b.code)
    if b.family == "compact":
        e, Rh = f["width"] / 2, f["H"] / 2           # flats e from the axis along Y, circle H clipping the ends along Z
        s = math.sqrt(Rh * Rh - e * e)
        add("sketch.create", plane="YZ", name="Flange")
        add("sketch.line", points=[[e, -s], [e, s]])
        add("sketch.arc.three_point", start=[e, s], through=[0, Rh], end=[-e, s])
        add("sketch.line", points=[[-e, s], [-e, -s]])
        add("sketch.arc.three_point", start=[-e, -s], through=[0, -Rh], end=[e, -s])
        add("sketch.finish")
        add("solid.extrude", distance=f["T"], operation="join", targets=[b.code], name="Compact flange")
    if b.family == "square":
        a = f["W"] / math.sqrt(2)           # the square stands on its corner: vertices on the axes, clipped by the circle H
        Rh = f["H"] / 2
        s = math.sqrt(2 * Rh * Rh - a * a)
        py, pz = (a + s) / 2, (a - s) / 2
        add("sketch.create", plane="YZ", name="Flange")
        for p, q in [((py, -pz), (pz, -py)), ((-pz, -py), (-py, -pz)), ((-py, pz), (-pz, py)), ((pz, py), (py, pz))]:
            add("sketch.line", points=[list(p), list(q)])
        for p, t, q in [((py, pz), (Rh, 0), (py, -pz)), ((pz, -py), (0, -Rh), (-pz, -py)), ((-py, -pz), (-Rh, 0), (-py, pz)),
                        ((-pz, py), (0, Rh), (pz, py))]:
            add("sketch.arc.three_point", start=list(p), through=list(t), end=list(q))
        add("sketch.finish")
        add("solid.extrude", distance=f["T"], operation="join", targets=[b.code], name="Square flange")
    add("solid.cylinder", diameter=b.d, height=L + 2, base=[-1, 0, 0], axis="X", operation="cut", targets=[b.code], name="Bore")
    if b.family in ("round", "square", "compact"):
        for i, (y, z) in enumerate(hole_centres(b)):       # counterbores on the outer flange face (x = 0), figure reading
            add("solid.hole", position=[0, y, z], diameter=f["d1"], type="counterbore", cb_diameter=f["d2"], cb_depth=f["t"],
                depth=f["T"], targets=[b.code], name=f"Mounting hole {i + 1}")
    add("component.metadata.set", component=b.code, part_number=b.code, description=b.description, material=b.material)
    add("document.metadata.set", values={"part_number": b.code, "description": b.description})
    return cmds

def parse_build(code: str):
    b = parse(code)
    return b, commands(b)
