#!/usr/bin/env python3
"""results.json -> the markdown tables of README.md.  usage: report.py [RESULTS.json]"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from runtime.parametric import kit as pk
print(pk.report_md(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_name("results.json")))
