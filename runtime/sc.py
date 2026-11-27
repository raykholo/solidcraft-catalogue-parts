"""Run solidcraft-cli on a command list, and find the SolidCraft binaries (shared by tools/ and the generators' checks).

SC_VER (default 0.50.0) picks the release; SC_CLI / SC_APP name the binaries; SC_RELEASES is a folder holding
<ver>/solidcraft-<ver>-linux-x86_64/bin/; otherwise `solidcraft-cli` and `solidcraft` are looked up on PATH.
"""
from __future__ import annotations
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VER = os.environ.get("SC_VER", "0.50.0")

def _find(binary: str, env: str, ver: str = VER) -> str:
    if os.environ.get(env):
        return os.environ[env]
    rel = os.environ.get("SC_RELEASES")
    if rel:
        p = Path(rel).expanduser() / ver / f"solidcraft-{ver}-linux-x86_64" / "bin" / binary
        if p.exists():
            return str(p)
    return shutil.which(binary) or binary

CLI = _find("solidcraft-cli", "SC_CLI")
APP = _find("solidcraft", "SC_APP")

def slug(code: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in code.strip())

def run_script(cmds, out_dir, name, extra=()):
    """Build `cmds` (a SolidCraft command list) into out_dir/name.sc; returns (sc path, results path)."""
    os.makedirs(out_dir, exist_ok=True)
    script = os.path.join(out_dir, name + ".json")
    with open(script, "w") as f:
        json.dump({"commands": cmds}, f, indent=1)
    sc = os.path.join(out_dir, name + ".sc")
    res = os.path.join(out_dir, name + ".results.json")
    r = subprocess.run([CLI, "run", script, "--save", sc, "--results", "--json-out", res, "--quiet", *extra],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout[-3000:] + r.stderr[-3000:])
        if os.path.exists(res):
            sys.stderr.write(open(res).read()[-3000:])
        raise SystemExit(f"solidcraft-cli failed ({r.returncode}) for {name}")
    return sc, res
