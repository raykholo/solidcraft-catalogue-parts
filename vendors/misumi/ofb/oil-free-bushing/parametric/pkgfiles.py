"""Write tables/*.csv and generator.toml of the oil-free-bushing package from ../data/*.csv (the single source of every number)."""
from __future__ import annotations
import csv, shutil
from pathlib import Path
from runtime.appearance import APPX
from runtime.table import read_csv
import rows as rw

TYPES = ["C-MUBZU", "C-MUBZ", "C-MUFZU", "C-MUFZ", "C-MUTSZ", "C-MUTNZ", "C-MUTZ", "E-MUGZ", "E-SHBZ", "E-SHFZ", "E-SHTNZ", "E-SHTZ"]
TEMPLATES = ["{otype: " + "|".join(TYPES) + r"}[0:dz]{d}\-[0:lz]{l}[{ending: rest}]",
             "{raw}"]
TABLES = ["copper_straight", "copper_shouldered", "copper_flanged", "thrust", "brass_straight", "brass_shouldered", "brass_flanged"]

from runtime.parametric.kit import write_csv

def write_tables(pkg: Path, data: Path, model_rows):
    t = pkg / "tables"; t.mkdir(parents=True, exist_ok=True)
    lists = []
    for tab in TABLES:
        shutil.copy(data / f"{tab}.csv", t / f"{tab}.csv")          # first column dr is the key; source, page and status stay on every row
        rows = read_csv(data / f"{tab}.csv")
        lists.append([tab, "|".join(str(d) for d in sorted(int(r["dr"]) for r in rows))])
        if "D_thin" in rows[0]:
            lists.append([f"{tab}-thin", "|".join(str(d) for d in sorted(int(r["dr"]) for r in rows if r["D_thin"]))])
    write_csv(t / "lists.csv", ["key", "value"], lists)
    shutil.copy(data / "types.csv", t / "types.csv")
    shutil.copy(data / "params.csv", t / "params.csv")
    write_csv(t / "rows.csv", ["name", "type", "dr", "source", "page", "status"], [[r["name"], r["type"], r["dr"], r["source"], r["page"], r["status"]] for r in model_rows])
    write_csv(t / "appearance.csv", ["key", "value"], [["appx", APPX]])

def write_toml(pkg: Path, model_rows):
    lens = [l for r in model_rows for l in r["lengths"]]
    lines = ['format = "solidcraft-generator/2"', 'id = "oil-free-bushing"',
             'name = "MISUMI Economy oil free bushings: copper alloy and special brass, straight, shouldered, flanged and thrust type"',
             'license = "CC0-1.0"', 'model = "oil-free-bushing.sc"', "", "[parameters]",
             f'blen = {{ type = "int", min = {min(lens)}, max = {max(lens)}, unit = "mm" }}', ""]
    for tpl in TEMPLATES:
        lines += ["[[template]]", f"pattern = '{tpl}'", ""]
    for r in model_rows:
        lines += [f'[rows."{r["name"]}"]', f'source = "MISUMI Economy Series catalogue {r["source"]} (sources.toml), {r["page"]}"',
                  f'page = "{r["page"]}"', 'status = "verified"', ""]
    from runtime.parametric.manifest import write_manifest
    write_manifest((pkg / "generator.toml"), "\n".join(lines), {'d': {'type': 'int', 'min': 0, 'max': 999}, 'l': {'type': 'int', 'min': 0, 'max': 999}, 'raw': {'type': 'text', 'min': 1, 'max': 80, 'escape': '[A-Za-z0-9 _./-]'}})
