"""Reference implementation of SolidCraft's generator field templates (docs/formats/generator.md section 3), until SolidCraft ships its own.

    t = Template.parse("MGN{size: int 1..99}{block: C|H}[E:special]{n: int 1..9}R{length: int 1..9999}")
    t.match("MGN 12 h 2 R300")  -> {"size": 12, "block": "H", "special": False, "n": 2, "length": 300}   (None when it does not match)
    t.print({...})              -> "MGN12H2R300"                                  (canonical spelling; a ValueError names the field)

Elements: literals; {name} (a choice listed in `choices`), {name: a|b|c} (longest listed value that fits), {name: C=standard, H=heavy}
(letter -> value; printing writes the letter), {name: int LO..HI}, {name: decimal LO..HI [step S] [digits D]}, {name: text MIN..MAX}
(characters from the escape class), [optional part] (fields in it are absent -> None / their default), [E:flag] (a literal that sets a
boolean). A text field may carry its own escape class after the length: {name: text 1..80 [A-Za-z0-9-]} (else the template's `escape`, else
any character but a separator). Separators " -_/." and case are ignored when parsing: they are skipped between elements (never inside a
text field whose class allows them), printing uses the template's own spelling. Matching backtracks, longest value first, the first complete
match wins; limits as the doc: code <= 128 characters, template <= 256, 32 fields, 20000 steps.
"""
from __future__ import annotations
import re

SEPARATORS = " -_/."
MAX_CODE, MAX_TEMPLATE, MAX_FIELDS, MAX_STEPS = 128, 256, 32, 20000

class TemplateError(ValueError): pass
class Refusal(ValueError):
    def __init__(self, kind, message): super().__init__(message); self.kind, self.message = kind, message

def _norm(s):
    return "".join(ch for ch in s.upper() if ch not in SEPARATORS)

def _charclass(esc):
    """[A-Za-z0-9-]+ -> (set test, min, max). A tiny class language: one [...] class plus +, * or {n,m}."""
    m = re.fullmatch(r"\[([^\]]+)\](\+|\*|\{(\d+),(\d+)\})?", esc)   # the quantifier is optional: an inline class has none
    if not m: raise TemplateError(f"bad escape pattern {esc!r}")
    cls = m.group(1); chars = set(); i = 0
    while i < len(cls):
        if i + 2 < len(cls) and cls[i + 1] == "-":
            chars |= {chr(c) for c in range(ord(cls[i]), ord(cls[i + 2]) + 1)}; i += 3
        else:
            chars.add(cls[i]); i += 1
    return chars

def _tokens(lit):
    """A literal as (character, required) pairs. A plain character is upper-cased and skipped when it is a separator; `\\-` (a backslash then
    a character) is a REQUIRED separator or character: it must be present as written (doc section 3: E-SFJ{d}\\-{l})."""
    out, i = [], 0
    while i < len(lit):
        if lit[i] == "\\" and i + 1 < len(lit):
            out.append((lit[i + 1].upper(), True)); i += 2
        else:
            if lit[i] not in SEPARATORS: out.append((lit[i].upper(), False))
            i += 1
    return out

def _unescape(lit):
    return re.sub(r"\\(.)", r"\1", lit)

