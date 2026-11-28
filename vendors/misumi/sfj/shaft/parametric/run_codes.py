#!/usr/bin/env python3
"""End-to-end proof for misumi.sfj.shaft: for every code of ../codes.txt (plus a battery of extra valid codes and refusals), ordering code ->
field template (option bag) -> Rhai resolve -> a configuration row for the code (parameters of the code on the diameter row) in a working
copy of the model -> a design inserts it with component.insert_design -> measure + the generator's own spec check; and the same code built
by the Python generator and measured the same way. Writes results.json to --out.

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

sh = importlib.import_module("vendors.misumi.sfj.shaft.src.shaft")
pycheck = importlib.import_module("vendors.misumi.sfj.shaft.src.check")
PKG = HERE / "sfj-shaft"
TEMPLATES = ft.load(PKG)

# valid codes beyond codes.txt: every family, every option, both ends of a flat, the corner cases of the positional tokens
EXTRA_VALID = ["E-SFJ12-100-FC40-A5", "E-SFJ12-100-WFC20-A5-E5", "E-PSFPG8-200-F9-P6-M3-SC0", "E-PSFPG8-200-F4-P6-M3-SC0-SX20-FC10-E90", "E-PSFPH8-200-F5-P6-M3-T9-SC0",
               "E-SFJ3-400", "E-PSFG6-15", "E-PSFJ50-1500", "E-PSFJ12-100-LKC", "E-PSFJT6-30-M3", "E-PSFG30-100-WFC20-A10-E10", "E-SFJ30-300-WSC12-X20",
               "E-PSFJC6-20-M3-SC0-LKC", "E-PSFGZ12-200-M6-N8-SC10", "E-SFJW13-100-M4-N5", "E-PSFJW35-300-M12-N16", "E-SFPG12-100-F5-P8-M4-SC0-FC10-E20",
               "E-PSFPG16-300-F8-P12-MD8-SC10-LFC4-A2", "E-PSFPG20-400-F10-P17-M10-SC10-FC30-E20-LKC", "E-SFPH30-600-F8-P27-M20-T9-SC20"]
# refusals beyond codes.txt: one or more per Python message (cross-option, family, range and shape)
EXTRA_REFUSALS = [
    "E-SFJ", "XYZ", "E-SFJ20", "E-SFJ6-", "E-PSFJX6-20", "E-PFPG8-200", "E-SFPK8-200-F4-P6-M3-SC0", "E-SFJ99-300", "E-SFJ6-20-M3", "E-PSFJT6-30",
    "E-PSFJT6-30-M9", "E-PSFJT4-30-M3", "E-PSFGT5-30-M3", "E-PSFJC3-30-M3-SC0", "E-PSFJZ4-30-M3-N3-SC0", "E-PSFJT6-4-M3", "E-PSFJW6-50-M3",
    "E-PSFJW6-50-M3-N9", "E-PSFJZ6-50-M3-N3", "E-PSFJZ6-50-M3-N3-SC0-SC5", "E-SFJ6-20-WSC5", "E-SFJ20-300-SC5-WSC12-X8", "E-SFJ20-300-FC20-A5-WFC10-A5-E5",
    "E-SFJ6-20-FC10", "E-SFJ6-20-FC10-A1", "E-SFJ6-20-WFC10-A8", "E-SFJ6-20-SC0-SC1", "E-SFJ6-20-SC5.5", "E-SFJ6-20-A5", "E-SFJ6-20-SX5", "E-SFJ6-20.5",
    "E-SFJ6-5.5-LKC", "E-SFJ6-20-LKC-LKC", "E-PSFJ4-30-SC0", "E-SFJ12-100-SC95", "E-SFJ12-100-SC0-SX90", "E-SFJ12-100-WSC0-X90",
    "E-SFJ12-100-FC70", "E-SFJ40-100-FC20", "E-SFJ12-100-FC10-A1", "E-SFJ12-100-FC10-A95", 
    "E-SFJ12-100-WFC10-A60-E60", "E-SFJ12-100-SC0-FC10-A9", "E-PSFJC6-40-M3-SC0-SX1", "E-PSFJC6-40-M3-SC0-SX90", "E-PSFJC6-40-M3-SC0-WSC5-X5",
    "E-PSFJC6-40-M3-SC50", "E-PSFJT6-20-M6", "E-PSFJZ6-20-M3-N3-SC0", "E-PSFJW6-30-M3-N3-LKC-WSC5", "E-SFJW35-300-M8-N8",
    "E-PSFPG8-200-F4-P6-M3", "E-PSFPG8-200-F4-M3-SC0", "E-PSFPG8-200-P6-M3-SC0", "E-PSFPG8-200-F4-P6-SC0", "E-PSFPG8-200-F4-P6-M4-SC0", "E-PSFPG8-200-F4-P6-M6-SC0",
    "E-PSFPG8-200-F4-P5-M3-SC0", "E-PSFPG8-200-F4-P6-MD3-SC0", "E-PSFPG30-200-F10-P20-MD3-SC0", "E-PSFPG12-200-F8-P10-MD4-SC0",
    "E-PSFPG20-12-F8-P10-MD10-SC0", "E-PSFPG8-200-F4-P6-M3-SC0-FC10-A5", "E-PSFPG8-200-F4-P6-M3-SC0-LFC4", "E-PSFPG8-200-F4-P6-M3-SC0-LFC9-A0",
    "E-PSFPG8-200-F4-P6-M3-SC0-LFC1-A9", "E-PSFPG8-200-F4-P6-M3-SC0-LFC0-A0", "E-PSFPG8-900-F4-P6-M3-SC0",
    "E-PSFPH8-200-F5-P6-M3-SC0", "E-PSFPH8-200-F5-P6-M3-T5", "E-PSFPH8-200-F5-P6-M3-T5-SC0-LKC", "E-PSFPH8-200-F5-P6-MD3-T5-SC0",
    "E-PSFPG8-2-F4-P6-M3-SC0", "E-PSFPG8-200-F4-P6-M3-SC0-WSC5-X5", "E-PSFPG8-200-F4-P6-M3-SC0-SC1", "E-PSFPG8-200-F4-P6-M3-SC0-WFC10-A8",
]

def resolve(code):
    """code -> (('ok', result) | ('refused', kind, message), fields)"""
    m = TEMPLATES.match(code.strip().upper())
    if m is None: return ("refused", "invalid", f"{code!r} matches none of the templates"), None
    out = rhai(PKG, "resolve", m[1])
    if not out.get("ok"): return ("refused", out["reason"], out["message"]), m[1]
    return ("ok", out["value"]), m[1]

def py_message(code):
    try:
        sh.parse(code); return "accepted"
    except ValueError as ex: return str(ex)

def shaft_from(res):
    """The Shaft the spec check needs, rebuilt from the Rhai result (not from the Python parser)."""
    pr, p = res["properties"], res["parameters"]
    return sh.Shaft(code=pr["part_number"], type=pr["type"], D=int(res["configuration"]), L=float(p["L"].split()[0]), tolerance_class=pr["tolerance_class"],
                    tol=tuple(pr["tol"]), material=pr["base_material"], hardness=pr["hardness"], surface=pr["surface"], family=pr["family"], tapped=pr["tapped"],
                    M=pr["M"], lkc=pr["lkc"], length_tol=pr["length_tol"] or None, F=pr["F"], P=pr["P"], T=pr["T"], ymax=pr["ymax"] or None, md=pr["md"],
                    taps=pr["taps"], flats=pr["flats"], notes=pr["notes"])

def row_cmds(code, res):
    vals = {f"param:{k}": v for k, v in res["parameters"].items()}
    return [{"command": "config.row", "params": {"name": code, "from": res["configuration"], "values": vals}}]

def insert_code(code, res, out, tag):
    """Working copy of the package model + a row for the code; a host design inserts it by `configuration`. -> host .sc, working copy, error"""
    wc = out / f"{tag}.model.sc"
    r, err = cli(row_cmds(code, res), src=PKG / "sfj-shaft.sc", save=wc)
    if err: return None, None, f"config.row: {err}"
    host = out / f"{tag}.host.sc"; pr = res["properties"]
    r, err = cli([{"command": "component.insert_design", "params": {"path": str(wc), "configuration": code, "name": pr["part_number"]}},
                  {"command": "component.metadata.set", "params": {"component": pr["part_number"], "part_number": pr["part_number"], "description": pr["description"],
                                                                    "material": pr["material"]}},
                  {"command": "document.metadata.set", "params": {"values": {"part_number": pr["part_number"], "description": pr["description"]}}}], save=host)
    return (None, None, f"insert_design: {err}") if err else (host, wc, None)

def both_ways(gen, code, work, tag, spec=True):
    """-> the result row of one valid code (python and parametric measured, spec checks)"""
    st, fields = resolve(code)
    row = {"code": code}
    part, cmds = gen.build(code)
    py_sc, _ = scrun.run_script(cmds, str(work), tag + ".py")
    row["python"] = measure(py_sc, work, tag + ".py")
    buf = pycheck.check(part, py_sc, str(work)); row["python_spec"] = {"rows": len(buf.rows), "failed": [r[1] for r in buf.rows if not r[0]]}
    if st[0] == "refused":
        row["parametric"] = {"refused": st[2]}; return row, None
    res = st[1]; row["configuration"] = res["configuration"]; row["parameters"] = res["parameters"]
    row["description_same"] = res["properties"]["description"] == part.description and res["properties"]["part_number"] == part.code
    host, wc, err = insert_code(code, res, work, tag)
    if err: row["parametric"] = {"error": err}; return row, res
    row["parametric"] = measure(host, work, tag + ".pa")
    s = shaft_from(res)
    row["parametric_spec"] = spec_check(pycheck, s, host, work, row["parametric"]["names"][0], s.code)
    f2 = rhai(PKG, "fields", res["configuration"], res["parameters"])
    printed = TEMPLATES.print(f2["value"]) if f2.get("ok") else None
    st2, _ = resolve(printed) if printed else (("refused", "", "no code"), None)
    row["roundtrip"] = {"printed": printed, "same": st2[0] == "ok" and st2[1]["parameters"] == res["parameters"] and st2[1]["configuration"] == res["configuration"]}
    row["same_threads"] = row["python"]["threads"] == row["parametric"]["threads"]
    return row, res

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=str(HERE)); ap.add_argument("--only"); a = ap.parse_args()
    out = Path(a.out); work = Path(tempfile.mkdtemp()); out.mkdir(parents=True, exist_ok=True)
    gen = registry.Generator(HERE.parent)
    results = {"codes": [], "refusals": [], "parametric": [], "limits": {}}
    for cl in gen.codes():
        if a.only and cl.code != a.only: continue
        if not cl.valid:
            st, _ = resolve(cl.code)
            results["refusals"].append({"code": cl.code, "python": py_message(cl.code), "parametric": st[2] if st[0] == "refused" else "ACCEPTED", "kind": st[1] if st[0] == "refused" else None})
            continue
        row, _ = both_ways(gen, cl.code, work, scrun.slug(cl.code))
        results["codes"].append(row)
    if not a.only:
        for code in EXTRA_VALID:
            row, _ = both_ways(gen, code, work, scrun.slug(code)); row["extra"] = True
            results["codes"].append(row)
        for code in EXTRA_REFUSALS:
            st, _ = resolve(code)
            results["refusals"].append({"code": code, "python": py_message(code), "parametric": st[2] if st[0] == "refused" else "ACCEPTED", "kind": st[1] if st[0] == "refused" else None, "extra": True})
        # ---- stays parametric: change the length of a built part and compare with the code built directly ---------------------
        for base, newlen in (("E-PSFJT12-60-M6", 100), ("E-PSFJZ6-50-M3-N3-SC0", 200), ("E-SFJC20-300-M10-SC5-FC40-E20", 500), ("E-PFPGH30-800-F30-P20-M16-T25-SC40", 600),
                             ("E-PSFPG25-400-F20-P16-MD10-SC30-WFC20-A50-E50", 700), ("E-PSSFJZ16-300-M8-N6-WSC20-X30-LKC", 450), ("E-SFJ20-300-SC5", 150)):
            st, _ = resolve(base)
            if st[0] != "ok": raise ValueError(f"rebuild base {base}: {st[1]}: {st[2]}")
            res = st[1]
            parts = base.split("-"); parts[2] = str(newlen); direct = "-".join(parts)
            std, _ = resolve(direct)
            if std[0] != "ok": raise ValueError(f"rebuild reference {direct}: {std[1]}: {std[2]}")
            dres = std[1]
            wc = work / f"pc_{scrun.slug(base)}.sc"
            cmds = row_cmds(base, res) + [{"command": "config.activate", "params": {"row": base}}, {"command": "parameters.change", "params": {"name": "L", "expression": f"{newlen} mm"}}]
            r, err = cli(cmds, src=PKG / "sfj-shaft.sc", save=wc)
            ent = {"base": base, "length": newlen, "direct": direct, "error": err}
            if not err:
                ent["changed"] = measure(wc, work, "pc.changed")
                hostd, _, e2 = insert_code(direct, dres, work, "pcd_" + scrun.slug(direct))
                ent["direct_inserted"] = measure(hostd, work, "pc.direct")
                part, cm = gen.build(direct); pysc, _ = scrun.run_script(cm, str(work), "pcpy_" + scrun.slug(direct))
                ent["python"] = measure(pysc, work, "pc.py")
            results["parametric"].append(ent)
        # ---- what 0.50.0 cannot express: exact errors -------------------------------------------------------------------
        st, _ = resolve("E-PSFJT12-60-M6"); res = st[1]
        host, wc, _ = insert_code("E-PSFJT12-60-M6", res, work, "lim")
        meas = {"command": "inspect.measure", "params": {}}
        probes = {
            "insert_design with a free `parameters` map (L 777 mm)": [{"command": "component.insert_design", "params": {"path": str(wc), "configuration": "12", "parameters": {"L": "777 mm"}, "name": "free"}}, meas],
            "component.set_link_parameters": [{"command": "component.set_link_parameters", "params": {"component": "E-PSFJT12-60-M6", "parameters": {"L": "777 mm"}}}],
            "generator.parse": [{"command": "generator.parse", "params": {"generator": str(PKG), "code": "E-PSFJT12-60-M6"}}],
            "a tapped hole by the thread designation M2.6": [{"command": "component.create", "params": {"name": "x"}}, {"command": "solid.cylinder", "params": {"diameter": 5, "height": 50, "base": [0, 0, 0], "axis": "X", "operation": "new", "body_name": "S"}},
                                                             {"command": "solid.hole", "params": {"position": [0, 0, 0], "thread": "M2.6", "depth": 5.2, "targets": ["S"]}}],
            "a zero-length step feature (F = 0)": [{"command": "parameters.add", "params": {"name": "F", "expression": "0 mm", "unit": "mm"}}, {"command": "component.create", "params": {"name": "x"}},
                                                  {"command": "solid.cylinder", "params": {"diameter": 5, "height": "F", "base": [0, 0, 0], "axis": "X", "operation": "new", "body_name": "S"}}],
            "L 5 mm (outside 10..1500) in a configuration row": [{"command": "config.row", "params": {"name": "bad", "from": "12", "values": {"param:L": "5 mm"}}}],
        }
        for k, c in probes.items():
            r, err = cli(c, src=None if k.startswith(("a tapped", "a zero")) else (wc if k.startswith("L ") else host))
            ent = {"error": err if isinstance(err, str) or err is None else json.dumps(err), "result": None}
            if r:
                last = r[-1]
                ent["result"] = ({"bbox_max": [b["bbox"]["max"] for b in last["bodies"]]} if isinstance(last, dict) and "bodies" in last and "body_count" in last else json.dumps(last)[:200])
            results["limits"][k] = ent
        # the hole of a tap and the face it was picked on: a row without the left step whose tap hole was picked on the step end
        r, err = cli([{"command": "config.row", "params": {"name": "x", "from": "12", "values": {"param:m_left": "6 mm"}}}, {"command": "config.activate", "params": {"row": "x"}}], src=PKG / "sfj-shaft.sc")
        r, err = cli([{"command": "config.row", "params": {"name": "x", "from": "12", "values": {"param:m_left": "6 mm", "param:F": "0 mm"}}},
                      {"command": "config.activate", "params": {"row": "x"}}, {"command": "timeline.suppress", "params": {"feature": "Tap L step M6", "suppressed": False}}], src=PKG / "sfj-shaft.sc")
        results["limits"]["a tap hole picked on the step end, step suppressed"] = {"error": err if isinstance(err, str) or err is None else json.dumps(err), "result": None}
        r, err = cli([{"command": "config.table", "params": {}}], src=PKG / "sfj-shaft.sc")
        if r:
            t = r[0]; results["table"] = {"rows": [x["name"] for x in t["rows"]], "columns": len(t["columns"]), "rules": len(t["rules"])}
    (out / "results.json").write_text(json.dumps(results, indent=1, default=str))
    print("wrote", out / "results.json")

main()
