# misumi.sth.flanged-shaft-support as a parametric SolidCraft generator

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai, and rules addressed by feature name requires the #23175 surface (unavailable on 0.50.0/0.51.1). The exact command errors quoted below are observations from SolidCraft 0.50.0. On capable hosts, link overrides and ordinary source `parameters.change` enforce limit rules marked `enforce_on_edit`.

The support modelled ONCE in SolidCraft (`flanged-shaft-support/flanged-shaft-support.sc`), a configuration table of the catalogue rows, the
ordering code as field templates and the logic as plain Rhai, following SolidCraft's generator interface (`docs/formats/generator.md`,
version 2, issue 22331). The Python generator in `../src` is untouched and is the reference every code below is compared with.

```
flanged-shaft-support/                 the package layout of the interface document
  generator.toml               [[template]] x2, [rows."<row>"] source / page / status per configuration row
  flanged-shaft-support.sc    the parametric model + its configuration table (built by build.py)
  generator.rhai               resolve(fields) -> #{configuration, parameters, properties}; no_match(raw)
  tables/*.csv                 copies of ../data/*.csv (first column = the key `table()` reads) and params.csv (message texts, size lists)
build.py                       builds the model with solidcraft-cli (runtime/parametric/build.py), writes the tables and generator.toml
run_codes.py                   the end-to-end proof (runtime/parametric/harness.py): results.json and faithfulness.json
ci.sh OUTDIR                   what the `parametric` workflow runs: build.py, run_codes.py, then tools/parametric-verdict reads faithfulness.json
../../../../runtime/parametric/build.py     shared with the other STH generators: units, configuration rows, two-stage build (rules name features by id)
../../../../runtime/parametric/harness.py   shared with the other STH generators: every code both ways, the spec check on both parts
../../../../runtime/fieldtemplate.py        stand-in for the field-template parser and printer (doc section 3), shared with the HIWIN MG and HFS proofs
../../../../runtime/rhai-run/               stand-in host for generator.rhai (the real Rhai engine, the documented sandbox limits)
```


## How the model is built (all of it worked on SolidCraft 0.50.0)

One model for all five series and their long sleeve types: standard sleeve (E-STHRB .. E-SSTHC, ...L), thickened (E-STHRBN .. E-STHCNL), end
mounting (E-STHXRB .. E-STHXC), flanged with slit (E-STHWRB .. E-SSTHWCL) and the compact clamp collar (E-STHMRB .. E-STHMRL).

- **30 user parameters, 6 derived.** Every dimension of a row is a parameter cell (`bore body_d fl_d fl_t len mh_d mh_h pcd sq_k cw cp1 cf
  x_l1 x_l x_d1 x_d2 mr_cb ss_z1 ss_z2 cl_b cl_g0 cl_s1 cl_slit cl_x cl_y cl_clear cl_cb cl_z1 cl_z2`), a number or an expression over the other parameters
  (`cl_z1 = len - cl_b / 2`, `cl_g0 = len - cl_b - cl_s1`, `ss_z2 = 2 * ss_z1`, `mh_h = fl_t + 2` or `len + 2`); derived: the sleeve wall (the set screw
  hole depth), the clamp radius and the point `cl_xo` where the clamp axis meets the outside, the ring start, the square flange's corner flats.
- **The body is the sleeve cylinder** `body_d x len` (for E-STHMR the collar body, `body_d = H`), drawn first and named `Body`; the flange joins it.
- **Three flange sketches, one feature each** (S4 of the analysis): `Flange round` (circle `fl_d`), `Flange square` (the eight points of the cut-corner square,
  `sq_t = fl_d / 2` and `sq_e = sq_k / sqrt(2) - fl_d / 2`) and `Flange compact` (rectangle `cw x fl_d`, rounds of `0.25 * cw`), each a sketch and an extrude
  `fl_t`; a row suppresses the two it does not use (and all three for the collar).
