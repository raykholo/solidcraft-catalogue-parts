"""Writes the generator package files that come from the catalogue tables: <pkg>/tables/*.csv and <pkg>/generator.toml
(the head, [parameters] and templates, comes from the generator's own parametric/package.toml.head; the [rows.*] provenance is generated).
The model <pkg>/<pkg>.sc is built by gw_build.py.   python3 gw_package.py SERIES PARAMETRIC_DIR"""
from __future__ import annotations
import csv, re, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gw_model as m

def write(S: m.Series, par: Path):
    pkg = par / f"{S.dirname}-guideway"
    data = par.parent / "data"
    (pkg / "tables").mkdir(parents=True, exist_ok=True)
    for name in ("rails.csv", "params.csv", "dust.csv"):
        if (data / name).exists():
            shutil.copy(data / name, pkg / "tables" / name)
    blocks = m.blocks_of(S)
    cols = ["key", "kind", "size", "load", "mount", "H", "H1", "N", "W", "B", "B1", "C", "C1", "L1", "L", "M", "M_depth", "hole", "hole_d", "source", "page", "status"]
    with (pkg / "tables/blocks.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(cols)
        for size in S.cat.SIZES:
            for b in blocks[size]:
                d = b.d
                w.writerow([f"{b.key}-{size}", b.kind, size, b.load, b.mount] + [("" if d.get(k) is None else d.get(k)) for k in cols[5:17]]
                           + [d["hole"], d.get("hole_d", ""), b.src["source"], b.src["page"], b.src["status"]])
    head = (par / "package.toml.head").read_text().rstrip() + "\n\n"
    out = ""
    for product, b, size, rm in m.row_list(S, blocks):
        name = m.row_name(S, product, b, size, rm)
        rs = m.rail_source(S, size)
        parts = [f"{x['source']} {x['page']}" for x in ([b.src] if b else []) + [rs]]
        status = "verified" if all(x["status"] == "labelled" for x in ([b.src] if b else []) + [rs]) else "needs_review"
        page = int(re.search(r"\d+", (b.src if b else rs)["page"]).group(0))
        what = {"set": "rail and blocks", "block": "block alone", "rail": "rail alone"}[product]
        out += f'[rows."{name}"]\nsource = "HIWIN Linear Guideway catalogue G99TE24-2410, {"; ".join(parts)}"\npage = {page}\nstatus = "{status}"\nnote = "{what}"\n\n'
    (pkg / "generator.toml").write_text(head + out.rstrip() + "\n")
    return pkg

if __name__ == "__main__":
    print("wrote", write(m.SERIES[sys.argv[1]], Path(sys.argv[2]).resolve()))
