#!/bin/bash
# usage: ci.sh OUTDIR   (repo root; SC_CLI and RHAI_RUN set): build the parametric design, run every code both ways, write OUTDIR/faithfulness.json
set -eu; P=vendors/misumi/lb/linear-bushing/parametric; O=$1; mkdir -p "$O"
python3 $P/rhai_equiv.py "$O/rhai_equiv.json" > /dev/null
python3 $P/build.py
python3 $P/run_codes.py --out "$O"
python3 $P/faithfulness.py "$O/results.json" "$O/faithfulness.json"
cp vendors/misumi/lb/linear-bushing/parametric/linear-bushing/linear-bushing.sc "$O/linear-bushing.sc.json"   # the model (a zip; named .json so the workflow uploads it)

# Optional link proof: release CLIs retain the legacy verdict unchanged.
python3 -m runtime.parametric.links "vendors/misumi/lb/linear-bushing" "$O"
