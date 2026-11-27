#!/usr/bin/env python3
"""End-to-end proof: for every code of ../codes.txt (plus extra refusals), ordering code -> field template -> Rhai resolve ->
configuration row + parameters -> the parametric .sc configured and inserted -> measure + the generator's own spec check; and the same
code built by the Python generator and measured the same way. Writes results.json in --out.

    SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run binary> python3 run_codes.py [--out DIR] [--only CODE]
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime import fieldtemplate as ft, registry, sc as scrun
from runtime.check import run_measure
from runtime.table import read_csv, num

PKG = HERE / "scs-collar"
MODEL = PKG / "scs-collar.sc"
RHAI = os.environ.get("RHAI_RUN", "rhai-run")
CLI = scrun.CLI
GEN = registry.find("C-SCSAW12-10")
co, pycheck = GEN.module("collar"), GEN.module("check")
EXTRA_REFUSALS = ["C-SCSAW1210", "C-SCSAW123-4", "E-SCDJ12-1", "E-SCDJ1210", "E-SCSPD6-10", "E-SCSBNAW6", "C-SCSBNAW12-1", "X", "E-SCSPD", "C-SCNPAW6-10",
                  "E-SCSPD99", "C-SCSBNAW9-9", "C-SCSMAW30-10", "C-SCSGAW16-8", "E-PSCSPD7", "E-SCDJ40-14",
                  "E-SSCD4", "E-SCD12-", "E-SCSPD6-", "C-SCSAW-10", "C-SCSAW12-", "E-SCDJ12-10-"]
REBUILD = [("C-SCSAW16-10", 12, "C-SCSAW16-12"), ("C-SCNPAW16-10", 12, "C-SCNPAW16-12")]



TEMPLATES = ft.load(PKG)

from runtime.parametric import cli, rhai as call_rhai, measure as measure_core

def rhai(fn, *args):
    return call_rhai(PKG, fn, *args)

def measure(sc_path, out_dir, tag, threads=True):
    return measure_core(sc_path, out_dir, tag, threads=threads and False, include_threads=False)


def resolve(code):
    """code -> (('ok', result) | ('refused', kind, message), fields)"""
    m = TEMPLATES.match(code.strip().upper())
    if m is None:
        return ("refused", "invalid", f"{code!r} matches none of the templates"), None
    out = rhai("resolve", m[1])
    if not out.get("ok"): return ("refused", out["reason"], out["message"]), m[1]
    return ("ok", out["value"]), m[1]


def python_part(code, out):
    part, cmds = registry.build(code)
    path, _ = scrun.run_script(cmds, str(out), scrun.slug(code) + ".py")
    return part, path

T = PKG / "tables"
SIZES = {r["key"]: {k: num(v) for k, v in r.items() if k != "key"} for r in read_csv(T / "sizes.csv")}
BEAR = {r["key"]: {k: num(v) for k, v in r.items() if k != "key"} for r in read_csv(T / "bearing.csv")}
UREROWS = {r["key"]: {k: (num(v) if k != "Z" else v) for k, v in r.items() if k != "key"} for r in read_csv(T / "urethane.csv")}
TYPES = {r["type"]: r for r in read_csv(T / "types.csv")}

def collar_from(res, code):
    """The Collar / Bearing / Urethane the spec check needs, built from the Rhai result and the package's own tables (not from the Python parser)."""
    pr = res["properties"]; typ = pr["type_name"]; t = TYPES[typ]; key = res["configuration"]; c = code.strip().upper()
    if typ == "C-SCSBNAW":
        r = BEAR[key]
        return co.Bearing(code=c, type=typ, kind=t["kind"], D=r["D"], Ds=r["Ds"], b=r["b"], B=r["B"], D1=r["D1"], M=r["M"], material=t["material"], surface=t["surface"])
    if typ.startswith("E-"):
        r = UREROWS[key]
        return co.Urethane(code=c, type=typ, family=r["family"], kind=t["kind"], D=r["D"], B=r["B"], D1=r["D1"], B1=r["B1"], t=r["t"], M=r["M"], d=r["d"], R=r["R"],
                           W=r["W"], X=r["X"], Y=r["Y"], Z=r["Z"], material=t["material"], surface=t["surface"], accessory=t["accessory"], damper=t["damper"])
    r = SIZES[key]
    return co.Collar(code=c, type=typ, kind=t["kind"], D=r["D"], B=r["B"], D1=r["D1"], M=r["M"], material=t["material"], surface=t["surface"],
                     P=r["P"], S=r["S"], d1=r["d1"], d2=r["d2"], t=r["t"])