- **Bore, mounting holes.** `Shaft hole` (through) or `Shaft hole blind` + `Mounting screw hole` + `Mounting screw counterbore` (end mounting); the
  mounting holes are `Round 1..4` (round and square flange, and the collar's two: 1 and 3, height `len + 2`), `Compact4 1..4` (F x P1) or `Compact2 1..2`
  (no F: two holes on the Y axis), plus the collar's two counterbores (`Collar counterbore 1..2`).
- **Set screws** (standard and thickened): 5 sizes x 2 stations x 2 screws (+X and +Y) = 20 `solid.hole` features, one per size, station and
  screw, at `z = ss_z1 / ss_z2`, depth `wall`; a row keeps the 2 or 4 of its size.
- **Clamp** (slit and collar types): `Groove`, `Slit`, and per screw (1, 2 on the slit long sleeve, at B/4 and 3B/4) a clearance hole, a counterbore
  and one thread feature per size (M4 M5 M6 M8 M10).
- **Configuration table = the catalogue rows.** 177 rows, one per geometry, named `<series>-<shape>-[long-]<D>` (`std-round-6`, `slit-compact-long-50`,
  `mr-collar-12`): the 59 dimension rows of the six CSVs x the shapes and sleeves that exist for them. The types that differ only in surface or material
  (E-STHRB, E-STHR, E-SSTHC ...) share a row. Source, page and status of every row are in `generator.toml` `[rows."std-round-6"]` ... Three
  limits that are the Python generator's, not the table's, stay in Rhai: the sizes a type is not sold in (`not_applicable_d`), the sizes without a long
  sleeve (`L1` empty), the type names.

## The ordering code

`generator.toml` has two templates. The structured one is
`E-[S:stainless]STH[{series: X=xend, W=slit, M=mr}]{shape: R=round, S=square, C=compact}[B:black][N:thick][L:long]{d: text 1..6 [0-9]}`: the six
families of the analysis as fields (series letter, shape, black oxide, thickened, long sleeve), which the printer writes back; the second
(`E-{type: text 1..12 [A-Za-z]}{d: text 1..6 [0-9]}`) hands every other type text to Rhai. `generator.rhai` does what `support.parse` does, with its
messages word for word: the unknown type (`'E-STHSBN10': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR ...`), D outside the
table of that series (`... hole diameter D must be one of [6, 8, ...] (p.534-535)`), the long sleeve that exists for the D marked * only, the sizes a
type is not sold in (`E-STHR is not applicable when D = 15 (p.535 note)`), a code that matches no template (`fn no_match(raw)`). It returns the row and the
component's properties (part number, the description, which is the Python text word for word, material, surface).

## What was run

For every line of `../codes.txt` (177 valid codes (the 50 of codes.txt and a sweep of one code for every other configuration row, so that all 177 rows are built and compared), 23 rejected codes of the file plus 12 extra refusals): code -> field template -> Rhai `resolve` ->
a configuration row of the package model -> a host design inserts the model with `component.insert_design {{configuration}}` -> `inspect.measure`
(volume, area, bbox, faces, bodies) + the unchanged `src/check.py` spec check (run on the inserted part, on a `Support` rebuilt from the Rhai
result and the package tables, never from the Python parser; its `description` is the text Rhai made, and one extra row of both spec checks
requires it to equal the Python description) -> the same code built by the Python generator and measured and checked the same way.
`tools/parametric-verdict` decides equality (volume and area within 1e-6 relative, the same bbox, faces and bodies, the same number of
passed spec rows, the same refusal message).

```
# on a build host (solidcraft-cli 0.50.0 and the Rhai host built from runtime/rhai-run), in the repository root:
export SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run binary>
bash vendors/misumi/sth/flanged-shaft-support/parametric/ci.sh OUT          # builds the model, runs every code both ways, writes OUT/results.json and OUT/faithfulness.json
tools/parametric-verdict OUT/faithfulness.json
python3 runtime/parametric/harness.py report OUT/results.json     # the tables below
```

## Result: side by side

Volume mm3 / area mm2 / bbox mm / faces. Equal = same bodies, volume and area within 1e-6 relative, same bbox and face count; the spec check
columns are passed rows / rows.

| code | row | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec check python | spec check parametric | equal |
|---|---|---|---|---|---|---|
| E-STHRB6 | std-round-6 | 2867.2 / 2304.4 / 28x28x15 / 12 | 2867.2 / 2304.4 / 28x28x15 / 12 | 20/20 | 20/20 | yes |
| E-STHRB12 | std-round-12 | 6595.9 / 4517.4 / 36x36x24 / 12 | 6595.9 / 4517.4 / 36x36x24 / 12 | 20/20 | 20/20 | yes |
| E-STHR20 | std-round-20 | 19561.4 / 9090.7 / 50x50x32 / 12 | 19561.4 / 9090.7 / 50x50x32 / 12 | 20/20 | 20/20 | yes |
| E-STHRB50 | std-round-50 | 131365.3 / 32431.1 / 100x100x50 / 12 | 131365.3 / 32431.1 / 100x100x50 / 12 | 20/20 | 20/20 | yes |
| E-STHSB6 | std-square-6 | 2372.1 / 2003.6 / 28x28x15 / 19 | 2372.1 / 2003.6 / 28x28x15 / 19 | 19/19 | 19/19 | yes |
| E-STHSB16 | std-square-16 | 9419.4 / 6123.7 / 42x42x32 / 19 | 9419.4 / 6123.7 / 42x42x32 / 19 | 19/19 | 19/19 | yes |
| E-STHS30 | std-square-30 | 29840.2 / 13363.0 / 66x66x38 / 19 | 29840.2 / 13363.0 / 66x66x38 / 19 | 19/19 | 19/19 | yes |
| E-STHSB50 | std-square-50 | 126384.0 / 31441.3 / 100x100x50 / 19 | 126384.0 / 31441.3 / 100x100x50 / 19 | 19/19 | 19/19 | yes |
| E-STHCB6 | std-compact-6 | 1928.3 / 1645.0 / 12x28x15 / 18 | 1928.3 / 1645.0 / 12x28x15 / 18 | 19/19 | 19/19 | yes |
| E-STHCB10 | std-compact-10 | 3235.4 / 2701.1 / 18x30x20 / 17 | 3235.4 / 2701.1 / 18x30x20 / 17 | 19/19 | 19/19 | yes |
| E-STHC16 | std-compact-16 | 9350.6 / 6104.3 / 26x42x32 / 19 | 9350.6 / 6104.3 / 26x42x32 / 19 | 19/19 | 19/19 | yes |
| E-STHCB25 | std-compact-25 | 21826.8 / 10794.4 / 37x55x38 / 19 | 21826.8 / 10794.4 / 37x55x38 / 19 | 19/19 | 19/19 | yes |
| E-STHC40 | std-compact-40 | 103560.8 / 26235.8 / 65x90x50 / 19 | 103560.8 / 26235.8 / 65x90x50 / 19 | 19/19 | 19/19 | yes |
| E-SSTHC12 | std-compact-12 | 4870.7 / 3714.6 / 20x36x24 / 17 | 4870.7 / 3714.6 / 20x36x24 / 17 | 19/19 | 19/19 | yes |
| E-SSTHC35 | std-compact-35 | 55147.3 / 20868.8 / 55x80x50 / 19 | 55147.3 / 20868.8 / 55x80x50 / 19 | 19/19 | 19/19 | yes |
| E-STHRBL12 | std-round-long-12 | 7123.7 / 5045.2 / 36x36x30 / 12 | 7123.7 / 5045.2 / 36x36x30 / 12 | 20/20 | 20/20 | yes |
| E-STHRL20 | std-round-long-20 | 24275.6 / 11554.2 / 50x50x48 / 14 | 24275.6 / 11554.2 / 50x50x48 / 14 | 22/22 | 22/22 | yes |
| E-STHSBL16 | std-square-long-16 | 12233.1 / 8062.2 / 42x42x48 / 21 | 12233.1 / 8062.2 / 42x42x48 / 21 | 21/21 | 21/21 | yes |
| E-STHSL25 | std-square-long-25 | 28017.6 / 14118.8 / 55x55x57 / 21 | 28017.6 / 14118.8 / 55x55x57 / 21 | 21/21 | 21/21 | yes |
| E-STHCBL30 | std-compact-long-30 | 38102.6 / 17554.6 / 42x66x57 / 21 | 38102.6 / 17554.6 / 42x66x57 / 21 | 21/21 | 21/21 | yes |
| E-STHCL16 | std-compact-long-16 | 12164.3 / 8042.7 / 26x42x48 / 21 | 12164.3 / 8042.7 / 26x42x48 / 21 | 21/21 | 21/21 | yes |
| E-STHMRB8 | mr-collar-8 | 7845.0 / 4862.5 / 30x30x16 / 21 | 7845.0 / 4862.5 / 30x30x16 / 21 | 23/23 | 23/23 | yes |
| E-STHMR15 | mr-collar-15 | 12553.0 / 6957.5 / 38x38x17 / 21 | 12553.0 / 6957.5 / 38x38x17 / 21 | 23/23 | 23/23 | yes |
| E-STHMRBL12 | mr-collar-long-12 | 18629.4 / 7964.2 / 36x36x25 / 21 | 18629.4 / 7964.2 / 36x36x25 / 21 | 23/23 | 23/23 | yes |
| E-STHMRL16 | mr-collar-long-16 | 23411.0 / 10125.2 / 39x39x30 / 21 | 23411.0 / 10125.2 / 39x39x30 / 21 | 23/23 | 23/23 | yes |
| E-STHMRL25 | mr-collar-long-25 | 59553.3 / 17752.1 / 54x54x38 / 21 | 59553.3 / 17752.1 / 54x54x38 / 21 | 23/23 | 23/23 | yes |
| E-STHMRL30 | mr-collar-long-30 | 71685.4 / 20395.6 / 59x59x40 / 21 | 71685.4 / 20395.6 / 59x59x40 / 21 | 23/23 | 23/23 | yes |
| E-STHXRB10 | xend-round-10 | 4368.8 / 3196.2 / 30x30x20 / 14 | 4368.8 / 3196.2 / 30x30x20 / 14 | 21/21 | 21/21 | yes |
| E-STHXR40 | xend-round-40 | 133447.8 / 32385.1 / 88x88x70 / 14 | 133447.8 / 32385.1 / 88x88x70 / 14 | 21/21 | 21/21 | yes |
| E-STHXCB8 | xend-compact-8 | 2635.2 / 2092.2 / 16x28x16 / 19 | 2635.2 / 2092.2 / 16x28x16 / 19 | 20/20 | 20/20 | yes |
| E-STHXC16 | xend-compact-16 | 10788.4 / 6140.3 / 26x42x32 / 21 | 10788.4 / 6140.3 / 26x42x32 / 21 | 20/20 | 20/20 | yes |
| E-STHXCB30 | xend-compact-30 | 47114.3 / 17969.9 / 42x66x58 / 21 | 47114.3 / 17969.9 / 42x66x58 / 21 | 20/20 | 20/20 | yes |
| E-STHRBN8 | thick-round-8 | 4933.8 / 3110.0 / 32x32x16 / 12 | 4933.8 / 3110.0 / 32x32x16 / 12 | 20/20 | 20/20 | yes |
| E-STHRN50 | thick-round-50 | 211173.8 / 39534.7 / 114x114x50 / 12 | 211173.8 / 39534.7 / 114x114x50 / 12 | 20/20 | 20/20 | yes |
| E-STHCBN10 | thick-compact-10 | 6626.0 / 3565.1 / 20x38x20 / 18 | 6626.0 / 3565.1 / 20x38x20 / 18 | 19/19 | 19/19 | yes |
| E-STHCN30 | thick-compact-30 | 51166.5 / 16116.9 / 50x73x38 / 19 | 51166.5 / 16116.9 / 50x73x38 / 19 | 19/19 | 19/19 | yes |
| E-STHRBNL16 | thick-round-long-16 | 27215.5 / 10980.9 / 50x50x48 / 14 | 27215.5 / 10980.9 / 50x50x48 / 14 | 22/22 | 22/22 | yes |
| E-STHCNL35 | thick-compact-long-35 | 131232.8 / 31845.6 / 61x89x75 / 21 | 131232.8 / 31845.6 / 61x89x75 / 21 | 21/21 | 21/21 | yes |
| E-STHRNL35 | thick-round-long-35 | 141150.5 / 33887.0 / 89x89x75 / 14 | 141150.5 / 33887.0 / 89x89x75 / 14 | 22/22 | 22/22 | yes |
| E-STHWRB10 | slit-round-10 | 16688.5 / 7775.2 / 49x49x20 / 23 | 16688.5 / 7775.2 / 49x49x20 / 23 | 24/24 | 24/24 | yes |
| E-STHWR50 | slit-round-50 | 291773.8 / 55367.4 / 119x119x65 / 23 | 291773.8 / 55367.4 / 119x119x65 / 23 | 24/24 | 24/24 | yes |
| E-SSTHWR30 | slit-round-30 | 86310.1 / 23518.1 / 79x79x40 / 23 | 86310.1 / 23518.1 / 79x79x40 / 23 | 24/24 | 24/24 | yes |
| E-STHWSB8 | slit-square-8 | 8764.0 / 4718.3 / 39x39x18 / 30 | 8764.0 / 4718.3 / 39x39x18 / 30 | 23/23 | 23/23 | yes |
| E-STHWS25 | slit-square-25 | 48144.6 / 16011.6 / 69x69x38 / 30 | 48144.6 / 16011.6 / 69x69x38 / 30 | 23/23 | 23/23 | yes |
| E-STHWCB35 | slit-compact-35 | 113850.3 / 29425.1 / 66x94x48 / 30 | 113850.3 / 29425.1 / 66x94x48 / 30 | 23/23 | 23/23 | yes |
| E-SSTHWC16 | slit-compact-16 | 26770.6 / 10461.4 / 37x56x30 / 30 | 26770.6 / 10461.4 / 37x56x30 / 30 | 23/23 | 23/23 | yes |
| E-STHWRBL12 | slit-round-long-12 | 28002.6 / 10936.4 / 52x52x33 / 29 | 28002.6 / 10936.4 / 52x52x33 / 29 | 24/24 | 24/24 | yes |
| E-STHWSL30 | slit-square-long-30 | 104517.2 / 26988.4 / 79x79x60 / 36 | 104517.2 / 26988.4 / 79x79x60 / 36 | 23/23 | 23/23 | yes |
| E-STHWCBL50 | slit-compact-long-50 | 397514.0 / 69980.2 / 91x119x97.5 / 36 | 397514.0 / 69980.2 / 91x119x97.5 / 36 | 23/23 | 23/23 | yes |
| E-SSTHWCL12 | slit-compact-long-12 | 25496.9 / 10066.4 / 34x52x33 / 36 | 25496.9 / 10066.4 / 34x52x33 / 36 | 23/23 | 23/23 | yes |
| E-STHRB8 | std-round-8 | 3306.4 / 2542.7 / 28x28x16 / 12 | 3306.4 / 2542.7 / 28x28x16 / 12 | 20/20 | 20/20 | yes |
| E-STHRB10 | std-round-10 | 4060.4 / 3170.9 / 30x30x20 / 12 | 4060.4 / 3170.9 / 30x30x20 / 12 | 20/20 | 20/20 | yes |
| E-STHRB15 | std-round-15 | 9353.5 / 6065.5 / 40x40x30 / 12 | 9353.5 / 6065.5 / 40x40x30 / 12 | 20/20 | 20/20 | yes |
| E-STHRB16 | std-round-16 | 11328.9 / 6806.3 / 42x42x32 / 12 | 11328.9 / 6806.3 / 42x42x32 / 12 | 20/20 | 20/20 | yes |
| E-STHRB25 | std-round-25 | 25141.0 / 11660.3 / 55x55x38 / 12 | 25141.0 / 11660.3 / 55x55x38 / 12 | 20/20 | 20/20 | yes |
| E-STHRB30 | std-round-30 | 37580.6 / 15029.5 / 66x66x38 / 12 | 37580.6 / 15029.5 / 66x66x38 / 12 | 20/20 | 20/20 | yes |
| E-STHRB35 | std-round-35 | 63035.7 / 22495.8 / 80x80x50 / 12 | 63035.7 / 22495.8 / 80x80x50 / 12 | 20/20 | 20/20 | yes |
| E-STHRB40 | std-round-40 | 110944.8 / 27719.0 / 90x90x50 / 12 | 110944.8 / 27719.0 / 90x90x50 / 12 | 20/20 | 20/20 | yes |
| E-STHSB8 | std-square-8 | 2599.2 / 2234.2 / 28x28x16 / 19 | 2599.2 / 2234.2 / 28x28x16 / 19 | 19/19 | 19/19 | yes |
| E-STHSB10 | std-square-10 | 3139.2 / 2770.2 / 30x30x20 / 19 | 3139.2 / 2770.2 / 30x30x20 / 19 | 19/19 | 19/19 | yes |
| E-STHSB12 | std-square-12 | 5114.9 / 3981.4 / 36x36x24 / 19 | 5114.9 / 3981.4 / 36x36x24 / 19 | 19/19 | 19/19 | yes |
| E-STHSB15 | std-square-15 | 7792.0 / 5506.8 / 40x40x30 / 19 | 7792.0 / 5506.8 / 40x40x30 / 19 | 19/19 | 19/19 | yes |
| E-STHSB20 | std-square-20 | 15808.9 / 8075.6 / 50x50x32 / 19 | 15808.9 / 8075.6 / 50x50x32 / 19 | 19/19 | 19/19 | yes |
| E-STHSB25 | std-square-25 | 21204.7 / 10606.2 / 55x55x38 / 19 | 21204.7 / 10606.2 / 55x55x38 / 19 | 19/19 | 19/19 | yes |
| E-STHSB35 | std-square-35 | 53598.4 / 20497.6 / 80x80x50 / 19 | 53598.4 / 20497.6 / 80x80x50 / 19 | 19/19 | 19/19 | yes |
| E-STHSB40 | std-square-40 | 100996.4 / 25635.7 / 90x90x50 / 19 | 100996.4 / 25635.7 / 90x90x50 / 19 | 19/19 | 19/19 | yes |
| E-STHCB8 | std-compact-8 | 2495.1 / 2074.1 / 16x28x16 / 17 | 2495.1 / 2074.1 / 16x28x16 / 17 | 19/19 | 19/19 | yes |
| E-STHCB15 | std-compact-15 | 7579.2 / 5256.6 / 24x40x30 / 17 | 7579.2 / 5256.6 / 24x40x30 / 17 | 19/19 | 19/19 | yes |
| E-STHCB20 | std-compact-20 | 16213.9 / 8199.3 / 32x50x32 / 19 | 16213.9 / 8199.3 / 32x50x32 / 19 | 19/19 | 19/19 | yes |
| E-STHCB30 | std-compact-30 | 30142.2 / 13448.1 / 42x66x38 / 19 | 30142.2 / 13448.1 / 42x66x38 / 19 | 19/19 | 19/19 | yes |
| E-STHCB50 | std-compact-50 | 124807.7 / 31156.1 / 75x100x50 / 19 | 124807.7 / 31156.1 / 75x100x50 / 19 | 19/19 | 19/19 | yes |
| E-STHRBL16 | std-round-long-16 | 14142.5 / 8744.8 / 42x42x48 / 14 | 14142.5 / 8744.8 / 42x42x48 / 14 | 22/22 | 22/22 | yes |
| E-STHRBL25 | std-round-long-25 | 31953.9 / 15172.9 / 55x55x57 / 14 | 31953.9 / 15172.9 / 55x55x57 / 14 | 22/22 | 22/22 | yes |
| E-STHRBL30 | std-round-long-30 | 45540.9 / 19136.0 / 66x66x57 / 14 | 45540.9 / 19136.0 / 66x66x57 / 14 | 22/22 | 22/22 | yes |
| E-STHSBL12 | std-square-long-12 | 5642.7 / 4509.2 / 36x36x30 / 19 | 5642.7 / 4509.2 / 36x36x30 / 19 | 19/19 | 19/19 | yes |
| E-STHSBL20 | std-square-long-20 | 20523.1 / 10539.1 / 50x50x48 / 21 | 20523.1 / 10539.1 / 50x50x48 / 21 | 21/21 | 21/21 | yes |
| E-STHSBL30 | std-square-long-30 | 37800.6 / 17469.6 / 66x66x57 / 21 | 37800.6 / 17469.6 / 66x66x57 / 21 | 21/21 | 21/21 | yes |
| E-STHCBL12 | std-compact-long-12 | 5398.5 / 4242.4 / 20x36x30 / 17 | 5398.5 / 4242.4 / 20x36x30 / 17 | 19/19 | 19/19 | yes |
| E-STHCBL20 | std-compact-long-20 | 20928.1 / 10662.8 / 32x50x48 / 21 | 20928.1 / 10662.8 / 32x50x48 / 21 | 21/21 | 21/21 | yes |
| E-STHCBL25 | std-compact-long-25 | 28639.7 / 14307.0 / 37x55x57 / 21 | 28639.7 / 14307.0 / 37x55x57 / 21 | 21/21 | 21/21 | yes |
| E-STHRBN10 | thick-round-10 | 8444.8 / 4493.8 / 38x38x20 / 12 | 8444.8 / 4493.8 / 38x38x20 / 12 | 20/20 | 20/20 | yes |
| E-STHRBN12 | thick-round-12 | 11200.2 / 5472.3 / 40x40x24 / 12 | 11200.2 / 5472.3 / 40x40x24 / 12 | 20/20 | 20/20 | yes |
| E-STHRBN15 | thick-round-15 | 17633.6 / 7849.7 / 48x48x30 / 12 | 17633.6 / 7849.7 / 48x48x30 / 12 | 20/20 | 20/20 | yes |
| E-STHRBN16 | thick-round-16 | 20683.4 / 8678.4 / 50x50x32 / 12 | 20683.4 / 8678.4 / 50x50x32 / 12 | 20/20 | 20/20 | yes |
| E-STHRBN20 | thick-round-20 | 36672.3 / 12372.5 / 63x63x32 / 12 | 36672.3 / 12372.5 / 63x63x32 / 12 | 20/20 | 20/20 | yes |
| E-STHRBN25 | thick-round-25 | 46796.3 / 15278.1 / 68x68x38 / 12 | 46796.3 / 15278.1 / 68x68x38 / 12 | 20/20 | 20/20 | yes |
| E-STHRBN30 | thick-round-30 | 57861.6 / 17503.9 / 73x73x38 / 12 | 57861.6 / 17503.9 / 73x73x38 / 12 | 20/20 | 20/20 | yes |
| E-STHRBN40 | thick-round-40 | 181202.3 / 34383.2 / 104x104x50 / 12 | 181202.3 / 34383.2 / 104x104x50 / 12 | 20/20 | 20/20 | yes |
| E-STHRBNL12 | thick-round-long-12 | 12802.4 / 6113.2 / 40x40x30 / 12 | 12802.4 / 6113.2 / 40x40x30 / 12 | 20/20 | 20/20 | yes |
| E-STHRBNL20 | thick-round-long-20 | 46831.1 / 15280.6 / 63x63x48 / 14 | 46831.1 / 15280.6 / 63x63x48 / 14 | 22/22 | 22/22 | yes |
| E-STHRBNL25 | thick-round-long-25 | 61137.5 / 19301.2 / 68x68x57 / 14 | 61137.5 / 19301.2 / 68x68x57 / 14 | 22/22 | 22/22 | yes |
| E-STHRBNL30 | thick-round-long-30 | 74354.3 / 22138.7 / 73x73x57 / 14 | 74354.3 / 22138.7 / 73x73x57 / 14 | 22/22 | 22/22 | yes |
| E-STHRBNL40 | thick-round-long-40 | 244905.9 / 43520.5 / 104x104x75 / 14 | 244905.9 / 43520.5 / 104x104x75 / 14 | 22/22 | 22/22 | yes |
| E-STHRBNL50 | thick-round-long-50 | 286659.0 / 50242.1 / 114x114x75 / 14 | 286659.0 / 50242.1 / 114x114x75 / 14 | 22/22 | 22/22 | yes |
| E-STHCBN8 | thick-compact-8 | 3348.5 / 2301.0 / 15x32x16 / 18 | 3348.5 / 2301.0 / 15x32x16 / 18 | 19/19 | 19/19 | yes |
| E-STHCBN12 | thick-compact-12 | 9459.2 / 4853.6 / 25x40x24 / 19 | 9459.2 / 4853.6 / 25x40x24 / 19 | 19/19 | 19/19 | yes |
| E-STHCBN15 | thick-compact-15 | 14857.5 / 6868.8 / 29x48x30 / 19 | 14857.5 / 6868.8 / 29x48x30 / 19 | 19/19 | 19/19 | yes |
| E-STHCBN16 | thick-compact-16 | 18172.8 / 7800.6 / 32x50x32 / 19 | 18172.8 / 7800.6 / 32x50x32 / 19 | 19/19 | 19/19 | yes |
| E-STHCBN20 | thick-compact-20 | 31207.6 / 10933.6 / 40x63x32 / 19 | 31207.6 / 10933.6 / 40x63x32 / 19 | 19/19 | 19/19 | yes |
| E-STHCBN25 | thick-compact-25 | 41353.7 / 13861.9 / 45x68x38 / 19 | 41353.7 / 13861.9 / 45x68x38 / 19 | 19/19 | 19/19 | yes |
| E-STHCBN35 | thick-compact-35 | 96283.2 / 24540.5 / 61x89x50 / 19 | 96283.2 / 24540.5 / 61x89x50 / 19 | 19/19 | 19/19 | yes |
| E-STHCBN40 | thick-compact-40 | 170393.3 / 32589.5 / 76x104x50 / 19 | 170393.3 / 32589.5 / 76x104x50 / 19 | 19/19 | 19/19 | yes |
| E-STHCBN50 | thick-compact-50 | 201575.8 / 37994.4 / 86x114x50 / 19 | 201575.8 / 37994.4 / 86x114x50 / 19 | 19/19 | 19/19 | yes |
| E-STHCBNL12 | thick-compact-long-12 | 11061.4 / 5494.5 / 25x40x30 / 19 | 11061.4 / 5494.5 / 25x40x30 / 19 | 19/19 | 19/19 | yes |
| E-STHCBNL16 | thick-compact-long-16 | 24704.9 / 10103.2 / 32x50x48 / 21 | 24704.9 / 10103.2 / 32x50x48 / 21 | 21/21 | 21/21 | yes |
| E-STHCBNL20 | thick-compact-long-20 | 41366.4 / 13841.8 / 40x63x48 / 21 | 41366.4 / 13841.8 / 40x63x48 / 21 | 21/21 | 21/21 | yes |
| E-STHCBNL25 | thick-compact-long-25 | 55694.9 / 17885.1 / 45x68x57 / 21 | 55694.9 / 17885.1 / 45x68x57 / 21 | 21/21 | 21/21 | yes |
| E-STHCBNL30 | thick-compact-long-30 | 67659.2 / 20751.7 / 50x73x57 / 21 | 67659.2 / 20751.7 / 50x73x57 / 21 | 21/21 | 21/21 | yes |
| E-STHCBNL40 | thick-compact-long-40 | 234096.8 / 41726.8 / 76x104x75 / 21 | 234096.8 / 41726.8 / 76x104x75 / 21 | 21/21 | 21/21 | yes |
| E-STHCBNL50 | thick-compact-long-50 | 277061.0 / 48701.8 / 86x114x75 / 21 | 277061.0 / 48701.8 / 86x114x75 / 21 | 21/21 | 21/21 | yes |
| E-STHXRB12 | xend-round-12 | 7102.7 / 4570.8 / 36x36x24 / 14 | 7102.7 / 4570.8 / 36x36x24 / 14 | 21/21 | 21/21 | yes |
| E-STHXRB15 | xend-round-15 | 10280.1 / 6132.4 / 40x40x30 / 14 | 10280.1 / 6132.4 / 40x40x30 / 14 | 21/21 | 21/21 | yes |
| E-STHXRB16 | xend-round-16 | 12766.6 / 6842.4 / 42x42x32 / 14 | 12766.6 / 6842.4 / 42x42x32 / 14 | 21/21 | 21/21 | yes |
| E-STHXRB20 | xend-round-20 | 23672.7 / 10115.9 / 50x50x38 / 14 | 23672.7 / 10115.9 / 50x50x38 / 14 | 21/21 | 21/21 | yes |
| E-STHXRB25 | xend-round-25 | 33329.9 / 13277.9 / 55x55x46 / 14 | 33329.9 / 13277.9 / 55x55x46 / 14 | 21/21 | 21/21 | yes |
| E-STHXRB30 | xend-round-30 | 54552.7 / 19551.3 / 66x66x58 / 14 | 54552.7 / 19551.3 / 66x66x58 / 14 | 21/21 | 21/21 | yes |
| E-STHXR8 | xend-round-8 | 3446.4 / 2560.8 / 28x28x16 / 14 | 3446.4 / 2560.8 / 28x28x16 / 14 | 21/21 | 21/21 | yes |
| E-STHXCB10 | xend-compact-10 | 3543.8 / 2726.4 / 18x30x20 / 19 | 3543.8 / 2726.4 / 18x30x20 / 19 | 20/20 | 20/20 | yes |
| E-STHXCB12 | xend-compact-12 | 5377.6 / 3768.0 / 20x36x24 / 19 | 5377.6 / 3768.0 / 20x36x24 / 19 | 20/20 | 20/20 | yes |
| E-STHXCB15 | xend-compact-15 | 8505.7 / 5323.5 / 24x40x30 / 19 | 8505.7 / 5323.5 / 24x40x30 / 19 | 20/20 | 20/20 | yes |
| E-STHXCB20 | xend-compact-20 | 20325.2 / 9224.5 / 32x50x38 / 21 | 20325.2 / 9224.5 / 32x50x38 / 21 | 20/20 | 20/20 | yes |
| E-STHXCB25 | xend-compact-25 | 30015.7 / 12412.0 / 37x55x46 / 21 | 30015.7 / 12412.0 / 37x55x46 / 21 | 20/20 | 20/20 | yes |
| E-STHXCB40 | xend-compact-40 | 125124.2 / 30689.7 / 62x88x70 / 21 | 125124.2 / 30689.7 / 62x88x70 / 21 | 20/20 | 20/20 | yes |
| E-STHMRB10 | mr-collar-10 | 10548.2 / 6029.6 / 34x34x17 / 21 | 10548.2 / 6029.6 / 34x34x17 / 21 | 23/23 | 23/23 | yes |
| E-STHMRB12 | mr-collar-12 | 11771.5 / 6481.6 / 36x36x17 / 21 | 11771.5 / 6481.6 / 36x36x17 / 21 | 23/23 | 23/23 | yes |
| E-STHMRB16 | mr-collar-16 | 16010.4 / 8411.3 / 39x39x22 / 21 | 16010.4 / 8411.3 / 39x39x22 / 21 | 23/23 | 23/23 | yes |
| E-STHMRB20 | mr-collar-20 | 27308.1 / 11609.6 / 49x49x22 / 21 | 27308.1 / 11609.6 / 49x49x22 / 21 | 23/23 | 23/23 | yes |
| E-STHMRB25 | mr-collar-25 | 31858.9 / 13118.0 / 54x54x22 / 21 | 31858.9 / 13118.0 / 54x54x22 / 21 | 23/23 | 23/23 | yes |
| E-STHMRB30 | mr-collar-30 | 40346.7 / 15258.8 / 59x59x24 / 21 | 40346.7 / 15258.8 / 59x59x24 / 21 | 23/23 | 23/23 | yes |
| E-STHMRBL15 | mr-collar-long-15 | 22561.5 / 9169.0 / 38x38x28 / 21 | 22561.5 / 9169.0 / 38x38x28 / 21 | 23/23 | 23/23 | yes |
| E-STHMRBL20 | mr-collar-long-20 | 45345.7 / 14708.1 / 49x49x34 / 21 | 45345.7 / 14708.1 / 49x49x34 / 21 | 23/23 | 23/23 | yes |
| E-STHWRB8 | slit-round-8 | 10295.7 / 5371.9 / 39x39x18 / 23 | 10295.7 / 5371.9 / 39x39x18 / 23 | 24/24 | 24/24 | yes |
| E-STHWRB12 | slit-round-12 | 21213.0 / 8942.3 / 52x52x22 / 23 | 21213.0 / 8942.3 / 52x52x22 / 23 | 24/24 | 24/24 | yes |
| E-STHWRB15 | slit-round-15 | 27909.2 / 10942.8 / 56x56x27 / 23 | 27909.2 / 10942.8 / 56x56x27 / 23 | 24/24 | 24/24 | yes |
| E-STHWRB16 | slit-round-16 | 29557.0 / 11424.5 / 56x56x30 / 23 | 29557.0 / 11424.5 / 56x56x30 / 23 | 24/24 | 24/24 | yes |
| E-STHWRB20 | slit-round-20 | 42379.2 / 14575.4 / 64x64x32 / 23 | 42379.2 / 14575.4 / 64x64x32 / 23 | 24/24 | 24/24 | yes |
| E-STHWRB25 | slit-round-25 | 55165.1 / 17870.6 / 69x69x38 / 23 | 55165.1 / 17870.6 / 69x69x38 / 23 | 24/24 | 24/24 | yes |
| E-STHWRB35 | slit-round-35 | 123544.4 / 31399.6 / 94x94x48 / 23 | 123544.4 / 31399.6 / 94x94x48 / 23 | 24/24 | 24/24 | yes |
| E-STHWRB40 | slit-round-40 | 187920.1 / 40599.5 / 104x104x55 / 23 | 187920.1 / 40599.5 / 104x104x55 / 23 | 24/24 | 24/24 | yes |
| E-STHWRBL16 | slit-round-long-16 | 40087.5 / 14365.3 / 56x56x45 / 29 | 40087.5 / 14365.3 / 56x56x45 / 29 | 24/24 | 24/24 | yes |
| E-STHWRBL20 | slit-round-long-20 | 56484.1 / 18195.7 / 64x64x48 / 29 | 56484.1 / 18195.7 / 64x64x48 / 29 | 24/24 | 24/24 | yes |
| E-STHWRBL25 | slit-round-long-25 | 75014.9 / 22706.2 / 69x69x57 / 29 | 75014.9 / 22706.2 / 69x69x57 / 29 | 24/24 | 24/24 | yes |
| E-STHWRBL30 | slit-round-long-30 | 117876.4 / 29839.1 / 79x79x60 / 29 | 117876.4 / 29839.1 / 79x79x60 / 29 | 24/24 | 24/24 | yes |
| E-STHWRBL35 | slit-round-long-35 | 166618.7 / 39536.0 / 94x94x72 / 29 | 166618.7 / 39536.0 / 94x94x72 / 29 | 24/24 | 24/24 | yes |
| E-STHWRBL40 | slit-round-long-40 | 255834.5 / 51599.8 / 104x104x82.5 / 29 | 255834.5 / 51599.8 / 104x104x82.5 / 29 | 24/24 | 24/24 | yes |
| E-STHWRBL50 | slit-round-long-50 | 406357.2 / 71366.9 / 119x119x97.5 / 29 | 406357.2 / 71366.9 / 119x119x97.5 / 29 | 24/24 | 24/24 | yes |
| E-STHWSB10 | slit-square-10 | 14367.4 / 6797.8 / 49x49x20 / 30 | 14367.4 / 6797.8 / 49x49x20 / 30 | 23/23 | 23/23 | yes |
| E-STHWSB12 | slit-square-12 | 17945.5 / 7787.5 / 52x52x22 / 30 | 17945.5 / 7787.5 / 52x52x22 / 30 | 23/23 | 23/23 | yes |
| E-STHWSB15 | slit-square-15 | 24514.7 / 9749.8 / 56x56x27 / 30 | 24514.7 / 9749.8 / 56x56x27 / 30 | 23/23 | 23/23 | yes |
| E-STHWSB16 | slit-square-16 | 26162.4 / 10231.5 / 56x56x30 / 30 | 26162.4 / 10231.5 / 56x56x30 / 30 | 23/23 | 23/23 | yes |
| E-STHWSB20 | slit-square-20 | 36283.1 / 12953.9 / 64x64x32 / 30 | 36283.1 / 12953.9 / 64x64x32 / 30 | 23/23 | 23/23 | yes |
| E-STHWSB30 | slit-square-30 | 72950.9 / 20667.4 / 79x79x40 / 30 | 72950.9 / 20667.4 / 79x79x40 / 30 | 23/23 | 23/23 | yes |
| E-STHWSB35 | slit-square-35 | 104145.8 / 27300.6 / 94x94x48 / 30 | 104145.8 / 27300.6 / 94x94x48 / 30 | 23/23 | 23/23 | yes |
| E-STHWSB40 | slit-square-40 | 163377.8 / 36266.6 / 104x104x55 / 30 | 163377.8 / 36266.6 / 104x104x55 / 30 | 23/23 | 23/23 | yes |
| E-STHWSB50 | slit-square-50 | 262011.0 / 50155.7 / 119x119x65 / 30 | 262011.0 / 50155.7 / 119x119x65 / 30 | 23/23 | 23/23 | yes |
| E-STHWSBL12 | slit-square-long-12 | 24735.1 / 9781.7 / 52x52x33 / 36 | 24735.1 / 9781.7 / 52x52x33 / 36 | 23/23 | 23/23 | yes |
| E-STHWSBL16 | slit-square-long-16 | 36692.9 / 13172.4 / 56x56x45 / 36 | 36692.9 / 13172.4 / 56x56x45 / 36 | 23/23 | 23/23 | yes |
| E-STHWSBL20 | slit-square-long-20 | 50387.9 / 16574.3 / 64x64x48 / 36 | 50387.9 / 16574.3 / 64x64x48 / 36 | 23/23 | 23/23 | yes |
| E-STHWSBL25 | slit-square-long-25 | 67994.4 / 20847.2 / 69x69x57 / 36 | 67994.4 / 20847.2 / 69x69x57 / 36 | 23/23 | 23/23 | yes |
| E-STHWSBL35 | slit-square-long-35 | 147220.2 / 35437.0 / 94x94x72 / 36 | 147220.2 / 35437.0 / 94x94x72 / 36 | 23/23 | 23/23 | yes |
| E-STHWSBL40 | slit-square-long-40 | 231292.1 / 47266.9 / 104x104x82.5 / 36 | 231292.1 / 47266.9 / 104x104x82.5 / 36 | 23/23 | 23/23 | yes |
| E-STHWSBL50 | slit-square-long-50 | 376594.3 / 66155.2 / 119x119x97.5 / 36 | 376594.3 / 66155.2 / 119x119x97.5 / 36 | 23/23 | 23/23 | yes |
| E-STHWCB8 | slit-compact-8 | 9392.3 / 5000.4 / 27x39x18 / 30 | 9392.3 / 5000.4 / 27x39x18 / 30 | 23/23 | 23/23 | yes |
| E-STHWCB10 | slit-compact-10 | 14825.4 / 7002.2 / 32x49x20 / 30 | 14825.4 / 7002.2 / 32x49x20 / 30 | 23/23 | 23/23 | yes |
| E-STHWCB12 | slit-compact-12 | 18707.0 / 8071.7 / 34x52x22 / 30 | 18707.0 / 8071.7 / 34x52x22 / 30 | 23/23 | 23/23 | yes |
| E-STHWCB15 | slit-compact-15 | 25122.9 / 9979.6 / 37x56x27 / 30 | 25122.9 / 9979.6 / 37x56x27 / 30 | 23/23 | 23/23 | yes |
| E-STHWCB20 | slit-compact-20 | 37390.6 / 13272.1 / 42x64x32 / 30 | 37390.6 / 13272.1 / 42x64x32 / 30 | 23/23 | 23/23 | yes |
| E-STHWCB25 | slit-compact-25 | 50247.2 / 16602.0 / 47x69x38 / 30 | 50247.2 / 16602.0 / 47x69x38 / 30 | 23/23 | 23/23 | yes |
| E-STHWCB30 | slit-compact-30 | 80580.9 / 22366.4 / 57x79x40 / 30 | 80580.9 / 22366.4 / 57x79x40 / 30 | 23/23 | 23/23 | yes |
| E-STHWCB40 | slit-compact-40 | 177112.6 / 38807.1 / 76x104x55 / 30 | 177112.6 / 38807.1 / 76x104x55 / 30 | 23/23 | 23/23 | yes |
| E-STHWCB50 | slit-compact-50 | 282928.8 / 53979.4 / 91x119x65 / 30 | 282928.8 / 53979.4 / 91x119x65 / 30 | 23/23 | 23/23 | yes |
| E-STHWCBL16 | slit-compact-long-16 | 37301.4 / 13402.8 / 37x56x45 / 36 | 37301.4 / 13402.8 / 37x56x45 / 36 | 23/23 | 23/23 | yes |
| E-STHWCBL20 | slit-compact-long-20 | 51495.7 / 16893.1 / 42x64x48 / 36 | 51495.7 / 16893.1 / 42x64x48 / 36 | 23/23 | 23/23 | yes |
| E-STHWCBL25 | slit-compact-long-25 | 70097.3 / 21438.1 / 47x69x57 / 36 | 70097.3 / 21438.1 / 47x69x57 / 36 | 23/23 | 23/23 | yes |
| E-STHWCBL30 | slit-compact-long-30 | 112147.6 / 28688.1 / 57x79x60 / 36 | 112147.6 / 28688.1 / 57x79x60 / 36 | 23/23 | 23/23 | yes |
| E-STHWCBL35 | slit-compact-long-35 | 156925.1 / 37562.2 / 66x94x72 / 36 | 156925.1 / 37562.2 / 66x94x72 / 36 | 23/23 | 23/23 | yes |
| E-STHWCBL40 | slit-compact-long-40 | 245028.0 / 49808.5 / 76x104x82.5 / 36 | 245028.0 / 49808.5 / 76x104x82.5 / 36 | 23/23 | 23/23 | yes |

| rejected code | python message | parametric message | same |
|---|---|---|---|
| E-STHR15 | E-STHR is not applicable when D = 15 (p.534-535 note) | E-STHR is not applicable when D = 15 (p.534-535 note) | yes |
| E-STHS6 | E-STHS is not applicable when D = 6 (p.534-535 note) | E-STHS is not applicable when D = 6 (p.534-535 note) | yes |
| E-SSTHC50 | E-SSTHC is not applicable when D = 50 (p.534-535 note) | E-SSTHC is not applicable when D = 50 (p.534-535 note) | yes |
| E-STHRB9 | E-STHRB9: hole diameter D must be one of [6, 8, 10, 12, 15, 16, 20, 25, 30, 35, 40, 50] (p.534-535) | E-STHRB9: hole diameter D must be one of [6, 8, 10, 12, 15, 16, 20, 25, 30, 35, 40, 50] (p.534-535) | yes |
| E-STHCB45 | E-STHCB45: hole diameter D must be one of [6, 8, 10, 12, 15, 16, 20, 25, 30, 35, 40, 50] (p.534-535) | E-STHCB45: hole diameter D must be one of [6, 8, 10, 12, 15, 16, 20, 25, 30, 35, 40, 50] (p.534-535) | yes |
| E-STHRB | 'E-STHRB': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | 'E-STHRB': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | yes |
| E-STHRBL15 | E-STHRBL15: the long sleeve type is only applicable to the D marked * in the table: [12, 16, 20, 25, 30] (p.534-535) | E-STHRBL15: the long sleeve type is only applicable to the D marked * in the table: [12, 16, 20, 25, 30] (p.534-535) | yes |
| E-STHCL10 | E-STHCL10: the long sleeve type is only applicable to the D marked * in the table: [12, 16, 20, 25, 30] (p.534-535) | E-STHCL10: the long sleeve type is only applicable to the D marked * in the table: [12, 16, 20, 25, 30] (p.534-535) | yes |
| E-STHRN35 | E-STHRN is not applicable when D = 35 (p.536 note) | E-STHRN is not applicable when D = 35 (p.536 note) | yes |
| E-STHCN10 | E-STHCN is not applicable when D = 10 (p.536 note) | E-STHCN is not applicable when D = 10 (p.536 note) | yes |
| E-STHRBN35 | E-STHRBN is not applicable when D = 35 (p.536 note) | E-STHRBN is not applicable when D = 35 (p.536 note) | yes |
| E-STHSBN10 | 'E-STHSBN10': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | 'E-STHSBN10': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | yes |
| E-STHXRB8 | E-STHXRB is not applicable when D = 8 (p.533 note) | E-STHXRB is not applicable when D = 8 (p.533 note) | yes |
| E-STHXR35 | E-STHXR35: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.533) | E-STHXR35: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.533) | yes |
| E-STHMRBL25 | E-STHMRBL is not applicable when D = 25 (p.532 note) | E-STHMRBL is not applicable when D = 25 (p.532 note) | yes |
| E-STHMR40 | E-STHMR40: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30] (p.532) | E-STHMR40: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30] (p.532) | yes |
| E-STHMRL10 | E-STHMRL10: the long sleeve type is only applicable to the D marked * in the table: [12, 15, 16, 20, 25, 30] (p.532) | E-STHMRL10: the long sleeve type is only applicable to the D marked * in the table: [12, 15, 16, 20, 25, 30] (p.532) | yes |
| E-SSTHWR35 | E-SSTHWR is not applicable when D = 35 (p.538-539 note) | E-SSTHWR is not applicable when D = 35 (p.538-539 note) | yes |
| E-SSTHWS40 | E-SSTHWS is not applicable when D = 40 (p.538-539 note) | E-SSTHWS is not applicable when D = 40 (p.538-539 note) | yes |
| E-SSTHWSL12 | E-SSTHWSL is not applicable when D = 12 (p.538-539 note) | E-SSTHWSL is not applicable when D = 12 (p.538-539 note) | yes |
| E-STHWRBL10 | E-STHWRBL10: hole diameter D must be one of [12, 16, 20, 25, 30, 35, 40, 50] (p.538-539) | E-STHWRBL10: hole diameter D must be one of [12, 16, 20, 25, 30, 35, 40, 50] (p.538-539) | yes |
| E-STHWRB6 | E-STHWRB6: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 35, 40, 50] (p.538-539) | E-STHWRB6: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 35, 40, 50] (p.538-539) | yes |
| E-STHWXB10 | 'E-STHWXB10': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | 'E-STHWXB10': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | yes |
| E-STHRB0 | E-STHRB0: hole diameter D must be one of [6, 8, 10, 12, 15, 16, 20, 25, 30, 35, 40, 50] (p.534-535) | E-STHRB0: hole diameter D must be one of [6, 8, 10, 12, 15, 16, 20, 25, 30, 35, 40, 50] (p.534-535) | yes |
| E-STHRB100 | E-STHRB100: hole diameter D must be one of [6, 8, 10, 12, 15, 16, 20, 25, 30, 35, 40, 50] (p.534-535) | E-STHRB100: hole diameter D must be one of [6, 8, 10, 12, 15, 16, 20, 25, 30, 35, 40, 50] (p.534-535) | yes |
| E-STHRB6X | 'E-STHRB6X': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | 'E-STHRB6X': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | yes |
| E-STHRBN | 'E-STHRBN': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | 'E-STHRBN': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | yes |
| E-STHSBN10 | 'E-STHSBN10': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | 'E-STHSBN10': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | yes |
| E-STHMRL8 | E-STHMRL8: the long sleeve type is only applicable to the D marked * in the table: [12, 15, 16, 20, 25, 30] (p.532) | E-STHMRL8: the long sleeve type is only applicable to the D marked * in the table: [12, 15, 16, 20, 25, 30] (p.532) | yes |
| E-STHMRBL10 | E-STHMRBL10: the long sleeve type is only applicable to the D marked * in the table: [12, 15, 16, 20, 25, 30] (p.532) | E-STHMRBL10: the long sleeve type is only applicable to the D marked * in the table: [12, 15, 16, 20, 25, 30] (p.532) | yes |
| E-STHWRBL8 | E-STHWRBL8: hole diameter D must be one of [12, 16, 20, 25, 30, 35, 40, 50] (p.538-539) | E-STHWRBL8: hole diameter D must be one of [12, 16, 20, 25, 30, 35, 40, 50] (p.538-539) | yes |
| E-STHNRB10 | 'E-STHNRB10': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | 'E-STHNRB10': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | yes |
| E-STHXSB10 | 'E-STHXSB10': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | 'E-STHXSB10': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | yes |
| E-STHXRBL12 | 'E-STHXRBL12': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | 'E-STHXRBL12': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | yes |
| E-SSTHRB12 | 'E-SSTHRB12': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | 'E-SSTHRB12': expected <type><D>, e.g. E-STHRB8, with type one of E-STHRB E-STHR E-STHSB E-STHS E-STHCB E-STHC E-SSTHC (standard), E-STHRBL .. E-STHCL (long sleeve), E-STHRBN .. E-STHCNL (thickened), E-STHXRB E-STHXR E-STHXCB E-STHXC (end mounting), E-STHMRB E-STHMR E-STHMRBL E-STHMRL (compact), E-STHWRB .. E-SSTHWC and ...L (slit) | yes |

