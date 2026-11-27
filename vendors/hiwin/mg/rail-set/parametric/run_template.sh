#!/bin/bash
# usage: run_template.sh OUTDIR   (builds OUTDIR/mg-rail-set.sc: stage 1 geometry + parameters + configuration table, stage 2 rules)
set -eu; D=$(cd "$(dirname "$0")" && pwd); O=$1
fail() { python3 -I -c "import json;r=json.load(open('$1'));print(json.dumps(r.get('error') if isinstance(r,dict) else r[-1])[:1500])"; exit 1; }
python3 "$D/build_template.py" "$O"
"$SC_CLI" run "$O/template.json" --save "$O/stage1.sc" --results --json-out "$O/template.res.json" --quiet || fail "$O/template.res.json"
python3 -I - "$O/template.res.json" "$O/feature-ids.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1])); json.dump({x["name"]: x["feature"] for x in r if isinstance(x, dict) and "feature" in x and x.get("name")}, open(sys.argv[2], "w"))
PY
python3 "$D/build_template.py" "$O" "$O/feature-ids.json"
"$SC_CLI" run "$O/rules.json" --in "$O/stage1.sc" --save "$O/mg-rail-set.sc" --results --json-out "$O/rules.res.json" --quiet || fail "$O/rules.res.json"
ls -l "$O/mg-rail-set.sc"
