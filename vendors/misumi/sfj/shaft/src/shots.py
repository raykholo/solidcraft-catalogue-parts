"""Screenshot scene and view of a MISUMI linear shaft (tools/shots, tools/preview)."""
from . import shaft

def scene(code):
    return shaft.parse_build(code)

def views(part):
    return [("", {"target": [part.L / 2, 0, 0], "yaw": -0.6, "pitch": 0.4, "distance": max(50, part.L * 1.4)})]
