"""Reference evaluator of SolidCraft generator packages, format `solidcraft-generator/1`.

Spec (v0, still moving): docs/formats/generator-package.md and generator-package.schema.json in the SolidCraft repository, draft pull
request 23175; our copy of the schema is schema/generator-package.schema.json and our notes and deviations are in
docs/generator-package.md. This module does what that spec says (grammar tokens, defaults, lookups, vars, rules, steps with when /
repeat, `${}` substitution, checks) over the package JSON, with no code in the package: every expression goes through runtime.expr.

Where the spec cannot express what a generator needs, the package carries an `x-` key and this evaluator implements it, marked
"x-" below and listed in docs/generator-package.md ("Gaps for the spec"):
  x-early-rules   rules run BEFORE the lookups (same shape as `rules`), so a code can be refused `not_modelled` although it has no table row.
  x-generator     the generator this package was exported from (id, version, sources hash, review evidence).
"""
from __future__ import annotations
import csv, io, json, math, re
from pathlib import Path
from runtime import expr as X
from runtime.expr import ExprError, Ctx, Budget, text

FORMAT = "solidcraft-generator/1"
MAX_PACKAGE, MAX_CODE, MAX_ROWS, MAX_COLS, MAX_POINTS = 1 << 20, 128, 5000, 64, 512
MAX_STEPS_PKG, MAX_EXPANDED, MAX_PARAM_JSON, MAX_REPEAT = 256, 512, 64 * 1024, 1024
MODEL_PREFIXES = ("sketch.", "solid.", "component.", "feature.", "parameter.")
KIND_CLASS = {"invalid": "CodeError", "not_modelled": "NotModelled"}

class Refusal(ValueError):
    """The ordering code is refused. kind: "invalid" or "not_modelled" (a real code this generator does not model)."""
    def __init__(self, kind: str, message: str):
        super().__init__(message)
        self.kind = kind

    @property
    def cls(self) -> str:
        return KIND_CLASS[self.kind]

class PackageError(ValueError):
    """The package itself is malformed."""

# ---- tables --------------------------------------------------------------------------------------
def _cell(v: str, typ: str, where: str):
    if typ == "text":
        return v
    if typ == "number":
        try:
            f = float(v)
        except ValueError:
            raise PackageError(f"{where}: {v!r} is not a number")
        if math.isnan(f) or math.isinf(f):
            raise PackageError(f"{where}: not finite")
        return f
    if typ == "list":
        return v.split()
    if typ == "points":
        pts = []
        for p in [q for q in v.split(";") if q.strip()]:
            xy = p.split()
            if len(xy) != 2:
                raise PackageError(f"{where}: point {p!r} is not 'x y'")
            pts.append([_cell(xy[0], "number", where), _cell(xy[1], "number", where)])
        if len(pts) > MAX_POINTS:
            raise PackageError(f"{where}: more than {MAX_POINTS} points")
        return pts
    raise PackageError(f"{where}: unknown column type {typ}")

class Table:
    def __init__(self, name: str, spec: dict):
        self.name, self.columns, self.keycols = name, spec["columns"], spec["key"]
        rows = list(csv.DictReader(io.StringIO(spec["csv"])))
        if len(rows) > MAX_ROWS or len(self.columns) > MAX_COLS:
            raise PackageError(f"table {name}: over {MAX_ROWS} rows or {MAX_COLS} columns")
        hdr = list(csv.reader(io.StringIO(spec["csv"])))[0] if rows else []
        for c in self.columns:
            if rows and c not in hdr:
                raise PackageError(f"table {name}: column {c} is not in the csv header")
        self.rows, self.index = [], {}
        for i, r in enumerate(rows, 2):
            rec = {c: (_cell(r[c], t, f"table {name} row {i} column {c}") if c in r else None) for c, t in self.columns.items()}
            for extra in ("source", "page", "status", "note"):
                if extra in r and extra not in rec:
                    rec[extra] = r[extra]
            key = tuple(text(rec[k]) for k in self.keycols)
            if key in self.index:
                raise PackageError(f"table {name}: key {key} repeated at row {i}")
            self.index[key] = rec
            self.rows.append(rec)

    def find(self, key: dict):
        return self.index.get(tuple(text(key[k]) for k in self.keycols))

