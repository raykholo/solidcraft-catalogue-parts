#!/usr/bin/env python3
"""End-to-end proof for misumi.sth.dowel-flanged-shaft-support: every codes.txt code both ways (the harness is runtime/parametric/harness.py).

    SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run binary> python3 run_codes.py --out DIR [--only CODE]     # writes DIR/results.json and DIR/faithfulness.json
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
GEN = HERE.parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime.parametric.harness import Harness, main, table_row, with_description

PKG = HERE / "dowel-flanged-shaft-support"
GEN_ID = "misumi.sth.dowel-flanged-shaft-support"
EXTRA_REFUSALS = ["E-STHWRBK12-", "E-STHWRBK0", "E-STHWRBK09", "E-STHWRBK100", "E-STHWSBK16", "E-STHWRK", "E-SSTHWCBK12", "E-STHWCK12", "E-STHWRBKL16", "E-STHWIRBK12"]
# a built design switched to another row (a different family, a different screw size, a very different size) = that other code inserted directly
REBUILD = [("E-STHWRBK12", "E-STHWCBK30"), ("E-STHWCBK16", "E-SSTHWRK25"), ("E-STHWRBK30", "E-STHWRBK12")]
BLOCKED = [{"what": "a code that matches no template gets the engine's message, not the generator's (the stand-in asks an optional fn no_match(raw))",
            "needs": "needs #23175 (our draft, being finished) (optional no_match(raw) in generator.rhai)"},
           {"what": "a thread designation cannot come from a parameter: one thread feature per clamp screw size (M5 M6), suppressed per row",
            "needs": 'follow-up: parameter-driven threads and persistent thread references (outside #23175)'}]

def support_from(h, res, code):
    p = res["properties"]; mod = h.gen.module("dowel")
    return with_description(mod.Support, p["description"], code=code.strip().upper(), type=p["type_name"], family=p["family"], D=p["D"],
                            dims=table_row(h.pkg, "dims", p["D"]), material=p["material"], surface=p["surface"])

if __name__ == "__main__":
    h = Harness(GEN, PKG, "dowel-flanged-shaft-support.sc", support_from, EXTRA_REFUSALS, REBUILD, BLOCKED)
    main(h, GEN_ID, BLOCKED)