| row switched on a built design | to | switched vol / area / bbox / faces | direct code (inserted) | equal |
|---|---|---|---|---|
| E-STHRB6 | E-STHWCBL50 | 397514.0 / 69980.2 / 91x119x97.5 / 36 | 397514.0 / 69980.2 / 91x119x97.5 / 36 | yes |
| E-STHWCBL50 | E-STHMRL16 | 23411.0 / 10125.2 / 39x39x30 / 21 | 23411.0 / 10125.2 / 39x39x30 / 21 | yes |
| E-STHMRB8 | E-STHXC16 | 10788.4 / 6140.3 / 26x42x32 / 21 | 10788.4 / 6140.3 / 26x42x32 / 21 | yes |
| E-STHXR40 | E-STHSBL16 | 12233.1 / 8062.2 / 42x42x48 / 21 | 12233.1 / 8062.2 / 42x42x48 / 21 | yes |
| E-STHCNL35 | E-STHRBN8 | 4933.8 / 3110.0 / 32x32x16 / 12 | 4933.8 / 3110.0 / 32x32x16 / 12 | yes |
| E-STHWSB8 | E-STHCBL30 | 38102.6 / 17554.6 / 42x66x57 / 21 | 38102.6 / 17554.6 / 42x66x57 / 21 | yes |

