"""HIWIN RG series (high rigidity roller type) linear guideway: ordering-code parser and catalogue dimensions.

Source (every number below): HIWIN "Linear Guideway" catalogue G99TE24-2410 (2024), RG Series, High Rigidity Roller Type,
https://hiwin.com/wp-content/uploads/2026/08/HIWIN-Linear-Guideway-Catalog-1.pdf   (id S17 in sources.toml; printed page numbers)
  - model number grammar: section 2-9-3, catalogue p.152-153; block and rail types: Tables 2-9-2 and 2-9-3, p.153-154
  - preload classes and stiffness: section 2-9-6, p.156-157 (Tables 2-9-13, 2-9-14)
  - dust-protection codes and the block length they give: section 2-9-8, p.160-161 (Table 2-9-22)
  - rail standard/maximum lengths, pitch P, end distance Es, L = (n-1)*P + 2*E: section 2-9-12, Table 2-9-29, p.165
  - block and rail dimensions: section 2-9-13 "Dimensions for RG series" tables (1) RGH-CA/HA p.166, (3) RGW-CC/HC p.168
Public catalogue facts only; no vendor CAD used. The roller tracks of rail and block and the flange outline of the RGW block are
not given as dimensions, so the generated parts are the catalogue envelopes (WR x HR rail; W x L1 x (H - H1) block with the rail
channel cut out, end caps and seals to the length L) with exact mounting holes.

Block naming: the second letter of a catalogue block name is the load class (C heavy, H super heavy), the third the mounting
(A from the top, C from the top or the bottom). The tables list RGH-CA / RGH-HA (square, mounting A) and RGW-CC / RGW-HC (flange,
mounting C). Every block drawing carries the legend "6-Mxl" (RGH) or "6-M" (RGW): six mounting holes. RGH: two columns C apart
times three rows (the two flank rows at B apart and one row on the rail axis). RGW: four flange holes (C x B) and two holes on the
rail axis C1 apart.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path
from runtime.table import read_csv, num

class CodeError(ValueError):
    """The ordering code is not valid; the message says why."""

class NotModelled(CodeError):
    """Valid HIWIN grammar that this generator does not build."""

SIZES = ("15", "20", "25", "30", "35", "45", "55", "65")
DATA = Path(__file__).resolve().parent.parent / "data"

def _cls(r, k):
    """(C, L1, L) of the heavy (ca / cc, load C) or super heavy (ha / hc, load H) block of one size; None when the row is absent."""
    L1 = num(r["L1_" + k])
    if L1 is None:
        return None
    return (num(r["C_" + k]) if "C_" + k in r else num(r["C"]), L1, num(r["L_" + k]))

_RGH = {_r["size"]: _r for _r in read_csv(DATA / "rgh.csv")}
_RGW = {_r["size"]: _r for _r in read_csv(DATA / "rgw.csv")}
RAILS = {}
for _r in read_csv(DATA / "rails.csv"):
    RAILS[_r["size"]] = dict(WR=num(_r["WR"]), HR=num(_r["HR"]), D=num(_r["D"]), h=num(_r["h"]), d=num(_r["d"]), P=num(_r["P"]),
                             Es=num(_r["Es"]), bolt=_r["bolt"])
_PARAMS = {_r["name"]: _r["value"] for _r in read_csv(DATA / "params.csv")}
MAX_LEN = num(_PARAMS["max_len"])      # Table 2-9-29
MIN_LEN = num(_PARAMS["min_len"])      # Table 2-9-2: rail length 100 ~ 4000
DUST = {_r["size_load"]: {k: num(_r[k]) for k in ("SS", "ZZ", "DD", "KK")} for _r in read_csv(DATA / "dust.csv")}   # Table 2-9-22

def block_dims(kind: str, size: str, load: str, mount: str) -> dict:
    """kind H (square) or W (flange); load C (heavy) or H (super heavy); mount A or C. Raises CodeError / NotModelled."""
    if kind in ("L", "S", "F"):
        raise NotModelled(f"RG{kind} ({ {'L': 'square, low', 'S': 'square, ultra low', 'F': 'flange, ultra low'}[kind] }) is valid HIWIN grammar; "
                          "its dimension table is not drawn here (RGH and RGW only)")
    if kind == "H" and mount != "A":
        raise CodeError(f"RGH is mounted from the top only: RGH{size}{load}A (the catalogue lists RGH-CA / RGH-HA)")
    if kind == "W" and mount != "C":
        raise CodeError(f"RGW has mounting code C (top or bottom): RGW{size}{load}C (the catalogue lists RGW-CC / RGW-HC)")
    row = (_RGH if kind == "H" else _RGW)[size]
    cl = _cls(row, ("ca" if kind == "H" else "cc") if load == "C" else ("ha" if kind == "H" else "hc"))
    if cl is None:
        raise CodeError(f"RG{kind}{size}{load}{mount} is not in the catalogue table (no row for it: the RG15 tables list the heavy load C block only)")
    C, L1, L = cl
    d = dict(H=num(row["H"]), H1=num(row["H1"]), N=num(row["N"]), W=num(row["W"]), B=num(row["B"]), B1=num(row["B1"]),
             C=C, L1=L1, L=L, n_holes=6)
    if kind == "H":
        d.update(M=row["M"], M_depth=num(row["l"]), hole="thread")        # Mxl (e.g. M4x8): depth l
        d.update(C1=None)                                                 # three rows at the same C: B apart and one on the rail axis
    else:
        d.update(M=row["M"], M_depth=num(row["T"]), hole="thread", C1=num(row["C1"]))   # table (3) M and T
    return d

# Model number, section 2-9-3: RG W 35 C C E 2 R 1640 E ZA P II + KK/E2+RC  (spaces optional). Rail mounting R: from the top, T: from the bottom.
SET = re.compile(
    r"^RG(?P<kind>[HWLSF])\s*(?P<size>\d{2})\s*(?P<load>[CH])\s*(?P<mount>[AC])\s*(?P<eblock>E)?\s*(?P<n>\d+)\s*"
    r"(?P<rm>[RT])\s*(?P<length>\d+(?:\.\d+)?)\s*(?P<erail>E)?\s*(?P<preload>Z0|ZA|ZB)?\s*(?P<prec>SP|UP|[CHP])?\s*"
    r"(?P<rails>I{1,4})?\s*(?:\+\s*(?P<opt>.*))?$", re.I)
RAIL = re.compile(
    r"^RGR\s*(?P<size>\d{2})\s*(?P<rm>[RT])\s*(?P<length>\d+(?:\.\d+)?)\s*(?P<erail>E)?\s*(?P<prec>SP|UP|[CHP])?\s*"
    r"(?:\+\s*(?P<opt>.*))?$", re.I)
BLOCK = re.compile(
    r"^RG(?P<kind>[HWLSF])\s*(?P<size>\d{2})\s*(?P<load>[CH])\s*(?P<mount>[AC])\s*(?P<eblock>E)?\s*(?P<preload>Z0|ZA|ZB)?\s*"
    r"(?P<prec>SP|UP|[CHP])?\s*(?:\+\s*(?P<opt>.*))?$", re.I)

@dataclass
class RgSet:
    code: str
    kind: str                 # "set", "rail" or "block"
    series: str               # "RGH" / "RGW" (block) or "RGR"
    size: str
    load: str | None
    mount: str | None         # block mounting A/C
    rail_mount: str | None    # R from the top (counterbore); bottom mounting T is refused
    n_blocks: int
    rail_length: float
    holes: int
    end_distance: float
    preload: str | None
    precision: str | None
    dust: str | None          # None (standard end seal + bottom seal), "ZZ", "DD" or "KK"
    options: str | None
    block: dict | None
    rail: dict | None
    notes: list
    material: str = "carbon steel"      # the RG chapter prints no stainless option

def end_range(P: float, Es: float) -> tuple[float, float]:
    """(smallest, largest) end distance E of a NON-standard rail length. The catalogue text (p.165) says only "specify the E-value to
    be no greater than 1/2 the pitch (P)", so the largest is P/2. It prints no smallest value; as in the HG and EG generators the
    standard distance Es is used as the smallest, except where Es > P/2 (RGR15 / 20 / 25: Es = 20, P/2 = 15), where P/2 is used.
    A standard length (Table 2-9-29: 160, 220, 340 ... ) has E = Es exactly and is accepted even when Es > P/2."""
    return min(Es, P / 2), P / 2

def holes_for(length: float, P: float, Es: float) -> tuple[int, float]:
    """L = (n-1)P + 2E (p.165): the most holes whose end distance E is the standard Es or lies within end_range."""
    lo, hi = end_range(P, Es)
    n = int((length - 2 * lo + 1e-9) // P) + 1
    E = (length - (n - 1) * P) / 2
    if n < 2 or E < lo - 1e-9:
        raise CodeError(f"rail length {length:g} leaves end distance {E:.2f} mm, below the smallest end distance {lo:g} mm (p.165)")
    if abs(E - Es) > 1e-9 and E > hi + 1e-9:
        raise CodeError(f"rail length {length:g} leaves end distance {E:.2f} mm, above P/2 = {hi:g} mm and not the standard "
                        f"Es = {Es:g} mm (an unstable rail end, p.165)")
    return n, E

def _size(size):
    if size not in RAILS:
        raise CodeError(f"RG size {size}: catalogue sizes are {', '.join(SIZES)}")

def _rail_mount(rm):
    if rm.upper() == "T":
        raise NotModelled("RGR rail mounted from the bottom (T) is valid HIWIN grammar, but the catalogue prints no tapped-hole "
                          "dimensions for it (the rail columns on p.166-170 are the top-mounted R rail), so it is not drawn")
    return "R"

def _rail_checks(size, length):
    _size(size)
    if length > MAX_LEN:
        raise CodeError(f"rail length {length:g} mm above the maximum {MAX_LEN:g} mm (Table 2-9-29)")
    if length < MIN_LEN:
        raise CodeError(f"rail length {length:g} mm below the catalogue minimum {MIN_LEN:g} mm (Table 2-9-2)")

def _options(opt):
    """Options after '+': ('ZZ' | 'DD' | 'KK' | None, rest). The dust-protection code gives the block length of Table 2-9-22; the
    others (E2 self-lubricant, RC reinforced cap, ...) are parsed and not drawn."""
    if not opt:
        return None, opt
    m = re.search(r"(?<![A-Z0-9])(ZZ|DD|KK)(?![A-Z0-9])", opt.upper())
    return (m.group(1) if m else None), opt

def _block(m, size):
    """Block dimensions for a parsed set / block code, with the preload and accuracy validity of the model number."""
    kind, load, mount = m["kind"].upper(), m["load"].upper(), m["mount"].upper()
    b = block_dims(kind, size, load, mount)
    dust, _ = _options(m["opt"])
    if dust:
        b = dict(b, L=DUST[f"{size}{load}"][dust])
    return b, dust

def _precision(prec, allowed, what):
    p = (prec or "").upper() or None
    if p and p not in allowed:
        raise CodeError(f"accuracy class {p} is not offered for {what}: the RG series has {', '.join(allowed)} there (model number, p.152-153)")
    return p

def parse(code: str) -> RgSet:
    c = code.strip()
    m = RAIL.match(c)
    if m:
        size = m["size"]; length = float(m["length"]); rm = _rail_mount(m["rm"])
        _size(size)
        _rail_checks(size, length)
        prec = _precision(m["prec"], ("H", "P"), "a rail ordered alone (interchangeable rail)")
        r = RAILS[size]
        n, E = holes_for(length, r["P"], r["Es"])
        notes = ["E: special rail (non-standard), modelled as standard"] if m["erail"] else []
        return RgSet(code=code, kind="rail", series="RGR", size=size, load=None, mount=None, rail_mount=rm, n_blocks=0,
                     rail_length=length, holes=n, end_distance=E, preload=None, precision=prec, dust=None,
                     options=m["opt"], block=None, rail=r, notes=notes)
    m = SET.match(c)
    if m:
        size = m["size"]
        _size(size)
        b, dust = _block(m, size)
        length = float(m["length"]); rm = _rail_mount(m["rm"])
        _rail_checks(size, length)
        prec = _precision(m["prec"], ("H", "P", "SP", "UP"), "a rail with blocks (non-interchangeable set)")
        r = RAILS[size]
        n, E = holes_for(length, r["P"], r["Es"])
        nb = int(m["n"])
        if nb < 1:
            raise CodeError("a set has at least one block (the digit before R is the number of blocks per rail)")
        if nb * b["L"] + (nb - 1) * BLOCK_GAP > length:
            raise CodeError(f"{nb} blocks of {b['L']:g} mm with {BLOCK_GAP:g} mm gaps do not fit on a {length:g} mm rail")
        notes = []
        if m["erail"]: notes.append("E: special rail (non-standard), modelled as standard")
        if m["eblock"]: notes.append("E: special block, modelled as standard")
        return RgSet(code=code, kind="set", series="RG" + m["kind"].upper(), size=size, load=m["load"].upper(),
                     mount=m["mount"].upper(), rail_mount=rm, n_blocks=nb, rail_length=length, holes=n, end_distance=E,
                     preload=(m["preload"] or "").upper() or None, precision=prec, dust=dust,
                     options=m["opt"], block=b, rail=r, notes=notes)
    m = BLOCK.match(c)
    if m:
        size = m["size"]
        _size(size)
        b, dust = _block(m, size)
        pre = (m["preload"] or "").upper() or None
        if pre == "ZB":
            raise CodeError("the interchangeable block form has preload Z0 or ZA only (model number, p.152); ZB belongs to a set "
                            "(non-interchangeable)")
        prec = _precision(m["prec"], ("H", "P"), "an interchangeable block")
        notes = ["E: special block, modelled as standard"] if m["eblock"] else []
        return RgSet(code=code, kind="block", series="RG" + m["kind"].upper(), size=size, load=m["load"].upper(),
                     mount=m["mount"].upper(), rail_mount=None, n_blocks=1, rail_length=0.0, holes=0, end_distance=0.0,
                     preload=pre, precision=prec, dust=dust, options=m["opt"], block=b, rail=RAILS[size], notes=notes)
    raise CodeError(f"{code!r}: expected a set RG<H|W><size><C|H><A|C><n>R<length>[Z0|ZA|ZB][H|P|SP|UP], e.g. RGH20CA2R1000ZAH, "
                    "a rail RGR<size>R<length>, e.g. RGR25R1240, or a block RGW25CC")

BLOCK_GAP = 10.0    # mm between neighbouring blocks on one rail: an illustration choice, not a catalogue value
