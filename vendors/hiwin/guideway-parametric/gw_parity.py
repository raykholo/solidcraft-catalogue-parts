#!/usr/bin/env python3
"""Local parity test (no SolidCraft): codes.txt plus a seeded sample of generated codes go through the Python generator's parse and through
template -> Rhai; the refusal messages must be identical, and an accepted code must name a configuration row whose table values and
parameters are the Python part's (block row, rail length, number of blocks, dust block length).
    python3 gw_parity.py SERIES [N]        (RHAI_RUN = the Rhai host)"""
import itertools, json, random, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import gw_model as m
from gw_stub import Package
from runtime import registry

def main(key, n=3000, seed=7):
    S = m.SERIES[key]
    gen = next(g for g in registry.generators() if g.id == S.gid)
    cat, build = gen.module("catalogue"), gen.module("build")
    pkg = Package(gen.dir / "parametric" / f"{S.dirname}-guideway")
    codes = [("codes.txt", l.code) for l in gen.codes()]
    rnd = random.Random(seed)
    sizes = list(cat.SIZES) + ["10", "99"]
    lens = ["100", "160", "220", "280", "340", "500", "640", "995", "1000", "1010", "1020", "1240", "2000", "2001", "4000", "4500", "60", "10", "40", "35", "850.5", "1000.0"]
    pre = ["", "Z0", "ZA", "ZB"]; prec = ["", "C", "H", "P", "SP", "UP"]; opts = ["", "+ZZ", "+DD", "+KK/E2+RC", "+E2", "+SS", "+ZZ+DD", "+XZZ", "+Z"]
    kinds = "HW" + ("L" if key == "HG" else "LSF" if key == "RG" else "")
    for _ in range(n):
        t = rnd.choice("srb")
        size = rnd.choice(sizes); kind = rnd.choice(kinds); load = rnd.choice("CHS"); mount = rnd.choice("ABC")
        rm = rnd.choice("RRRTU"); e1 = rnd.choice(["", "", "E"]); e2 = rnd.choice(["", "", "E"]); mat = rnd.choice(["", "", "", "M"]); rails = rnd.choice(["", "", "II"])
        o = rnd.choice(opts); L = rnd.choice(lens); nb = rnd.choice(["0", "1", "1", "2", "3", "9"])
        a, p, q = rnd.choice(pre), rnd.choice(prec), rnd.choice(opts)
        if t == "s": c = f"{S.key}{kind}{size}{load}{mount}{e1}{nb}{rm}{L}{e2}{a}{p}{mat}{rails}{o}"
        elif t == "r": c = f"{S.key}R{size}{rm}{L}{e2}{p}{mat}{q}"
        else: c = f"{S.key}{kind}{size}{load}{mount}{e1}{a}{p}{mat}{q}"
        codes.append(("fuzz", c))
    bad = 0; stats = dict(valid=0, refused=0, notemplate=0)
    for src, code in codes:
        try:
            s, _ = build.parse_build(code); py = None
        except ValueError as e:
            s, py = None, str(e)
        r = pkg.parse(code)
        if py is not None:
            if r["ok"]: bad += 1; print("ACCEPTED but Python refuses:", code, "|", py); continue
            if r.get("reason") == "no_template":
                stats["notemplate"] += 1
                if "expected a set" not in py: bad += 1; print("NO TEMPLATE but Python gives a specific message:", code, "|", py)
                continue
            stats["refused"] += 1
            if r["message"] != py: bad += 1; print("MESSAGE", code, "\n   py :", py, "\n   rhai:", r["message"])
            continue
        if not r["ok"]:
            bad += 1; print("REFUSED but Python accepts:", code, "|", r.get("message")); continue
        stats["valid"] += 1
        ps = r["parameters"]
        name = r["configuration"]
        want_blocks = s.n_blocks if s.kind == "set" else None
        if s.kind != "block" and abs(float(ps["length"].split()[0]) - s.rail_length) > 1e-9: bad += 1; print("LENGTH", code, ps, s.rail_length)
        if s.kind == "set" and ps["blocks"] != str(s.n_blocks): bad += 1; print("BLOCKS", code, ps)
        if s.kind != "rail":
            row = pkg.rhai("resolve", {})  # placeholder, keeps the host warm
            import csv
            tb = {r_["key"]: r_ for r_ in csv.DictReader((pkg.dir / "tables/blocks.csv").open())}
            want = f"{S.key}{s.series[-1]}-{s.load}{s.mount}-{s.size}"
            if name.rsplit("-block", 1)[0].rsplit("-" + name.split("-")[-1], 1)[0] != name and False: pass
            keyname = name[:-len("-block")] if name.endswith("-block") else name
            keyname = keyname.rsplit("-", 1)[0] if S.rm_in_name and not name.endswith("-block") else keyname
            if keyname != want: bad += 1; print("ROW", code, name, want)
            tr = tb.get(want)
            L = float(tr["L"]) if tr else None
            Lpy = s.block["L"]
            if key == "RG" and s.dust:   # the dust block length is a parameter override
                if "L" not in ps or abs(float(ps["L"].split()[0]) - Lpy) > 1e-9: bad += 1; print("DUST L", code, ps, Lpy)
            elif L is None or abs(L - Lpy) > 1e-9: bad += 1; print("BLOCK L", code, L, Lpy)
        if s.kind == "rail" or s.kind == "set":
            if S.rm_in_name and not name.endswith("-" + s.rail_mount): bad += 1; print("RAIL MOUNT", code, name, s.rail_mount)
        if s.kind == "block" and not name.endswith("-block"): bad += 1; print("KIND", code, name)
        if s.kind == "rail" and not name.startswith(f"{S.key}R-"): bad += 1; print("KIND", code, name)
    print(f"{key}: {len(codes)} codes, {stats}, {bad} differences")
    return bad

if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3000) else 0)
