"""Resolver validation and geometry-free catalogue sweeps for legacy harnesses."""
import json
from pathlib import Path


def checked(templates, call, code):
    match = templates.match(code.strip().upper())
    if match is None:
        return ("refused", "invalid", f"{code!r} matches none of the templates"), None
    fields = match[1]
    try:
        reply = call("resolve", fields)
        if not reply.get("ok"):
            return ("refused", reply.get("reason", "script_error"), reply.get("message", str(reply))), fields
        value = reply.get("value")
        if not (isinstance(value, dict) and isinstance(value.get("configuration"), str)
                and isinstance(value.get("parameters"), dict) and isinstance(value.get("properties"), dict)):
            raise ValueError(f"resolve returned an invalid result: {value!r}")
        return ("ok", value), fields
    except (OSError, ValueError, TypeError, AttributeError) as error:
        return ("refused", "script_error", str(error)), fields


def sweep(codes, build, resolve, call, templates, out):
    """Resolve every Python-accepted candidate and check descriptions and inverse maps."""
    rows = []
    for code in sorted(set(codes)):
        try:
            part, _ = build(code)
        except ValueError:
            continue
        state, _ = resolve(code)
        row = {"code": code, "ok": False}
        if state[0] != "ok":
            row["error"] = f"Python accepted; resolve {state[1]}: {state[2]}"
        else:
            value = state[1]
            try:
                inverse = call("fields", value["configuration"], value["parameters"])
                if not inverse.get("ok"):
                    raise ValueError(str(inverse))
                printed = templates.print(inverse["value"])
                again, _ = resolve(printed)
                row.update(configuration=value["configuration"], parameters=value["parameters"], printed=printed)
                row["ok"] = (value["properties"]["description"] == part.description and again[0] == "ok"
                             and again[1]["configuration"] == value["configuration"]
                             and again[1]["parameters"] == value["parameters"])
                if not row["ok"]:
                    row["error"] = "description or inverse resolver differs"
            except (ValueError, TypeError, KeyError, OSError) as error:
                row["error"] = str(error)
        rows.append(row)
    Path(out).mkdir(parents=True, exist_ok=True)
    (Path(out) / "resolve.json").write_text(json.dumps(rows, indent=2) + "\n")
    failed = [r for r in rows if not r["ok"]]
    print(f"resolve sweep: {len(rows)} Python-valid codes, {len(failed)} differences")
    for row in failed:
        print(row["code"], row["error"])
    return bool(failed)
