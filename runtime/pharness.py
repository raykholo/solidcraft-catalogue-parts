"""Helpers shared by the parametric harnesses (vendors/<v>/<s>/<g>/parametric/run_codes.py): run solidcraft-cli on a command list,
call a generator package's Rhai through runtime/rhai-run, measure a design, and run a generator's own src/check.py against an inserted
part whose body has another name than the Python build's.

    cli(cmds, src=None, save=None) -> (results, error)
    rhai(pkg, fn, *args)           -> {"ok": ..., "value": ...} | {"ok": False, "reason", "message"}
    measure(sc, out_dir, tag)      -> {bodies, volume, area, faces, bbox, threads, names}
    spec_check(check_module, part, host_sc, out_dir, body_name, code) -> {rows, failed}
"""
from __future__ import annotations
import json, os, subprocess, tempfile
from pathlib import Path
from runtime import sc as scrun
from runtime.check import run_measure

ROOT = Path(__file__).resolve().parent.parent
RHAI = os.environ.get("RHAI_RUN", "rhai-run")

def cli(cmds, src=None, save=None):
    d = Path(tempfile.mkdtemp())
    (d / "s.json").write_text(json.dumps({"commands": cmds}))
    a = [scrun.CLI, "run", str(d / "s.json"), "--results", "--json-out", str(d / "r.json"), "--quiet"]
    if src: a += ["--in", str(src)]
    if save: a += ["--save", str(save)]
    r = subprocess.run(a, capture_output=True, text=True)
    out = json.loads((d / "r.json").read_text()) if (d / "r.json").exists() else {}
    err = out.get("error") if isinstance(out, dict) else None
    res = out.get("results") if isinstance(out, dict) else out
    return res, (err or (r.stderr.strip() if r.returncode else None))

def rhai(pkg, fn, *args):
    env = dict(os.environ, FT_ROOT=str(ROOT))
    r = subprocess.run([RHAI, str(pkg), fn, *[json.dumps(a) for a in args]], capture_output=True, text=True, env=env)
    return json.loads(r.stdout) if r.stdout.strip() else {"ok": False, "reason": "script_error", "message": r.stderr}

def measure(sc_path, out_dir, tag, threads=True):
    cmds = [{"command": "inspect.measure", "params": {}}] + ([{"command": "model.threads", "params": {}}] if threads else [])
    r = run_measure(sc_path, cmds, str(out_dir), tag)
    m = r[0]; b = m["bodies"]
    lo = [min(x["bbox"]["min"][i] for x in b) for i in range(3)]; hi = [max(x["bbox"]["max"][i] for x in b) for i in range(3)]
    th = sorted((round(t["start"], 3), round(t["end"], 3)) for t in (r[1]["threads"] if threads else []))
    return {"bodies": len(b), "volume": m["total"]["volume_mm3"], "area": m["total"]["area_mm2"], "faces": m["total"]["faces"],
            "bbox": [round(h - l, 4) for l, h in zip(lo, hi)], "threads": th, "names": [x["name"] for x in b]}

def subst(o, old, new):
    """The spec check names the body after the code (the Python build does); the inserted body keeps the model's own name:
    rename the `body` references only."""
    if isinstance(o, dict): return {k: (new if k == "body" and v == old else subst(v, old, new)) for k, v in o.items()}
    if isinstance(o, list): return [subst(v, old, new) for v in o]
    return o

def spec_check(mod, part, host_sc, out, body, code):
    """Run `mod.check(part, host_sc, out)` with every body reference renamed from `code` to `body`."""
    orig = mod.run_measure
    mod.run_measure = lambda sc, cmds, o, name: orig(sc, subst(cmds, code, body), o, name)
    try:
        R = mod.check(part, host_sc, str(out))
    finally:
        mod.run_measure = orig
    bad = [r for r in R.rows if not r[0]]
    return {"rows": len(R.rows), "failed": [f"{r[1]}: spec {r[2]} got {r[3]}" for r in bad]}
