# misumi.sth.dowel-flanged-shaft-support: MISUMI Economy flanged shaft supports with positioning holes

Ordering code in (`E-STHWRBK12`, `E-SSTHWCK30`), native SolidCraft design out: a steel flanged shaft support with its shaft bore (H8), four flange
mounting holes, two positioning (dowel) holes Q (H8), the clamp groove, the radial slit and the clamp screw. It holds the linear shafts of
`misumi.sfj.shaft`; the same support without the positioning holes is `misumi.sth.flanged-shaft-support`, the one with a pilot spigot is
`misumi.sth.pilot-flanged-shaft-support`.

## Ordering code

```
<type><D>
round flanged    E-STHWRBK<D> (black oxide)   E-STHWRK<D> (electroless nickel)   E-SSTHWRK<D> (stainless steel)
compact flanged  E-STHWCBK<D> (black oxide)                                      E-SSTHWCK<D> (stainless steel)      (S19 p.537)
```

D is the shaft bore diameter (H8): 12, 16, 20, 25 or 30. Examples: `E-STHWRBK12` (the catalogue's own), `E-STHWCBK25`, `E-SSTHWCK30`.

Refused with a message: a D that is not in the table, a missing D, a type that is not in the catalogue (there is no compact electroless nickel
type, no square type, and the slit type without positioning holes is `E-STHWRB`).

## Dimensioned and appearance-only

**Dimensioned**: bore D and its H8 tolerance (written into the description), sleeve outside diameter D1 and overall length L, flange thickness T,
flange H (round diameter or compact length) and W, the four mounting holes d on P (round) or on F by P1 (compact), the two positioning holes Q at
P / 2 from the axis, the groove (S1 wide, B + S1 from the sleeve end), the slit S, and the clamp screw M at X above the axis with its clearance
hole d2, counterbore d1 (floor Y from the slit centre) and tapped hole. Thickness (N) is the sleeve wall (D1 - D) / 2, checked in every row.

**Not guaranteed**: see `generator.toml` (`[guarantee]`): the compact flange outline, the angle of the round flange's positioning holes, the groove
depth and the slit stub, the side of the clamp screw, the H8 and position tolerances of Q, chamfers, the supplied screw, surface treatment, and that
both flange types are built for every D. The aluminium long-sleeve types on the upper half of p.537 are not part of this generator.

## Run

```
tools/gen E-STHWRBK20                          # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/misumi/sth/dowel-flanged-shaft-support   # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/shots E-STHWRBK20                        # English and German screenshots into shots/
tools/preview vendors/misumi/sth/dowel-flanged-shaft-support
tools/provenance vendors/misumi/sth/dowel-flanged-shaft-support   # re-write PROVENANCE.md (never edit it by hand)
```

Invalid codes stop with a message (`CodeError: ...`). See `PROVENANCE.md` (generated) and `sources.toml` for every citation (S19, catalogue
page 537).
