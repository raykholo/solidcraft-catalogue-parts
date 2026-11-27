#!/usr/bin/env python3
"""Convert guideway reports through the shared faithfulness writer."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import gw_model as gm
from runtime.parametric.results import write_faithfulness

S = gm.SERIES[sys.argv[1]]
blocked = [
    {"what": "free parameter values on an inserted link (insert_design `parameters` is ignored silently; component.set_link_parameters is unknown): the instance file is a copy of the design with the values set",
     "needs": "needs #23175 (our draft, being finished)"},
    {"what": "a thread designation cannot come from a parameter: one hole feature per designation (" + ", ".join(gm.feature_names(S, gm.blocks_of(S))[4]) + "), all but the row's own suppressed",
     "needs": "follow-up: parameter-driven thread designations (outside #23175)"},
    {"what": "feature-pattern copies are named Body<N>, not Block 1..n: the spec check reads the blocks by position (the harness renames them)",
     "needs": "follow-up: feature-pattern body names (outside #23175)"}]
write_faithfulness(sys.argv[2], sys.argv[3], S.gid, blocked, "guideway")
