# misumi.ofb.oil-free-bushing: MISUMI Economy oil free bushings, copper alloy and special brass

Ordering code in (`C-MUFZ5-10`, `E-SHTZ25-35`), native SolidCraft design out: the bushing body (outside diameter, plain bore at the nominal
inner diameter, overall length), the shoulder or flange, and the counterbored mounting holes of the flanged types. Catalogue pages p.514 to
p.516 and p.519 to p.520 (printed 04-129 to 04-131, 04-134, 04-135; page images `files/mobile/514.jpg` ... `520.jpg`).

## Ordering code

```
<type><d>-<L>        d = inner diameter (I.D.), L = overall length, both in mm
type:   C-MUBZ   C-MUBZU    straight, standard / thin wall                 copper alloy   d 5-100   (p.514)
        C-MUFZ   C-MUFZU    shouldered, standard / thin wall               copper alloy   d 5-100   (p.514)
        C-MUTZ   C-MUTSZ  C-MUTNZ   round / square / compact flanged     copper alloy   d 6-50    (p.515)
        E-MUGZ              thrust type (plain flange)                     copper alloy   d 6-50    (p.516)
        E-SHBZ   E-SHFZ     special brass straight / shouldered            d 5-30                   (p.519)
        E-SHTZ   E-SHTNZ    special brass round / compact flanged          d 6-30                   (p.520)
```

The offered d and L differ per type and are read from the printed table: a bracketed L is offered for the standard wall type only (straight,
shouldered) or for the round and compact flanges only (flanged), an L with `*` for the thin wall type only. Examples: `C-MUFZ5-10`,
`C-MUTNZ6-15`, `E-SHBZ10-12`, `E-SHFZ8-10`, `E-SHTZ25-35`, `E-SHTNZ10-25` and `E-MUGZ10-15` (the catalogue's own ordering examples),
`C-MUBZU35-15`, `C-MUTSZ16-40`. Refused with a message: a bore size not offered for that type, an L not printed for that bore (with a note when the
L belongs to the other wall type or to the round and compact flanges), the thin wall type for a bore without thin wall, and the pages this
generator does not cover (E-MUSZ, E-MUKZ, centre and pilot flanged, resin types).

## Dimensioned and appearance-only

**Dimensioned**: O.D. D, bore d, overall length L (flange included, measured from the outer flange face), wall N (derived check), shoulder or
thrust flange H and t, flange H / T, hole d1, counterbore d2 and depth t, P.C.D., square flange W across flats, compact flange width D + 6 and
hole pitches A and F. Tolerances (bore F7 / E7 values, O.D. class m6 / r6 / h7, L -0.1 / -0.3, T, thrust t) are written into the part description.

**Not guaranteed** (the same list as `generator.toml`):

- Solid lubricant plugs (graphite / lubricant inserts) and any lubricating grooves (appearance, approximate): not drawn, no dimensions printed
- Chamfers and edge breaks (appearance, approximate): not drawn
- The bore is a plain cylinder at the nominal d; tolerance classes are described, not drawn
- The rotation stopper screw, housing diameter and the applicable cap screws (reference / not provided) are not drawn
- Which flange face carries the counterbores: the outer face away from the barrel (read from the p.515 section figure)
- Hole layout and flange outlines: round 2 holes (d 6-13) or 4 (d 16 up) on the axes; square flange standing on its corner clipped by the circle H;
  compact flange as the circle H clipped by two flats D + 6 apart (figure reading)
- Not generated: E-MUSZ / E-MUKZ (p.516), centre and pilot flanged types (p.517), resin bushings (p.521-p.523), bushing housing units (p.524 on)

## Run

```
tools/gen C-MUTNZ16-30                                  # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/misumi/ofb/oil-free-bushing         # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/preview vendors/misumi/ofb/oil-free-bushing       # re-render preview.png
tools/provenance vendors/misumi/ofb/oil-free-bushing    # re-write PROVENANCE.md (never edit it by hand)
```

`SC_VER` picks the SolidCraft release. Invalid codes stop with a message (`CodeError: ...`). See `PROVENANCE.md` (generated) and `sources.toml`.
