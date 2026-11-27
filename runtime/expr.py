"""The expression language of SolidCraft generator packages (spec: docs/formats/generator-package.md, section 4, in the SolidCraft
repository; summarised in docs/generator-package.md). A hand-written tokenizer and precedence parser: no eval, no `ast`, no I/O,
no loops, no user functions. Values are numbers (finite floats), text, booleans and lists. Errors are ExprError; the caller turns one
into a refusal of the code.

  expr   := or ("?" expr ":" expr)?
  or     := and ("||" and)*          and := eq ("&&" eq)*          eq := rel (("=="|"!=") rel)*
  rel    := add (("<"|"<="|">"|">=") add)*     add := mul (("+"|"-") mul)*     mul := unary (("*"|"/"|"%") unary)*
  unary  := ("-"|"!") unary | primary
  primary:= number | "text" | name ("." name)* | name "(" [expr ("," expr)*] ")" | "(" expr ")"

Functions: min max abs round floor ceil sqrt pow sin cos tan asin acos atan atan2 (degrees) pi() if in len at join fmt concat upper lower.
Bounds: 512 characters, nesting depth 32, 10000 evaluation steps per expression, 1,000,000 per build.
"""
from __future__ import annotations
import math, re

MAX_CHARS, MAX_DEPTH, MAX_STEPS, MAX_BUILD_STEPS, MAX_TEXT, MAX_LIST = 512, 32, 10_000, 1_000_000, 4096, 512

class ExprError(ValueError):
    pass

_TOK = re.compile(r"\s*(?:(?P<num>\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)|(?P<str>\"(?:[^\"\\]|\\.)*\")|(?P<name>[A-Za-z_][A-Za-z0-9_]*)|(?P<op>\|\||&&|==|!=|<=|>=|[-+*/%<>!?:(),.]))")

def _tokens(src: str):
    pos, out = 0, []
    src = src.rstrip()
    while pos < len(src):
        m = _TOK.match(src, pos)
        if not m or m.end() == pos:
            raise ExprError(f"unexpected character {src[pos:].lstrip()[:1]!r} in {src!r}")
        pos = m.end()
        kind = m.lastgroup
        v = m.group(kind)
        if kind == "num": out.append(("num", float(v)))
        elif kind == "str": out.append(("str", re.sub(r"\\(.)", r"\1", v[1:-1])))
        else: out.append((kind, v))
    return out

class _Parser:
    def __init__(self, src):
        if len(src) > MAX_CHARS:
            raise ExprError(f"expression longer than {MAX_CHARS} characters")
        self.src, self.t, self.i, self.depth = src, _tokens(src), 0, 0

    def peek(self): return self.t[self.i] if self.i < len(self.t) else (None, None)
    def eat(self, v=None):
        k, x = self.peek()
        if k is None or (v is not None and x != v):
            raise ExprError(f"expected {v!r} in {self.src!r}")
        self.i += 1
        return k, x
    def at(self, *ops):
        k, x = self.peek()
        return k == "op" and x in ops

    def parse(self):
        e = self.expr()
        if self.i != len(self.t):
            raise ExprError(f"unexpected {self.peek()[1]!r} in {self.src!r}")
        return e

    def expr(self):
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise ExprError(f"expression nests deeper than {MAX_DEPTH}")
        c = self.bin(0)
        if self.at("?"):
            self.eat(); a = self.expr(); self.eat(":"); b = self.expr()
            c = ("if", c, a, b)
        self.depth -= 1
        return c

    LEVELS = [("||",), ("&&",), ("==", "!="), ("<", "<=", ">", ">="), ("+", "-"), ("*", "/", "%")]
    def bin(self, lvl):
        if lvl == len(self.LEVELS):
            return self.unary()
        left = self.bin(lvl + 1)
        while self.at(*self.LEVELS[lvl]):
            op = self.eat()[1]
            left = (op, left, self.bin(lvl + 1))
        return left

    def unary(self):
        if self.at("-", "!"):
            op = self.eat()[1]
            self.depth += 1
            if self.depth > MAX_DEPTH: raise ExprError(f"expression nests deeper than {MAX_DEPTH}")
            e = ("neg" if op == "-" else "not", self.unary())
            self.depth -= 1
            return e
        return self.primary()

    def primary(self):
        k, x = self.peek()
        if k == "num": self.eat(); return ("lit", x)
        if k == "str": self.eat(); return ("lit", x)
        if k == "op" and x == "(":
            self.eat(); e = self.expr(); self.eat(")"); return e
        if k == "name":
            self.eat()
            if self.at("("):
                self.eat(); args = []
                if not self.at(")"):
                    args.append(self.expr())
                    while self.at(","):
                        self.eat(); args.append(self.expr())
                self.eat(")")
                return ("call", x, args)
            path = [x]
            while self.at("."):
                self.eat(); path.append(self.eat()[1] if self.peek()[0] == "name" else self._bad())
            return ("ref", path)
        raise ExprError(f"unexpected {x!r} in {self.src!r}")

    def _bad(self):
        raise ExprError(f"name expected after '.' in {self.src!r}")

