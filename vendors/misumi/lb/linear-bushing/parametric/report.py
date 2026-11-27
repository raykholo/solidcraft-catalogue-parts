#!/usr/bin/env python3
"""results.json -> the markdown tables of README.md (python reference | parametric | spec check | equal?).  usage: report.py [results.json]"""
import json, sys
from pathlib import Path
R = json.loads((Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_name("results.json"))).read_text())
def f(m): return f"{m['volume']:.1f} / {m['area']:.1f} / {m['bbox'][0]:g}x{m['bbox'][1]:g}x{m['bbox'][2]:g} / {m['faces']}"
def eq(a, b):
    close = lambda x, y: abs(x - y) <= 1e-6 * max(1.0, abs(x), abs(y))
    return close(a["volume"], b["volume"]) and close(a["area"], b["area"]) and all(close(x, y) for x, y in zip(a["bbox"], b["bbox"])) and a["faces"] == b["faces"] and a["bodies"] == b["bodies"]
print("| code | row | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec python | spec parametric | description same | equal |")
print("|---|---|---|---|---|---|---|---|")
sweep = [c for c in R["codes"] if c.get("sweep")]
for c in [c for c in R["codes"] if not c.get("sweep")]:
    p, q = c["python"], c.get("parametric", {})
    ps = c["python_spec"]; qs = c.get("parametric_spec")
    if "volume" not in q:
        print(f"| {c['code']} | | {f(p)} | {q} | | | | no |"); continue
    print(f"| {c['code']} | {c['configuration']} | {f(p)} | {f(q)} | {ps['rows'] - len(ps['failed'])}/{ps['rows']} | {qs['rows'] - len(qs['failed'])}/{qs['rows']} | {'yes' if c.get('description_same') else 'NO'} | {'yes' if eq(p, q) else 'NO'} |")
if sweep:
    same = sum(1 for c in sweep if "volume" in c.get("parametric", {}) and eq(c["python"], c["parametric"]))
    spec = sum(1 for c in sweep if c.get("parametric_spec") and not c["parametric_spec"]["failed"] and c["python_spec"]["rows"] == c["parametric_spec"]["rows"])
    desc = sum(1 for c in sweep if c.get("description_same"))
    print(f"\nSweep of every other valid code of the generator: {len(sweep)} codes, identical to the Python part {same}/{len(sweep)}, same spec check rows and all passed {spec}/{len(sweep)}, same description {desc}/{len(sweep)}.")
print()
print("| rejected code | python message | parametric message | same |")
print("|---|---|---|---|")
for r in R["refusals"]:
    print(f"| {r['code']} | {r['python']} | {r['parametric']} | {'yes' if r['python'] == r['parametric'] else 'no'} |")
print()
print("| built | changed | to | changed in place vol / area / bbox / faces | direct code (inserted) | python | equal |")
print("|---|---|---|---|---|---|---|")
for e in R["parametric"]:
    if e.get("error"): print(f"| {e['base']} | {e['changes']} | {e['direct']} | ERROR {e['error']} | | | |"); continue
    a, b, c = e["changed"], e["direct_inserted"], e["python"]
    print(f"| {e['base']} | {', '.join(e['changes'])} | {e['direct']} | {f(a)} | {f(b)} | {f(c)} | {'yes' if eq(a, b) and eq(a, c) else 'NO'} |")
print()
print("| round trip | printed | same configuration and parameters |")
print("|---|---|---|")
for e in R["roundtrip"]:
    print(f"| {e['code']} | {e['printed']} | {'yes' if e['same_parameters'] else 'NO'} |")
print()
print("| what was tried (SolidCraft 0.50.0) | error | result |")
print("|---|---|---|")
for k, v in R["limits"].items():
    print(f"| {k} | {v['error']} | {v['result']} |")
