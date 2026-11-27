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

PKG = HERE / "shf-shaft-holder"
MODEL = PKG / "shf-shaft-holder.sc"
RHAI = os.environ.get("RHAI_RUN", "rhai-run")
CLI = scrun.CLI
GEN = registry.find("E-SHSTM8-25")
hm, pycheck = GEN.module("holder"), GEN.module("check")
EXTRA_REFUSALS = ["E-SHSTM8-25-3", "E-SHA10", "E-SHSTM100-20", "E-SHSTA16-25", "E-SHSTMN10-15", "E-SHSTB15", "C-SHA7", "C-SHA10-5", "E-SHWTB9-10", "E-SHSTM8-0",
                  "E-SHWTA12-25", "E-SHSTB8-45", "E-SHSTA8-10", "E-SHWTA8-10", "E-SHSTBN9-10", "E-SHSTMN15-25-1", "C-SHA", "C-SHA25-20", "X", "E-SHSTM8-25-"]
REBUILD = [("E-SHSTM8-25", 40, "E-SHSTM8-40"), ("E-SHWTB20-30", 60, "E-SHWTB20-60"), ("E-SHSTBN30-80", 25, "E-SHSTBN30-25"), ("E-SHSTA16-20", 15, "E-SHSTA16-15"),
           ("E-SHSTB15-20", 30, "E-SHSTB15-30")]

def cli(cmds, src=None, save=None):
    d = Path(tempfile.mkdtemp())
    (d / "s.json").write_text(json.dumps({"commands": cmds}))
    a = [CLI, "run", str(d / "s.json"), "--results", "--json-out", str(d / "r.json"), "--quiet"]
    if src: a += ["--in", str(src)]
    if save: a += ["--save", str(save)]
    r = subprocess.run(a, capture_output=True, text=True)
    out = json.loads((d / "r.json").read_text()) if (d / "r.json").exists() else {}
    err = out.get("error") if isinstance(out, dict) else None
    res = out.get("results") if isinstance(out, dict) else out
    return res, (err or (r.stderr.strip() if r.returncode else None))

def rhai(fn, *args):
    env = dict(os.environ, FT_ROOT=str(ROOT))
    r = subprocess.run([RHAI, str(PKG), fn, *[json.dumps(a) for a in args]], capture_output=True, text=True, env=env)
    return json.loads(r.stdout) if r.stdout.strip() else {"ok": False, "reason": "script_error", "message": r.stderr}

TEMPLATES = ft.load(PKG)

def resolve(code):
    """code -> (('ok', result) | ('refused', kind, message), fields)"""
    m = TEMPLATES.match(code.strip().upper())
    if m is None:
        return ("refused", "invalid", f"{code!r} matches none of the templates"), None
    out = rhai("resolve", m[1])
    if not out.get("ok"): return ("refused", out["reason"], out["message"]), m[1]
    return ("ok", out["value"]), m[1]

def measure(sc_path, out_dir, tag):
    r = run_measure(sc_path, [{"command": "inspect.measure", "params": {}}], str(out_dir), tag)
    m = r[0]; b = m["bodies"]
    lo = [min(x["bbox"]["min"][i] for x in b) for i in range(3)]; hi = [max(x["bbox"]["max"][i] for x in b) for i in range(3)]
    return {"bodies": len(b), "volume": m["total"]["volume_mm3"], "area": m["total"]["area_mm2"], "faces": m["total"]["faces"],
            "bbox": [round(h - l, 4) for l, h in zip(lo, hi)], "names": [x["name"] for x in b]}

def python_part(code, out):
    part, cmds = registry.build(code)
    path, _ = scrun.run_script(cmds, str(out), scrun.slug(code) + ".py")
    return part, path

def _lst(s): return [int(x) for x in s.split("|")] if s else []
T = PKG / "tables"
DIMS = {r["key"]: {k: (v if k in ("family", "source", "page", "status") else (_lst(v) if k in ("h_all", "h_alu") else num(v))) for k, v in r.items() if k != "key"}
        for r in read_csv(T / "dims.csv")}
CSHA = {r["key"]: {k: num(v) for k, v in r.items() if k != "key"} for r in read_csv(T / "csha.csv")}
TYPES = {r["type"]: r for r in read_csv(T / "types.csv")}
TOL = {int(r["D"]): (num(r["upper"]), num(r["lower"])) for r in read_csv(T / "tolerance.csv")}

