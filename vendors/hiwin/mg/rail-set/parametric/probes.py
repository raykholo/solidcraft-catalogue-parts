#!/usr/bin/env python3
"""Feasibility probes for a parametric MG design on SolidCraft 0.50.0. Writes one command list per probe into probes/;
run.sh runs each through solidcraft-cli and prints the first error or the measurement."""
import json, sys
from pathlib import Path
OUT = Path(__file__).resolve().parent / "probes"
OUT.mkdir(exist_ok=True)
def c(command, **p): return {"command": command, "params": p}
def P(name, cmds): (OUT / f"{name}.json").write_text(json.dumps({"commands": cmds}, indent=1))

def params(extra=()):
    base = [c("parameters.add", name="length", expression="300 mm"), c("parameters.add", name="WR", expression="12 mm"),
            c("parameters.add", name="HR", expression="8 mm"), c("parameters.add", name="P", expression="25 mm"),
            c("parameters.add", name="Es", expression="10 mm")]
    return base + list(extra)

# p01: user parameters drive a box (expressions in dimensions)
P("p01_box_expr", params() + [c("solid.box", length="length", width="WR", height="HR", corner=[0, "-WR/2", 0], operation="new", body_name="Rail", name="Rail"),
    c("inspect.measure")])
# p02: box with numeric corner, param dims only
P("p02_box_param_dims", params() + [c("solid.box", length="length", width="WR", height="HR", corner=[0, -6, 0], operation="new", body_name="Rail", name="Rail"),
    c("inspect.measure")])
# p03: derived count parameter (unitless) and hole pattern whose count is the parameter
P("p03_pattern_count_expr", params([c("parameters.add", name="n", expression="floor((length - 2*Es)/P) + 1", unit="")]) + [
    c("solid.box", length="length", width="WR", height="HR", corner=[0, -6, 0], operation="new", body_name="Rail", name="Rail"),
    c("sketch.create", plane={"origin": [0, 0, 8], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="Rail hole"),
    c("sketch.point", point=[10, 0]), c("sketch.finish"),
    c("solid.hole", sketch="Rail hole", diameter=3.5, type="counterbore", cb_diameter=6, cb_depth=4.5, name="Rail hole 1"),
    c("solid.pattern.rectangular", features=["Rail hole 1"], dir1=[1, 0, 0], count1="n", spacing1="P", name="Rail holes"),
    c("inspect.measure")])
# p04: hole sketch point given as an expression
P("p04_point_expr", params() + [
    c("solid.box", length="length", width="WR", height="HR", corner=[0, -6, 0], operation="new", body_name="Rail", name="Rail"),
    c("sketch.create", plane={"origin": [0, 0, 8], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="Rail hole"),
    c("sketch.point", point=["Es", 0]), c("sketch.finish"),
    c("solid.hole", sketch="Rail hole", diameter=3.5, name="Rail hole 1"), c("inspect.measure")])

# ---- block probes
def bparams():
    return params([c("parameters.add", name=k, expression=v) for k, v in dict(W="27 mm", H="13 mm", H1="3 mm", L1="21.7 mm", L="34.7 mm", B="20 mm", C="15 mm", blocks="2", gap="10 mm").items() if k != "blocks"] + [c("parameters.add", name="blocks", expression="2", unit="")] +
                  [c("parameters.add", name="x0", expression="length/2 - (blocks-1)*(L+gap)/2 - L1/2")])
def ublock():
    pts = [("-W/2", "H1"), ("-WR/2", "H1"), ("-WR/2", "HR"), ("WR/2", "HR"), ("WR/2", "H1"), ("W/2", "H1"), ("W/2", "H"), ("-W/2", "H")]
    cmds = [c("sketch.create", plane={"origin": ["x0", 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}, name="Block profile")]
    ids = []
    for i, (a, b) in enumerate(pts):
        nxt = pts[(i + 1) % len(pts)]
        ids.append(f"l{i+1}")
        cmds.append(c("sketch.line", ids=[f"l{i+1}"], points=[[a, b], [nxt[0], nxt[1]]], construction=False))
    cmds.append(c("sketch.finish"))
    cmds.append(c("solid.extrude", sketch="Block profile", profiles=[{"sketch": "Block profile", "loops": [{"curves": ids, "outer": True}]}], distance="L1",
                  direction="positive", operation="new", body_name="Block", name="Block"))
    return cmds
P("p05_block_uprofile", bparams() + ublock() + [c("inspect.measure")])
P("p06_block_pattern", bparams() + ublock() + [
    c("solid.pattern.rectangular", features=["Block"], dir1=[1, 0, 0], count1="blocks", spacing1="L + gap", name="Blocks"), c("inspect.measure")])
holes = [c("sketch.create", plane={"origin": [0, 0, "H"], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="Block holes")] + \
    [c("sketch.point", point=[f"x0 + L1/2 + ({sx})*C/2", f"({sy})*B/2"]) for sx in ("-1", "1") for sy in ("-1", "1")] + [c("sketch.finish"),
     c("solid.hole", sketch="Block holes", thread="M3", depth="3.5 mm", targets=["Block"], name="Block threads M3")]
P("p07_block_holes_pattern", bparams() + ublock() + holes + [
    c("solid.pattern.rectangular", features=["Block", "Block threads M3"], dir1=[1, 0, 0], count1="blocks", spacing1="L + gap", name="Blocks"), c("inspect.measure"), c("model.threads")])


# ---- block pattern variants
holes_nt = [c("sketch.create", plane={"origin": [0, 0, "H"], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="Block holes")] + \
    [c("sketch.point", point=[f"x0 + L1/2 + ({sx})*C/2", f"({sy})*B/2"]) for sx in ("-1", "1") for sy in ("-1", "1")] + [c("sketch.finish"),
     c("solid.hole", sketch="Block holes", thread="M3", depth="3.5 mm", name="Block threads M3")]
mm = [c("inspect.measure"), c("model.threads")]
P("p08_features_no_target", bparams() + ublock() + holes_nt + [
    c("solid.pattern.rectangular", features=["Block", "Block threads M3"], dir1=[1, 0, 0], count1="blocks", spacing1="L + gap", name="Blocks")] + mm)
P("p09_body_pattern", bparams() + ublock() + holes + [
    c("solid.pattern.rectangular", bodies=["Block"], dir1=[1, 0, 0], count1="blocks", spacing1="L + gap", name="Blocks")] + mm)
P("p10_body_pattern_names", bparams() + ublock() + holes + [
    c("solid.pattern.rectangular", bodies=["Block"], dir1=[1, 0, 0], count1="blocks", spacing1="L + gap", name="Blocks", body_names=["Block", "Block 2"], operation="new")] + mm)
print("wrote", len(list(OUT.glob("*.json"))), "probes")
