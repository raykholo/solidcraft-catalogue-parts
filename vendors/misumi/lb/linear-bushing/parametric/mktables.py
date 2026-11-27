import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[4])); sys.path.insert(0, str(HERE))
import pkgfiles, rows
pkg = HERE / "linear-bushing"
pkgfiles.write_tables(pkg, HERE.parent / "data"); pkgfiles.write_toml(pkg, HERE.parent / "data", rows.make_rows())
