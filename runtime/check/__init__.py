"""The spec-check harness every generator uses: Rows (PASS/FAIL per dimension: spec, measured, tolerance, source id),
run_measure (solidcraft-cli on a built design) and small helpers over `model.faces` replies.

Each generator has a `src/check.py` with `check(part, sc_path, out_dir) -> Rows`; `tools/check` runs it for every code in codes.txt.
"""
from __future__ import annotations
import argparse, json, math, os, subprocess, sys
from runtime.sc import CLI

class Rows:
    def __init__(self): self.rows = []
    def num(self, name, spec, got, tol, src, note=""):
        ok = got is not None and abs(got - spec) <= tol
        self.rows.append((ok, name, f"{spec:.4g}", "-" if got is None else f"{got:.4f}", f"+-{tol:g}", src, note))
    def true(self, name, cond, src, note=""):
        self.rows.append((bool(cond), name, "yes", "yes" if cond else "no", "", src, note))
    def at_least(self, name, spec, got, src, note=""):
        self.rows.append((got >= spec, name, f">={spec}", str(got), "", src, note))
    def eq(self, name, spec, got, src, note=""):
        self.rows.append((spec == got, name, str(spec), str(got), "", src, note))
    def print(self):
        w = max(len(r[1]) for r in self.rows)
        for ok, n, s, g, t, src, note in self.rows:
            print(f"{'PASS' if ok else 'FAIL'}  {n:<{w}}  spec {s:>9}  got {g:>10}  {t:<8} [{src}] {note}".rstrip())
        bad = sum(1 for r in self.rows if not r[0])
        print(f"{len(self.rows) - bad}/{len(self.rows)} passed")
        return bad == 0

def run_measure(sc_path, cmds, out_dir, name):
    script = os.path.join(out_dir, name + ".measure.json")
    res = os.path.join(out_dir, name + ".measure.res.json")
    json.dump({"commands": cmds}, open(script, "w"), indent=1)
    r = subprocess.run([CLI, "run", script, "--in", sc_path, "--results", "--json-out", res, "--quiet"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("measure failed: " + r.stdout[-2000:] + r.stderr[-2000:])
    return json.load(open(res))

def faces_of(res_faces):
    return res_faces[0]["faces"]

def cyl_groups(faces):
    """radius (rounded) -> list of (origin, axis)"""
    g = {}
    for f in faces:
        c = f.get("cylinder")
        if c:
            g.setdefault(round(c["radius"], 3), []).append((c["origin"], c["axis"]))
    return g

def uniq(vals, tol=1e-3):
    out = []
    for v in sorted(vals):
        if not out or abs(v - out[-1]) > tol:
            out.append(v)
    return out

def find_key(o, k):
    if isinstance(o, dict):
        if k in o and isinstance(o[k], str): return o[k]
        for v in o.values():
            r = find_key(v, k)
            if r: return r
    elif isinstance(o, list):
        for v in o:
            r = find_key(v, k)
            if r: return r
    return None
