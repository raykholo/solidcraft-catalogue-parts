"""MISUMI aluminium extrusion cross-sections (5 series 2020/2040/4040, 6 series 3030): dimensions and outline builders.

Every number is cited in sources.toml: "labelled" = printed on the catalogue drawing, "measured" = read from the vertex
coordinates of the vector drawing in the catalogue PDF (accuracy about 0.05 mm), "approximate" = not printed and not
measurable on the page (the part description says so).
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from pathlib import Path
from runtime.table import read_csv, num

DATA = Path(__file__).resolve().parent.parent / "data"

@dataclass(frozen=True)
class SlotDim:
    mouth: float        # opening between the lip tips
    lip: float          # lip thickness (outer face to cavity roof)
    cavity: float       # cavity width
    d0: float           # depth where the cavity wall ends and the 45 degree flank starts
    floor_half: float   # half width of the slot floor
    depth: float        # outer face to slot floor
    tip_r: float        # round on each lip tip outer corner

    def check(self):
        # the flank is 45 degrees: horizontal run equals vertical run
        run = self.cavity / 2 - self.floor_half
        assert abs((self.depth - self.d0) - run) < 0.06, (self.depth, self.d0, run)

@dataclass(frozen=True)
class Profile:
    key: str                 # "2020"
    series: int              # 5 or 6
    w: float                 # extent along sketch x (world Y)
    h: float                 # extent along sketch y (world Z)
    corner_r: float
    slot: SlotDim
    slots: dict              # side R/T/L/B -> offsets along the side (see side_frame)
    voids: tuple = ()        # closed polygons (sketch x, y), CCW
    bores: tuple = ()        # (x, y, diameter) separate circles in the sketch
    tap: tuple = ("M5", 15.0)
    published_area: float = 0.0
    published_i: tuple = (0.0, 0.0)   # catalogue Ix, Iy in mm4 (axis naming as the catalogue's, compared sorted)
    page: str = ""
    # wrench access holes: H, J, K and the diameters allowed
    wrench_hjk: tuple = (10.0, 20.0, 20.0)
    wrench_d: tuple = (7.35,)
    arc_bores: tuple = ()    # (x, y, diameter) bores that are arcs of a void loop (4040)
    published_mass: float = 0.0   # catalogue mass per metre, kg/m

# ---- slot dimensions: one row per profile in data/profiles.csv (S1 p.529-530 for the 5 series; S10 p.571 for the 6 series 3030:
# mouth 8, cavity 16.5, lip 2, depth 9 labelled; d0 and floor_half measured (cavity wall ends at depth 5.35, floor half width
# 4.6, the flank is 45 degrees); tip round approximate). The flank is checked at load.

def _rot(p, k):
    x, y = p
    for _ in range(k % 4):
        x, y = -y, x
    return (x, y)

@dataclass(frozen=True)
class Arc:
    """A circular arc in a void path, counter-clockwise from `a` through `t` to `b` about `c`."""
    a: tuple
    t: tuple
    b: tuple
    c: tuple
    r: float

WEB = 1.5       # 4040: web thickness between a slot flank and the void (labelled 1.5)
NOTCH = 3.6     # 4040: default of the bore-block inner-corner notch (data/profiles.csv column void_notch overrides it)

def _void_4040(notch=NOTCH, flank=21.0):
    """Central void of the 4040, CCW: four arms (flat 4 wide, 2 mm behind the outer face, 1 mm run, then 45 degree webs to the
    bore blocks' inner faces), and at each 8 x 8 bore block the inner corner cut away (a NOTCH square) which opens into the
    O4.2 bore, so the bores are arcs of this loop (3/4 of the circle) and not separate circles. Items: (x, y) or Arc."""
    # The web is 1.5 mm thick (labelled): its two faces are the slot flank x + y = 21 (in the arm frame) and x + y = c.
    c = flank - WEB * math.sqrt(2)
    f, a, blk = 2.0, 18.0, 6.0                          # arm flat half width, flat x, block inner face
    b, foot = c - f, c - blk                            # wall end x (about 17), web foot on the block face (about 13)
    cx = cy = 10.0
    r = 2.1
    X = blk + notch
    yc = cy - math.sqrt(r * r - (cy - X) ** 2)         # circle meets the notch edge x = X
    items = []
    for k in range(4):
        pts = [(foot, -blk), (b, -f), (a, -f), (a, f), (b, f), (foot, blk), (X, blk), (X, yc)]
        arc = (X, yc), (cx + r * math.cos(math.pi / 4), cy + r * math.sin(math.pi / 4)), (yc, X)
        tail = [(yc, X), (blk, X)]
        for p in pts:
            items.append(_rot(p, k))
        items.append(Arc(_rot(arc[0], k), _rot(arc[1], k), _rot(arc[2], k), _rot((cx, cy), k), r))
        # the arc's end point (yc, X) is the first point of `tail`
        for p in tail[1:]:
            items.append(_rot(p, k))
    return tuple(items)

def path_polyline(path, n=400):
    """Vertices of a void path with the arcs sampled (for area and moments)."""
    out = []
    for it in path:
        if isinstance(it, Arc):
            a0 = math.atan2(it.a[1] - it.c[1], it.a[0] - it.c[0])
            a1 = math.atan2(it.b[1] - it.c[1], it.b[0] - it.c[0])
            while a1 <= a0:
                a1 += 2 * math.pi
            for i in range(1, n):
                t = a0 + (a1 - a0) * i / n
                out.append((it.c[0] + it.r * math.cos(t), it.c[1] + it.r * math.sin(t)))
            out.append(it.b)
        else:
            out.append(it)
    return out

def _void_2040():
    """Central void of the 2040 between the two bore blocks (0, +-10): hexagon with 4 mm wide flats 2 mm behind the left and
    right faces. CCW."""
    return ((3, -6), (7, -2), (8, -2), (8, 2), (7, 2), (3, 6), (-3, 6), (-7, 2), (-8, 2), (-8, -2), (-7, -2), (-3, -6))

def _slots(txt):
    return {side.split(":")[0]: [num(o) for o in side.split(":")[1].split(";")] for side in txt.split("|")}

def _bores(txt):
    return tuple(tuple(num(v) for v in b.split(":")) for b in txt.split("|")) if txt else ()

def _void_args(r):
    """Arguments of the 4040 void: the notch (csv column void_notch) and the slot flank line x + y = w/2 - depth + 10 - floor_half (arm frame), which the
    1.5 mm web is measured from; the 2040 void takes none."""
    if r["key"] != "4040":
        return {}
    return {"notch": num(r["void_notch"]), "flank": num(r["w"]) / 2 - num(r["depth"]) + 10.0 - num(r["floor_half"])}

_VOIDS = {"2040": _void_2040, "4040": _void_4040}      # the central voids: geometry read from the drawings, kept as code
P = {}
for _r in read_csv(DATA / "profiles.csv"):
    _sd = SlotDim(mouth=num(_r["mouth"]), lip=num(_r["lip"]), cavity=num(_r["cavity"]), d0=num(_r["d0"]),
                  floor_half=num(_r["floor_half"]), depth=num(_r["depth"]), tip_r=num(_r["tip_r"]))
    _sd.check()
    P[_r["key"]] = Profile(_r["key"], int(_r["series"]), num(_r["w"]), num(_r["h"]), num(_r["corner_r"]), _sd, _slots(_r["slots"]),
                           (_VOIDS[_r["key"]](**_void_args(_r)),) if _r["key"] in _VOIDS else (), _bores(_r["bores"]),
                           (_r["tap_thread"], num(_r["tap_depth"])), num(_r["published_area"]),
                           (num(_r["published_ix"]), num(_r["published_iy"])), _r["cite"],
                           (num(_r["wrench_h"]), num(_r["wrench_j"]), num(_r["wrench_k"])),
                           tuple(num(d) for d in _r["wrench_d"].split("|")), _bores(_r["arc_bores"]), num(_r["published_mass"]))

# ---- geometry -----------------------------------------------------------------------------
SIDES = "RTLB"   # CCW: right (+x) first, then top (+y), left, bottom
def side_frame(p: Profile, side: str):
    """(outward normal n, tangent t, centre point of the side's outer face, half length). t = n rotated +90 degrees,
    the direction of travel of the CCW outline; offsets in p.slots are measured along t from the side's centre."""
    hx, hy = p.w / 2, p.h / 2
    return {"R": ((1, 0), (0, 1), (hx, 0), hy), "T": ((0, 1), (-1, 0), (0, hy), hx),
            "L": ((-1, 0), (0, -1), (-hx, 0), hy), "B": ((0, -1), (1, 0), (0, -hy), hx)}[side]

def slot_local(s: SlotDim):
    """Slot outline in (u along t, v depth) from the first lip tip to the last, with a fillet tag."""
    m, w, f = s.mouth / 2, s.cavity / 2, s.floor_half
    return [(-m, 0.0, "mouth"), (-m, s.lip, ""), (-w, s.lip, ""), (-w, s.d0, ""), (-f, s.depth, ""),
            (f, s.depth, ""), (w, s.d0, ""), (w, s.lip, ""), (m, s.lip, ""), (m, 0.0, "mouth")]

def slot_point(p: Profile, side: str, off: float, u: float, v: float):
    """Sketch point at (u along the side's tangent, v depth) of the slot on `side` whose centre is `off` along it."""
    n, t, c, _ = side_frame(p, side)
    uu = off + u
    return (c[0] + uu * t[0] - v * n[0], c[1] + uu * t[1] - v * n[1])

def outline(p: Profile):
    """Closed outline CCW: list of (x, y, tag), tag in {"", "corner", "mouth"}. The corner point of a side's start comes first."""
    pts = []
    for side in SIDES:
        n, t, c, half = side_frame(p, side)
        # start corner of this side: centre - half * t
        pts.append((c[0] - half * t[0], c[1] - half * t[1], "corner"))
        for off in sorted(p.slots.get(side, [])):
            for u, v, tag in slot_local(p.slot):
                uu = off + u
                pts.append((c[0] + uu * t[0] - v * n[0], c[1] + uu * t[1] - v * n[1], tag))
    return pts

def _shoelace(poly):
    return sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
               for i in range(len(poly))) / 2

def expected_area(p: Profile) -> float:
    """Section area from the dimensions: outline minus the round-offs of the outer corners and lip tips, minus the voids and bores."""
    a = abs(_shoelace([(x, y) for x, y, _ in outline(p)]))
    a -= 4 * p.corner_r ** 2 * (1 - math.pi / 4)
    n_slots = sum(len(v) for v in p.slots.values())
    a -= n_slots * 2 * p.slot.tip_r ** 2 * (1 - math.pi / 4)
    for v in p.voids:
        a -= abs(_shoelace(path_polyline(v)))
    for _, _, d in p.bores:
        a -= math.pi * (d / 2) ** 2
    return a

def all_bores(p: Profile):
    return list(p.bores) + list(p.arc_bores)

def _poly_moments(poly):
    """(area, Ix, Iy) of a polygon about the origin (Ix = integral y^2 dA, Iy = integral x^2 dA), signed by orientation."""
    A = Ix = Iy = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % n]
        cr = x0 * y1 - x1 * y0
        A += cr
        Ix += (y0 * y0 + y0 * y1 + y1 * y1) * cr
        Iy += (x0 * x0 + x0 * x1 + x1 * x1) * cr
    return A / 2, Ix / 12, Iy / 12

