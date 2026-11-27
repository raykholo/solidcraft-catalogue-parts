"""Adapters for harnesses recording absolute bounding boxes and raw CLI results."""
import json
import subprocess
from pathlib import Path
from runtime import sc


def c(command, **params):
    return {"command": command, "params": params}


class AbsoluteHarness:
    def __init__(self, out):
        self.out = Path(out)

    def run(self, cmds, name, base=None, save=None, allow_fail=False):
        """solidcraft-cli run on `base` (a design) with these commands; -> (results or None, error or None)"""
        script = self.out / f"{name}.json"; res = self.out / f"{name}.res.json"
        script.write_text(json.dumps({"commands": cmds}))
        args = [sc.CLI, "run", str(script), "--results", "--json-out", str(res), "--quiet"]
        if base: args += ["--in", str(base)]
        if save: args += ["--save", str(save)]
        r = subprocess.run(args, capture_output=True, text=True)
        try: j = json.load(open(res))
        except Exception: j = None
        if r.returncode != 0:
            err = (j or {}).get("error") if isinstance(j, dict) else None
            return None, (err or {"error": (r.stdout + r.stderr)[-600:]})
        return j, None

    def measure(self, path, name):
        j, err = self.run([c("inspect.measure")], name, base=path)
        if err: return {"error": err}
        m = j[0]; b = m["bodies"]
        lo = [min(x["bbox"]["min"][i] for x in b) for i in range(3)]; hi = [max(x["bbox"]["max"][i] for x in b) for i in range(3)]
        return dict(vol=m["total"]["volume_mm3"], area=m["total"]["area_mm2"], faces=m["total"]["faces"], bodies=len(b), lo=lo, hi=hi)

def fmt(m):
    if not m or "error" in m: return "ERROR " + json.dumps((m or {}).get("error"))[:120]
    r = lambda v: f"{v:.3f}"
    return f"{m['vol']:.2f} / {m['area']:.2f} / [{r(m['lo'][0])}..{r(m['hi'][0])}] x [{r(m['lo'][1])}..{r(m['hi'][1])}] x [{r(m['lo'][2])}..{r(m['hi'][2])}] / {m['faces']}f {m['bodies']}b"

def same(a, b, tol=1e-6):
    if not a or not b or "error" in a or "error" in b: return False
    close = lambda x, y: abs(x - y) <= tol * max(1.0, abs(x), abs(y))
    return close(a["vol"], b["vol"]) and close(a["area"], b["area"]) and a["faces"] == b["faces"] and a["bodies"] == b["bodies"] \
        and all(close(a["lo"][i], b["lo"][i]) and close(a["hi"][i], b["hi"][i]) for i in range(3))



def summarize(m):
    """Keep absolute bounds and per-body names for guideway spec-check adapters."""
    bodies = m["bodies"]
    return dict(vol=m["total"]["volume_mm3"], area=m["total"]["area_mm2"], faces=m["total"]["faces"], bodies=len(bodies),
                lo=[min(b["bbox"]["min"][i] for b in bodies) for i in range(3)],
                hi=[max(b["bbox"]["max"][i] for b in bodies) for i in range(3)],
                names=[(b["name"], b["bbox"]) for b in bodies])
