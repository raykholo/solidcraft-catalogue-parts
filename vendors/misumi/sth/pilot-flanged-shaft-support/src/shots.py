"""Screenshot scene and view of a MISUMI pilot flanged shaft support (tools/shots, tools/preview)."""
from . import pilot

def scene(code):
    return pilot.parse_build(code)

def views(part):
    return [("", {"target": [0, 0, part.dims["L1"] / 2], "yaw": -0.7, "pitch": 0.45, "distance": max(80, part.dims["H"] * 3.2)})]
