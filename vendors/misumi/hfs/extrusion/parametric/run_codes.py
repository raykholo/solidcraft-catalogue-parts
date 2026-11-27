#!/usr/bin/env python3
"""End-to-end proof: for every code of ../codes.txt (plus a battery of extra refusals), ordering code -> field template -> Rhai resolve ->
configuration row + parameters -> the parametric .sc configured and inserted -> measure + the generator's own spec check; and the
same code built by the Python generator and measured the same way. Writes results.json next to this file (or --out).

    SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run binary> python3 run_codes.py [--out DIR] [--only CODE]
"""
from __future__ import annotations
import argparse, copy, json, os, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime import fieldtemplate as ft, registry, sc as scrun
from runtime.check import run_measure
from vendors.misumi.hfs.extrusion.src import ext, check as pycheck

PKG = HERE / "hfs-extrusion"
RHAI = os.environ.get("RHAI_RUN", "rhai-run")
CLI = scrun.CLI
EXTRA_REFUSALS = ["HFS5-2020", "HFS5-2020-LTP", "HFS7-2020-100", "HFS5-6060-100", "HFSY5-2040-100", "NFSF5-2020-100", "XYZ5-2020-100", "HFS5-2020-100-SC-SC",
                  "HFS5-2020-2000-SC", "HFS5-2020-100-LHP", "HFS5-2020-100-LCP", "HFS6-3030-100-RWV", "HFS5-2020-100-RWV-X5", "HFS5-2020-100-X5",
                  "HFS5-2020-100-FL", "HFS5-2020-30-LTP-RTP", "HFS5-2020-100-LCH-LCV", "HFS5-2020-100-LWH-RWH-RCH", "KHFS5-2020-1000-LTP", "HFS5-2020-4001"]



TEMPLATES = ft.load(PKG)

from runtime.parametric import cli, rhai as call_rhai, measure as measure_core

def rhai(fn, *args):
    return call_rhai(PKG, fn, *args)

def measure(sc_path, out_dir, tag, threads=True):
    return measure_core(sc_path, out_dir, tag, threads=threads)


def resolve(code):
    """code -> (('ok', result) | ('refused', kind, message), fields)"""
    m = TEMPLATES.match(code.strip().upper())
    if m is None:
        return ("refused", "invalid", f"{code!r} matches none of the templates"), None
    fields = m[1]
    out = rhai("resolve", fields)
    if not out.get("ok"): return ("refused", out["reason"], out["message"]), fields
    return ("ok", out["value"]), fields


def python_part(code, out):
    part, cmds = registry.build(code)
    path, _ = scrun.run_script(cmds, str(out), scrun.slug(code) + ".py")
    return part, path

def extrusion_from(res, code):
    """The ext.Extrusion the spec check needs, rebuilt from the Rhai result (not from the Python parser)."""
    p, pr = res["parameters"], res["properties"]
    wrench = {}
    for side, k in (("L", "wl"), ("R", "wr")):
        rows = int(p[f"{k}_rows"])
        if rows:
            wrench[side] = dict(rows=rows, orient="HV"[int(p[f"{k}_dir"])], shift=float(p[f"{k}_shift"].split()[0]),
                                axis_name="horizontal" if p[f"{k}_dir"] == "0" else "vertical")
    return ext.Extrusion(code=code.strip().upper(), fixed=p["fixed"] == "1", type=pr["type_name"], material=pr["material"], surface=pr["surface"],
                         profile=p["profile"], length=float(p["length"].split()[0]),
                         end_tap=("L" if p["tap_l"] == "1" else "") + ("R" if p["tap_r"] == "1" else ""), wrench=wrench,
                         wrench_d=float(p["wh_d"].split()[0]) if "wh_d" in p else 0.0, tolerance=pr["tolerance"], notes=list(pr["notes"]))

def code_row_cmds(code, res):
    vals = {f"param:{k}": v for k, v in res["parameters"].items()}
    return [{"command": "config.row", "params": {"name": code, "from": res["configuration"], "values": vals}}]

from runtime.parametric import subst