def expected_moments(p: Profile):
    """(Ix, Iy) about the section centre from the outline, voids and bores (round-offs of the corners and lip tips included)."""
    o = [(x, y) for x, y, _ in outline(p)]
    _, ix, iy = _poly_moments(o)
    sgn = 1 if _shoelace(o) > 0 else -1
    ix, iy = ix * sgn, iy * sgn
    # the round-offs (outer corners R, lip tips R): each takes away a spandrel of area r^2 (1 - pi/4) whose centroid lies
    # 0.2234 r from the sharp corner along both edges (they are not small on the 3030: R2 corners at 14 mm from the axis)
    q = 1 - math.pi / 4
    n = len(outline(p))
    ol = outline(p)
    for i, (x, y, tag) in enumerate(ol):
        if tag not in ("corner", "mouth"):
            continue
        r = p.corner_r if tag == "corner" else p.slot.tip_r
        ax, ay, _ = ol[(i - 1) % n]; bx, by, _ = ol[(i + 1) % n]
        ul = math.hypot(ax - x, ay - y); vl = math.hypot(bx - x, by - y)
        cx = x + 0.2234 * r * ((ax - x) / ul + (bx - x) / vl)
        cy = y + 0.2234 * r * ((ay - y) / ul + (by - y) / vl)
        sa = r * r * q
        ix -= sa * cy * cy; iy -= sa * cx * cx
    for v in p.voids:
        vp = path_polyline(v); _, vx, vy = _poly_moments(vp); s = 1 if _shoelace(vp) > 0 else -1
        ix -= vx * s; iy -= vy * s
    for bx, by, d in p.bores:
        r = d / 2; ar = math.pi * r * r
        ix -= math.pi * r ** 4 / 4 + ar * by * by
        iy -= math.pi * r ** 4 / 4 + ar * bx * bx
    return ix, iy

if __name__ == "__main__":
    for k, p in P.items():
        ea = expected_area(p); ix, iy = expected_moments(p)
        print(k, "area", round(ea, 2), "published", p.published_area, f"{(ea/p.published_area-1)*100:+.2f}%",
              "I", round(ix), round(iy), "published", p.published_i)
