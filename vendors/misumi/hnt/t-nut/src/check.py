"""Spec check for MISUMI pre-assembly insertion nuts (nut.py, sources.toml S9)."""
from __future__ import annotations
from runtime.check import Rows, run_measure, find_key
from runtime.sc import slug
from . import nut as nt

def check(n, sc, out):
    cmds = [{"command": "inspect.measure", "params": {}},
            {"command": "model.faces", "params": {"body": n.code}},
            {"command": "model.threads", "params": {}},
            {"command": "inspect.measure", "params": {"items": [
                {"type": "face", "body": n.code, "point": [3, -nt.NECK / 2, n.T - 0.2]},
                {"type": "face", "body": n.code, "point": [3, nt.NECK / 2, n.T - 0.2]}]}},
            {"command": "component.metadata", "params": {"component": n.code}},
            {"command": "document.metadata", "params": {}}]
    r = run_measure(sc, cmds, out, slug(n.code))
    m = r[0]; body = m["bodies"][0]; bb = body["bbox"]
    faces = r[1]["faces"] if isinstance(r[1], dict) else r[1][0]["faces"]
    th = r[2]["threads"]
    R = Rows()
    R.eq("one closed body", 1, m["body_count"] if body["closed"] else 0, "S9")
    R.num("plan length along the slot", nt.PLAN, bb["max"][0] - bb["min"][0], 0.005, "S9 p.559 '10'")
    R.num("plan width across the slot", nt.PLAN, bb["max"][1] - bb["min"][1], 0.005, "S9 p.559 '10'")
    R.num("total thickness T", n.T, bb["max"][2] - bb["min"][2], 0.005, "S9 p.559 table T")
    R.num("neck width", nt.NECK, r[3]["distance_mm"], 0.005, "S9 p.559 '5.8'")
    sh = [f for f in faces if f.get("plane_normal") and abs(f["plane_normal"][2] - 1) < 1e-6 and abs(f["centroid"][2] - n.E) < 0.005]
    R.eq("shoulder faces at height E", 2, len(sh), "S9 p.559 table E", f"E={n.E:g}")
    bottom = [f for f in faces if f.get("plane_normal") and abs(f["plane_normal"][2] + 1) < 1e-6 and abs(f["centroid"][2]) < 0.005]
    R.eq("bottom face (5.8 wide) at z = 0", 1, len(bottom), "S9 p.559")
    sel = [t for t in th if t["designation"] == f"M{n.M}"]
    R.eq(f"thread M{n.M} present", 1, len(sel), "S9 p.559 'M'")
    if sel:
        R.num("thread runs through the nut (T)", n.T, sel[0]["end"] - sel[0]["start"], 0.01, "S9 p.559", "thickness T")
    R.true("thread axis at the plan centre", bool(sel) and abs(sel[0]["axis_point"][0] - nt.PLAN / 2) < 0.01 and abs(sel[0]["axis_point"][1]) < 0.01, "S9 p.559 plan view")
    R.eq("part number metadata", n.code, (r[4].get("metadata") or r[4]).get("part_number"), "-")
    R.eq("design part number", n.code, find_key(r[5], "part_number"), "-")
    return R
