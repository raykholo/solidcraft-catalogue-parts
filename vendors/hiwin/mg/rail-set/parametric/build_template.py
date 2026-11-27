#!/usr/bin/env python3
"""Writes template.json, the command list that models the HIWIN MG rail set ONCE, parametric (SolidCraft 0.50.0).

    python3 build_template.py OUTDIR      then:  solidcraft-cli run OUTDIR/template.json --save OUTDIR/mg-rail-set.sc

Everything size-dependent is a user parameter driven by a configuration table (one row per size and block type, values read
from ../data/rails.csv, blocks.csv, caps.csv). `length`, `blocks`, `gap` and `caps` are plain user parameters.
Dimensioned geometry only (rail with its holes, blocks with their threads, optional hole caps); no appearance bodies.
"""
import csv, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
def rows(name): return list(csv.DictReader((DATA / name).open()))
def c(command, **p): return {"command": command, "params": p}

RAILS = {r["size"]: r for r in rows("rails.csv")}
BLOCKS = rows("blocks.csv")
CAPS = {r["size"]: r for r in rows("caps.csv")}

# column -> (unit, source column(s)); values per row come from the csv
COLUMNS = ["size", "WR", "HR", "D", "h", "d", "P", "Es", "maxlen", "W", "H", "H1", "L1", "L", "B", "C", "Mdepth", "capH"]
NOUNIT = {"size", "blocks", "caps"}
FREE = ["length", "blocks", "caps"]   # configured too: rules range-check them and switch features on them; the row holds the defaults

def row_values(b):
    r = RAILS[b["size"]]; cap = CAPS.get(b["size"])
    v = dict(size=r["size"], WR=r["WR"], HR=r["HR"], D=r["D"], h=r["h"], d=r["d"], P=r["P"], Es=r["Es"], maxlen=r["max_len"],
             W=b["W"], H=b["H"], H1=b["H1"], L1=b["L1"], L=b["L"], B=b["B"], C=b["C"], Mdepth=b["M_depth"], capH=cap["H"] if cap else "1.2")   # sizes without a catalogue cap: placeholder, the caps features are suppressed there
    return {k: (x if k in NOUNIT else f"{x} mm") for k, x in v.items()}

