# misumi.hfs.extrusion: MISUMI aluminium extrusions, 5 series 2020 / 2040 / 4040 and 6 series 3030

Ordering code in (`HFS5-2020-497.5-TPW-LEV-REH`), native SolidCraft design out: the four-slot extrusion section extruded to the length, with end
tapping and wrench access holes. One engine draws all four profiles (5 series: NFS5, NFSB5, HFS5, HFSB5, CAF5, HFSY5; 6 series 3030: HFS6, HFSB6, CAF6,
HFSY6), so the 5 and 6 series are one generator with two `[[declares.matches]]`.

## Ordering code

```
[K]<type>5|6-<profile>-<length>[-<alteration>]...
```

5 series profiles 2020, 2040, 4040 and 6 series profile 3030 are drawn (sources.toml rows 45-75 of misumi.hfs.extrusion). Four-slot types of the 6 series drawn: `HFS6` `HFSB6`
`CAF6` `HFSY6`; the other 6 series types (`NEFS6`, `EFS6`, `GFS6`, `NFSL6`, `HFSL6`, the flat/three-slot variants...) are different sections and refused as not
modelled. `HFSY5` exists for 2020 only. End tapping `LTP`/`RTP`/`TPW`: 2020 one M5 hole per end, 2040 two, 4040 four (all M5 depth 15), 3030 one M8
depth 24 (S2 p.757). Wrench holes: 5 series H 10 / J 20 / K 20 d 7.35; 6 series H 15 / J 30 / K 30 and d 5 or 8, which the code must state: `-X5` or `-X8`
(`HFS6-3030-500-LCH-X5`, S3 p.759).

| Field | Allowed values | Source |
|-------|---------------|--------|
| `K` prefix | fixed-length extrusion; length must be 1000 or 4000 (effective length); no alterations | S1 p.529 |
| type | four-slot: `NFS5` `NFSB5` `HFS5` `HFSB5` `CAF5` `HFSY5`. Other 5 series types in the catalogue (`NFSF5` `HFSF5` `HFSFB5` three-side slot, `NFST5` `HFST5` `HFSTB5` two-side slots two flats, `HFSH5`, `HFSC5`, `HFSR5` curved) are recognised and refused as "not modelled" | S1 p.529-530 |
| `B` in type | black anodize (`HFSB5`, `NFSB5`) | S1 |
| profile | `2020`, `2040`, `4040` (drawn); other sizes (2525, 2060, 4080...) appear in the p.757 table and are refused until their drawing is read | S1 p.529-530, S2 p.757 |
| length | configurable: 50 to 4000 mm in 0.5 mm steps (6000 mm by special order, not accepted). Length tolerance L +-0.5; `SC` makes it +-0.2 for L <= 1500 | S1, S5 |
| `LTP` / `RTP` / `TPW` | end tapping left / right / both ends: M5 depth 15, one hole in the centre bore, HFS5-2020 | S2 p.757 |
| `LHP` / `RHP` / `HPW` | same with a heli-coil insert (M3 depth 6 for 2020). Parsed, refused as not modelled | S2 p.757 |
| wrench access hole `<L|R><C|W|E><H|V|P>` | L/R: left or right end; C/W/E: one, two or three holes in a line; H horizontal, V vertical, P crisscross. HFS5: first hole H = 10 from the end, then J = 20, K = 20; diameter 7.35. `P` is refused: the catalogue text does not say how a one-row crisscross is laid out | S3 p.759 |
| `FL` / `FR` | moves the wrench hole of that side 3 mm toward the end (end cap clearance); only valid with a wrench hole on that side | S3 p.760 |
| `FL`/`FR` caveat | S3 p.760 lists 6 and 8 series only; on the 5 series FL/FR is unverified, so the parser adds a note | S3 |
| `SC` | high precision cut, tolerance only | S5, S2 |
| `CW` | end face C chamfer; parsed, refused as not modelled | S5 p.756 |
| not accepted | `L_T45` / `R_T45` 45 degree cuts, `LSP/RSP/SPW` four-side-hole tapping, `LDH` D/S/M/L holes, `Z6/XA100`, `AH/BH/AV/BV`, `ZZZ` labelling: listed in S5 p.755-756, unsupported (clear error) | S5 |

Validation errors: bad shape, unknown type, profile or alteration, length out of range or off the 0.5 grid,
K with a length other than 1000/4000, duplicate options, FL/FR without a hole, holes that do not fit the length.
`CodeError` = invalid code; `NotModelled` (a subclass) = valid MISUMI code this prototype does not build.

## How the extrusion is built

A sketch of the cross-section on the YZ plane (one slot written out and rotated per side, then `sketch.fillet` for the outer corners and the lip tips,
plus the bores) and `solid.extrude` to the length, inside a `component.create` named by the code. Machining: `solid.cylinder` cut for each wrench access hole,
`solid.thread` M5 (cosmetic thread on the bore, length 15) for LTP / RTP / TPW. Part number, description and material go to `component.metadata.set` and the
design's `document.metadata.set`. Why not `frame.member`: it is a path-driven weldment member; a single catalogue length is a plain extrusion, and
`frame.member` stays the right choice once these parts are placed along a frame.

