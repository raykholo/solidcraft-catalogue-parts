"""Write tables/*.csv and generator.toml of the generator package from data/*.csv (the single source of every number)."""
from __future__ import annotations
import csv, shutil
from pathlib import Path
from runtime.table import read_csv

PAGE = "p.537"
TEMPLATES = ["E-[S:stainless]STHW{shape: R=round, C=compact}[B:black]K{d}",
             "E-{type}{d}"]

def write_tables(pkg: Path, data: Path):
    t = pkg / "tables"; t.mkdir(parents=True, exist_ok=True)
    for n in ("dims", "types"):
        shutil.copyfile(data / f"{n}.csv", t / f"{n}.csv")
    dims, types = read_csv(data / "dims.csv"), read_csv(data / "types.csv")
    rows = [("types_text", ", ".join(r["type"] for r in types)), ("dkeys", "|".join(r["D"] for r in dims)), ("page", PAGE)]
    with open(t / "params.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["name", "value"]); w.writerows(rows)

def write_toml(pkg: Path, data: Path, row_keys):
    dims = {r["D"]: r for r in read_csv(data / "dims.csv")}
    lines = ['format = "solidcraft-generator/2"', 'id = "dowel-flanged-shaft-support"',
             'name = "MISUMI Economy dowel flanged shaft support"', 'license = "CC0-1.0"',
             'model = "dowel-flanged-shaft-support.sc"', ""]
    for tpl in TEMPLATES + ["{raw}"]:
        lines += ["[[template]]", f"pattern = '{tpl}'", ""]
    for key in row_keys:
        d = dims[key.split("-")[1]]
        lines += [f'[rows."{key}"]', f'source = "MISUMI Economy Series catalogue {d["source"]} (sources.toml), {d["page"]}"', f'page = "{d["page"]}"', 'status = "verified"', ""]
    from runtime.parametric.manifest import write_manifest
    write_manifest((pkg / "generator.toml"), "\n".join(lines), {'raw': {'type': 'text', 'min': 1, 'max': 128, 'escape': '[ -~]'}, 'd': {'type': 'int', 'min': 0, 'max': 999999}, 'type': {'type': 'text', 'min': 1, 'max': 12, 'escape': '[A-Za-z]'}})
