#!/usr/bin/env python3
"""Convert harness results to the shared faithfulness schema."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from runtime.parametric.results import write_faithfulness

BLOCKED = [{'what': 'free parameter values on an inserted link (insert_design parameters ignored; set_link_parameters unknown)', 'needs': 'needs #23175 (our draft, being finished)'}, {'what': 'cosmetic thread shortened by a later wrench-hole cut (threads placed before the cuts; the solid is identical)', 'needs': 'follow-up: being filed (repro sent)'}]

if __name__ == "__main__":
    write_faithfulness(sys.argv[1], sys.argv[2], 'misumi.hfs.extrusion', BLOCKED, 'extrusion')
