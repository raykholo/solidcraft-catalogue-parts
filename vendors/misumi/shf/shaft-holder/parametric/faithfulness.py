#!/usr/bin/env python3
"""results.json of run_codes.py -> faithfulness.json for tools/parametric-verdict.  usage: faithfulness.py RESULTS.json OUT.json"""
import json, sys
r = json.load(open(sys.argv[1]))
def m(x):
    if not x or "error" in x or "volume" not in x: return {"error": True}
    return {"volume": x["volume"], "area": x["area"], "bbox": list(x["bbox"]), "faces": x["faces"], "bodies": x["bodies"]}
def spec(s): return f"{s['rows'] - len(s['failed'])}/{s['rows']}" if s else None
rebuild = []
for p in r["parametric"]:
    direct = p.get("direct_inserted") or p.get("python")
    label = f"{p['base']} {p['param']} -> {p['value']}" + (f" vs {p['direct']}" if p.get("direct") else "")
    if not p.get("direct"):
        continue
    rebuild.append({"label": label, "direct": m(direct), "changed": m(p.get("changed"))})
out = {"generator": "misumi.shf.shaft-holder",
       "valid": [{"code": c["code"], "python": m(c.get("python")), "parametric": m(c.get("parametric")),
                  "spec_python": spec(c.get("python_spec")), "spec_parametric": spec(c.get("parametric_spec"))}
                 | ({} if c.get("description_same", True) else {"note": "description differs"}) for c in r["codes"]],
       "rejects": [{"code": x["code"], "python": x["python"], "parametric": x["parametric"]} for x in r["refusals"]],
       "rebuild": rebuild,
       "blocked": [{"what": "free parameter values on an inserted link (insert_design parameters ignored; set_link_parameters unknown): the height H of a code is set in a row of a working copy of the model", "needs": "tangency-labs/solidcraft#23175"}]}
json.dump(out, open(sys.argv[2], "w"), indent=1)
