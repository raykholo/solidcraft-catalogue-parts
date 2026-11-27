# misumi.lhb.tall-housing: MISUMI Economy linear bushing housing units with dowel holes (tall blocks)

Ordering code in (`E-LBHS10`, `E-LBHS16L-P`, `E-LBHSW20-P`), native SolidCraft design out: the aluminium tall block (width W, height H, length L), the
shaft bore at the nominal diameter dr at height h above the base, the tapped holes M1 (top) and M2 (side) with their effective lengths, the d1 x t
counterbores and optional dowel holes. The housings hold the bushings of `misumi.lb.linear-bushing` and run on the shafts of `misumi.sfj.shaft`.
The built-in bushing is **not drawn**: the bore is left empty. The wide blocks are in `misumi.lhb.bushing-housing`, the centre-hole-height types in `misumi.lhb.housing-g`.

## Ordering code

```
E-LBHS<dr>[D|S|L][-P]   tall block: single (no suffix), medium (D), medium long (S), long (L)
                          single: dr 5, 6, 8, 10, 12, 13, 16, 20, 25, 30        medium: 6, 8, 10, 12, 16, 20, 25, 30
                          medium long: 12, 16, 20, 25, 30                       long: 8, 10, 12, 13, 16, 20, 25, 30
E-LBHSW<dr>[-P]         tall block, double (no suffix), dr as the single
-P                      with dowel holes (and 2 dowel pins): single and double dr 8 and up, long dr 16 and up only
```

Examples: `E-LBHS10`, `E-LBHS12S` (the catalogue's own medium long example), `E-LBHS16L-P`, `E-LBHSW10` and `E-LBHSW10-P` (its examples). Refused with a message:
a dr not offered for that length, -P at dr 5 / 6, -P on the medium and medium long housings, -P on the long type below dr 16, a length suffix on E-LBHSW, anything else after the dr.
Stainless steel bushings `E-LBHS<dr>UU` (not these housings) belong to `misumi.lb.linear-bushing`, which refuses them: the two code families do not overlap.

## Dimensioned and appearance-only

**Dimensioned**: L, W, H, bore dr and its height h above the base, hole spacings L1 and L2, thread sizes M1 / M2 with their effective lengths (the M2 length is the
thread depth), l, counterbore d1 x t, dowel hole diameter P, depth l2 and the distances E and F. Tolerances of dr are written into the description, not drawn.

**Not guaranteed**:

- The built-in linear bushing is not drawn: the bore is an empty plain cylinder at the nominal shaft diameter dr (the catalogue prints the dr tolerance and the bushing length D, but no inner dimensions of the unit); dr tolerances are written into the description, not drawn
- Hole layout (appearance, approximate): the tables print M1, M2 with effective lengths, d1 x t, l, L1 and L2, but the figures do not show unambiguously which hole sits where. Drawn as read: 2 vertical M1 holes in the top face L1 apart on a diagonal at x = +-0.35 W; 2 horizontal M2 holes (3 on the long type, the middle one at mid-length) from the +X face L2 apart at l below the top face; one d1 x t counterbore from the opposite face coaxial with each M2 hole. Only the sizes, depths and spacings are printed; the sides, the x offset and the coaxial placement are not
- Dowel hole positions (appearance, approximate): P and depth l2 and the distances E (and F, single only) are printed; the single housing is drawn with the diagonal pair (-F/2, -E/2), (F/2, E/2), the double and long housings on the centre line E apart. C1 and the dimension B of the A view are not drawn
- Through holes of the counterbores (bolt clearance holes), grease nipple hole (M5 x 0.8, dimension Q) of the medium long and long types, the datum edge chamfers, resin retainer colours and the MISUMI label are not drawn; the printed columns D, (S), P and C are not modelled
- dr tolerance as printed: +0.003 / -0.012 (dr 5-16) and -0.013 (dr 20-30) on p.488 and p.489; +0.003 / -0.012 (dr 6-16) and -0.015 (dr 20-30) on p.490: only echoed in the description
- Load ratings, allowable static moments and masses are not modelled

## Run

```
tools/gen E-LBHS16L-P                              # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/misumi/lhb/tall-housing        # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/preview vendors/misumi/lhb/tall-housing
tools/provenance vendors/misumi/lhb/tall-housing   # re-write PROVENANCE.md (never edit it by hand)
```

Invalid codes stop with a message (`CodeError: ...`). See `PROVENANCE.md` (generated) and `sources.toml` for every citation (S14, catalogue pages 488-490).
