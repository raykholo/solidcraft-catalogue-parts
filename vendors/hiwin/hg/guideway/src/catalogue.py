"""HIWIN HG series (heavy load ball type) linear guideway: ordering-code parser and catalogue dimensions.

Source (every number below): HIWIN "Linear Guideway" catalogue G99TE24-2410 (2024), HG Series, Heavy Load Ball Type,
https://hiwin.com/wp-content/uploads/2026/08/HIWIN-Linear-Guideway-Catalog-1.pdf   (id S7 in sources.toml; printed page numbers)
  - model number grammar: section 2-1-3, catalogue p.22-23
  - rail standard/maximum lengths, pitch P, end distance Es, L = (n-1)*P + 2*E: section 2-1-12, Table 2-1-27, p.37
  - block and rail dimensions: section 2-1-13 "Dimensions for HIWIN HG Series" tables (1) HGH-CA/HA, (3) HGW-CA/HA,
    (4) HGW-CB/HB, (5) HGW-CC/HC, (6) HGR-T, p.38-43
Public catalogue facts only; no vendor CAD used. The ball-groove profile of rail and block and the flange outline of the
HGW block are not given as dimensions, so the generated parts are the catalogue envelopes (WR x HR rail; W x L x (H - H1)
block with the rail channel cut out) with exact mounting holes; the part description says so.
"""
from __future__ import annotations
import re
from dataclasses import dataclass

class CodeError(ValueError):
    """The ordering code is not valid; the message says why."""

class NotModelled(CodeError):
    """Valid HIWIN grammar that this prototype does not build."""

SIZES = ("15", "20", "25", "30", "35", "45", "55", "65")

# Tables live in data/*.csv (every row cites sources.toml): block dimensions per size and load class for HGH (table (1)) and HGW
# (tables (3)-(5)), rail dimensions (tables (1), (6), Table 2-1-27) and the length limits (params.csv).
from pathlib import Path
from runtime.table import read_csv, num
DATA = Path(__file__).resolve().parent.parent / "data"

def _cls(r, k):
    c = num(r["C_" + k])
    return None if c is None else (c, num(r["L1_" + k]), num(r["L_" + k]))

_HGH = {}   # H, H1, N, W, B, B1, (C, L1, L) CA, (C, L1, L) HA, thread, depth l
for _r in read_csv(DATA / "hgh.csv"):
    _HGH[_r["size"]] = (num(_r["H"]), num(_r["H1"]), num(_r["N"]), num(_r["W"]), num(_r["B"]), num(_r["B1"]),
                        _cls(_r, "ca"), _cls(_r, "ha"), _r["M"], num(_r["l"]))
_HGW = {}   # H, H1, N, W, B, B1, CA, HA, thread M, T (thread length), CB through-hole diameter
for _r in read_csv(DATA / "hgw.csv"):
    _HGW[_r["size"]] = (num(_r["H"]), num(_r["H1"]), num(_r["N"]), num(_r["W"]), num(_r["B"]), num(_r["B1"]),
                        _cls(_r, "ca"), _cls(_r, "ha"), _r["M"], num(_r["T"]), num(_r["hole_d_cb"]))
RAILS = {}
for _r in read_csv(DATA / "rails.csv"):
    RAILS[_r["size"]] = dict(WR=num(_r["WR"]), HR=num(_r["HR"]), D=num(_r["D"]), h=num(_r["h"]), d=num(_r["d"]), P=num(_r["P"]),
                             Es=num(_r["Es"]), bolt=_r["bolt"], S=_r["S"], hT=num(_r["hT"]))
_PARAMS = {_r["name"]: _r["value"] for _r in read_csv(DATA / "params.csv")}
MAX_LEN = num(_PARAMS["max_len"])
MAX_LEN_STAINLESS = num(_PARAMS["max_len_stainless"])      # Table 2-1-27 note 4: HGR15/20/25 stainless
STAINLESS_OK = set(_PARAMS["stainless_sizes"].split("|"))   # model number note 5: HG15C, HG20C, HG25C

