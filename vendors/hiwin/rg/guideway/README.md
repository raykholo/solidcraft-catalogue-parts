# hiwin.rg.guideway: HIWIN RG high-rigidity roller type linear guideway

One generator for the three kinds of RG code, because they share one table set and one engine (the same engine as `hiwin.hg.guideway` and `hiwin.eg.guideway`): a rail with blocks
(`RGH20CA2R1000ZAH`, `RGW25CC2R640ZAH`), a block alone (`RGW45CC`, `RGH20CA`) and a rail alone (`RGR15R160`, `RGR25R640`). The folder holds all three; each
has its own `[[declares.matches]]` in `generator.toml`. Built as catalogue envelopes (block: steel body L1 plus end caps and seals to L) with the exact mounting
holes (rail counterbored from the top; block tapped from the top, six holes).

## Ordering code

```
set    RG<H|W><size><C|H><A|C>[E]<blocks>R<length>[E][Z0|ZA|ZB][H|P|SP|UP][I..IV][+ options]
rail   RGR<size>R<length>[E][H|P][+ options]
block  RG<H|W><size><C|H><A|C>[E][Z0|ZA][H|P][+ options]
```

Examples: `RGH20CA2R1000ZAH` (size 20, heavy load square block, mounted from the top, 2 blocks, rail 1000 mm from the top, preload ZA, accuracy H),
`RGW25CC2R640ZAH` (flange block), `RGH45HA1R885ZBSP` (super heavy load, preload ZB, super precision), `RGR30R1000`. Sizes 15, 20, 25, 30, 35, 45, 55, 65. The load letter is C
(heavy) or H (super heavy); the RG15 tables have the heavy load C block only. RGH is mounted from the top (A), RGW has mounting code C (top or bottom), as the table
row names print (RGH-CA / RGH-HA, RGW-CC / RGW-HC). Rail: `L = (n-1)P + 2E`, length 100 to 4000 mm. Options after `+`: the dust-protection codes `ZZ`, `DD` and `KK` give the
block length L of Table 2-9-22 (p.161); `E2` and `RC` are parsed and not drawn.

Refused with a message: bottom-mounted rails (`T`, the catalogue prints no tapped-hole dimensions), RGL / RGS / RGF blocks (valid grammar, tables not drawn), ZB or accuracy
SP / UP on an interchangeable block or rail, accuracy C (does not exist for RG), a trailing `M` (the RG model number has no stainless option), blocks that do not fit the rail, rail lengths
whose end distance is outside the printed bounds.

## Dimensioned and appearance-only

**Dimensioned** (catalogue values, checked): rail WR, HR, D, h, d, P, E and mounting bolt; block H, H1, N, W, B, C (and C1 on the flange block), L1, L (with the dust-code lengths),
mounting thread M x depth (RGH: l of Mxl, RGW: T), hole count (6) and positions; the rail end-distance rule L = (n-1)P + 2E; length limits.

**Not guaranteed** (shown for looks or as an illustration choice, not checked against a catalogue dimension):

- The whole body shape: rails and blocks are the catalogue envelopes (WR x HR rail; W x L1 x (H - H1) block body with the rail channel cut out, end caps and seals to L); the roller tracks and the flange outline are not published as dimensions
- RGW mounting holes are tapped to the depth T (T and T1 are printed without a definition; the mounting code C means top or bottom, so the real holes may run through the flange), and the two rail-axis holes of both block types (legend 6-Mxl / 6-M) take the same thread depth as the flank holes
- The 10 mm gap between neighbouring blocks (illustration)
- Rail top chamfers (0.02 x rail width), one circular roller track per rail side, block top chamfers (0.02 x block width): appearance features named `... (appearance, approximate)`
- End cap / end seal split of (L - L1) / 2 (seal 25 percent, 0.5 mm inset), their black plastic, and the brass grease nipple on the +X end of each block (shape and size are estimates)
- Rail screws: SolidCraft's ISO 4762 standard part of the catalogue bolt size, black oxide
- Materials and PBR looks of every body as SolidCraft appearance-library entries (ground top and side faces, raceway faces, satin body, plastics, brass; black-oxide screws carry their own pbr); the check reads the finish back per face with `appearance.chain`
- E2 and RC options after `+` (parsed, not drawn), accuracy, preload and special E blocks / rails (recorded in the code only)

## Interpretation notes for the reviewer

- Six mounting holes for every block: the drawings print the legend `6-Mxl` (RGH) and `6-M` (RGW). RGH: two columns C apart times three rows (flank rows B apart, one row on the rail axis, aligned with the flank holes). RGW: four flange holes at C x B plus two holes on the rail axis C1 apart. One legend serves the short and the long block of a table, so the long HA / HC block also gets six holes.
- RGW: T and T1 of the flange table are printed without a definition; T is used as the tapped depth, as for the EG and HG flange blocks. The mounting code C (top or bottom) suggests through-tapped flange holes; that is not drawn.
- End distance: the text of 2-9-12 (p.165) says E no greater than P/2 for non-standard lengths; Table 2-9-29 prints Es = 20 for RGR15 / 20 / 25 (P = 30, so P/2 = 15) and the standard lengths 160, 220, 340 ... all use E = 20. So the allowed E is the standard Es exactly, or E <= P/2; the smallest E is not printed and is taken as Es (P/2 when Es > P/2), as in the HG and EG generators. RGR15 / 20 / 25 therefore take E = 15 or E = 20 only; RGR30 / 35 / 45 / 55 only the standard E; RGR65 35 to 37.5.
- The 100 mm lower end of the "100 ~ 4000" rail length column (Table 2-9-2) is the minimum rail length.
- RGH15HA and RGW15HC are refused because the tables have no such row (absent rows, not "-" cells); ZB preload is accepted for every size (Table 2-9-14 prints ZB stiffness for RG15C too).
- Dust protection: the unparenthesised block lengths of Table 2-9-22 are used; the SS column equals the L column of the dimension tables, so no symbol is the standard block.
- Only RGH and RGW are drawn; RGL, RGS and RGF (tables on p.167, 169, 170) are valid grammar and refused as not modelled.

## Run

```
tools/gen RGH20CA2R1000ZAH                 # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/hiwin/rg/guideway      # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/preview vendors/hiwin/rg/guideway    # re-render preview.png
tools/provenance vendors/hiwin/rg/guideway # re-write PROVENANCE.md (never edit it by hand)
```

`SC_VER` (default 0.50.0) picks the SolidCraft release. Invalid codes stop with a message (`CodeError: ...`); valid options that are not drawn give `NotModelled`.

See `PROVENANCE.md` (generated) for where every number comes from and how it was verified, and `sources.toml` for the full citations.
