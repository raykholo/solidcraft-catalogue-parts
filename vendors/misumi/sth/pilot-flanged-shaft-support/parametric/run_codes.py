#!/usr/bin/env python3
"""End-to-end proof for misumi.sth.pilot-flanged-shaft-support: every codes.txt code both ways (the harness is runtime/parametric/harness.py).

    SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run binary> python3 run_codes.py --out DIR [--only CODE]     # writes DIR/results.json and DIR/faithfulness.json
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
GEN = HERE.parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime.parametric.harness import Harness, main, table_row, with_description

PKG = HERE / "pilot-flanged-shaft-support"
GEN_ID = "misumi.sth.pilot-flanged-shaft-support"
EXTRA_REFUSALS = ["E-STHWIRB8-", "E-STHWIRB0", "E-STHWIRB09", "E-STHWIRB100", "E-STHWISB8", "E-STHWI8", "E-STHWIRBK12", "E-SSTHWIRB12"]
# a built design switched to another row (a different family, a different screw size, a very different size) = that other code inserted directly
REBUILD = [("E-STHWIRB8", "E-STHWICB40"), ("E-STHWICB30", "E-STHWIRB12"), ("E-STHWIRB40", "E-STHWIRB8")]
BLOCKED = [{"what": "a code that matches no template gets the engine's message, not the generator's (the stand-in asks an optional fn no_match(raw))",
            "needs": "follow-up after #23175: optional no_match(raw) in generator.rhai"},
           {"what": "a thread designation cannot come from a parameter: one thread feature per clamp screw size (M4 M5 M6 M8), suppressed per row",
            "needs": 'follow-up: tangency-labs/solidcraft#9594'}]

def support_from(h, res, code):
    p = res["properties"]; mod = h.gen.module("pilot")
    return with_description(mod.Support, p["description"], code=code.strip().upper(), type=p["type_name"], family=p["family"], D=p["D"],
                            dims=table_row(h.pkg, "dims", p["D"]), material=p["material"], surface=p["surface"])

if __name__ == "__main__":
    h = Harness(GEN, PKG, "pilot-flanged-shaft-support.sc", support_from, EXTRA_REFUSALS, REBUILD, BLOCKED)
    main(h, GEN_ID, BLOCKED)
