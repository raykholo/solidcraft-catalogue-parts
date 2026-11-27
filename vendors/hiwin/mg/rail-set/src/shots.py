"""Screenshot scene and views of a HIWIN MG rail set (tools/shots, tools/preview).

Shots-only extras live here, never in the part: the rail stands on a plain base plate (so the screw shanks read as going into a base),
joint markers and origin planes are hidden, and rail and blocks keep the builder's PBR looks (SC_SHOT_METAL=<library name> overrides them).
Set SC_MGN_CAPS=1 to show the plastic bolt caps (MGN12 / MGN15).
"""
import os
from . import build

def _metal(part, cmds):
    """The builder's own photoreal looks (PBR steel, ground faces, plastics) are kept; SC_SHOT_METAL=<library name> flattens rail and
    blocks to that one library look instead."""
    look = os.environ.get("SC_SHOT_METAL")
    if look:
        cmds = cmds + [{"command": "appearance.assign", "params": {"bodies": ["Rail"] + [f"Block {i + 1}" for i in range(part.n_blocks)], "appearance": look}}]
    return part, cmds

def scene(code):
    part, cmds = build.parse_build(code, base_plate=True)
    cmds = cmds + [
        {"command": "browser.visibility", "params": {"folder": "joints", "visible": False}},
        {"command": "browser.visibility", "params": {"folder": "origin", "visible": False}},
    ]
    return _metal(part, cmds)

def preview(code):
    """The part alone (no base plate, no hidden folders)."""
    return _metal(*build.parse_build(code))

def views(part):
    L = part.rail_length
    cx = build.block_centres(part)[-1]; b = part.block
    return [("", {"target": [L / 2, 0, 6], "yaw": -0.6, "pitch": 0.55, "distance": max(60, L * 1.1)}),
            ("block", {"target": [cx + b["L"] / 2 - 6, 0, b["H"] * 0.6], "yaw": -0.5, "pitch": 0.3, "distance": 2.6 * b["W"]})]
