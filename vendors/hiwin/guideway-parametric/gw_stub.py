"""Guideway parsing policy over the shared template/Rhai adapter."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from runtime.parametric.package import Package as SharedPackage


class Package(SharedPackage):
    def __init__(self, folder):
        super().__init__(folder, no_match=lambda code: f"no template of the generator matches {code!r}",
                         no_match_reason="no_template", typed_code_field="raw_code")
