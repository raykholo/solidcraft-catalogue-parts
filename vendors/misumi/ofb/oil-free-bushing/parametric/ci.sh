#!/bin/bash
# usage: ci.sh OUTDIR   (repo root; SC_CLI and RHAI_RUN set): build the parametric design, run every code both ways, write OUTDIR/faithfulness.json
set -eu; P=vendors/misumi/ofb/oil-free-bushing/parametric; O=$1; mkdir -p "$O"
python3 $P/rhai_equiv.py "$O/rhai_equiv.json" > /dev/null
python3 $P/build.py
python3 $P/run_codes.py --out "$O"
python3 $P/faithfulness.py "$O/results.json" "$O/faithfulness.json"
cp vendors/misumi/ofb/oil-free-bushing/parametric/oil-free-bushing/oil-free-bushing.sc "$O/oil-free-bushing.sc.json"   # the model (a zip; named .json so the workflow uploads it)
