#!/usr/bin/env python3
"""End-to-end proof for misumi.lhb.bushing-housing: every code of ../codes.txt (plus extra refusals) goes code -> field template -> Rhai `resolve` ->
a configuration row for the code (`config.row from=<row>`) in a working copy of bushing-housing.sc -> a design inserts that copy with
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
    dr, series = pr["dr"], pr["series"]
    d = dict(R.tables["double" if series in ("double", "medlong", "long") else "single"][str(dr)])
    col = {"single": ("L_single", "L1_single", "dr_tol_single_upper", "dr_tol_single_lower"), "medium": ("L_medium", "L1_medium", "dr_tol_medium_upper", "dr_tol_medium_lower"),
           "double": ("L_double", "L1_double", None, "dr_tol_double"), "medlong": ("L_medlong", "L1_medlong", None, "dr_tol_medlong"),
           "long": ("L_long", "L1_long", None, "dr_tol_long")}[series]
    tol = (d[col[2]] if col[2] else 0, d[col[3]])
    return R.gen.module("housing").Housing(pr["part_number"], pr["type"], series, dr, pr["dowel"], d, d[col[0]], d[col[1]], tol)

GEN = pk.Gen(
    gid="misumi.lhb.bushing-housing", sample="E-LBHN16", pkg=HERE / "bushing-housing", model="bushing-housing.sc", part_from_result=part_from_result,
    extra_refusals=["E-LBHN", "E-LBHNW-P", "E-LBHN16X", "E-LBHN16-X", "E-LBHN16DP", "E-LBHN160", "E-LBHN6D-P", "E-LBHN35D", "E-LBHNW6-P", "E-LBHNW13D", "E-LBHNW10L",
                    "E-LBHNW35L", "E-LBHN8L", "E-LBHN9-P", "E-LBHP20LUU", "E-LBHNW50D", "E-LBHN40D-P"],
    rebuilds=[("E-LBHN16", "dowel", "1", "E-LBHN16-P"), ("E-LBHNW20L-P", "dowel", "0", "E-LBHNW20L"), ("E-LBHN30D", "dowel", "1", "E-LBHN30D-P"),
              ("E-LBHNW50-P", "dowel", "0", "E-LBHNW50")],
    probes={"dowel = 1 on dr 6 (no dowel hole version) in a configuration row": lambda res: [
                {"command": "config.row", "params": {"name": "bad", "from": "single-6", "values": {"param:dowel": "1"}}}],
            "dowel = 2 (outside 0..1) by an ordinary parameters.change": lambda res: [
                {"command": "parameters.change", "params": {"name": "dowel", "expression": "2"}}, {"command": "inspect.measure", "params": {}}]},
    free_param="dowel", free_value="1",
    blocked=[{"what": "free parameter values on an inserted link (insert_design parameters ignored; set_link_parameters unknown)", "needs": "needs #23175 (our draft, being finished)"},
             {"what": "thread designation from a parameter (one suppressed hole feature per size M4 / M5 / M6 / M8 / M10, for the end rows and for the middle row)",
              "needs": 'follow-up: parameter-driven threads and persistent thread references (outside #23175)'}])

if __name__ == "__main__":
    pk.main(GEN)
