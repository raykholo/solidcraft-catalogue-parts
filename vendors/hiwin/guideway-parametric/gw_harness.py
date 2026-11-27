#!/usr/bin/env python3
"""Guideway-specific proof plans; execution lives in runtime.parametric.guideway."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
import gw_model as gm
from runtime.parametric.guideway import main

PLANS = {
    "EG": dict(rebuild=[("length 1000 -> 1240", "EGH20CA2R1000ZAH", {"length": "1240 mm"}, "EGH20CA2R1240ZAH"),
                        ("blocks 1 -> 2", "EGW25CA1R640ZAP", {"blocks": "2"}, "EGW25CA2R640ZAP")],
               insert=("EGH-CA-20", "EGH20CA1R400")),
    "HG": dict(rebuild=[("length 1000 -> 1240", "HGH20CA2R1000ZAH", {"length": "1240 mm"}, "HGH20CA2R1240ZAH"),
                        ("blocks 1 -> 2", "HGW25CC1R640ZAP", {"blocks": "2"}, "HGW25CC2R640ZAP"),
                        ("length 640 -> 760 (rail mounted from the bottom)", "HGW25CC1T640ZAP", {"length": "760 mm"}, "HGW25CC1T760ZAP")],
               insert=("HGH-CA-20-R", "HGH20CA1R400")),
    "RG": dict(rebuild=[("length 1000 -> 1240", "RGH20HA2R1000ZAH", {"length": "1240 mm"}, "RGH20HA2R1240ZAH"),
                        ("blocks 1 -> 2", "RGW25CC1R640ZAP", {"blocks": "2"}, "RGW25CC2R640ZAP")],
               insert=("RGH-CA-20", "RGH20CA1R400")),
}

if __name__ == "__main__":
    key = sys.argv[1]
    main(gm.SERIES[key], PLANS[key], sys.argv[2], sys.argv[3])
