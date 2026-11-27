"""Screenshot scene and views of a MISUMI extrusion (tools/shots, tools/preview): the whole part and an end-on view of the section."""
from . import ext

def scene(code):
    return ext.parse_build(code)

def views(part):
    L = part.length
    sp = getattr(part, "spec", None)
    end = max(55, 2.6 * max(sp.w, sp.h)) if sp else 55       # 55 for the 2020, more for the larger sections
    return [("", {"target": [L / 2, 0, 0], "yaw": -0.7, "pitch": 0.5, "distance": max(60, L * 1.2)}),
            ("end", {"target": [0, 0, 0], "yaw": -1.5708, "pitch": 0.0, "distance": end})]
