#!/usr/bin/env python3
"""End-to-end proof: for every code of ../codes.txt (plus a battery of extra refusals), ordering code -> field template -> Rhai resolve ->
configuration row + parameters -> the parametric .sc configured and inserted -> measure + the generator's own spec check; and the
same code built by the Python generator and measured the same way. Writes results.json next to this file (or --out).

    SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run binary> python3 run_codes.py [--out DIR] [--only CODE]
"""
from __future__ import annotations
import argparse, importlib, json, os, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from runtime import fieldtemplate as ft, registry, sc as scrun
from runtime.check import run_measure
from runtime.parametric import bushing as pc
ob = importlib.import_module("vendors.misumi.ofb.oil-free-bushing.src.oilfree")
pycheck = importlib.import_module("vendors.misumi.ofb.oil-free-bushing.src.check")

PKG = HERE / "oil-free-bushing"
PKG_SC = PKG / "oil-free-bushing.sc"
RHAI = os.environ.get("RHAI_RUN", "rhai-run")
CLI = scrun.CLI
SWEEP = os.environ.get("SWEEP", "1") != "0"      # every valid code of the generator, not only the codes.txt lines
TEMPLATES = ft.load(PKG)
EXTRA_REFUSALS = ["C-MUFZ5-10-", "E-MUGZ10-15_", "C-MUBZ110-100", "C-MUBZ5-3", "C-MUBZ5-11", "C-MUBZ5-100", "C-MUBZU32-30", "C-MUBZU14-10", "C-MUFZU18-20", "C-MUFZ14-10",
                  "C-MUFZ5-15", "C-MUFZU6-8", "C-MUTSZ6-15", "C-MUTZ60-50", "C-MUTNZ20-90", "C-MUTNZ18-20", "E-MUGZ6-10", "E-MUGZ6-13",
                  "E-MUGZ14-20", "E-SHTZ35-40", "E-SHTNZ35-40", "E-SHBZ32-30", "E-SHBZ5-9", "E-SHFZ18-20", "E-SHFZ5-11", "E-MUSZ10-15", "E-MUKZ10-15", "E-MUCTZ10-15",
                  "E-MUIZ10-15", "C-MUIZ10-15", "E-MJBZ10-15", "E-MGFZ10-15", "E-MXBZ10-15", "C-MUFZ10", "C-MUFZ-10", "C-MUFZ5-", "C-MUTXZ10-20", "E-SHBZU10-12",
                  "E-MUGZ10-15-X", "E-LBF20LUU", "C-SHA10", "C-MUFZ5 10", "E-MUGZ"]
# free parameter changed on a built part: (code built, the length it changes to, code built directly)
REBUILDS = [("C-MUBZ20-30", "C-MUBZ20-40"), ("C-MUBZU12-20", "C-MUBZU12-25"), ("C-MUFZ5-10", "C-MUFZ5-12"), ("C-MUFZU16-12", "C-MUFZU16-30"), ("C-MUTZ6-10", "C-MUTZ6-20"),
            ("C-MUTSZ16-40", "C-MUTSZ16-25"), ("C-MUTNZ13-25", "C-MUTNZ13-35"), ("E-MUGZ10-15", "E-MUGZ10-20"), ("E-SHBZ10-12", "E-SHBZ10-25"), ("E-SHTZ25-35", "E-SHTZ25-60")]

def rz(code): return pc.resolve(TEMPLATES, RHAI, PKG, ROOT, code)
def measure(sc, out, tag): return pc.measure(run_measure, sc, out, tag)

def part_from(res):
    f = res["properties"]["facts"]
    return ob.Part(code=f["code"], type=f["typ"], family=f["family"], wall=f["wall"], material=f["material"], d=f["d"], L=f["L"], D=f["D"],
                   bore_class=f["bore_class"], od_class=f["od_class"], bore_tol=tuple(f["bore_tol"]), L_tol=tuple(f["L_tol"]), page=f["page"],
                   N=f["N"], flange=f["flange"])

def python_part(code, out):
    part, cmds = registry.build(code)
    path, _ = scrun.run_script(cmds, str(out), scrun.slug(code) + ".py")
    return part, path

def all_valid():
    """Every code the Python generator accepts: type x d x L 3..100."""
    out = []
    for typ in ob.TYPES:
        for d in sorted({d for t in ob.TABLES.values() for d in t}):
            for L in range(3, 101):
                code = f"{typ}{d}-{L}"
                try: ob.parse(code)
                except ValueError: continue
                out.append(code)
    return out

