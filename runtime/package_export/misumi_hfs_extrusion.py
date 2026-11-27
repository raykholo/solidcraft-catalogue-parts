"""misumi.hfs.extrusion as a generator package: 5 series 2020 / 2040 / 4040 and 6 series 3030 aluminium extrusions (S1, S2, S3, S10).

The package format has no loops and no list building, so the geometry that depends only on the profile (outline polygon, fillet
corner references, the central voids, bores, tapped-bore points) is written into the `profiles` table as derived columns by running the
Python generator's own geometry code; the numbers it is derived from stay in the same row. Everything that depends on the code (length,
end tapping, wrench holes, material, names) is expressed in variables, rules and steps."""
from __future__ import annotations
import importlib
from runtime.table import read_csv, num
from . import table, pts

WRENCH_SIDES = {"L": "left", "R": "right"}
ALTS = ["LTP", "RTP", "TPW", "LHP", "RHP", "HPW", "SC", "CW", "FL", "FR", "X5", "X8"]
WRENCH = [s + r + o for s in "LR" for r in "CWE" for o in "HVP"]
NM = 5      # arms / circles / taps slots in the template

def describe(gen):
    ext = importlib.import_module(gen.pkg + ".ext")
    pr = importlib.import_module(gen.pkg + ".profiles")
    data = gen.dir / "data"
    prof_rows, type_rows, params = read_csv(data / "profiles.csv"), read_csv(data / "types.csv"), read_csv(data / "params.csv")
    fixed = [int(v) for v in ext._PARAMS["fixed_lengths"].split("|")]
    assert len(fixed) == 2

    # ---- profiles: the catalogue numbers of data/profiles.csv plus the derived geometry columns
    zero = lambda x: 0.0 if x is None else float(x)
    hdr = ["profile", "series", "w", "h", "corner_r", "tip_r", "mouth", "lip", "cavity", "d0", "floor_half", "depth", "tap_thread", "tap_depth",
           "wrench_h", "wrench_j", "wrench_k", "wrench_d", "published_area", "published_ix", "published_iy", "published_mass",
           "slots", "bores", "outline", "corner_refs", "mouth_refs", "void_poly"]
    hdr += [f"v{k}_{t}" for k in range(4) for t in ("line", "arc")]
    hdr += [f"b{k}_{t}" for k in range(NM) for t in ("c", "d")]
    hdr += [f"t{k}_{t}" for k in range(4) for t in ("c", "n")]
    hdr += ["source", "page", "status", "note"]
    types_ = {"profile": "text", "series": "number", **{c: "number" for c in ("w", "h", "corner_r", "tip_r", "mouth", "lip", "cavity", "d0", "floor_half", "depth",
              "tap_depth", "wrench_h", "wrench_j", "wrench_k", "wrench_d", "published_area", "published_ix", "published_iy", "published_mass")},
              "tap_thread": "text", "slots": "text", "bores": "text", "outline": "points", "corner_refs": "list", "mouth_refs": "list", "void_poly": "points",
              "source": "text", "page": "text", "status": "text", "note": "text"}
    for k in range(4):
        types_[f"v{k}_line"] = "points"; types_[f"v{k}_arc"] = "points"
        types_[f"t{k}_c"] = "points"; types_[f"t{k}_n"] = "number"
    for k in range(NM):
        types_[f"b{k}_c"] = "points"; types_[f"b{k}_d"] = "number"
    prows = []
    for r in prof_rows:
        sp = pr.P[r["key"]]
        o = pr.outline(sp); n = len(o)
        corner = [f"l{(i - 1) % n + 1}.end" for i in range(n) if o[i][2] == "corner"]
        mouth = [f"l{(i - 1) % n + 1}.end" for i in range(n) if o[i][2] == "mouth"]
        poly, lines, arcs = [], [], []
        for v in sp.voids:
            if any(isinstance(it, pr.Arc) for it in v):
                st = ext._void_runs(v)
                assert [k for k, _ in st] == ["line", "arc"] * (len(st) // 2) and len(st) // 2 <= 4
                lines = [s for k, s in st if k == "line"]
                arcs = [[s.a, s.t, s.b] for k, s in st if k == "arc"]
            else:
                poly = v
        bores = list(sp.bores)
        assert len(bores) <= NM
        taps = []
        for bi, (bx, by, d) in enumerate(pr.all_bores(sp)):
            if sp.arc_bores:
                ux, uy = (1 if bx > 0 else -1) / 2 ** 0.5, (1 if by > 0 else -1) / 2 ** 0.5
            else:
                ux, uy = 1.0, 0.0
            if sp.key == "3030" and d != 6.8:
                continue
            taps.append((bx + ux * d / 2, by + uy * d / 2, bi + 1))
        assert len(taps) <= 4
        wd = sp.wrench_d[0] if len(sp.wrench_d) == 1 else 0.0
        row = [r["key"], sp.series, sp.w, sp.h, sp.corner_r, sp.slot.tip_r, sp.slot.mouth, sp.slot.lip, sp.slot.cavity, sp.slot.d0, sp.slot.floor_half,
               sp.slot.depth, sp.tap[0], sp.tap[1], *sp.wrench_hjk, wd, sp.published_area, sp.published_i[0], sp.published_i[1], sp.published_mass,
               r["slots"], r["bores"], pts([(x, y) for x, y, _ in o]), " ".join(corner), " ".join(mouth), pts(poly)]
        for k in range(4):
            row += [pts(lines[k]) if k < len(lines) else "", pts(arcs[k]) if k < len(arcs) else ""]
        for k in range(NM):
            row += [pts([(bores[k][0], bores[k][1])]) if k < len(bores) else "", bores[k][2] if k < len(bores) else 0.0]
        for k in range(4):
            row += [pts([(taps[k][0], taps[k][1])]) if k < len(taps) else "", taps[k][2] if k < len(taps) else 0]
        cite = r["cite"].split()
        row += [cite[0], " ".join(cite[1:]), "measured",
                f"series / outline / corner_refs / mouth_refs / void_poly / v*_line / v*_arc / b*_c / t*_c are derived from the numbers of this row by tools/export-package "
                f"(the Python generator's geometry); wrench_d 0 = chosen with -X5 / -X8. Original note: {r['note']}"]
        prows.append(row)
    # ---- types: one row per (type, profile) with the material the Python generator resolves
    trows, seen = [], []
    for tr in type_rows:
        if tr["type"] not in seen: seen.append(tr["type"])
    for typ in seen:
        series = int(typ[-1])
        for prof in sorted(ext.PROFILES[series]):
            if typ == "HFSY5" and prof in ext.NO_YELLOW:
                continue
            mat, surf = ext.TYPE_BY_PROFILE.get((typ, prof), ext.TYPES[typ])
            cands = [tr for tr in type_rows if tr["type"] == typ]
            spec = [tr for tr in cands if prof in tr["profiles"].split("|")]
            src = (spec or cands)[-1]
            assert (src["material"], src["surface"]) == (mat, surf)
            trows.append([typ, prof, mat, surf, src["source"], src["page"], src["status"], "one row per (type, profile): the Python generator's lookup, expanded"])
    prm = [[r["name"], num(r["value"]) if "|" not in r["value"] else None, r["unit"], r["source"], r["page"], r["status"]] for r in params]
    prm_rows = []
    for r in params:
        if r["name"] == "fixed_lengths":
            for i, v in enumerate(fixed, 1):
                prm_rows.append([f"fixed_length_{i}", float(v), r["unit"], r["source"], r["page"], r["status"]])
        else:
            prm_rows.append([r["name"], float(num(r["value"])), r["unit"], r["source"], r["page"], r["status"]])
    tables = {
        "profiles": table(types_, ["profile"], hdr, prows),
        "types": table({"type": "text", "profile": "text", "material": "text", "surface": "text", "source": "text", "page": "text", "status": "text", "note": "text"},
                       ["type", "profile"], ["type", "profile", "material", "surface", "source", "page", "status", "note"], trows),
        "params": table({"name": "text", "value": "number", "unit": "text", "source": "text", "page": "text", "status": "text"}, ["name"],
                        ["name", "value", "unit", "source", "page", "status"], prm_rows),
    }

    O = lambda v: f'in("{v}", options)'
    drawn = sorted(set(seen))
    other = sorted(ext.OTHER_TYPES)
    all_types = sorted(set(seen) | set(other))
    chunks = [other[i:i + 10] for i in range(0, len(other), 10)]
    early = [{"when": " || ".join(f'type == "{t}"' for t in ch),
              "refuse": "{type}: valid {series} series type, but not drawn here (drawn: " + ", ".join(drawn) + ")", "kind": "not_modelled"} for ch in chunks]
    used = ["l_min", "l_max", "l_step", "fixed_length_1", "fixed_length_2"]
    alias = {"l_min": "lmin", "l_max": "lmax", "l_step": "lstep", "fixed_length_1": "fl1", "fixed_length_2": "fl2"}
    defaults = {"type": "concat(tname, series)", **{f"k_{u}": f'"{u}"' for u in used}}
    lookups = [{"table": "profiles", "as": "pr", "key": {"profile": "profile"}, "missing": "profile {profile} is not available here (drawn: " + ", ".join(sorted(ext.PROFILES[5]) + sorted(ext.PROFILES[6])) + ")"},
               {"table": "types", "as": "tp", "key": {"type": "type", "profile": "profile"},
                "missing": "{type} is not listed for profile {profile} (unknown type, wrong series, or HFSY5 outside 2020)"}]
    lookups += [{"table": "params", "as": alias[u], "key": {"name": f"k_{u}"}} for u in used]

    def side(S):
        sd = lambda r, o: f'({O(S + r + o)})'
        rows = f'({O(S+"CH")} || {O(S+"CV")}) ? 1 : (({O(S+"WH")} || {O(S+"WV")}) ? 2 : (({O(S+"EH")} || {O(S+"EV")}) ? 3 : 0))'
        cnt = " + ".join(f'if({O(S + r + o)}, 1, 0)' for r in "CWE" for o in "HV")
        return [
            {"name": f"rows{S}", "expr": rows},
            {"name": f"cnt{S}", "expr": cnt},
            {"name": f"orient{S}", "expr": f'({O(S+"CH")} || {O(S+"WH")} || {O(S+"EH")}) ? "H" : "V"'},
            {"name": f"h0{S}", "expr": f'pr.wrench_h - ({O("F" + S)} ? 3 : 0)'},
            {"name": f"last{S}", "expr": f"h0{S} + (rows{S} >= 2 ? pr.wrench_j : 0) + (rows{S} >= 3 ? pr.wrench_k : 0)"},
        ]
    vars_ = [{"name": "code", "expr": "code_in"}, {"name": "fixed", "expr": 'k == "K"'}, {"name": "type_full", "expr": "concat(k, type)"},
             {"name": "tapL", "expr": f'{O("LTP")} || {O("TPW")}'}, {"name": "tapR", "expr": f'{O("RTP")} || {O("TPW")}'}]
    vars_ += side("L") + side("R")
    vars_ += [
        {"name": "hasW", "expr": "rowsL > 0 || rowsR > 0"},
        {"name": "xany", "expr": f'{O("X5")} || {O("X8")}'},
        {"name": "wd", "expr": f'pr.wrench_d > 0 ? pr.wrench_d : ({O("X5")} ? 5 : ({O("X8")} ? 8 : 0))'},
        {"name": "tap_txt", "expr": '(tapL || tapR) ? concat(", end tapped ", pr.tap_thread, " depth ", pr.tap_depth, " (", (tapL && tapR) ? "both ends" : (tapL ? "left end" : "right end"), ")") : ""'},
        {"name": "wtxtL", "expr": 'rowsL > 0 ? concat(", left wrench access holes x", rowsL, " ", orientL == "H" ? "horizontal" : "vertical", " d", wd) : ""'},
        {"name": "wtxtR", "expr": 'rowsR > 0 ? concat(", right wrench access holes x", rowsR, " ", orientR == "H" ? "horizontal" : "vertical", " d", wd) : ""'},
        {"name": "desc", "expr": 'concat("MISUMI aluminium extrusion ", type_full, "-", profile, " ", lower(tp.surface), ", ", tp.material, ", L=", length, " mm", tap_txt, wtxtL, wtxtR, ". Generated from the published catalogue dimensions.")'},
        {"name": "mat", "expr": 'concat(tp.material, ", ", tp.surface)'},
    ]
    R = lambda when, msg, kind="invalid": {"when": when, "refuse": msg, **({"kind": kind} if kind != "invalid" else {})}
    rules = [
        R("fixed && len(options) > 0", "alterations apply to configurable-length extrusions only (fixed-length K types have none)"),
        R("fixed && length != fl1.value && length != fl2.value", "fixed-length (K) extrusions come only in {fl1.value}, {fl2.value} mm, not {length}"),
        R("!fixed && (length < lmin.value || length > lmax.value)", "length {length} mm outside {lmin.value}-{lmax.value} mm"),
        R("!fixed && abs(length / lstep.value - round(length / lstep.value)) > 0.000000001", "length {length} mm is not a multiple of {lstep.value} mm"),
        R(f'({O("LTP")} || {O("RTP")}) && {O("TPW")}', "end tapping given twice for the same end"),
        R(f'{O("LHP")} || {O("RHP")} || {O("HPW")}', "heli-coil end tapping (LHP / RHP / HPW): parsed, not modelled", "not_modelled"),
        R(" || ".join(O(x) for x in WRENCH if x.endswith("P")), "crisscross (P) wrench-hole layout is ambiguous in the catalogue text; use H or V", "not_modelled"),
        R("cntL > 1", "two wrench-hole options for the left end"),
        R("cntR > 1", "two wrench-hole options for the right end"),
        R(f'{O("X5")} && {O("X8")}', "X5 and X8 are both given (the package refuses; the Python generator takes the last)"),
        R("hasW && pr.wrench_d > 0 && xany", "X5/X8 (wrench hole diameter) applies to the 6 series; the 5 series hole is d{pr.wrench_d}"),
        R("hasW && pr.wrench_d == 0 && !xany", "the 6 series wrench hole diameter is selectable: add -X5 or -X8 (S3 p.759 footnote)"),
        R("!hasW && xany", "X5/X8 sets the wrench hole diameter; there is no wrench hole alteration in this code"),
        R(f'{O("FL")} && rowsL == 0', "FL shifts a wrench hole on the left end, but there is none"),
        R(f'{O("FR")} && rowsR == 0', "FR shifts a wrench hole on the right end, but there is none"),
        R(f'{O("SC")} && length > 1500', "SC (high precision cut) applies to L <= 1500 mm only"),
        R(O("CW"), "CW: End face C chamfer (thread chamfer C0.2-0.3): not modelled", "not_modelled"),
        R("(tapL || tapR) && 2 * pr.tap_depth > length", "tapped holes overlap"),
        R("rowsL > 0 && (h0L - wd / 2 < 0 || lastL + wd / 2 > length)", "wrench holes of the left end do not fit in a {length} mm length"),
        R("rowsR > 0 && (length - lastR - wd / 2 < 0 || h0R - wd / 2 < 0)", "wrench holes of the right end do not fit in a {length} mm length"),
    ]
    S = lambda c, p, **kw: {"command": c, "params": p, **kw}
    steps = [S("sketch.create", {"plane": "YZ", "name": "Profile"}),
             S("sketch.line", {"points": "${pr.outline}", "closed": True}),
             S("sketch.fillet", {"points": "${pr.corner_refs}", "radius": "${pr.corner_r}"}),
             S("sketch.fillet", {"points": "${pr.mouth_refs}", "radius": "${pr.tip_r}"}),
             S("sketch.line", {"points": "${pr.void_poly}", "closed": True}, when="len(pr.void_poly) > 0")]
    for k in range(4):
        steps.append(S("sketch.line", {"points": f"${{pr.v{k}_line}}"}, when=f"len(pr.v{k}_line) > 0"))
        steps.append(S("sketch.arc.three_point", {"start": f"${{at(pr.v{k}_arc, 0)}}", "through": f"${{at(pr.v{k}_arc, 1)}}", "end": f"${{at(pr.v{k}_arc, 2)}}"},
                       when=f"len(pr.v{k}_arc) > 0"))
    for k in range(NM):
        steps.append(S("sketch.circle.center", {"center": f"${{at(pr.b{k}_c, 0)}}", "diameter": f"${{pr.b{k}_d}}"}, when=f"len(pr.b{k}_c) > 0"))
    steps += [S("sketch.finish", {}), S("solid.extrude", {"distance": "${length}", "name": "Extrusion", "body_name": "${code}"})]
    for Sd, nm in WRENCH_SIDES.items():
        off = f'(i == 0 ? h0{Sd} : (i == 1 ? h0{Sd} + pr.wrench_j : h0{Sd} + pr.wrench_j + pr.wrench_k))'
        x = off if Sd == "L" else f"(length - {off})"
        H = f'orient{Sd} == "H"'
        steps.append(S("solid.cylinder", {"diameter": "${wd}", "height": f"${{{H} ? pr.w + 2 : pr.h + 2}}",
                                          "base": [f"${{{x}}}", f"${{{H} ? -pr.w / 2 - 1 : 0}}", f"${{{H} ? 0 : -pr.h / 2 - 1}}"],
                                          "axis": f'${{{H} ? "Y" : "Z"}}', "operation": "cut", "targets": ["${code}"], "name": f"Wrench hole {Sd}${{i + 1}}"},
                       when=f"rows{Sd} > 0", repeat={"var": "i", "count": f"rows{Sd}", "max": 3}))
    for Sd in "LR":
        for k in range(4):
            y, z = f"${{at(at(pr.t{k}_c, 0), 0)}}", f"${{at(at(pr.t{k}_c, 0), 1)}}"
            xf, xt = (0.5, 0.0) if Sd == "L" else ("${length - 0.5}", "${length}")
            steps.append(S("solid.thread", {"face": [xf, y, z], "designation": "${pr.tap_thread}", "extent": "length", "length": "${pr.tap_depth}",
                                            "from": [xt, y, z], "name": f"Tap {Sd}${{pr.t{k}_n}}"}, when=f"tap{Sd} && len(pr.t{k}_c) > 0"))
    steps += [S("browser.visibility", {"items": ["Profile"], "visible": False}),
              S("component.metadata.set", {"component": "${code}", "part_number": "${code}", "description": "${desc}", "material": "${mat}"}),
              S("document.metadata.set", {"values": {"part_number": "${code}", "description": "${desc}"}})]
    opts = [{"code": "-" + v, "value": v} for v in ALTS + WRENCH]
    pkg = {
        "grammar": {"alternatives": [[{"optional": [{"field": "k", "enum": ["K"]}], "default": {"k": ""}},
                                      {"field": "tname", "chars": "alpha", "min_len": 1, "max_len": 8},
                                      {"field": "series", "enum": ["5", "6"]}, {"lit": "-"},
                                      {"field": "profile", "chars": "digits", "min_len": 4, "max_len": 6}, {"lit": "-"},
                                      {"field": "length", "decimal": {"min": 0, "max": 100000, "digits": 6}},
                                      {"flags": {"field": "options", "options": opts, "max": len(opts)}}]],
                    "refuse": "{code}: expected [K]<type>5|6-<profile>-<length>[-<alteration>...], e.g. HFS5-2040-800-LTP-RTP"},
        "tables": tables, "defaults": defaults, "x-early-rules": early, "lookups": lookups, "vars": vars_, "rules": rules, "steps": steps,
        "insert": {"component": "${code}"},
    }
    return {"package": pkg, "dimension_vars": ["length", "wd", "rowsL", "rowsR"]}

def sweep(rng, n):
    """Seeded codes beyond codes.txt for tools/package-equiv (kept clear of the documented deviations: case, X5 with X8, number text)."""
    types = ["HFS5", "HFSB5", "NFS5", "NFSB5", "CAF5", "HFSY5", "HFS6", "HFSB6", "CAF6", "HFSY6", "NEFS6", "HFSF5", "HFST5", "HFSX5", "HFS7"]
    profs = ["2020", "2040", "4040", "3030", "2525", "30300"]
    lens = ["50", "49", "49.5", "50.5", "100", "100.3", "120", "300", "497.5", "800", "1000", "1500", "1500.5", "1501", "2000", "3999.5", "4000", "4000.5", "4001", "0", "0.5", "40", "60", "75"]
    alts = ["LTP", "RTP", "TPW", "LHP", "RHP", "HPW", "SC", "CW", "FL", "FR", "X5", "X8", "X7", "ZZZ", "L_T45"] + ["LCH", "LCV", "LWH", "LWV", "LEH", "LEV", "RCH", "RCV", "RWH", "RWV", "REH", "REV", "LCP", "RWP"] * 2
    out = []
    while len(out) < n:
        a = rng.sample(alts, rng.choice([0, 0, 1, 1, 2, 2, 3, 4]))
        if "X5" in a and "X8" in a:
            continue
        t = rng.choice(types); k = "K" if rng.random() < 0.12 else ""
        ln = rng.choice(["1000", "4000", "800", "500"]) if k else rng.choice(lens)
        out.append(f"{k}{t}-{rng.choice(profs) if rng.random() < 0.3 else rng.choice(['2020', '2040', '4040']) if t.endswith('5') else '3030'}-{ln}" + "".join("-" + x for x in a))
    return out
