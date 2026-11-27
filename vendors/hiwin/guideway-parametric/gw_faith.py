#!/usr/bin/env python3
"""gw_harness.py output (report.json, rebuild.json) -> faithfulness.json for tools/parametric-verdict.
usage: gw_faith.py SERIES HARNESS_OUTDIR OUT.json"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import gw_model as gm
S = gm.SERIES[sys.argv[1]]; d = Path(sys.argv[2])
rows = json.load(open(d / "report.json"))
rb = json.load(open(d / "rebuild.json")) if (d / "rebuild.json").exists() else {}
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
rebuild = []
for x in rb.get("rebuild", []):
    if "error" in x:
        rebuild.append({"label": x["label"], "direct": {"error": True}, "changed": {"error": True}}); continue
    rebuild.append({"label": x["label"] + " (the fresh parametric instance)", "direct": m(x["fresh"]), "changed": m(x["rebuilt"])})
    rebuild.append({"label": x["label"] + " (the Python part)", "direct": m(x["python"]), "changed": m(x["rebuilt"])})
if rb.get("insert"):
    rebuild.append({"label": rb["insert"]["label"], "direct": m(rb["insert"]["direct"]), "changed": m(rb["insert"]["changed"])})
blocked = [
    {"what": "free parameter values on an inserted link (insert_design `parameters` is ignored silently; component.set_link_parameters is unknown): the instance file is a copy of the design with the values set",
     "needs": "tangency-labs/solidcraft#23175"},
    {"what": "a thread designation cannot come from a parameter: one hole feature per designation (" + ", ".join(gm.feature_names(S, gm.blocks_of(S))[4]) + "), all but the row's own suppressed",
     "needs": "tangency-labs/solidcraft#23175 (solid.hole thread from a parameter or an expression)"},
    {"what": "feature-pattern copies are named Body<N>, not Block 1..n: the spec check reads the blocks by position (the harness renames them)",
     "needs": "tangency-labs/solidcraft#23175 (body_names on solid.pattern.rectangular)"}]
json.dump({"generator": S.gid, "valid": valid, "rejects": rejects, "rebuild": rebuild, "blocked": blocked}, open(sys.argv[3], "w"), indent=1)
