#!/usr/bin/env python3
"""Builds the parametric model of a guideway series with solidcraft-cli (SC_CLI) and writes <pkg>/<pkg>.sc.
    python3 gw_build.py SERIES PARAMETRIC_DIR OUTDIR
Writes the package tables and generator.toml (gw_package), runs gw_model's command list, then activates a few rows as a smoke test of the rules.
The range rule of `blocks` and `length` is first tried with column expressions as bounds; if 0.50.0 refuses that, the literal per-size rules."""
import json, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gw_model as m, gw_package

CLI = os.environ.get("SC_CLI", "solidcraft-cli")

def cli(script, res, base=None, save=None):
    args = [CLI, "run", str(script), "--results", "--json-out", str(res), "--quiet"]
    if base: args += ["--in", str(base)]
    if save: args += ["--save", str(save)]
    r = subprocess.run(args, capture_output=True, text=True)
    try: j = json.load(open(res))
    except Exception: j = None
    if r.returncode != 0:
        err = j.get("error") if isinstance(j, dict) else (j[-1] if isinstance(j, list) and j else None)
        return None, (err or (r.stdout + r.stderr)[-1500:])
    return j, None

def build(S: m.Series, par: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    pkg = gw_package.write(S, par)
    blocks = m.blocks_of(S); rows = m.row_list(S, blocks)
    names = [m.row_name(S, *r) for r in rows]
    smoke = [names[0], names[len(names) // 2], names[-1]]
    log = {}
    for mode in ("expr", "literal"):
        script = out / f"template-{mode}.json"
        script.write_text(json.dumps({"commands": m.commands(S, mode)}))
        sc = out / f"{pkg.name}-{mode}.sc"
        j, err = cli(script, out / f"template-{mode}.res.json", save=sc)
        if err:
            log[mode] = f"build failed: {json.dumps(err)[:600]}"; print(f"[{mode}] {log[mode]}", flush=True); continue
        ok = True
        for row in smoke:
            sm = out / f"smoke-{mode}.json"
            sm.write_text(json.dumps({"commands": [m.c("config.activate", row=row), m.c("inspect.measure")]}))
            j, err = cli(sm, out / f"smoke-{mode}.res.json", base=sc)
            if err: ok = False; log[mode] = f"row {row}: {json.dumps(err)[:600]}"; print(f"[{mode}] {log[mode]}", flush=True); break
        if ok:
            log[mode] = "ok"
            dest = pkg / f"{pkg.name}.sc"
            dest.write_bytes(sc.read_bytes())
            (out / "build.json").write_text(json.dumps(dict(rules=mode, log=log, rows=len(names), size=dest.stat().st_size), indent=1))
            print(f"built {dest} ({dest.stat().st_size} bytes, {len(names)} rows, rules: {mode})", flush=True)
            return mode
    raise SystemExit("no variant of the model builds: " + json.dumps(log))

if __name__ == "__main__":
    build(m.SERIES[sys.argv[1]], Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve())