class _Field:
    def __init__(self, name, spec, choices):
        self.name, self.spec = name, (spec or "").strip()
        s = self.spec
        if not s:
            if name not in choices: raise TemplateError(f"field {{{name}}} has no spec and no choice list")
            self.kind, self.values = "choice", [str(v) for v in choices[name]]
        elif m := re.fullmatch(r"int(?:\s+(\d*)\s*\.\.\s*(\d*))?", s):
            self.kind = "int"; self.lo = int(m.group(1)) if m.group(1) else 0; self.hi = int(m.group(2)) if m.group(2) else 10**9
        elif m := re.fullmatch(r"decimal(?:\s+([\d.]+)\.\.([\d.]+))?(?:\s+step\s+([\d.]+))?(?:\s+digits\s+(\d+))?", s):
            self.kind = "decimal"; self.lo = float(m.group(1) or 0); self.hi = float(m.group(2) or 1e9)
            self.step = float(m.group(3)) if m.group(3) else None; self.digits = int(m.group(4)) if m.group(4) else None
        elif m := re.fullmatch(r"text\s+(\d+)\.\.(\d+)(?:\s+(\[[^\]]+\]))?", s):
            self.kind = "text"; self.lo, self.hi = int(m.group(1)), int(m.group(2)); self.cls = _charclass(m.group(3)) if m.group(3) else None
        elif "=" in s:
            self.kind = "map"; self.map = {}
            for part in s.split(","):
                k, v = part.split("=", 1); self.map[k.strip().upper()] = v.strip()
        else:
            self.kind, self.values = "choice", [v.strip() for v in s.split("|")]

    def options(self, text, pos, esc):
        """Yield (value, new position) in preference order (longest first)."""
        if self.kind == "choice":
            for v in sorted(self.values, key=len, reverse=True):
                if text.startswith(_norm(v), pos): yield self._typed(v), pos + len(_norm(v))
        elif self.kind == "map":
            for k in sorted(self.map, key=len, reverse=True):
                if text.startswith(_norm(k), pos): yield self.map[k], pos + len(_norm(k))
        elif self.kind == "int":
            m = re.compile(r"[1-9]\d*|0").match(text, pos)
            if m:
                full = m.group(0)
                for ln in range(len(full), 0, -1):
                    s = full[:ln]
                    if not re.fullmatch(r"[1-9]\d*|0", s): continue
                    if self.lo <= int(s) <= self.hi: yield int(s), pos + ln
        elif self.kind == "decimal":
            m = re.compile(r"\d+(?:\.\d+)?").match(text, pos)
            if m:
                full = m.group(0)
                for ln in range(len(full), 0, -1):
                    s = full[:ln]
                    if s.endswith("."): continue
                    v = float(s)
                    if self.lo <= v <= self.hi and (not self.step or abs((v - self.lo) / self.step - round((v - self.lo) / self.step)) < 1e-9):
                        yield v, pos + ln
        elif self.kind == "text":
            allowed = self.cls if self.cls is not None else esc
            n = 0
            while (pos + n < len(text) and n < self.hi and
                   (text[pos + n] not in SEPARATORS if allowed is None else (text[pos + n].upper() in allowed or text[pos + n].lower() in allowed))): n += 1
            for ln in range(n, self.lo - 1, -1):
                if ln >= 1: yield text[pos:pos + ln], pos + ln

    def _typed(self, v):
        return int(v) if re.fullmatch(r"\d+", v) else v

    def printed(self, value):
        if self.kind == "map":
            for k, v in self.map.items():
                if v == value: return k
            raise ValueError(f"field {self.name}: {value!r} is not one of {list(self.map.values())}")
        if self.kind == "choice":
            if str(value) not in self.values: raise ValueError(f"field {self.name}: {value!r} is not one of {self.values}")
            return str(value)
        if self.kind == "int":
            if not isinstance(value, int) or isinstance(value, bool) or not self.lo <= value <= self.hi:
                raise ValueError(f"field {self.name}: {value!r} is outside {self.lo}..{self.hi}")
            return str(value)
        if self.kind == "decimal":
            if not self.lo <= value <= self.hi: raise ValueError(f"field {self.name}: {value!r} is outside {self.lo}..{self.hi}")
            return f"{value:.{self.digits}f}" if self.digits is not None else f"{value:g}"
        if self.kind == "text":
            if not (self.lo <= len(str(value)) <= self.hi): raise ValueError(f"field {self.name}: text length outside {self.lo}..{self.hi}")
            return str(value)

