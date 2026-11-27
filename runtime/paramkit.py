"""Shared pieces of the parametric generator proofs that follow the HFS extrusion layout (the LHB housings use them): running solidcraft-cli,
building a parametric model in two stages (geometry, then the configuration table and its rules), the Rhai host, measuring, the spec check on
an inserted part, a working-copy row for a code, rebuilds of a free parameter, and the faithfulness.json writer.

A generator's parametric/run_codes.py describes itself with a `Gen` and calls `main(gen)`:
    python3 run_codes.py --out DIR            every codes.txt code both ways (needs SC_CLI and RHAI_RUN)  -> DIR/results.json
    python3 run_codes.py --rhai-only          no SolidCraft: only the refusals (Rhai against the Python message) and the descriptions
"""
from __future__ import annotations
import argparse, base64, json, os, shutil, subprocess, sys, tempfile, traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from runtime import fieldtemplate as ft, sc as scrun                      # noqa: E402
from runtime.check import run_measure                                       # noqa: E402

CLI = scrun.CLI
RHAI = os.environ.get("RHAI_RUN", "rhai-run")

# ------------------------------------------------------------------------------------------------ solidcraft-cli
def cli(cmds, src=None, save=None, workdir=None):
    """Run a command list; -> (results, error or None). Never exits."""
    d = Path(workdir or tempfile.mkdtemp())
    d.mkdir(parents=True, exist_ok=True)
    script, res = d / "s.json", d / "r.json"
    if res.exists(): res.unlink()
    script.write_text(json.dumps({"commands": cmds}))
    a = [CLI, "run", str(script), "--results", "--json-out", str(res), "--quiet"]
    if src: a += ["--in", str(src)]
    if save: a += ["--save", str(save)]
    r = subprocess.run(a, capture_output=True, text=True)
    out = json.loads(res.read_text()) if res.exists() else {}
    err = out.get("error") if isinstance(out, dict) else None
    results = out.get("results") if isinstance(out, dict) else out
    if err is None and r.returncode:
        err = (r.stderr.strip() or r.stdout.strip())[-1500:]
    return results, err

def cli_or_exit(cmds, src=None, save=None, workdir=None, what="solidcraft-cli"):
    res, err = cli(cmds, src, save, workdir)
    if err:
        sys.exit(f"{what} failed: {json.dumps(err)[:2500]}")
    return res

# ------------------------------------------------------------------------------------------------ building the model
def feature_ids(cmds, res):
    """Feature ids by name from the creating commands' replies (rules take ids, not names)."""
    ids = {}
    for c, r in zip(cmds, res):
        nm = c["params"].get("name")
        if c["command"] == "sketch.create" and isinstance(r, dict): ids[nm] = r.get("sketch")
        elif isinstance(r, dict) and r.get("feature") is not None and nm and c["command"].startswith("solid."): ids[nm] = r["feature"]
    return ids

def build_model(pkg: Path, model: str, cmds, columns, feature_cols, rows, rules_fn, first_row):
    """Stage 1: `cmds` (user parameters, geometry, suppression). Stage 2: the configuration table (columns = parameters and features, one
    row each, `rows` = [(name, {"param:x": "...", "suppress:Feature": bool})]), the rules (`rules_fn(ids)`, features by id) and the first row
    activated. Stage 3: the row SolidCraft seeds ("Default") is dropped when it can be."""
    wd = Path(tempfile.mkdtemp()); pkg.mkdir(parents=True, exist_ok=True)
    res = cli_or_exit(cmds, save=wd / "stage1.sc", workdir=wd / "a", what="model, stage 1")
    ids = feature_ids(cmds, res)
    cfg = [{"command": "config.configure", "params": {"params": columns, "features": feature_cols}}]
    cfg += [{"command": "config.row", "params": {"name": n, "values": v}} for n, v in rows]
    cfg += [{"command": "config.rule", "params": {"rules": rules_fn(ids)}}, {"command": "config.activate", "params": {"row": first_row}}]
    cli_or_exit(cfg, src=wd / "stage1.sc", save=wd / "stage2.sc", workdir=wd / "b", what="model, stage 2 (configuration table)")
    r, err = cli([{"command": "config.row", "params": {"name": "Default", "delete": True}}], src=wd / "stage2.sc", save=pkg / model, workdir=wd / "c")
    if err:
        print(f"note: the seeded Default row stays ({json.dumps(err)[:300]})")
        shutil.copy(wd / "stage2.sc", pkg / model)
    shutil.rmtree(wd, ignore_errors=True)
    return ids