| code | printed by the template from its fields | same |
|---|---|---|
| E-STHRB6 | E-STHRB6 | yes |
| E-STHRB12 | E-STHRB12 | yes |
| E-STHR20 | E-STHR20 | yes |
| E-STHRB50 | E-STHRB50 | yes |
| E-STHSB6 | E-STHSB6 | yes |
| E-STHSB16 | E-STHSB16 | yes |
| E-STHS30 | E-STHS30 | yes |
| E-STHSB50 | E-STHSB50 | yes |
| E-STHCB6 | E-STHCB6 | yes |
| E-STHCB10 | E-STHCB10 | yes |
| E-STHC16 | E-STHC16 | yes |
| E-STHCB25 | E-STHCB25 | yes |
| E-STHC40 | E-STHC40 | yes |
| E-SSTHC12 | E-SSTHC12 | yes |
| E-SSTHC35 | E-SSTHC35 | yes |
| E-STHRBL12 | E-STHRBL12 | yes |
| E-STHRL20 | E-STHRL20 | yes |
| E-STHSBL16 | E-STHSBL16 | yes |
| E-STHSL25 | E-STHSL25 | yes |
| E-STHCBL30 | E-STHCBL30 | yes |
| E-STHCL16 | E-STHCL16 | yes |
| E-STHMRB8 | E-STHMRB8 | yes |
| E-STHMR15 | E-STHMR15 | yes |
| E-STHMRBL12 | E-STHMRBL12 | yes |
| E-STHMRL16 | E-STHMRL16 | yes |
| E-STHMRL25 | E-STHMRL25 | yes |
| E-STHMRL30 | E-STHMRL30 | yes |
| E-STHXRB10 | E-STHXRB10 | yes |
| E-STHXR40 | E-STHXR40 | yes |
| E-STHXCB8 | E-STHXCB8 | yes |
| E-STHXC16 | E-STHXC16 | yes |
| E-STHXCB30 | E-STHXCB30 | yes |
| E-STHRBN8 | E-STHRBN8 | yes |
| E-STHRN50 | E-STHRN50 | yes |
| E-STHCBN10 | E-STHCBN10 | yes |
| E-STHCN30 | E-STHCN30 | yes |
| E-STHRBNL16 | E-STHRBNL16 | yes |
| E-STHCNL35 | E-STHCNL35 | yes |
| E-STHRNL35 | E-STHRNL35 | yes |
| E-STHWRB10 | E-STHWRB10 | yes |
| E-STHWR50 | E-STHWR50 | yes |
| E-SSTHWR30 | E-SSTHWR30 | yes |
| E-STHWSB8 | E-STHWSB8 | yes |
| E-STHWS25 | E-STHWS25 | yes |
| E-STHWCB35 | E-STHWCB35 | yes |
| E-SSTHWC16 | E-SSTHWC16 | yes |
| E-STHWRBL12 | E-STHWRBL12 | yes |
| E-STHWSL30 | E-STHWSL30 | yes |
| E-STHWCBL50 | E-STHWCBL50 | yes |
| E-SSTHWCL12 | E-SSTHWCL12 | yes |
| E-STHRB8 | E-STHRB8 | yes |
| E-STHRB10 | E-STHRB10 | yes |
| E-STHRB15 | E-STHRB15 | yes |
| E-STHRB16 | E-STHRB16 | yes |
| E-STHRB25 | E-STHRB25 | yes |
| E-STHRB30 | E-STHRB30 | yes |
| E-STHRB35 | E-STHRB35 | yes |
| E-STHRB40 | E-STHRB40 | yes |
| E-STHSB8 | E-STHSB8 | yes |
| E-STHSB10 | E-STHSB10 | yes |
| E-STHSB12 | E-STHSB12 | yes |
| E-STHSB15 | E-STHSB15 | yes |
| E-STHSB20 | E-STHSB20 | yes |
| E-STHSB25 | E-STHSB25 | yes |
| E-STHSB35 | E-STHSB35 | yes |
| E-STHSB40 | E-STHSB40 | yes |
| E-STHCB8 | E-STHCB8 | yes |
| E-STHCB15 | E-STHCB15 | yes |
| E-STHCB20 | E-STHCB20 | yes |
| E-STHCB30 | E-STHCB30 | yes |
| E-STHCB50 | E-STHCB50 | yes |
| E-STHRBL16 | E-STHRBL16 | yes |
| E-STHRBL25 | E-STHRBL25 | yes |
| E-STHRBL30 | E-STHRBL30 | yes |
| E-STHSBL12 | E-STHSBL12 | yes |
| E-STHSBL20 | E-STHSBL20 | yes |
| E-STHSBL30 | E-STHSBL30 | yes |
| E-STHCBL12 | E-STHCBL12 | yes |
| E-STHCBL20 | E-STHCBL20 | yes |
| E-STHCBL25 | E-STHCBL25 | yes |
| E-STHRBN10 | E-STHRBN10 | yes |
| E-STHRBN12 | E-STHRBN12 | yes |
| E-STHRBN15 | E-STHRBN15 | yes |
| E-STHRBN16 | E-STHRBN16 | yes |
| E-STHRBN20 | E-STHRBN20 | yes |
| E-STHRBN25 | E-STHRBN25 | yes |
| E-STHRBN30 | E-STHRBN30 | yes |
| E-STHRBN40 | E-STHRBN40 | yes |
| E-STHRBNL12 | E-STHRBNL12 | yes |
| E-STHRBNL20 | E-STHRBNL20 | yes |
| E-STHRBNL25 | E-STHRBNL25 | yes |
| E-STHRBNL30 | E-STHRBNL30 | yes |
| E-STHRBNL40 | E-STHRBNL40 | yes |
| E-STHRBNL50 | E-STHRBNL50 | yes |
| E-STHCBN8 | E-STHCBN8 | yes |
| E-STHCBN12 | E-STHCBN12 | yes |
| E-STHCBN15 | E-STHCBN15 | yes |
| E-STHCBN16 | E-STHCBN16 | yes |
| E-STHCBN20 | E-STHCBN20 | yes |
| E-STHCBN25 | E-STHCBN25 | yes |
| E-STHCBN35 | E-STHCBN35 | yes |
| E-STHCBN40 | E-STHCBN40 | yes |
| E-STHCBN50 | E-STHCBN50 | yes |
| E-STHCBNL12 | E-STHCBNL12 | yes |
| E-STHCBNL16 | E-STHCBNL16 | yes |
| E-STHCBNL20 | E-STHCBNL20 | yes |
| E-STHCBNL25 | E-STHCBNL25 | yes |
| E-STHCBNL30 | E-STHCBNL30 | yes |
| E-STHCBNL40 | E-STHCBNL40 | yes |
| E-STHCBNL50 | E-STHCBNL50 | yes |
| E-STHXRB12 | E-STHXRB12 | yes |
| E-STHXRB15 | E-STHXRB15 | yes |
| E-STHXRB16 | E-STHXRB16 | yes |
| E-STHXRB20 | E-STHXRB20 | yes |
| E-STHXRB25 | E-STHXRB25 | yes |
| E-STHXRB30 | E-STHXRB30 | yes |
| E-STHXR8 | E-STHXR8 | yes |
| E-STHXCB10 | E-STHXCB10 | yes |
| E-STHXCB12 | E-STHXCB12 | yes |
| E-STHXCB15 | E-STHXCB15 | yes |
| E-STHXCB20 | E-STHXCB20 | yes |
| E-STHXCB25 | E-STHXCB25 | yes |
| E-STHXCB40 | E-STHXCB40 | yes |
| E-STHMRB10 | E-STHMRB10 | yes |
| E-STHMRB12 | E-STHMRB12 | yes |
| E-STHMRB16 | E-STHMRB16 | yes |
| E-STHMRB20 | E-STHMRB20 | yes |
| E-STHMRB25 | E-STHMRB25 | yes |
| E-STHMRB30 | E-STHMRB30 | yes |
| E-STHMRBL15 | E-STHMRBL15 | yes |
| E-STHMRBL20 | E-STHMRBL20 | yes |
| E-STHWRB8 | E-STHWRB8 | yes |
| E-STHWRB12 | E-STHWRB12 | yes |
| E-STHWRB15 | E-STHWRB15 | yes |
| E-STHWRB16 | E-STHWRB16 | yes |
| E-STHWRB20 | E-STHWRB20 | yes |
| E-STHWRB25 | E-STHWRB25 | yes |
| E-STHWRB35 | E-STHWRB35 | yes |
| E-STHWRB40 | E-STHWRB40 | yes |
| E-STHWRBL16 | E-STHWRBL16 | yes |
| E-STHWRBL20 | E-STHWRBL20 | yes |
| E-STHWRBL25 | E-STHWRBL25 | yes |
| E-STHWRBL30 | E-STHWRBL30 | yes |
| E-STHWRBL35 | E-STHWRBL35 | yes |
| E-STHWRBL40 | E-STHWRBL40 | yes |
| E-STHWRBL50 | E-STHWRBL50 | yes |
| E-STHWSB10 | E-STHWSB10 | yes |
| E-STHWSB12 | E-STHWSB12 | yes |
| E-STHWSB15 | E-STHWSB15 | yes |
| E-STHWSB16 | E-STHWSB16 | yes |
| E-STHWSB20 | E-STHWSB20 | yes |
| E-STHWSB30 | E-STHWSB30 | yes |
| E-STHWSB35 | E-STHWSB35 | yes |
| E-STHWSB40 | E-STHWSB40 | yes |
| E-STHWSB50 | E-STHWSB50 | yes |
| E-STHWSBL12 | E-STHWSBL12 | yes |
| E-STHWSBL16 | E-STHWSBL16 | yes |
| E-STHWSBL20 | E-STHWSBL20 | yes |
| E-STHWSBL25 | E-STHWSBL25 | yes |
| E-STHWSBL35 | E-STHWSBL35 | yes |
| E-STHWSBL40 | E-STHWSBL40 | yes |
| E-STHWSBL50 | E-STHWSBL50 | yes |
| E-STHWCB8 | E-STHWCB8 | yes |
| E-STHWCB10 | E-STHWCB10 | yes |
| E-STHWCB12 | E-STHWCB12 | yes |
| E-STHWCB15 | E-STHWCB15 | yes |
| E-STHWCB20 | E-STHWCB20 | yes |
| E-STHWCB25 | E-STHWCB25 | yes |
| E-STHWCB30 | E-STHWCB30 | yes |
| E-STHWCB40 | E-STHWCB40 | yes |
| E-STHWCB50 | E-STHWCB50 | yes |
| E-STHWCBL16 | E-STHWCBL16 | yes |
| E-STHWCBL20 | E-STHWCBL20 | yes |
| E-STHWCBL25 | E-STHWCBL25 | yes |
| E-STHWCBL30 | E-STHWCBL30 | yes |
| E-STHWCBL35 | E-STHWCBL35 | yes |
| E-STHWCBL40 | E-STHWCBL40 | yes |


