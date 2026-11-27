#!/bin/bash
# usage: run_exp.sh OUTDIR TEMPLATE.sc script.json...   runs each script on the template, writes results
set -u; O=$1; T=$2; shift 2; mkdir -p "$O"
for f in "$@"; do n=$(basename "$f" .json); echo "=== $n"
  "$SC_CLI" run "$f" --in "$T" --results --json-out "$O/$n.res.json" --save "$O/$n.sc" --quiet 2>&1 | head -c 800
  python3 -I - "$O/$n.res.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1]))
if isinstance(r,dict): print("ERROR", json.dumps(r.get("error"))[:800])
else: print("steps ok:",len(r))
PY
done
