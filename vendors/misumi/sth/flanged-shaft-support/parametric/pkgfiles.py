"""Write tables/*.csv and generator.toml of the generator package from data/*.csv (the single source of every number)."""
from __future__ import annotations
import csv, shutil, sys
from pathlib import Path
from runtime import registry
from runtime.table import read_csv

TABLES = {"std": "dims", "thick": "thick", "xend": "xend", "slit": "slit", "slit_long": "slit_long", "mr": "mr"}
TEMPLATES = ["E-[S:stainless]STH[{series: X=xend, W=slit, M=mr}]{shape: R=round, S=square, C=compact}[B:black][N:thick][L:long]{d}",
             "E-{type}{d}"]

def write_tables(pkg: Path, data: Path):
    t = pkg / "tables"; t.mkdir(parents=True, exist_ok=True)
    for f in list(TABLES.values()) + ["types"]:
        shutil.copyfile(data / f"{f}.csv", t / f"{f}.csv")
    mod = registry.Generator(data.parent).module("support")      # the message texts of the Python generator
    rows = [("families_text", mod.FAMILIES_TEXT)] + [(f"page_{s}", p) for s, p in mod.PAGES.items()]
    for key, f in TABLES.items():
        ds = read_csv(data / f"{f}.csv")
        rows.append((f"dkeys_{f}", "|".join(r["D"] for r in ds)))
        rows.append((f"long_ok_{f}", "|".join(r["D"] for r in ds if r.get("L1"))))
    with open(t / "params.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n"); w.writerow(["name", "value"]); w.writerows(rows)

def write_toml(pkg: Path, data: Path, row_keys):
    T = {k: {r["D"]: r for r in read_csv(data / f"{f}.csv")} for k, f in TABLES.items()}
    lines = ['format = "solidcraft-generator/2"', 'id = "flanged-shaft-support"',
             'name = "MISUMI Economy flanged shaft supports: standard, thickened, end mounting, with slit and compact, round / square / compact flange, long sleeve"',
             'license = "CC0-1.0"', 'model = "flanged-shaft-support.sc"', ""]
    for tpl in TEMPLATES:
        lines += ["[[template]]", f"pattern = '{tpl}'", ""]
    for key in row_keys:
        series, rest = key.split("-", 1)
        long = "-long-" in "-" + rest
        D = key.rsplit("-", 1)[1]
        d = T["slit_long" if (series == "slit" and long) else series][D]
        lines += [f'[rows."{key}"]', f'source = "MISUMI Economy Series catalogue {d["source"]} (sources.toml), {d["page"]}"', f'page = "{d["page"]}"', f'status = "{d["status"]}"', ""]
    from runtime.parametric.manifest import write_manifest
    write_manifest((pkg / "generator.toml"), "\n".join(lines), {'d': {'type': 'text', 'min': 1, 'max': 6, 'escape': '[0-9]'}, 'type': {'type': 'text', 'min': 1, 'max': 12, 'escape': '[A-Za-z]'}})
