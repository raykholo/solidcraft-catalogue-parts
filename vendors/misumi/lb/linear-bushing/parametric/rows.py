"""The configuration rows of the parametric linear bushing, read from ../data/*.csv: one row per catalogue table row (and flange shape).

A row holds every dimension of the catalogue row (parameter columns) and says which features of the one model exist (suppression columns);
the code-level choices (single / double length, counterbore side, plating) are parameters set on top of a row.
"""
from __future__ import annotations
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime.table import read_csv, num

# the variants of the model (revolve profiles and flange kinds) and the hole sets: feature names, in timeline order
REVOLVES = ["Plain", "Grooved", "Round0", "RoundOff"]
FLANGES = ["Square", "Compact"]
# hole sets: a hole refers to the face it was picked on, so each variant of the body has its own sets: Near = counterbores on the flange face
# toward the barrel (x0 + T, the standard side), Far = on the face away from the barrel (x0, the Z types); the `opp` parameter switches them
HOLEVARS = [("Round0", 1), ("RoundOff", 2), ("Square", 3), ("Compact", 4)]      # the value of the `kind` parameter
HOLES = [f"Hole{v}{side}{i}" for v, _ in HOLEVARS for side in ("Near", "Far") if not (v == "RoundOff" and side == "Far") for i in (1, 2, 3, 4)]
def feature_names():
    f = []
    for v in REVOLVES: f += [f"Profile{v}", f"Revolve{v}"]
    for v in FLANGES: f += [f"{v}Sketch", f"{v}Flange"]
    return f + HOLES

# defaults of the columns a row does not use (reference values of a dr 6 row: they keep the derived parameters evaluable)
REF = dict(fl_h=28, fl_t=5, hole_d=3.5, cb_d=6, cb_t=3.1, pcd=20, sq_w=22, cp_a=20, cp_f=0, cp_w=18, x0=0, g_b=20, g_w=1.1, g_d1=11.5)

# table file -> (key columns, kind of rows, allowed shapes, series, layout, long?, pages (as the Python messages print them))
TABLES = [("short", None, "straight", "short"), ("medium", None, "straight", "medium"),
          ("flanged_long", ("round", "square"), "flanged", "long"), ("flanged_medium", ("round", "square"), "flanged", "medium"),
          ("compact_long", ("compact",), "compact", "long"), ("compact_medium", ("compact",), "compact", "medium"),
          ("pilot_long", None, "pilot", "long"), ("pilot_medium", None, "pilot", "medium"),
          ("center_long", None, "center", "long"), ("center_medium", None, "center", "medium")]

def g(x):
    return f"{x:g}"

def read(name):
    return read_csv(DATA / f"{name}.csv")

def make_rows():
    out = []
    n = 0
    for tab, shapes, kind, series in TABLES:
        for r in read(tab):
            r = {k: (v if k in ("source", "page", "status", "shape") else num(v)) for k, v in r.items()}
            dr = int(r["dr"])
            row_shapes = [None] if kind == "straight" else ([r["shape"]] if "shape" in r else list(shapes))
            for shape in row_shapes:
                n += 1
                name = f"{tab}-{shape + '-' if shape else ''}{dr}"
                L1 = r["L"] if r.get("L") is not None else r["L_single"]
                L2 = r.get("L_double")
                p = dict(REF)
                p.update(rowno=n, kind=0, od=r["D"], blen=L1, bore=dr, opp=0, plated=1 if (kind in ("pilot", "center") and series == "medium") else 0)
                if kind != "straight":
                    p.update(fl_h=r["H"], fl_t=r["T"], hole_d=r["d"], cb_d=r["d1"], cb_t=r["t"])
                    if r.get("pcd") is not None: p["pcd"] = r["pcd"]
                    p["x0"] = r["l"] if kind in ("pilot", "center") else 0
                if shape == "square": p["sq_w"] = r["W"]
                if shape == "compact": p.update(cp_a=r["A"], cp_f=r.get("F") or 0, cp_w=r["width"])
                if kind == "straight" and series == "medium": p.update(g_b=r["B"], g_w=r["W"], g_d1=r["D1"])
                # which features exist
                on = set()
                if kind == "straight": on.add("Plain" if series == "short" else "Grooved")
                elif shape == "round": on.add("Round0" if kind == "flanged" else "RoundOff")
                else: on.add("Plain")
                holes = set()
                hv = {"round": "Round0" if kind == "flanged" else "RoundOff", "square": "Square", "compact": "Compact"}.get(shape)
                if hv:
                    p["kind"] = dict(HOLEVARS)[hv]
                    holes = {f"Hole{hv}Near{i}" for i in ((1, 2, 3, 4) if (shape != "compact" or p["cp_f"]) else (1, 4))}
                feats = set(holes)
                for v in on: feats |= {f"Profile{v}", f"Revolve{v}"}
                for v in FLANGES:
                    if v.lower() == shape: feats |= {f"{v}Sketch", f"{v}Flange"}
                z_ok = kind in ("flanged", "compact") and series == "long" and dr <= 30 and not (kind == "compact" and dr == 5)
                out.append(dict(name=name, table=tab, shape=shape, dr=dr, kind=kind, holevar=hv, series=series, params=p, features=feats,
                                lengths=[L1] + ([L2] if L2 is not None else []), opp=[0, 1] if z_ok else [0],
                                plated=[0] if (kind == "straight" and series == "short") else ([1] if p["plated"] else [0, 1]),
                                source=r["source"], page=r["page"], status=r["status"]))
    return out

if __name__ == "__main__":
    rows = make_rows()
    print(len(rows), "rows")
    for r in rows[:3] + rows[-2:]: print(r["name"], r["params"], sorted(r["features"]), r["lengths"], r["opp"], r["plated"])
