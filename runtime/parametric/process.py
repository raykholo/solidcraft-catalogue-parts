"""Shared model-build command execution, preserving legacy failure diagnostics."""
import json
import subprocess
import sys
from pathlib import Path
from runtime import sc as scrun

def run_build(cmds, src=None, save=None, workdir=None, detailed=False, executable=None):
    wd = Path(workdir)
    script = wd / "step.json"; res = wd / "step.res.json"
    script.write_text(json.dumps({"commands": cmds}))
    a = [executable or scrun.CLI, "run", str(script), "--results", "--json-out", str(res), "--quiet"]
    if src: a += ["--in", str(src)]
    if save: a += ["--save", str(save)]
    r = subprocess.run(a, capture_output=True, text=True)
    out = json.loads(res.read_text()) if res.exists() else {}
    if r.returncode != 0 or (isinstance(out, dict) and out.get("error")):
        err = out.get("error") if isinstance(out, dict) else out
        if detailed:
            done = len(out.get("results", [])) if isinstance(out, dict) else 0
            where = cmds[done] if done < len(cmds) else None
            sys.exit(f"solidcraft-cli failed after {done} commands, at {json.dumps(where)[:600]}:\n{r.stderr[-1500:]}\n{json.dumps(err)[:1500]}")
        sys.exit(f"solidcraft-cli failed: {r.stderr[-1500:]}\n{json.dumps(err)[:1500]}")
    return out if isinstance(out, list) else out["results"]


def drop_default(source, target, workdir, executable):
    """Try removing the seeded Default row, retaining the original design on refusal."""
    import shutil
    wd = Path(workdir)
    (wd / "del.json").write_text(json.dumps({"commands": [{"command": "config.row", "params": {"name": "Default", "delete": True}}]}))
    result = subprocess.run([executable, "run", str(wd / "del.json"), "--in", str(source), "--save", str(target), "--quiet"], capture_output=True, text=True)
    if result.returncode != 0:
        print("note: the Default row stays:", result.stderr[-300:], file=sys.stderr)
        shutil.copy(source, target)
