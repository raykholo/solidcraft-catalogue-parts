# misumi.hbl.bracket: MISUMI 5 series extruded brackets (HBLTS, HBLTV, HBLTSW, HBLTVW, HBLTF, HBKTS, HBKUS, HBLUS, HBLTH)

Ordering code in (`HBLTSW5`), native SolidCraft design out: the L-shaped extruded bracket for the 6 mm slot of the 5 series extrusions, with its mounting holes.
Codes HBLTS5, HBLTS5-4, HBLTSB5, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTST5, HBKTS5, HBKTSB5, HBKUS5, HBKUSB5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5,
each with at most one alteration (`-C`, `-SET`, ...). Source: MISUMI FA catalogue 2014 p.2-539/540 (S40).

## Ordering code

```
HBLTS5 HBLTS5-4 HBLTSB5 CHBLTS5 NBLTS5     14 wide, 35 x 35, 2 holes (20 square extrusion)      -4: O4.5 holes for an M4 screw
HBLTV5 HBLTVB5                              19 wide, 35 x 35, 2 holes (25 square extrusion)
HBLTSW5                                     14 wide, 57 x 57, 4 holes
HBLTVW5                                     19 wide, 57 x 57, 4 holes
HBLTF5                                      14 wide, scalene: wall 57, foot 37, 3 holes
HBKTST5 HBKTS5 HBKTSB5                      14 wide, 35 x 35, 2 holes, perpendicularly machined, with 6 x 1 tabs for the slot (K 0.03 / 0.06)
HBKUS5 HBKUSB5                              14 wide, ultra thick 51 x 51 (9 thick), 2 holes at 41, with tabs (K 0.06)
NBLUS5 HBLUS5                               14 wide, ultra thick 51 x 51 (9 thick), 2 holes at 41, no tabs
HBLTH5 HBLTHB5                              eccentric: 12 wide, holes 5 from one side and 7 from the other, 35 x 35
```

The letter before `BL` or after the type is the finish: `B` black anodize, `C` prefix anodize plus clear paint, `N` prefix A6063S-T5 (sides and screw holes not anodized).

Alterations (one per code, after the type and the optional `-4`):

```
-C                                          M5 taps on both sides for cover mounting (not offered for HBLTSB5, HBKTST5, HBKTSB5, HBKUSB5)
-SET -SST -SEU -SSU -SEP -SSP -SEC          screw and nut set that comes with the bracket (all types)
```

Both kinds are accessories: accepted, written into the part description, not drawn. Other brackets of the same catalogue pages (tabbed `HBLFS...`, `HBLS5`)
are recognised and refused as not modelled.

## Dimensioned and appearance-only

**Dimensioned**: width, plate thickness (5, or 9 for the foot of the ultra thick types), both arm lengths, number, diameter and position of the holes (measured from the outer face of the other arm, on the centre line, or 5 from one side for the eccentric types), the 6 wide and 1 high tabs of the HBK types, material and surface (description), mass, screw, T nut and allowable load (description).

**Not guaranteed**:

- The arms are plain flat plates: the inner-corner web with its ribs, the triangular cut-outs of the ultra thick types and the edge rounds are not drawn, the catalogue gives no dimensions for them
- The O4.2 relief at the inner corner (12 mm from the outer faces) is published but not drawn
- The tabs of HBKTST5, HBKTS5, HBKTSB5, HBKUS5 and HBKUSB5 are drawn as 6 wide, 1 high strips (centred on the width, proud of the outer faces) over the whole arm length: width and height are published, the length and the end shape are appearance, approximate, and the 6 mm slot fit is not guaranteed
- The wall thickness of the ultra thick types (NBLUS5, HBLUS5, HBKUS5, HBKUSB5) is not labelled; the wall is drawn 9 thick like the labelled foot and is not dimension-checked
- The eccentric types HBLTH5 and HBLTHB5 put both holes 5 from the same side of the 12 wide plate (the page does not say which side); the mirror image is the same part
- Perpendicularity K of the machined types is only written into the description, nothing is checked against it
- Alteration C (M5 taps for cover mounting) and the screw sets SET, SST, SEU, SSU, SEP, SSP, SEC are accepted and recorded in the description only; neither the taps nor the screws and nuts are drawn
- Surface treatment and its colour are not drawn
- Mass is the catalogue value in the description; the drawn plates weigh less because the web is missing

## Run

```
tools/gen HBLTSW5                          # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/misumi/hbl/bracket     # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/shots HBLTSW5                        # English and German screenshots into shots/
tools/preview vendors/misumi/hbl/bracket   # re-render preview.png
tools/provenance vendors/misumi/hbl/bracket   # re-write PROVENANCE.md (never edit it by hand)
```

`SC_VER` (default 0.50.0) picks the SolidCraft release; `SC_CLI`, `SC_APP` or `SC_RELEASES` say where the binaries are.
Invalid codes stop with a message (`CodeError: ...`); valid codes that are not drawn give `NotModelled`.

See `PROVENANCE.md` (generated) for where every number comes from and how it was verified, and `sources.toml` for the full citations.
