# hiwin.mg.rail-set: HIWIN MG miniature linear guide, rail with blocks

Ordering code in (`MGN12H2R300Z0C`), native SolidCraft design out: the MGNR rail with its counterbored holes and N MGN blocks, built
with SolidCraft's own commands, dimensions checked against HIWIN's published MG Series catalogue. Sizes 7, 9, 12, 15; block C or H.
Only the "rail with blocks" code is built; a lone block or rail code is not.

## Ordering code

```
MGN <size> <C|H> [E] <blocks> R <length> [E] [Z0|Z1|ZF] [C|H|P] [M|HC|NC] [I..IV] [+ options]
```

Examples: `MGN12H2R500Z0C` (size 12, long block H, 2 blocks, rail 500 mm, Z0 preload, normal accuracy C),
`MGN9C1R195ZFH`. Size 7, 9, 12, 15. Rail holes: `L = (n-1)P + 2E`, E <= P/2 (S4 p.85).

## Dimensioned and appearance-only

The model has two layers, split in the part description (DIMENSIONED / APPEARANCE), in the body names and in the check.

**Dimensioned** (catalogue values, every one checked): rail WR x HR, counterbored holes (D, h, d) at pitch P and end distance E, block
W, L1 (steel body), L (with end caps and seals), H, H1, the four M x depth threads at B x C, L Max (with the end screws), the lube hole Gn at
H2 below the block top (MGN7/9/12) or the grease nipple M3 / G (MGN15).

**Appearance** (approximate, not a catalogue dimension). Every such body is named `... (appearance, approximate)`; the rail features
are named the same way. They are listed under "Not guaranteed" in `PROVENANCE.md`:

- Rail top chamfers (0.025 x rail width) and the two side ball grooves (a circular approximation: the catalogue draws no groove profile)
- Block top chamfers and the 0.2 mm black top insert between the mounting holes
- End cap / end seal split of (L - L1) / 2, their 0.3 mm inset, colours (green cap, red seal as HIWIN's photo shows) and plastic material
- Retainer strips, the four cross-head end screws (only their projection (L Max - L) / 2 is catalogue) and the grease nipple shape (only M3 and G are catalogue)
- Rail screws: SolidCraft's ISO 4762 standard part of the catalogue bolt size (the screw model is SolidCraft's, not HIWIN's)
- Rail hole caps (option `caps`, MGN12 / MGN15): thickness 1.2 is catalogue, the diameter is the counterbore diameter (the catalogue O6.15 is a press fit)
- Materials and appearance looks of every body; the 10 mm gap between neighbouring blocks (illustration)

Colours and materials are SolidCraft appearance-library entries (`appearance.assign appearance=<id>`; per face through `faces`): ground faces (rail top and sides, block top and sides) `starter.metal.carbon-steel-polished` (roughness 0.16), the ball grooves and the block channel `starter.metal.silver-cool` (0.12), the satin body `Steel - Satin PBR` (0.4), end caps and seals `ABS - Green` / `ABS - Red` with their own pbr (no starter entry has these colours), top insert `starter.plastic.tpu-matte-black`, grease nipple `starter.metal.brass-champagne`, retainer strips `starter.metal.stainless-soft-satin`, black-oxide end screws and rail screws with their own pbr (no starter black-oxide). The check reads the finish back per face (`appearance.chain`, rows named "appearance: ..."). Stainless sets (M) use the soft satin stainless entry. Option `caps` (`tools/gen CODE --opt caps`, `caps=True` in the API, or
`SC_MGN_CAPS=1`): the catalogue's plastic bolt caps for MGN12 / MGN15 (Table 2-4-9: thickness 1.2, supplied with the rail; the model number has
no symbol for them), default off. Screenshots stand the rail on a base plate (shots only, in `src/shots.py`, never in the part).

## Checks

`src/check.py`: `check_mgn` is the original check on the dimensioned bodies, unchanged. `check_mgn_dimensioned` runs it on the full model after one
adjustment of the measurement it reads: appearance and screw bodies leave the body list, and a block's steel body takes the extent of steel body
+ end caps + end seals (the catalogue L). `check_mgn_appearance` adds rows (L1, L, L Max, Gn / G, H2, grooves, colours, materials, caps,
interference of all bodies = 0, description sections).

## Run

```
tools/gen MGN12H2R300Z0C                 # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/hiwin/mg/rail-set   # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/shots MGN12H2R300Z0C                      # English and German screenshots into shots/
tools/preview vendors/hiwin/mg/rail-set   # re-render preview.png
tools/provenance vendors/hiwin/mg/rail-set   # re-write PROVENANCE.md (never edit it by hand)
```

`SC_VER` (default 0.49.1) picks the SolidCraft release; `SC_CLI`, `SC_APP` or `SC_RELEASES` say where the binaries are.
Invalid codes stop with a message (`CodeError: ...`); valid options that are not drawn give `NotModelled`.

See `PROVENANCE.md` (generated) for where every number comes from and how it was verified, and `sources.toml` for the full citations.
