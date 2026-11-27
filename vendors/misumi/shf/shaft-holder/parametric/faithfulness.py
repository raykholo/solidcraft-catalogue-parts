#!/usr/bin/env python3
"""Convert harness results to the shared faithfulness schema."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from runtime.parametric.results import write_faithfulness

BLOCKED = [{'what': 'free parameter values on an inserted link (insert_design parameters ignored; set_link_parameters unknown): the height H of a code is set in a row of a working copy of the model', 'needs': 'needs #23175 (our draft, being finished)'}]

if __name__ == "__main__":
    write_faithfulness(sys.argv[1], sys.argv[2], 'misumi.shf.shaft-holder', BLOCKED, 'description')
