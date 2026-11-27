"""Screenshot scene and view of a MISUMI shaft collar (tools/shots, tools/preview)."""
from . import collar

def scene(code):
    return collar.parse_build(code)

def views(part):
    return [("", {"target": [0, 0, part.B / 2], "yaw": -0.6, "pitch": 0.6, "distance": max(40, part.D1 * 2.4)})]
