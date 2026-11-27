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
import pcommon as pc
bu = importlib.import_module("vendors.misumi.lb.linear-bushing.src.bushing")
pycheck = importlib.import_module("vendors.misumi.lb.linear-bushing.src.check")

PKG = HERE / "linear-bushing"
PKG_SC = PKG / "linear-bushing.sc"
RHAI = os.environ.get("RHAI_RUN", "rhai-run")
CLI = scrun.CLI
SWEEP = os.environ.get("SWEEP", "1") != "0"      # every valid code of the generator, not only the codes.txt lines
TEMPLATES = ft.load(PKG)
EXTRA_REFUSALS = ["E-LBF20UU-", "E-LB10TUU_", "E-LB10UU", "E-LBF10TUU", "E-LBF1UU", "E-LBF20DUU1", "E-LBF14LUU", "E-LBFM20DUU", "E-LBFZ40UU", "E-LBFZ35LUU", "E-LBK35DUU", "E-LB26DUU",
                  "E-LBS10UU", "E-LBHS20UU", "E-LBFS5UU", "E-LB", "E-LBX10UU", "E-LBHZ40UU", "E-LBHM20DUU", "E-LBH13DUU", "E-LBH5LUU", "E-LBHM5UU", "E-LBH20TUU",
                  "E-LBFP35UU", "E-LBFP6DUU", "E-LBFPM20DMUU", "E-LBKP20DUU", "E-LBHPM20DMUU", "E-LBFC20UU", "E-LBKC20DUU", "E-LBKCM20DMUU", "E-LBHC50LUU",
                  "E-LBFC13LUU", "E-LBFC35DMUU", "E-LBHP13LUU", "E-LBHP50DMUU", "E-LBK20TUU"]
# free parameter changed on a built part: (code built, {parameter: new value from the direct code's row}, code built directly)
REBUILDS = [("E-LBF20UU", ("blen",), "E-LBF20LUU"), ("E-LBK16UU", ("blen",), "E-LBK16LUU"), ("E-LBHP16UU", ("blen",), "E-LBHP16LUU"),
            ("E-LBH10UU", ("blen",), "E-LBH10LUU"), ("E-LBF10UU", ("opp",), "E-LBFZ10UU"), ("E-LBHZ20UU", ("opp",), "E-LBH20UU"),
            ("E-LBK12DUU", ("plated",), "E-LBK12DMUU"), ("E-LB12DUU", ("plated",), "E-LB12DMUU")]

def rz(code): return pc.resolve(TEMPLATES, RHAI, PKG, ROOT, code)
def measure(sc, out, tag): return pc.measure(run_measure, sc, out, tag)

def bushing_from(res):
    f = res["properties"]["facts"]
    return bu.Bushing(code=f["code"], type=f["typ"], family=f["family"], series=f["series"], dr=f["dr"], D=f["D"], D_tol=f["D_tol"], L=f["L"],
                      L_tol=tuple(f["L_tol"]), dr_tol=tuple(f["dr_tol"]), plated=f["plated"], double=f["double"], counterbore=f["counterbore"],
                      layout=f["layout"], x0=f["x0"], page=f["page"], grooves=f["grooves"], flange=f["flange"])

def python_part(code, out):
    part, cmds = registry.build(code)
    path, _ = scrun.run_script(cmds, str(out), scrun.slug(code) + ".py")
    return part, path

def all_valid():
    """Every code the Python generator accepts: type letters x dr 1..60 x suffix."""
    out = []
    for typ in bu.TYPES:
        for dr in range(1, 61):
            for suf in ("TUU", "DMUU", "DUU", "LUU", "UU"):
                code = f"{typ}{dr}{suf}"
                try: bu.parse(code)
                except ValueError: continue
                out.append(code)
    return out

def py_message(code):
    try:
        bu.parse(code); return "accepted"
    except ValueError as ex: return str(ex)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); ap.add_argument("--only"); a = ap.parse_args()
    out = Path(a.out); work = Path(tempfile.mkdtemp()); out.mkdir(exist_ok=True)
    gen = registry.find("E-LB10TUU")
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
        b = bushing_from(res)
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
        for base, names, direct in REBUILDS:
            st, _ = rz(base); res = st[1]
            std, _ = rz(direct); dres = std[1]
            wc = work / f"pc_{scrun.slug(base)}.sc"
            changes = {n: (dres["parameters"][n] if n == "blen" else dres["parameters"][n]) for n in names}
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
        st, _ = rz("E-LBF20UU"); res = st[1]
        host, wc, _ = pc.insert_code(CLI, PKG_SC, "E-LBF20UU", res, work, "lim")
        meas = {"command": "inspect.measure", "params": {}}
        for k, c, src in [
            ("insert_design with a free `parameters` map (blen 35 mm)", [{"command": "component.insert_design", "params": {"path": str(wc), "configuration": "flanged_long-round-20", "parameters": {"blen": "55 mm"}, "name": "free"}}, meas], host),
            ("component.set_link_parameters", [{"command": "component.set_link_parameters", "params": {"component": "E-LBF20UU", "parameters": {"blen": "55 mm"}}}], host),
            ("generator.parse", [{"command": "generator.parse", "params": {"generator": str(PKG), "code": "E-LBF20UU"}}], host),
            ("generator.insert", [{"command": "generator.insert", "params": {"generator": str(PKG), "code": "E-LBF20UU"}}], host),
            ("blen 40 mm (not an allowed length of the row) by an ordinary parameters.change", [{"command": "config.activate", "params": {"row": "flanged_long-round-20"}}, {"command": "parameters.change", "params": {"name": "blen", "expression": "40 mm"}}, meas], PKG_SC),
            ("blen 40 mm in a configuration row", [{"command": "config.row", "params": {"name": "bad", "from": "flanged_long-round-20", "values": {"param:blen": "40 mm"}}}], PKG_SC),
            ("opp 1 in a row that has no opposite-counterbore type", [{"command": "config.row", "params": {"name": "bad2", "from": "flanged_medium-round-20", "values": {"param:opp": "1"}}}], PKG_SC),
            ("unknown row", [{"command": "component.insert_design", "params": {"path": str(wc), "configuration": "no-such-row"}}], host)]:
            pc.probe(CLI, results["limits"], k, c, src)
        r, err = pc.cli(CLI, [{"command": "config.table", "params": {}}], src=PKG_SC)
        t = r[0]; results["table"] = {"rows": len(t["rows"]), "columns": len(t["columns"]), "rules": len(t["rules"])}
    (out / "results.json").write_text(json.dumps(results, indent=1, default=str))
    print("wrote", out / "results.json")

main()
