#!/usr/bin/env python3
"""Convert harness results to the shared faithfulness schema."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from runtime.parametric.results import write_faithfulness

BLOCKED = [{'what': 'thread designation (M3 / M4 / M5) from a parameter: one thread feature per size, suppressed per row', 'needs': 'follow-up: tangency-labs/solidcraft#9594'}]

if __name__ == "__main__":
    write_faithfulness(sys.argv[1], sys.argv[2], 'misumi.hnt.t-nut', BLOCKED, 'nut')
