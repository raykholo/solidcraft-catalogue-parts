"""Faithfulness conversion for all harness layouts; numeric data is never recomputed."""
import json
from pathlib import Path

DRAFT = "needs #23175 (our draft, being finished)"
LINK_BLOCKED = {"what": "free parameter values on an inserted link", "needs": DRAFT}


def dependencies(blocked):
    """Describe draft-provided link features separately from thread follow-ups."""
    rows = []
    for row in blocked:
        row = dict(row)
        what = row["what"].lower()
        if "free parameter values on an inserted link" in what:
            row = dict(LINK_BLOCKED)
        elif "cosmetic thread created after a cross cut" in what:
            row["needs"] = "follow-up: tangency-labs/solidcraft#23507"
        elif "thread" in what:
            row["needs"] = "follow-up: tangency-labs/solidcraft#9594"
        rows.append(row)
    return rows


def measurement(value, absolute=False):
    """Normalize a measurement, retaining HIWIN's absolute bounds and MISUMI's extents."""
    if not value or any(k in value for k in ("error", "refused")):
        return {"error": True}
    volume = "vol" if absolute else "volume"
    if volume not in value:
        return {"error": True}
    return {"volume": value[volume], "area": value["area"],
            "bbox": list(value["lo"]) + list(value["hi"]) if absolute else list(value["bbox"]),
            "faces": value["faces"], "bodies": value["bodies"]}


def spec(value):
    """Format the existing passed/total spec count."""
    return f"{value['rows'] - len(value['failed'])}/{value['rows']}" if value else None


def convert(results, gid, blocked, layout="standard"):
    """Convert a results dictionary without changing its row order or numeric values."""
    out = {"generator": gid, "valid": [], "rejects": [], "rebuild": [], "blocked": dependencies(blocked)}
    for row in results["codes"]:
        v = {"code": row["code"], "python": measurement(row.get("python")),
             "parametric": measurement(row.get("parametric")),
             "spec_python": spec(row.get("python_spec")), "spec_parametric": spec(row.get("parametric_spec"))}
        if layout == "description" and not row.get("description_same", True):
            v["note"] = "description differs"
        if layout == "shaft" and row.get("extra"):
            v["note"] = "extra code (not in codes.txt)"
        if layout == "rows" and "error" in row.get("parametric", {}):
            v["note"] = row["parametric"]["error"]
        failure = row.get("parametric") or {}
        if "refused" in failure or "error" in failure:
            v["note"] = str(failure.get("refused", failure.get("error")))
        out["valid"].append(v)
    seen = {r["code"] for r in out["valid"]}
    if layout == "nut":
        for row in results.get("all_rows", []):
            if row["code"] not in seen:
                out["valid"].append({"code": row["code"], "python": measurement(row["python"]),
                                     "parametric": measurement(row["parametric"]),
                                     "spec_python": spec(row.get("python_spec")), "spec_parametric": spec(row.get("parametric_spec")),
                                     "note": "row of the types table that codes.txt does not list"})
    out["rejects"] = [{k: row[k] for k in ("code", "python", "parametric")} for row in results["refusals"]]
    for row in ([] if layout == "nut" else results.get("rebuild" if layout == "rows" else "parametric", [])):
        direct = row.get("direct_inserted")
        if layout == "rows":
            label = f"row {row['from']} switched to {row['to']}"
            direct = row.get("direct")
        elif layout == "description":
            if not row.get("direct"): continue
            label = f"{row['base']} {row['param']} -> {row['value']} vs {row['direct']}"
            direct = direct or row.get("python")
        elif layout in ("extrusion", "shaft"):
            param = "L" if layout == "shaft" else "length"
            label = f"{row['base']} {param} -> {row['length']} vs {row['direct']}"
        elif layout == "bushing":
            label = f"{row['base']} {','.join(row['changes'])} -> {row['direct']}"
        else:
            label = f"{row['base']} {row['param']} -> {row['value']} vs {row['direct']}"
        out["rebuild"].append({"label": label, "direct": measurement(direct), "changed": measurement(row.get("changed"))})
    return out


def convert_hiwin(directory, gid="hiwin.mg.rail-set", blocked=None, guideway=False):
    """Convert HIWIN report.json and rebuild.json with their original absolute bounding boxes."""
    directory = Path(directory)
    out = {"generator": gid, "valid": [], "rejects": [], "rebuild": [], "blocked": dependencies(blocked) if blocked is not None else [dict(LINK_BLOCKED)]}
    for row in json.loads((directory / "report.json").read_text()):
        if row["code"].startswith("!"):
            message = row["param"]
            out["rejects"].append({"code": row["code"], "python": row["python"],
                                   "parametric": message[len("REFUSED: "):] if message.startswith("REFUSED: ") else None})
        else:
            out["valid"].append({"code": row["code"], "python": measurement(row.get("python_m"), True),
                                 "parametric": measurement(row.get("param_m"), True),
                                 "spec_python": (row.get("pycheck") or "").split(" ")[0] or None,
                                 "spec_parametric": (row.get("check") or "").split(" ")[0] or None})
    path = directory / "rebuild.json"
    rb = json.loads(path.read_text()) if path.exists() else {}
    if guideway:
        for row in rb.get("rebuild", []):
            if "error" in row:
                out["rebuild"].append({"label": row["label"], "direct": {"error": True}, "changed": {"error": True}})
                continue
            for label, key in (("the fresh parametric instance", "fresh"), ("the Python part", "python")):
                out["rebuild"].append({"label": row["label"] + f" ({label})", "direct": measurement(row[key], True), "changed": measurement(row["rebuilt"], True)})
        if rb.get("insert"):
            row = rb["insert"]
            out["rebuild"].append({"label": row["label"], "direct": measurement(row["direct"], True), "changed": measurement(row["changed"], True)})
        return out
    if rb:
        out["rebuild"] = [{"label": "MGN12H2R300Z0C length 300 -> 400 vs MGN12H2R400Z0C",
                           "direct": measurement(rb.get("fresh"), True), "changed": measurement(rb.get("rebuilt"), True)},
                          {"label": "MGN12H2R400Z0C parametric vs Python",
                           "direct": measurement(rb.get("python"), True), "changed": measurement(rb.get("fresh"), True)}]
    return out


def write_faithfulness(source, target, gid, blocked, layout="standard"):
    """Read results and write the common verdict schema; performs no CLI calls."""
    if layout == "guideway":
        result = convert_hiwin(source, gid, blocked, guideway=True)
    elif layout == "hiwin":
        result = convert_hiwin(source)
    else:
        result = convert(json.loads(Path(source).read_text()), gid, blocked, layout)
    Path(target).write_text(json.dumps(result, indent=1))
    return result
