#!/usr/bin/env python3
"""End-to-end proof for misumi.lhb.tall-housing: every code of ../codes.txt (plus extra refusals) goes code -> field template -> Rhai `resolve` ->
a configuration row for the code (`config.row from=<row>`) in a working copy of tall-housing.sc -> a design inserts that copy with
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
    key = res["configuration"]
    d = dict(R.tables["blocks"][key])
    dw = dict(R.tables["dowel"][key]) if pr["dowel"] else None
    return R.gen.module("housing").Housing(pr["part_number"], pr["type"], pr["series"], pr["dr"], pr["dowel"], d, dw)

GEN = pk.Gen(
    gid="misumi.lhb.tall-housing", sample="E-LBHS10", pkg=HERE / "tall-housing", model="tall-housing.sc", part_from_result=part_from_result,
    extra_refusals=["E-LBHS", "E-LBHSW-P", "E-LBHS16-X", "E-LBHS20UU", "E-LBHS16LP", "E-LBHS160", "E-LBHSW6L", "E-LBHS5D", "E-LBHS6S", "E-LBHS6L", "E-LBHSW14", "E-LBHSW5-P",
                    "E-LBHS13S", "E-LBHS20D-P", "E-LBHS20S-P", "E-LBHS8L-P", "E-LBHN16", "E-LBHSW30D"],
    rebuilds=[("E-LBHS16", "dowel", "1", "E-LBHS16-P"), ("E-LBHS16L-P", "dowel", "0", "E-LBHS16L"), ("E-LBHSW20", "dowel", "1", "E-LBHSW20-P"),
              ("E-LBHS30L-P", "dowel", "0", "E-LBHS30L")],
    probes={"dowel = 1 on a medium housing (no dowel hole version) in a configuration row": lambda res: [
                {"command": "config.row", "params": {"name": "bad", "from": "medium-12", "values": {"param:dowel": "1"}}}],
            "dowel = 2 (outside 0..1) by an ordinary parameters.change": lambda res: [
                {"command": "parameters.change", "params": {"name": "dowel", "expression": "2"}}, {"command": "inspect.measure", "params": {}}]},
    free_param="dowel", free_value="1",
    blocked=[{"what": "free parameter values on an inserted link (insert_design parameters ignored; set_link_parameters unknown)", "needs": "needs #23175 (our draft, being finished)"},
             {"what": "thread designation from a parameter (one suppressed hole feature per size M4 / M5 / M6 / M8 / M10 for M1, for M2 and for the middle M2 hole)",
              "needs": 'follow-up: tangency-labs/solidcraft#9594'}])

if __name__ == "__main__":
    pk.main(GEN)
