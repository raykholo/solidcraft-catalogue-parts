#!/usr/bin/env python3
"""End-to-end for one guideway series on SolidCraft 0.50.0: EVERY line of the generator's codes.txt through
template -> Rhai -> configuration row + parameters -> parametric design, measured, beside the Python generator's part (dimensioned bodies
only: build.commands(appearance=False)), measured the same way; the generator's own src/check.py on both; and rebuild checks (a free
parameter changed on a built part against the code built directly).
    python3 gw_harness.py SERIES PARAMETRIC_DIR OUTDIR            (SC_CLI, RHAI_RUN set; repo root not required)
Writes OUTDIR/report.json (and report.md). Codes run in parallel processes."""
from __future__ import annotations
import json, os, re, shutil, subprocess, sys, traceback
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
from pathlib import Path

from runtime.parametric.package import Package
from runtime.parametric.absolute import AbsoluteHarness, c, fmt, same, summarize
from runtime import registry, sc
import runtime.check as rc

class Ctx:                 # set before the pool forks
    plans = None; S = None; GEN = None; PKG = None; TEMPLATE = None; OUT = None; cat = None; build = None; chk = None

def run(cmds, name, base=None, save=None):
    out = Ctx.OUT / "work"
    out.mkdir(parents=True, exist_ok=True)
    return AbsoluteHarness(out).run(cmds, name, base, save)



def measure(path, name):
    j, err = run([c("inspect.measure")], name, base=path)
    return {"error": err} if err else summarize(j[0])





def clean(m):          # drop the per-body list from what goes into the report
    return {k: v for k, v in m.items() if k != "names"} if m and "error" not in m else m

def python_part(code, tag):
    s, cmds = Ctx.build.parse_build(code, appearance=False)
    path, _ = sc.run_script(cmds, str(Ctx.OUT / "work"), f"py-{tag}")
    return s, path

def instance(parsed, code, tag, extra=None):
    """The parametric part at a configuration row and parameter values: 0.50.0 has no free parameters on insert_design, so the values are
    set in a copy of the design (config.activate, parameters.change), which is then the file that gets inserted."""
    ps = dict(parsed["parameters"]); ps.update(extra or {})
    cmds = [c("config.activate", row=parsed["configuration"])]
    if ps: cmds.append(c("parameters.change", changes=ps))
    cmds.append(c("document.metadata.set", values={"part_number": code}))
    path = Ctx.OUT / "work" / f"inst-{tag}.sc"
    j, err = run(cmds, f"inst-{tag}", base=Ctx.TEMPLATE, save=path)
    return str(path), err

# ---- the spec check on the parametric part: block bodies are pattern copies named Body<N>; the check wants Block 1..n (left to right),
# answers component.metadata from the design's document metadata (no component exists in the instance file)
def param_check(s, path, tag):
    m = measure(path, f"nm-{tag}")
    blocks = sorted([(n, b) for n, b in m["names"] if n != "Rail"], key=lambda nb: nb[1]["min"][0])
    inv = {f"Block {i + 1}": n for i, (n, _) in enumerate(blocks)}
    fwd = {n: f"Block {i + 1}" for i, (n, _) in enumerate(blocks)}
    boxes = [(f"Block {i + 1}", b) for i, (_, b) in enumerate(blocks)]
    real = rc.run_measure
    def inside(p, b, t=1e-6): return all(b["min"][i] - t <= p[i] <= b["max"][i] + t for i in range(3))
    def wrapped(sc_path, cmds, out_dir, name):
        send = []
        for x in cmds:
            if x["command"] == "component.metadata": continue
            p = dict(x.get("params", {}))
            if p.get("body") in inv: p["body"] = inv[p["body"]]
            send.append({"command": x["command"], "params": p})
        res = real(sc_path, send, out_dir, name)
        it = iter(res); out = []
        for x in cmds:
            out.append(None if x["command"] == "component.metadata" else next(it))
        pn = None
        for x, r in zip(cmds, out):
            if x["command"] == "inspect.measure":
                for b in r["bodies"]:
                    if b["name"] in fwd: b["name"] = fwd[b["name"]]
            elif x["command"] == "model.threads":
                for t in r["threads"]:
                    for nm, bb in boxes:
                        if inside(t["axis_point"], bb): t["body"] = nm
            elif x["command"] == "document.metadata":
                mm = re.search(r'"part_number":\s*"([^"]+)"', json.dumps(r)); pn = mm.group(1) if mm else None
        return [({"metadata": {"part_number": pn, "description": ""}} if r is None else r) for r in out]
    Ctx.chk.run_measure = wrapped
    try:
        R = Ctx.chk.check(s, path, str(Ctx.OUT / "chk-param"), appearance=False)
    finally:
        Ctx.chk.run_measure = real
    bad = [r[1] for r in R.rows if not r[0]]
    return f"{len(R.rows) - len(bad)}/{len(R.rows)}" + (" FAIL: " + "; ".join(bad) if bad else "")