def code_row_cmds(code, res):
    vals = {f"param:{k}": v for k, v in res["parameters"].items()}
    return [{"command": "config.row", "params": {"name": code.strip().upper(), "from": res["configuration"], "values": vals}}]

from runtime.parametric import subst

from runtime.parametric import spec_check as check_inserted

def spec_check(h, host_sc, out, body):
    return check_inserted(pycheck, h, host_sc, out, body, h.code)

def insert_code(code, res, out, tag):
    """Working copy of the package model + a row for the code; a host design inserts it by `configuration`. -> host .sc path, working copy, error"""
    wc = out / f"{tag}.model.sc"
    r, err = cli(code_row_cmds(code, res), src=MODEL, save=wc)
    if err: return None, None, f"config.row: {err}"
    host = out / f"{tag}.host.sc"
    pr = res["properties"]; c = code.strip().upper()
    r, err = cli([{"command": "component.insert_design", "params": {"path": str(wc), "configuration": c, "name": c}},
                  {"command": "component.metadata.set", "params": {"component": c, "part_number": pr["part_number"], "description": pr["description"],
                                                                    "material": f'{pr["material"]}; {pr["surface"]}'}},
                  {"command": "document.metadata.set", "params": {"values": {"part_number": pr["part_number"], "description": pr["description"]}}}], save=host)
    if err: return None, None, f"insert_design: {err}"
    return host, wc, None

