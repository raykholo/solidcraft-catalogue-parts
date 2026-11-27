"""The faithfulness harness of a generator's parametric form (shared by the STH generators; the HFS and MG proofs have their own).

For every line of the generator's codes.txt (and some extra refusals):
  parametric: code -> field template (runtime/fieldtemplate.py) -> Rhai `resolve` (runtime/rhai-run) -> a configuration row of the
              package model -> the model inserted with `component.insert_design {configuration}` -> inspect.measure + the generator's
              own src/check.py spec check (run on the inserted part, on a support object rebuilt from the Rhai result and the package
              tables, never from the Python parser);
  python:     the same code built by the generator's Python builder and measured and checked the same way.
Rejected codes: the Python message and the Rhai message are compared word for word. Rebuild: a configuration row switched to another row
on a built design against that other code inserted directly. Writes results.json and faithfulness.json (tools/parametric-verdict schema).

    SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run binary> python3 -m runtime.parametric.harness ... (used through a generator's run_codes.py)
"""
from __future__ import annotations
import json, os, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from runtime import fieldtemplate as ft, registry, sc as scrun
from runtime.check import run_measure

RHAI = os.environ.get("RHAI_RUN", "rhai-run")
CLI = scrun.CLI




from runtime.parametric import cli, subst, rhai as call_rhai, measure as measure_core

def measure(sc_path, out_dir, tag):
    return measure_core(sc_path, out_dir, tag, threads=False, include_threads=False)