## SolidCraft 0.50.0 observations (exact errors) and workarounds

1. **A thread designation cannot come from a parameter.** `solid.hole` with `thread: "msize"` (a user parameter) -> `invalid parameters for
   `solid.hole`: unknown tapped thread `msize` (ISO metric or a catalogued UNC/UNF, G, Rp, Rc or NPT size)`. Workaround (labelled): one thread
   feature per screw size (set screws M3 M4 M5 M6 M8, clamp screws M4 M5 M6 M8 M10), each suppressed in the rows whose screw is another size; they are `temp` units of the build
   (`runtime/parametric/build.py`): drawn one by one with the others suppressed, because a second thread feature drawn while the first is live
   fails with `invalid parameters for `solid.hole`: `position` [10, 7.5, 18] is not on a face of a body; pick a point on the face to drill`.
2. **A picked face cannot follow a cut that a row switches.** A thread feature drawn while the groove, slit and clearance cuts were suppressed
   picks the plain sleeve face; activating a row with those cuts live then fails: `config.activate ... configuration slit-round-8 would fail to
   rebuild: Clamp screw 1 thread M4: ... the reference `F3:side` no longer exists as it was picked; reselect it`. Workaround: every unit is drawn
   live, in the order of the Python builder, and the default row's suppression is applied at the end. Drilling the threaded holes FIRST (so that
   they pick the plain face in every row) gives a different solid, not a rebuild-safe one: the holes then end in material that the bore and the
   slit remove later (E-STHRB6: 14 faces, 2867.81 mm3 against 12 faces, 2867.16 mm3 built the Python way).
