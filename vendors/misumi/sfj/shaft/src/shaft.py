"""MISUMI linear shafts: ordering-code parser, catalogue data and native-SolidCraft command builder.

Families (all MISUMI Economy Series catalogue 2025, https://th.c.misumi-ec.com/book/THA_EconomySeries_e-catalog2025/files/basic-html/page<N>.html,
page images files/mobile/<N>.jpg):

  straight   E-SFJ ... E-PSFG          "Linear Shafts Straight"                              p.432 (04-047)   source S8
  T          ... T                     "One End Tapped"                                      p.433 (04-048)   source S8
  C          ... C                     "One End Tapped with Wrench Slot"                     p.434 (04-049)   source S30
  Z          ... Z                     "Both Ends Tapped with Wrench Flat"                   p.435 (04-050)   source S30
  W          ... W                     "Both Ends Tapped"                                    p.436 (04-051)   source S30
  PG         E-SFPG ... E-PSSFPG       "One End Stepped and Tapped with Wrench Flats"        p.437 (04-052)   source S30
  PH         E-SFPH ... E-PFPGH        "Both Ends Stepped, Both Ends Tapped with Wrench Flats" p.438 (04-053) source S30

The shaft is a plain cylinder at its nominal diameter; the catalogue gives no end chamfer, so none is drawn.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path

from runtime.table import read_csv, num

class CodeError(ValueError):
    """The ordering code is not valid; the message says why."""

class NotModelled(CodeError):
    """Valid MISUMI grammar that this prototype does not build."""

DATA = Path(__file__).resolve().parent.parent / "data"

# type -> row of data/types.csv (family, base type, tolerance class, material, hardness, surface). p.432 type table, p.434-438 type tables.
TYPES = {_r["type"]: _r for _r in read_csv(DATA / "types.csv")}
# D -> g7 (upper, lower) mm, f8 (upper, lower) or None, L range g7 (min, max), L range f8 or None. p.432 spec table.
D_TABLE = {}
for _r in read_csv(DATA / "diameters.csv"):
    D_TABLE[int(_r["D"])] = ((num(_r["g7_upper"]), num(_r["g7_lower"])),
                             None if _r["f8_upper"] == "" else (num(_r["f8_upper"]), num(_r["f8_lower"])),
                             (num(_r["g7_lmin"]), num(_r["g7_lmax"])),
                             None if _r["f8_lmin"] == "" else (num(_r["f8_lmin"]), num(_r["f8_lmax"])))

def _taptable(name):
    return {int(_r["D"]): ((num(_r["lmin"]), num(_r["lmax"])), tuple(num(m) for m in _r["m_options"].split("|"))) for _r in read_csv(DATA / name)}

# One end tapped (p.433): D -> (L range, coarse M selection). Applies to the g7 types and E-PSFGT (f8, D6-30, same L range).
TAP_TABLE = _taptable("tap.csv")
# Tapped families: p.434 (C, one end + wrench slot), p.435 (Z, both ends + wrench flat), p.436 (W, both ends).
FAM_TAP = {"T": TAP_TABLE, "C": _taptable("tap_jc.csv"), "Z": _taptable("tap_jz.csv"), "W": _taptable("tap_jw.csv")}
# Stepped families: p.437 (PG) and p.438 (PH): D -> dict(L range, P range, M options, Y max).
def _steptable(name):
    return {int(_r["D"]): dict(L=(num(_r["lmin"]), num(_r["lmax"])), P=(num(_r["pmin"]), num(_r["pmax"])),
                               M=tuple(num(m) for m in _r["m_options"].split("|")), Y=num(_r["ymax"])) for _r in read_csv(DATA / name)}
FAM_STEP = {"PG": _steptable("stepped_pg.csv"), "PH": _steptable("stepped_ph.csv")}
FAM_PAGE = {"straight": 432, "T": 433, "C": 434, "Z": 435, "W": 436, "PG": 437, "PH": 438}
# Wrench flat SC / WSC / SX: D -> (W across flats, l1 flat length); p.432 tables "Applicable to D=6 or more" (the same table repeats on p.434-438).
WRENCH = {int(_r["D"]): (num(_r["W"]), num(_r["l1"])) for _r in read_csv(DATA / "wrench.csv")}
_P = {_r["name"]: num(_r["value"]) for _r in read_csv(DATA / "params.csv")}

# Flat surface FC / WFC: depth H by D.
def flat_depth(D: float) -> float:
    return _P["flat_depth_le_5"] if D <= 5 else _P["flat_depth_le_16"] if D <= 16 else _P["flat_depth_le_40"] if D <= 40 else _P["flat_depth_gt_40"]

def lfc_depth(P: float) -> float:
    return _P["lfc_depth_le_16"] if P <= 16 else _P["lfc_depth_gt_16"]

LKC_TOL = ((200, _P["lkc_tol_lt_200"]), (500, _P["lkc_tol_lt_500"]), (float("inf"), _P["lkc_tol_ge_500"]))   # +-0.03 / +-0.05 / +-0.1

CODE = re.compile(r"^(E-[A-Z]+)(\d{1,2})-(\d+(?:\.\d+)?)((?:-[A-Z0-9.]+)*)$")

# Alterations offered per family (the pages' alteration tables), and the wrench flat the ordering code requires.
ALTS = {"straight": {"LKC", "SC", "WSC", "FC", "WFC"}, "T": {"LKC", "SC", "WSC", "FC", "WFC"},
        "C": {"LKC", "SC", "FC", "WFC", "SX"}, "Z": {"LKC", "SC", "WSC", "FC", "WFC"}, "W": {"LKC", "SC", "WSC", "FC", "WFC"},
        "PG": {"LKC", "SC", "FC", "WFC", "SX", "LFC"}, "PH": {"SC"}}

@dataclass
class Shaft:
    code: str
    type: str
    D: int
    L: float
    tolerance_class: str
    tol: tuple
    material: str
    hardness: str
    surface: str
    family: str = "straight"
    tapped: bool = False          # at least one tapped end
    M: float = 0.0                # thread at the left end (first tap)
    lkc: bool = False
    length_tol: float | None = None
    F: float = 0.0                # left step length (stepped families)
    P: float = 0.0                # step diameter
    T: float = 0.0                # right step length (PH)
    ymax: float | None = None
    md: bool = False              # MD: effective tap length M x 3 (p.437)
    taps: list = field(default_factory=list)      # dicts: M, face (x of the end face), dir (+1 into the body from the left), depth, label
    flats: list = field(default_factory=list)     # dicts: kind sc/fc/lfc, x0, x1, axis, depth / across, r
    notes: list = field(default_factory=list)

    @property
    def name(self) -> str:
        return f"{self.type}{'T' if self.family == 'T' else ''}{self.D}"

    @property
    def total_length(self) -> float:
        return self.L + self.F + self.T

    @property
    def description(self) -> str:
        d = (f"MISUMI linear shaft {self.name}, L={self.L:g} mm, D tolerance {self.tolerance_class} "
             f"({self.tol[0]:+.3f}/{self.tol[1]:+.3f} mm, drawn at the nominal diameter), {self.material}, {self.hardness}")
        if self.surface != "-":
            d += f", {self.surface}"
        if self.F:
            d += f", left end stepped F={self.F:g} mm to P{self.P:g} g7"
        if self.T:
            d += f", right end stepped T={self.T:g} mm to P{self.P:g} g7"
        for t in self.taps:
            d += f", {t['label']} end tapped M{t['M']:g} depth {t['depth']:g}"
        if self.length_tol:
            d += f", length tolerance L+-{self.length_tol:g} (LKC)"
        return d + ". Generated from the published catalogue dimensions; no end chamfer (not given in the catalogue)."

_MRX = r"\d+(?:\.\d)?"

def parse(code: str) -> Shaft:
    raw = code
    c = code.strip().upper()
    m = CODE.match(c)
    if not m:
        raise CodeError(f"{raw!r}: expected <type><D>-<L>[-<option>...], e.g. E-PSFJ6-20 (straight), E-PSFJT6-30-M3 (one end tapped), "
                        "E-PSFJC6-40-M3-SC0, E-PSFJZ6-50-M3-N3-SC0, E-PSFJW6-50-M3-N3, E-PSFPG8-200-F4-P6-M3-SC0, E-PSFPH8-200-F5-P6-M3-T5-SC0")
    name, ds, ls, alts_s = m.groups()
    tflag = False
    if name in TYPES:
        typ = name
    elif name.endswith("T") and name[:-1] in TYPES and TYPES[name[:-1]]["family"] == "straight":
        typ, tflag = name[:-1], True
    else:
        raise CodeError(f"{name!r} is not a type of the catalogue: E-SFJ, E-SSFJ, E-PSFJ, E-PSSFJ, E-PSFG (+ T, C, Z, W) and the stepped "
                        "E-SFPG, E-SSFPG, E-PSFPG, E-PSSFPG, E-SFPH, E-SSFPH, E-PSFPH, E-PSSFPH, E-PFPGH")
    D = int(ds)
    trow = TYPES[typ]
    fam = "T" if tflag else trow["family"]
    base = trow["base"]
    page = FAM_PAGE[fam]
    sfx = {"straight": "", "T": "T", "C": "C", "Z": "Z", "W": "W"}.get(fam, "")
    if D not in D_TABLE:
        raise CodeError(f"diameter {D}: catalogue sizes are {sorted(D_TABLE)}")
    cls, mat, hard, surf = trow["tolerance_class"], trow["material"], trow["hardness"], trow["surface"]
    g7, f8, lg7, lf8 = D_TABLE[D]
    if cls == "f8":
        if f8 is None:
            raise CodeError(f"{typ} has no D{D}: the f8 type is listed for D 6-30 (p.432 note: D3, 4, 5 not applicable, 35/40/50 only E-PSFJ)")
        tol, lrange = f8, lf8
    else:
        tol, lrange = g7, lg7
    if D in (35, 40, 50) and base != "E-PSFJ" and fam in ("straight", "T", "C", "Z", "W"):
        raise CodeError(f"O.D. {D} is applicable only to E-PSFJ{sfx} (p.{page} note)")
    L = float(ls)
    toks = [t for t in alts_s.split("-") if t]
    s = Shaft(code=c, type=typ, D=D, L=L, tolerance_class=cls, tol=tol, material=mat, hardness=hard, surface=surf, family=fam)

    # ---- family specific positional fields: threads (M, N), steps (F, P, T)
    def thread_tok(prefix, label):
        if toks and re.fullmatch(prefix + _MRX, toks[0]):
            return float(toks.pop(0)[len(prefix):])
        return None

    if fam in ("T", "C", "Z", "W"):
        table = FAM_TAP[fam]
        if D not in table:
            raise CodeError(f"{typ}{'T' if fam == 'T' else ''}{D}: no such version of D{D} in the p.{page} table "
                            f"(D {min(table)}-{max(table)}{'; D3 and D4/D5 are only on p.432-433/436' if fam in ('C', 'Z') else ''})")
        if cls == "f8" and D in (4, 5):
            raise CodeError(f"{typ}{'T' if fam == 'T' else ''}{D}: no tapped version of D{D} in the p.{page} table")
        lrange, Ms = table[D]
        tail = {"T": f"{typ}T{D}-{int(L)}-M{Ms[-1]:g}", "C": f"{typ}{D}-{int(L)}-M{Ms[-1]:g}-SC0",
               "Z": f"{typ}{D}-{int(L)}-M{Ms[-1]:g}-N{Ms[-1]:g}-SC0", "W": f"{typ}{D}-{int(L)}-M{Ms[-1]:g}-N{Ms[-1]:g}"}[fam]
        M = thread_tok("M", "M")
        if M is None:
            raise CodeError(f"a tapped shaft needs its thread after the length, e.g. {tail} (choices for D{D}: " + ", ".join(f"M{x:g}" for x in Ms) + ")")
        if M not in Ms:
            raise CodeError(f"M{M:g} is not offered for D{D} (coarse selection p.{page}: " + ", ".join(f"M{x:g}" for x in Ms) + ")")
        s.tapped = True; s.M = M
        s.taps.append(dict(M=M, face=0.0, dir=1, depth=2 * M, label="left"))
        if fam in ("Z", "W"):
            N = thread_tok("N", "N")
            if N is None:
                raise CodeError(f"both ends tapped: the second thread N follows M, e.g. {tail} (choices for D{D}: " + ", ".join(f"N{x:g}" for x in Ms) + ")")
            if N not in Ms:
                raise CodeError(f"N{N:g} is not offered for D{D} (coarse selection p.{page}: " + ", ".join(f"N{x:g}" for x in Ms) + ")")
            s.taps.append(dict(M=N, face=L, dir=-1, depth=2 * N, label="right"))
            if 2 * M + 2 * N > L:
                raise CodeError(f"overall length L = {L:g} requires M x 2 + N x 2 <= L = {2 * M + 2 * N:g} (p.{page} note)")
            if 2.5 * M + 4 + 2.5 * N + 4 >= L:
                s.notes.append("M x 2.5 + 4 + N x 2.5 + 4 >= L: the catalogue says the tap pilot holes may go through")
    elif fam in ("PG", "PH"):
        table = FAM_STEP[fam]
        if D not in table:
            raise CodeError(f"{typ}{D}: the stepped shafts of p.{page} are listed for D {min(table)}-{max(table)} only (D 8, 10, 12, 13, 15, 16, 20, 25, 30)")
        row = table[D]
        lrange, Ms = row["L"], row["M"]
        ex = f"{typ}{D}-200-F4-P{row['P'][0]:g}-M{Ms[0]:g}" + ("-T4" if fam == "PH" else "") + "-SC0"
        ftok = toks.pop(0) if toks and re.fullmatch(r"F\d+", toks[0]) else None
        ptok = toks.pop(0) if toks and re.fullmatch(r"P\d+", toks[0]) else None
        if ftok is None or ptok is None:
            raise CodeError(f"a stepped shaft needs the step length F and diameter P after L, e.g. {ex}")
        F, P = int(ftok[1:]), int(ptok[1:])
        if not (row["P"][0] <= P <= row["P"][1]):
            raise CodeError(f"P{P} is outside P {row['P'][0]:g}-{row['P'][1]:g} for D{D} (p.{page} table)")
        if not (_P["step_f_min"] <= F <= _P["step_f_max_factor"] * P):
            raise CodeError(f"F{F} is outside 2 <= F <= P x 4 = {_P['step_f_max_factor'] * P:g} (p.{page})")
        md = False
        if toks and re.fullmatch(r"MD" + _MRX, toks[0]):
            md = True; M = float(toks.pop(0)[2:])
        elif toks and re.fullmatch(r"M" + _MRX, toks[0]):
            M = float(toks.pop(0)[1:])
        else:
            raise CodeError(f"a stepped shaft needs its thread M after P, e.g. {ex} (choices for D{D}: " + ", ".join(f"M{x:g}" for x in Ms) + ")")
        if M not in Ms:
            raise CodeError(f"M{M:g} is not offered for D{D} (coarse selection p.{page}: " + ", ".join(f"M{x:g}" for x in Ms) + ")")
        if M >= P:
            raise CodeError(f"M{M:g} does not fit into the step P{P}")
        depth = 2 * M
        if md:
            if fam != "PG":
                raise CodeError("MD (effective tap length M x 3) is an alteration of p.437 only")
            if not (_P["md_d_min"] <= D <= _P["md_d_max"] and _P["md_m_min"] <= M <= _P["md_m_max"]):
                raise CodeError(f"MD applies to D = 12-30 and M = 6-20 (p.437), not D{D} M{M:g}")
            depth = _P["md_tap_factor"] * M
            if 3.5 * M + 4 > L:
                raise CodeError(f"MD x 3.5 + 4 = {3.5 * M + 4:g} exceeds L = {L:g} (p.437)")
        T = 0
        if fam == "PH":
            ttok = toks.pop(0) if toks and re.fullmatch(r"T\d+", toks[0]) else None
            if ttok is None:
                raise CodeError(f"both ends stepped: the right step length T follows M, e.g. {ex}")
            T = int(ttok[1:])
            if not (_P["step_f_min"] <= T <= _P["step_f_max_factor"] * P):
                raise CodeError(f"T{T} is outside 2 <= T <= P x 4 = {_P['step_f_max_factor'] * P:g} (p.{page})")
        s.F, s.P, s.T, s.ymax = F, P, T, row["Y"]
        if s.total_length > row["Y"]:
            raise CodeError(f"overall length (Y) = {s.total_length:g} mm exceeds the maximum {row['Y']:g} mm for D{D} (p.{page} table)")
        s.tapped = True; s.M = M
        s.taps.append(dict(M=M, face=-F, dir=1, depth=depth, label="left"))
        if fam == "PH":
            s.taps.append(dict(M=M, face=L + T, dir=-1, depth=depth, label="right"))
        s.md = md
    elif toks and re.fullmatch(r"M" + _MRX, toks[0]):
        raise CodeError(f"{typ} is the plain shaft; a thread needs the tapped type {typ}T (or C, Z, W)")
    # ---- alterations
    allowed = ALTS[fam]
    seen = set()
    i = 0
    sc = wsc = fc = wfc = sx = lfc = None
    ext = {}
    while i < len(toks):
        t = toks[i]; i += 1
        key = re.match(r"[A-Z]+", t).group(0)
        if key in ("A", "E", "X") or key not in ALTS["straight"] | ALTS["C"] | ALTS["PG"]:
            raise CodeError(f"unknown or unsupported alteration {t!r} (supported here: " + ", ".join(sorted(allowed)) + ")")
        if key not in allowed:
            raise CodeError(f"alteration {key} is not offered for {typ}{'T' if fam == 'T' else ''} (p.{page}); offered: " + ", ".join(sorted(allowed)))
        if key in seen:
            raise CodeError(f"alteration {key} given twice")
        if t == "LKC":
            s.lkc = True
        elif key == "SC" and re.fullmatch(r"SC\d+", t):
            sc = int(t[2:])
        elif key == "SX" and re.fullmatch(r"SX\d+", t):
            sx = int(t[2:])
        elif key == "WSC" and re.fullmatch(r"WSC\d+", t):
            wsc = int(t[3:])
            if i < len(toks) and re.fullmatch(r"X\d+", toks[i]):
                ext["X"] = int(toks[i][1:]); i += 1
            else:
                raise CodeError("WSC needs the distance between the two flats: WSC12-X8")
        elif key == "FC" and re.fullmatch(r"FC\d+", t):
            fc = int(t[2:])
            if i < len(toks) and re.fullmatch(r"[AE]\d+", toks[i]):
                ext["FC"] = (toks[i][0], int(toks[i][1:])); i += 1
            else:
                raise CodeError("FC needs its position from an end: FC10-A8 (from the left end) or FC10-E8 (from the right end)")
            if fam == "PG" and ext["FC"][0] != "E":
                raise CodeError("FC on a stepped shaft is given from the right end only: FC10-E8 (p.437)")
        elif key == "WFC" and re.fullmatch(r"WFC\d+", t):
            wfc = int(t[3:])
            if i + 1 < len(toks) and re.fullmatch(r"A\d+", toks[i]) and re.fullmatch(r"E\d+", toks[i + 1]):
                ext["WFC"] = (int(toks[i][1:]), int(toks[i + 1][1:])); i += 2
            else:
                raise CodeError("WFC needs both positions: WFC10-A8-E20")
        elif key == "LFC" and re.fullmatch(r"LFC\d+", t):
            lfc = int(t[3:])
            if i < len(toks) and re.fullmatch(r"A\d+", toks[i]):
                ext["LFC"] = int(toks[i][1:]); i += 1
            else:
                raise CodeError("LFC needs its distance from the step end: LFC10-A0 (p.437)")
        else:
            raise CodeError(f"unknown or unsupported alteration {t!r} (supported: " + ", ".join(sorted(allowed)) + ")")
        seen.add(key)
    # ---- required wrench flats
    if fam in ("C", "PG", "PH") and sc is None:
        raise CodeError(f"{typ}{D} needs its wrench flat position SC after the thread, e.g. ...-SC0 (p.{page} ordering example)")
    if fam == "Z" and sc is None and wsc is None:
        raise CodeError(f"{typ}{D} needs its wrench flat after N: SC<n> (one set) or WSC<n>-X<m> (two sets) (p.{page})")
    # ---- length checks
    if s.lkc:
        if fam == "PG" and D - s.P <= _P["lkc_min_d_minus_p"]:
            raise CodeError(f"LKC is not applicable when D - P <= 2 (D{D}, P{s.P:g}; p.437)")
        if abs(L * 10 - round(L * 10)) > 1e-9:
            raise CodeError(f"length {L:g} is not a multiple of 0.1 mm")
        s.length_tol = next(v for lim, v in LKC_TOL if L < lim)
    elif abs(L - round(L)) > 1e-9:
        raise CodeError(f"length {L:g} mm: lengths are in 1 mm steps; 0.1 mm steps need the LKC alteration")
    if not (lrange[0] <= L <= lrange[1]):
        raise CodeError(f"length {L:g} mm outside {lrange[0]}-{lrange[1]} mm for {typ}{'T' if fam == 'T' else ''}{D} (p.{page} table)")
    if fam in ("T", "C") and 2 * s.M > L:
        raise CodeError("thread depth exceeds the length")
    if "SC" in seen and "WSC" in seen:
        raise CodeError(f"SC cannot be combined with WSC (p.{page})")
    if "FC" in seen and "WFC" in seen:
        raise CodeError(f"FC cannot be combined with WFC (p.{page})")
    if ("SC" in seen or "WSC" in seen) and D < 6:
        raise CodeError("SC / WSC apply to D = 6 or more (p.432)")
    if sc is not None:
        W, l1 = WRENCH[D]
        if sc != 0 and sc < 1:
            raise CodeError("SC = 0 or SC >= 1")
        if sc + l1 > L:
            raise CodeError(f"SC + l1 = {sc + l1} exceeds L = {L:g} (p.{page}: SC + l1 <= L)")
        s.flats.append(dict(kind="sc", x0=sc, x1=sc + l1, axis="Y", across=W, r=D / 2))
    if sx is not None:
        W, l1 = WRENCH[D]
        if sc is None:
            raise CodeError("SX adds a second set of wrench flats and needs SC")
        if sc + sx + l1 * 2 >= L:
            raise CodeError(f"SC + SX + 2 x l1 = {sc + sx + 2 * l1} must be less than L = {L:g} (p.{page})")
        s.flats.append(dict(kind="sc", x0=sc + l1 + sx, x1=sc + 2 * l1 + sx, axis="Z", across=W, r=D / 2))
        s.notes.append("SX: the catalogue says the second set of flats is not coplanar with the first; drawn turned 90 degrees (angle not given)")
    if wsc is not None:
        W, l1 = WRENCH[D]; X = ext["X"]
        if wsc != 0 and wsc < 1 or X != 0 and X < 1:
            raise CodeError("WSC(X) = 0 or WSC(X) >= 1")
        if wsc + X + l1 * 2 >= L:
            raise CodeError(f"WSC + X + 2 x l1 = {wsc + X + 2 * l1} must be less than L = {L:g} (p.{page})")
        s.flats.append(dict(kind="sc", x0=wsc, x1=wsc + l1, axis="Y", across=W, r=D / 2))
        s.flats.append(dict(kind="sc", x0=wsc + l1 + X, x1=wsc + 2 * l1 + X, axis="Z", across=W, r=D / 2))
        s.notes.append("WSC: the catalogue says the two flats are not coplanar; the second is turned 90 degrees (angle not given)")
    H = flat_depth(D)
    def fc_len_ok(n, doubled):
        if D <= 30 and n > 5 * D:
            raise CodeError(f"FC / WFC = {n} exceeds 5 x D = {5 * D} (D <= 30, p.{page})")
        if D >= 35 and n < 3 * D:
            raise CodeError(f"FC / WFC = {n} below 3 x D = {3 * D} (D >= 35, as printed on p.{page})")
        if 1.5 * D < n and (2 * n if doubled else n) > L / 2:
            raise CodeError(f"FC / WFC = {n}: when 1.5 x D < FC, FC <= L/2 (WFC: 2 x WFC <= L/2) (p.{page})")
    if fc is not None:
        fc_len_ok(fc, False)
        side, a = ext["FC"]
        if a != 0 and a < 2:
            raise CodeError("A(E) = 0 or A(E) >= 2")
        x0 = a if side == "A" else L - a - fc
        if x0 < 0 or x0 + fc > L:
            raise CodeError("the flat does not fit in the length")
        s.flats.append(dict(kind="fc", x0=x0, x1=x0 + fc, axis="Y", depth=H, r=D / 2))
    if wfc is not None:
        fc_len_ok(wfc, True)
        a, e = ext["WFC"]
        for v in (a, e):
            if v != 0 and v < 2:
                raise CodeError("A(E) = 0 or A(E) >= 2")
        x0, x1 = a, L - e - wfc
        if x0 + wfc > x1:
            raise CodeError("the two flats overlap")
        s.flats.append(dict(kind="fc", x0=x0, x1=x0 + wfc, axis="Y", depth=H, r=D / 2))
        s.flats.append(dict(kind="fc", x0=x1, x1=x1 + wfc, axis="Z", depth=H, r=D / 2))
        s.notes.append("WFC: the catalogue says the two flats are not coplanar; the second is turned 90 degrees (angle not given)")
    if lfc is not None:
        a = ext["LFC"]
        if lfc < 1:
            raise CodeError("LFC must be at least 1 mm")
        if lfc + a > s.F:
            raise CodeError(f"LFC + A = {lfc + a} exceeds the step length F = {s.F:g} (p.437: LFC + A <= F)")
        if s.P - s.M < 1:
            raise CodeError(f"LFC needs P - M >= 1 (p.437), got P{s.P:g} M{s.M:g}")
        s.flats.append(dict(kind="lfc", x0=-s.F + a, x1=-s.F + a + lfc, axis="Y", depth=lfc_depth(s.P), r=s.P / 2))
    # machined parts spaced by more than 2 mm (p.432 note). The taps of one shaft are not held to it (their own limit is M x 2 + N x 2 <= L), and where
    # the ordering code itself carries the wrench flat (C, Z, PG, PH: the catalogue's own example is SC0) that flat may sit on the tapped end.
    base_flats = fam in ("C", "Z", "PG", "PH")
    spans = []
    for k, f in enumerate(s.flats):
        if f["kind"] == "lfc":
            continue
        is_base = base_flats and f["kind"] == "sc" and k == 0
        spans.append((f["x0"], f["x1"], "base" if is_base else "alt"))
    for t in s.taps:
        a0, a1 = sorted((t["face"], t["face"] + t["dir"] * t["depth"]))
        a0, a1 = max(a0, 0.0), min(a1, L)
        if a1 > a0:
            spans.append((a0, a1, "tap"))
    spans.sort()
    for (a0, a1, ka), (b0, b1, kb) in zip(spans, spans[1:]):
        if {ka, kb} in ({"tap"}, {"tap", "base"}):
            continue
        if b0 - a1 <= 2:
            raise CodeError(f"machined parts need more than 2 mm between them (p.{page} note)")
    return s

def commands(s: Shaft) -> list[dict]:
    cmds: list[dict] = []
    def add(c, **p): cmds.append({"command": c, "params": p})
    D, L = s.D, s.L
    add("component.create", name=s.code)
    add("solid.cylinder", diameter=D, height=L, base=[0, 0, 0], axis="X", operation="new", body_name=s.code, name="Shaft")
    if s.F:
        add("solid.cylinder", diameter=s.P, height=s.F, base=[-s.F, 0, 0], axis="X", operation="join", targets=[s.code], name="Left step")
    if s.T:
        add("solid.cylinder", diameter=s.P, height=s.T, base=[L, 0, 0], axis="X", operation="join", targets=[s.code], name="Right step")
    for t in s.taps:
        add("solid.hole", position=[t["face"], 0, 0], thread=f"M{t['M']:g}", depth=t["depth"], targets=[s.code], name=f"Tapped end ({t['label']})")
    for i, f in enumerate(s.flats):
        x0, x1 = f["x0"], f["x1"]
        r = f["r"]
        big = 2 * r + 2
        half = f["across"] / 2 if f["kind"] == "sc" else r - f["depth"]
        sides = (1, -1) if f["kind"] == "sc" else (1,)
        for sg in sides:
            lo = half if sg > 0 else -r - 1          # the slab removed lies from `lo` over a thickness of r + 1 - half
            w = r + 1 - half
            if f["axis"] == "Y":
                add("solid.box", length=x1 - x0, width=w, height=big, corner=[x0, lo, -big / 2],
                    operation="cut", targets=[s.code], name=f"Flat {i + 1}{'a' if sg > 0 else 'b'}")
            else:
                add("solid.box", length=x1 - x0, width=big, height=w, corner=[x0, -big / 2, lo],
                    operation="cut", targets=[s.code], name=f"Flat {i + 1}{'a' if sg > 0 else 'b'}")
    add("component.metadata.set", component=s.code, part_number=s.code, description=s.description,
        material=f"{s.material}; {s.hardness}" + ("" if s.surface == "-" else f"; {s.surface}"))
    add("document.metadata.set", values={"part_number": s.code, "description": s.description})
    return cmds

def parse_build(code: str):
    s = parse(code)
    return s, commands(s)
