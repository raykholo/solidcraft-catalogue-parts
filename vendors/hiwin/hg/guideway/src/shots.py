"""Screenshot scene and views of a HIWIN HG rail, block or set (tools/shots, tools/preview).

Shots-only extras live here, never in the part: the rail stands on a plain base plate so the screw shanks read as going into a base,
and joint markers and origin planes are hidden. The rail, blocks, plastics and screws keep the builder's PBR looks.
"""
from . import build

def scene(code):
    part, cmds = build.parse_build(code)
    if part.kind != "block":
        r = part.rail; ln = float(r["bolt"].split("x")[1]) if part.rail_mount == "R" else 0.0; th = ln + 3
        cmds = cmds + [
            {"command": "solid.box", "params": {"length": part.rail_length + 30, "width": r["WR"] + 50, "height": th,
                                                "corner": [-15, -(r["WR"] + 50) / 2, -th], "operation": "new",
                                                "body_name": "Base plate (screenshot only)", "name": "Base plate (screenshot only)"}},
            {"command": "appearance.assign", "params": {"bodies": ["Base plate (screenshot only)"], "appearance": "starter.metal.aluminum-bead-blast"}},
        ]
    cmds = cmds + [
        {"command": "browser.visibility", "params": {"folder": "joints", "visible": False}},
        {"command": "browser.visibility", "params": {"folder": "origin", "visible": False}},
    ]
    return part, cmds

def preview(code):
    """The part alone (no base plate, no hidden folders)."""
    return build.parse_build(code)

def views(part):
    L = part.rail_length or 3 * part.block["L"]
    out = [("", {"target": [L / 2, 0, 6], "yaw": -0.6, "pitch": 0.55, "distance": max(60, L * 1.1)})]
    if part.block:
        cx = build.block_centres(part)[-1]; b = part.block
        out.append(("block", {"target": [cx + b["L"] / 2 - 6, 0, b["H"] * 0.6], "yaw": -0.5, "pitch": 0.3, "distance": 2.6 * b["W"]}))
    return out