## Dimensioned and appearance-only

**Dimensioned**: overall size, slot mouth / cavity / lip / depth / core, corner radii, bores, end tapping (thread and depth), wrench access holes
(position H, J, K and diameter), length range and step, fixed lengths, the published section area and moments (as a check band: the outline built from the
drawing dimensions is within 0.3 % of the printed sectional area and within 1 % of the printed Ix / Iy for every profile, and the spec check says so, see "Section properties" below).

**Not guaranteed** (measured from the drawing, estimated, or a convention):

- Section values read from the vector drawing rather than printed: lip thickness on the 5 series, where the cavity wall ends and the floor half width (measured to 0.01 mm; on the 3030 the wall end 5.31 follows from the 45 degree flank closing on the printed numbers); the lip-tip round R0.3 (the pages show a tip round but do not size it)
- The central voids of the 2040 / 4040 (measured) and the 4040 bore-block inner-corner notch (3.6 mm square, fitted so that the section area meets the printed 472 mm2; the drawing shows 3.0 to 3.4): with them the section matches the printed area within 0.3 % and Ix / Iy within 1 % (sources.toml rows 1900-1904)
- Wrench access hole depth (through the whole section) and, on 2040 / 4040 / 3030, the H / V axis convention
- The cosmetic M5 / M8 end thread on the bore (its length and the effect of a wrench hole cutting the bore)
- FL / FR on the 5 series (the catalogue table lists the 6 and 8 series only)

Known gaps: only the 2014 FA catalogue pages were read. Other sizes and the other 3030 sections (NEFS6 / EFS6 296 mm2, light, GFS6) are refused until their
drawings are read. Wrench holes are drawn through the whole section; `P` (crisscross) is not built; with a wrench hole at 10 mm (H) the first M5 thread
segment ends at the hole, because the hole cuts the bore.

## Section properties against the printed table

The product tables under the drawings print mass per metre, sectional area and Ix / Iy (S22 p.529-530, S23 p.571; sources.toml rows 1900-1904). `check.py` compares
the built end-face area with the printed area within 0.3 % (never below half a unit of the last printed digit), the moments within 1 %, and the mass per metre
(area x 2.71 g/cm3, an aluminium alloy density the catalogue does not print) within half a unit of the printed digit. SolidCraft's inertia tensor gives the polar
moment Ix + Iy of a plain bar (checked against the sum of the printed ones); Ix and Iy separately are computed from the profile geometry, because the tensor of a
long bar is dominated by the A L^2 / 12 term.

| Profile | printed area, Ix, Iy | before: area, Ix, Iy | after: area, Ix, Iy |
|---|---|---|---|
| 2020 | 183, 7420, 7420 | 181.13 (-1.02 %), 7386, 7386 | 182.83 (-0.09 %), 7430, 7430 |
| 2040 | 324, 13580, 51300 | 321.20 (-0.86 %), 13480, 50934 | 323.75 (-0.08 %), 13551, 51344 |
| 4040 | 472, 88900, 88900 | 476.01 (+0.85 %), 88640, 88640 | 472.43 (+0.09 %), 88658, 88658 |
| 3030 | 333, 28300, 28300 | 331.97 (-0.31 %), 28391, 28391 | 333.14 (+0.04 %), 28453, 28453 |

What changed: the slot's cavity-wall end and floor half width are now the drawing's own values to 0.01 mm (2.93 / 2.93 instead of the rounded 3.0 / 3.0; 3030: 5.31 / 4.56
instead of 5.35 / 4.6), the 4040 bore-block notch is a fitted 3.6 mm instead of the 3.3 first read, and the moment calculation now includes the corner and lip-tip round-offs
(they are not small on the 3030: R2 at 14 mm from the axis).

## Tapped holes

The catalogue calls the bores of the profile the pilot holes of end tapping (S2 p.757). The convention here, the same as SolidCraft's own tapped hole (`solid.hole` with a thread
takes the tap drill): **the modelled hole is the printed pilot bore (O4.2 for M5, O6.8 for M8: the ISO tap drills), never the nominal thread diameter**; the thread is a cosmetic
`solid.thread` of the catalogue's nominal size and depth (M5 depth 15, M8 depth 24) on that bore, listed by `model.threads`. The check verifies the diameter of the cylinder that carries the thread
(sources.toml row 1905).

## Run

```
tools/gen HFS5-2020-120-LTP-RTP-LCH                 # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/misumi/hfs/extrusion   # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/shots HFS5-2020-120-LTP-RTP-LCH                      # English and German screenshots into shots/
tools/preview vendors/misumi/hfs/extrusion   # re-render preview.png
tools/provenance vendors/misumi/hfs/extrusion   # re-write PROVENANCE.md (never edit it by hand)
```

`SC_VER` (default 0.49.1) picks the SolidCraft release; `SC_CLI`, `SC_APP` or `SC_RELEASES` say where the binaries are.
Invalid codes stop with a message (`CodeError: ...`); valid options that are not drawn give `NotModelled`.

See `PROVENANCE.md` (generated) for where every number comes from and how it was verified, and `sources.toml` for the full citations.