3. **Features that meet while the model is drawn once.** All alternatives exist while the model is drawn (a round and a compact flange, every
   hole set), so their sizes must not meet: a thread drawn where an earlier cut is in its path fails with `an M8 thread does not fit a 12.00 mm
   hole; this hole takes M12`. The drawing uses default parameter values that keep every feature clear of the others (`PARAMS` in `build.py`).
4. **Body names.** The alternatives that make the body (round / square / compact flange) are joins to one sleeve body, so every later cut is
   written without `targets` and the inserted body is named after the model (`flanged-shaft-support`), not after the code; the spec check is run with its
   `body` references renamed (as in the HFS proof).
5. **No free parameter.** Every dimension of these parts is a catalogue row; there is no length or count to change. The "rebuild" rows of
   the tables switch a built design from one configuration row to another (`config.activate` twice) and compare it with that other code
   inserted directly, which proves that the suppression columns and the rows reset a design completely.

## What does not fit the interface document, and proposals

| Where | What this generator needs | Proposal |
|---|---|---|
| 4 `resolve` | a code that matches no template (no digits, an unknown letter after `E-STH`) must get the generator's message, which is also the Python one (`'E-STHRB': expected <type><D>, ...`) | optional `fn no_match(raw)` in `generator.rhai` returning the message (done in the stand-in: `runtime/parametric/harness.py` asks for it) |
| 3 field kinds | `int 6..50` refuses a leading zero and 0; the Python generator reads `E-STHRB06` as D6 and words `D0` as "hole diameter D must be one of ..." | the table check stays in Rhai: the proof uses `{d: text 1..6 [0-9]}` and `parse_int`; an `int` kind with `lenient` (any digits, range checked by the script) would keep the typed range for search |
| 3 second template | one structured template gives the fields (series, shape, black, thick, long, size); a second, generic one (`E-{type: text 1..12 [A-Za-z]}{d: ...}`) gives every other type text to Rhai, which refuses it with the Python message | document that a script may refuse a template match; or `generator.parse` hands the raw code to `resolve` as `fields.raw` (Python words its messages with the typed code, `raw!r`, here the printed code stands in) |
| 3 separators | the template ignores `-`, space, `_`, `/`, `.` between elements, Python's `re.fullmatch` does not: `E-STHRB 12` is read by the template and refused by Python | a per-template `strict` switch, or a required separator mark on every boundary (the doc has `\-` for one) |
| 2 `[parameters]` / `solid.hole` | a thread designation chosen by a parameter | `thread` as an expression over a choice or text parameter (designation text), or `thread: {from: size_param}`, so one feature covers every size |
| model | the picked face of a hole stays valid when a later row switches cuts that split it | a hole feature that picks "the face of the body at this point" by position at every rebuild instead of by the topological name |

What fits without change: per-row topology as suppression columns (one activation switches flange, hole set, bore, thread features), every dimension as a
parameter cell (numbers and expressions over other cells), `generator.toml` rows with source and page, `generator.rhai` with `table()` /
`refuse()` / `code_template()` for every refusal of the Python generator, the field templates for the code shape, and `config.activate` for
switching a built design to another row.

This package has no free ordering parameter, so it adds no optional link-parameter checks. Internal dimension rebuild probes remain as recorded above.

### #23175 checks

The 0.50.0/0.51.1 results above remain release observations. The #23175 CI artifact records 177 valid, 36 rejects, 6 rebuild checks and 2 blocked records. The next CI run also checks link overrides and ordinary edit refusal with `enforce_on_edit` where limit rules exist; these new checks are pending. Differences remain differences.

Unmatched-code diagnostic: follow-up after #23175: optional no_match(raw) in generator.rhai.

The supplied #23175 artifact includes 0 link checks; the added ordinary-edit enforcement check awaits CI.
