"""Write tables/*.csv and generator.toml of the bracket package from data/*.csv (the single source of every number)."""
from __future__ import annotations
import csv, json
from pathlib import Path
from runtime.table import read_csv
from vendors.misumi.hbl.bracket.src import bracket as br

TEMPLATE = "{base: text 1..24 [A-Za-z0-9]}[-{rest: text 1..40 [A-Za-z0-9-]}]"

def write_csv(path, header, rows):
    with open(path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(header); w.writerows(rows)

def write_tables(pkg: Path, data: Path):
    t = pkg / "tables"; t.mkdir(parents=True, exist_ok=True)
    types = read_csv(data / "types.csv")
    write_csv(t / "types.csv", list(types[0]), [list(r.values()) for r in types])
    alts = read_csv(data / "alterations.csv")
    write_csv(t / "alterations.csv", list(alts[0]), [list(r.values()) for r in alts])
    pr = [[r["name"], r["value"], r["unit"], r["source"], r["page"], r["status"]] for r in read_csv(data / "params.csv")]
    drawn = [r["type"] for r in types if "-" not in r["type"]]
    derived = [("drawn", "|".join(drawn)), ("alt_c_types", "|".join(r["type"] for r in types if r["alt_c"] == "1")),
               ("alterations", "|".join(r["code"] for r in alts)), ("other_types", "|".join(sorted(br.OTHER)))]
    pr += [[n, v, "", "S40", "p.539 / p.540", "labelled"] for n, v in derived]
    write_csv(t / "params.csv", ["name", "value", "unit", "source", "page", "status"], pr)

def write_toml(pkg: Path, data: Path):
    lines = ['format = "solidcraft-generator/2"', 'id = "hbl-bracket"',
             'name = "MISUMI 5 series extruded brackets (HBLTS, HBLTV, HBLTSW, HBLTVW, HBLTF, HBKTS, HBKUS, HBLUS, HBLTH)"', 'license = "CC0-1.0"',
             'model = "hbl-bracket.sc"', "",
             "# The code is the type (one configuration row per type, -4 included) and at most one alteration. The alteration only adds accessory text,",
             "# so there is no free parameter. Both fields are plain text: generator.rhai answers every Python refusal with its own message.",
             "[[template]]", f"pattern = '{TEMPLATE}'", ""]
    for r in read_csv(data / "types.csv"):
        lines += [f'[rows."{r["type"]}"]', f'source = {json.dumps("MISUMI FA catalogue 2014 " + r["source"] + " (sources.toml), " + r["page"])}', f'page = "{r["page"].split()[0]}"',
                  'status = "verified"', 'note = "plain flat arms: the inner-corner web, its ribs and the tab length are not drawn (README, not guaranteed)"', ""]
    (pkg / "generator.toml").write_text("\n".join(lines))
