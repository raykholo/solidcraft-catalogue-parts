#!/bin/bash
# usage: ci.sh OUTDIR   (repo root; SC_CLI and RHAI_RUN set): build the parametric design, run every code both ways, write OUTDIR/faithfulness.json
set -eu; P=vendors/misumi/scs/collar/parametric; O=$1; mkdir -p "$O"
python3 $P/build.py
python3 $P/run_codes.py --out "$O"
python3 $P/faithfulness.py "$O/results.json" "$O/faithfulness.json"
cp "$P/scs-collar/scs-collar.sc" "$O/scs-collar.sc.json"    # the built model, kept with the CI artifact (a .json name so the upload picks it up)

# Optional link proof: release CLIs retain the legacy verdict unchanged.
python3 -m runtime.parametric.links "vendors/misumi/scs/collar" "$O"

python3 -m runtime.parametric.native_parse "vendors/misumi/scs/collar" "$O"
