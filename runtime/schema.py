"""A small JSON-Schema subset (type, required, properties, additionalProperties, items, enum, pattern, minItems, maxItems,
minLength, maxLength, const, uniqueItems, minimum, maximum, anyOf, patternProperties, maxProperties; "format" is ignored): enough for schema/*.json, with no dependency."""
from __future__ import annotations
import re

_TYPES = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool}

def validate(value, schema, path="$") -> list[str]:
    errs: list[str] = []
    if "anyOf" in schema:
        subs = [validate(value, s, path) for s in schema["anyOf"]]
        if all(subs):
            errs.append(f"{path}: matches none of the allowed shapes ({'; '.join(s[0] for s in subs)})")
        return errs
    t = schema.get("type")
    if t:
        ok = isinstance(value, _TYPES[t]) and not (t in ("integer", "number") and isinstance(value, bool))
        if not ok:
            return [f"{path}: expected {t}, got {type(value).__name__}"]
    if "const" in schema and value != schema["const"]:
        errs.append(f"{path}: {value!r} is not {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: {value!r} not one of {schema['enum']}")
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errs.append(f"{path}: {value!r} does not match {schema['pattern']}")
        if len(value) < schema.get("minLength", 0):
            errs.append(f"{path}: shorter than {schema['minLength']}")
        if len(value) > schema.get("maxLength", 10 ** 9):
            errs.append(f"{path}: longer than {schema['maxLength']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errs.append(f"{path}: {value} below {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errs.append(f"{path}: {value} above {schema['maximum']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errs.append(f"{path}: fewer than {schema['minItems']} items")
        if len(value) > schema.get("maxItems", 10 ** 9):
            errs.append(f"{path}: more than {schema['maxItems']} items")
        if schema.get("uniqueItems") and len({repr(v) for v in value}) != len(value):
            errs.append(f"{path}: items are not unique")
        for i, v in enumerate(value):
            if "items" in schema:
                errs += validate(v, schema["items"], f"{path}[{i}]")
    if isinstance(value, dict):
        for k in schema.get("required", []):
            if k not in value:
                errs.append(f"{path}: missing {k}")
        props = schema.get("properties", {})
        pats = schema.get("patternProperties", {})
        if len(value) > schema.get("maxProperties", 10 ** 9):
            errs.append(f"{path}: more than {schema['maxProperties']} properties")
        for k, v in value.items():
            if k in props:
                errs += validate(v, props[k], f"{path}.{k}")
            elif any(re.search(p, k) for p in pats):
                for p, sub in pats.items():
                    if re.search(p, k):
                        errs += validate(v, sub, f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}: unknown field {k}")
            elif isinstance(schema.get("additionalProperties"), dict):
                errs += validate(v, schema["additionalProperties"], f"{path}.{k}")
    return errs
