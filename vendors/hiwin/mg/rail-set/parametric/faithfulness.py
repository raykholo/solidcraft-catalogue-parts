#!/usr/bin/env python3
"""Convert HIWIN harness results to the shared faithfulness schema."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from runtime.parametric.results import write_faithfulness

if __name__ == "__main__":
    write_faithfulness(sys.argv[1], sys.argv[2], "hiwin.mg.rail-set", [], "hiwin")
