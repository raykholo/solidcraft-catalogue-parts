"""Python stand-in for SolidCraft's generator.parse / generator.code (docs/formats/generator.md sections 3-5): the field template from
generator.toml (runtime/fieldtemplate.py) and resolve(fields) in generator.rhai, evaluated by the real Rhai engine (rhai-resolve)."""
import json, os, subprocess, sys, tomllib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT))
from runtime.fieldtemplate import Template, TemplateSet, Refusal

RHAI = os.environ.get("RHAI_RESOLVE", str(ROOT / "rbin" / "rhai-resolve"))

class Package:
    def __init__(self, folder):
        self.dir = Path(folder); self.toml = tomllib.loads((self.dir / "generator.toml").read_text())
        ch = {k: v["values"] for k, v in self.toml.get("parameters", {}).items() if v.get("type") == "choice"}
        self.templates = TemplateSet([Template.parse(t["pattern"], ch, t.get("escape")) for t in self.toml["template"]])

    def rhai(self, fn, arg):
        r = subprocess.run([RHAI, str(self.dir), fn], input=json.dumps(arg), capture_output=True, text=True)
        return json.loads(r.stdout)

    def parse(self, code):
        """-> {ok, parameters, configuration, template, fields, provenance} or {ok: False, reason, message}"""
        m = self.templates.match(code)
        if m is None:
            return {"ok": False, "reason": "invalid", "message": f"not an MGN set code: {code!r}"}
        idx, fields = m
        res = self.rhai("resolve", {k: v for k, v in fields.items() if v is not None})
        if not res["ok"]:
            return res
        v = res["value"]
        prov = self.toml.get("rows", {}).get(v["configuration"])
        return {"ok": True, "parameters": v["parameters"], "configuration": v["configuration"], "template": idx, "fields": fields, "provenance": prov}

    def code(self, fields):
        return self.templates.print(fields)
