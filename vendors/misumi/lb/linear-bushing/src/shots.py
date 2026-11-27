"""Screenshot scene and view of a MISUMI linear bushing (tools/shots, tools/preview)."""
from . import bushing

def scene(code):
    return bushing.parse_build(code)

def views(part):
    size = max(part.L, part.flange["H"] if part.flange else part.D)
    return [("", {"target": [part.L / 2, 0, 0], "yaw": -0.6, "pitch": 0.45, "distance": max(40, size * 2.6)})]
