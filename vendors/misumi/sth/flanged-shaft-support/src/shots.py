"""Screenshot scene and view of a MISUMI flanged shaft support (tools/shots, tools/preview)."""
from . import support

def scene(code):
    return support.parse_build(code)

def views(part):
    return [("", {"target": [0, 0, part.L / 2], "yaw": -0.7, "pitch": 0.45, "distance": max(80, part.dims["H"] * 3.2)})]
