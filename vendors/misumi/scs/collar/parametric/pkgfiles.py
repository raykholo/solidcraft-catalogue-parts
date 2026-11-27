"""Write tables/*.csv and generator.toml of the shaft-collar package from data/*.csv (the single source of every number)."""
from __future__ import annotations
import csv, json
from pathlib import Path
from runtime.table import read_csv

TEMPLATES = [r"C-{type: SCSAW|SCNPAW|SCSMAW|SCSGAW}{d: int 0..99}\-{b: int 0..99}",
             r"C-{kind: SCSBNAW}{d: int 0..99}\-{ds: int 0..99}",
             "E-[{plat: P|S}]{fam: SCSPD|SCD}{d: int 0..99}",
             r"E-[{plat: P|S}]{fam: SCDJ}{d: int 0..99}[\-{b: int 0..99}]",
             "{raw: text 1..64 [A-Za-z0-9-]}"]

def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(header); w.writerows(rows)

def keyed(path, rows, key):
    write_csv(path, ["key"] + list(rows[0]), [[key(r)] + list(r.values()) for r in rows])

def write_tables(pkg: Path, data: Path):
    t = pkg / "tables"; t.mkdir(parents=True, exist_ok=True)
    sizes, bearing, ure, types = (read_csv(data / f"{n}.csv") for n in ("sizes", "bearing", "urethane", "types"))
    keyed(t / "sizes.csv", sizes, lambda r: f'{r["type"]}-{r["D"]}-{r["B"]}')
    keyed(t / "bearing.csv", bearing, lambda r: f'C-SCSBNAW-{r["D"]}')
    keyed(t / "urethane.csv", ure, lambda r: f'{r["family"]}-{r["D"]}')
    write_csv(t / "types.csv", list(types[0]), [list(r.values()) for r in types])
    pr = [[r["name"], r["value"], r["unit"], r["source"], r["page"], r["status"]] for r in read_csv(data / "params.csv")]
    ints = lambda xs: "|".join(str(x) for x in sorted(set(xs)))
    lists = []
    for typ in ("C-SCSAW", "C-SCNPAW", "C-SCSMAW", "C-SCSGAW"):
        lists.append((f"ds_{typ}", ints(int(r["D"]) for r in sizes if r["type"] == typ), "S20"))
        for D in sorted({int(r["D"]) for r in sizes if r["type"] == typ}):
            lists.append((f"bs_{typ}_{D}", ints(int(r["B"]) for r in sizes if r["type"] == typ and int(r["D"]) == D), "S20"))
    lists.append(("ds_bearing", "|".join(r["D"] for r in bearing), "S21"))
    for fam in ("slit", "slit-compact", "split-compact"):
        lists.append((f"ds_{fam}", ints(int(r["D"]) for r in ure if r["family"] == fam), "S21"))
        lists.append((f"stainless_{fam}", ints(int(r["D"]) for r in ure if r["family"] == fam and r["stainless"] == "1"), "S21"))
    pr += [[n, v, "", s, "derived from the size tables", "labelled"] for n, v, s in lists]
    write_csv(t / "params.csv", ["name", "value", "unit", "source", "page", "status"], pr)

def write_toml(pkg: Path, data: Path):
    lines = ['format = "solidcraft-generator/2"', 'id = "scs-collar"',
             'name = "MISUMI Economy Series shaft collars: aluminium slit and split, with fixing holes, bearing inner mount, and with urethane damper"',
             'license = "CC0-1.0"', 'model = "scs-collar.sc"', "",
             "# One configuration row per catalogue row; no free parameter (B follows from D in every table, and the plating E- / E-P / E-S only changes the text).",
             "# The `\\-` between the two sizes is a required separator (`C-SCSAW1210` is refused, as the Python regular expressions do).",
             "# The last template takes anything else so that generator.rhai can give the Python generator's message for a code of the wrong shape."]
    for p in TEMPLATES:
        lines += ["", "[[template]]", f"pattern = '{p}'"]
    lines.append("")
    for fn, key in (("sizes", lambda r: f'{r["type"]}-{r["D"]}-{r["B"]}'), ("bearing", lambda r: f'C-SCSBNAW-{r["D"]}'), ("urethane", lambda r: f'{r["family"]}-{r["D"]}')):
        for r in read_csv(data / f"{fn}.csv"):
            lines += [f'[rows."{key(r)}"]', f'source = {json.dumps("MISUMI Economy Series catalogue 2025 " + r["source"] + " (sources.toml), " + r["page"])}',
                      f'page = {json.dumps(r["page"])}', 'status = "verified"',
                      'note = "slit width, gap, clamp screw position and the damper shape are appearance, approximate (README, not guaranteed)"', ""]
    (pkg / "generator.toml").write_text("\n".join(lines))
