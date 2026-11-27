#!/usr/bin/env python3
"""End-to-end proof for misumi.lhb.housing-g: every code of ../codes.txt (plus extra refusals) goes code -> field template -> Rhai `resolve` ->
a configuration row for the code (`config.row from=<row>`) in a working copy of housing-g.sc -> a design inserts that copy with
`component.insert_design {configuration}` -> `inspect.measure` + `model.threads` + the unchanged ../src/check.py spec check; the same code is
built by the Python generator and measured the same way. Writes results.json in --out.

    SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run binary> python3 run_codes.py --out DIR      (--rhai-only: no SolidCraft)
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[4]))
from runtime.parametric import kit as pk

def part_from_result(R, res, code):
    """The object src/check.py takes, built from the Rhai result and the package tables (never from the Python parser)."""
    pr = res["properties"]
    d = dict(R.tables["housing-g"][str(pr["dr"])])
    d["H_choices"] = [int(x) for x in str(d["H_choices"]).split("|")]
    return R.gen.module("housing").Housing(pr["part_number"], pr["type"], pr["series"], pr["dr"], pr["h"], d)

GEN = pk.Gen(
    gid="misumi.lhb.housing-g", sample="E-LBHG12-15", pkg=HERE / "housing-g", model="housing-g.sc", part_from_result=part_from_result,
    extra_refusals=["E-LBHG12-", "E-LBHG1215", "E-LBHGW-25", "E-LBHGW12-15-P", "E-LBHG12X", "E-LBHG16-35", "E-LBHGW25-50", "E-LBHG013-15", "E-LBHGW20-0", "E-LBHG99-99"],
    rebuilds=[("E-LBHG12-15", "hc", "25 mm", "E-LBHG12-25"), ("E-LBHGW25-25", "hc", "40 mm", "E-LBHGW25-40"), ("E-LBHG30-30", "hc", "50 mm", "E-LBHG30-50")],
    probes={"centre height 60 mm (outside 15..50) by an ordinary parameters.change": lambda res: [
                {"command": "parameters.change", "params": {"name": "hc", "expression": "60 mm"}}, {"command": "inspect.measure", "params": {}}],
            "centre height 15 mm on dr 30 in a configuration row (allowed 30, 40, 50)": lambda res: [
                {"command": "config.row", "params": {"name": "bad", "from": "G-30", "values": {"param:hc": "15 mm"}}}]},
    free_param="hc", free_value="25 mm",
    blocked=[{"what": "free parameter values on an inserted link (insert_design parameters ignored; set_link_parameters unknown)", "needs": "needs #23175 (our draft, being finished)"}])

if __name__ == "__main__":
    pk.main(GEN)
