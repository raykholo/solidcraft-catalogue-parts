#!/usr/bin/env python3
"""End-to-end proof: for every code of ../codes.txt (plus extra refusals), ordering code -> field template -> Rhai resolve ->
configuration row -> the parametric .sc inserted with `configuration` -> measure + the generator's own spec check; and the same code built by
the Python generator and measured the same way. Writes results.json in --out.

    SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run binary> python3 run_codes.py [--out DIR] [--only CODE]
    python3 run_codes.py --rhai-only --out DIR  # full valid catalogue; no SolidCraft
"""
from __future__ import annotations
import argparse, json, os, subprocess, sys, tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime import fieldtemplate as ft, registry, sc as scrun
from runtime.check import run_measure
from vendors.misumi.hbl.bracket.src import bracket as br, check as pycheck

PKG = HERE / "hbl-bracket"
MODEL = PKG / "hbl-bracket.sc"
RHAI = os.environ.get("RHAI_RUN", "rhai-run")
CLI = scrun.CLI
EXTRA_REFUSALS = ["HBLTS5-4-C-SET", "HBLTS5-4-5", "HBLFSNK5", "HBLTS8", "HBLTSB5-4", "HBKTST5-C", "HBKUSB5-C", "HBLTS5-SEC-SST", "HBLTV5-4-C",
                  "HBLTS5-C-C", "HBLTS5-4-4", "HBLUS5-4", "HBLTH5-C-SET", "HBLTS5-", "HBLTS5--C", "HBLTS5-C-"]
REBUILD = [("HBLTS5", "width", "19 mm", "HBLTV5"), ("HBLTS5", "hole_d", "4.5 mm", "HBLTS5-4")]



TEMPLATES = ft.load(PKG)

from runtime.parametric import cli, rhai as call_rhai, measure as measure_core

def rhai(fn, *args):
    return call_rhai(PKG, fn, *args)

def measure(sc_path, out_dir, tag, threads=True):
    return measure_core(sc_path, out_dir, tag, threads=threads and False, include_threads=False)


def resolve(code):
    """code -> (('ok', result) | ('refused', kind, message), fields)"""
    from runtime.parametric.resolve import checked
    return checked(TEMPLATES, rhai, code)


def python_part(code, out):
    part, cmds = registry.build(code)
    path, _ = scrun.run_script(cmds, str(out), scrun.slug(code) + ".py")
    return part, path

def bracket_from(res):
    """The br.Bracket the spec check needs, built from the Rhai result and the package's own table (not from the Python parser)."""
    key = res["configuration"]
    if key == "HBLTS5" and res["parameters"].get("hole_d") == f'{float(br.TYPES["HBLTS5-4"]["hole_d"]):g} mm':
        key = "HBLTS5-4"
    return br._bracket(key, res["properties"]["part_number"], res["properties"]["alteration"])

from runtime.parametric import subst

from runtime.parametric import spec_check as check_inserted

def spec_check(b, host_sc, out, body):
    return check_inserted(pycheck, b, host_sc, out, body, b.code)

def insert_code(code, res, out, tag):
    """A host design inserts the package model with `configuration` (the type's row), names the component after the code and writes its metadata."""
    wc = out / f"{tag}.model.sc"
    values = {f"param:{k}": v for k, v in res["parameters"].items()}
    _, error = cli([{"command": "config.row", "params": {"name": code, "from": res["configuration"], "values": values}}], src=MODEL, save=wc)
    if error: return None, f"config.row: {error}"
    host = out / f"{tag}.host.sc"
    pr = res["properties"]; c = code.strip().upper()
    r, err = cli([{"command": "component.insert_design", "params": {"path": str(wc), "configuration": code, "name": c}},
                  {"command": "component.metadata.set", "params": {"component": c, "part_number": pr["part_number"], "description": pr["description"],
                                                                    "material": f'{pr["material"]}; {pr["surface"]}'}},
                  {"command": "document.metadata.set", "params": {"values": {"part_number": pr["part_number"], "description": pr["description"]}}}], save=host)
    if err: return None, f"insert_design: {err}"
    return host, None

def pymsg(code):
    try:
        br.parse(code); return "accepted"
    except ValueError as ex: return str(ex)

