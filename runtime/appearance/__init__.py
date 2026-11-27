"""Appearance-only content: anything that is not a catalogue dimension (groove shapes, caps, colours, screws) is named with
this suffix, so a check, a reader or the part description can tell it from a dimensioned feature."""
APPX = "(appearance, approximate)"

def is_appearance(name: str) -> bool:
    return name.endswith(APPX)
