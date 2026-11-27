"""misumi.hnt.t-nut as a generator package: the HNTT family pre-assembly T-nuts (sources.toml S9, p.559)."""
from __future__ import annotations
import importlib
from runtime.table import read_csv, num
from . import table, pts

def describe(gen):
    nut = importlib.import_module(gen.pkg + ".nut")
    data = gen.dir / "data"
    types, params, tap = read_csv(data / "types.csv"), read_csv(data / "params.csv"), read_csv(data / "tap.csv")
    P = {r["name"]: num(r["value"]) for r in params}
    assert P["default_m"] == 5 and nut.DEFAULT_M == 5      # the grammar's `default` repeats this catalogue note
    drawn = [r["type"] for r in types]
    other = sorted(nut.OTHER)

    # section polygons: one per type (they differ in E and T), derived by the Python generator's own section()
    trows = []
    for r in types:
        n = nut.parse(f"{r['type']}-{r['allowed_m'].split('|')[0]}")
        trows.append([r["type"], r["kind"], r["material"], r["surface"], " ".join(r["allowed_m"].split("|")),
                      ", ".join("M" + x for x in r["allowed_m"].split("|")), num(r["E"]), num(r["T"]), pts(nut.section(n)),
                      r["source"], r["page"], r["status"], "polygon (section across the slot: y, z) and allowed_text are derived from E, T and the params rows by tools/export-package"])
    tables = {
        "types": table({"type": "text", "kind": "text", "material": "text", "surface": "text", "allowed_m": "list", "allowed_text": "text",
                        "E": "number", "T": "number", "polygon": "points", "source": "text", "page": "text", "status": "text", "note": "text"},
                       ["type"], ["type", "kind", "material", "surface", "allowed_m", "allowed_text", "E", "T", "polygon", "source", "page", "status", "note"], trows),
        "params": table({"name": "text", "value": "number", "unit": "text", "source": "text", "page": "text", "status": "text"}, ["name"],
                        ["name", "value", "unit", "source", "page", "status"], [[r["name"], num(r["value"]), r["unit"], r["source"], r["page"], r["status"]] for r in params]),
        "tap": table({"m": "text", "pilot": "number", "unit": "text", "source": "text", "page": "text", "status": "text"}, ["m"],
                     ["m", "pilot", "unit", "source", "page", "status"], [[r["m"], num(r["pilot"]), r["unit"], r["source"], r["page"], r["status"]] for r in tap]),
    }
    used = ["plan", "flank_h", "round_bottom", "round_flank_top", "round_edge", "torque_m5"]
    defaults = {f"k_{n}": f'"{n}"' for n in used}
    lookups = [{"table": "types", "as": "s", "key": {"type": "type"}},
               {"table": "tap", "as": "tp", "key": {"m": "m"}, "missing": "{type} is offered in {s.allowed_text}, not M{m}"}]
    lookups += [{"table": "params", "as": f"p_{n}", "key": {"name": f"k_{n}"}} for n in used]
    ref = lambda *idx: [f"l{i % 10 or 10}.end" for i in idx]       # as nut.commands: section corner i -> l{i}.end
    pv = lambda n: "${p_%s.value}" % n
    steps = [
        {"command": "sketch.create", "params": {"plane": "YZ", "name": "Profile"}},
        {"command": "sketch.line", "params": {"points": "${s.polygon}", "closed": True}},
        {"command": "sketch.fillet", "params": {"points": ref(0, 1), "radius": pv("round_bottom")}},
        {"command": "sketch.fillet", "params": {"points": ref(2, 9), "radius": "${flank_r}"}},
        {"command": "sketch.fillet", "params": {"points": ref(3, 8, 5, 6), "radius": pv("round_edge")}},
        {"command": "sketch.finish", "params": {}},
        {"command": "solid.extrude", "params": {"distance": pv("plan"), "name": "Nut", "body_name": "${code}"}},
        {"command": "solid.cylinder", "params": {"diameter": "${pilot}", "height": "${T + 2}", "base": ["${p_plan.value / 2}", 0, -1], "axis": "Z",
                                                "operation": "cut", "targets": ["${code}"], "name": "Pilot bore O${pilot}"}},
        {"command": "solid.thread", "params": {"face": ["${p_plan.value / 2 + pilot / 2}", 0, "${T / 2}"], "designation": "M${m}", "extent": "length",
                                               "length": "${T}", "from": ["${p_plan.value / 2 + pilot / 2}", 0, "${T}"], "name": "Thread M${m}"}},
        {"command": "browser.visibility", "params": {"items": ["Profile"], "visible": False}},
        {"command": "component.metadata.set", "params": {"component": "${code}", "part_number": "${code}", "description": "${desc}", "material": "${mat}"}},
        {"command": "document.metadata.set", "params": {"values": {"part_number": "${code}", "description": "${desc}"}}},
    ]
    q = lambda s: '"' + s + '"'
    pkg = {
        "grammar": {"alternatives": [[{"field": "type", "enum": drawn + other},
                                      {"optional": [{"lit": "-"}, {"field": "m", "chars": "digits", "min_len": 1, "max_len": 3}], "default": {"m": "5"}}]],
                    "refuse": "{code}: expected <type>-<M>, e.g. HNTT5-4 (types: " + ", ".join(drawn) + ")"},
        "tables": tables,
        "defaults": defaults,
        "x-early-rules": [{"when": " || ".join(f'type == "{t}"' for t in other),
                           "refuse": "{type}: a valid 5 series nut, not drawn here; drawn: " + ", ".join(drawn), "kind": "not_modelled"}],
        "lookups": lookups,
        "vars": [
            {"name": "code", "expr": 'concat(type, "-", m)'},
            {"name": "E", "expr": "s.E"}, {"name": "T", "expr": "s.T"},
            {"name": "pilot", "expr": "tp.pilot"},
            {"name": "flank_r", "expr": "min(p_round_flank_top.value, (E - p_round_edge.value - p_flank_h.value) / tan(17.5))"},
            {"name": "surf", "expr": 's.surface == "-" ? "" : concat(", ", s.surface)'},
            {"name": "torque", "expr": 'm == "5" ? concat(", reference tightening torque ", p_torque_m5.value, " N m") : ""'},
            {"name": "desc", "expr": 'concat("MISUMI pre-assembly insertion nut ", type, " (", s.kind, ") for 5 series (slot width 6 mm) extrusions, M", m, ", ", p_plan.value, " x ", p_plan.value, " mm plan, E=", E, ", T=", T, ", ", s.material, surf, torque, ". Generated from the published catalogue dimensions; the flank profile and the edge rounds are measured from the drawing; the tap drill is the ISO coarse one.")'},
            {"name": "mat", "expr": 's.surface == "-" ? s.material : concat(s.material, "; ", s.surface)'},
        ],
        "rules": [{"when": "!in(m, s.allowed_m)", "refuse": "{type} is offered in {s.allowed_text}, not M{m}"}],
        "steps": steps,
        "insert": {"component": "${code}"},
    }
    return {"package": pkg, "dimension_vars": ["E", "T", "pilot", "flank_r"]}

def sweep(rng, n):
    """Codes for tools/package-equiv beyond codes.txt: every type, the M suffixes, and junk."""
    types = ["HNTT5", "HNTTV5", "HNTTZ5", "HNTTSN5", "HNTTSS5", "HNTU5", "HNTUV5", "HNST5", "SHNST5", "HNTTBS5", "HNTX5", "HNTT6", "HNT5", "HNTT"]
    ms = ["", "-3", "-4", "-5", "-6", "-2", "-8", "-3.5", "-", "--4", "-4-4", "-M4", "-0"]
    return [t + m for t in types for m in ms]
