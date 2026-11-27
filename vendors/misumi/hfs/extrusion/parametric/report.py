#!/usr/bin/env python3
"""results.json -> the markdown tables of README.md (python reference | parametric | spec check | equal?)."""
import json, sys
from pathlib import Path
R = json.loads((Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_name("results.json"))).read_text())
def f(m): return f"{m['volume']:.1f} / {m['area']:.1f} / {m['bbox'][0]:g}x{m['bbox'][1]:g}x{m['bbox'][2]:g} / {m['faces']}"
def eq(a, b):
    return (abs(a["volume"] - b["volume"]) <= 1e-6 * a["volume"] and abs(a["area"] - b["area"]) <= 1e-6 * a["area"] and a["bbox"] == b["bbox"] and a["faces"] == b["faces"]
            and a["bodies"] == b["bodies"])
print("| code | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec check python | spec check parametric | equal |")
print("|---|---|---|---|---|---|")
for c in R["codes"]:
    p, q = c["python"], c.get("parametric", {})
    ps = c["python_spec"]; qs = c.get("parametric_spec")
    if "volume" not in q:
        print(f"| {c['code']} | {f(p)} | {q} | | | no |"); continue
    print(f"| {c['code']} | {f(p)} | {f(q)} | {ps['rows'] - len(ps['failed'])}/{ps['rows']} | {qs['rows'] - len(qs['failed'])}/{qs['rows']} | {'yes' if eq(p, q) else 'NO'} |")
print()
print("| rejected code | python message | parametric message | same |")
print("|---|---|---|---|")
for r in R["refusals"]:
    print(f"| {r['code']} | {r['python']} | {r['parametric']} | {'yes' if r['python'] == r['parametric'] else 'no'} |")
print()
print("| change length of | to | changed-in-place vol / area / bbox / faces | direct code (inserted) | python | equal (changed = direct = python) |")
print("|---|---|---|---|---|---|")
for e in R["parametric"]:
    if e.get("error"): print(f"| {e['base']} | {e['length']} | ERROR {e['error']} | | | |"); continue
    a, b, c = e["changed"], e["direct_inserted"], e["python"]
    print(f"| {e['base']} | {e['length']} | {f(a)} | {f(b)} | {f(c)} | {'yes' if eq(a, b) and eq(a, c) else 'NO'} |")