def block_dims(kind: str, size: str, load: str, mount: str) -> dict:
    """kind H or W; load C or H; mount A, B, C. Raises CodeError / NotModelled."""
    if kind == "L":
        raise NotModelled("HGL (low square type) is valid HIWIN grammar; its table (2) is not drawn here")
    if kind == "H":
        if mount != "A":
            raise CodeError(f"HGH is mounted from the top only: HGH{size}{load}A (the catalogue lists HGH-CA / HGH-HA)")
        H, H1, N, W, B, B1, ca, ha, M, l = _HGH[size]
        cl = ca if load == "C" else ha
        if cl is None:
            raise CodeError(f"HGH{size}{load}A is not in the catalogue table (HG15 has the heavy load C block only)")
        C, L1, L = cl
        return dict(H=H, H1=H1, N=N, W=W, B=B, B1=B1, C=C, L1=L1, L=L, M=M, M_depth=l, hole="thread")
    H, H1, N, W, B, B1, ca, ha, M, T, dB = _HGW[size]
    cl = ca if load == "C" else ha
    if cl is None:
        raise CodeError(f"HGW{size}{load}{mount} is not in the catalogue table (HG15 has the heavy load C block only)")
    C, L1, L = cl
    d = dict(H=H, H1=H1, N=N, W=W, B=B, B1=B1, C=C, L1=L1, L=L)
    if mount == "B":
        d.update(M=f"O{dB:g}", M_depth=None, hole="through", hole_d=dB)
    else:
        d.update(M=M, M_depth=T, hole="thread")
    return d

# Model number, section 2-1-3: HG W 25 C A E 2 R 1600 E ZA P M II + DD/E2+RC  (spaces optional).
SET = re.compile(
    r"^HG(?P<kind>[HWL])\s*(?P<size>\d{2})\s*(?P<load>[CH])\s*(?P<mount>[ABC])\s*(?P<eblock>E)?\s*(?P<n>\d+)\s*"
    r"(?P<rm>[RT])\s*(?P<length>\d+(?:\.\d+)?)\s*(?P<erail>E)?\s*(?P<preload>Z0|ZA|ZB)?\s*(?P<prec>SP|UP|[CHP])?\s*"
    r"(?P<mat>M)?\s*(?P<rails>I{1,4})?\s*(?:\+\s*(?P<opt>.*))?$", re.I)
RAIL = re.compile(
    r"^HGR\s*(?P<size>\d{2})\s*(?P<rm>[RT])\s*(?P<length>\d+(?:\.\d+)?)\s*(?P<erail>E)?\s*(?P<prec>SP|UP|[CHP])?\s*"
    r"(?P<mat>M)?\s*(?:\+\s*(?P<opt>.*))?$", re.I)
BLOCK = re.compile(
    r"^HG(?P<kind>[HWL])\s*(?P<size>\d{2})\s*(?P<load>[CH])\s*(?P<mount>[ABC])\s*(?P<eblock>E)?\s*(?P<preload>Z0|ZA)?\s*"
    r"(?P<prec>[CHP])?\s*(?P<mat>M)?\s*(?:\+\s*(?P<opt>.*))?$", re.I)

