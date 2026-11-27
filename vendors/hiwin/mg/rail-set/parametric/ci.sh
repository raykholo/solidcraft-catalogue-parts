#!/bin/bash
# usage: ci.sh OUTDIR   (repo root; SC_CLI and RHAI_RUN set): build the parametric design, run every code both ways, write OUTDIR/faithfulness.json
set -eu; P=vendors/hiwin/mg/rail-set/parametric; O=$1; mkdir -p "$O"
bash $P/run_all.sh "$O"
python3 $P/faithfulness.py "$O/harness" "$O/faithfulness.json"

# Optional link proof: release CLIs retain the legacy verdict unchanged.
python3 -m runtime.parametric.links "vendors/hiwin/mg/rail-set" "$O"