def python_check(s, path):
    R = Ctx.chk.check(s, path, str(Ctx.OUT / "chk-py"), appearance=False)
    bad = [r[1] for r in R.rows if not r[0]]
    return f"{len(R.rows) - len(bad)}/{len(R.rows)}" + (" FAIL: " + "; ".join(bad) if bad else "")

def do_code(line):
    """one line of codes.txt -> the report row"""
    tag = line.name
    try:
        r = Ctx.PKG.parse(line.code)
        if not line.valid:
            try: Ctx.build.parse_build(line.code); pymsg = "ACCEPTED"
            except ValueError as ex: pymsg = str(ex)
            return dict(code="!" + line.code, python=pymsg, param=("REFUSED: " + r["message"]) if not r["ok"] else "ACCEPTED",
                        same=(not r["ok"]) and r["message"] == pymsg, check="-")
        s, pypath = python_part(line.code, tag)
        pm = measure(pypath, f"m-py-{tag}")
        if not r["ok"]:
            return dict(code=line.code, python=fmt(pm), python_m=clean(pm), param="REFUSED: " + r["message"], same=False, check="-")
        try:
            canon = Ctx.PKG.code(r["fields"], r["template"]); rt = Ctx.PKG.parse(canon)
        except Exception as ex:
            canon, rt = f"print failed: {ex}", {"ok": False}
        ipath, err = instance(r, line.code, tag)
        if err:
            return dict(code=line.code, python=fmt(pm), python_m=clean(pm), param="ERROR " + json.dumps(err)[:300], same=False, check="-")
        am = measure(ipath, f"m-inst-{tag}")
        row = dict(code=line.code, configuration=r["configuration"], parameters=r["parameters"], template=r["template"], printed=canon,
                   roundtrip=bool(rt["ok"] and rt["fields"] == r["fields"]), python=fmt(pm), param=fmt(am), same=same(pm, am),
                   python_m=clean(pm), param_m=clean(am))
        try: row["pycheck"] = python_check(s, pypath)
        except BaseException as ex: row["pycheck"] = f"ERROR {ex}"
        try: row["check"] = param_check(s, ipath, tag)
        except BaseException as ex: row["check"] = f"ERROR {ex}"
        print(f"[{line.code}] same={row['same']} spec {row['pycheck'].split(' ')[0]} / {row['check'].split(' ')[0]}", flush=True)
        return row
    except BaseException as ex:
        traceback.print_exc()
        return dict(code=("!" if not line.valid else "") + line.code, python="?", param=f"HARNESS ERROR {type(ex).__name__}: {ex}", same=False, check="-")

def do_rebuild(plan):
    label, base, change, target = plan
    tag = re.sub(r"\W+", "_", f"rb-{base}-{target}")[:60]
    try:
        rb = Ctx.PKG.parse(base); rt = Ctx.PKG.parse(target)
        ip, err = instance(rb, base, tag + "-base")
        if err: return dict(label=label, error=err)
        shutil.copy(ip, Ctx.OUT / "work" / f"{tag}-before.sc")
        j, err = run([c("parameters.change", changes=change), c("inspect.measure")], f"{tag}-change", base=Ctx.OUT / "work" / f"{tag}-before.sc")
        if err: return dict(label=label, error=err)
        rebuilt = summarize(j[1])
        tp, err = instance(rt, target, tag + "-fresh")
        fresh = measure(tp, f"{tag}-m-fresh") if not err else {"error": err}
        s, py = python_part(target, tag + "-py")
        pm = measure(py, f"{tag}-m-py")
        return dict(label=f"{base} {label} vs {target}", rebuilt=clean(rebuilt), fresh=clean(fresh), python=clean(pm),
                    same_fresh=same(rebuilt, fresh), same_python=same(rebuilt, pm))
    except BaseException as ex:
        traceback.print_exc()
        return dict(label=label, error=f"{type(ex).__name__}: {ex}")

def probes():
    """what 0.50.0 does with a link: insert a row at its defaults, a free parameter on insert, set_link_parameters, parameters.change in the assembly"""
    row, code = Ctx.plans["insert"]
    out = {}
    def short(e): return json.dumps(e)[:300]
    j, err = run([c("component.insert_design", path=Ctx.TEMPLATE, configuration=row), c("inspect.measure")], "p-insert-config")
    out["insert_design configuration=" + row] = short(err) if err else "ok"
    res = None
    if not err:
        am = summarize(j[1]); s, py = python_part(code, "probe-row"); pm = measure(py, "m-probe-row")
        out[f"row {row} inserted == Python {code}"] = f"{same(pm, am)}; python {fmt(pm)}; inserted {fmt(am)}"
        res = dict(direct=clean(pm), changed=clean(am), label=f"component.insert_design of row {row} (defaults: 400 mm, 1 block) vs Python {code}")
    j, err = run([c("component.insert_design", path=Ctx.TEMPLATE, configuration=row, parameters={"length": "800 mm"}), c("inspect.measure")], "p-insert-params")
    out[f"insert_design configuration={row} parameters={{length: 800 mm}}"] = short(err) if err else \
        "accepted, rail x extent is " + str(max(b["bbox"]["max"][0] for b in j[1]["bodies"])) + " (400 = the parameters key is ignored)"
    j, err = run([c("component.insert_design", path=Ctx.TEMPLATE, configuration=row), c("component.set_link_parameters", component=1, parameters={"length": "800 mm"})], "p-setlink")
    out["component.set_link_parameters"] = short(err) if err else "ok"
    j, err = run([c("component.insert_design", path=Ctx.TEMPLATE, configuration=row), c("parameters.change", changes={"length": "800 mm"})], "p-asm-param")
    out["parameters.change length in the assembly that holds the link"] = short(err) if err else "accepted"
    j, err = run([c("component.insert_design", path=Ctx.TEMPLATE, configuration="nope")], "p-insert-badrow")
    out["insert_design configuration=nope"] = short(err) if err else "accepted"
    return out, res

