"""Screenshot scene and view of a MISUMI centre-hole-height-optional housing unit (tools/shots, tools/preview)."""
from . import housing

def scene(code):
    return housing.parse_build(code)

def views(part):
    return [("", {"target": [0, 0, part.H1 / 2], "yaw": -0.7, "pitch": 0.45, "distance": max(120, part.T * 2.2, part.d["L"] * 2.5)})]