class Template:
    def __init__(self, pattern, nodes, fields, escape):
        self.pattern, self.nodes, self.fields, self.escape = pattern, nodes, fields, escape

    @classmethod
    def parse(cls, pattern, choices=None, escape=None):
        if len(pattern) > MAX_TEMPLATE: raise TemplateError("template longer than 256 characters")
        choices = choices or {}
        pos = 0; fields = []
        def parse_seq(closing):
            nonlocal pos
            nodes = []
            while pos < len(pattern):
                ch = pattern[pos]
                if ch == "]":
                    if not closing: raise TemplateError("unmatched ]")
                    pos += 1; return nodes
                if ch == "[":
                    pos += 1; nodes.append(("opt", parse_seq(True))); continue
                if ch == "{":
                    end = pattern.index("}", pos)
                    body = pattern[pos + 1:end]; pos = end + 1
                    name, _, spec = body.partition(":")
                    f = _Field(name.strip(), spec, choices); fields.append(f); nodes.append(("field", f)); continue
                m = re.compile(r"[^\[\]{}]+").match(pattern, pos)
                lit = m.group(0); pos = m.end()
                flag = None
                if closing and (fm := re.fullmatch(r"(.*?):([A-Za-z_]\w*)", lit)):   # [E:flag]
                    lit, flag = fm.group(1), fm.group(2)
                nodes.append(("lit", _tokens(lit), flag, lit))
            if closing: raise TemplateError("unclosed [")
            return nodes
        nodes = parse_seq(False)
        if len(fields) > MAX_FIELDS: raise TemplateError("more than 32 fields")
        return cls(pattern, nodes, fields, _charclass(escape) if escape else None)

    # ---- code -> fields
    def match(self, code):
        if len(code) > MAX_CODE: raise Refusal("invalid", "code longer than 128 characters")
        text = code.strip().upper(); steps = [0]
        def skip(p):
            while p < len(text) and text[p] in SEPARATORS: p += 1
            return p
        names = {f.name for f in self.fields} | {n[2] for n in self._walk() if n[0] == "lit" and n[2]}
        def run(nodes, i, pos, acc, k):
            """match nodes[i:] at pos, then continue with k(pos, acc); returns the final acc or None"""
            steps[0] += 1
            if steps[0] > 20000: raise Refusal("invalid", "code too complex to match (20000 steps)")
            if i == len(nodes): return k(pos, acc)
            n = nodes[i]
            if n[0] == "lit":
                p = pos
                for c, req in n[1]:                 # separators in the code are skipped between the literal's characters, but not before a required one
                    if not req: p = skip(p)
                    if text[p:p + 1] != c: return None
                    p += 1
                a = dict(acc)
                if n[2]: a[n[2]] = True
                return run(nodes, i + 1, p, a, k)
            if n[0] == "field":
                for v, p in n[1].options(text, skip(pos), self.escape):
                    r = run(nodes, i + 1, p, {**acc, n[1].name: v}, k)
                    if r is not None: return r
                return None
            if n[0] == "opt":
                r = run(n[1], 0, pos, acc, lambda p, a: run(nodes, i + 1, p, a, k))
                if r is not None: return r
                return run(nodes, i + 1, pos, acc, k)
        out = run(self.nodes, 0, 0, {}, lambda p, a: a if skip(p) == len(text) else None)
        if out is None: return None
        return {n: out.get(n, False if n in {x[2] for x in self._walk() if x[0] == "lit" and x[2]} else None) for n in sorted(names, key=lambda x: str(x))} | {k: v for k, v in out.items()}

    def _walk(self, nodes=None):
        for n in (self.nodes if nodes is None else nodes):
            yield n
            if n[0] == "opt": yield from self._walk(n[1])

    # ---- fields -> code
    def print(self, params):
        def emit(nodes):
            s = ""
            for n in nodes:
                if n[0] == "lit": s += _unescape(n[3])
                elif n[0] == "field":
                    if params.get(n[1].name) is None: raise ValueError(f"field {n[1].name}: no value")
                    s += n[1].printed(params[n[1].name])
                else:
                    sub = n[1]
                    flags = [x[2] for x in sub if x[0] == "lit" and x[2]]
                    fnames = [x[1].name for x in sub if x[0] == "field"]
                    want = any(params.get(f) is not None for f in fnames) or any(params.get(f) for f in flags)
                    if want: s += emit(sub)
            return s
        return emit(self.nodes)

class TemplateSet:
    """Several templates tried in order: the first complete match wins."""
    def __init__(self, templates): self.templates = templates
    def match(self, code):
        for i, t in enumerate(self.templates):
            r = t.match(code)
            if r is not None: return i, r
        return None
    def print(self, params, index=0): return self.templates[index].print(params)

def load(gen_dir):
    """The TemplateSet of a generator package folder: generator.toml [[template]] entries (pattern, optional escape), choices from [parameters]."""
    import tomllib
    from pathlib import Path
    toml = tomllib.loads((Path(gen_dir) / "generator.toml").read_text())
    ch = {k: v["values"] for k, v in toml.get("parameters", {}).items() if v.get("type") == "choice"}
    return TemplateSet([Template.parse(t["pattern"], ch, t.get("escape")) for t in toml["template"]])

if __name__ == "__main__":      # python3 runtime/fieldtemplate.py parse|print PACKAGE_DIR CODE|JSON   (the Rhai host's code_template() uses print)
    import json, sys
    cmd, gdir, arg = sys.argv[1:4]
    ts = load(gdir)
    try:
        if cmd == "parse":
            m = ts.match(arg)
            print(json.dumps({"template": m[0], "fields": m[1]} if m else {"refusal": {"kind": "invalid", "message": "no template matches"}}))
        else:
            print(ts.print(json.loads(arg)))
    except (Refusal, ValueError) as e:
        print(json.dumps({"refusal": {"kind": getattr(e, "kind", "invalid"), "message": str(e)}}))
