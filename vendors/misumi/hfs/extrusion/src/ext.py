"""MISUMI aluminium extrusion (5 series 2020/2040/4040, 6 series 3030) ordering-code parser and native-SolidCraft command builder.

Every dimension is cited in sources.toml (S-numbers in comments refer to it); cross-section numbers live in profiles.py.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from .profiles import P, Arc, outline, all_bores, SIDES, DATA
from runtime.table import read_csv, num

class CodeError(ValueError):
    """The ordering code is not valid; the message says why."""

class NotModelled(CodeError):
    """The code is valid MISUMI grammar but this prototype does not build that option or profile."""

# ---- grammar tables (docs/grammar.md) -------------------------------------------------------------
# Four-slot-family types drawn here: code -> (material, surface). S1 p.529-530 (5 series), S10 p.571 (6 series).
# A row with `profiles` set applies to those profiles only (NFS: A6063S-T5 on 2020, p.529; A6063SS-T5 on 2040 / 4040, p.530).
_TYPE_ROWS = read_csv(DATA / "types.csv")
TYPES5 = {_r["type"]: (_r["material"], _r["surface"]) for _r in _TYPE_ROWS if _r["series"] == "5"}
TYPES6 = {_r["type"]: (_r["material"], _r["surface"]) for _r in _TYPE_ROWS if _r["series"] == "6"}
TYPE_BY_PROFILE = {(_r["type"], _pf): (_r["material"], _r["surface"]) for _r in _TYPE_ROWS for _pf in _r["profiles"].split("|") if _pf}
# types whose p.530 table has no HFSY5 (2040, 4040)
NO_YELLOW = {"2040", "4040"}
TYPES = {**TYPES5, **TYPES6}
# Valid catalogue types of those series whose cross-section is not drawn here.
OTHER_TYPES = {"NFSF5", "HFSF5", "HFSFB5", "NFST5", "HFST5", "HFSTB5", "HFSH5", "HFSC5", "HFSR5",
               "NEFS6", "NEFSB6", "EFS6", "EFSB6", "GFS6", "NFSL6", "HFSL6", "HFSLB6", "NEFSF6", "EFSF6", "HFSF6", "HFSFB6",
               "NEFST6", "EFST6", "HFST6", "HFSTB6", "HFSH6", "EFSH6", "HFSC6", "EFSC6"}
PROFILES = {5: {"2020", "2040", "4040"}, 6: {"3030"}}   # profiles whose drawing was read
_PARAMS = {_r["name"]: _r["value"] for _r in read_csv(DATA / "params.csv")}
FIXED_LENGTHS = {int(v) for v in _PARAMS["fixed_lengths"].split("|")}   # S1, S10
L_MIN, L_MAX, L_STEP = (float(_PARAMS[k]) for k in ("l_min", "l_max", "l_step"))   # S1, S10: 50-4000 mm, 0.5 mm steps

END_TAP = {"LTP": "L", "RTP": "R", "TPW": "LR"}
HELI_TAP = {"LHP", "RHP", "HPW"}
NOT_MODELLED_ALT = {"SC": "High Precision Cut (tolerance L+-0.2 for L<=1500): recorded, no geometry",
                    "CW": "End face C chamfer (thread chamfer C0.2-0.3): not modelled"}
WRENCH = re.compile(r"^([LR])([CWE])([HVP])$")
WRENCH_ROWS = {"C": 1, "W": 2, "E": 3}
XDIA = re.compile(r"^X([58])$")                # 6 series wrench hole diameter option (S3 p.759 footnote)

@dataclass
class Extrusion:
    code: str
    fixed: bool
    type: str
    material: str
    surface: str
    profile: str
    length: float
    end_tap: str = ""                  # "", "L", "R", "LR"
    wrench: dict = field(default_factory=dict)   # side -> dict(rows, orient, shift, axis_name)
    wrench_d: float = 0.0
    high_precision: bool = False
    tolerance: float = 0.5
    notes: list = field(default_factory=list)

    @property
    def spec(self):
        return P[self.profile]

    @property
    def part_number(self) -> str:
        return self.code

    @property
    def description(self) -> str:
        t, dep = self.spec.tap
        d = f"MISUMI aluminium extrusion {self.type}-{self.profile} {self.surface.lower()}, {self.material}, L={self.length:g} mm"
        if self.end_tap:
            d += f", end tapped {t} depth {dep:g} ({'both ends' if self.end_tap == 'LR' else 'left end' if self.end_tap == 'L' else 'right end'})"
        for side, w in sorted(self.wrench.items()):
            d += f", {side.lower() == 'l' and 'left' or 'right'} wrench access holes x{w['rows']} {w['axis_name']} d{self.wrench_d:g}"
        return d + ". Generated from the published catalogue dimensions."

CODE = re.compile(r"^(K?)([A-Z]+[56])-(\d{4,6})(?:-([0-9]+(?:\.[0-9]+)?))?((?:-[A-Z0-9]+)*)$")

def parse(code: str) -> Extrusion:
    raw = code
    code = code.strip().upper()
    m = CODE.match(code)
    if not m:
        raise CodeError(f"{raw!r}: expected [K]<type>5|6-<profile>-<length>[-<alteration>...], e.g. HFS5-2040-800-LTP-RTP")
    k, typ, prof, length_s, alts_s = m.groups()
    series = int(typ[-1])
    if typ in OTHER_TYPES:
        raise NotModelled(f"{typ}: valid {series} series type, but only {sorted(t for t in TYPES if t.endswith(str(series)))} are drawn")
    if typ not in TYPES:
        raise CodeError(f"unknown {series} series type {typ!r}; known: {sorted(set(TYPES) | OTHER_TYPES)}")
    if prof not in PROFILES[series]:
        raise CodeError(f"profile {prof!r} not available for {typ} here; verified for the {series} series: {sorted(PROFILES[series])}")
    if typ == "HFSY5" and prof in NO_YELLOW:
        raise CodeError(f"HFSY5 is listed for 2020 only (S1 p.530 type table has no HFSY5 for {prof})")
    if length_s is None:
        raise CodeError("a length is required: the last number before the alterations, in mm")
    length = float(length_s)
    fixed = bool(k)
    if fixed:
        if length not in FIXED_LENGTHS:
            raise CodeError(f"fixed-length (K) extrusions come only in {sorted(FIXED_LENGTHS)} mm, not {length:g}")
    else:
        if not (L_MIN <= length <= L_MAX):
            raise CodeError(f"length {length:g} mm outside {L_MIN:g}-{L_MAX:g} mm")
        if abs(length / L_STEP - round(length / L_STEP)) > 1e-9:
            raise CodeError(f"length {length:g} mm is not a multiple of {L_STEP} mm")
    mat, surf = TYPE_BY_PROFILE.get((typ, prof), TYPES[typ])
    e = Extrusion(code=code, fixed=fixed, type=("K" if fixed else "") + typ, material=mat, surface=surf,
                  profile=prof, length=length)
    sp = e.spec
    alts = [a for a in alts_s.split("-") if a]
    if alts and fixed:
        raise CodeError("alterations apply to configurable-length extrusions only (fixed-length K types have none)")
    seen = set()
    xdia = None
    for a in alts:
        if a in seen:
            raise CodeError(f"alteration {a} given twice")
        seen.add(a)
        if a in END_TAP:
            if set(e.end_tap) & set(END_TAP[a]):
                raise CodeError(f"end tapping given twice for the same end ({a})")
            e.end_tap = "".join(sorted(set(e.end_tap) | set(END_TAP[a])))
        elif a in HELI_TAP:
            raise NotModelled(f"{a}: heli-coil end tapping: parsed, not modelled")
        elif WRENCH.match(a):
            side, rows, orient = WRENCH.match(a).groups()
            if orient == "P":
                raise NotModelled(f"{a}: crisscross (P) layout is ambiguous in the catalogue text; use H or V")
            if side in e.wrench:
                raise CodeError(f"two wrench-hole options for the {'left' if side == 'L' else 'right'} end")
            e.wrench[side] = dict(rows=WRENCH_ROWS[rows], orient=orient, shift=0.0,
                                  axis_name="horizontal" if orient == "H" else "vertical")
        elif XDIA.match(a):
            xdia = float(XDIA.match(a).group(1))
        elif a in ("FL", "FR"):
            pass
        elif a in NOT_MODELLED_ALT:
            if a == "SC":
                if length > 1500:
                    raise CodeError("SC (high precision cut) applies to L <= 1500 mm only")
                e.high_precision = True; e.tolerance = 0.2
                e.notes.append("SC: tolerance L+-0.2 (no geometry change)")
            else:
                raise NotModelled(f"{a}: {NOT_MODELLED_ALT[a]}")
        else:
            raise CodeError(f"unknown or unsupported alteration {a!r}")
    # wrench hole diameter: one value for 5 series, X5 / X8 to be given for the 6 series (S3 p.759)
    if e.wrench:
        if len(sp.wrench_d) == 1:
            if xdia is not None:
                raise CodeError("X5/X8 (wrench hole diameter) applies to the 6 series; the 5 series hole is d7.35")
            e.wrench_d = sp.wrench_d[0]
        else:
            if xdia is None:
                raise CodeError("the 6 series wrench hole diameter is selectable: add -X5 or -X8 (S3 p.759 footnote)")
            e.wrench_d = xdia
    elif xdia is not None:
        raise CodeError("X5/X8 sets the wrench hole diameter; there is no wrench hole alteration in this code")
    for a in ("FL", "FR"):
        if a in seen:
            side = a[1]
            if side not in e.wrench:
                raise CodeError(f"{a} shifts a wrench hole on the {'left' if side == 'L' else 'right'} end, but there is none")
            e.wrench[side]["shift"] = 3.0      # S3 p.760: moves the hole 3 mm toward the end (end cap thickness)
            e.notes.append(f"{a}: the p.760 table lists 6 and 8 series only; availability on the 5 series is unverified")
    if e.end_tap and 2 * sp.tap[1] > length:
        raise CodeError("tapped holes overlap")
    for side, w in e.wrench.items():
        xs = wrench_positions(e, side)
        d = e.wrench_d
        if min(xs) - d / 2 < 0 or max(xs) + d / 2 > length:
            raise CodeError(f"wrench holes at {xs} do not fit in a {length:g} mm length")
    return e

def wrench_positions(e: Extrusion, side: str) -> list[float]:
    """Distance of each wrench-hole centre from x=0 (the left end)."""
    w = e.wrench[side]
    Hh, J, K = e.spec.wrench_hjk
    H = Hh - w["shift"]
    offs = [H, H + J, H + J + K][: w["rows"]]
    return offs if side == "L" else [e.length - o for o in offs]

# ---- command builder -------------------------------------------------------------------------
def _void_runs(path):
    """Split a void path (points and Arc items) into drawing steps: ("line", [pts]) and ("arc", Arc). Each run of
    points starts at the end of the arc before it and ends at the start of the arc after it, so that the pieces join
    by coincident end points."""
    items = list(path)
    ai = [i for i, it in enumerate(items) if isinstance(it, Arc)]
    s = ai[-1] + 1                          # start right after an arc so that no run wraps around the end
    items = items[s:] + items[:s]
    prev_arc = items[-1]                    # cyclic: the arc before the first run
    steps, run = [], []
    for it in items:
        if isinstance(it, Arc):
            if not run:
                run = [prev_arc.b]
            if run[-1] != it.a:
                run.append(it.a)
            steps.append(("line", run)); steps.append(("arc", it)); run = []; prev_arc = it
        else:
            if not run:
                run = [prev_arc.b]
            run.append(it)
    return steps

def commands(e: Extrusion) -> list[dict]:
    """SolidCraft command list (solidcraft-cli run). The extrusion runs along +X from x=0 (left end)
    to x=L; its section is drawn on the YZ plane (sketch x = world Y, y = world Z)."""
    sp = e.spec
    pts = outline(sp)
    n = len(pts)
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    add("component.create", name=e.code)
    add("sketch.create", plane="YZ", name="Profile")
    add("sketch.line", points=[[x, y] for x, y, _ in pts], closed=True)
    # Corner i joins line i-1 and line i; with closed=True the lines are l1..l{n}; point between
    # l{i} and l{i+1} is l{i}.end.
    corner = [f"l{(i - 1) % n + 1}.end" for i in range(n) if pts[i][2] == "corner"]
    mouth = [f"l{(i - 1) % n + 1}.end" for i in range(n) if pts[i][2] == "mouth"]
    add("sketch.fillet", points=corner, radius=sp.corner_r)
    add("sketch.fillet", points=mouth, radius=sp.slot.tip_r)
    for v in sp.voids:
        if any(isinstance(it, Arc) for it in v):
            for kind, s in _void_runs(v):
                if kind == "line":
                    add("sketch.line", points=[[x, y] for x, y in s])
                else:
                    add("sketch.arc.three_point", start=list(s.a), through=list(s.t), end=list(s.b))
        else:
            add("sketch.line", points=[[x, y] for x, y in v], closed=True)
    for bx, by, d in sp.bores:
        add("sketch.circle.center", center=[bx, by], diameter=d)
    add("sketch.finish")
    add("solid.extrude", distance=e.length, name="Extrusion", body_name=e.code)
    # machining
    for side, w in sorted(e.wrench.items()):
        for i, x in enumerate(wrench_positions(e, side)):
            d = e.wrench_d
            if w["orient"] == "H":
                base, axis, ln = [x, -sp.w / 2 - 1, 0], "Y", sp.w + 2
            else:
                base, axis, ln = [x, 0, -sp.h / 2 - 1], "Z", sp.h + 2
            add("solid.cylinder", diameter=d, height=ln, base=base, axis=axis, operation="cut",
                targets=[e.code], name=f"Wrench hole {side}{i + 1}")
    # Tapped ends (sources.toml row 1905): the hole is the printed pilot bore (the tap drill, O4.2 for M5 / O6.8 for M8) that is already in
    # the section; the thread is cosmetic, of the catalogue's nominal size and depth, laid on that bore. The nominal diameter is never cut.
    thread, depth = sp.tap
    for side in e.end_tap:
        x_from = 0.5 if side == "L" else e.length - 0.5
        for bi, (bx, by, d) in enumerate(all_bores(sp)):
            if sp.arc_bores:       # 4040: the O4.2 bores are arcs of the void loop; take the point facing away from the section centre
                ux, uy = (1 if bx > 0 else -1) / 2 ** 0.5, (1 if by > 0 else -1) / 2 ** 0.5
            else:
                ux, uy = 1.0, 0.0
            if len(all_bores(sp)) > 1 and not sp.arc_bores:
                pass
            if sp.key == "3030" and d != 6.8:
                continue                      # the four corner O4.2 holes are not tapped (S2 p.757: 1 tapped hole per end)
            py, pz = bx + ux * d / 2, by + uy * d / 2
            add("solid.thread", face=[x_from, py, pz], designation=thread, extent="length", length=depth,
                **{"from": [0.0 if side == "L" else e.length, py, pz]}, name=f"Tap {side}{bi + 1}")
    add("browser.visibility", items=["Profile"], visible=False)
    add("component.metadata.set", component=e.code, part_number=e.part_number, description=e.description,
        material=f"{e.material}, {e.surface}")
    add("document.metadata.set", values={"part_number": e.part_number, "description": e.description})
    return cmds

def parse_build(code: str):
    e = parse(code.strip().upper())
    return e, commands(e)
