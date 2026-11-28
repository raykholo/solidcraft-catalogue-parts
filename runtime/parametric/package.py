"""Python stand-in for SolidCraft's generator.parse / generator.code (docs/formats/generator.md sections 3-5): the field template from
generator.toml (runtime/fieldtemplate.py) and resolve(fields) in generator.rhai, evaluated by the real Rhai engine (runtime/rhai-run)."""
import tomllib
from runtime.parametric import rhai as call_rhai
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
from runtime.fieldtemplate import load, Refusal


class Package:
    def __init__(self, folder, no_match=None, no_match_reason="invalid", typed_code_field=None):
        self.no_match_reason, self.typed_code_field = no_match_reason, typed_code_field
        self.no_match = no_match or (lambda code: f"not an MGN set code: {code!r}")
        self.dir = Path(folder); self.toml = tomllib.loads((self.dir / "generator.toml").read_text())
        self.templates = load(self.dir)

    def rhai(self, fn, arg):
        return call_rhai(self.dir, fn, arg)

    def parse(self, code):
        """-> {ok, parameters, configuration, template, fields, provenance} or {ok: False, reason, message}"""
        m = self.templates.match(code)
        if m is None:
            return {"ok": False, "reason": self.no_match_reason, "message": self.no_match(code)}
        idx, fields = m
        args = {k: v for k, v in fields.items() if v is not None}
        if self.typed_code_field:
            args[self.typed_code_field] = code
        res = self.rhai("resolve", args)
        if not res["ok"]:
            return res
        v = res["value"]
        prov = self.toml.get("rows", {}).get(v["configuration"])
        return {"ok": True, "parameters": v["parameters"], "configuration": v["configuration"], "template": idx, "fields": fields, "provenance": prov}

    def code(self, fields, index=0):
        return self.templates.print(fields, index)
