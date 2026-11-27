# misumi.sth.pilot-flanged-shaft-support: MISUMI Economy pilot flanged shaft supports

Ordering code in (`E-STHWIRB8`, `E-STHWICB30`), native SolidCraft design out: a flanged shaft support with a pilot spigot, its shaft bore (H8),
the four flange mounting holes, the clamp groove, the radial slit and the clamp screw. The pilot is machined to locate in an H8 hole of the
fixing plate. It holds the linear shafts of `misumi.sfj.shaft`; the same flange without the pilot is in `misumi.sth.flanged-shaft-support`.

## Ordering code

```
<type><D>
round flanged    E-STHWIRB<D>      compact flanged  E-STHWICB<D>      (S18 p.540)
```

D is the shaft bore diameter (H8): 8, 10, 12, 15, 16, 20, 25, 30 or 40. Examples: `E-STHWIRB8` (the catalogue's own), `E-STHWIRB40`, `E-STHWICB16`.

Refused with a message: a D that is not in the table, a missing D, a type that is not in the catalogue (a square, a long sleeve or the slit type
`E-STHWRB`).

## Dimensioned and appearance-only

**Dimensioned**: bore D and its H8 tolerance (written into the description), pilot and sleeve outside diameter D1 and overall length L1, pilot length
and flange thickness T, flange H (round diameter or compact length) and W, the mounting holes d on P (round) or on F by P1 (compact), the groove
(S1 wide, B + S1 from the sleeve end), the slit S, and the clamp screw M at X above the axis with its clearance hole d2, counterbore d1 (floor Y from
the slit centre) and tapped hole. Thickness (N) is the sleeve wall (D1 - D) / 2, checked in every row.

**Not guaranteed**: see `generator.toml` (`[guarantee]`): the compact flange corner radii, the groove depth and the slit stub, the side of the clamp
screw, the hole angle of the round flange, the reading of the two T dimensions as pilot length and flange thickness, chamfers, the supplied screw,
surface treatment, and that both types are built for every D.

## Run

```
tools/gen E-STHWIRB12                          # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/misumi/sth/pilot-flanged-shaft-support   # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/shots E-STHWIRB12                        # English and German screenshots into shots/
tools/preview vendors/misumi/sth/pilot-flanged-shaft-support
tools/provenance vendors/misumi/sth/pilot-flanged-shaft-support   # re-write PROVENANCE.md (never edit it by hand)
```

Invalid codes stop with a message (`CodeError: ...`). See `PROVENANCE.md` (generated) and `sources.toml` for every citation (S18, catalogue
page 540).
