"""Screenshot scene and view of a MISUMI bracket (tools/shots, tools/preview)."""
from . import bracket

def scene(code):
    return bracket.parse_build(code)

def views(part):
    return [("", {"target": [part.W / 2, part.foot / 2, part.wall / 2], "yaw": -0.7, "pitch": 0.45, "distance": 150})]