def holder_from(res, code):
    """The Holder the spec check needs, built from the Rhai result and the package's own tables (not from the Python parser)."""
    pr, p = res["properties"], res["parameters"]
    typ = pr["type_name"]; t = TYPES[typ]; fam, D = res["configuration"].split("-"); D = int(D)
    if fam == "csha":
        r = CSHA[res["configuration"]]
        return hm.Holder(code=code.strip().upper(), type=typ, family="csha", D=D, H=r["H"], dims=r, tol=(None, None), tolerance_class="H7", material=t["material"],
                         surface=t["surface"], accessory=t["accessory"])
    return hm.Holder(code=code.strip().upper(), type=typ, family=fam, D=D, H=float(p["h"].split()[0]), dims=DIMS[res["configuration"]], tol=TOL[D],
                     tolerance_class="H8", material=t["material"], surface=t["surface"], accessory=t["accessory"])

def code_row_cmds(code, res):
    vals = {f"param:{k}": v for k, v in res["parameters"].items()}
    return [{"command": "config.row", "params": {"name": code.strip().upper(), "from": res["configuration"], "values": vals}}]

def subst(o, old, new):
    """The spec check names the body after the code (the Python build does); the inserted body keeps the model's own name, the component is
    named after the code: rename the `body` references only."""
    if isinstance(o, dict): return {k: (new if k == "body" and v == old else subst(v, old, new)) for k, v in o.items()}
    if isinstance(o, list): return [subst(v, old, new) for v in o]
    return o

def spec_check(h, host_sc, out, body):
    orig = pycheck.run_measure
    pycheck.run_measure = lambda sc, cmds, o, name: orig(sc, subst(cmds, h.code, body), o, name)
    try:
        R = pycheck.check(h, host_sc, str(out))
    finally:
        pycheck.run_measure = orig
    return {"rows": len(R.rows), "failed": [f"{r[1]}: spec {r[2]} got {r[3]}" for r in R.rows if not r[0]]}

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
        hm.parse(code); return "accepted"
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
        row["parametric_spec"] = spec_check(holder_from(res, code), host, work, row["parametric"]["names"][0])
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
        # ---- stays parametric: change the free height on the configured design, compare with the code built directly --------
        for base, newh, direct_code in REBUILD:
            st, _ = resolve(base); res = st[1]
            dst, _ = resolve(direct_code); dres = dst[1]
            wc = work / f"pc_{scrun.slug(base)}.sc"
            cmds = code_row_cmds(base, res) + [{"command": "config.activate", "params": {"row": base}},
                                               {"command": "parameters.change", "params": {"name": "h", "expression": f"{newh} mm"}}]
            r, err = cli(cmds, src=MODEL, save=wc)
            ent = {"base": base, "param": "h", "value": f"{newh} mm", "direct": direct_code, "error": err}
            if not err:
                ent["changed"] = measure(wc, work, "pc.changed")
                hostd, _, e2 = insert_code(direct_code, dres, work, "pcd_" + scrun.slug(direct_code))
                ent["direct_inserted"] = measure(hostd, work, "pc.direct")
                part, pysc = python_part(direct_code, work)
                ent["python"] = measure(pysc, work, "pc.py")
            results["parametric"].append(ent)
        # ---- what 0.50.0 cannot express / what the rules enforce: exact messages ------------------------------------------
        st, _ = resolve("E-SHSTM8-25"); res = st[1]
        host, wc, _ = insert_code("E-SHSTM8-25", res, work, "lim")
        meas = {"command": "inspect.measure", "params": {}}
        probes = {
            "insert_design with a free `parameters` map (h 40 mm)": ([{"command": "component.insert_design", "params": {"path": str(wc), "configuration": "slit-8", "parameters": {"h": "40 mm"}, "name": "free"}}, meas], host),
            "component.set_link_parameters": ([{"command": "component.set_link_parameters", "params": {"component": "E-SHSTM8-25", "parameters": {"h": "40 mm"}}}], host),
            "generator.parse": ([{"command": "generator.parse", "params": {"generator": str(PKG), "code": "E-SHSTM8-25"}}], host),
            "row with h 35 mm for slit-8 (not in 10 15 20 25 30 40)": ([{"command": "config.row", "params": {"name": "bad", "from": "slit-8", "values": {"param:h": "35 mm"}}}], MODEL),
            "row with h 15 mm for the aluminium slit-10 (only 20)": ([{"command": "config.row", "params": {"name": "bad", "from": "slit-10", "values": {"param:h": "15 mm", "param:alu": "1"}}}], MODEL),
            "h 35 mm by an ordinary parameters.change": ([{"command": "parameters.change", "params": {"name": "h", "expression": "35 mm"}}, meas], MODEL),
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
