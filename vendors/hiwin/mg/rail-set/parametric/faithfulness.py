#!/usr/bin/env python3
"""harness/run_all.py output (report.json, rebuild.json) -> faithfulness.json for tools/parametric-verdict.
usage: faithfulness.py HARNESS_OUTDIR OUT.json"""
import json, sys
from pathlib import Path
d = Path(sys.argv[1])
rows = json.load(open(d / "report.json"))
def m(x):
    if not x or "error" in x: return {"error": True}
    return {"volume": x["vol"], "area": x["area"], "bbox": list(x["lo"]) + list(x["hi"]), "faces": x["faces"], "bodies": x["bodies"]}
valid, rejects = [], []
for r in rows:
    if r["code"].startswith("!"):
        p = r["param"]
        rejects.append({"code": r["code"], "python": r["python"], "parametric": p[len("REFUSED: "):] if p.startswith("REFUSED: ") else None})
    else:
        valid.append({"code": r["code"], "python": m(r.get("python_m")), "parametric": m(r.get("param_m")),
                      "spec_python": (r.get("pycheck") or "").split(" ")[0] or None, "spec_parametric": (r.get("check") or "").split(" ")[0] or None})
rb = json.load(open(d / "rebuild.json")) if (d / "rebuild.json").exists() else {}
rebuild = [{"label": "MGN12H2R300Z0C length 300 -> 400 vs MGN12H2R400Z0C", "direct": m(rb.get("fresh")), "changed": m(rb.get("rebuilt"))},
           {"label": "MGN12H2R400Z0C parametric vs Python", "direct": m(rb.get("python")), "changed": m(rb.get("fresh"))}] if rb else []
blocked = [{"what": "free parameter values on an inserted link (insert_design parameters ignored; set_link_parameters unknown)",
            "needs": "tangency-labs/solidcraft#23175"}]
json.dump({"generator": "hiwin.mg.rail-set", "valid": valid, "rejects": rejects, "rebuild": rebuild, "blocked": blocked}, open(sys.argv[2], "w"), indent=1)
