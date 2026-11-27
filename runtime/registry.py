"""Find generators (vendors/<vendor>/<series>/<generator>/generator.toml), match ordering codes against their [declares], and
call their entry points. The folder path is the id: vendors/hiwin/mg/rail-set is hiwin.mg.rail-set."""
from __future__ import annotations
import importlib, re, sys, tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

@dataclass
class CodeLine:
    code: str
    valid: bool
    opts: dict = field(default_factory=dict)
    note: str = ""

    @property
    def name(self) -> str:       # file name of its check result
        from runtime.sc import slug
        return slug(self.code) + "".join(f"-{k}" for k, v in sorted(self.opts.items()) if v is True)

class Generator:
    def __init__(self, path: Path):
        self.dir = Path(path)
        self.manifest = tomllib.loads((self.dir / "generator.toml").read_text())
        self.id = self.manifest["id"]
        self.pkg = ".".join(self.dir.relative_to(ROOT).parts) + ".src"

    def __repr__(self):
        return f"Generator({self.id})"

    def module(self, name: str):
        return importlib.import_module(f"{self.pkg}.{name}")

    def entry(self, key: str):
        mod, fn = self.manifest["entry"][key].split(":")
        return getattr(self.module(mod), fn)

    def build(self, code: str, **opts):
        """-> (part, command list). Raises ValueError (CodeError / NotModelled) for an invalid code."""
        return self.entry("build")(code, **opts)

    def check(self, part, sc_path, out_dir):
        return self.entry("check")(part, sc_path, out_dir)

    def matches(self, code: str) -> list[dict]:
        out = []
        for m in self.manifest.get("declares", {}).get("matches", []):
            flags = re.I if "i" in m.get("flags", "") else 0
            if re.search(m["pattern"], code.strip(), flags):
                out.append(m)
        return out

    def codes(self) -> list[CodeLine]:
        """codes.txt: `CODE [option ...]  # note` is a valid code to build and check; `!CODE  # why` must be rejected."""
        lines = []
        for raw in (self.dir / "codes.txt").read_text().splitlines():
            body, _, note = raw.partition("#")
            body = body.strip()
            if not body:
                continue
            valid = not body.startswith("!")
            parts = body.lstrip("!").split()
            lines.append(CodeLine(parts[0], valid, {o: True for o in parts[1:]}, note.strip()))
        return lines

def generators() -> list[Generator]:
    return [Generator(p.parent) for p in sorted(ROOT.glob("vendors/*/*/*/generator.toml"))]

def find(code: str) -> Generator:
    hits = [g for g in generators() if g.matches(code)]
    if not hits:
        raise ValueError(f"no generator declares a pattern that matches {code!r}")
    if len(hits) > 1:
        raise ValueError(f"{code!r} is claimed by several generators: {', '.join(g.id for g in hits)}")
    return hits[0]

def build(code: str, **opts):
    return find(code).build(code, **opts)
