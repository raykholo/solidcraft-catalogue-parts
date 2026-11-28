#!/usr/bin/env python3
"""Convert harness results to the shared faithfulness schema."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from runtime.parametric.results import write_faithfulness

BLOCKED = [{'what': 'free parameter values on an inserted link (insert_design parameters ignored; set_link_parameters unknown)', 'needs': 'needs #23175 (our draft, being finished)'}, {'what': 'a cosmetic thread created after a cross cut stops at the cut (the Python build gives [0, 6.984]); the parametric model places the threads before the wrench cuts, so they keep their full length; the solid is identical', 'needs': 'follow-up: tangency-labs/solidcraft#23507'}]

if __name__ == "__main__":
    write_faithfulness(sys.argv[1], sys.argv[2], 'misumi.hfs.extrusion', BLOCKED, 'extrusion')
