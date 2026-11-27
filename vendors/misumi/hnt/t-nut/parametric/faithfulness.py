#!/usr/bin/env python3
"""results.json of run_codes.py -> faithfulness.json for tools/parametric-verdict.  usage: faithfulness.py RESULTS.json OUT.json"""
import json, sys
r = json.load(open(sys.argv[1]))
def m(x):
    if not x or "error" in x or "refused" in x: return {"error": True}
    return {"volume": x["volume"], "area": x["area"], "bbox": list(x["bbox"]), "faces": x["faces"], "bodies": x["bodies"]}
def spec(s): return f"{s['rows'] - len(s['failed'])}/{s['rows']}" if s else None
valid = [{"code": c["code"], "python": m(c.get("python")), "parametric": m(c.get("parametric")),
          "spec_python": spec(c.get("python_spec")), "spec_parametric": spec(c.get("parametric_spec"))} for c in r["codes"]]
seen = {c["code"] for c in valid}
# the other (type, M) rows of the table that codes.txt does not list
valid += [{"code": e["code"], "python": m(e["python"]), "parametric": m(e["parametric"]),
           "spec_python": spec(e.get("python_spec")), "spec_parametric": spec(e.get("parametric_spec")), "note": "row of the types table that codes.txt does not list"}
          for e in r.get("all_rows", []) if e["code"] not in seen]
out = {"generator": "misumi.hnt.t-nut", "valid": valid,
       "rejects": [{"code": x["code"], "python": x["python"], "parametric": x["parametric"]} for x in r["refusals"]],
       "rebuild": [],
       "blocked": [{"what": "thread designation (M3 / M4 / M5) from a parameter: one thread feature per size, suppressed per row", "needs": "tangency-labs/solidcraft#23175 (S8)"}]}
json.dump(out, open(sys.argv[2], "w"), indent=1)
