"""The parametric model shared by the HIWIN EG, HG and RG guideway generators (SolidCraft 0.50.0): ONE design per series with a rail
(counterbored or tapped holes at pitch P, count from `length`), N blocks (U profile over the rail, mounting holes, count from `blocks`)
and a configuration table, built from the catalogue tables through each series' catalogue.py (so the numbers are the Python generator's).

What a row is: one product of one catalogue row.
    set   <block>-<size>[-<rail mount>]   rail + blocks
    block <block>-<size>-block            the block alone (rail features suppressed, rail = 0 puts it at x = 0 like the Python part)
    rail  <series>R-<size>[-<rail mount>] the rail alone (block features suppressed)
Suppression columns pick, per row, which of the alternative features exist: the rail hole (counterbore, or a tapped hole of the
size's thread, HG only), the block hole (the thread designation of the row, or the through hole; EG adds a second hole column that
the short S block does not have). `length` and `blocks` are free parameters: columns too, so that the range rules check them.

    python3 gw_model.py SERIES OUTDIR      writes OUTDIR/template.json
"""
from __future__ import annotations
import csv, importlib, json, sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))

def c(command, **p):
    return {"command": command, "params": p}

def g10(x):
    return format(float(x), ".10g")

@dataclass
class Series:
    key: str                    # "EG"
    dirname: str                # "eg"
    gid: str                    # "hiwin.eg.guideway"
    kinds: str                  # block kinds: "HW"
    loads: str
    mounts: dict                # kind -> mounting letters tried
    rail_mounts: tuple          # ("R",) or ("R", "T")
    extra_columns: tuple = ()   # ("hT",) HG, ("C1",) RG
    tol: str = "0.000001 mm"    # added inside floor() of the hole count: float noise of unit conversion (the Python RG generator has 1e-9)
    layouts: tuple = ()         # hole layouts, filled below

    @property
    def cat(self):
        return importlib.import_module(f"vendors.hiwin.{self.dirname}.guideway.src.catalogue")

    @property
    def rm_in_name(self):
        return len(self.rail_mounts) > 1

SERIES = {
    "EG": Series("EG", "eg", "hiwin.eg.guideway", "HW", "SC", {"H": "A", "W": "AB"}, ("R",)),
    "HG": Series("HG", "hg", "hiwin.hg.guideway", "HW", "CH", {"H": "A", "W": "ABC"}, ("R", "T"), extra_columns=("hT", "tap")),
    "RG": Series("RG", "rg", "hiwin.rg.guideway", "HW", "CH", {"H": "A", "W": "C"}, ("R",), extra_columns=("C1",)),
}

BASE_COLUMNS = ["size", "rail", "WR", "HR", "D", "h", "d", "P", "Es", "Elo", "minlen", "maxlen", "W", "H", "H1", "L1", "L", "B", "C", "Mdepth", "hole_d"]
NOUNIT = {"size", "rail", "blocks", "tap"}

def columns(S: Series):
    return BASE_COLUMNS + list(S.extra_columns)

# ----------------------------------------------------------------------------------------------------------------------- catalogue rows
@dataclass
class Block:
    kind: str; load: str; mount: str; size: str
    d: dict
    src: dict          # source, page, status of the data row
    @property
    def key(self):     # "EGH-SA"
        return f"{self.series}{self.kind}-{self.load}{self.mount}"
    series: str = ""
    @property
    def hole_key(self):          # which block hole feature this row keeps
        return "through" if self.d["hole"] == "through" else self.d["M"]

def blocks_of(S: Series):
    cat = S.cat
    out = {}
    for size in cat.SIZES:
        for kind in S.kinds:
            for load in S.loads:
                for mount in S.mounts[kind]:
                    try:
                        d = cat.block_dims(kind, size, load, mount)
                    except cat.CodeError:
                        continue
                    out.setdefault(size, []).append(Block(kind, load, mount, size, d, source_of(S, kind, size), S.key))
    return out

def source_of(S: Series, kind, size):
    f = HERE.parents[0] / S.dirname / "guideway" / "data" / f"{S.key.lower()}{kind.lower()}.csv"
    for r in csv.DictReader(f.open()):
        if r["size"] == size:
            return {"source": r["source"], "page": r["page"], "status": r["status"]}
    raise KeyError((S.key, kind, size))

def rail_source(S: Series, size):
    f = HERE.parents[0] / S.dirname / "guideway" / "data" / "rails.csv"
    for r in csv.DictReader(f.open()):
        if r["size"] == size:
            return {"source": r["source"], "page": r["page"], "status": r["status"]}