def limits():
    """where the model's range rules apply on 0.50.0"""
    S = Ctx.S; lim = {}
    row = Ctx.plans["insert"][0]
    def tryit(label, cmds, base=None):
        j, err = run(cmds, "lim-" + re.sub(r"\W+", "_", label)[:40], base=base or Ctx.TEMPLATE)
        lim[label] = ("REFUSED " + json.dumps(err)[:260]) if err else "accepted: " + json.dumps(j[-1])[:160]
    tryit("ordinary edit: length 9000 mm (max 4000)", [c("config.activate", row=row), c("parameters.change", changes={"length": "9000 mm"})])
    tryit("ordinary edit: blocks 40 on a 400 mm rail", [c("config.activate", row=row), c("parameters.change", changes={"blocks": "40"})])
    tryit("row with length 9000 mm, config.activate", [c("config.row", name="bad-length", **{"from": row, "values": {"param:length": "9000 mm"}}), c("config.activate", row="bad-length")])
    tryit("row with 40 blocks on 400 mm, config.activate", [c("config.row", name="bad-blocks", **{"from": row, "values": {"param:blocks": "40"}}), c("config.activate", row="bad-blocks")])
    tryit("row with length 30 mm, config.activate", [c("config.row", name="bad-short", **{"from": row, "values": {"param:length": "30 mm"}}), c("config.activate", row="bad-short")])
    return lim

def main(S, plans, par, out):
    Ctx.plans = plans
    gen = next(g for g in registry.generators() if g.id == S.gid)
    pkgdir = Path(par) / f"{S.dirname}-guideway"
    Ctx.S, Ctx.GEN, Ctx.OUT = S, gen, Path(out).resolve()
    Ctx.PKG = Package(pkgdir, no_match=lambda code: f"no template of the generator matches {code!r}", no_match_reason="no_template", typed_code_field="raw_code"); Ctx.TEMPLATE = str((pkgdir / f"{S.dirname}-guideway.sc").resolve())
    Ctx.cat, Ctx.build, Ctx.chk = gen.module("catalogue"), gen.module("build"), gen.module("check")
    for d in ("work", "chk-py", "chk-param"): (Ctx.OUT / d).mkdir(parents=True, exist_ok=True)
    lines = gen.codes()
    jobs = int(os.environ.get("GW_JOBS", "4"))
    with ProcessPoolExecutor(max_workers=jobs, mp_context=get_context("fork")) as ex:
        rows = list(ex.map(do_code, lines))
        plans = Ctx.plans["rebuild"]
        rbs = list(ex.map(do_rebuild, plans))
    pr, ins = probes()
    lim = limits()
    json.dump(rows, open(Ctx.OUT / "report.json", "w"), indent=1)
    json.dump(dict(rebuild=rbs, insert=ins, probes=pr, limits=lim), open(Ctx.OUT / "rebuild.json", "w"), indent=1)
    md = [f"# {S.gid}: generator package on SolidCraft 0.50.0 vs the Python generator", "",
          "Measures: volume mm3 / area mm2 / bbox / faces f, bodies b. Parametric = configuration row + parameters on the single .sc; Python = build.py with appearance off.", "",
          "| code | python | parametric | spec: parametric | spec: Python (appearance off) | equal |", "|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['code']} | {r['python']} | {r['param']} | {r.get('check', '-')} | {r.get('pycheck', '-')} | {r['same']} |")
    md += ["", "## Rebuild on a free parameter change", ""]
    for x in rbs:
        md.append(f"- {x['label']}: " + (f"ERROR {json.dumps(x['error'])[:200]}" if "error" in x else f"== fresh instance {x['same_fresh']}, == Python {x['same_python']}; rebuilt {fmt(x['rebuilt'])}"))
    md += ["", "## Link behaviour (0.50.0)", ""] + [f"- {k}: {v}" for k, v in pr.items()]
    md += ["", "## Where the limits apply", ""] + [f"- {k}: {v}" for k, v in lim.items()]
    (Ctx.OUT / "report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))
