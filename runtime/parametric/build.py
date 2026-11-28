"""Build the parametric model of a generator with solidcraft-cli (shared by the STH generators' parametric/build.py).

A model is drawn ONCE: user parameters, derived parameters, then the features as ordered UNITS (a sketch and its extrude, a cut, a hole).
The catalogue rows become configuration rows: every row gives the parameter cells (numbers, or expressions over other parameters) and
which features are suppressed; `rules(ids)` adds the limit and suppress-if rules (they name features by id, so the model is built in two
stages: stage 1 draws it and reads the ids from the replies, stage 2 writes the configuration table and the rules).

    spec = Spec(name="x", params=[(name, expr, unit, comment)], derived=[...], units=[Unit(...)], rows={key: Row(...)}, rules=fn)
    ids = build_model(spec, Path("out/pkg"), cli)      # writes out/pkg/<name>.sc
"""
from __future__ import annotations
from runtime.parametric import limit_rules
import json, shutil, subprocess, sys, tempfile
from dataclasses import dataclass, field
from pathlib import Path

@dataclass
class Unit:
    cmds: list                     # command dicts, in order
    names: list = field(default_factory=list)       # features of this unit that a row can suppress (sketch names and solid names)
    temp: bool = False             # an alternative that must be drawn with the other alternatives suppressed

@dataclass
class Row:
    cells: dict                    # parameter name -> number or expression text
    suppress: set                  # feature names suppressed in this row

@dataclass
class Spec:
    name: str
    params: list                   # (name, default expression, unit, comment): the columns of the table
    derived: list                  # (name, expression, unit, comment): follow the columns, not columns themselves
    units: list
    rows: dict
    rules: object = None           # fn(ids: {feature name: id}) -> [rule dicts]
    component: str = "part"
    first_values: bool = True      # draw with the first row's values; False: with the defaults of `params` (when no one row makes every feature valid)

def cell(v):
    if isinstance(v, float):
        return f"{v:.12g}"
    return str(v)

def run(cli, cmds, workdir, src=None, save=None):
    wd = Path(workdir)
    script, res = wd / "step.json", wd / "step.res.json"
    if res.exists(): res.unlink()
    script.write_text(json.dumps({"commands": cmds}))
    a = [cli, "run", str(script), "--results", "--json-out", str(res), "--quiet"]
    if src: a += ["--in", str(src)]
    if save: a += ["--save", str(save)]
    r = subprocess.run(a, capture_output=True, text=True)
    out = json.loads(res.read_text()) if res.exists() else {}
    if r.returncode != 0 or (isinstance(out, dict) and out.get("error")):
        err = out.get("error") if isinstance(out, dict) else out
        sys.exit(f"solidcraft-cli failed: {r.stderr[-1500:]}\n{json.dumps(err)[:2500]}")
    return out if isinstance(out, list) else out["results"]

def build_model(spec: Spec, pkg: Path, cli: str):
    pkg.mkdir(parents=True, exist_ok=True)
    wd = Path(tempfile.mkdtemp())
    first = next(iter(spec.rows.values()))
    cmds = []
    add = lambda c, **kw: cmds.append({"command": c, "params": kw})
    for n, e, u, c in spec.params:
        add("parameters.add", name=n, expression=str(e), unit=u, comment=c)
    for n, e, u, c in spec.derived:
        add("parameters.add", name=n, expression=e, unit=u, comment=c)
    # the default row's values drive the first drawing: set them before the features exist
    if spec.first_values:
        add("parameters.change", changes={n: cell(first.cells[n]) for n, *_ in spec.params if n in first.cells})
    add("component.create", name=spec.component)
    # Every unit is drawn active, so a later feature that picks a face (a thread on the outside of the sleeve) is picked on the geometry
    # that a row with the earlier cuts live has too. A `temp` unit (alternatives that exclude each other, such as one thread feature per
    # screw size on the same face) is suppressed right after it is drawn, so the alternatives never see one another. At the end the default
    # row's suppression is applied, in timeline order: the units it suppresses off, the temp units it keeps on.
    for u in spec.units:
        cmds.extend(u.cmds)
        if u.temp:
            for n in u.names:
                add("timeline.suppress", feature=n, suppressed=True)
    for u in spec.units:
        for n in u.names:
            if u.temp and n not in first.suppress:
                add("timeline.suppress", feature=n, suppressed=False)
            elif not u.temp and n in first.suppress:
                add("timeline.suppress", feature=n, suppressed=True)
    res = run(cli, cmds, wd, save=wd / "stage1.sc")
    ids = {}
    for c, r in zip(cmds, res):
        nm = c["params"].get("name")
        if c["command"] == "sketch.create": ids[nm] = r["sketch"]
        elif isinstance(r, dict) and r.get("feature") is not None and nm and c["command"].startswith("solid."): ids[nm] = r["feature"]
    feats = [n for u in spec.units for n in u.names]
    cols = [n for n, *_ in spec.params]
    cfg = [{"command": "config.configure", "params": {"params": cols, "features": feats}}]
    for key, row in spec.rows.items():
        vals = {f"param:{n}": cell(row.cells[n]) for n in cols if n in row.cells}
        for f in feats:
            vals[f"suppress:{f}"] = f in row.suppress
        cfg.append({"command": "config.row", "params": {"name": key, "values": vals}})
    if spec.rules:
        cfg.append({"command": "config.rule", "params": {"rules": limit_rules(spec.rules(ids))}})
    cfg.append({"command": "config.activate", "params": {"row": next(iter(spec.rows))}})
    run(cli, cfg, wd, src=wd / "stage1.sc", save=pkg / f"{spec.name}.sc")
    for bak in pkg.glob("*.bak"):
        bak.unlink()
    shutil.rmtree(wd, ignore_errors=True)
    return ids
