#!/usr/bin/env python3
"""End-to-end: every code in ../../codes.txt through the generator package (template -> Rhai -> configuration row + parameters ->
parametric design) on SolidCraft 0.50.0, beside the Python generator's part. Run where SC_CLI is set, from the repo root:
    python3 vendors/hiwin/mg/rail-set/parametric/harness/run_all.py OUTDIR
Writes OUTDIR/report.md and OUTDIR/report.json."""

import json, os, re, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE))
from runtime.parametric.package import Package
from runtime.parametric.absolute import AbsoluteHarness, c, fmt, same
from runtime import registry, sc
import runtime.check as rc

OUT = Path(sys.argv[1]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
io = AbsoluteHarness(OUT)
run, measure = io.run, io.measure
PKGDIR = HERE.parent / "mg-rail-set"
PKG = Package(PKGDIR)
TEMPLATE = str((PKGDIR / "mg-rail-set.sc").resolve())
GEN = registry.find("MGN12H2R300Z0C")
cat, build, chk = GEN.module("catalogue"), GEN.module("build"), GEN.module("check")





def python_part(code, caps, tag):
    s = cat.parse(code)
    cmds = build.commands(s, appearance=False, screws=False, caps=False)
    if caps:     # the Python generator builds caps only with appearance on; same cylinders, nothing else
        r = s.rail; cs = build.CAP_SIZES[s.size]
        cmds = [x for x in cmds if x["command"] not in ("browser.visibility",)]
        for j in range(s.holes):
            cmds.append(c("solid.cylinder", diameter=r["D"], height=cs["H"], base=[s.end_distance + j * r["P"], 0, r["HR"] - cs["H"]], axis="Z",
                          operation="new", body_name=f"Rail cap {j + 1}", name=f"Rail cap {j + 1}"))
    path, _ = sc.run_script(cmds, str(OUT), f"py-{tag}")
    return s, path

def instance(parsed, caps, tag):
    """The parametric part at a configuration row and parameter values: 0.50.0 has no free parameters on insert_design, so the values are
    set in a copy of the design (config.activate, parameters.change), which is then the file that gets inserted."""
    ps = dict(parsed["parameters"]); ps["caps"] = "1" if caps else "0"
    cmds = [c("config.activate", row=parsed["configuration"]), c("parameters.change", changes=ps),
            c("document.metadata.set", values={"part_number": tag_code[tag]})]
    path = OUT / f"inst-{tag}.sc"
    j, err = run(cmds, f"inst-{tag}", base=TEMPLATE, save=path)
    return (str(path), err)

# ---- check wrapper: body names of the pattern copies (Body1, ...) -> Block i; caps bodies and the component metadata row
def renaming(code):
    real = rc.run_measure
    def wrapped(sc_path, cmds, out_dir, name):
        keep = [x for x in cmds if x["command"] != "component.metadata"]
        res = real(sc_path, keep, out_dir, name)
        it = iter(res); out = []
        for x in cmds:
            out.append({"metadata": {"part_number": None}} if x["command"] == "component.metadata" else next(it))
        meas = next((r for x, r in zip(cmds, out) if x["command"] == "inspect.measure"), None)
        if meas:
            hr = None
            blocks = [b for b in meas["bodies"] if b["name"] != "Rail" and b["bbox"]["max"][2] > RAILHR[0] + 1e-6]
            blocks.sort(key=lambda b: b["bbox"]["min"][0])
            mapping = {b["name"]: f"Block {i + 1}" for i, b in enumerate(blocks)}
            for b in meas["bodies"]:
                if b["name"] in mapping: b["name"] = mapping[b["name"]]
            meas["bodies"] = [b for b in meas["bodies"] if b["name"] == "Rail" or b["name"] in mapping.values()]
            for x, r in zip(cmds, out):
                if x["command"] == "model.threads":
                    for t in r["threads"]:
                        for b in blocks:
                            if b["bbox"]["min"][0] - 1e-6 <= t["axis_point"][0] <= b["bbox"]["max"][0] + 1e-6: t["body"] = f"Block {blocks.index(b) + 1}"
                if x["command"] == "document.metadata":
                    pn = json.dumps(r)
                    m = re.search(r'"part_number":\s*"([^"]+)"', pn)
                    for y, r2 in zip(cmds, out):
                        if y["command"] == "component.metadata": r2["metadata"]["part_number"] = m.group(1) if m else None
        return out
    return wrapped
RAILHR = [0.0]

def spec_check(s, path, tag):
    RAILHR[0] = s.rail["HR"]
    chk.run_measure = renaming(s.code)
    try:
        R = chk.check_mgn_dimensioned(s, path, str(OUT))
    finally:
        chk.run_measure = rc.run_measure
    bad = [r[1] for r in R.rows if not r[0]]
    return len(R.rows), bad

rows, notes = [], []
tag_code = {}
for line in GEN.codes():
    tag = line.name
    caps = bool(line.opts.get("caps"))
    r = PKG.parse(line.code)
    if not line.valid:
        try: build.parse_build(line.code); pymsg = "ACCEPTED"
        except ValueError as ex: pymsg = str(ex)
        rows.append(dict(code="!" + line.code, python=pymsg, param=("REFUSED: " + r["message"]) if not r["ok"] else "ACCEPTED", same=(not r["ok"]) and r["message"] == pymsg, check="-"))
        continue
    assert r["ok"], r
    # round trip: code -> fields -> code
    canon = PKG.code(r["fields"]); rt = PKG.parse(canon)
    tag_code[tag] = line.code
    s, pypath = python_part(line.code, caps, tag)
    pm = measure(pypath, f"m-py-{tag}")
    ipath, err = instance(r, caps, tag)
    if err:
        rows.append(dict(code=line.code + (" caps" if caps else ""), python=fmt(pm), param="ERROR " + json.dumps(err)[:200], same=False, check="-")); continue
    am = measure(ipath, f"m-inst-{tag}")
    n, bad = spec_check(s, ipath, tag)
    pn, pbad = spec_check(s, pypath, tag)
    rows.append(dict(code=line.code + (" caps" if caps else ""), configuration=r["configuration"], parameters=r["parameters"], roundtrip=(canon, rt["fields"] == r["fields"]),
                     python=fmt(pm), param=fmt(am), same=same(pm, am), python_m=pm, param_m=am, check=f"{n - len(bad)}/{n}" + (" FAIL: " + "; ".join(bad) if bad else ""), pycheck=f"{pn - len(pbad)}/{pn}" + (" FAIL: " + "; ".join(pbad) if pbad else ""), template_idx=r["template"]))
json.dump(rows, open(OUT / "report.json", "w"), indent=1)

# ---------------------------------------------------------------------------------------------- insertion (0.50.0)
def short(err): return json.dumps(err)[:300]
ins_rows = []
for r_ in rows:
    pass
for line in GEN.codes():
    if not line.valid: continue
    tag = line.name; ip = OUT / f"inst-{tag}.sc"
    asm = OUT / f"asm-{tag}.sc"
    j, err = run([c("component.insert_design", path=str(ip)), c("inspect.measure")], f"asm-{tag}", save=asm)
    if err: ins_rows.append((line.code, "ERROR " + short(err), False)); continue
    m = j[1]; b = m["bodies"]
    inst = measure(str(ip), f"m-inst2-{tag}")
    am = dict(vol=m["total"]["volume_mm3"], area=m["total"]["area_mm2"], faces=m["total"]["faces"], bodies=len(b),
              lo=[min(x["bbox"]["min"][i] for x in b) for i in range(3)], hi=[max(x["bbox"]["max"][i] for x in b) for i in range(3)])
    ins_rows.append((line.code + (" caps" if "caps" in line.opts else ""), fmt(am), same(inst, am), j[0]))

# configuration on insert (0.50.0): the row alone, defaults length 300 and blocks 1
probe = {}
j, err = run([c("component.insert_design", path=TEMPLATE, configuration="H-12"), c("inspect.measure")], "p-insert-config")
probe["insert_design configuration=H-12"] = short(err) if err else "ok"
if not err:
    b = j[1]["bodies"]; m = j[1]["total"]
    am = dict(vol=m["volume_mm3"], area=m["area_mm2"], faces=m["faces"], bodies=len(b), lo=[min(x["bbox"]["min"][i] for x in b) for i in range(3)], hi=[max(x["bbox"]["max"][i] for x in b) for i in range(3)])
    s2, p2 = python_part("MGN12H1R300Z0C", False, "row-default"); pm2 = measure(p2, "m-py-row-default")
    probe["row H-12 inserted == Python MGN12H1R300Z0C"] = f"{same(pm2, am)}; python {fmt(pm2)}; inserted {fmt(am)}"
j, err = run([c("component.insert_design", path=TEMPLATE, configuration="H-12", parameters={"length": "400 mm"}), c("inspect.measure")], "p-insert-params")
probe["insert_design configuration=H-12 parameters={length: 400 mm}"] = short(err) if err else "accepted, but rail x extent is " + str(max(b["bbox"]["max"][0] for b in j[1]["bodies"])) + " (300 = the parameters key is ignored)"
j, err = run([c("component.insert_design", path=TEMPLATE, configuration="H-12"), c("component.set_link_parameters", component=1, parameters={"length": "400 mm"})], "p-setlink")
probe["component.set_link_parameters"] = short(err) if err else "ok"
j, err = run([c("component.insert_design", path=TEMPLATE, configuration="H-12"), c("parameters.change", changes={"length": "400 mm"})], "p-asm-param")
probe["parameters.change length in the assembly that holds the link"] = short(err) if err else "accepted"
j, err = run([c("component.insert_design", path=TEMPLATE, configuration="nope")], "p-insert-badrow")
probe["insert_design configuration=nope"] = short(err) if err else "accepted"
j, err = run([c("component.insert_design", path=TEMPLATE, configuration="H-12"), c("component.links"), c("parameters.list")], "p-insert-links")
probe["links and parameters after insert (is the part still parametric?)"] = short(err) if err else json.dumps(j[1])[:300] + " | user parameters in the assembly: " + str([p["name"] for p in j[2].get("parameters", j[2]) ] if isinstance(j[2], dict) else j[2])[:200]

# ---------------------------------------------------------------------------------------------- rebuild on a length change
tag = [l for l in GEN.codes() if l.valid][0].name
code0 = "MGN12H2R300Z0C"; tag0 = tag_code and [t for t, cc in tag_code.items() if cc == code0 and "caps" not in t][0]
ip = OUT / f"inst-{tag0}.sc"; asm = OUT / f"asm-{tag0}.sc"
import shutil
shutil.copy(ip, OUT / "inst-before.sc")
j, err = run([c("parameters.change", changes={"length": "400 mm"}), c("inspect.measure")], "rebuild-inst", base=OUT / "inst-before.sc", save=OUT / "inst-after.sc")
rebuilt = None
rb = {}
if not err:
    m = j[1]; b = m["bodies"]
    rebuilt = dict(vol=m["total"]["volume_mm3"], area=m["total"]["area_mm2"], faces=m["total"]["faces"], bodies=len(b), lo=[min(x["bbox"]["min"][i] for x in b) for i in range(3)], hi=[max(x["bbox"]["max"][i] for x in b) for i in range(3)])
r400 = PKG.parse("MGN12H2R400Z0C"); tag_code["r400"] = "MGN12H2R400Z0C"
p400 = instance(r400, False, "r400")[0]; m400 = measure(p400, "m-inst-r400")
s4, py4 = python_part("MGN12H2R400Z0C", False, "r400"); pm400 = measure(py4, "m-py-r400")
rb["parameters.change length 300 -> 400 on the instance == fresh MGN12H2R400 instance"] = same(rebuilt, m400) if rebuilt else short(err)
rb["... == Python MGN12H2R400Z0C"] = same(rebuilt, pm400) if rebuilt else "-"
json.dump({"rebuilt": rebuilt, "fresh": m400, "python": pm400}, open(OUT / "rebuild.json", "w"))
rb["rebuilt " ] = fmt(rebuilt) if rebuilt else "-"; rb["fresh R400 instance"] = fmt(m400); rb["python R400"] = fmt(pm400)
# linked in an assembly: edit the linked file in place, update links
shutil.copy(ip, OUT / "linked.sc")
asm2 = OUT / "asm-linked.sc"
j, err = run([c("component.insert_design", path=str(OUT / "linked.sc"))], "asm-linked", save=asm2)
j2, err2 = run([c("parameters.change", changes={"length": "400 mm"})], "linked-edit", base=OUT / "linked.sc", save=OUT / "linked-new.sc")
shutil.copy(OUT / "linked-new.sc", OUT / "linked.sc")
j3, err3 = run([c("component.update_links"), c("inspect.measure")], "asm-update", base=asm2, save=OUT / "asm-linked-updated.sc")
if not err3:
    m = j3[1]; b = m["bodies"]
    am = dict(vol=m["total"]["volume_mm3"], area=m["total"]["area_mm2"], faces=m["total"]["faces"], bodies=len(b), lo=[min(x["bbox"]["min"][i] for x in b) for i in range(3)], hi=[max(x["bbox"]["max"][i] for x in b) for i in range(3)])
    rb["assembly: linked file edited to length 400, component.update_links == fresh R400 instance"] = same(am, m400)
    rb["update_links reply"] = json.dumps(j3[0])[:300]
else: rb["assembly update_links"] = short(err3)

# ---------------------------------------------------------------------------------------------- limits: where the rules apply
lim = {}
def tryit(label, cmds, base=TEMPLATE):
    j, err = run(cmds, "lim-" + re.sub(r"\W+", "_", label)[:40], base=base)
    lim[label] = ("ERROR " + short(err)) if err else "accepted: " + json.dumps(j[-1])[:200]
tryit("ordinary edit parameters.change length=3000 mm on MGN12 (max 2000)", [c("config.activate", row="H-12"), c("parameters.change", changes={"length": "3000 mm"})])
tryit("ordinary edit blocks=9 (max 4)", [c("config.activate", row="H-12"), c("parameters.change", changes={"blocks": "9"})])
tryit("ordinary edit caps=1 on MGN9 (caps only 12/15)", [c("config.activate", row="C-9"), c("parameters.change", changes={"caps": "1"})])
tryit("row with length 900 mm on MGN7 (max 600), config.activate", [c("config.row", name="bad7", **{"from": "C-7", "values": {"param:length": "900 mm"}}), c("config.activate", row="bad7")])
tryit("row with caps 1 on MGN9, config.activate", [c("config.row", name="bad9", **{"from": "C-9", "values": {"param:caps": "1"}}), c("config.activate", row="bad9")])
tryit("row with blocks 5, config.activate", [c("config.row", name="bad5", **{"from": "C-9", "values": {"param:blocks": "5"}}), c("config.activate", row="bad5")])
tryit("config.preview of a bad row (length 900 on MGN7)", [c("config.row", name="bad7", **{"from": "C-7", "values": {"param:length": "900 mm"}}), c("config.preview", row="bad7")])
tryit("ordinary edit length=30 mm on MGN12 (n would be 0: floor(-0.4)+1)", [c("config.activate", row="H-12"), c("parameters.change", changes={"length": "30 mm"})])

# ---------------------------------------------------------------------------------------------- report
md = ["# MG rail set: generator package on SolidCraft 0.50.0 vs the Python generator", "",
      "Measures: volume mm3 / area mm2 / bbox / faces f, bodies b. Parametric = config row + parameters on the single .sc, Python = build.py (appearance off, caps only as the same cylinders).", "",
      "| code | python | parametric | spec check on the parametric part | spec check on the Python part (appearance off) | equal |", "|---|---|---|---|---|---|"]
for r_ in rows:
    md.append(f"| {r_['code']} | {r_['python']} | {r_['param']} | {r_['check']} | {r_.get('pycheck', '-')} | {r_['same']} |")
md += ["", "## Configuration row and parameters per code", ""]
for r_ in rows:
    if "configuration" in r_: md.append(f"- {r_['code']}: row `{r_['configuration']}`, {r_['parameters']}, template {r_['template_idx']}, printed `{r_['roundtrip'][0]}` round trip {r_['roundtrip'][1]}")
md += ["", "## component.insert_design of the instance file into an assembly (measured in the assembly)", "", "| code | measure in assembly | equals instance |", "|---|---|---|"]
for x in ins_rows: md.append(f"| {x[0]} | {x[1]} | {x[2]} |")
md += ["", "## Insert with a configuration (0.50.0)", ""] + [f"- {k}: {v}" for k, v in probe.items()]
md += ["", "## Rebuild on a length change", ""] + [f"- {k}: {v}" for k, v in rb.items()]
md += ["", "## Where the limits apply", ""] + [f"- {k}: {v}" for k, v in lim.items()]
(OUT / "report.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
