#!/usr/bin/env python3
"""results.json of run_codes.py -> faithfulness.json for tools/parametric-verdict.  usage: faithfulness.py RESULTS.json OUT.json"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[5]))
from runtime.parametric import kit as pk
from run_codes import GEN
pk.write_faithfulness(sys.argv[1], sys.argv[2], GEN.gid, GEN.blocked)
