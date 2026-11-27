# misumi.sfj.shaft: MISUMI linear shafts (g7 / f8), plain, tapped at one or both ends, stepped

Ordering code in (`E-PSFJ6-20`, `E-SSFJ10-123.4-LKC-WSC12-X8`), native SolidCraft design out: a cylinder at its nominal diameter, optionally tapped at one
or both ends (T, C, Z, W types), stepped at one or both ends (PG, PH types), with wrench flats (SC / WSC / SX) and flat surfaces (FC / WFC / LFC).
Types E-SFJ, E-SSFJ, E-PSFJ, E-PSSFJ (g7) and E-PSFG (f8) and their variants.

## Which catalogue the codes follow

These codes are **MISUMI Economy Series (E- prefix)** codes, as printed in the MISUMI Economy Series catalogue 2025 (ASEAN edition, th.c.misumi-ec.com). The E- series is sold on MISUMI's Asian regional sites (for example Thailand, Singapore, Malaysia, Vietnam, Indonesia). These codes may not be sold in every region: they are not found on the US site (us.misumi-ec.com). The US catalogue lists the standard (non-Economy) linear shafts instead, ordered without the E- prefix (SFJ, SSFJ, PSFJ, PSSFJ, PSFG, ...). The standard parts can differ from the Economy ones (the US catalogue pages found give g6 for the SFJ / PSFJ family where the Economy catalogue prints g7, and plating thickness and material choices are not the same), so do not assume a US part matches this generator's dimensions; check the US catalogue page before ordering. This generator does not cover the standard series.

## Ordering code

```
<type><D>-<L>[-LKC][-SC<n> | -WSC<n>-X<m>][-FC<l>-A<a>|E<e> | -WFC<l>-A<a>-E<e>]
<type>T<D>-<L>-M<thread>[-alterations]                one end tapped                                 p.433
<type>C<D>-<L>-M<m>-SC<n>[-alterations]               one end tapped, wrench slot (SC mandatory)    p.434   (+ SX<n>)
<type>Z<D>-<L>-M<m>-N<n>-(SC<n> | WSC<n>-X<m>)[...]   both ends tapped, wrench flat                   p.435
<type>W<D>-<L>-M<m>-N<n>[-alterations]                both ends tapped                               p.436
<pgtype><D>-<L>-F<f>-P<p>-(M<m> | MD<m>)-SC<n>[...]   one end stepped and tapped (types E-SFPG ...)   p.437   (+ SX, LFC<l>-A<a>, MD)
<phtype><D>-<L>-F<f>-P<p>-M<m>-T<t>-SC<n>             both ends stepped and tapped (E-SFPH ..., E-PFPGH)  p.438
type: E-SFJ  E-SSFJ  E-PSFJ  E-PSSFJ (g7)   E-PSFG (f8); the T / C / Z / W variants append the letter to the type (E-PSFJZ6, E-PSFGW16)
```

Examples: `E-PSFJ6-20` (the catalogue's own), `E-PSFJT6-30-M3`, `E-SFJ20-300-SC5`, `E-PSFG16-250-FC20-A10`, `E-SSFJ10-123.4-LKC-WSC12-X8`, `E-PSSFJ30-200-WFC40-A10-E20`.
New on p.434-438: `E-PSFJC6-40-M3-SC0`, `E-PSFJZ6-50-M3-N3-SC0`, `E-PSFJW6-50-M3-N3`, `E-PSFPG8-200-F4-P6-M3-SC0` (the catalogue's own examples),
`E-PSFPH8-200-F5-P6-M3-T5-SC0`, `E-PSSFPG20-500-F10-P12-M8-SC20-SX15-FC30-E50-LFC6-A2`.
In the stepped types L is the length of the main body; the step of length F (and T) lies beyond its ends, so the overall length (Y) is F + L (+ T) and is limited per D.
D in 3, 4, 5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30, 35, 40, 50; length range per diameter from the table; 1 mm steps (0.1 mm with LKC). The tolerance class comes from the type (g7 or f8) and is
written into the part description. Refused with a message (besides the above, per family): a missing mandatory SC (C, PG, PH), M x 2 + N x 2 above L (Z, W), P outside its range, F or T outside 2 to P x 4, overall length (Y) above the maximum, LKC with D - P <= 2, SX on the Z type, D35-50 on a type other than E-PSFJ; a length or thread outside the table, D3/4/5 or D35-50 on E-PSFG, SC with WSC, FC with WFC, flats closer than 2 mm to each other or to the tap, wrench flats on D < 6.

## Dimensioned and appearance-only

**Dimensioned**: diameter and its tolerance class (g7 / f8 limits per diameter), length range per diameter, 1 mm steps (0.1 mm with LKC and its tolerance),
taps at one or both ends (thread per diameter, depth M x 2; MD: M x 3), steps (F, P, T, overall length (Y)), second wrench-flat set SX, set screw flat LFC on the step, wrench-flat width and length, flat-surface depth.

**Not guaranteed**:

- The shaft is a plain cylinder at its nominal diameter: no end chamfer is drawn (the catalogue gives none)
- Which end is tapped (the figure shows the left end; the text does not say)
- The orientation of the second flat of WSC / WFC (turned 90 degrees)
- The orientation of the second wrench flat set SX (turned 90 degrees)
- The diameter tolerance of the step P (g7 is printed but no limits are given): the step is drawn at its nominal diameter
- The datum of FC / WFC / LFC / SC positions on a stepped shaft (taken from the shoulder of the main body, as in the figures)
- Chamfers at the shaft ends (drawn in the p.436 figure but not dimensioned)
- WSC is read as the alternative to SC on the both-ends-tapped wrench-flat type

## Run

```
tools/gen E-PSFJ6-20                 # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/misumi/sfj/shaft   # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/shots E-PSFJ6-20                      # English and German screenshots into shots/
tools/preview vendors/misumi/sfj/shaft   # re-render preview.png
tools/provenance vendors/misumi/sfj/shaft   # re-write PROVENANCE.md (never edit it by hand)
```

`SC_VER` (default 0.49.1) picks the SolidCraft release; `SC_CLI`, `SC_APP` or `SC_RELEASES` say where the binaries are.
Invalid codes stop with a message (`CodeError: ...`); valid options that are not drawn give `NotModelled`.

See `PROVENANCE.md` (generated) for where every number comes from and how it was verified, and `sources.toml` for the full citations.
