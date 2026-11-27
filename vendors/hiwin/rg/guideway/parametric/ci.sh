#!/bin/bash
# usage: ci.sh OUTDIR   (repo root; SC_CLI and RHAI_RUN set): build the parametric design, run every code both ways, write OUTDIR/faithfulness.json
set -eu; P=vendors/hiwin/rg/guideway/parametric; G=vendors/hiwin/guideway-parametric; O=$1; mkdir -p "$O"
python3 $G/gw_build.py RG $P "$O/build"
cp $P/rg-guideway/rg-guideway.sc "$O/rg-guideway.sc.json"         # the model (a zip), kept with the other artifacts
python3 $G/gw_harness.py RG $P "$O/harness"
cp "$O/harness/report.json" "$O/harness/rebuild.json" "$O/build/build.json" "$O/"
python3 $G/gw_faith.py RG "$O/harness" "$O/faithfulness.json"
