#!/usr/bin/env python3
"""End-to-end proof for misumi.hnt.t-nut: for every code of ../codes.txt (plus a battery of extra refusals), ordering code -> field
template -> Rhai resolve -> configuration row -> the parametric hnt-t-nut.sc inserted by that row -> measure + the generator's own spec
check; and the same code built by the Python generator and measured the same way. Writes results.json to --out.

    SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run binary> python3 run_codes.py [--out DIR] [--only CODE]
"""
from __future__ import annotations
import argparse, importlib, json, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime import fieldtemplate as ft, registry, sc as scrun
from runtime.parametric import cli, rhai, measure, spec_check
from runtime.table import read_csv, num

nt = importlib.import_module("vendors.misumi.hnt.t-nut.src.nut")
pycheck = importlib.import_module("vendors.misumi.hnt.t-nut.src.check")
PKG = HERE / "hnt-t-nut"
TEMPLATES = ft.load(PKG)
TYPES = {r["type"]: r for r in read_csv(PKG / "tables" / "types.csv")}
EXTRA_REFUSALS = ["HNTU5", "HNTU5-5", "SHNTU5", "HNTTX5", "HNTT5-0", "HNTT5-5.5", "HNTT5-3.0", "HNTT5-6", "HNTTSS5-3", "HNTTZ5-4", "HNTTV5-3", "HNTTSN5-6",
                  "HNTT6-4", "HNTT-4", "XHNTT5", "HNTT5-12", "HNTTSN5-2", "HNST5", "HNTTBS5-5", "HNTT5-06", "HNTT5-", "HNTT5-4-4", "HNTT5--4", "HNTT5-4-", "HNTT"]

def resolve(code):
    m = TEMPLATES.match(code.strip().upper())
    if m is None:
        return ("refused", "invalid", f"{code!r} matches none of the templates"), None
    out = rhai(PKG, "resolve", m[1])
    if not out.get("ok"): return ("refused", out["reason"], out["message"]), m[1]
    return ("ok", out["value"]), m[1]

def nut_from(res, code):
    """The Nut the spec check needs, rebuilt from the Rhai result and the package tables (not from the Python parser)."""
    typ, m = res["configuration"].split("-"); r = TYPES[typ]
    return nt.Nut(code=res["configuration"], type=typ, kind=r["kind"], material=r["material"], surface=r["surface"], M=int(m),
                  E=float(r["E"]), T=float(r["T"]), notes=[])

def insert_code(res, out, tag):
    """A host design inserts the package model by the configuration row Rhai named. -> host .sc path, error"""
    host = out / f"{tag}.host.sc"; pr = res["properties"]; name = res["configuration"]
    r, err = cli([{"command": "component.insert_design", "params": {"path": str(PKG / "hnt-t-nut.sc"), "configuration": res["configuration"], "name": name}},
                  {"command": "component.metadata.set", "params": {"component": name, "part_number": pr["part_number"], "description": pr["description"],
                                                                    "material": pr["material"]}},
                  {"command": "document.metadata.set", "params": {"values": {"part_number": pr["part_number"], "description": pr["description"]}}}], save=host)
    return (None, f"insert_design: {err}") if err else (host, None)

def py_message(code):
    try:
        nt.parse(code); return "accepted"
    except ValueError as ex: return str(ex)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); ap.add_argument("--only"); a = ap.parse_args()
    out = Path(a.out); work = Path(tempfile.mkdtemp()); out.mkdir(parents=True, exist_ok=True)
    gen = registry.Generator(HERE.parent)
    results = {"codes": [], "refusals": [], "roundtrip": [], "limits": {}}
    for cl in gen.codes():
        if a.only and cl.code != a.only: continue
        code = cl.code
        st, fields = resolve(code)
        if not cl.valid:
            results["refusals"].append({"code": code, "python": py_message(code), "parametric": st[2] if st[0] == "refused" else "ACCEPTED", "kind": st[1] if st[0] == "refused" else None})
            continue
        row = {"code": code}; tag = scrun.slug(code)
        part, cmds = gen.build(code)
        py_sc, _ = scrun.run_script(cmds, str(work), tag + ".py")
        row["python"] = measure(py_sc, work, tag + ".py")
        buf = pycheck.check(part, py_sc, str(work)); row["python_spec"] = {"rows": len(buf.rows), "failed": [r[1] for r in buf.rows if not r[0]]}
        if st[0] == "refused":
            row["parametric"] = {"refused": st[2]}; results["codes"].append(row); continue
        res = st[1]; row["configuration"] = res["configuration"]; row["parameters"] = res["parameters"]
        host, err = insert_code(res, work, tag)
        if err: row["parametric"] = {"error": err}; results["codes"].append(row); continue
        row["parametric"] = measure(host, work, tag + ".pa")
        n = nut_from(res, code)
        row["parametric_spec"] = spec_check(pycheck, n, host, work, row["parametric"]["names"][0], n.code)
        f2 = rhai(PKG, "fields", res["configuration"], res["parameters"])
        printed = TEMPLATES.print(f2["value"]) if f2.get("ok") else None
        st2, _ = resolve(printed) if printed else (("refused", "", "no code"), None)
        results["roundtrip"].append({"code": code, "printed": printed, "same_parameters": st2[0] == "ok" and st2[1]["parameters"] == res["parameters"] and st2[1]["configuration"] == res["configuration"]})
        results["codes"].append(row)
    if not a.only:
        for code in EXTRA_REFUSALS:
            st, _ = resolve(code)
            results["refusals"].append({"code": code, "python": py_message(code), "parametric": st[2] if st[0] == "refused" else "ACCEPTED", "kind": st[1] if st[0] == "refused" else None, "extra": True})
        # every valid (type, M) pair the table offers, not only the codes of codes.txt: Python volume and bbox against the parametric row
        for t, r in TYPES.items():
            for m in str(r["allowed_m"]).split("|"):
                code = f"{t}-{m}"
                st, _ = resolve(code)
                part, cmds = gen.build(code); py_sc, _ = scrun.run_script(cmds, str(work), scrun.slug(code) + ".all.py")
                ent = {"code": code, "python": measure(py_sc, work, scrun.slug(code) + ".allpy")}
                host, err = insert_code(st[1], work, scrun.slug(code) + ".all")
                ent["parametric"] = {"error": err} if err else measure(host, work, scrun.slug(code) + ".allpa")
                buf = pycheck.check(part, py_sc, str(work)); ent["python_spec"] = {"rows": len(buf.rows), "failed": [r[1] for r in buf.rows if not r[0]]}
                if not err:
                    n = nut_from(st[1], code)
                    ent["parametric_spec"] = spec_check(pycheck, n, host, work, ent["parametric"]["names"][0], n.code)
                results.setdefault("all_rows", []).append(ent)
        r, err = cli([{"command": "config.table", "params": {}}], src=PKG / "hnt-t-nut.sc")
        if r:
            t = r[0]; results["table"] = {"rows": [x["name"] for x in t["rows"]], "columns": len(t["columns"]), "rules": len(t["rules"])}
    (out / "results.json").write_text(json.dumps(results, indent=1, default=str))
    print("wrote", out / "results.json")

main()