def write_csv(path: Path, header, rows):
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(header); w.writerows(rows)

def package_files_json(pkg: Path, out: Path):
    """Every file of the package (the built .sc included) as base64 in one JSON file: CI uploads *.json, so the built model can be committed."""
    files = {str(p.relative_to(pkg)): base64.b64encode(p.read_bytes()).decode() for p in sorted(pkg.rglob("*")) if p.is_file()}
    out.write_text(json.dumps({"package": pkg.name, "files": files}))

# ------------------------------------------------------------------------------------------------ the generator under test
@dataclass
class Gen:
    gid: str                                   # misumi.lhb.tall-housing
    sample: str                                # a code that finds the generator through its [declares]
    pkg: Path                                  # parametric/<name>/
    model: str                                 # <name>.sc
    part_from_result: Callable                 # (runner, res, code) -> the object the generator's src/check.py takes, built from the Rhai result
    extra_refusals: list = field(default_factory=list)
    rebuilds: list = field(default_factory=list)      # (base code, parameter, expression, direct code)
    probes: dict = field(default_factory=dict)        # label -> function(host, wc) -> command list
    blocked: list = field(default_factory=list)
    free_param: str = ""                       # for the "cannot express" probes
    free_value: str = ""

def rhai(pkg, fn, *args):
    env = dict(os.environ, FT_ROOT=str(ROOT))
    r = subprocess.run([RHAI, str(pkg), fn, *[json.dumps(a) for a in args]], capture_output=True, text=True, env=env)
    return json.loads(r.stdout) if r.stdout.strip() else {"ok": False, "reason": "script_error", "message": r.stderr}

def tables_of(pkg: Path):
    """tables/*.csv of the package as {name: {key: row}}, cells typed as the Python generators read them (runtime.table.num)."""
    from runtime.table import read_csv, num
    out = {}
    for p in sorted((pkg / "tables").glob("*.csv")):
        rows = read_csv(p)
        first = next(iter(rows[0])) if rows else "key"
        out[p.stem] = {r[first]: {k: num(v) for k, v in r.items()} for r in rows}
    return out

