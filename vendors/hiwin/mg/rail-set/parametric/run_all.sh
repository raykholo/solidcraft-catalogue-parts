#!/bin/bash
# usage: run_all.sh OUTDIR   (with SC_CLI set, from the repo root): builds the template, the package .sc, runs the harness
set -eu; P=vendors/hiwin/mg/rail-set/parametric; O=$1; mkdir -p "$O"
bash $P/run_template.sh "$O/template"
cp "$O/template/mg-rail-set.sc" $P/mg-rail-set/mg-rail-set.sc
python3 $P/harness/run_all.py "$O/harness"
cp $P/mg-rail-set/mg-rail-set.sc "$O/"
