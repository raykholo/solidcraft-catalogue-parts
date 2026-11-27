"""Write tables/*.csv and generator.toml of the generator package from data/*.csv (the single source of every number)."""
from __future__ import annotations
import csv, shutil
from pathlib import Path
from runtime.table import read_csv

PAGE = "p.537"
TEMPLATES = ["E-[S:stainless]STHW{shape: R=round, C=compact}[B:black]K{d: text 1..6 [0-9]}",
             "E-{type: text 1..12 [A-Za-z]}{d: text 1..6 [0-9]}"]

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
             'name = "MISUMI Economy flanged shaft supports with slit and positioning (dowel) holes: round (E-STHWRBK, E-STHWRK, E-SSTHWRK) and compact (E-STHWCBK, E-SSTHWCK)"', 'license = "CC0-1.0"',
             'model = "dowel-flanged-shaft-support.sc"', ""]
    for tpl in TEMPLATES:
        lines += ["[[template]]", f"pattern = '{tpl}'", ""]
    for key in row_keys:
        d = dims[key.split("-")[1]]
        lines += [f'[rows."{key}"]', f'source = "MISUMI Economy Series catalogue {d["source"]} (sources.toml), {d["page"]}"', f'page = "{d["page"]}"', f'status = "{d["status"]}"', ""]
    (pkg / "generator.toml").write_text("\n".join(lines))
