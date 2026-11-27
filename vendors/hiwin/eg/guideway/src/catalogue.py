"""HIWIN EG series (low profile ball type) linear guideway: ordering-code parser and catalogue dimensions.

Source (every number below): HIWIN "Linear Guideway" catalogue G99TE24-2410 (2024), EG Series, Low Profile Ball Type,
https://hiwin.com/wp-content/uploads/2026/08/HIWIN-Linear-Guideway-Catalog-1.pdf   (id S15 in sources.toml; printed page numbers)
  - model number grammar: section 2-2-3, catalogue p.44-45; block and rail types: Tables 2-2-1 and 2-2-2, p.46
  - preload classes: section 2-2-6, p.49 (Tables 2-2-8, 2-2-9: ZB stiffness is printed for every size, EG15 included)
  - rail standard/maximum lengths, pitch P, end distance Es, L = (n-1)*P + 2*E: section 2-2-12, Table 2-2-22, p.56
  - block and rail dimensions: section 2-2-13 "Dimensions for HIWIN EG Series" tables (1) EGH-SA/CA, (2) EGW-SA/CA,
    (3) EGW-SB/CB, p.57-59
Public catalogue facts only; no vendor CAD used. The ball-groove profile of rail and block and the flange outline of the
EGW block are not given as dimensions, so the generated parts are the catalogue envelopes (WR x HR rail; W x L1 x (H - H1)
block with the rail channel cut out, end caps and seals to the length L) with exact mounting holes.

Block naming: the second letter of a catalogue block name is the load class (S medium load = short block, C heavy load = long
block), the third is the mounting (A from the top, B from the bottom, i.e. through holes). The short S blocks have two mounting
holes (2-MxL / 2-M in the drawings, C printed as "-"), the long C blocks four (4-MxL / 4-M).
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

SIZES = ("15", "20", "25", "30", "35")
DATA = Path(__file__).resolve().parent.parent / "data"

def _cls(r, k):
    """(C, L1, L, K1) of the short (sa) or long (ca) block of one size."""
    if k == "sa":
        return (None, num(r["L1_sa"]), num(r["L_sa"]))
    return (num(r["C_ca"]), num(r["L1_ca"]), num(r["L_ca"]))

_EGH = {_r["size"]: _r for _r in read_csv(DATA / "egh.csv")}
_EGW = {_r["size"]: _r for _r in read_csv(DATA / "egw.csv")}
RAILS = {}
for _r in read_csv(DATA / "rails.csv"):
    RAILS[_r["size"]] = dict(WR=num(_r["WR"]), HR=num(_r["HR"]), D=num(_r["D"]), h=num(_r["h"]), d=num(_r["d"]), P=num(_r["P"]),
                             Es=num(_r["Es"]), bolt=_r["bolt"])
_PARAMS = {_r["name"]: _r["value"] for _r in read_csv(DATA / "params.csv")}
MAX_LEN = num(_PARAMS["max_len"])
MAX_LEN_STAINLESS = num(_PARAMS["max_len_stainless"])     # Table 2-2-22 note 4: EGR15 stainless
MIN_LEN = num(_PARAMS["min_len"])                        # Table 2-2-1: rail length 100 ~ 4000
STAINLESS_OK = set(_PARAMS["stainless_sizes"].split("|"))  # model number note 4: EG15C

def block_dims(kind: str, size: str, load: str, mount: str) -> dict:
    """kind H (square) or W (flange); load S (medium, short block) or C (heavy, long block); mount A or B. Raises CodeError."""
    if kind == "H" and mount != "A":
        raise CodeError(f"EGH is mounted from the top only: EGH{size}{load}A (the catalogue lists EGH-SA / EGH-CA)")
    row = (_EGH if kind == "H" else _EGW)[size]
    C, L1, L = _cls(row, "sa" if load == "S" else "ca")
    d = dict(H=num(row["H"]), H1=num(row["H1"]), N=num(row["N"]), W=num(row["W"]), B=num(row["B"]), B1=num(row["B1"]),
             C=C, L1=L1, L=L, n_holes=2 if load == "S" else 4)
    if kind == "H":
        d.update(M=row["M"], M_depth=num(row["l"]), hole="thread")        # Mxl (e.g. M4x6): depth l
    elif mount == "B":
        d.update(M=f"O{num(row['hole_d_b']):g}", M_depth=None, hole="through", hole_d=num(row["hole_d_b"]))
    else:
        d.update(M=row["M"], M_depth=num(row["T"]), hole="thread")        # table (2) M and T (thread length)
    return d

# Model number, section 2-2-3: EG W 25 C A E 2 R 1600 E ZA P M II + DD/E2+RC  (spaces optional). Rail mounting R / U: from the top, T: from the bottom.
SET = re.compile(
    r"^EG(?P<kind>[HW])\s*(?P<size>\d{2})\s*(?P<load>[CS])\s*(?P<mount>[AB])\s*(?P<eblock>E)?\s*(?P<n>\d+)\s*"
    r"(?P<rm>[RUT])\s*(?P<length>\d+(?:\.\d+)?)\s*(?P<erail>E)?\s*(?P<preload>Z0|ZA|ZB)?\s*(?P<prec>SP|UP|[CHP])?\s*"
    r"(?P<mat>M)?\s*(?P<rails>I{1,4})?\s*(?:\+\s*(?P<opt>.*))?$", re.I)
RAIL = re.compile(
    r"^EGR\s*(?P<size>\d{2})\s*(?P<rm>[RUT])\s*(?P<length>\d+(?:\.\d+)?)\s*(?P<erail>E)?\s*(?P<prec>SP|UP|[CHP])?\s*"
    r"(?P<mat>M)?\s*(?:\+\s*(?P<opt>.*))?$", re.I)
BLOCK = re.compile(
    r"^EG(?P<kind>[HW])\s*(?P<size>\d{2})\s*(?P<load>[CS])\s*(?P<mount>[AB])\s*(?P<eblock>E)?\s*(?P<preload>Z0|ZA)?\s*"
    r"(?P<prec>[CHP])?\s*(?P<mat>M)?\s*(?:\+\s*(?P<opt>.*))?$", re.I)

@dataclass
class EgSet:
    code: str
    kind: str                 # "set", "rail" or "block"
    series: str               # "EGH" / "EGW" (block) or "EGR"
    size: str
    load: str | None
    mount: str | None         # block mounting A/B
    rail_mount: str | None    # R from the top (counterbore; U is the same top mounting); bottom mounting T is refused
    n_blocks: int
    rail_length: float
    holes: int
    end_distance: float
    preload: str | None
    precision: str | None
    material: str
    options: str | None
    block: dict | None
    rail: dict | None
    notes: list

def holes_for(length: float, P: float, Es: float) -> tuple[int, float]:
    """L = (n-1)P + 2E (Eq. 2.2, p.56): the most holes with Es <= E <= P/2 (the catalogue says E no greater than P/2; Es is
    used as the smallest end distance, as in the HG generator)."""
    n = int((length - 2 * Es) // P) + 1
    E = (length - (n - 1) * P) / 2
    while E > P / 2 + 1e-9 and E - P / 2 >= Es:
        n += 1
        E = (length - (n - 1) * P) / 2
    if E < Es - 1e-9:
        raise CodeError(f"rail length {length:g} leaves end distance {E:.2f} mm, below the standard {Es:g} mm")
    if E > P / 2 + 1e-9:
        raise CodeError(f"rail length {length:g} leaves end distance {E:.2f} mm, above P/2 = {P / 2:g} mm (unstable rail end, p.56)")
    return n, E

def _size(size):
    if size not in RAILS:
        raise CodeError(f"EG size {size}: catalogue sizes are {', '.join(SIZES)}")

def _rail_mount(rm):
    if rm.upper() == "T":
        raise NotModelled("EGR rail mounted from the bottom (T) is valid HIWIN grammar, but the catalogue prints no tapped-hole "
                          "dimensions for it (tables (1)-(3) on p.57-59 are the top-mounted R rail), so it is not drawn")
    return "R"

def _rail_checks(size, length, stainless):
    _size(size)
    lim = MAX_LEN_STAINLESS if stainless else MAX_LEN
    if length > lim:
        raise CodeError(f"rail length {length:g} mm above the maximum {lim:g} mm" + (" for stainless EGR15 (Table 2-2-22 note 4)" if stainless else ""))
    r = RAILS[size]
    if length < MIN_LEN:
        raise CodeError(f"rail length {length:g} mm below the catalogue minimum {MIN_LEN:g} mm (Table 2-2-1)")
    if length < 2 * r["Es"]:
        raise CodeError(f"rail length {length:g} mm below 2 x Es = {2 * r['Es']:g} mm")

def _material(m, size, load):
    if not m:
        return "carbon steel"
    if size not in STAINLESS_OK or (load not in (None, "C")):
        raise CodeError("stainless steel (M) exists for EG15C only (model number note 4, p.45)")
    return "stainless steel"

def _options(opt):
    """Options after '+': the dust-protection codes ZZ, DD and KK change the block length L (p.53) and are not drawn; the
    others (E2, SE, RC, ...) are parsed and not drawn either (appearance of the block ends / the rail cap)."""
    if opt and re.search(r"(?<![A-Z0-9])(ZZ|DD|KK)(?![A-Z0-9])", opt.upper()):
        raise NotModelled("dust-protection codes ZZ, DD and KK are valid HIWIN grammar; they change the overall block length (p.53), "
                          "which is not drawn: leave the option out for the standard end seal and bottom seal length")
    return opt

def _preload(pre, size):
    pre = (pre or "").upper() or None
    return pre

def parse(code: str) -> EgSet:
    c = code.strip()
    m = RAIL.match(c)
    if m:
        size = m["size"]; length = float(m["length"]); rm = _rail_mount(m["rm"])
        _size(size)
        mat = _material(m["mat"], size, None)
        _rail_checks(size, length, mat == "stainless steel")
        r = RAILS[size]
        n, E = holes_for(length, r["P"], r["Es"])
        notes = ["E: special rail (non-standard), modelled as standard"] if m["erail"] else []
        return EgSet(code=code, kind="rail", series="EGR", size=size, load=None, mount=None, rail_mount=rm, n_blocks=0,
                     rail_length=length, holes=n, end_distance=E, preload=None, precision=(m["prec"] or "").upper() or None,
                     material=mat, options=_options(m["opt"]), block=None, rail=r, notes=notes)
    m = SET.match(c)
    if m:
        size = m["size"]
        _size(size)
        b = block_dims(m["kind"].upper(), size, m["load"].upper(), m["mount"].upper())
        length = float(m["length"]); rm = _rail_mount(m["rm"])
        mat = _material(m["mat"], size, m["load"].upper())
        _rail_checks(size, length, mat == "stainless steel")
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
        return EgSet(code=code, kind="set", series="EG" + m["kind"].upper(), size=size, load=m["load"].upper(),
                     mount=m["mount"].upper(), rail_mount=rm, n_blocks=nb, rail_length=length, holes=n, end_distance=E,
                     preload=_preload(m["preload"], size), precision=(m["prec"] or "").upper() or None,
                     material=mat, options=_options(m["opt"]), block=b, rail=r, notes=notes)
    m = BLOCK.match(c)
    if m:
        size = m["size"]
        _size(size)
        b = block_dims(m["kind"].upper(), size, m["load"].upper(), m["mount"].upper())
        mat = _material(m["mat"], size, m["load"].upper())
        notes = ["E: special block, modelled as standard"] if m["eblock"] else []
        return EgSet(code=code, kind="block", series="EG" + m["kind"].upper(), size=size, load=m["load"].upper(),
                     mount=m["mount"].upper(), rail_mount=None, n_blocks=1, rail_length=0.0, holes=0, end_distance=0.0,
                     preload=_preload(m["preload"], size), precision=(m["prec"] or "").upper() or None,
                     material=mat, options=_options(m["opt"]), block=b, rail=RAILS[size], notes=notes)
    raise CodeError(f"{code!r}: expected a set EG<H|W><size><C|S><A|B><n>R<length>[Z0|ZA|ZB][C|H|P], e.g. EGH20CA2R1000ZAH, "
                    "a rail EGR<size>R<length>, e.g. EGR25R1600, or a block EGW25CA")

BLOCK_GAP = 10.0    # mm between neighbouring blocks on one rail: an illustration choice, not a catalogue value
