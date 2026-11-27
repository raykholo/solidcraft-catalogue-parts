"""Shared pieces of the end-to-end harness of the parametric MISUMI bushing generators (linear bushing, oil free bushing):
solidcraft-cli and Rhai calls, measurement, the code -> configuration row -> inserted part path, the spec check on a part that was
not built by the Python generator."""
from __future__ import annotations
import json, os, subprocess, tempfile
from pathlib import Path



from runtime.parametric import cli as call_cli, rhai as call_rhai, measure as call_measure, subst

def cli(CLI, cmds, src=None, save=None):
    return call_cli(cmds, src, save)

def rhai(RHAI, pkg, root, fn, *args):
    return call_rhai(pkg, fn, *args)

def measure(run_measure, sc_path, out_dir, tag):
    return call_measure(sc_path, out_dir, tag, threads=False, include_threads=False)

def resolve(templates, RHAI, pkg, root, code):
    """code -> (('ok', result) | ('refused', kind, message), fields)"""
    m = templates.match(code.strip().upper())
    if m is None:
        return ("refused", "invalid", f"{code!r} matches none of the templates"), None
    fields = m[1]
    out = rhai(RHAI, pkg, root, "resolve", fields)
    if not out.get("ok"): return ("refused", out["reason"], out["message"]), fields
    return ("ok", out["value"]), fields



def spec_check(pycheck, part, host_sc, out, body):
    orig = pycheck.run_measure
    pycheck.run_measure = lambda sc, cmds, o, name: orig(sc, subst(cmds, part.code, body), o, name)
    try:
        R = pycheck.check(part, host_sc, str(out))
    finally:
        pycheck.run_measure = orig
    return {"rows": len(R.rows), "failed": [f"{r[1]}: spec {r[2]} got {r[3]}" for r in R.rows if not r[0]]}

def code_row_cmds(code, res):
    vals = {f"param:{k}": v for k, v in res["parameters"].items()}
    return [{"command": "config.row", "params": {"name": code, "from": res["configuration"], "values": vals}}]

def insert_code(CLI, pkg_sc, code, res, out, tag):
    """Working copy of the package model + a row for the code; a host design inserts it by `configuration`. -> host .sc, working copy, error"""
    code = code.strip().upper()
    wc = Path(out) / f"{tag}.model.sc"
    r, err = cli(CLI, code_row_cmds(code, res), src=pkg_sc, save=wc)
    if err: return None, None, f"config.row: {err}"
    host = Path(out) / f"{tag}.host.sc"
    pr = res["properties"]
    r, err = cli(CLI, [{"command": "component.insert_design", "params": {"path": str(wc), "configuration": code, "name": code}},
                       {"command": "component.metadata.set", "params": {"component": code, "part_number": pr["part_number"], "description": pr["description"],
                                                                         "material": pr["material"]}},
                       {"command": "document.metadata.set", "params": {"values": {"part_number": pr["part_number"], "description": pr["description"]}}}], save=host)
    if err: return None, None, f"insert_design: {err}"
    return host, wc, None

def probe(CLI, results, name, cmds, src):
    r, err = cli(CLI, cmds, src=src)
    ent = {"error": err if isinstance(err, str) or err is None else json.dumps(err), "result": None}
    if r:
        last = r[-1]
        ent["result"] = ({"bbox_max": [b["bbox"]["max"] for b in last["bodies"]], "bodies": [b["name"] for b in last["bodies"]]}
                         if isinstance(last, dict) and "bodies" in last and "body_count" in last else json.dumps(last)[:200])
    results[name] = ent
