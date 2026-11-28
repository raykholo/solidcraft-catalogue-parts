"""Write tables/*.csv and generator.toml of the linear-bushing package from ../data/*.csv (the single source of every number)."""
from __future__ import annotations
import csv
from pathlib import Path
from runtime.appearance import APPX
from runtime.table import read_csv
import rows as rw

TEMPLATES = ["E-LB[{shape: F|K|H}[{variant: PM|CM|Z|M|P|C}]]{dr}{suffix: TUU|DMUU|DUU|LUU|UU}",
             "{raw}"]

from runtime.parametric.kit import write_csv

def ilist(vals):
    return "|".join(str(v) for v in sorted(vals))

def write_tables(pkg: Path, data: Path):
    t = pkg / "tables"; t.mkdir(parents=True, exist_ok=True)
    lists = []
    for tab, _shapes, kind, series in rw.TABLES:
        rows = read_csv(data / f"{tab}.csv")
        hdr = list(rows[0])
        if "shape" in hdr:
            write_csv(t / f"{tab}.csv", ["key"] + hdr, [[f'{r["shape"]}-{r["dr"]}'] + [r[c] for c in hdr] for r in rows])
            for shape in sorted({r["shape"] for r in rows}):
                sel = [r for r in rows if r["shape"] == shape]
                lists.append([f"{tab}-{shape}", ilist(int(r["dr"]) for r in sel)])
                lists.append([f"{tab}-{shape}-pages", "/".join(sorted({r["page"].split()[0] for r in sel}))])
        else:
            write_csv(t / f"{tab}.csv", ["key"] + hdr, [[r["dr"]] + [r[c] for c in hdr] for r in rows])
            lists.append([tab, ilist(int(r["dr"]) for r in rows)])
    write_csv(t / "lists.csv", ["key", "value"], lists)
    ty = read_csv(data / "types.csv"); ext = read_csv(data / "types_ext.csv")
    out = [[r["type"], r["family"], "standard", r["counterbore"], r["plated"], r["source"], r["page"], r["status"]] for r in ty]
    out += [[r["type"], r["family"], r["layout"], r["counterbore"], r["plated"], r["source"], r["page"], r["status"]] for r in ext]
    write_csv(t / "types.csv", ["type", "family", "layout", "counterbore", "plated", "source", "page", "status"], out)
    mr = rw.make_rows()
    write_csv(t / "rows.csv", ["name", "kind", "series", "shape", "dr", "L1", "L2", "source", "page", "status"],
              [[r["name"], r["kind"], r["series"], r["shape"] or "", r["dr"], rw.g(r["lengths"][0]), rw.g(r["lengths"][1]) if len(r["lengths"]) > 1 else "",
                r["source"], r["page"], r["status"]] for r in mr])
    write_csv(t / "params.csv", ["key", "value"], [["appx", APPX]])

def write_toml(pkg: Path, data: Path, model_rows):
    lines = ['format = "solidcraft-generator/2"', 'id = "linear-bushing"',
             'name = "MISUMI Economy linear bushings: straight, round / square / compact flanged, with pilot and centre flange"',
             'license = "CC0-1.0"', 'model = "linear-bushing.sc"', "", "[parameters]",
             f'blen = {{ type = "decimal", min = {min(l for r in model_rows for l in r["lengths"])}, max = {max(l for r in model_rows for l in r["lengths"])}, unit = "mm" }}',
             'opp = { type = "int", min = 0, max = 1 }', 'plated = { type = "int", min = 0, max = 1 }', ""]
    for tpl in TEMPLATES:
        lines += ["[[template]]", f"pattern = '{tpl}'", ""]
    for r in model_rows:
        lines += [f'[rows."{r["name"]}"]', f'source = "MISUMI Economy Series catalogue {r["source"]} (sources.toml), {r["page"]}"',
                  f'page = "{r["page"]}"', f'status = "{r["status"]}"', ""]
    from runtime.parametric.manifest import write_manifest
    write_manifest((pkg / "generator.toml"), "\n".join(lines), {'dr': {'type': 'text', 'min': 1, 'max': 2, 'escape': '[0-9]'}, 'raw': {'type': 'text', 'min': 1, 'max': 80, 'escape': '[A-Za-z0-9 _./-]'}})