@dataclass
class HgSet:
    code: str
    kind: str                 # "set", "rail" or "block"
    series: str               # "HGH" / "HGW" (block) or "HGR"
    size: str
    load: str | None
    mount: str | None         # block mounting A/B/C
    rail_mount: str | None    # R from the top (counterbore), T from the bottom (thread)
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
    """L = (n-1)P + 2E (Eq. 2.1, p.37): standard E when it fits exactly, otherwise the most holes with Es <= E <= P/2
    (the catalogue recommends E no greater than P/2; Es is used as the smallest end distance)."""
    n = int((length - 2 * Es) // P) + 1
    E = (length - (n - 1) * P) / 2
    while E > P / 2 + 1e-9 and E - P / 2 >= Es:
        n += 1
        E = (length - (n - 1) * P) / 2
    if E < Es - 1e-9:
        raise CodeError(f"rail length {length:g} leaves end distance {E:.2f} mm, below the standard {Es:g} mm")
    if E > P / 2 + 1e-9:
        raise CodeError(f"rail length {length:g} leaves end distance {E:.2f} mm, above P/2 = {P / 2:g} mm (unstable rail end, p.37)")
    return n, E

def _rail_checks(size, length, stainless):
    if size not in RAILS:
        raise CodeError(f"HG size {size}: catalogue sizes are {', '.join(SIZES)}")
    lim = MAX_LEN_STAINLESS if stainless else MAX_LEN
    if length > lim:
        raise CodeError(f"rail length {length:g} mm above the maximum {lim:g} mm" + (" for stainless HGR15/20/25 (Table 2-1-27 note 4)" if stainless else ""))
    r = RAILS[size]
    if length < 2 * r["Es"]:
        raise CodeError(f"rail length {length:g} mm below 2 x Es = {2 * r['Es']:g} mm")

def _material(m, size, load):
    if not m:
        return "carbon steel"
    if size not in STAINLESS_OK or (load not in (None, "C")):
        raise CodeError("stainless steel (M) exists for HG15C, HG20C and HG25C only (model number note 5, p.23)")
    return "stainless steel"

def parse(code: str) -> HgSet:
    c = code.strip()
    m = RAIL.match(c)
    if m:
        size = m["size"]; length = float(m["length"]); rm = m["rm"].upper()
        mat = _material(m["mat"], size, None)
        _rail_checks(size, length, mat == "stainless steel")
        r = RAILS[size]
        n, E = holes_for(length, r["P"], r["Es"])
        notes = ["E: special rail (non-standard), modelled as standard"] if m["erail"] else []
        return HgSet(code=code, kind="rail", series="HGR", size=size, load=None, mount=None, rail_mount=rm, n_blocks=0,
                     rail_length=length, holes=n, end_distance=E, preload=None, precision=(m["prec"] or "").upper() or None,
                     material=mat, options=m["opt"], block=None, rail=r, notes=notes)
    m = SET.match(c)
    if m:
        size = m["size"]
        if size not in RAILS:
            raise CodeError(f"HG size {size}: catalogue sizes are {', '.join(SIZES)}")
        b = block_dims(m["kind"].upper(), size, m["load"].upper(), m["mount"].upper())
        length = float(m["length"]); rm = m["rm"].upper()
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
        return HgSet(code=code, kind="set", series="HG" + m["kind"].upper(), size=size, load=m["load"].upper(),
                     mount=m["mount"].upper(), rail_mount=rm, n_blocks=nb, rail_length=length, holes=n, end_distance=E,
                     preload=(m["preload"] or "").upper() or None, precision=(m["prec"] or "").upper() or None,
                     material=mat, options=m["opt"], block=b, rail=r, notes=notes)
    m = BLOCK.match(c)
    if m:
        size = m["size"]
        if size not in RAILS:
            raise CodeError(f"HG size {size}: catalogue sizes are {', '.join(SIZES)}")
        b = block_dims(m["kind"].upper(), size, m["load"].upper(), m["mount"].upper())
        mat = _material(m["mat"], size, m["load"].upper())
        notes = ["E: special block, modelled as standard"] if m["eblock"] else []
        return HgSet(code=code, kind="block", series="HG" + m["kind"].upper(), size=size, load=m["load"].upper(),
                     mount=m["mount"].upper(), rail_mount=None, n_blocks=1, rail_length=0.0, holes=0, end_distance=0.0,
                     preload=(m["preload"] or "").upper() or None, precision=(m["prec"] or "").upper() or None,
                     material=mat, options=m["opt"], block=b, rail=RAILS[size], notes=notes)
    raise CodeError(f"{code!r}: expected a set HG<H|W><size><C|H><A|B|C><n>R<length>[Z0|ZA|ZB][C|H|P], e.g. HGH20CA2R1000ZAH, "
                    "a rail HGR<size>R<length>, e.g. HGR25R1600, or a block HGW25CC")

BLOCK_GAP = 10.0    # mm between neighbouring blocks on one rail: an illustration choice, not a catalogue value
