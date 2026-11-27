"""The configuration rows of the parametric oil free bushing, read from ../data/*.csv: one row per (type, d), i.e. per catalogue table row and
type (the thin wall types and the three copper flange shapes share a table). A row holds the dimensions of the catalogue row and says which
features of the one model exist; the length L is the free parameter, with the row's printed lengths as its allowed values."""
from __future__ import annotations
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from runtime.table import read_csv, num

REVOLVES = ["Plain", "Flange"]
FLANGES = ["Square", "Compact"]
HOLES = [f"AxisHole{i}" for i in (1, 2, 3, 4)] + [f"CompactHole{i}" for i in (1, 2, 3, 4)]
def feature_names():
    f = []
    for v in REVOLVES: f += [f"Profile{v}", f"Revolve{v}"]
    for v in FLANGES: f += [f"{v}Sketch", f"{v}Flange"]
    return f + HOLES

# defaults of the columns a row does not use (reference values of a d 16 row: they keep the derived parameters evaluable)
REF = dict(fl_h=40, fl_t=5, hole_d=4.5, cb_d=7.5, cb_t=3, pcd=30, sq_w=31, cp_a=24, cp_f=18, cp_w=28)

def offered(tokens, thin=False, square=False):
    """The L values the catalogue row offers (the Python generator's rule): (n) only for the standard wall / round and compact flanges,
    n* only for the thin wall type."""
    out = []
    for t in str(tokens).split():
        if t.startswith("("):
            if thin or square: continue
        elif t.endswith("*"):
            if not thin: continue
        out.append(int(t.strip("()*")))
    return out

def params():
    return {r["key"]: num(r["value"]) for r in read_csv(DATA / "params.csv")}

def make_rows():
    P = params()
    types = read_csv(DATA / "types.csv")
    out, n, skipped = [], 0, []
    for ty in types:
        thin, fam = ty["wall"] == "thin", ty["family"]
        for raw in read_csv(DATA / f"{ty['table']}.csv"):
            r = {k: (v if k in ("source", "page", "status", "lengths") else num(v)) for k, v in raw.items()}
            if thin and not r.get("D_thin"): continue
            d = int(r["dr"])
            lens = offered(r["lengths"], thin=thin, square=fam == "square")
            name = f"{ty['type']}-{d}"
            if not lens:
                skipped.append(name); continue
            n += 1
            p = dict(REF)
            p.update(rowno=n, od=r["D_thin"] if thin else r["D"], blen=lens[0], bore=d)
            if fam in ("shouldered", "thrust"):
                p.update(fl_h=r["H_thin"] if thin else r["H"], fl_t=r["t_thin"] if thin else r["t"])
            if fam in ("round", "square", "compact"):
                p.update(fl_h=r["H"], fl_t=r["T"], hole_d=r["d1"], cb_d=r["d2"], cb_t=r["t"])
                if r.get("pcd") is not None: p["pcd"] = r["pcd"]
                if fam == "square": p["sq_w"] = r["W"]
                if fam == "compact": p.update(cp_a=r["A"], cp_f=r.get("F") or 0, cp_w=r["D"] + P["compact_flat_extra"])
                if fam == "round": p["cp_f"] = r.get("F") or 0
            if fam != "square": p["sq_w"] = round(0.8 * p["fl_h"], 1)        # unused here; below H, so that sqrt() of the derived corner points stays real
            if fam != "compact": p["cp_w"] = round(0.8 * p["fl_h"], 1)
            feats = set()
            rev = "Plain" if fam in ("straight", "square", "compact") else "Flange"
            feats |= {f"Profile{rev}", f"Revolve{rev}"}
            if fam == "square": feats |= {"SquareSketch", "SquareFlange"} | {f"AxisHole{i}" for i in (1, 2, 3, 4)}
            if fam == "compact": feats |= {"CompactSketch", "CompactFlange"} | {f"CompactHole{i}" for i in ((1, 2, 3, 4) if p["cp_f"] else (1, 4))}
            if fam == "round": feats |= {f"AxisHole{i}" for i in ((1, 2, 3, 4) if p["cp_f"] else (2, 4))}
            out.append(dict(name=name, type=ty["type"], family=fam, wall=ty["wall"], table=ty["table"], dr=d, params=p, features=feats, lengths=lens,
                            source=r["source"], page=r["page"], status=r["status"]))
    return out, skipped

if __name__ == "__main__":
    R, sk = make_rows()
    print(len(R), "rows; no printed length for:", sk)
    import collections
    print(collections.Counter(r["type"] for r in R))
    print(max(len(r["lengths"]) for r in R), "longest allowed list")
    print([r["name"] for r in R if r["params"]["fl_t"] >= r["params"]["blen"] and r["family"] in ("shouldered", "thrust", "round")])
    print(min(r['params']['fl_h'] - r['params']['sq_w'] for r in R), min(r['params']['fl_h'] - r['params']['cp_w'] for r in R))