def pymsg(code):
    try:
        co.parse(code); return "accepted"
    except ValueError as ex: return str(ex)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); ap.add_argument("--only"); a = ap.parse_args()
    out = Path(a.out); work = Path(tempfile.mkdtemp()); out.mkdir(parents=True, exist_ok=True)
    results = {"codes": [], "refusals": [], "parametric": [], "limits": {}, "roundtrip": []}
    for cl in GEN.codes():
        if a.only and cl.code != a.only: continue
        code = cl.code
        st, fields = resolve(code)
        if not cl.valid:
            results["refusals"].append({"code": code, "python": pymsg(code), "parametric": st[2] if st[0] == "refused" else "ACCEPTED", "kind": st[1] if st[0] == "refused" else None})
            continue
        row = {"code": code}
        tag = scrun.slug(code)
        part, py_sc = python_part(code, work)
        row["python"] = measure(py_sc, work, tag + ".py")
        buf = pycheck.check(part, py_sc, str(work)); row["python_spec"] = {"rows": len(buf.rows), "failed": [r[1] for r in buf.rows if not r[0]]}
        if st[0] == "refused":
            row["parametric"] = {"refused": st[2]}; results["codes"].append(row); continue
        res = st[1]
        row["configuration"] = res["configuration"]; row["parameters"] = res["parameters"]
        row["description_same"] = res["properties"]["description"] == part.description
        host, wc, err = insert_code(code, res, work, tag)
        if err: row["parametric"] = {"error": err}; results["codes"].append(row); continue
        row["parametric"] = measure(host, work, tag + ".pa")
        row["parametric_spec"] = spec_check(collar_from(res, code), host, work, row["parametric"]["names"][0])
        f2 = rhai("fields", res["configuration"], res["parameters"])
        printed = TEMPLATES.print(f2["value"]) if f2.get("ok") else None
        st2, _ = resolve(printed) if printed else (("refused", "", "no code"), None)
        results["roundtrip"].append({"code": code, "printed": printed, "same_parameters": st2[0] == "ok" and st2[1]["parameters"] == res["parameters"]
                                     and st2[1]["configuration"] == res["configuration"]})
        results["codes"].append(row)
    if not a.only:
        for code in EXTRA_REFUSALS:
            st, _ = resolve(code)
            results["refusals"].append({"code": code, "python": pymsg(code), "parametric": st[2] if st[0] == "refused" else "ACCEPTED", "kind": st[1] if st[0] == "refused" else None, "extra": True})
        # ---- stays parametric: change the width on the configured design, compare with the code built directly ----------------
        for base, newb, direct_code in REBUILD:
            st, _ = resolve(base); res = st[1]
            dst, _ = resolve(direct_code); dres = dst[1]
            wc = work / f"pc_{scrun.slug(base)}.sc"
            cmds = [{"command": "config.activate", "params": {"row": res["configuration"]}},
                    {"command": "parameters.change", "params": {"name": "ring_h", "expression": f"{newb} mm"}},
                    {"command": "parameters.change", "params": {"name": "ht", "expression": f"{newb} mm"}}]
            r, err = cli(cmds, src=MODEL, save=wc)
            ent = {"base": base, "param": "width", "value": f"{newb} mm", "direct": direct_code, "error": err}
            if not err:
                ent["changed"] = measure(wc, work, "pc.changed")
                hostd, _, e2 = insert_code(direct_code, dres, work, "pcd_" + scrun.slug(direct_code))
                ent["direct_inserted"] = measure(hostd, work, "pc.direct")
                part, pysc = python_part(direct_code, work)
                ent["python"] = measure(pysc, work, "pc.py")
            results["parametric"].append(ent)
        # ---- what 0.50.0 cannot express / what the rules enforce: exact messages ------------------------------------------
        st, _ = resolve("C-SCSAW12-10"); res = st[1]
        host, wc, _ = insert_code("C-SCSAW12-10", res, work, "lim")
        meas = {"command": "inspect.measure", "params": {}}
        probes = {
            "insert_design with a free `parameters` map (ring_h 12 mm)": ([{"command": "component.insert_design", "params": {"path": str(wc), "configuration": "C-SCSAW-12-10", "parameters": {"ring_h": "12 mm"}, "name": "free"}}, meas], host),
            "component.set_link_parameters": ([{"command": "component.set_link_parameters", "params": {"component": "C-SCSAW12-10", "parameters": {"ring_h": "12 mm"}}}], host),
            "generator.parse": ([{"command": "generator.parse", "params": {"generator": str(PKG), "code": "C-SCSAW12-10"}}], host),
            "split = 1 on the slit row (rules switch the second clamp screw on, the gap replaces the slit)": ([{"command": "config.row", "params": {"name": "t", "from": "C-SCSAW-12-10", "values": {"param:split": "1", "param:cut_w": "0.5 mm"}}}, {"command": "config.activate", "params": {"row": "t"}}, meas], MODEL),
            "unknown row": ([{"command": "component.insert_design", "params": {"path": str(MODEL), "configuration": "no-such-row"}}], host),
        }
        for k, (c, src) in probes.items():
            r, err = cli(c, src=src)
            ent = {"error": err if isinstance(err, str) or err is None else json.dumps(err), "result": None}
            if r:
                last = r[-1]
                ent["result"] = ({"bodies": [b["name"] for b in last["bodies"]], "volume": last["total"]["volume_mm3"]} if isinstance(last, dict) and "bodies" in last else json.dumps(last)[:200])
            results["limits"][k] = ent
        r, err = cli([{"command": "config.table", "params": {}}], src=MODEL)
        t = r[0]; results["table"] = {"rows": len(t["rows"]), "columns": len(t["columns"]), "rules": len(t["rules"])}
    (out / "results.json").write_text(json.dumps(results, indent=1, default=str))
    print("wrote", out / "results.json")

main()
