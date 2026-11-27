"""HIWIN MGN miniature linear guide: ordering-code parser and catalogue dimensions.

Source (every number is in data/*.csv, each row citing sources.toml): HIWIN "Linear Guideways" catalogue, form G99TE24-2410 (c) 2024, MG Series chapter 2-4,
https://hiwin.com/wp-content/uploads/2026/08/HIWIN-Linear-Guideway-Catalog-1.pdf (printed page numbers; PDF page = printed + 3)
  - model-number grammar: section 2-4-10, catalogue p.78
  - rail standard/max lengths, pitch P, end distance Es, L = (n-1)*P + 2*E: section 2-4-17 (Table 2-4-15), p.85
  - block and rail dimensions: section 2-4-19 (p.88) "Dimensions for MGN/MGW Series", table (1) MGN-C / MGN-H
Public catalogue facts only; no vendor CAD used. The rail's ball-groove profile is NOT given in the
catalogue, so the generated rail is the catalogue envelope (WR x HR) with exact mounting holes; say so in
the part description.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, asdict

# Tables live in data/*.csv (every row cites sources.toml): block dimensions (H, H1, N, W, B, C, L1, L, M x depth) and the
# lube / nipple / L Max columns (LOOK), rail dimensions with the standard end distance and lengths, the bolt caps.
from pathlib import Path
from runtime.table import read_csv, num
DATA = Path(__file__).resolve().parent.parent / "data"
BLOCKS, LOOK, RAILS, CAP_SIZES = {}, {}, {}, {}
for _r in read_csv(DATA / "blocks.csv"):
    BLOCKS[(_r["size"], _r["block"])] = dict(H=num(_r["H"]), H1=num(_r["H1"]), N=num(_r["N"]), W=num(_r["W"]), B=num(_r["B"]),
                                             C=num(_r["C"]), L1=num(_r["L1"]), L=num(_r["L"]), M=_r["M"], M_depth=num(_r["M_depth"]))
    LOOK[(_r["size"], _r["block"])] = dict(Lmax=num(_r["Lmax"]), H2=num(_r["H2"]), Gn=num(_r["Gn"]), G=num(_r["G"]))
for _r in read_csv(DATA / "rails.csv"):
    RAILS[_r["size"]] = dict(WR=num(_r["WR"]), HR=num(_r["HR"]), D=num(_r["D"]), h=num(_r["h"]), d=num(_r["d"]), P=num(_r["P"]),
                             Es=num(_r["Es"]), max_std=num(_r["max_std"]), max_len=num(_r["max_len"]), bolt=_r["bolt"])
for _r in read_csv(DATA / "caps.csv"):
    CAP_SIZES[_r["size"]] = dict(D=num(_r["D"]), H=num(_r["H"]))

# Model number (non-interchangeable set), p.78 example: "MGN 12 C E 2 R1600 E Z1 P M II + SS/U/EL+RC/-O"
CODE = re.compile(
    r"^MGN\s*(?P<size>\d+)\s*(?P<block>[CH])\s*(?P<eblock>E)?\s*(?P<n_blocks>\d+)\s*R\s*(?P<length>\d+)"
    r"\s*(?P<erail>E)?\s*(?P<preload>ZF|Z0|Z1)?\s*(?P<precision>[CHP])?\s*(?P<material>M|HC|NC)?"
    r"\s*(?P<rails>I{1,4})?\s*(?:\+\s*(?P<options>.*))?$", re.I)

@dataclass
class MgnSet:
    code: str
    size: str
    block_type: str
    n_blocks: int
    rail_length: float
    holes: int
    end_distance: float
    preload: str | None
    precision: str | None
    material: str
    rails_per_axis: int
    options: str | None
    block: dict
    rail: dict
    notes: list

def holes_for(length: float, P: float, Es: float) -> tuple[int, float]:
    """L = (n-1)P + 2E (Eq. 2.4). Standard E when it fits exactly; otherwise the most holes with
    E_min <= E <= P/2 per section 2-4-17 (E <= P/2 recommended; E >= E_min to avoid a broken hole;
    we use Es as E_min here: conservative)."""
    n = int((length - 2 * Es) // P) + 1
    E = (length - (n - 1) * P) / 2
    while E > P / 2 + 1e-9 and E - P / 2 >= Es:
        n += 1
        E = (length - (n - 1) * P) / 2
    if E < Es - 1e-9:
        raise ValueError(f"rail length {length} leaves end distance {E:.2f} < {Es} mm")
    return n, E

def parse(code: str) -> MgnSet:
    m = CODE.match(code.strip())
    if not m:
        raise ValueError(f"not an MGN set code: {code!r}")
    size, block = m["size"], m["block"].upper()
    if (size, block) not in BLOCKS:
        raise ValueError(f"MGN{size}{block}: size not in this table (have 7, 9, 12, 15)")
    rail = RAILS[size]
    L = float(m["length"])
    if L > rail["max_len"]:
        raise ValueError(f"MGNR{size} max single length is {rail['max_len']} mm")
    n, E = holes_for(L, rail["P"], rail["Es"])
    notes = []
    if m["erail"]: notes.append("E: special rail (non-standard), modelled as standard")
    if m["eblock"]: notes.append("E: special block, modelled as standard")
    if L > rail["max_std"]: notes.append("longer than max standard length")
    return MgnSet(code=code, size=size, block_type=block, n_blocks=int(m["n_blocks"]), rail_length=L,
                  holes=n, end_distance=E, preload=(m["preload"] or "").upper() or None,
                  precision=(m["precision"] or "").upper() or None,
                  material={"M": "stainless", "HC": "carbon steel + hard chrome", "NC": "carbon steel + coating"}.get((m["material"] or "").upper(), "carbon steel"),
                  rails_per_axis=len(m["rails"] or "I"), options=m["options"],
                  block=BLOCKS[(size, block)], rail=rail, notes=notes)

if __name__ == "__main__":
    import json, sys
    for c in sys.argv[1:] or ["MGN12H2R500Z0C", "MGN 12 C E 2 R1600 E Z1 P M II + SS/U/EL+RC/-O", "MGN9C1R195ZFH"]:
        s = parse(c)
        print(json.dumps({k: v for k, v in asdict(s).items() if k not in ("block", "rail")}))