def commands(fids=None):
    cm = []
    first = BLOCKS[0]
    v0 = row_values(first)
    # --- parameters: size columns (initial values = first row), then the free ones, then derived ones
    for k in COLUMNS:
        cm.append(c("parameters.add", name=k, expression=v0[k], **({"unit": ""} if k in NOUNIT else {})))
    cm += [c("parameters.add", name="length", expression="300 mm"),
           c("parameters.add", name="blocks", expression="1", unit=""),
           c("parameters.add", name="gap", expression="10 mm"),
           c("parameters.add", name="caps", expression="0", unit=""),
           c("parameters.add", name="n", expression="floor((length - 2 * Es) / P) + 1", unit=""),
           c("parameters.add", name="E", expression="(length - (n - 1) * P) / 2"),
           c("parameters.add", name="x0", expression="length / 2 - (blocks - 1) * (L + gap) / 2 - L1 / 2")]
    for k, txt in dict(n="holes: L = (n-1)P + 2E, HIWIN MG catalogue S4 p.85", E="end distance, S4 p.85", gap="illustration choice, not a catalogue value",
                       caps="1 = plastic bolt caps (MGN12, MGN15 only, S4 p.82 Table 2-4-9), appearance").items():
        cm.append(c("parameters.comment", name=k, comment=txt))
    # --- rail: along +X from 0, centred on Y, bottom at z=0; hole 1 at x=E, n holes at pitch P
    cm.append(c("solid.box", length="length", width="WR", height="HR", corner=[0, "-WR / 2", 0], operation="new", body_name="Rail", name="Rail"))
    cm.append(c("sketch.create", plane={"origin": [0, 0, "HR"], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="Rail hole"))
    cm += [c("sketch.point", point=["E", 0]), c("sketch.finish")]
    cm.append(c("solid.hole", sketch="Rail hole", diameter="d", type="counterbore", cb_diameter="D", cb_depth="h", targets=["Rail"], name="Rail hole 1"))
    cm.append(c("solid.pattern.rectangular", features=["Rail hole 1"], dir1=[1, 0, 0], count1="n", spacing1="P", name="Rail holes"))
    # --- hole caps (option): one cylinder per hole, flush in the counterbore; suppressed unless caps = 1 (rule below)
    cm.append(c("solid.cylinder", diameter="D", height="capH", base=["E", 0, "HR - capH"], axis="Z", operation="new", body_name="Rail cap", name="Rail cap 1"))
    cm.append(c("solid.pattern.rectangular", features=["Rail cap 1"], dir1=[1, 0, 0], count1="n", spacing1="P", name="Rail caps"))
    # --- block: U profile (rail channel cut in) extruded over L1, four threads; M2 or M3 feature is suppressed per row
    pts = [("-W/2", "H1"), ("-WR/2", "H1"), ("-WR/2", "HR"), ("WR/2", "HR"), ("WR/2", "H1"), ("W/2", "H1"), ("W/2", "H"), ("-W/2", "H")]
    cm.append(c("sketch.create", plane={"origin": ["x0", 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}, name="Block profile"))
    ids = []
    for i, (a, b) in enumerate(pts):
        nx = pts[(i + 1) % len(pts)]
        ids.append(f"l{i + 1}")
        cm.append(c("sketch.line", ids=[ids[-1]], points=[[a, b], list(nx)], construction=False))
    cm.append(c("sketch.finish"))
    cm.append(c("solid.extrude", sketch="Block profile", profiles=[{"sketch": "Block profile", "loops": [{"curves": ids, "outer": True}]}], distance="L1",
                direction="positive", operation="new", body_name="Block", name="Block"))
    cm.append(c("sketch.create", plane={"origin": [0, 0, "H"], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="Block holes"))
    cm += [c("sketch.point", point=[f"x0 + L1/2 + ({sx}) * C/2", f"({sy}) * B/2"]) for sx in ("-1", "1") for sy in ("-1", "1")] + [c("sketch.finish")]
    for m in ("M2", "M3"):
        cm.append(c("solid.hole", sketch="Block holes", thread=m, depth="Mdepth", name=f"Block threads {m}"))
    cm.append(c("solid.pattern.rectangular", features=["Block", "Block threads M2", "Block threads M3"], dir1=[1, 0, 0], count1="blocks", spacing1="L + gap", name="Blocks"))
    cm.append(c("browser.visibility", items=["Rail hole", "Block holes", "Block profile"], visible=False))
    # --- configuration table: one row per size and block type
    cm.append(c("config.configure", params=COLUMNS + FREE, features=["Block threads M2", "Block threads M3", "Rail cap 1", "Rail caps"]))
    for b in BLOCKS:
        vals = {f"param:{k}": x for k, x in row_values(b).items()}
        vals.update({"param:length": "300 mm", "param:blocks": "1", "param:caps": "0", "suppress:Rail cap 1": "true", "suppress:Rail caps": "true"})
        vals["suppress:Block threads M2"] = "false" if b["M"] == "M2" else "true"
        vals["suppress:Block threads M3"] = "false" if b["M"] == "M3" else "true"
        cm.append(c("config.row", name=f"{b['block']}-{b['size']}", values=vals))
    cm.append(c("config.row", name="Default", delete=True))   # the row SolidCraft seeds from the first parameter values
    if fids is None:
        return cm
    # --- ordered rules: option switch, ranges and allowed values (the catalogue's limits and refusals)
    rules = [dict(id="caps-off", name="No hole caps unless caps = 1", condition=dict(type="parameter", parameter="caps", operator="eq", expression="0"),
                  effect=dict(type="drive_suppression", feature=fids[f], value=True)) for f in ("Rail cap 1", "Rail caps")]
    rules[0]["id"], rules[1]["id"] = "caps-off-cap", "caps-off-pattern"
    for i, f in enumerate(("Rail cap 1", "Rail caps")):
        rules.append(dict(id=f"caps-on-{i}", name="Hole caps when caps = 1", condition=dict(type="parameter", parameter="caps", operator="eq", expression="1"),
                          effect=dict(type="drive_suppression", feature=fids[f], value=False)))
    rules.append(dict(id="caps-sizes", name="Caps exist for MGN12 and MGN15 only (S4 p.82 Table 2-4-9)", condition=dict(type="parameter", parameter="size", operator="lt", expression="12"),
                      effect=dict(type="allow_parameter_values", parameter="caps", expressions=["0"])))
    rules.append(dict(id="blocks-range", name="1 to 4 blocks", condition=dict(type="always"),
                      effect=dict(type="parameter_range", parameter="blocks", minimum="1", maximum="4")))
    for size, r in RAILS.items():
        rules.append(dict(id=f"len-{size}", name=f"MGNR{size} lengths, S4 p.85 Table 2-4-15", condition=dict(type="parameter", parameter="size", operator="eq", expression=size),
                          effect=dict(type="parameter_range", parameter="length", minimum=f"{2 * float(r['Es']):g} mm", maximum=f"{r['max_len']} mm")))
    cm.append(c("config.rule", rules=rules))
    return cm

if __name__ == "__main__":
    # stage 1 (no rules): template.json; stage 2 (needs feature ids, which rules take as numbers): `build_template.py OUT ids.json`
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    if len(sys.argv) > 2:
        fids = json.load(open(sys.argv[2]))
        (out / "rules.json").write_text(json.dumps({"commands": commands(fids)[len(commands()):]}, indent=1))
        print(out / "rules.json")
    else:
        (out / "template.json").write_text(json.dumps({"commands": commands()}, indent=1))
        print(out / "template.json")
