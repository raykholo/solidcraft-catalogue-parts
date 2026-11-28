"""Write tables/*.csv and generator.toml of the shaft-holder package from data/*.csv (the single source of every number)."""
from __future__ import annotations
import csv, json
from pathlib import Path
from runtime.table import read_csv

TEMPLATES = ["{pfx: E|C}-SH{fam: STBN|STMN|STB|STM|STA|WTB|WTA|A}{d: int 1..99}[\\-{h: int 0..99999999}]",
             "{raw}"]

from runtime.parametric.kit import write_csv

def write_tables(pkg: Path, data: Path, keys=None):
    t = pkg / "tables"; t.mkdir(parents=True, exist_ok=True)
    dims = read_csv(data / "dims.csv"); csha = read_csv(data / "csha.csv")
    write_csv(t / "dims.csv", ["key"] + list(dims[0]), [[f'{r["family"]}-{r["D"]}'] + list(r.values()) for r in dims])
    write_csv(t / "csha.csv", ["key"] + list(csha[0]), [[f'csha-{r["D"]}'] + list(r.values()) for r in csha])
    for n in ("types", "tolerance"):
        rows = read_csv(data / f"{n}.csv")
        write_csv(t / f"{n}.csv", list(rows[0]), [list(r.values()) for r in rows])
    sizes = lambda rows, fam=None: "|".join(str(x) for x in sorted({int(r["D"]) for r in rows if fam is None or r["family"] == fam}))
    pr = [["h_tol", "0.02", "mm", "S50", "p.541 / p.542 (H +-0.02)", "labelled"]]
    for fam in ("slit", "side", "thick"):
        pr.append([f"sizes_{fam}", sizes(dims, fam), "mm", "S50", "p.542 table" if fam == "thick" else "p.541 table", "labelled"])
    pr.append(["sizes_csha", sizes(csha), "mm", "S50", "p.540 table", "labelled"])
    write_csv(t / "params.csv", ["name", "value", "unit", "source", "page", "status"], pr)

def write_toml(pkg: Path, data: Path):
    lines = ['format = "solidcraft-generator/2"', 'id = "shf-shaft-holder"',
             'name = "MISUMI Economy shaft supports: T-shaped with slit, with side slit, thickened, and T-shaped aluminium (C-SHA)"', 'license = "CC0-1.0"',
             'model = "shf-shaft-holder.sc"', "",
             "# E-SH<type><D>-<H> or C-SHA<D>: one configuration row per (family, D); H is the free parameter (a list per row in the model's rules).",
             "# The second template takes anything else so that generator.rhai can give the Python generator's message for a code of the wrong shape.",
             "[parameters]", 'h = { type = "int", min = 10, max = 80, unit = "mm" }', ""]
    for p in TEMPLATES:
        lines += ["[[template]]", f"pattern = '{p}'", ""]
    for fam, fn in (("", "dims"), ("csha-", "csha")):
        for r in read_csv(data / f"{fn}.csv"):
            key = f'{r["family"]}-{r["D"]}' if fn == "dims" else f'csha-{r["D"]}'
            lines += [f'[rows."{key}"]', f'source = {json.dumps("MISUMI Economy Series catalogue 2025 " + r["source"] + " (sources.toml), " + r["page"])}',
                      f'page = {json.dumps(r["page"])}', 'status = "verified"',
                      'note = "labelled catalogue dimensions; the position of the second base row and second screw of the thickened types is appearance"', ""]
    from runtime.parametric.manifest import write_manifest
    write_manifest((pkg / "generator.toml"), "\n".join(lines), {'raw': {'type': 'text', 'min': 1, 'max': 64, 'escape': '[A-Za-z0-9-]'}})
