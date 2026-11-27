# hiwin.eg.guideway: HIWIN EG low-profile linear guideway

One generator for the three kinds of EG code, because they share one table set and one engine (the same engine as `hiwin.hg.guideway`): a rail with blocks
(`EGH20CA2R1000ZAH`, `EGW25CA2R640ZAP`), a block alone (`EGW35CA`, `EGH20SA`) and a rail alone (`EGR15R160`, `EGR25R640`). The folder holds all three; each
has its own `[[declares.matches]]` in `generator.toml`. Built as catalogue envelopes (block: steel body L1 plus end caps and seals to L) with the exact mounting
holes (rail counterbored from the top; block tapped from the top or through holes).

## Ordering code

```
set    EG<H|W><size><C|S><A|B>[E]<blocks>R|U<length>[E][Z0|ZA|ZB][C|H|P|SP|UP][M][I..IV][+ options]
rail   EGR<size>R|U<length>[E][C|H|P|SP|UP][M]
block  EG<H|W><size><C|S><A|B>[E][Z0|ZA][C|H|P][M]
```

Examples: `EGH20CA2R1000ZAH` (size 20, heavy load long square block, mounted from the top, 2 blocks, rail 1000 mm from the top, preload ZA, accuracy H),
`EGW25CA2R640ZAP`, `EGW25SB1R340` (medium load short flange block, through holes), `EGR30R1000`. Sizes 15, 20, 25, 30, 35. The load letter is C (heavy, long block, four
holes) or S (medium, short block, two holes). EGH is mounted from the top only (A); EGW-A is tapped from the top, EGW-B has through holes. Rail: `L = (n-1)P + 2E`,
Es <= E <= P/2, length 100 to 4000 mm (stainless M, EG15C and EGR15 only: 2000).

Refused with a message: bottom-mounted rails (`T`, the catalogue prints no tapped-hole dimensions), dust-protection options `ZZ`, `DD`, `KK` (they change the block
length, p.53), stainless outside EG15, blocks that do not fit the rail. Other options after `+` are parsed and not drawn.

## Dimensioned and appearance-only

**Dimensioned** (catalogue values, checked): rail WR, HR, D, h, d, P, E and mounting bolt; block H, H1, N, W, B, C (long blocks), L1, L, mounting thread M x depth (EGH: l of
Mxl, EGW-A: T) or through-hole diameter (EGW-B), hole count (2 or 4); the rail end-distance rule L = (n-1)P + 2E; length limits.

**Not guaranteed** (shown for looks or as an illustration choice, not checked against a catalogue dimension):

- The whole body shape: rails and blocks are the catalogue envelopes (WR x HR rail; W x L1 x (H - H1) block body with the rail channel cut out, end caps and seals to L); the ball grooves and the flange outline are not published as dimensions
- EGW-B through holes are drilled through the whole envelope height (the flange thickness is not published as a drilling depth)
- The 10 mm gap between neighbouring blocks (illustration)
- Rail top chamfers (0.02 x rail width), one circular ball groove per rail side, block top chamfers (0.02 x block width): appearance features named `... (appearance, approximate)`
- End cap / end seal split of (L - L1) / 2 (seal 25 percent, 0.5 mm inset), their black plastic, and the brass grease nipple on the +X end of each block (shape and size are estimates)
- Rail screws: SolidCraft's ISO 4762 standard part of the catalogue bolt size, black oxide
- Materials and PBR looks of every body as SolidCraft appearance-library entries (ground top and side faces, raceway faces, satin body, plastics, brass; black-oxide screws carry their own pbr); the check reads the finish back per face with `appearance.chain`

## Interpretation notes for the reviewer

- C is printed "-" for the short S blocks, whose drawings show `2-MxL` / `2-M`; the two holes are placed on the block centre line at B apart.
- `U` is printed next to `R` as "Mounting from top" in the model number block and is treated as the same top-mounted rail.
- ZB preload is accepted for EG15: Table 2-2-9 prints ZB stiffness for EG15S / EG15C; the "-" in the EG15 ZB column of Tables 2-2-18 / 2-2-19 only means no tolerance value.
- The 100 mm lower end of the "100 ~ 4000" rail length column (Table 2-2-1) is the minimum rail length.
- T and T1 of the flange tables are printed without a definition; T is used as the tapped depth of EGW-A, as for the HG flange blocks.

## Run

```
tools/gen EGH20CA2R1000ZAH                 # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/hiwin/eg/guideway      # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/preview vendors/hiwin/eg/guideway    # re-render preview.png
tools/provenance vendors/hiwin/eg/guideway # re-write PROVENANCE.md (never edit it by hand)
```

`SC_VER` (default 0.50.0) picks the SolidCraft release. Invalid codes stop with a message (`CodeError: ...`); valid options that are not drawn give `NotModelled`.

See `PROVENANCE.md` (generated) for where every number comes from and how it was verified, and `sources.toml` for the full citations.