def thread_set(S: Series, blocks):
    """thread designations of the block holes, in table order; and whether any block has through holes"""
    ms, through = [], False
    for size in S.cat.SIZES:
        for b in blocks.get(size, []):
            if b.d["hole"] == "through": through = True
            elif b.d["M"] not in ms: ms.append(b.d["M"])
    return sorted(ms, key=lambda m: int(m[1:])), through       # smallest first: a later (larger) hole must still find material to thread

def rail_threads(S: Series):
    out = []
    if "T" in S.rail_mounts:
        for size in S.cat.SIZES:
            t = S.cat.RAILS[size]["S"]
            if t not in out: out.append(t)
    return out

# ----------------------------------------------------------------------------------------------------------------------- features
def layout_tags(S: Series):
    return ("col 1", "col 2") if S.key == "EG" else ("",)

def feature_names(S: Series, blocks):
    ms, through = thread_set(S, blocks)
    taps = rail_threads(S)
    rail = ["Rail", "Rail hole 1"] + [f"Rail hole tap {t}" for t in taps] + ["Rail holes"]
    holes = []
    for tag in layout_tags(S):
        for m in ms:
            holes.append(f"Block threads {m}" + (f" {tag}" if tag else ""))
        if through:
            holes.append("Block through holes" + (f" {tag}" if tag else ""))
    blockf = ["Block"] + holes + ["Blocks"]
    return rail, blockf, holes, taps, ms

def row_list(S: Series, blocks):
    """[(product, Block or None, size, rail_mount or None)]"""
    rows = []
    for size in S.cat.SIZES:
        for rm in S.rail_mounts:
            rows.append(("rail", None, size, rm))
        for b in blocks[size]:
            for rm in S.rail_mounts:
                rows.append(("set", b, size, rm))
            rows.append(("block", b, size, None))
    return rows

def row_name(S: Series, product, b, size, rm):
    suffix = f"-{rm}" if S.rm_in_name and rm else ""
    if product == "rail": return f"{S.key}R-{size}{suffix}"
    if product == "block": return f"{b.key}-{size}-block"
    return f"{b.key}-{size}{suffix}"

def row_values(S: Series, blocks, product, b, size, rm):
    cat = S.cat
    r = cat.RAILS[size]
    ref = b or blocks[size][0]            # a rail row carries the first block of the size as unused placeholder values
    d = ref.d
    mm = lambda x: f"{g10(x)} mm"
    v = dict(size=size, rail="0" if product == "block" else "1", WR=mm(r["WR"]), HR=mm(r["HR"]), D=mm(r["D"]), h=mm(r["h"]), d=mm(r["d"]),
             P=mm(r["P"]), Es=mm(r["Es"]), Elo=mm(min(r["Es"], r["P"] / 2) if S.key == "RG" else r["Es"]),
             minlen=mm(max(getattr(cat, "MIN_LEN", 0.0), 2 * r["Es"])), maxlen=mm(cat.MAX_LEN),
             W=mm(d["W"]), H=mm(d["H"]), H1=mm(d["H1"]), L1=mm(d["L1"]), L=mm(d["L"]), B=mm(d["B"]),
             C=mm(d["C"] or 0), Mdepth=mm(d["M_depth"] or 1), hole_d=mm(d.get("hole_d") or 1))
    if "hT" in S.extra_columns: v["hT"] = mm(r["hT"])
    if "tap" in S.extra_columns: v["tap"] = str(int(r["S"][1:])) if rm == "T" else "0"      # the thread of a bottom-mounted rail: selects the tap feature
    if "C1" in S.extra_columns: v["C1"] = mm(d.get("C1") or d["C"])
    v["length"] = "400 mm"; v["blocks"] = "1"
    return v

def suppressed(S: Series, blocks, product, b, size, rm):
    rail, blockf, holes, taps, ms = feature_names(S, blocks)
    sup = set()
    if product == "block": sup |= set(rail)
    if product == "rail": sup |= set(blockf)
    if product != "block":
        if rm == "T":
            sup.add("Rail hole 1"); sup |= {f"Rail hole tap {t}" for t in taps if t != S.cat.RAILS[size]["S"]}
        else:
            sup |= {f"Rail hole tap {t}" for t in taps}
    if product != "rail":
        want = b.hole_key
        for h in holes:
            tag = next((t for t in layout_tags(S) if t and h.endswith(" " + t)), "")
            is_through = h.startswith("Block through")
            m = None if is_through else h.split()[2]
            if (want == "through") != is_through or (not is_through and m != want): sup.add(h)
            if tag == "col 2" and not b.d["C"]: sup.add(h)       # the short S block has one column of holes
    return sup

