# hiwin.hg.guideway: HIWIN HG heavy-load linear guideway

One generator for the three kinds of HG code, because they share one table set and one engine: a rail with blocks (`HGH20CA2R1000ZAH`,
`HGW25CC1R640ZAP`), a block alone (`HGW45CB`) and a rail alone (`HGR15R160M`, `HGR25T640`). The folder holds all three; each has its own
`[[declares.matches]]` in `generator.toml`. Built as catalogue envelopes (block: steel body L1 plus end caps and seals to L) with the exact mounting holes (rail counterbore from the top or tapped
from the bottom; block tapped from the top or through holes).

## Ordering code

```
set    HG<H|W><size><C|H><A|B|C>[E]<blocks>R|T<length>[E][Z0|ZA|ZB][C|H|P|SP|UP][M][I..IV][+ options]
rail   HGR<size>R|T<length>[E][C|H|P|SP|UP][M]
block  HG<H|W><size><C|H><A|B|C>[E][Z0|ZA][C|H|P][M]
```

Examples: `HGH20CA2R1000ZAH` (size 20, heavy load square block, mounted from the top, 2 blocks, rail 1000 mm from the top, preload ZA, accuracy H),
`HGW25CC1R640ZAP`, `HGR25T640` (rail mounted from the bottom), `HGW45CB`. Sizes 15, 20, 25, 30, 35, 45, 55, 65. HGH is A only; HG15 has the C (heavy) block only;
HGW-CB drills O through holes, CA/CC tap M from the top. Rail: `L = (n-1)P + 2E`, Es <= E <= P/2, maximum 4000 mm (stainless M, HG15/20/25 only: 2000). `HGL` (low) and
other options after `+` are parsed or refused as not modelled; blocks that do not fit the rail are refused.

## Dimensioned and appearance-only

**Dimensioned** (catalogue values, checked): rail WR, HR, D, h, d, P, E and mounting bolt (HGR-R) or tapped hole S x hT (HGR-T); block H, H1, N, W,
B, C, L1, L, mounting thread M x depth (HGH, HGW-CA / CC) or through-hole diameter (HGW-CB); the rail end-distance rule L = (n-1)P + 2E; length limits.

**Not guaranteed** (shown for looks or as an illustration choice, not checked against a catalogue dimension):

- The whole body shape: rails and blocks are the catalogue envelopes (WR x HR rail; W x L x (H - H1) block with the rail channel cut out); the ball grooves and the flange outline are not published as dimensions
- HGW-CB through holes are drilled through the whole envelope height (the flange thickness is not published)
- The 10 mm gap between neighbouring blocks (illustration)
- Rail top chamfers (0.02 x rail width), one circular ball groove per rail side, block top chamfers (0.02 x block width): appearance features named `... (appearance, approximate)`
- End cap / end seal split of (L - L1) / 2 (seal 25 percent, 0.5 mm inset), their black plastic, and the brass grease nipple on the +X end of each block (shape and size are estimates)
- Rail screws (HGR-R): SolidCraft's ISO 4762 standard part of the catalogue bolt size, black oxide
- Materials and PBR looks of every body as SolidCraft appearance-library entries (ground top and side faces `starter.metal.carbon-steel-polished`, raceway faces `starter.metal.silver-cool`, satin body `Steel - Satin PBR`, end caps `starter.plastic.abs-charcoal`, end seals `starter.plastic.tpu-matte-black`, grease nipple `starter.metal.brass-champagne`; black-oxide screws carry their own pbr); the check reads the finish back per face with `appearance.chain`

## Run

```
tools/gen HGH20CA2R1000ZAH                 # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/hiwin/hg/guideway   # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/shots HGH20CA2R1000ZAH                      # English and German screenshots into shots/
tools/preview vendors/hiwin/hg/guideway   # re-render preview.png
tools/provenance vendors/hiwin/hg/guideway   # re-write PROVENANCE.md (never edit it by hand)
```

`SC_VER` (default 0.50.0) picks the SolidCraft release; `SC_CLI`, `SC_APP` or `SC_RELEASES` say where the binaries are.
Invalid codes stop with a message (`CodeError: ...`); valid options that are not drawn give `NotModelled`.

See `PROVENANCE.md` (generated) for where every number comes from and how it was verified, and `sources.toml` for the full citations.