class Runner:
    def __init__(self, g: Gen):
        from runtime import registry
        self.g, self.reg = g, registry
        self.gen = registry.find(g.sample)
        self.templates = ft.load(g.pkg)
        self.tables = tables_of(g.pkg)

    def resolve(self, code):
        """code -> (('ok', result) | ('refused', kind, message))"""
        m = self.templates.match(code.strip())
        if m is None:
            return ("refused", "invalid", f"{code!r} matches none of the templates")
        out = rhai(self.g.pkg, "resolve", m[1])
        if not out.get("ok"):
            return ("refused", out["reason"], out["message"])
        return ("ok", out["value"])

    def python_message(self, code):
        try:
            self.gen.module("housing").parse(code); return "accepted"
        except ValueError as ex:
            return str(ex)

    def python_part(self, code, out):
        part, cmds = self.gen.build(code)
        path, _ = scrun.run_script(cmds, str(out), scrun.slug(code) + ".py")
        return part, path

    def measure(self, sc_path, out_dir, tag):
        r = run_measure(str(sc_path), [{"command": "inspect.measure", "params": {}}, {"command": "model.threads", "params": {}}], str(out_dir), tag)
        m = r[0]; b = m["bodies"]
        lo = [min(x["bbox"]["min"][i] for x in b) for i in range(3)]; hi = [max(x["bbox"]["max"][i] for x in b) for i in range(3)]
        th = sorted((round(t["start"], 3), round(t["end"], 3)) for t in r[1]["threads"])
        return {"bodies": len(b), "volume": m["total"]["volume_mm3"], "area": m["total"]["area_mm2"], "faces": m["total"]["faces"],
                "bbox": [round(h - l, 4) for l, h in zip(lo, hi)], "threads": th, "names": [x["name"] for x in b]}

    def code_row_cmds(self, res):
        vals = {f"param:{k}": v for k, v in res["parameters"].items()}
        name = res["properties"]["part_number"]
        return [{"command": "config.row", "params": {"name": name, "from": res["configuration"], "values": vals}}]

    def insert_code(self, res, out, tag):
        """Working copy of the package model + a row for the code; a host design inserts it by `configuration`. -> host path, copy path, error"""
        pr = res["properties"]; name = pr["part_number"]
        wc = out / f"{tag}.model.sc"
        r, err = cli(self.code_row_cmds(res), src=self.g.pkg / self.g.model, save=wc)
        if err: return None, None, f"config.row: {json.dumps(err)[:600]}"
        host = out / f"{tag}.host.sc"
        r, err = cli([{"command": "component.insert_design", "params": {"path": str(wc), "configuration": name, "name": name}},
                      {"command": "component.metadata.set", "params": {"component": name, "part_number": pr["part_number"], "description": pr["description"],
                                                                        "material": pr["material"]}},
                      {"command": "document.metadata.set", "params": {"values": {"part_number": pr["part_number"], "description": pr["description"]}}}], save=host)
        if err: return None, None, f"insert_design: {json.dumps(err)[:600]}"
        return host, wc, None

    def spec_check(self, part, host_sc, out, body):
        chk = self.gen.module("check")
        orig = chk.run_measure
        chk.run_measure = lambda sc, cmds, o, name: orig(sc, subst(cmds, part.code, body), o, name)
        try:
            R = chk.check(part, str(host_sc), str(out))
        finally:
            chk.run_measure = orig
        bad = [r for r in R.rows if not r[0]]
        return {"rows": len(R.rows), "failed": [f"{r[1]}: spec {r[2]} got {r[3]}" for r in bad]}

def subst(o, old, new):
    """The spec check names the body after the code (the Python build does); the inserted body keeps the model's own name: rename the
    `body` references only (the component is named after the code)."""
    if isinstance(o, dict): return {k: (new if k == "body" and v == old else subst(v, old, new)) for k, v in o.items()}
    if isinstance(o, list): return [subst(v, old, new) for v in o]
    return o

def say(*a):
    print(*a, flush=True)