def valid_candidates():
    from runtime.table import read_csv
    codes = [cl.code for cl in registry.Generator(HERE.parent).codes() if cl.valid]
    alterations = ["", "C"] + [r["code"] for r in read_csv(PKG / "tables/alterations.csv")]
    return codes + [key + ("-" + alt if alt else "") for key in br.TYPES for alt in alterations]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); ap.add_argument("--only"); ap.add_argument("--rhai-only", action="store_true"); a = ap.parse_args()
    if a.rhai_only:
        from runtime.parametric.resolve import sweep
        raise SystemExit(sweep(valid_candidates(), registry.Generator(HERE.parent).build, resolve, rhai, TEMPLATES, a.out))
    out = Path(a.out); work = Path(tempfile.mkdtemp()); out.mkdir(parents=True, exist_ok=True)
    gen = registry.find("HBLTS5")
    results = {"codes": [], "refusals": [], "parametric": [], "limits": {}, "roundtrip": []}
    for cl in gen.codes():
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
        row["configuration"] = res["configuration"]
        row["description_same"] = res["properties"]["description"] == part.description
        host, err = insert_code(code, res, work, tag)
        if err: row["parametric"] = {"error": err}; results["codes"].append(row); continue
        row["parametric"] = measure(host, work, tag + ".pa")
        row["parametric_spec"] = spec_check(bracket_from(res), host, work, row["parametric"]["names"][0])
        f2 = rhai("fields", res["configuration"], res["parameters"])
        printed = TEMPLATES.print(f2["value"]) if f2.get("ok") else None
        st2, _ = resolve(printed) if printed else (("refused", "", "no code"), None)
        results["roundtrip"].append({"code": code, "printed": printed, "same_configuration": st2[0] == "ok" and st2[1]["configuration"] == res["configuration"]})
        results["codes"].append(row)
    if not a.only:
        for code in EXTRA_REFUSALS:
            st, _ = resolve(code)
            results["refusals"].append({"code": code, "python": pymsg(code), "parametric": st[2] if st[0] == "refused" else "ACCEPTED", "kind": st[1] if st[0] == "refused" else None, "extra": True})
        # ---- stays parametric: change a parameter on the configured design, compare with the code built directly --------------
        for base, name, value, direct_code in REBUILD:
            ent = {"base": base, "param": name, "value": value, "direct": direct_code}
            wc = work / f"pc_{scrun.slug(base)}_{name}.sc"
            r, err = cli([{"command": "config.activate", "params": {"row": base}}, {"command": "parameters.change", "params": {"name": name, "expression": value}}],
                         src=MODEL, save=wc)
            ent["error"] = err
            if not err:
                ent["changed"] = measure(wc, work, "pc.changed")
                if direct_code:
                    stt, _ = resolve(direct_code)
                    if stt[0] != "ok":
                        ent["error"] = f"{direct_code}: resolve {stt[1]}: {stt[2]}"
                        ent["changed"] = {"error": ent["error"]}
                        results["parametric"].append(ent)
                        continue
                    hostd, e2 = insert_code(direct_code, stt[1], work, "pcd_" + scrun.slug(direct_code))
                    ent["direct_inserted"] = {"error": e2} if e2 else measure(hostd, work, "pc.direct")
                    part, pysc = python_part(direct_code, work)
                    ent["python"] = measure(pysc, work, "pc.py")
            results["parametric"].append(ent)
        # ---- what 0.50.0 cannot express: exact errors ------------------------------------------------------------------------
        state, _ = resolve("HBLTS5")
        if state[0] != "ok":
            (out / "results.json").write_text(json.dumps(results, indent=1))
            return
        host, _ = insert_code("HBLTS5", state[1], work, "lim")
        meas = {"command": "inspect.measure", "params": {}}
        probes = {
            "insert_design with a free `parameters` map (width 19 mm)": ([{"command": "component.insert_design", "params": {"path": str(MODEL), "configuration": "HBLTS5", "parameters": {"width": "19 mm"}, "name": "free"}}, meas], host),
            "component.set_link_parameters": ([{"command": "component.set_link_parameters", "params": {"component": "HBLTS5", "parameters": {"width": "19 mm"}}}], host),
            "generator.parse": ([{"command": "generator.parse", "params": {"generator": str(PKG), "code": "HBLTS5"}}], host),
            "unknown row": ([{"command": "component.insert_design", "params": {"path": str(MODEL), "configuration": "no-such-row"}}], host),
            "tabs = 1 on an HBLTS5 row (rules switch the tab features on)": ([{"command": "config.row", "params": {"name": "t", "from": "HBLTS5", "values": {"param:tabs": "1"}}}, {"command": "config.activate", "params": {"row": "t"}}, meas], MODEL),
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

if __name__ == "__main__":
    main()
