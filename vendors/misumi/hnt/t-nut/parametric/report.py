#!/usr/bin/env python3
"""results.json -> the markdown tables of README.md (python reference | parametric | spec check | equal?)."""
import json, sys
from pathlib import Path
R = json.loads(Path(sys.argv[1]).read_text())
def f(m): return f"{m['volume']:.3f} / {m['area']:.3f} / {m['bbox'][0]:g}x{m['bbox'][1]:g}x{m['bbox'][2]:g} / {m['faces']}"
def eq(a, b):
    return (abs(a["volume"] - b["volume"]) <= 1e-6 * a["volume"] and abs(a["area"] - b["area"]) <= 1e-6 * a["area"] and a["bbox"] == b["bbox"]
            and a["faces"] == b["faces"] and a["bodies"] == b["bodies"] and a["threads"] == b["threads"])
def spec(s): return f"{s['rows'] - len(s['failed'])}/{s['rows']}" if s else "-"
print("| code | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec check python | spec check parametric | equal (incl. thread span) |")
print("|---|---|---|---|---|---|")
seen = set()
for c in R["codes"] + [e for e in R.get("all_rows", [])]:
    if c["code"] in seen: continue
    seen.add(c["code"])
    p, q = c["python"], c.get("parametric", {})
    if "volume" not in q: print(f"| {c['code']} | {f(p)} | {q} | | | no |"); continue
    print(f"| {c['code']} | {f(p)} | {f(q)} | {spec(c.get('python_spec'))} | {spec(c.get('parametric_spec'))} | {'yes' if eq(p, q) else 'NO'} |")
print()
print("| rejected code | python message | parametric message | same |")
print("|---|---|---|---|")
for r in R["refusals"]:
    print(f"| {r['code']} | {r['python']} | {r['parametric']} | {'yes' if r['python'] == r['parametric'] else 'no'} |")
