#!/bin/bash
# usage: ci.sh OUTDIR   (repo root; SC_CLI and RHAI_RUN set): build the parametric design, run every code both ways, write OUTDIR/faithfulness.json
set -eu; P=vendors/misumi/lhb/housing-g/parametric; O=$1; mkdir -p "$O"
python3 $P/build.py
python3 $P/run_codes.py --out "$O"
python3 $P/faithfulness.py "$O/results.json" "$O/faithfulness.json"