from runtime.parametric import spec_check as check_inserted

def spec_check(e, host_sc, out, body):
    return check_inserted(pycheck, e, host_sc, out, body, e.code)

def insert_code(code, res, out, tag):
    """Working copy of the package model + a row for the code; a host design inserts it by `configuration`. -> host .sc path, body name"""
    wc = out / f"{tag}.model.sc"
    r, err = cli(code_row_cmds(code, res), src=PKG / "hfs-extrusion.sc", save=wc)
    if err: return None, None, f"config.row: {err}"
    host = out / f"{tag}.host.sc"
    pr = res["properties"]
    r, err = cli([{"command": "component.insert_design", "params": {"path": str(wc), "configuration": code.strip().upper(), "name": code.strip().upper()}},
                  {"command": "component.metadata.set", "params": {"component": code.strip().upper(), "part_number": pr["part_number"], "description": pr["description"],
                                                                    "material": f'{pr["material"]}, {pr["surface"]}'}},
                  {"command": "document.metadata.set", "params": {"values": {"part_number": pr["part_number"], "description": pr["description"]}}}], save=host)
    if err: return None, None, f"insert_design: {err}"
    return host, wc, None

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); ap.add_argument("--only"); a = ap.parse_args()
    out = Path(a.out); work = Path(tempfile.mkdtemp()); out.mkdir(exist_ok=True)
    gen = registry.find("HFS5-2020-100")
    results = {"codes": [], "refusals": [], "parametric": [], "limits": {}, "roundtrip": []}
    for cl in gen.codes():
        if a.only and cl.code != a.only: continue
        code = cl.code
        st, fields = resolve(code)
        if not cl.valid:
            try:
                ext.parse(code); py = "accepted"
            except ValueError as ex: py = str(ex)
            results["refusals"].append({"code": code, "python": py, "parametric": st[2] if st[0] == "refused" else "ACCEPTED", "kind": st[1] if st[0] == "refused" else None})
            continue
        row = {"code": code}
        tag = scrun.slug(code)
        part, py_sc = python_part(code, work)
        row["python"] = measure(py_sc, work, tag + ".py")
        row["python_spec"] = {"rows": None}
        buf = pycheck.check(part, py_sc, str(work)); row["python_spec"] = {"rows": len(buf.rows), "failed": [r[1] for r in buf.rows if not r[0]]}
        if st[0] == "refused":
            row["parametric"] = {"refused": st[2]}; results["codes"].append(row); continue
        res = st[1]
        row["configuration"] = res["configuration"]; row["parameters"] = res["parameters"]
        host, wc, err = insert_code(code, res, work, tag)
        if err: row["parametric"] = {"error": err}; results["codes"].append(row); continue
        row["parametric"] = measure(host, work, tag + ".pa")
        body = row["parametric"]["names"][0]
        e = extrusion_from(res, code)
        row["parametric_spec"] = spec_check(e, host, work, body)
        # parameters -> fields -> code (generator.code) and the round trip parameters == parameters
        f2 = rhai("fields", res["configuration"], res["parameters"])
        printed = TEMPLATES.print(f2["value"]) if f2.get("ok") else None
        st2, _ = resolve(printed) if printed else (("refused", "", "no code"), None)
        results["roundtrip"].append({"code": code, "printed": printed, "same_parameters": st2[0] == "ok" and st2[1]["parameters"] == res["parameters"]
                                     and st2[1]["configuration"] == res["configuration"]})
        results["codes"].append(row)
    if not a.only:
        for code in EXTRA_REFUSALS:
            st, _ = resolve(code)
            try:
                ext.parse(code); py = "accepted"
            except ValueError as ex: py = str(ex)
            results["refusals"].append({"code": code, "python": py, "parametric": st[2] if st[0] == "refused" else "ACCEPTED", "kind": st[1] if st[0] == "refused" else None, "extra": True})
        # ---- item 4: stays parametric -------------------------------------------------------------------------
        for base, newlen in (("HFS5-2020-1000-LTP-RTP", 300), ("HFS5-2020-300-TPW-RWV", 800), ("HFS5-4040-300-TPW", 1500)):
            st, _ = resolve(base); res = st[1]
            direct_code = "-".join(base.split("-")[:2] + [str(newlen)] + base.split("-")[3:])
            std, _ = resolve(direct_code); dres = std[1]
            wc = work / f"pc_{scrun.slug(base)}.sc"
            cmds = code_row_cmds(base, res) + [{"command": "config.activate", "params": {"row": base}},
                                               {"command": "parameters.change", "params": {"name": "length", "expression": f"{newlen} mm"}}]
            r, err = cli(cmds, src=PKG / "hfs-extrusion.sc", save=wc)
            ent = {"base": base, "length": newlen, "direct": direct_code, "error": err}
            if not err:
                ent["changed"] = measure(wc, work, "pc.changed")
                hostd, _, e2 = insert_code(direct_code, dres, work, "pcd_" + scrun.slug(direct_code))
                ent["direct_inserted"] = measure(hostd, work, "pc.direct")
                part, pysc = python_part(direct_code, work)
                ent["python"] = measure(pysc, work, "pc.py")
            results["parametric"].append(ent)
        # ---- what 0.50.0 cannot express: exact errors ------------------------------------------------------------
        wc = work / "lim.sc"; st, _ = resolve("HFS5-2020-300-TPW-RWV"); res = st[1]
        host, wc, _ = insert_code("HFS5-2020-300-TPW-RWV", res, work, "lim")
        meas = {"command": "inspect.measure", "params": {}}
        probes = {
            "insert_design with a free `parameters` map (length 777 mm)": [{"command": "component.insert_design", "params": {"path": str(wc), "configuration": "2020", "parameters": {"length": "777 mm"}, "name": "free"}}, meas],
            "component.set_link_parameters": [{"command": "component.set_link_parameters", "params": {"component": "HFS5-2020-300-TPW-RWV", "parameters": {"length": "777 mm"}}}],
            "generator.parse": [{"command": "generator.parse", "params": {"generator": str(PKG), "code": "HFS5-2020-300"}}],
            "generator.insert": [{"command": "generator.insert", "params": {"generator": str(PKG), "code": "HFS5-2020-300"}}],
            "parameters.change length on the host design holding the linked part": [{"command": "parameters.change", "params": {"name": "length", "expression": "777 mm"}}, meas],
            "length 20 mm (outside 50..4000) by an ordinary parameters.change": [{"command": "parameters.change", "params": {"name": "length", "expression": "20 mm"}}, meas],
            "length 20 mm in a configuration row": [{"command": "config.row", "params": {"name": "bad", "from": "2020", "values": {"param:length": "20 mm"}}}],
            "length 777.3 mm (not a 0.5 mm step) in a configuration row": [{"command": "config.row", "params": {"name": "bad2", "from": "2020", "values": {"param:length": "777.3 mm"}}}],
            "unknown row": [{"command": "component.insert_design", "params": {"path": str(wc), "configuration": "no-such-row"}}],
        }
        for k, c in probes.items():
            src = wc if k.startswith(("length", "length 20", "length 777")) else host
            r, err = cli(c, src=src)
            ent = {"error": err if isinstance(err, str) or err is None else json.dumps(err), "result": None}
            if r:
                last = r[-1]
                ent["result"] = ({"bbox_max": [b["bbox"]["max"] for b in last["bodies"]], "bodies": [b["name"] for b in last["bodies"]]} if isinstance(last, dict) and "bodies" in last and "body_count" in last else json.dumps(last)[:200])
            results["limits"][k] = ent
        # config.table of the template (rules and rows) for the README
        r, err = cli([{"command": "config.table", "params": {}}], src=PKG / "hfs-extrusion.sc")
        t = r[0]; results["table"] = {"rows": [x["name"] for x in t["rows"]], "columns": len(t["columns"]), "rules": len(t["rules"])}
    (out / "results.json").write_text(json.dumps(results, indent=1, default=str))
    print("wrote", out / "results.json")

main()
