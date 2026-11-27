# misumi.sth.flanged-shaft-support: MISUMI Economy flanged shaft supports

Ordering code in (`E-STHRB12`, `E-STHWSL30`), native SolidCraft design out: a flanged shaft support with its shaft bore (H8), the flange
mounting holes and, per type, the tapped set screw holes, the blind bore of the end mounting type or the clamp groove, slit and clamp screw
of the slit types. These hold the linear shafts of `misumi.sfj.shaft`; the clamp-type T supports are in `misumi.shf.shaft-holder`.

## Ordering code

```
<type><D>
standard sleeve   E-STHRB E-STHR  round        E-STHSB E-STHS square       E-STHCB E-STHC E-SSTHC compact        (S51 p.534-535)
long sleeve       E-STHRBL E-STHRL  E-STHSBL E-STHSL  E-STHCBL E-STHCL                                          (S51 p.534-535, D marked *)
compact clamp     E-STHMRB E-STHMR  and long E-STHMRBL E-STHMRL                                                  (S52 p.532)
end mounting      E-STHXRB E-STHXR round     E-STHXCB E-STHXC compact                                          (S52 p.533)
thickened         E-STHRBN E-STHRN round     E-STHCBN E-STHCN compact, long ...NL                              (S52 p.536)
flanged with slit E-STHWRB E-STHWR E-SSTHWR round, E-STHWSB E-STHWS E-SSTHWS square, E-STHWCB E-STHWC E-SSTHWC compact, long ...L   (S52 p.538-539)
```

B = black oxide film, no B = electroless nickel plating, E-SS.. = stainless steel. D is the shaft bore diameter (H8); the sizes of each series are
the rows of its table (`data/*.csv`). Examples: `E-STHRB8` (the catalogue's own), `E-STHRBL12`, `E-STHMRL16`, `E-STHXCB8`, `E-STHRBN8`,
`E-STHWRB10` (the catalogue's own for the slit types), `E-SSTHWCL12`.

Refused with a message: a D that is not in the table of that series, a long sleeve type for a D that is not marked * on the page, every
"not applicable" note of the pages (E-STHS D6, E-STHR D15, E-SSTHC D50, E-STHRN D8 / D35, E-STHCN D10, E-STHRBN D35, E-STHXRB D8,
E-STHMRBL D25, E-SSTHWR D35, E-SSTHWS D40 / D50, E-SSTHWSL D12; each applied to the named type only), a missing D and a type that is not in
the catalogue (for example a square thickened type).

## Dimensioned and appearance-only

**Dimensioned**: bore D and its H8 tolerance (written into the description), sleeve outside diameter D1 and length L (L1 for the long
sleeve), flange thickness T, flange H (round diameter, square extent across the cut corners, compact length), K (square side) and W (compact width), the mounting holes (d1, d on P
for round and square, on P1 and F for compact), the set screws M at l (l1, and 2 x l1 for the long sleeve D16 and up) from the flange back
face; the end mounting bore floor l1, the through hole d2 and the counterbore d1 with depth l; for the slit types and E-STHMR the groove
(S1 / S wide, at B from the sleeve end), the radial slit, the clamp screw M at X above the axis with its clearance hole, counterbore (floor Y
from the slit centre) and tapped hole. Thickness (N) is the sleeve wall (D1 - D) / 2, checked in every row.

**Not guaranteed**: see `generator.toml` (`[guarantee]`): the compact flange corner radii, the rotation of the set screws about the axis,
the reading of the square flange K, the groove depth and the slit stub below the bore, the E-STHMR counterbore depth, the side of the clamp
screw, chamfers, the supplied screws, surface treatment, and which D the "not applicable" notes exclude.

## Run

```
tools/gen E-STHRB12                          # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/misumi/sth/flanged-shaft-support   # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/shots E-STHRB12                        # English and German screenshots into shots/
tools/preview vendors/misumi/sth/flanged-shaft-support
tools/provenance vendors/misumi/sth/flanged-shaft-support   # re-write PROVENANCE.md (never edit it by hand)
```

Invalid codes stop with a message (`CodeError: ...`). See `PROVENANCE.md` (generated) and `sources.toml` for every citation (S51, catalogue
pages 534-535; S52, pages 532, 533, 536, 538, 539). Not covered: the aluminium types and the positioning hole (p.536 lower half, p.537).
