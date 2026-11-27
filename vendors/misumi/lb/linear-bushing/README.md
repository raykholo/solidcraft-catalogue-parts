# misumi.lb.linear-bushing: MISUMI Economy linear bushings, straight, flanged, compact, pilot and centre flanged

Ordering code in (`E-LB10TUU`, `E-LBF20LUU`), native SolidCraft design out: the bushing body (outside diameter, bore at the nominal shaft
diameter, overall length), the two ring grooves of the medium straight type, and the round or square flange with its four counterbored holes.
Types E-LB (straight), E-LBF / E-LBFZ / E-LBFM (round flange), E-LBK / E-LBKZ / E-LBKM (square flange), p.464-469; and, from p.470-480,
E-LBH / E-LBHZ / E-LBHM (compact flange: round ends clipped by two flats, 2 or 4 holes), the same three shapes with a pilot (E-LBFP, E-LBKP, E-LBHP and
their M types) and with the flange in the centre (E-LBFC, E-LBKC, E-LBHC and their M types).

## Ordering code

```
<type><dr><suffix>
type:   E-LB                         straight
        E-LBF  E-LBFZ  E-LBFM        round flange   (Z = counterbored from the opposite side, M = electroless nickel plated)
        E-LBK  E-LBKZ  E-LBKM        square flange  (same letters)
        E-LBH  E-LBHZ  E-LBHM        compact flange (same letters; dr 5 only as E-LBH5UU)
        E-LBFP E-LBKP E-LBHP         round / square / compact flange with pilot (M types: E-LBFPM, E-LBKPM, E-LBHPM)
        E-LBFC E-LBKC E-LBHC         round / square / compact centre flange     (M types: E-LBFCM, E-LBKCM, E-LBHCM)
suffix: TUU            short straight (E-LB, dr 6, 8, 10, 12, 13, 16, 20)
        DUU  DMUU      medium: straight E-LB dr 6, 8, 10, 12, 16, 20, 25, 30; flanged E-LBF / E-LBK dr 6-30 (DMUU = nickel plated)
        UU   LUU       flanged long, single / double: dr 6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50 (Z types dr 6-30 only);
                       compact E-LBH dr 5-50 (dr 5 single only); pilot dr 6, 8, 10, 12, 16, 20, 25, 30, 40; centre LUU only (same dr)
        DMUU           pilot and centre medium: dr 6-30, plain type letters only (E-LBFP30DMUU, E-LBHC6DMUU); compact medium E-LBH<dr>DUU / DMUU dr 6-30
```

Examples: `E-LB10TUU` (short), `E-LB12DUU` (the catalogue's own medium example), `E-LBF20LUU` and `E-LBF10DUU` (its flanged examples),
`E-LBFZ10UU`, `E-LBK16LUU`, `E-LBKM35LUU`, `E-LBK12DMUU`, `E-LBH5UU`, `E-LBHZ20UU`, `E-LBFP20LUU`, `E-LBKPM40LUU`,
`E-LBHP25DMUU`, `E-LBFC30DMUU`, `E-LBHCM40LUU`. The outside-diameter tolerance follows the type (plain or nickel plated, single or
double) and is written into the part description with the bore and length tolerances. Refused with a message: a bore size not offered for that
series, a flanged type with TUU, a straight type with UU / LUU, Z types above dr 30, the Z or M type letter on a medium flanged bushing (plating is
the M of DMUU there; the same for the medium pilot and centre bushings), pilot or centre types with UU / DUU where only LUU / DMUU
exist, and the stainless E-LBHS (named on p.470, no table printed).

## Dimensioned and appearance-only

**Dimensioned**: O.D. D, bore dr, overall length L (flange included), flange H / T / hole d / counterbore d1 and depth t / P.C.D., the square flange
W across flats, ring groove W, B and D1 (medium straight); compact flange width D+6 / D+8 / D+10, hole pitches A and F; pilot or flange
position l.

**Not guaranteed**:

- Balls, ball tracks, retainer and end seals (appearance, approximate): not drawn, the catalogue gives no dimensions for them
- The bore is a plain cylinder at the nominal shaft diameter dr; tolerances are written into the description, not drawn
- Which flange face carries the counterbores: barrel side as standard, outer face for the Z types (read from the figure)
- Corner orientation of the square flange (corners on the mounting-hole axes) and its corner clipping by the circle H (appearance, approximate)
- No chamfers or edge breaks are drawn (the catalogue gives none)
- Position of the two ring grooves of the medium straight bushing: B read as the clear distance between them, centred on the length
- Compact flange (E-LBH series): outline read as the circle H clipped by two flats D+6 / D+8 / D+10 apart, the long axis along the holes A apart (and F across from dr 16); the two-hole or four-hole pattern follows the figure
- Pilot and centre flanged bushings (E-LBFP, E-LBKP, E-LBHP, E-LBFC, E-LBKC, E-LBHC): l read as the distance from the end of the barrel to the flange face nearer that end; counterbores on the flange face on the long barrel side (figure reading)
- Stainless steel linear bushings (type E-LBHS) are mentioned on p.470 but no table is printed: not generated

Not drawn: the stainless variants named in the catalogue notes (no table) and the linear bushing housings (not read for this generator).

## Run

```
tools/gen E-LBF20LUU                 # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/misumi/lb/linear-bushing   # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/shots E-LBF20LUU                      # English and German screenshots into shots/
tools/preview vendors/misumi/lb/linear-bushing   # re-render preview.png
tools/provenance vendors/misumi/lb/linear-bushing   # re-write PROVENANCE.md (never edit it by hand)
```

`SC_VER` picks the SolidCraft release; `SC_CLI`, `SC_APP` or `SC_RELEASES` say where the binaries are.
Invalid codes stop with a message (`CodeError: ...`).

See `PROVENANCE.md` (generated) for where every number comes from and how it was verified, and `sources.toml` for the full citations.
