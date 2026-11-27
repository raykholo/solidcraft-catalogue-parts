# misumi.lhb.bushing-housing: MISUMI Economy linear bushing housing units (wide blocks)

Ordering code in (`E-LBHN16`, `E-LBHNW20L-P`), native SolidCraft design out: the aluminium housing block (width W, height H, length L, top shoulders),
the shaft bore at the nominal diameter dr at height h below the top face, the four (six on the Long type) mounting holes with their M thread and
pilot hole, and optional dowel holes. The housings hold the bushings of `misumi.lb.linear-bushing` and run on the shafts of `misumi.sfj.shaft`.
The built-in bushing itself is **not drawn**: the bore is left empty (no sleeve), because the catalogue gives only the outer unit.

## Ordering code

```
E-LBHN<dr>[D][-P]     wide block, single (no suffix) or medium (D)                 dr 6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50
                                                                                     (medium: 6, 8, 10, 12, 16, 20, 25, 30)
E-LBHNW<dr>[D|L][-P]  wide block, double (no suffix), medium long (D) or long (L)  double: 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50
                                                                                     medium long: 16, 20, 25, 30; long: 12, 16, 20, 25, 30
-P                    with dowel holes (and 2 dowel pins), dr 8 and up
```

Examples: `E-LBHN16` (the catalogue's own), `E-LBHN16D-P`, `E-LBHNW16` and `E-LBHNW16-P` (its double examples), `E-LBHNW20L-P`. Refused with a
message: a dr not offered for that length, -P at dr 6, D on the single-only sizes, L on E-LBHN, anything after the length other than -P.

## Dimensioned and appearance-only

**Dimensioned**: overall length L, width W, height H, bore dr and its height h below the top face, shoulder height H2, H1 (the lower end of the body wall
from the top face), mounting hole spacing W1 x L1, thread M with depth l, pilot hole d, dowel hole diameter P and depth l2. Tolerances of dr, L, h, H1, W and W1
are written into the description, not drawn.

**Not guaranteed**:

- The built-in linear bushing is not drawn: the bore is an empty plain cylinder at the nominal shaft diameter dr (the catalogue gives no inner dimensions of the unit); dr tolerances are written into the description, not drawn
- Cross-section outline (appearance, approximate): the narrower lower wall (1 mm behind the top shoulders), the foot width (0.16 W) and the 3-point chamfer shape are not printed; only W, H, H1 (from the top face) and H2 (shoulder height) are
- Dowel hole positions (appearance, approximate): no coordinates are printed; read from the figures. P and depth l2 are dimensioned; C1 is printed without a clear meaning and is not drawn
- The mounting threads: M and thread depth l are printed; the pilot hole d is drawn through the full height H (read from the figure)
- Grease nipple hole (A-MT6M1) of the E-LBHNW types, the 2-C datum edge chamfers, the shallow recess between the top shoulders, and the printed columns A, B, N, P (second table of p.487) and C are not drawn
- dr tolerance of the medium E-LBHN as printed (0 / -0.12 for dr 6-16, 0 / -0.15 for dr 20-30): recorded as read, only echoed in the description
- Load ratings, allowable moments and masses are not modelled

Not in this generator: the tall blocks with dowel holes (E-LBHS / E-LBHSW, p.488-490) are in `misumi.lhb.tall-housing`, the center-hole-height-optional units (E-LBHG / E-LBHGW, p.491) in `misumi.lhb.housing-g`; the oil free bushing housing units are not drawn.

## Run

```
tools/gen E-LBHN16D-P                      # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/misumi/lhb/bushing-housing   # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/shots E-LBHN16D-P                    # English and German screenshots into shots/
tools/preview vendors/misumi/lhb/bushing-housing
tools/provenance vendors/misumi/lhb/bushing-housing   # re-write PROVENANCE.md (never edit it by hand)
```

Invalid codes stop with a message (`CodeError: ...`). See `PROVENANCE.md` (generated) and `sources.toml` for every citation (S12, catalogue pages 485-487).