def py_message(code):
    try:
        ob.parse(code); return "accepted"
    except ValueError as ex: return str(ex)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); ap.add_argument("--only"); a = ap.parse_args()
    out = Path(a.out); work = Path(tempfile.mkdtemp()); out.mkdir(exist_ok=True)
    gen = registry.find("C-MUFZ5-10")
    results = {"codes": [], "refusals": [], "parametric": [], "limits": {}, "roundtrip": []}
    swept = []
    todo = [(cl.code, cl.valid) for cl in gen.codes() if not (a.only and cl.code != a.only)]
    if SWEEP and not a.only:
        have = {c for c, v in todo if v}
        swept = [c for c in all_valid() if c not in have]
        todo += [(c, True) for c in swept]
    for code, valid in todo:
        st, fields = rz(code)
        if not valid:
            results["refusals"].append({"code": code, "python": py_message(code), "parametric": st[2] if st[0] == "refused" else "ACCEPTED", "kind": st[1] if st[0] == "refused" else None})
            continue
        row = {"code": code, "sweep": code in swept}
        tag = scrun.slug(code)
        part, py_sc = python_part(code, work)
        row["python"] = measure(py_sc, work, tag + ".py")
        buf = pycheck.check(part, py_sc, str(work)); row["python_spec"] = {"rows": len(buf.rows), "failed": [r[1] for r in buf.rows if not r[0]]}
        if st[0] == "refused":
            row["parametric"] = {"refused": st[2]}; results["codes"].append(row); continue
        res = st[1]
        row["configuration"] = res["configuration"]; row["parameters"] = res["parameters"]
        host, wc, err = pc.insert_code(CLI, PKG_SC, code, res, work, tag)
        if err: row["parametric"] = {"error": err}; results["codes"].append(row); continue
        row["parametric"] = measure(host, work, tag + ".pa")
        b = part_from(res)
        row["parametric_spec"] = pc.spec_check(pycheck, b, host, work, row["parametric"]["names"][0])
        row["description_same"] = res["properties"]["description"] == part.description
        for q in (host, wc): Path(q).unlink(missing_ok=True)      # the working copy holds the whole model: keep the disk free over hundreds of codes
        # parameters -> fields -> code (generator.code) and the round trip
        f2 = pc.rhai(RHAI, PKG, ROOT, "fields", res["configuration"], res["parameters"])
        printed = TEMPLATES.print(f2["value"]) if f2.get("ok") else None
        st2, _ = rz(printed) if printed else (("refused", "", "no code"), None)
        results["roundtrip"].append({"code": code, "printed": printed, "same_parameters": st2[0] == "ok" and st2[1]["parameters"] == res["parameters"]
                                     and st2[1]["configuration"] == res["configuration"]})
        results["codes"].append(row)
    if not a.only:
        for code in EXTRA_REFUSALS:
            st, _ = rz(code)
            results["refusals"].append({"code": code, "python": py_message(code), "parametric": st[2] if st[0] == "refused" else "ACCEPTED",
                                        "kind": st[1] if st[0] == "refused" else None, "extra": True})
        # ---- a free parameter changed on a built part -----------------------------------------------------------------
        for base, direct in REBUILDS:
            st, _ = rz(base); res = st[1]
            std, _ = rz(direct); dres = std[1]
            wc = work / f"pc_{scrun.slug(base)}.sc"
            changes = {"blen": dres["parameters"]["blen"]}
            cmds = pc.code_row_cmds(base, res) + [{"command": "config.activate", "params": {"row": base.upper()}}]
            cmds += [{"command": "parameters.change", "params": {"name": n, "expression": v}} for n, v in changes.items()]
            r, err = pc.cli(CLI, cmds, src=PKG_SC, save=wc)
            ent = {"base": base, "changes": changes, "direct": direct, "error": err}
            if not err:
                ent["changed"] = measure(wc, work, "pc.changed")
                hostd, _, e2 = pc.insert_code(CLI, PKG_SC, direct, dres, work, "pcd_" + scrun.slug(direct))
                ent["direct_inserted"] = measure(hostd, work, "pc.direct")
                part, pysc = python_part(direct, work)
                ent["python"] = measure(pysc, work, "pc.py")
            results["parametric"].append(ent)
        # ---- what 0.50.0 cannot express: exact errors -------------------------------------------------------------------
        st, _ = rz("C-MUFZ5-10"); res = st[1]
        host, wc, _ = pc.insert_code(CLI, PKG_SC, "C-MUFZ5-10", res, work, "lim")
        meas = {"command": "inspect.measure", "params": {}}
        for k, c, src in [
            ("insert_design with a free `parameters` map (blen 12 mm)", [{"command": "component.insert_design", "params": {"path": str(wc), "configuration": "C-MUFZ-5", "parameters": {"blen": "12 mm"}, "name": "free"}}, meas], host),
            ("component.set_link_parameters", [{"command": "component.set_link_parameters", "params": {"component": "C-MUFZ5-10", "parameters": {"blen": "12 mm"}}}], host),
            ("generator.parse", [{"command": "generator.parse", "params": {"generator": str(PKG), "code": "C-MUFZ5-10"}}], host),
            ("generator.insert", [{"command": "generator.insert", "params": {"generator": str(PKG), "code": "C-MUFZ5-10"}}], host),
            ("blen 11 mm (not a printed length of the row) by an ordinary parameters.change", [{"command": "config.activate", "params": {"row": "C-MUFZ-5"}}, {"command": "parameters.change", "params": {"name": "blen", "expression": "11 mm"}}, meas], PKG_SC),
            ("blen 11 mm in a configuration row", [{"command": "config.row", "params": {"name": "bad", "from": "C-MUFZ-5", "values": {"param:blen": "11 mm"}}}], PKG_SC),
            ("unknown row", [{"command": "component.insert_design", "params": {"path": str(wc), "configuration": "no-such-row"}}], host)]:
            pc.probe(CLI, results["limits"], k, c, src)
        r, err = pc.cli(CLI, [{"command": "config.table", "params": {}}], src=PKG_SC)
        t = r[0]; results["table"] = {"rows": len(t["rows"]), "columns": len(t["columns"]), "rules": len(t["rules"])}
    (out / "results.json").write_text(json.dumps(results, indent=1, default=str))
    print("wrote", out / "results.json")

main()
