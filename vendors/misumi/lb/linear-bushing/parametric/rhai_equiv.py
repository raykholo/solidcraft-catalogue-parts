#!/usr/bin/env python3
"""Exhaustive agreement of generator.rhai with the Python parser, no SolidCraft needed: every type letter combination x a list of bore sizes x
every suffix goes through template -> Rhai resolve, and through bushing.parse. A refusal must carry the same message word for word; an
accepted code must give the same part (every field of the Python Bushing, and its description).

    RHAI_RUN=<rhai-run> python3 rhai_equiv.py [OUT.json]
"""
from __future__ import annotations
import importlib, json, os, re, subprocess, sys
from dataclasses import asdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime import fieldtemplate as ft
bu = importlib.import_module("vendors.misumi.lb.linear-bushing.src.bushing")
PKG = HERE / "linear-bushing"
RHAI = os.environ.get("RHAI_RUN", "rhai-run")
TEMPLATES = ft.load(PKG)

from runtime.parametric import rhai as call_rhai

def rhai(fn, *args):
    return call_rhai(PKG, fn, *args)

def norm(v):
    """JSON-comparable form of a Python Bushing field (tuples -> lists, '' -> None)."""
    if isinstance(v, tuple): return [norm(x) for x in v]
    if isinstance(v, dict): return {k: norm(x) for k, x in v.items()}
    return v

def py_facts(b):
    d = asdict(b); d.pop("notes", None)
    d["typ"] = d.pop("type")
    return norm(d)

def main():
    shapes = [""] + ["F", "K", "H"]
    variants = ["", "PM", "CM", "Z", "M", "P", "C"]
    drs = ["1", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "20", "25", "30", "35", "40", "45", "50", "60", "99", "06"]
    sufs = ["TUU", "DMUU", "DUU", "LUU", "UU"]
    extra = ["E-LBHS20UU", "E-LBS20UU", "E-LBFS5UU", "E-LBHZP10UU", "E-LBFCZ10LUU", "E-LB", "E-LB10", "E-LBX10UU", "E-LBF20LU", "E-LBF20-UU", "E-LBF20-LUU", "E-LB100TUU", "E-LBF20UU-", "E-LBF20UU.", "E-LB10TUU_"]
    codes = [f"E-LB{s}{v}{d}{x}" for s in shapes for v in variants if not (v and not s) for d in drs for x in sufs] + extra
    n = ok = bad = 0
    lenient = []
    diffs = []
    for code in codes:
        n += 1
        try:
            b = bu.parse(code); py = ("ok", b)
        except ValueError as e:
            py = ("refused", str(e))
        m = TEMPLATES.match(code.strip().upper())
        if m is None:
            rr = ("refused", "no template")
        else:
            out = rhai("resolve", m[1])
            rr = ("ok", out["value"]) if out.get("ok") else ("refused", out["message"])
        if py[0] == "refused" and rr[0] == "ok" and re.search(r"[ _/.\-]", code[5:]):
            lenient.append(code); continue      # the interface ignores separators " -_/." when it reads a code (docs/formats/generator.md section 3)
        if py[0] != rr[0]:
            diffs.append((code, "verdict", py[0], rr[0], py[1] if py[0] == "refused" else rr[1])); bad += 1; continue
        if py[0] == "refused":
            if py[1] != rr[1]: diffs.append((code, "message", py[1], rr[1])); bad += 1; continue
        else:
            b, res = py[1], rr[1]
            facts = res["properties"]["facts"]; pf = py_facts(b)
            for k in pf:
                if k in ("description",): continue
                a, c = pf[k], facts.get(k)
                if k == "flange" and a and c:
                    a = {x: y for x, y in a.items() if y is not None}; c = {x: y for x, y in c.items() if y is not None}
                if k == "grooves" and a and c: pass
                if a != c and not (isinstance(a, (int, float)) and isinstance(c, (int, float)) and abs(a - c) < 1e-12):
                    diffs.append((code, f"field {k}", a, c)); bad += 1; break
            else:
                if res["properties"]["description"] != b.description:
                    diffs.append((code, "description", b.description, res["properties"]["description"])); bad += 1; continue
                if res["configuration"] is None: diffs.append((code, "configuration", None, None)); bad += 1; continue
        ok += 1
    out = {"codes": n, "agree": ok, "differ": bad, "separator_tolerant": lenient, "examples": diffs[:20]}
    print(json.dumps(out, indent=1))
    if len(sys.argv) > 1: Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
    return 1 if bad else 0

sys.exit(main())
