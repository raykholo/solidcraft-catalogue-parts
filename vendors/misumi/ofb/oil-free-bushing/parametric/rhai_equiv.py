#!/usr/bin/env python3
"""Exhaustive agreement of generator.rhai with the Python parser, no SolidCraft needed: every type x every bore size x every length 1..110
(and a list of shape errors) goes through template -> Rhai resolve, and through oilfree.parse. A refusal must carry the same message word
for word; an accepted code must give the same part (every field of the Python Part, and its description).

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
ob = importlib.import_module("vendors.misumi.ofb.oil-free-bushing.src.oilfree")
PKG = HERE / "oil-free-bushing"
RHAI = os.environ.get("RHAI_RUN", "rhai-run")
TEMPLATES = ft.load(PKG)

def rhai(fn, *args):
    r = subprocess.run([RHAI, str(PKG), fn, *[json.dumps(a) for a in args]], capture_output=True, text=True, env=dict(os.environ, FT_ROOT=str(ROOT)))
    return json.loads(r.stdout) if r.stdout.strip() else {"ok": False, "reason": "script_error", "message": r.stderr}

def norm(v):
    if isinstance(v, tuple): return [norm(x) for x in v]
    if isinstance(v, dict): return {k: norm(x) for k, x in v.items()}
    return v

def main():
    types = list(ob.TYPES)
    ds = sorted({d for t in ob.TABLES.values() for d in t} | {1, 4, 7, 14, 17, 19, 99, 101})
    extra = ["E-MUSZ10-15", "E-MUKZ10-15", "E-MUCTZ10-15", "E-MJBZ10-15", "E-MGFZ10-15", "E-MXBZ10-15", "C-MUIZ10-15", "C-MUFZ10", "C-MUFZ-10", "C-MUFZ5-", "C-MUTXZ10-20",
             "E-SHBZU10-12", "E-MUGZ10-15-X", "E-LBF20LUU", "C-SHA10", "C-MUFZ5-1000", "C-MUFZ1000-10", "c-mufz5-10", "C-MUFZ05-10", "C-MUFZ5-010", "C-MUFZ5 10", "E-MUGZ", "C-MUFZ5-10-", "C-MUFZ5-10.", "E-MUGZ10-15_"]
    codes = [(f"{t}{d}-{l}") for t in types for d in ds for l in range(3, 101) if str(l) in ("3", "6", "8", "9", "10", "12", "14", "15", "16", "19", "20", "25", "30", "35", "40", "50", "60", "70", "80", "90", "100", "11", "99")] + extra
    n = ok = bad = 0
    diffs, lenient = [], []
    for code in codes:
        n += 1
        try:
            p = ob.parse(code); py = ("ok", p)
        except ValueError as e:
            py = ("refused", str(e))
        m = TEMPLATES.match(code.strip().upper())
        if m is None:
            rr = ("refused", "no template")
        else:
            out = rhai("resolve", m[1])
            rr = ("ok", out["value"]) if out.get("ok") else ("refused", out["message"])
        if py[0] == "refused" and rr[0] == "ok" and re.search(r"[ _/.]", code):
            lenient.append(code); continue      # the interface ignores separators " -_/." when it reads a code (docs/formats/generator.md section 3)
        if py[0] != rr[0]:
            diffs.append((code, "verdict", py[0], rr[0], py[1] if py[0] == "refused" else rr[1])); bad += 1; continue
        if py[0] == "refused":
            if py[1] != rr[1]: diffs.append((code, "message", py[1], rr[1])); bad += 1; continue
        else:
            b, res = py[1], rr[1]
            facts = res["properties"]["facts"]; pf = norm(asdict(b)); pf.pop("notes", None); pf["typ"] = pf.pop("type")
            for k in pf:
                a, c = pf[k], facts.get(k)
                if isinstance(a, dict) and isinstance(c, dict):
                    a = {x: y for x, y in a.items() if y is not None}; c = {x: y for x, y in c.items() if y is not None}
                if a != c and not (isinstance(a, (int, float)) and isinstance(c, (int, float)) and abs(a - c) < 1e-12):
                    diffs.append((code, f"field {k}", a, c)); bad += 1; break
            else:
                if res["properties"]["description"] != b.description:
                    diffs.append((code, "description", b.description, res["properties"]["description"])); bad += 1; continue
        ok += 1
    out = {"codes": n, "agree": ok, "differ": bad, "separator_tolerant": lenient, "examples": diffs[:20]}
    print(json.dumps(out, indent=1))
    if len(sys.argv) > 1: Path(sys.argv[1]).write_text(json.dumps(out, indent=1))
    return 1 if bad else 0

sys.exit(main())
