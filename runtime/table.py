"""Read the data/*.csv dimension tables: strings stay strings, numbers become int or float (as written), empty is None."""
from __future__ import annotations
import csv

def num(v):
    if v is None or v == "":
        return None
    try:
        f = float(v)
    except ValueError:
        return v
    return f if ("." in v or "e" in v.lower() or "inf" in v.lower() or "nan" in v.lower()) else int(f)

def read_csv(path) -> list[dict]:
    with open(path, newline="") as f:
        return list(csv.DictReader(f))
