#!/usr/bin/env python3
"""Convert harness results to the shared faithfulness schema."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from runtime.parametric.results import write_faithfulness

BLOCKED = [{'what': 'free parameter values on an inserted link (insert_design parameters ignored; set_link_parameters unknown)', 'needs': 'needs #23175 (our draft, being finished)'}, {'what': 'thread designation from a parameter (M2.6 has no coarse pitch; one hole feature per size and host face, 46 features)', 'needs': 'follow-up: tangency-labs/solidcraft#9594'}, {'what': 'unordered option set with arguments: each option at most once, object value; the code needs repeats and order', 'needs': 'follow-up after #23175: an ordered bag/list option kind beside set(...)'}]

if __name__ == "__main__":
    write_faithfulness(sys.argv[1], sys.argv[2], 'misumi.sfj.shaft', BLOCKED, 'shaft')