# ----------------------------------------------------------------------------------------------------------------------- commands
def commands(S: Series, rules_mode="expr"):
    blocks = blocks_of(S)
    rail_f, block_f, holes, taps, ms = feature_names(S, blocks)
    through = any(h.startswith("Block through") for h in holes)
    rows = row_list(S, blocks)
    cols = columns(S)
    # the parameters start at the values of the LAST set row (largest size, a block with two hole columns): every alternative feature is
    # modelled once before the table suppresses them, so each must find material at those values (a thread needs a cylindrical face)
    first = row_values(S, blocks, *next(r for r in reversed(rows) if r[0] == "set" and r[1].d["hole"] == "thread" and r[1].d["C"]))
    cm = []
    for k in cols:
        cm.append(c("parameters.add", name=k, expression=first[k] if k != "rail" else "1", **({"unit": ""} if k in NOUNIT else {})))
    n_expr = f"floor((length - 2 * Elo + {S.tol}) / P) + 1"
    cm += [c("parameters.add", name="length", expression=first["length"]),
           c("parameters.add", name="blocks", expression="1", unit=""),
           c("parameters.add", name="gap", expression="10 mm"),
           c("parameters.add", name="n", expression=n_expr, unit=""),
           c("parameters.add", name="E", expression="(length - (n - 1) * P) / 2"),
           c("parameters.add", name="x0", expression="rail * length / 2 - (blocks - 1) * (L + gap) / 2 - L1 / 2")]
    notes = dict(n="rail holes: L = (n-1)P + 2E, the most holes whose end distance E is at least the smallest end distance Elo", E="end distance",
                 gap="illustration choice, not a catalogue value", rail="1 = rail present; 0 = block alone, placed at x = 0",
                 Elo="smallest end distance (Es; RG: min(Es, P/2))", minlen="shortest rail", maxlen="longest single rail",
                 x0="start of the first block: blocks centred on the rail (rail = 1) or on x = 0 (block alone)")
    for k, txt in notes.items():
        cm.append(c("parameters.comment", name=k, comment=txt))
    # ---- rail: along +X from 0, centred on Y, bottom at z = 0; hole 1 at x = E, n holes at pitch P
    cm.append(c("solid.box", length="length", width="WR", height="HR", corner=[0, "-WR / 2", 0], operation="new", body_name="Rail", name="Rail"))
    cm.append(c("sketch.create", plane={"origin": [0, 0, "HR"], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name="Rail hole"))
    cm += [c("sketch.point", point=["E", 0]), c("sketch.finish")]
    if taps:       # one sketch and one tap per thread. A tap sits at x = E only when `tap` is its size; the others are displaced (the
        # alternatives must not cut into each other while all of them exist: a thread needs a cylindrical face), the row suppresses them anyway
        for tp in taps:
            k = tp[1:]
            cm.append(c("sketch.create", plane={"origin": [0, 0, 0], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name=f"Rail hole bottom {tp}"))
            cm += [c("sketch.point", point=[f"E + max(tap - {k}, {k} - tap) * 20 mm", 0]), c("sketch.finish")]
            cm.append(c("solid.hole", sketch=f"Rail hole bottom {tp}", thread=tp, depth="hT", targets=["Rail"], name=f"Rail hole tap {tp}"))
    cm.append(c("solid.hole", sketch="Rail hole", diameter="d", type="counterbore", cb_diameter="D", cb_depth="h", targets=["Rail"], name="Rail hole 1"))
    cm.append(c("solid.pattern.rectangular", features=[f for f in rail_f if f.startswith("Rail hole ")], dir1=[1, 0, 0], count1="n", spacing1="P", name="Rail holes"))
    # ---- block: U profile (rail channel cut in) extruded over L1, then the mounting holes of the row's kind
    pts = [("-W/2", "H1"), ("-WR/2", "H1"), ("-WR/2", "HR"), ("WR/2", "HR"), ("WR/2", "H1"), ("W/2", "H1"), ("W/2", "H"), ("-W/2", "H")]
    cm.append(c("sketch.create", plane={"origin": ["x0", 0, 0], "x_dir": [0, 1, 0], "y_dir": [0, 0, 1]}, name="Block profile"))
    ids = []
    for i, (a, b2) in enumerate(pts):
        nx = pts[(i + 1) % len(pts)]
        ids.append(f"l{i + 1}")
        cm.append(c("sketch.line", ids=[ids[-1]], points=[[a, b2], list(nx)], construction=False))
    cm.append(c("sketch.finish"))
    cm.append(c("solid.extrude", sketch="Block profile", profiles=[{"sketch": "Block profile", "loops": [{"curves": ids, "outer": True}]}], distance="L1",
                direction="positive", operation="new", body_name="Block", name="Block"))
    hidden = ["Rail hole", "Block profile"] + [f"Rail hole bottom {tp}" for tp in taps]
    cx = "x0 + L1 / 2"
    for tag in layout_tags(S):
        if S.key == "EG":
            dx = "-" if tag == "col 1" else "+"
            points = [[f"{cx} {dx} C / 2", f"({sy}) * B / 2"] for sy in ("-1", "1")]
        elif S.key == "HG":
            points = [[f"{cx} + ({sx}) * C / 2", f"({sy}) * B / 2"] for sx in ("-1", "1") for sy in ("-1", "1")]
        else:       # RG: four flange holes C x B and two on the rail axis C1 apart (C1 = C for RGH)
            points = [[f"{cx} + ({sx}) * C / 2", f"({sy}) * B / 2"] for sx in ("-1", "1") for sy in ("-1", "1")]
            points += [[f"{cx} + ({sx}) * C1 / 2", 0] for sx in ("-1", "1")]
        sk = "Block holes" + (f" {tag}" if tag else "")
        hidden.append(sk)
        cm.append(c("sketch.create", plane={"origin": [0, 0, "H"], "x_dir": [1, 0, 0], "y_dir": [0, 1, 0]}, name=sk))
        cm += [c("sketch.point", point=p) for p in points] + [c("sketch.finish")]
        sfx = f" {tag}" if tag else ""
        for m in ms:
            cm.append(c("solid.hole", sketch=sk, thread=m, depth="Mdepth", name=f"Block threads {m}{sfx}"))
        if through:
            cm.append(c("solid.hole", sketch=sk, diameter="hole_d", name=f"Block through holes{sfx}"))
    cm.append(c("solid.pattern.rectangular", features=["Block"] + holes, dir1=[1, 0, 0], count1="blocks", spacing1="L + gap", name="Blocks"))
    cm.append(c("browser.visibility", items=hidden, visible=False))
    # ---- configuration table
    allf = rail_f + block_f
    cm.append(c("config.configure", params=cols + ["length", "blocks"], features=allf))
    for product, b, size, rm in rows:
        vals = {f"param:{k}": x for k, x in row_values(S, blocks, product, b, size, rm).items()}
        sup = suppressed(S, blocks, product, b, size, rm)
        vals.update({f"suppress:{f}": ("true" if f in sup else "false") for f in allf})
        cm.append(c("config.row", name=row_name(S, product, b, size, rm), values=vals))
    cm.append(c("config.row", name="Default", delete=True))
    # ---- rules: the catalogue's limits. They are checked when a row is activated (0.50.0)
    rules = []
    if rules_mode == "expr":
        rules.append(dict(id="length-range", name="Rail length: the catalogue minimum and the largest single rail", condition=dict(type="always"),
                          effect=dict(type="parameter_range", parameter="length", minimum="minlen", maximum="maxlen")))
        rules.append(dict(id="blocks-fit", name="Blocks that fit on the rail with the gap between them", condition=dict(type="always"),
                          effect=dict(type="parameter_range", parameter="blocks", minimum="1", maximum="floor((length + gap) / (L + gap))")))
    else:
        for size in S.cat.SIZES:
            r = S.cat.RAILS[size]
            lo = max(getattr(S.cat, "MIN_LEN", 0.0), 2 * r["Es"])
            rules.append(dict(id=f"len-{size}", name=f"{S.key}R{size} rail lengths", condition=dict(type="parameter", parameter="size", operator="eq", expression=size),
                              effect=dict(type="parameter_range", parameter="length", minimum=f"{g10(lo)} mm", maximum=f"{g10(S.cat.MAX_LEN)} mm")))
        rules.append(dict(id="blocks-range", name="1 to 99 blocks", condition=dict(type="always"),
                          effect=dict(type="parameter_range", parameter="blocks", minimum="1", maximum="99")))
    from runtime.parametric import limit_rules
    cm.append(c("config.rule", rules=limit_rules(rules)))
    return cm

if __name__ == "__main__":
    S = SERIES[sys.argv[1]]; out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    mode = sys.argv[3] if len(sys.argv) > 3 else "expr"
    (out / "template.json").write_text(json.dumps({"commands": commands(S, mode)}, indent=1))
    print(out / "template.json", len(commands(S, mode)), "commands")
