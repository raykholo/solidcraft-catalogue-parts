#!/bin/bash
# usage: run_probes.sh OUTDIR  (runs every probes/*.json on SolidCraft; prints the error or the body list)
set -u; B=${B:-$(dirname "$SC_CLI")}; D=$(cd "$(dirname "$0")" && pwd); mkdir -p "$1"
for f in "$D"/probes/*.json; do n=$(basename "$f" .json); echo "=== $n"
  "$SC_CLI" run "$f" --results --json-out "$1/$n.res.json" --save "$1/$n.sc" --quiet >"$1/$n.log" 2>&1; echo "exit $?"
  python3 -I - "$1/$n.res.json" <<'PY'
import json,sys
try: r=json.load(open(sys.argv[1]))
except Exception as e: print("no result:",e); raise SystemExit
if isinstance(r,dict) and r.get("error"): print("ERROR", json.dumps(r["error"])[:600])
else:
    res=r["results"] if isinstance(r,dict) else r
    print("ok", json.dumps(res[-1])[:700])
PY
  head -c 400 "$1/$n.log"
done
