"""Tiny linear-expression helper: builds the parameter expressions ("w / 2 - depth + 10") that drive the sketch points."""
class Lin:
    def __init__(self, terms=None, c=0.0):
        self.t = {k: v for k, v in (terms or {}).items() if v}
        self.c = c
    @staticmethod
    def of(x):
        return x if isinstance(x, Lin) else Lin({}, float(x))
    def __add__(self, o):
        o = Lin.of(o); t = dict(self.t)
        for k, v in o.t.items(): t[k] = t.get(k, 0) + v
        return Lin(t, self.c + o.c)
    __radd__ = __add__
    def __neg__(self): return self * -1
    def __sub__(self, o): return self + (Lin.of(o) * -1)
    def __rsub__(self, o): return Lin.of(o) - self
    def __mul__(self, k): return Lin({a: b * k for a, b in self.t.items()}, self.c * k)
    __rmul__ = __mul__
    def value(self):
        """A number when no parameter is involved, else the expression text."""
        if not self.t:
            return round(self.c, 9) + 0.0
        s = ""
        for k, v in self.t.items():
            mag = abs(v)
            term = k if mag == 1 else f"{mag:g}*{k}"
            s += (" - " if v < 0 else (" + " if s else "")) + term if s or v < 0 else term
        if s.startswith(" - "): s = "-" + s[3:]
        if abs(self.c) > 1e-12:
            s += f" {'-' if self.c < 0 else '+'} {abs(self.c):.9g}"
        return s
def P(name): return Lin({name: 1.0})
