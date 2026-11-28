#!/usr/bin/env python3
"""Writes the generator package files that come from ../data/*.csv: mg-rail-set/tables/*.csv and mg-rail-set/generator.toml.
(The model mg-rail-set/mg-rail-set.sc is built by run_template.sh from build_template.py.)"""
import csv, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
HERE = Path(__file__).resolve().parent; DATA = HERE.parent / "data"; PKG = HERE / "mg-rail-set"
(PKG / "tables").mkdir(parents=True, exist_ok=True)
shutil.copy(DATA / "rails.csv", PKG / "tables/rails.csv")
shutil.copy(DATA / "caps.csv", PKG / "tables/caps.csv")
blocks = list(csv.DictReader((DATA / "blocks.csv").open()))
with (PKG / "tables/blocks.csv").open("w", newline="") as f:      # first column is the key: "<block>-<size>", the configuration row's name
    cols = ["key"] + list(blocks[0].keys())
    w = csv.DictWriter(f, cols, lineterminator="\n"); w.writeheader()
    for b in blocks: w.writerow({"key": f"{b['block']}-{b['size']}", **b})
head = '''format = "solidcraft-generator/2"
id = "mg-rail-set"
name = "HIWIN MG miniature linear guide: rail with blocks"
license = "CC0-1.0"
model = "mg-rail-set.sc"

# Ordering code, HIWIN MG catalogue G99TE24-2410 section 2-4-10 (p.78): MGN 12 C E 2 R1600 E Z1 P M II + SS/U/EL+RC/-O
# Size and length are plain integers here and checked in generator.rhai, so that the refusals carry the catalogue's wording.
[parameters]
size   = { type = "int", min = 7, max = 15 }
block  = { type = "choice", values = ["C", "H"], labels = { C = "standard", H = "heavy" } }
blocks = { type = "int", min = 1, max = 4 }
length = { type = "int", min = 40, max = 2000, unit = "mm" }
caps   = { type = "int", min = 0, max = 1, default = 0 }   # option, not in the code: plastic bolt caps (MGN12, MGN15)

[[template]]
pattern = "MGN{size: int 1..99}{block: C|H}[E:special_block]{blocks: int 0..99}R{length: int 1..9999}[E:special_rail][{preload: Z0|ZF|Z1}][{precision: C|H|P}][{material: M|HC|NC}][{rails: I|II|III|IIII}][+{code_options}]"

'''
rows = ""
for b in blocks:
    rows += f'[rows."{b["block"]}-{b["size"]}"]\nsource = "HIWIN MG catalogue G99TE24-2410, {b["source"]} {b["page"]}; rail: S4 p.88 table 2-4-19 (1), p.85 Table 2-4-15"\npage = 88\nstatus = "{ "verified" if b["status"] == "labelled" else "needs_review" }"\n\n'
from runtime.parametric.manifest import write_manifest
write_manifest((PKG / "generator.toml"), head + rows.rstrip() + "\n", {'code_options': {'type': 'text', 'min': 1, 'max': 64, 'escape': '[A-Za-z0-9+]'}})
print("wrote", PKG)
