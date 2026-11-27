"""Screenshot scene and view of a MISUMI shaft support (tools/shots, tools/preview)."""
from . import holder

def scene(code):
    return holder.parse_build(code)

def views(part):
    d = part.dims
    return [("", {"target": [0, 0, part.H1 / 2], "yaw": -0.7, "pitch": 0.45, "distance": max(80, part.H1 * 3.2)})]