_CACHE: dict = {}
def parse(src: str):
    if src not in _CACHE:
        _CACHE[src] = _Parser(src).parse()
    return _CACHE[src]

def refs(src: str) -> list:
    """Every reference path (["s", "E"]) and function name ("call:min") the expression uses; for static checks."""
    out = []
    def walk(n):
        if n[0] == "ref": out.append(n[1])
        elif n[0] == "call":
            out.append(["call:" + n[1], len(n[2])])
            for a in n[2]: walk(a)
        elif n[0] != "lit":
            for a in n[1:]: walk(a)
    walk(parse(src))
    return out

ARITY = {"min": (1, 99), "max": (1, 99), "abs": (1, 1), "round": (1, 1), "floor": (1, 1), "ceil": (1, 1), "sqrt": (1, 1), "pow": (2, 2),
         "sin": (1, 1), "cos": (1, 1), "tan": (1, 1), "asin": (1, 1), "acos": (1, 1), "atan": (1, 1), "atan2": (2, 2), "pi": (0, 0),
         "if": (3, 3), "in": (2, 2), "len": (1, 1), "at": (2, 2), "join": (2, 2), "fmt": (2, 2), "concat": (1, 99), "upper": (1, 1), "lower": (1, 1)}

def text(v) -> str:
    """Value -> text, as `${...}` inside a string and `{name}` in a refusal text show it: whole numbers without a decimal point,
    other numbers in the shortest form that reads back, lists joined with ", "."""
    if isinstance(v, bool): return "true" if v else "false"
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e15: return str(int(v))
        return repr(v)
    if isinstance(v, list): return ", ".join(text(x) for x in v)
    return str(v)

def _num(v, what="value"):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ExprError(f"{what} must be a number, got {text(v)!r}")
    return float(v)

def _finite(x):
    if not isinstance(x, float) or math.isnan(x) or math.isinf(x):
        raise ExprError("result is not a finite number")
    return x

class Budget:
    def __init__(self): self.build = 0

class Ctx:
    """Evaluation context: `env` maps names to values (numbers, text, booleans, lists, or a dict for a lookup record)."""
    def __init__(self, env: dict, budget: Budget | None = None):
        self.env, self.budget, self.steps = env, budget or Budget(), 0

def evaluate(src: str, ctx: Ctx):
    ctx.steps = 0
    return _ev(parse(src), ctx)

def _ev(n, c: Ctx):
    c.steps += 1; c.budget.build += 1
    if c.steps > MAX_STEPS: raise ExprError("expression exceeds 10000 evaluation steps")
    if c.budget.build > MAX_BUILD_STEPS: raise ExprError("build exceeds 1,000,000 evaluation steps")
    k = n[0]
    if k == "lit": return n[1]
    if k == "ref":
        path = n[1]
        if path[0] not in c.env: raise ExprError(f"unknown name {path[0]!r}")
        v = c.env[path[0]]
        for p in path[1:]:
            if not isinstance(v, dict) or p not in v: raise ExprError(f"{'.'.join(path)}: no such column")
            v = v[p]
        return v
    if k == "neg": return -_num(_ev(n[1], c))
    if k == "not":
        v = _ev(n[1], c)
        if not isinstance(v, bool): raise ExprError("! needs a boolean")
        return not v
    if k == "if":
        t = _ev(n[1], c)
        if not isinstance(t, bool): raise ExprError("the condition of ?: must be a boolean")
        return _ev(n[2], c) if t else _ev(n[3], c)
    if k in ("&&", "||"):
        a = _ev(n[1], c)
        if not isinstance(a, bool): raise ExprError(f"{k} needs booleans")
        if (k == "&&") != a: return a
        b = _ev(n[2], c)
        if not isinstance(b, bool): raise ExprError(f"{k} needs booleans")
        return b
    if k in ("==", "!="):
        a, b = _ev(n[1], c), _ev(n[2], c)
        if type(a) is not type(b) and not (isinstance(a, float) and isinstance(b, float)):
            raise ExprError(f"cannot compare {type(a).__name__} with {type(b).__name__}")
        return (a == b) == (k == "==")
    if k in ("<", "<=", ">", ">="):
        a, b = _num(_ev(n[1], c)), _num(_ev(n[2], c))
        return {"<": a < b, "<=": a <= b, ">": a > b, ">=": a >= b}[k]
    if k in ("+", "-", "*", "/", "%"):
        a, b = _ev(n[1], c), _ev(n[2], c)
        if k == "+" and isinstance(a, str) and isinstance(b, str):
            if len(a) + len(b) > MAX_TEXT: raise ExprError("text longer than 4096 characters")
            return a + b
        a, b = _num(a), _num(b)
        if k == "+": return _finite(a + b)
        if k == "-": return _finite(a - b)
        if k == "*": return _finite(a * b)
        if b == 0: raise ExprError("division by zero")
        return _finite(a / b if k == "/" else math.fmod(a, b))
    if k == "call":
        return _call(n[1], [_ev(a, c) for a in n[2]], n[2], c)
    raise ExprError(f"bad expression node {k}")