# ------------------------------------------------------------------------------------------------ the run
def main(g: Gen):
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="."); ap.add_argument("--only"); ap.add_argument("--rhai-only", action="store_true")
    a = ap.parse_args()
    R = Runner(g)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True); work = Path(tempfile.mkdtemp())
    results = {"codes": [], "refusals": [], "parametric": [], "limits": {}, "descriptions": [], "roundtrip": []}
    bad = 0
    for cl in R.gen.codes():
        if a.only and cl.code != a.only: continue
        code = cl.code
        st = R.resolve(code)
        if not cl.valid:
            py = R.python_message(code)
            results["refusals"].append({"code": code, "python": py, "parametric": st[2] if st[0] == "refused" else "ACCEPTED", "kind": st[1] if st[0] == "refused" else None})
            say("reject", code, "same" if py == results["refusals"][-1]["parametric"] else "DIFFERS"); continue
        row = {"code": code}
        try:
            if st[0] == "refused":
                row["parametric"] = {"refused": st[2]}; results["codes"].append(row); say("valid", code, "REFUSED", st[2]); continue
            res = st[1]; row["configuration"] = res["configuration"]; row["parameters"] = res["parameters"]
            pypart, _ = R.gen.build(code)
            same = res["properties"]["description"] == pypart.description
            results["descriptions"].append({"code": code, "same": same, "python": pypart.description, "parametric": res["properties"]["description"]})
            f2 = rhai(g.pkg, "fields", res["configuration"], res["parameters"])
            printed = R.templates.print(f2["value"]) if f2.get("ok") else None
            st2 = R.resolve(printed) if printed else ("refused", "", "no code")
            results["roundtrip"].append({"code": code, "printed": printed, "same": st2[0] == "ok" and st2[1]["parameters"] == res["parameters"]
                                         and st2[1]["configuration"] == res["configuration"]})
            if a.rhai_only:
                row["parametric"] = {"rhai_only": True}; results["codes"].append(row)
                say("valid", code, "description", "same" if same else "DIFFERS", "roundtrip", printed); continue
            tag = scrun.slug(code)
            part, py_sc = R.python_part(code, work)
            row["python"] = R.measure(py_sc, work, tag + ".py")
            buf = R.gen.module("check").check(part, py_sc, str(work)); row["python_spec"] = {"rows": len(buf.rows), "failed": [r[1] for r in buf.rows if not r[0]]}
            host, wc, err = R.insert_code(res, work, tag)
            if err: row["parametric"] = {"error": err}; results["codes"].append(row); say("valid", code, "ERROR", err); continue
            row["parametric"] = R.measure(host, work, tag + ".pa")
            body = row["parametric"]["names"][0]
            pobj = g.part_from_result(R, res, code)
            row["parametric_spec"] = R.spec_check(pobj, host, work, body)
            say("valid", code, "py", row["python"]["volume"], row["python_spec"]["rows"], "param", row["parametric"]["volume"], row["parametric_spec"]["rows"],
                "failed", row["python_spec"]["failed"], row["parametric_spec"]["failed"])
        except Exception as ex:                                       # one code never stops the run
            row["parametric"] = {"error": "".join(traceback.format_exception_only(type(ex), ex)).strip()}
            say("valid", code, "EXCEPTION", traceback.format_exc()[-800:])
        results["codes"].append(row)
    if not a.only:
        for code in g.extra_refusals:
            st = R.resolve(code); py = R.python_message(code)
            results["refusals"].append({"code": code, "python": py, "parametric": st[2] if st[0] == "refused" else "ACCEPTED", "kind": st[1] if st[0] == "refused" else None, "extra": True})
            say("reject", code, "same" if py == results["refusals"][-1]["parametric"] else "DIFFERS")
        if not a.rhai_only:
            rebuild_and_probes(g, R, results, work)
    (out / "results.json").write_text(json.dumps(results, indent=1, default=str))
    say("wrote", out / "results.json")
    return results