# ---- templates -----------------------------------------------------------------------------------
def split_template(s: str) -> list:
    """`a ${expr} b` -> [("t","a "),("e","expr"),("t"," b")]; `$${` is a literal `${`."""
    out, i, buf = [], 0, []
    while i < len(s):
        if s.startswith("$${", i):
            buf.append("${"); i += 3
        elif s.startswith("${", i):
            j, depth, instr = i + 2, 1, False
            while j < len(s):
                ch = s[j]
                if instr:
                    if ch == "\\": j += 1
                    elif ch == '"': instr = False
                elif ch == '"': instr = True
                elif ch == "{": depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0: break
                j += 1
            if j >= len(s):
                raise PackageError(f"unterminated ${{ in {s!r}")
            if buf: out.append(("t", "".join(buf))); buf = []
            out.append(("e", s[i + 2:j])); i = j + 1
        else:
            buf.append(s[i]); i += 1
    if buf: out.append(("t", "".join(buf)))
    return out

_PLACE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_.]*)\}")

class Package:
    def __init__(self, data):
        if isinstance(data, (str, Path)):
            p = Path(data)
            if p.stat().st_size > MAX_PACKAGE:
                raise PackageError("package file over 1 MiB")
            data = json.loads(p.read_text())
            self.path = p
        else:
            self.path = None
        self.d = data
        self.id = data["id"]
        self.tables = {n: Table(n, t) for n, t in data.get("tables", {}).items()}
        self.warnings: list[str] = []

    def __repr__(self):
        return f"Package({self.id})"

    # ---- static validation -----------------------------------------------------------------------
    def validate(self, schema: dict | None = None) -> list[str]:
        """Schema, then everything the schema cannot say: expressions parse and use known names and functions in order (no forward
        reference), lookups name real tables and key columns, steps stay in the model-building commands, the grammar's field defaults
        exist, the RFC 0019 declarations hold (every example parses, every negative is refused), checks are well formed."""
        from runtime.schema import validate as schema_validate
        e: list[str] = []
        d = self.d
        if schema is not None:
            e += schema_validate(d, schema)
        if d.get("format") != FORMAT:
            e.append(f"format must be {FORMAT}")
        if e:
            return e
        scope: dict = {"code_in": None}          # name -> None (value) or set of columns (lookup record)
        def ex(src, where):
            try:
                X.parse(src)
                for r in X.refs(src):
                    if r[0].startswith("call:"):
                        nm = r[0][5:]
                        if nm not in X.ARITY: e.append(f"{where}: unknown function {nm}")
                        else:
                            lo, hi = X.ARITY[nm]
                            if not lo <= r[1] <= hi: e.append(f"{where}: {nm} takes {lo}..{hi} arguments")
                    else:
                        if r[0] not in scope: e.append(f"{where}: {'.'.join(r)} is not defined yet (names: fields, lookups, earlier vars, repeat index)")
                        elif len(r) > 1:
                            if scope[r[0]] is None: e.append(f"{where}: {r[0]} is not a lookup record")
                            elif r[1] not in scope[r[0]]: e.append(f"{where}: {r[0]} has no column {r[1]}")
                        elif scope[r[0]] is not None: e.append(f"{where}: {r[0]} is a lookup record, use {r[0]}.column")
            except ExprError as x:
                e.append(f"{where}: {x}")
        def text_names(s, where):
            for nm in _PLACE.findall(s):
                p = nm.split(".")
                if p[0] not in scope or (len(p) > 1 and (scope[p[0]] is None or p[1] not in scope[p[0]])):
                    e.append(f"{where}: {{{nm}}} is not a field, lookup column or variable")
        # grammar fields
        g = d["grammar"]
        for ai, alt in enumerate(g["alternatives"]):
            self._grammar_fields(alt, scope, e, f"grammar.alternatives[{ai}]")
        for name, src in d.get("defaults", {}).items():
            ex(src, f"defaults.{name}"); scope[name] = None
        for i, r in enumerate(d.get("x-early-rules", [])):
            ex(r["when"], f"x-early-rules[{i}].when"); text_names(r["refuse"], f"x-early-rules[{i}].refuse")
        for i, lk in enumerate(d.get("lookups", [])):
            w = f"lookups[{i}]"
            if lk["table"] not in self.tables: e.append(f"{w}: no table {lk['table']}"); continue
            t = self.tables[lk["table"]]
            if set(lk["key"]) != set(t.keycols): e.append(f"{w}: key columns {sorted(lk['key'])} are not the table's key {t.keycols}")
            for col, field in lk["key"].items():
                p = field.split(".")
                if p[0] not in scope or (len(p) > 1 and (scope[p[0]] is None or p[1] not in scope[p[0]])):
                    e.append(f"{w}: key field {field} is not defined yet")
            if "missing" in lk: text_names(lk["missing"], f"{w}.missing")
            scope[lk["as"]] = set(t.columns) | {"source", "page", "status", "note"}
        for i, v in enumerate(d.get("vars", [])):
            ex(v["expr"], f"vars[{i}] {v['name']}"); scope[v["name"]] = None
        for i, r in enumerate(d.get("rules", [])):
            ex(r["when"], f"rules[{i}].when"); text_names(r["refuse"], f"rules[{i}].refuse")
        if "refuse" in g: text_names(g["refuse"], "grammar.refuse")
        for i, st in enumerate(d["steps"]):
            w = f"steps[{i}]"
            if not st["command"].startswith(MODEL_PREFIXES):
                self.warnings.append(f"{w}: command {st['command']} is outside the model-building prefixes {MODEL_PREFIXES} (allowed-list question for the spec)")
            if "when" in st: ex(st["when"], f"{w}.when")
            inner = dict(scope)
            if "repeat" in st:
                rp = st["repeat"]; ex(rp["count"], f"{w}.repeat.count"); scope[rp["var"]] = None
            self._params(st.get("params", {}), ex, f"{w}.params", e)
            if "repeat" in st: del scope[st["repeat"]["var"]]
        if "insert" in d and "component" in d["insert"]:
            self._params(d["insert"]["component"], ex, "insert.component", e)
        for i, c in enumerate(d.get("checks", [])):
            for k, v in c.get("dimensions", {}).items():
                if k not in scope or scope[k] is not None: e.append(f"checks[{i}].dimensions.{k}: not a variable or field")
        for i, m in enumerate(d.get("declares", {}).get("matches", [])):
            for ex_ in m.get("examples", []):
                try: self.run(ex_)
                except Refusal as r: e.append(f"declares.matches[{i}]: example {ex_!r} is refused: {r}")
                except (ExprError, PackageError) as r: e.append(f"declares.matches[{i}]: example {ex_!r}: {r}")
            for ng in m.get("negative", []):
                try: self.run(ng); e.append(f"declares.matches[{i}]: negative {ng!r} is accepted")
                except Refusal: pass
                except (ExprError, PackageError): pass
        if len(d["steps"]) > MAX_STEPS_PKG: e.append("more than 256 steps")
        return e

    def _grammar_fields(self, toks, scope, e, where):
        for j, t in enumerate(toks):
            w = f"{where}[{j}]"
            if "lit" in t: continue
            if "field" in t:
                if sum(k in t for k in ("enum", "int", "decimal", "chars")) != 1: e.append(f"{w}: exactly one of enum / int / decimal / chars")
                scope[t["field"]] = None
            elif "optional" in t:
                self._grammar_fields(t["optional"], scope, e, w + ".optional")
                for k in t.get("default", {}): scope[k] = None
            elif "flags" in t:
                scope[t["flags"]["field"]] = None
            else:
                e.append(f"{w}: unknown token {sorted(t)}")

    def _params(self, v, ex, where, e):
        if isinstance(v, dict):
            for k, x in v.items(): self._params(x, ex, f"{where}.{k}", e)
        elif isinstance(v, list):
            for j, x in enumerate(v): self._params(x, ex, f"{where}[{j}]", e)
        elif isinstance(v, str):
            try:
                for kind, s in split_template(v):
                    if kind == "e": ex(s, where)
            except PackageError as x:
                e.append(f"{where}: {x}")

    # ---- grammar --------------------------------------------------------------------------------
    def _match(self, toks, s, pos, fields):
        """Match tokens at pos -> new pos or None. Hand-written, linear: an enum takes the longest listed value that fits, a number
        or a character run takes all it can, an optional group is taken when it fits and else its defaults apply."""
        for t in toks:
            if "lit" in t:
                lit = t["lit"]
                seg = s[pos:pos + len(lit)]
                if (seg.lower() != lit.lower()) if t.get("nocase") else (seg != lit): return None
                pos += len(lit)
            elif "field" in t:
                f = t["field"]
                if "enum" in t:
                    fit = [v for v in t["enum"] if s.startswith(v, pos)]
                    if not fit: return None
                    v = max(fit, key=len); fields[f] = v; pos += len(v)
                elif "int" in t or "decimal" in t:
                    spec = t.get("int") or t["decimal"]
                    m = re.compile(r"\d+" if "int" in t else r"\d+(?:\.\d+)?").match(s, pos)
                    if not m: return None
                    v = float(m.group(0))
                    if "decimal" in t and "." in m.group(0) and len(m.group(0).split(".")[1]) > spec.get("digits", 6): return None
                    if "min" in spec and v < spec["min"]: return None
                    if "max" in spec and v > spec["max"]: return None
                    step = spec.get("step", 1 if "int" in t else None)
                    if step:
                        base = spec.get("min", 0)
                        if abs((v - base) / step - round((v - base) / step)) > 1e-9: return None
                    fields[f] = v; pos = m.end()
                else:
                    cls = {"digits": str.isdigit, "alpha": lambda c: c.isalpha() and c.isascii(), "alnum": lambda c: c.isalnum() and c.isascii()}[t["chars"]]
                    j = pos
                    while j < len(s) and cls(s[j]) and j - pos < t.get("max_len", 64): j += 1
                    if j - pos < t.get("min_len", 1): return None
                    fields[f] = s[pos:j]; pos = j
            elif "optional" in t:
                trial = {}
                p2 = self._match(t["optional"], s, pos, trial)
                if p2 is None:
                    fields.update({k: v for k, v in t.get("default", {}).items()})
                else:
                    fields.update(trial); pos = p2
            elif "flags" in t:
                fl = t["flags"]; got = []
                opts = sorted(fl["options"], key=lambda o: -len(o["code"]))
                while pos < len(s):
                    o = next((o for o in opts if s.startswith(o["code"], pos) and o["value"] not in got), None)
                    if o is None: break
                    got.append(o["value"]); pos += len(o["code"])
                    if len(got) > fl.get("max", 8): return None
                fields[fl["field"]] = got
        return pos

    def parse_fields(self, code: str) -> dict:
        if len(code) > MAX_CODE:
            raise Refusal("invalid", f"an ordering code is at most {MAX_CODE} characters")
        for alt in self.d["grammar"]["alternatives"]:
            fields: dict = {}
            if self._match(alt, code, 0, fields) == len(code):
                return fields
        msg = self.d["grammar"].get("refuse", "{code} is not an ordering code of this generator")
        raise Refusal("invalid", msg.replace("{code}", code))

    def _subst_text(self, s: str, env: dict) -> str:
        def rep(m):
            p = m.group(1).split("."); v = env[p[0]]
            for q in p[1:]: v = v[q]
            return text(v)
        return _PLACE.sub(rep, s)

    # ---- the whole pipeline -----------------------------------------------------------------------
    def run(self, code: str, budget: Budget | None = None):
        """Parse `code`, run defaults / lookups / vars / rules, expand the steps. -> (env, commands). Raises Refusal."""
        d = self.d; budget = budget or Budget()
        env: dict = dict(self.parse_fields(code))
        env["code_in"] = code
        def ev(src, what):
            try:
                return X.evaluate(src, Ctx(env, budget))
            except ExprError as ex:
                raise Refusal("invalid", f"{what}: {ex} (in {src})")
        for name, src in d.get("defaults", {}).items():
            env[name] = ev(src, f"default {name}")
        for r in d.get("x-early-rules", []):
            if ev(r["when"], "rule"):
                raise Refusal(r.get("kind", "invalid"), self._subst_text(r["refuse"], env))
        for lk in d.get("lookups", []):
            key = {}
            for col, field in lk["key"].items():
                p = field.split("."); v = env[p[0]]
                for q in p[1:]: v = v[q]
                key[col] = v
            row = self.tables[lk["table"]].find(key)
            if row is None:
                raise Refusal("invalid", self._subst_text(lk.get("missing", f"{lk['table']}: no row for {text(list(key.values()))}"), env))
            env[lk["as"]] = row
        for v in d.get("vars", []):
            env[v["name"]] = ev(v["expr"], f"variable {v['name']}")
        for r in d.get("rules", []):
            w = ev(r["when"], "rule")
            if not isinstance(w, bool):
                raise Refusal("invalid", f"rule condition is not a boolean: {r['when']}")
            if w:
                raise Refusal(r.get("kind", "invalid"), self._subst_text(r["refuse"], env))
        cmds: list = []
        ins = d.get("insert", {}).get("component", "${code}")
        cmds.append({"command": "component.create", "params": {"name": self._value(ins, env, budget)}})
        for st in d["steps"]:
            if "when" in st:
                w = ev(st["when"], "step condition")
                if not isinstance(w, bool): raise Refusal("invalid", f"step condition is not a boolean: {st['when']}")
                if not w: continue
            if "repeat" in st:
                rp = st["repeat"]
                n = ev(rp["count"], "repeat count")
                if not isinstance(n, float) or n != int(n) or not 0 <= n <= min(rp["max"], MAX_REPEAT):
                    raise Refusal("invalid", f"repeat count {text(n)} is not a whole number from 0 to {rp['max']}")
                if len(cmds) + int(n) > MAX_EXPANDED + 1: raise Refusal("invalid", "more than 512 commands")
                for i in range(int(n)):
                    env[rp["var"]] = float(i)
                    cmds.append({"command": st["command"], "params": self._value(st.get("params", {}), env, budget)})
                env.pop(rp["var"], None)
            else:
                cmds.append({"command": st["command"], "params": self._value(st.get("params", {}), env, budget)})
        if len(cmds) > MAX_EXPANDED + 1: raise Refusal("invalid", "more than 512 commands")
        return env, cmds

    def build(self, code: str):
        return self.run(code)

    def _value(self, v, env, budget):
        if isinstance(v, dict): return {k: self._value(x, env, budget) for k, x in v.items()}
        if isinstance(v, list): return [self._value(x, env, budget) for x in v]
        if not isinstance(v, str): return v
        parts = split_template(v)
        try:
            if len(parts) == 1 and parts[0][0] == "e":
                return _out(X.evaluate(parts[0][1], Ctx(env, budget)))
            return X.text_limit("".join(s if k == "t" else text(X.evaluate(s, Ctx(env, budget))) for k, s in parts))
        except ExprError as ex:
            raise Refusal("invalid", f"{ex} (in {v})")

    # ---- checks -------------------------------------------------------------------------------
    def check_cheap(self) -> list[tuple]:
        """The package's `checks` that need no SolidCraft: every invalid code is refused with the text, every valid code builds and its
        `dimensions` equal the variables. -> [(ok, code, what)]"""
        out = []
        for c in self.d.get("checks", []):
            code = c["code"]
            try:
                env, cmds = self.run(code)
            except Refusal as r:
                ok = c.get("invalid") is True and c.get("message_contains", "") in str(r)
                out.append((ok, code, f"refused: {r}" if c.get("invalid") else f"unexpected refusal: {r}")); continue
            if c.get("invalid"):
                out.append((False, code, "accepted but expected to be refused")); continue
            bad = [f"{k}={text(env[k])} != {v}" for k, v in c.get("dimensions", {}).items() if abs(env[k] - v) > 1e-9]
            out.append((not bad, code, "; ".join(bad) or "dimensions equal"))
        return out

def _out(v):
    """A value for a command parameter: whole numbers as integers, lists as arrays."""
    if isinstance(v, float) and v == int(v) and abs(v) < 1e15: return int(v)
    if isinstance(v, list):
        if len(v) > MAX_POINTS: raise ExprError("more than 512 list items handed to a command")
        return [_out(x) for x in v]
    return v

def diff(a, b, tol: float = 1e-9, path: str = "$") -> list[str]:
    """Differences between two JSON values: same structure, same text, numbers equal within tol."""
    if isinstance(a, bool) or isinstance(b, bool):
        return [] if a is b else [f"{path}: {a!r} != {b!r}"]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return [] if abs(a - b) <= tol else [f"{path}: {a!r} != {b!r}"]
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b)):
            if k not in a: out.append(f"{path}.{k}: missing on the left")
            elif k not in b: out.append(f"{path}.{k}: missing on the right")
            else: out += diff(a[k], b[k], tol, f"{path}.{k}")
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b): return [f"{path}: {len(a)} items != {len(b)} items"]
        out = []
        for i, (x, y) in enumerate(zip(a, b)): out += diff(x, y, tol, f"{path}[{i}]")
        return out
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]