class Harness:
    def __init__(self, gen_dir, pkg_dir, model, support_from, extra_refusals, rebuild, blocked, check_module="check", extra_valid=()):
        self.gen = registry.Generator(gen_dir)
        self.pkg, self.model = Path(pkg_dir), Path(pkg_dir) / model
        self.support_from, self.extra, self.rebuild, self.blocked = support_from, extra_refusals, rebuild, blocked
        self.extra_valid = list(extra_valid)      # valid codes beyond codes.txt (a sweep that reaches every configuration row)
        self.pycheck = self.gen.module(check_module)
        self.templates = ft.load(self.pkg)

    # ---- Rhai ------------------------------------------------------------------------------------------------
    def rhai(self, fn, *args):
        return call_rhai(self.pkg, fn, *args)

    def resolve(self, code):
        """code -> (('ok', result) | ('refused', kind, message), fields)"""
        raw = code.strip()
        m = self.templates.match(raw.upper())
        if m is None:
            out = self.rhai("no_match", raw)       # proposal: the generator words the message of a code that matches no template
            if out.get("ok"): return ("refused", "invalid", out["value"]), None
            return ("refused", out.get("reason", "invalid"), out.get("message", "")), None
        out = self.rhai("resolve", m[1])
        if not out.get("ok"): return ("refused", out["reason"], out["message"]), m[1]
        return ("ok", out["value"]), m[1]

    def python_message(self, code):
        try:
            self.gen.build(code); return "accepted"
        except ValueError as ex:
            return str(ex)

    # ---- the two builds ---------------------------------------------------------------------------------------
    def python_part(self, code, out):
        part, cmds = self.gen.build(code)
        path, _ = scrun.run_script(cmds, str(out), scrun.slug(code) + ".py")
        return part, path

    def rows_summary(self, R):
        return {"rows": len(R.rows), "failed": [f"{r[1]}: spec {r[2]} got {r[3]}" for r in R.rows if not r[0]]}

    def insert(self, code, res, out, tag):
        """a host design inserting the package model with the row Rhai chose; the component is named after the code"""
        host = Path(out) / f"{tag}.host.sc"
        pr = res["properties"]; c = code.strip().upper()
        cmds = [{"command": "component.insert_design", "params": {"path": str(self.model), "configuration": res["configuration"], "name": c}}]
        if res.get("parameters"):
            cmds[0]["params"]["parameters"] = res["parameters"]
        cmds += [{"command": "component.metadata.set", "params": {"component": c, "part_number": pr["part_number"], "description": pr["description"],
                                                                 "material": f'{pr["material"]}; {pr["surface"]}'}},
                 {"command": "document.metadata.set", "params": {"values": {"part_number": pr["part_number"], "description": pr["description"]}}}]
        r, err = cli(cmds, save=host)
        return (None, f"insert_design: {err}") if err else (host, None)

    def spec_check(self, support, host_sc, out, body, tag):
        orig = self.pycheck.run_measure
        self.pycheck.run_measure = lambda sc, cmds, o, name: orig(sc, subst(cmds, support.code, body), o, name)
        try:
            R = self.pycheck.check(support, str(host_sc), str(out))
        finally:
            self.pycheck.run_measure = orig
        return R

    # ---- the run -----------------------------------------------------------------------------------------------
    def run(self, outdir, only=None):
        out = Path(outdir); out.mkdir(parents=True, exist_ok=True); work = Path(tempfile.mkdtemp())
        results = {"codes": [], "refusals": [], "rebuild": [], "roundtrip": []}
        from runtime.registry import CodeLine
        lines = self.gen.codes() + [CodeLine(c, True, {}, "row sweep") for c in self.extra_valid if c not in {x.code for x in self.gen.codes()}]
        for cl in lines:
            if only and cl.code != only: continue
            code = cl.code
            st, fields = self.resolve(code)
            if not cl.valid:
                results["refusals"].append({"code": code, "python": self.python_message(code),
                                            "parametric": st[2] if st[0] == "refused" else "ACCEPTED", "kind": st[1] if st[0] == "refused" else None})
                continue
            row = {"code": code}; tag = scrun.slug(code)
            part, py_sc = self.python_part(code, work)
            row["python"] = measure(py_sc, work, tag + ".py")
            R = self.pycheck.check(part, py_sc, str(work)); R.true("description text is the Python description (reference)", True, "-")
            row["python_spec"] = self.rows_summary(R)
            if st[0] == "refused":
                row["parametric"] = {"error": st[2]}; results["codes"].append(row); continue
            res = st[1]
            row["configuration"] = res["configuration"]
            host, err = self.insert(code, res, work, tag)
            if err: row["parametric"] = {"error": err}; results["codes"].append(row); continue
            row["parametric"] = measure(host, work, tag + ".pa")
            body = row["parametric"]["names"][0]
            sup = self.support_from(self, res, code)
            R2 = self.spec_check(sup, host, work, body, tag)
            R2.true("description text is the Python description (reference)", res["properties"]["description"] == part.description, "-",
                    "" if res["properties"]["description"] == part.description else f"rhai: {res['properties']['description']!r} python: {part.description!r}")
            row["parametric_spec"] = self.rows_summary(R2)
            printed = self.templates.print(fields, self.templates_index(code)) if fields is not None else None
            results["roundtrip"].append({"code": code, "printed": printed, "same": printed is not None and printed.upper() == code.upper()})
            results["codes"].append(row)
        if not only:
            for code in self.extra:
                st, _ = self.resolve(code)
                results["refusals"].append({"code": code, "python": self.python_message(code), "parametric": st[2] if st[0] == "refused" else "ACCEPTED",
                                            "kind": st[1] if st[0] == "refused" else None, "extra": True})
            for a, b in self.rebuild:
                ent = {"from": a, "to": b}
                sta, _ = self.resolve(a); stb, _ = self.resolve(b)
                wc = work / f"rb_{scrun.slug(a)}_{scrun.slug(b)}.sc"
                r, err = cli([{"command": "config.activate", "params": {"row": sta[1]["configuration"]}},
                              {"command": "config.activate", "params": {"row": stb[1]["configuration"]}}], src=self.model, save=wc)
                if err: ent["error"] = err if isinstance(err, str) else json.dumps(err)
                else:
                    ent["changed"] = measure(wc, work, "rb.changed")
                    h, e2 = self.insert(b, stb[1], work, "rbd_" + scrun.slug(b))
                    ent["direct"] = measure(h, work, "rb.direct")
                results["rebuild"].append(ent)
        (out / "results.json").write_text(json.dumps(results, indent=1, default=str))
        print("wrote", out / "results.json")
        return results

    def templates_index(self, code):
        m = self.templates.match(code.strip().upper())
        return m[0] if m else 0

