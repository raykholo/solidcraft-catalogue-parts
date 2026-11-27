"""Screenshot scene and view of a MISUMI linear bushing housing unit (tools/shots, tools/preview)."""
from . import housing

def scene(code):
    return housing.parse_build(code)

def views(part):
    d = part.d
    return [("", {"target": [0, 0, d["H"] / 2], "yaw": -0.7, "pitch": 0.45, "distance": max(120, part.L * 2.2, d["W"] * 2.5)})]
