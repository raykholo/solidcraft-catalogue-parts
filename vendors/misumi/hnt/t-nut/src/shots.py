"""Screenshot scene and view of a MISUMI T-nut (tools/shots, tools/preview)."""
from . import nut

def scene(code):
    return nut.parse_build(code)

def views(part):
    return [("", {"target": [5, 0, 2], "yaw": -0.7, "pitch": 0.5, "distance": 45})]