def _call(name, a, _nodes, c):
    if name not in ARITY: raise ExprError(f"unknown function {name!r}")
    lo, hi = ARITY[name]
    if not lo <= len(a) <= hi: raise ExprError(f"{name} takes {lo if lo == hi else f'{lo} to {hi}'} argument(s), got {len(a)}")
    N = lambda i: _num(a[i], f"argument {i + 1} of {name}")
    if name in ("min", "max"):
        vals = [_num(x, name) for x in (a[0] if len(a) == 1 and isinstance(a[0], list) else a)]
        if not vals: raise ExprError(f"{name} of nothing")
        return min(vals) if name == "min" else max(vals)
    if name == "abs": return abs(N(0))
    if name == "round": x = N(0); return float(math.floor(x + 0.5)) if x >= 0 else -float(math.floor(-x + 0.5))
    if name == "floor": return float(math.floor(N(0)))
    if name == "ceil": return float(math.ceil(N(0)))
    if name == "sqrt":
        if N(0) < 0: raise ExprError("sqrt of a negative number")
        return math.sqrt(N(0))
    if name == "pow":
        try: return _finite(math.pow(N(0), N(1)))
        except (OverflowError, ValueError) as ex: raise ExprError(f"pow: {ex}")
    if name in ("sin", "cos", "tan"): return _finite(getattr(math, name)(math.radians(N(0))))
    if name in ("asin", "acos"):
        if not -1 <= N(0) <= 1: raise ExprError(f"{name} outside [-1, 1]")
        return math.degrees(getattr(math, name)(N(0)))
    if name == "atan": return math.degrees(math.atan(N(0)))
    if name == "atan2": return math.degrees(math.atan2(N(0), N(1)))
    if name == "pi": return math.pi
    if name == "if":
        if not isinstance(a[0], bool): raise ExprError("if: the condition must be a boolean")
        return a[1] if a[0] else a[2]
    if name == "in":
        if not isinstance(a[1], list): raise ExprError("in: the second argument must be a list")
        return any(type(x) is type(a[0]) and x == a[0] for x in a[1])
    if name == "len":
        if not isinstance(a[0], list): raise ExprError("len: needs a list")
        return float(len(a[0]))
    if name == "at":
        if not isinstance(a[0], list): raise ExprError("at: needs a list")
        i = N(1)
        if i != int(i) or not 0 <= i < len(a[0]): raise ExprError(f"at: index {text(i)} out of range 0..{len(a[0]) - 1}")
        return a[0][int(i)]
    if name == "join":
        if not isinstance(a[0], list): raise ExprError("join: needs a list")
        return text_limit(str(a[1]).join(text(x) for x in a[0]))
    if name == "fmt":
        d = N(1)
        if d != int(d) or not 0 <= d <= 12: raise ExprError("fmt: digits must be a whole number 0 to 12")
        return f"{N(0):.{int(d)}f}"
    if name == "concat": return text_limit("".join(text(x) for x in a))
    if name == "upper": return str(a[0]).upper()
    return str(a[0]).lower()

def text_limit(s: str) -> str:
    if len(s) > MAX_TEXT: raise ExprError("text longer than 4096 characters")
    return s