def rebuild_and_probes(g: Gen, R: Runner, results, work):
    for base, param, expr, direct in g.rebuilds:
        ent = {"base": base, "param": param, "value": expr, "direct": direct}
        try:
            st = R.resolve(base); res = st[1]
            dres = R.resolve(direct)[1]
            wc = work / f"pc_{scrun.slug(base)}.sc"
            cmds = R.code_row_cmds(res) + [{"command": "config.activate", "params": {"row": res["properties"]["part_number"]}},
                                           {"command": "parameters.change", "params": {"name": param, "expression": expr}}]
            r, err = cli(cmds, src=g.pkg / g.model, save=wc)
            if err: ent["error"] = json.dumps(err)[:600]
            else:
                ent["changed"] = R.measure(wc, work, "pc.changed")
                hostd, _, e2 = R.insert_code(dres, work, "pcd_" + scrun.slug(direct))
                ent["direct_inserted"] = R.measure(hostd, work, "pc.direct")
                part, pysc = R.python_part(direct, work)
                ent["python"] = R.measure(pysc, work, "pc.py")
        except Exception as ex:
            ent["error"] = "".join(traceback.format_exception_only(type(ex), ex)).strip()
        say("rebuild", base, param, expr, ent.get("error", "ok"))
        results["parametric"].append(ent)
    # what 0.50.0 cannot express: the exact errors, for the README
    try:
        st = R.resolve(g.rebuilds[0][0]); res = st[1]
        host, wc, _ = R.insert_code(res, work, "lim")
        name = res["properties"]["part_number"]; meas = {"command": "inspect.measure", "params": {}}
        probes = {
            f"insert_design with a free `parameters` map ({g.free_param} {g.free_value})": ([{"command": "component.insert_design", "params": {"path": str(wc), "configuration": res["configuration"], "parameters": {g.free_param: g.free_value}, "name": "free"}}, meas], host),
            "component.set_link_parameters": ([{"command": "component.set_link_parameters", "params": {"component": name, "parameters": {g.free_param: g.free_value}}}], host),
            "generator.parse": ([{"command": "generator.parse", "params": {"generator": str(g.pkg), "code": g.rebuilds[0][0]}}], host),
            "generator.insert": ([{"command": "generator.insert", "params": {"generator": str(g.pkg), "code": g.rebuilds[0][0]}}], host),
            f"parameters.change {g.free_param} on the host design holding the linked part": ([{"command": "parameters.change", "params": {"name": g.free_param, "expression": g.free_value}}, meas], host),
            "unknown row": ([{"command": "component.insert_design", "params": {"path": str(wc), "configuration": "no-such-row"}}], host),
        }
        for label, (cmds, src) in {**probes, **{k: (f(res), wc) for k, f in g.probes.items()}}.items():
            r, err = cli(cmds, src=src)
            ent = {"error": err if isinstance(err, str) or err is None else json.dumps(err)[:700], "result": None}
            if r:
                last = r[-1]
                ent["result"] = ({"bbox_max": [b["bbox"]["max"] for b in last["bodies"]], "bodies": [b["name"] for b in last["bodies"]]}
                                 if isinstance(last, dict) and "bodies" in last and "body_count" in last else json.dumps(last)[:300])
            results["limits"][label] = ent
        r, err = cli([{"command": "config.table", "params": {}}], src=g.pkg / g.model)
        if r:
            t = r[0]; results["table"] = {"rows": len(t["rows"]), "columns": len(t["columns"]), "rules": len(t["rules"])}
    except Exception as ex:
        results["limits"]["(probes failed)"] = {"error": str(ex), "result": None}

# ------------------------------------------------------------------------------------------------ faithfulness.json
def write_faithfulness(results_path, out_path, gid, blocked):
    r = json.load(open(results_path))
    def m(x):
        if not x or "error" in x or "refused" in x or "volume" not in x: return {"error": True}
        return {"volume": x["volume"], "area": x["area"], "bbox": list(x["bbox"]), "faces": x["faces"], "bodies": x["bodies"]}
    def spec(s): return f"{s['rows'] - len(s['failed'])}/{s['rows']}" if s else None
    out = {"generator": gid,
           "valid": [{"code": c["code"], "python": m(c.get("python")), "parametric": m(c.get("parametric")),
                      "spec_python": spec(c.get("python_spec")), "spec_parametric": spec(c.get("parametric_spec"))} for c in r["codes"]],
           "rejects": [{"code": x["code"], "python": x["python"], "parametric": x["parametric"]} for x in r["refusals"]],
           "rebuild": [{"label": f"{p['base']} {p['param']} -> {p['value']} vs {p['direct']}", "direct": m(p.get("direct_inserted")), "changed": m(p.get("changed"))}
                       for p in r["parametric"]],
           "blocked": blocked}
    json.dump(out, open(out_path, "w"), indent=1)
    return out