def faithfulness(results, gen_id, blocked, path):
    from runtime.parametric.results import convert
    Path(path).write_text(json.dumps(convert(results, gen_id, blocked, "rows"), indent=1))

def table_row(pkg, name, key):
    """a row of the package's tables/<name>.csv with the cells typed as the Python generator types data/*.csv (empty is None)"""
    from runtime.table import read_csv, num
    for r in read_csv(Path(pkg) / "tables" / f"{name}.csv"):
        if r[next(iter(r))] == str(key):
            return {k: (v if k in ("source", "page", "status") else (None if v == "" else num(v))) for k, v in r.items()}
    raise KeyError(f"{name}.csv has no row {key}")

def with_description(cls, description, **kw):
    """a Support of the generator (its dataclass) whose description is the text Rhai made"""
    class S(cls):
        @property
        def description(self): return description
    return S(**kw)

def main(h: Harness, gen_id: str, blocked, argv=None):
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="."); ap.add_argument("--only"); ap.add_argument("--faithfulness")
    a = ap.parse_args(argv)
    results = h.run(a.out, a.only)
    if not a.only:
        faithfulness(results, gen_id, blocked, a.faithfulness or Path(a.out) / "faithfulness.json")

def report_md(results) -> str:
    """results.json -> the markdown tables of a generator's parametric README (python | parametric | spec check | equal?)"""
    f = lambda m: f"{m['volume']:.1f} / {m['area']:.1f} / {m['bbox'][0]:g}x{m['bbox'][1]:g}x{m['bbox'][2]:g} / {m['faces']}"
    def eq(a, b):
        c = lambda x, y: abs(x - y) <= 1e-6 * max(1.0, abs(x), abs(y))
        return c(a["volume"], b["volume"]) and c(a["area"], b["area"]) and a["bbox"] == b["bbox"] and a["faces"] == b["faces"] and a["bodies"] == b["bodies"]
    o = ["| code | row | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec check python | spec check parametric | equal |", "|---|---|---|---|---|---|---|"]
    for c in results["codes"]:
        p, q = c["python"], c.get("parametric", {})
        ps, qs = c["python_spec"], c.get("parametric_spec")
        if "volume" not in q:
            o.append(f"| {c['code']} | {c.get('configuration', '')} | {f(p)} | {q} | | | no |"); continue
        o.append(f"| {c['code']} | {c['configuration']} | {f(p)} | {f(q)} | {ps['rows'] - len(ps['failed'])}/{ps['rows']} | {qs['rows'] - len(qs['failed'])}/{qs['rows']} | {'yes' if eq(p, q) else 'NO'} |")
    o += ["", "| rejected code | python message | parametric message | same |", "|---|---|---|---|"]
    for r in results["refusals"]:
        o.append(f"| {r['code']} | {r['python']} | {r['parametric']} | {'yes' if r['python'] == r['parametric'] else 'no'} |")
    o += ["", "| row switched on a built design | to | switched vol / area / bbox / faces | direct code (inserted) | equal |", "|---|---|---|---|---|"]
    for e in results["rebuild"]:
        if e.get("error"): o.append(f"| {e['from']} | {e['to']} | ERROR {e['error']} | | |"); continue
        o.append(f"| {e['from']} | {e['to']} | {f(e['changed'])} | {f(e['direct'])} | {'yes' if eq(e['changed'], e['direct']) else 'NO'} |")
    o += ["", "| code | printed by the template from its fields | same |", "|---|---|---|"]
    for r in results["roundtrip"]:
        o.append(f"| {r['code']} | {r['printed']} | {'yes' if r['same'] else 'no'} |")
    return "\n".join(o)

if __name__ == "__main__" and len(sys.argv) == 3 and sys.argv[1] == "report":
    print(report_md(json.load(open(sys.argv[2]))))
