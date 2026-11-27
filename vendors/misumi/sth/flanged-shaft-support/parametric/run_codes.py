#!/usr/bin/env python3
"""End-to-end proof for misumi.sth.flanged-shaft-support: every codes.txt code both ways (the harness is runtime/parametric_harness.py).

    SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run binary> python3 run_codes.py --out DIR [--only CODE]     # writes DIR/results.json and DIR/faithfulness.json
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
GEN = HERE.parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime.parametric_harness import Harness, main, table_row, with_description

PKG = HERE / "flanged-shaft-support"
GEN_ID = "misumi.sth.flanged-shaft-support"
EXTRA_REFUSALS = ["E-STHRB8-", "E-STHRB0", "E-STHRB100", "E-STHRB6X", "E-STHRBN", "E-STHSBN10", "E-STHMRL8", "E-STHMRBL10", "E-STHWRBL8", "E-STHNRB10", "E-STHXSB10", "E-STHXRBL12", "E-SSTHRB12"]
# a built design switched to another row (a different series, shape or sleeve) = that other code inserted directly
REBUILD = [("E-STHRB6", "E-STHWCBL50"), ("E-STHWCBL50", "E-STHMRL16"), ("E-STHMRB8", "E-STHXC16"), ("E-STHXR40", "E-STHSBL16"),
           ("E-STHCNL35", "E-STHRBN8"), ("E-STHWSB8", "E-STHCBL30")]
BLOCKED = [{"what": "a code that matches no template gets the engine's message, not the generator's (the stand-in asks an optional fn no_match(raw))",
            "needs": "tangency-labs/solidcraft#23175 (optional no_match(raw) in generator.rhai)"},
           {"what": "a thread designation cannot come from a parameter: one thread feature per screw size (set screws M3 M4 M5 M6 M8; clamp screws M4 M5 M6 M8 M10), per station and screw, suppressed per row",
            "needs": "tangency-labs/solidcraft#23175 (solid.hole thread designation as an expression)"}]

def sweep_codes():
    """a code for every configuration row that codes.txt does not reach: the first type of that (series, shape, sleeve) the table allows"""
    import build
    from runtime.table import read_csv
    types = read_csv(GEN / "data" / "types.csv"); keys = {}
    for t in types:
        long = t["long"] == "1"; na = {x for x in t["not_applicable_d"].split("|") if x}
        for key in build.rows():
            series, rest = key.split("-", 1); fam = rest.split("-")[0]; D = key.rsplit("-", 1)[1]
            if series == t["series"] and fam == t["family"] and ("-long-" in "-" + rest) == long and D not in na:
                keys.setdefault(key, t["type"] + D)
    return keys

def support_from(h, res, code):
    p = res["properties"]; mod = h.gen.module("support")
    return with_description(mod.Support, p["description"], code=code.strip().upper(), type=p["type_name"], series=p["series"], family=p["family"], long=p["long"],
                            D=p["D"], dims=table_row(h.pkg, p["table"], p["D"]), material=p["material"], surface=p["surface"])

if __name__ == "__main__":
    sys.path.insert(0, str(HERE))
    h0 = Harness(GEN, PKG, "flanged-shaft-support.sc", support_from, [], [], [])
    covered = set()
    for cl in h0.gen.codes():
        if cl.valid:
            st, _ = h0.resolve(cl.code)
            if st[0] == "ok": covered.add(st[1]["configuration"])
    sweep = [code for key, code in sweep_codes().items() if key not in covered]
    h = Harness(GEN, PKG, "flanged-shaft-support.sc", support_from, EXTRA_REFUSALS, REBUILD, BLOCKED, extra_valid=sweep)
    main(h, GEN_ID, BLOCKED)
