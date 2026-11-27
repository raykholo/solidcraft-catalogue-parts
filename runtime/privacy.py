"""What must never be published from this repository, as byte patterns (shared by tools/lint and tools/privacy).

PERSONAL: home directories and personal addresses. PRIVATE: development-session links and trailers, and any mention of a vendor-CAD
"oracle" (no vendor CAD is ever used here). A maintainer can add their own words, such as the names of their machines, without
publishing them: one regular expression per line in the file named by $SC_PARTS_PRIVATE_WORDS (default
~/.config/sc-parts/private-words); blank lines and lines starting with # are skipped. The pre-push hook and a local tools/lint use
it; CI, which has no such file, checks the built-in patterns."""
import os, re
from pathlib import Path

PERSONAL = re.compile(rb"(/home/[A-Za-z0-9_.-]+|/var/home/|/Users/[A-Za-z0-9_.-]+|[A-Za-z]:\\Users\\|/root/|\bray@)")
PRIVATE = re.compile(rb"(?i)(claude\.ai/code/session|claude-session:|\boracle\b)")

def _local_words():
    f = Path(os.environ.get("SC_PARTS_PRIVATE_WORDS") or Path.home() / ".config" / "sc-parts" / "private-words")
    if not f.is_file():
        return None
    words = [l.strip() for l in f.read_text().splitlines() if l.strip() and not l.lstrip().startswith("#")]
    return re.compile(("(?i)(" + "|".join(f"(?:{w})" for w in words) + ")").encode()) if words else None

LOCAL = _local_words()

def find(blob: bytes, text: bool = True):
    """The first forbidden text in blob, with its kind, or None. text=False (inflated pixel data) checks only PERSONAL: the
    case-insensitive patterns are slow over megabytes of pixels and would only find noise there."""
    pats = (("personal path or address", PERSONAL), ("private development text", PRIVATE), ("private word", LOCAL))
    for kind, pat in pats if text else pats[:1]:
        if pat is not None:
            m = pat.search(blob)
            if m:
                return kind, m.group(0).decode(errors="replace")
    return None
