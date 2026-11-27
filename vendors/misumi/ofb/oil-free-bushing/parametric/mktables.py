import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[4])); sys.path.insert(0, str(HERE))
import pkgfiles, rows
pkg = HERE / "oil-free-bushing"
R, _ = rows.make_rows()
pkgfiles.write_tables(pkg, HERE.parent / "data", R); pkgfiles.write_toml(pkg, R)
