#!/bin/bash
# usage: ci.sh OUTDIR   (repo root; SC_CLI and RHAI_RUN set): build the parametric design, run every code both ways, write OUTDIR/faithfulness.json
set -eu; P=vendors/hiwin/eg/guideway/parametric; G=vendors/hiwin/guideway-parametric; O=$1; mkdir -p "$O"
python3 $G/gw_build.py EG $P "$O/build"
cp $P/eg-guideway/eg-guideway.sc "$O/eg-guideway.sc.json"         # the model (a zip), kept with the other artifacts
python3 $G/gw_harness.py EG $P "$O/harness"
cp "$O/harness/report.json" "$O/harness/rebuild.json" "$O/build/build.json" "$O/"
python3 $G/gw_faith.py EG "$O/harness" "$O/faithfulness.json"

python3 -m runtime.parametric.links "vendors/hiwin/eg/guideway" "$O"

python3 -m runtime.parametric.native_parse "vendors/hiwin/eg/guideway" "$O"
