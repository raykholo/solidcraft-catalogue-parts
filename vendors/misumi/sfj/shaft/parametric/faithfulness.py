#!/usr/bin/env python3
"""results.json of run_codes.py -> faithfulness.json for tools/parametric-verdict.  usage: faithfulness.py RESULTS.json OUT.json"""
import json, sys
r = json.load(open(sys.argv[1]))
def m(x):
    if not x or "error" in x or "refused" in x: return {"error": True}
    return {"volume": x["volume"], "area": x["area"], "bbox": list(x["bbox"]), "faces": x["faces"], "bodies": x["bodies"]}
def spec(s): return f"{s['rows'] - len(s['failed'])}/{s['rows']}" if s else None
out = {"generator": "misumi.sfj.shaft",
       "valid": [{"code": c["code"], "python": m(c.get("python")), "parametric": m(c.get("parametric")),
                  "spec_python": spec(c.get("python_spec")), "spec_parametric": spec(c.get("parametric_spec")),
                  **({"note": "extra code (not in codes.txt)"} if c.get("extra") else {})} for c in r["codes"]],
       "rejects": [{"code": x["code"], "python": x["python"], "parametric": x["parametric"]} for x in r["refusals"]],
       "rebuild": [{"label": f"{p['base']} L -> {p['length']} vs {p['direct']}", "direct": m(p.get("direct_inserted")), "changed": m(p.get("changed"))}
                   for p in r["parametric"]],
       "blocked": [{"what": "free parameter values on an inserted link (insert_design parameters ignored; set_link_parameters unknown)", "needs": "tangency-labs/solidcraft#23175"},
                   {"what": "thread designation from a parameter (M2.6 has no coarse pitch; one hole feature per size and host face, 46 features)", "needs": "tangency-labs/solidcraft#23175 (S8: designation or size from a parameter, a hole that follows its face)"},
                   {"what": "unordered option set with arguments: each option at most once, object value; the code needs repeats and order", "needs": "field template bag(...) with an ordered [name, argument] list (runtime/fieldtemplate.py)"}]}
json.dump(out, open(sys.argv[2], "w"), indent=1)
