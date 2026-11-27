"""Shared pieces of the end-to-end harness of the parametric MISUMI bushing generators (linear bushing, oil free bushing):
solidcraft-cli and Rhai calls, measurement, the code -> configuration row -> inserted part path, the spec check on a part that was
not built by the Python generator."""
from __future__ import annotations
import json, os, subprocess, tempfile
from pathlib import Path

def cli(CLI, cmds, src=None, save=None):
    d = Path(tempfile.mkdtemp())
    (d / "s.json").write_text(json.dumps({"commands": cmds}))
    a = [CLI, "run", str(d / "s.json"), "--results", "--json-out", str(d / "r.json"), "--quiet"]
    if src: a += ["--in", str(src)]
    if save: a += ["--save", str(save)]
    r = subprocess.run(a, capture_output=True, text=True)
    out = json.loads((d / "r.json").read_text()) if (d / "r.json").exists() else {}
    err = out.get("error") if isinstance(out, dict) else None
    res = out.get("results") if isinstance(out, dict) else out
    return res, (err or (r.stderr.strip() if r.returncode else None))

def rhai(RHAI, pkg, root, fn, *args):
    env = dict(os.environ, FT_ROOT=str(root))
    r = subprocess.run([RHAI, str(pkg), fn, *[json.dumps(a) for a in args]], capture_output=True, text=True, env=env)
    return json.loads(r.stdout) if r.stdout.strip() else {"ok": False, "reason": "script_error", "message": r.stderr}

def resolve(templates, RHAI, pkg, root, code):
    """code -> (('ok', result) | ('refused', kind, message), fields)"""
    m = templates.match(code.strip().upper())
    if m is None:
        return ("refused", "invalid", f"{code!r} matches none of the templates"), None
    fields = m[1]
    out = rhai(RHAI, pkg, root, "resolve", fields)
    if not out.get("ok"): return ("refused", out["reason"], out["message"]), fields
    return ("ok", out["value"]), fields

def measure(run_measure, sc_path, out_dir, tag):
    r = run_measure(sc_path, [{"command": "inspect.measure", "params": {}}], str(out_dir), tag)
    m = r[0]; b = m["bodies"]
    lo = [min(x["bbox"]["min"][i] for x in b) for i in range(3)]; hi = [max(x["bbox"]["max"][i] for x in b) for i in range(3)]
    return {"bodies": len(b), "volume": m["total"]["volume_mm3"], "area": m["total"]["area_mm2"], "faces": m["total"]["faces"],
            "bbox": [round(h - l, 4) for l, h in zip(lo, hi)], "names": [x["name"] for x in b]}

def subst(o, old, new):
    """The spec check names the body after the code (the Python build does); the inserted body keeps the model's own name, the component is
    named after the code: rename the `body` references only."""
    if isinstance(o, dict): return {k: (new if k == "body" and v == old else subst(v, old, new)) for k, v in o.items()}
    if isinstance(o, list): return [subst(v, old, new) for v in o]
    return o

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
