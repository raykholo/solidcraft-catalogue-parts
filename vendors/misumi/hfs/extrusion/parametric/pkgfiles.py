"""Write tables/*.csv and generator.toml of the generator package from data/*.csv (the single source of every number)."""
from __future__ import annotations
import csv
from pathlib import Path
from runtime.table import read_csv
from vendors.misumi.hfs.extrusion.src import ext

TEMPLATE = "[K:fixed]{part_type}-{profile}[-{length: decimal}][-{alts}]"

from runtime.parametric.kit import write_csv

def write_tables(pkg: Path, data: Path):
    t = pkg / "tables"; t.mkdir(parents=True, exist_ok=True)
    prof = read_csv(data / "profiles.csv")
    cols = [c for c in prof[0] if c not in ("key", "cite", "note")]
    write_csv(t / "sections.csv", ["key"] + cols + ["source", "page", "status"],
              [[r["key"]] + [r[c] for c in cols] + [r["cite"].split(" ", 1)[0], r["cite"].split(" ", 1)[1], "verified"] for r in prof])
    rows, series_types = [], {"5": set(), "6": set()}
    for r in read_csv(data / "types.csv"):
        series_types[r["series"]].add(r["type"])
        keys = [f'{r["type"]}:{p}' for p in r["profiles"].split("|")] if r["profiles"] else [r["type"]]
        for k in keys:
            rows.append([k, r["type"], r["series"], r["material"], r["surface"], r["source"], r["page"], r["status"]])
    write_csv(t / "types.csv", ["key", "type", "series", "material", "surface", "source", "page", "status"], rows)
    pr = [[r["name"], r["value"], r["unit"], r["source"], r["page"], r["status"]] for r in read_csv(data / "params.csv")]
    derived = [("types5", "|".join(sorted(series_types["5"]))), ("types6", "|".join(sorted(series_types["6"]))),
               ("other_types", "|".join(sorted(ext.OTHER_TYPES))), ("profiles5", "|".join(sorted(ext.PROFILES[5]))),
               ("profiles6", "|".join(sorted(ext.PROFILES[6])))]
    pr += [[n, v, "", "S1;S10", "p.529 / p.571", "labelled"] for n, v in derived]
    write_csv(t / "params.csv", ["name", "value", "unit", "source", "page", "status"], pr)

def write_toml(pkg: Path, data: Path):
    prof = read_csv(data / "profiles.csv")
    lines = ['format = "solidcraft-generator/2"', 'id = "hfs-extrusion"',
             'name = "MISUMI aluminium extrusions, 5 series 2020 / 2040 / 4040 and 6 series 3030"', 'license = "CC0-1.0"',
             'model = "hfs-extrusion.sc"', "", "[parameters]",
             'part_type = { type = "text", default = "HFS5" }',
             'profile = { type = "choice", values = ["2020", "2040", "4040", "3030"] }',
             'length = { type = "decimal", min = 50, max = 4000, step = 0.5, unit = "mm" }',
             'fixed = { type = "int", min = 0, max = 1 }', 'tap_l = { type = "int", min = 0, max = 1 }', 'tap_r = { type = "int", min = 0, max = 1 }',
             'wl_rows = { type = "int", min = 0, max = 3 }', 'wr_rows = { type = "int", min = 0, max = 3 }', "",
             "[[template]]", f"pattern = '{TEMPLATE}'", ""]
    for r in prof:
        src, page = r["cite"].split(" ", 1)
        lines += [f'[rows."{r["key"]}"]', f'source = "MISUMI FA catalogue {src} (sources.toml), {page}"', f'page = "{page}"', 'status = "verified"',
                  'note = "section values read from the vector drawing are listed in the generator README under not guaranteed"', ""]
    from runtime.parametric.manifest import write_manifest
    write_manifest((pkg / "generator.toml"), "\n".join(lines), {'part_type': {'type': 'text', 'min': 3, 'max': 8, 'escape': '[A-Za-z0-9]'}, 'profile': {'type': 'text', 'min': 4, 'max': 6, 'escape': '[0-9]'}, 'alts': {'type': 'text', 'min': 1, 'max': 80, 'escape': '[A-Za-z0-9-]'}})
