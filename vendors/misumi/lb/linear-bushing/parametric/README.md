# misumi.lb.linear-bushing as a parametric SolidCraft generator

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai, and rules addressed by feature name requires the #23175 surface (unavailable on 0.50.0/0.51.1). The exact command errors quoted below are observations from SolidCraft 0.50.0. On capable hosts, link overrides and ordinary source `parameters.change` enforce limit rules marked `enforce_on_edit`.

The bushing modelled ONCE in SolidCraft (`linear-bushing/linear-bushing.sc`), 178 configuration rows (one per catalogue table row and flange shape), the ordering code as a field
template and the logic as plain Rhai, following SolidCraft's generator interface (`docs/formats/generator.md`, version 2, issue 22331). The Python generator in `../src` is untouched and
is the reference everything below is compared with.

```
linear-bushing/            generator.toml ([[template]] x2, [rows."<row>"] source / page / status), linear-bushing.sc, generator.rhai, tables/*.csv
build.py rows.py pkgfiles.py   build the model with solidcraft-cli; the rows and tables come from ../data/*.csv
rhai_equiv.py              no SolidCraft: 2652 codes (every type letter combination x 24 bore sizes x 5 suffixes) through template + Rhai and through bushing.parse
run_codes.py report.py faithfulness.py ci.sh   every valid code of the generator both ways (results.json, faithfulness.json)
```

## The model

- Parameters: `od blen bore fl_h fl_t hole_d cb_d cb_t pcd sq_w cp_a cp_f cp_w x0 g_b g_w g_d1` (the catalogue dimensions), `opp` (counterbore on the far flange face, Z types),
  `plated`, `rowno`, `kind`; derived: hole radii, the square flange corner points, the compact flange flat ends (`sqrt` of lengths squared works).
- Revolve profiles as alternative features (a sketch cannot drop vertices): plain barrel, barrel with the two ring grooves, round flange at x0 = 0, round flange at x0 > 0
  (pilot, centre). Square and compact flanges are sketches joined to the plain barrel (arcs through `sketch.point` ids, so they follow the parameters).
- Holes: a hole set per body variant and counterbore side (28 features); `opp` and `kind` select the set with `drive_suppression` rules (suppress-if), also on a built part.
- Rows set every parameter and the suppression columns; 590 rules: allowed lengths per row (single / double), allowed `opp` and `plated` per row, the hole-set switches.
  Plating is metadata only (tolerance text, material).
- Code level choices (single or double length, Z, plated) are parameters set on top of a row; the harness makes a row for the code in a working copy and inserts it.

## Ordering code

`E-LB[{shape: F|K|H}[{variant: PM|CM|Z|M|P|C}]]{dr: text 1..2 [0-9]}{suffix: TUU|DMUU|DUU|LUU|UU}` and a fallback template `{raw: ...}` so that a code the strict one
does not read still reaches `resolve` and gets the Python message (stainless E-LBHS, shape error). Every refusal of `bushing.parse`, in its order, with its message, is in
`generator.rhai`; `fields(configuration, parameters)` prints the code back (round trip parse(print(parse(c))) is the same for all 480 codes). The part description is built
in Rhai too and equals the Python one for all 480.

**Documented deviation.** The interface ignores the separators ` -_/.` when it reads a code, so `E-LBF20-UU` is read as `E-LBF20UU` where the Python regex refuses it
(`rhai_equiv.json`: 2653 codes, 0 real disagreements; the 2 that are counted apart from the agreeing ones are exactly these two separator cases, Python refuses and the interface accepts, by design; they are not in the reject battery). A dangling trailing separator (`E-LBF20UU-`, `E-LB10TUU_`) is refused with the Python message and is in the battery.

## What was run

`ci.sh` (GitHub CI, SolidCraft 0.50.0): `rhai_equiv.py`, `build.py`, then `run_codes.py`: the 37 valid codes of `codes.txt` and every other valid code of the generator (480 in all) ->
Rhai -> row for the code -> inserted -> `inspect.measure` + the unchanged `src/check.py` (run on a `Bushing` rebuilt from the Rhai result) -> the same code from the Python
generator; the `!` codes of `codes.txt` and 36 more refusals; 8 rebuilds (length single -> double, counterbore side, plating changed on a built part).
`ci.sh` also leaves the built model as `linear-bushing.sc.json` in the output; `linear-bushing/linear-bushing.sc` is that file.
Locally only the Rhai and template checks run (`RHAI_RUN=<rhai-run> python3 rhai_equiv.py`).

## Result: side by side

Volume mm3 / area mm2 / bbox mm / faces. Equal = same bodies, volume and area within 1e-6 relative, same bbox and face count (the rule of `tools/parametric-verdict`).

| code | row | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec python | spec parametric | description same | equal |
|---|---|---|---|---|---|---|---|
| E-LB6TUU | short-6 | 1357.2 / 1074.4 / 16x12x12 / 4 | 1357.2 / 1074.4 / 16x12x12 / 4 | 10/10 | 10/10 | yes | yes |
| E-LB20TUU | short-20 | 17153.1 / 6697.9 / 35x32x32 / 4 | 17153.1 / 6697.9 / 35x32x32 / 4 | 10/10 | 10/10 | yes | yes |
| E-LB12DUU | medium-12 | 10879.6 / 5459.8 / 47x21x21 / 12 | 10879.6 / 5459.8 / 47x21x21 / 12 | 14/14 | 14/14 | yes | yes |
| E-LB30DMUU | medium-30 | 78885.9 / 23631.1 / 90x45x45 / 12 | 78885.9 / 23631.1 / 90x45x45 / 12 | 14/14 | 14/14 | yes | yes |
| E-LBF20LUU | flanged_long-round-20 | 49521.5 / 18161.2 / 80x54x54 / 18 | 49521.5 / 18161.2 / 80x54x54 / 18 | 15/15 | 15/15 | yes | yes |
| E-LBFZ10UU | flanged_long-round-10 | 10937.9 / 5760.7 / 29x40x40 / 18 | 10937.9 / 5760.7 / 29x40x40 / 18 | 15/15 | 15/15 | yes | yes |
| E-LBFM50UU | flanged_long-round-50 | 372113.8 / 60990.9 / 100x116x116 / 18 | 372113.8 / 60990.9 / 100x116x116 / 18 | 15/15 | 15/15 | yes | yes |
| E-LBK16LUU | flanged_long-square-16 | 32586.5 / 12655.2 / 70x48x48 / 25 | 32586.5 / 12655.2 / 70x48x48 / 25 | 16/16 | 16/16 | yes | yes |
| E-LBKZ6UU | flanged_long-square-6 | 2992.0 / 2430.3 / 19x28x28 / 25 | 2992.0 / 2430.3 / 19x28x28 / 25 | 16/16 | 16/16 | yes | yes |
| E-LBKM35LUU | flanged_long-square-35 | 172935.4 / 44686.3 / 135x82x82 / 25 | 172935.4 / 44686.3 / 135x82x82 / 25 | 16/16 | 16/16 | yes | yes |
| E-LBF25DUU | flanged_medium-round-25 | 76084.4 / 23145.4 / 83x62x62 / 18 | 76084.4 / 23145.4 / 83x62x62 / 18 | 15/15 | 15/15 | yes | yes |
| E-LBF20DUU | flanged_medium-round-20 | 42170.1 / 15710.8 / 65x54x54 / 18 | 42170.1 / 15710.8 / 65x54x54 / 18 | 15/15 | 15/15 | yes | yes |
| E-LBK12DMUU | flanged_medium-square-12 | 14118.5 / 7377.8 / 47x42x42 / 25 | 14118.5 / 7377.8 / 47x42x42 / 25 | 16/16 | 16/16 | yes | yes |
| E-LBH5UU | compact_long-compact-5 | 2125.1 / 1740.9 / 15x16x25 / 15 | 2125.1 / 1740.9 / 15x16x25 / 15 | 17/17 | 17/17 | yes | yes |
| E-LBH10LUU | compact_long-compact-10 | 14733.0 / 7238.5 / 55x25x40 / 15 | 14733.0 / 7238.5 / 55x25x40 / 15 | 17/17 | 17/17 | yes | yes |
| E-LBHZ20UU | compact_long-compact-20 | 27513.0 / 11038.3 / 42x38x54 / 21 | 27513.0 / 11038.3 / 42x38x54 / 21 | 17/17 | 17/17 | yes | yes |
| E-LBHM50LUU | compact_long-compact-50 | 637014.6 / 95808.1 / 192x90x116 / 21 | 637014.6 / 95808.1 / 192x90x116 / 21 | 17/17 | 17/17 | yes | yes |
| E-LBH16DUU | compact_medium-compact-16 | 27579.4 / 11003.1 / 56x34x48 / 21 | 27579.4 / 11003.1 / 56x34x48 / 21 | 17/17 | 17/17 | yes | yes |
| E-LBH30DMUU | compact_medium-compact-30 | 95256.5 / 28367.4 / 90x51x74 / 21 | 95256.5 / 28367.4 / 90x51x74 / 21 | 17/17 | 17/17 | yes | yes |
| E-LBFP20LUU | pilot_long-round-20 | 49521.5 / 18161.2 / 80x54x54 / 20 | 49521.5 / 18161.2 / 80x54x54 / 20 | 16/16 | 16/16 | yes | yes |
| E-LBFPM10UU | pilot_long-round-10 | 10937.9 / 5760.7 / 29x40x40 / 20 | 10937.9 / 5760.7 / 29x40x40 / 20 | 16/16 | 16/16 | yes | yes |
| E-LBFP30DMUU | pilot_medium-round-30 | 103773.1 / 30197.7 / 90x74x74 / 20 | 103773.1 / 30197.7 / 90x74x74 / 20 | 16/16 | 16/16 | yes | yes |
| E-LBKP6UU | pilot_long-square-6 | 2992.0 / 2430.3 / 19x28x28 / 27 | 2992.0 / 2430.3 / 19x28x28 / 27 | 17/17 | 17/17 | yes | yes |
| E-LBKPM40LUU | pilot_long-square-40 | 265956.7 / 58655.8 / 151x96x96 / 27 | 265956.7 / 58655.8 / 151x96x96 / 27 | 17/17 | 17/17 | yes | yes |
| E-LBKP12DMUU | pilot_medium-square-12 | 14118.5 / 7377.8 / 47x42x42 / 27 | 14118.5 / 7377.8 / 47x42x42 / 27 | 17/17 | 17/17 | yes | yes |
| E-LBHP16LUU | pilot_long-compact-16 | 33385.1 / 12938.3 / 70x34x48 / 23 | 33385.1 / 12938.3 / 70x34x48 / 23 | 18/18 | 18/18 | yes | yes |
| E-LBHPM8UU | pilot_long-compact-8 | 5039.5 / 3228.8 / 24x21x32 / 17 | 5039.5 / 3228.8 / 24x21x32 / 17 | 18/18 | 18/18 | yes | yes |
| E-LBHP25DMUU | pilot_medium-compact-25 | 72434.2 / 22169.0 / 83x46x62 / 23 | 72434.2 / 22169.0 / 83x46x62 / 23 | 18/18 | 18/18 | yes | yes |
| E-LBFC20LUU | center_long-round-20 | 49521.5 / 18161.2 / 80x54x54 / 20 | 49521.5 / 18161.2 / 80x54x54 / 20 | 17/17 | 17/17 | yes | yes |
| E-LBFCM40LUU | center_long-round-40 | 288296.1 / 62341.8 / 151x96x96 / 20 | 288296.1 / 62341.8 / 151x96x96 / 20 | 17/17 | 17/17 | yes | yes |
| E-LBFC30DMUU | center_medium-round-30 | 103773.1 / 30197.7 / 90x74x74 / 20 | 103773.1 / 30197.7 / 90x74x74 / 20 | 17/17 | 17/17 | yes | yes |
| E-LBKC12LUU | center_long-square-12 | 16451.1 / 8414.5 / 57x42x42 / 27 | 16451.1 / 8414.5 / 57x42x42 / 27 | 18/18 | 18/18 | yes | yes |
| E-LBKCM16LUU | center_long-square-16 | 32586.5 / 12655.2 / 70x48x48 / 27 | 32586.5 / 12655.2 / 70x48x48 / 27 | 18/18 | 18/18 | yes | yes |
| E-LBKC25DMUU | center_medium-square-25 | 71292.8 / 21865.4 / 83x62x62 / 27 | 71292.8 / 21865.4 / 83x62x62 / 27 | 18/18 | 18/18 | yes | yes |
| E-LBHC10LUU | center_long-compact-10 | 14733.0 / 7238.5 / 55x25x40 / 17 | 14733.0 / 7238.5 / 55x25x40 / 17 | 19/19 | 19/19 | yes | yes |
| E-LBHCM40LUU | center_long-compact-40 | 273038.7 / 59821.4 / 151x70x96 / 23 | 273038.7 / 59821.4 / 151x70x96 / 23 | 19/19 | 19/19 | yes | yes |
| E-LBHC6DMUU | center_medium-compact-6 | 4016.2 / 2858.5 / 29x18x28 / 17 | 4016.2 / 2858.5 / 29x18x28 / 17 | 19/19 | 19/19 | yes | yes |

Sweep of every other valid code of the generator: 443 codes, identical to the Python part 443/443, same spec check rows and all passed 443/443, same description 443/443.

| rejected code | python message | parametric message | same |
|---|---|---|---|
| E-LB25TUU | E-LB25TUU: the short straight bushing is offered for dr [6, 8, 10, 12, 13, 16, 20] (p.464) | E-LB25TUU: the short straight bushing is offered for dr [6, 8, 10, 12, 13, 16, 20] (p.464) | yes |
| E-LB10UU | E-LB is the straight bushing: its suffix is TUU (short), DUU or DMUU (medium), not UU | E-LB is the straight bushing: its suffix is TUU (short), DUU or DMUU (medium), not UU | yes |
| E-LBFZ40UU | E-LBFZ40: the opposite-counterbore type E-LBFZ is offered for dr 6-30; dr 35, 40, 50 only as E-LBF and E-LBFM (p.466 / p.468) | E-LBFZ40: the opposite-counterbore type E-LBFZ is offered for dr 6-30; dr 35, 40, 50 only as E-LBF and E-LBFM (p.466 / p.468) | yes |
| E-LBF10TUU | E-LBF has no short (TUU) version: flanged bushings end in UU / LUU (long) or DUU / DMUU (medium) | E-LBF has no short (TUU) version: flanged bushings end in UU / LUU (long) or DUU / DMUU (medium) | yes |
| E-LBFM20DUU | E-LBFM: the medium flanged bushing is ordered as E-LBF<dr>DUU, or E-LBF<dr>DMUU for electroless nickel plating (p.467 / p.469); the Z and M type letters belong to the UU / LUU bushings | E-LBFM: the medium flanged bushing is ordered as E-LBF<dr>DUU, or E-LBF<dr>DMUU for electroless nickel plating (p.467 / p.469); the Z and M type letters belong to the UU / LUU bushings | yes |
| E-LBK35DUU | E-LBK35DUU: the medium flanged bushing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] (p.467 / p.469) | E-LBK35DUU: the medium flanged bushing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] (p.467 / p.469) | yes |
| E-LBH5LUU | E-LBH5LUU: dr 5 is offered as a single bushing (UU) only (p.470) | E-LBH5LUU: dr 5 is offered as a single bushing (UU) only (p.470) | yes |
| E-LBHM5UU | E-LBHM5UU: dr 5 is offered only as the plain E-LBH5UU (p.470) | E-LBHM5UU: dr 5 is offered only as the plain E-LBH5UU (p.470) | yes |
| E-LBHZ35UU | E-LBHZ35UU: the opposite-counterbore type E-LBHZ is offered for dr 6-30 (p.470) | E-LBHZ35UU: the opposite-counterbore type E-LBHZ is offered for dr 6-30 (p.470) | yes |
| E-LBH13DUU | E-LBH13DUU: the medium compact flanged bushing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] (p.471) | E-LBH13DUU: the medium compact flanged bushing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] (p.471) | yes |
| E-LBHM20DUU | E-LBHM: the medium compact flanged bushing is ordered as E-LBH<dr>DUU, or E-LBH<dr>DMUU for electroless nickel plating (p.471); the Z and M type letters belong to the UU / LUU bushings | E-LBHM: the medium compact flanged bushing is ordered as E-LBH<dr>DUU, or E-LBH<dr>DMUU for electroless nickel plating (p.471); the Z and M type letters belong to the UU / LUU bushings | yes |
| E-LBH20TUU | E-LBH has no short (TUU) version | E-LBH has no short (TUU) version | yes |
| E-LBFP35UU | E-LBFP35UU: flanged bushings with pilot are offered for dr [6, 8, 10, 12, 16, 20, 25, 30, 40] (p.472) | E-LBFP35UU: flanged bushings with pilot are offered for dr [6, 8, 10, 12, 16, 20, 25, 30, 40] (p.472) | yes |
| E-LBFPM20DMUU | E-LBFPM: the medium bushing with pilot is ordered as E-LBFP<dr>DMUU only (the case is always nickel plated; no DUU, no M type letter on the medium series) | E-LBFPM: the medium bushing with pilot is ordered as E-LBFP<dr>DMUU only (the case is always nickel plated; no DUU, no M type letter on the medium series) | yes |
| E-LBKP20DUU | E-LBKP: the medium bushing with pilot is ordered as E-LBKP<dr>DMUU only (the case is always nickel plated; no DUU, no M type letter on the medium series) | E-LBKP: the medium bushing with pilot is ordered as E-LBKP<dr>DMUU only (the case is always nickel plated; no DUU, no M type letter on the medium series) | yes |
| E-LBFC20UU | E-LBFC: the centre flanged bushing is a double bushing: LUU (long) or DMUU (medium, plain type E-LBFC only), not UU | E-LBFC: the centre flanged bushing is a double bushing: LUU (long) or DMUU (medium, plain type E-LBFC only), not UU | yes |
| E-LBKCM20DMUU | E-LBKCM: the medium centre flanged bushing is ordered as E-LBKC<dr>DMUU (nickel plated by the DMUU suffix), not with the M type letter | E-LBKCM: the medium centre flanged bushing is ordered as E-LBKC<dr>DMUU (nickel plated by the DMUU suffix), not with the M type letter | yes |
| E-LBHC50LUU | E-LBHC50LUU: centre flanged bushings are offered for dr [6, 8, 10, 12, 16, 20, 25, 30, 40] (p.480) | E-LBHC50LUU: centre flanged bushings are offered for dr [6, 8, 10, 12, 16, 20, 25, 30, 40] (p.480) | yes |
| E-LBHS20UU | 'E-LBHS20UU': stainless steel linear bushings (representative type E-LBHS) are only mentioned on p.470; the catalogue prints no dimension table for them, so they are not covered | 'E-LBHS20UU': stainless steel linear bushings (representative type E-LBHS) are only mentioned on p.470; the catalogue prints no dimension table for them, so they are not covered | yes |
| E-LBFP13LUU | E-LBFP13LUU: flanged bushings with pilot are offered for dr [6, 8, 10, 12, 16, 20, 25, 30, 40] (p.472) | E-LBFP13LUU: flanged bushings with pilot are offered for dr [6, 8, 10, 12, 16, 20, 25, 30, 40] (p.472) | yes |
| E-LB10UU | E-LB is the straight bushing: its suffix is TUU (short), DUU or DMUU (medium), not UU | E-LB is the straight bushing: its suffix is TUU (short), DUU or DMUU (medium), not UU | yes |
| E-LBF10TUU | E-LBF has no short (TUU) version: flanged bushings end in UU / LUU (long) or DUU / DMUU (medium) | E-LBF has no short (TUU) version: flanged bushings end in UU / LUU (long) or DUU / DMUU (medium) | yes |
| E-LBF1UU | E-LBF1UU: flanged bushings are offered for dr [6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.466 / p.468) | E-LBF1UU: flanged bushings are offered for dr [6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.466 / p.468) | yes |
| E-LBF20DUU1 | 'E-LBF20DUU1': expected <type><dr><suffix>, type E-LB, E-LBF, E-LBFZ, E-LBFM, E-LBK, E-LBKZ or E-LBKM, suffix TUU (short), DUU / DMUU (medium) or UU / LUU (flanged single / double), e.g. E-LB10TUU, E-LBF20LUU; the compact, pilot and centre types add H, P and C: E-LBH, E-LBHZ, E-LBHM, E-LBFP, E-LBKPM, E-LBHC, ... | 'E-LBF20DUU1': expected <type><dr><suffix>, type E-LB, E-LBF, E-LBFZ, E-LBFM, E-LBK, E-LBKZ or E-LBKM, suffix TUU (short), DUU / DMUU (medium) or UU / LUU (flanged single / double), e.g. E-LB10TUU, E-LBF20LUU; the compact, pilot and centre types add H, P and C: E-LBH, E-LBHZ, E-LBHM, E-LBFP, E-LBKPM, E-LBHC, ... | yes |
| E-LBF14LUU | E-LBF14LUU: flanged bushings are offered for dr [6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.466 / p.468) | E-LBF14LUU: flanged bushings are offered for dr [6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.466 / p.468) | yes |
| E-LBFM20DUU | E-LBFM: the medium flanged bushing is ordered as E-LBF<dr>DUU, or E-LBF<dr>DMUU for electroless nickel plating (p.467 / p.469); the Z and M type letters belong to the UU / LUU bushings | E-LBFM: the medium flanged bushing is ordered as E-LBF<dr>DUU, or E-LBF<dr>DMUU for electroless nickel plating (p.467 / p.469); the Z and M type letters belong to the UU / LUU bushings | yes |
| E-LBFZ40UU | E-LBFZ40: the opposite-counterbore type E-LBFZ is offered for dr 6-30; dr 35, 40, 50 only as E-LBF and E-LBFM (p.466 / p.468) | E-LBFZ40: the opposite-counterbore type E-LBFZ is offered for dr 6-30; dr 35, 40, 50 only as E-LBF and E-LBFM (p.466 / p.468) | yes |
| E-LBFZ35LUU | E-LBFZ35: the opposite-counterbore type E-LBFZ is offered for dr 6-30; dr 35, 40, 50 only as E-LBF and E-LBFM (p.466 / p.468) | E-LBFZ35: the opposite-counterbore type E-LBFZ is offered for dr 6-30; dr 35, 40, 50 only as E-LBF and E-LBFM (p.466 / p.468) | yes |
| E-LBK35DUU | E-LBK35DUU: the medium flanged bushing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] (p.467 / p.469) | E-LBK35DUU: the medium flanged bushing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] (p.467 / p.469) | yes |
| E-LB26DUU | E-LB26DUU: the medium straight bushing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] (p.465) | E-LB26DUU: the medium straight bushing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] (p.465) | yes |
| E-LBS10UU | 'E-LBS10UU': stainless steel linear bushings (representative type E-LBHS) are only mentioned on p.470; the catalogue prints no dimension table for them, so they are not covered | 'E-LBS10UU': stainless steel linear bushings (representative type E-LBHS) are only mentioned on p.470; the catalogue prints no dimension table for them, so they are not covered | yes |
| E-LBHS20UU | 'E-LBHS20UU': stainless steel linear bushings (representative type E-LBHS) are only mentioned on p.470; the catalogue prints no dimension table for them, so they are not covered | 'E-LBHS20UU': stainless steel linear bushings (representative type E-LBHS) are only mentioned on p.470; the catalogue prints no dimension table for them, so they are not covered | yes |
| E-LBFS5UU | 'E-LBFS5UU': stainless steel linear bushings (representative type E-LBHS) are only mentioned on p.470; the catalogue prints no dimension table for them, so they are not covered | 'E-LBFS5UU': stainless steel linear bushings (representative type E-LBHS) are only mentioned on p.470; the catalogue prints no dimension table for them, so they are not covered | yes |
| E-LB | 'E-LB': expected <type><dr><suffix>, type E-LB, E-LBF, E-LBFZ, E-LBFM, E-LBK, E-LBKZ or E-LBKM, suffix TUU (short), DUU / DMUU (medium) or UU / LUU (flanged single / double), e.g. E-LB10TUU, E-LBF20LUU; the compact, pilot and centre types add H, P and C: E-LBH, E-LBHZ, E-LBHM, E-LBFP, E-LBKPM, E-LBHC, ... | 'E-LB': expected <type><dr><suffix>, type E-LB, E-LBF, E-LBFZ, E-LBFM, E-LBK, E-LBKZ or E-LBKM, suffix TUU (short), DUU / DMUU (medium) or UU / LUU (flanged single / double), e.g. E-LB10TUU, E-LBF20LUU; the compact, pilot and centre types add H, P and C: E-LBH, E-LBHZ, E-LBHM, E-LBFP, E-LBKPM, E-LBHC, ... | yes |
| E-LBX10UU | 'E-LBX10UU': expected <type><dr><suffix>, type E-LB, E-LBF, E-LBFZ, E-LBFM, E-LBK, E-LBKZ or E-LBKM, suffix TUU (short), DUU / DMUU (medium) or UU / LUU (flanged single / double), e.g. E-LB10TUU, E-LBF20LUU; the compact, pilot and centre types add H, P and C: E-LBH, E-LBHZ, E-LBHM, E-LBFP, E-LBKPM, E-LBHC, ... | 'E-LBX10UU': expected <type><dr><suffix>, type E-LB, E-LBF, E-LBFZ, E-LBFM, E-LBK, E-LBKZ or E-LBKM, suffix TUU (short), DUU / DMUU (medium) or UU / LUU (flanged single / double), e.g. E-LB10TUU, E-LBF20LUU; the compact, pilot and centre types add H, P and C: E-LBH, E-LBHZ, E-LBHM, E-LBFP, E-LBKPM, E-LBHC, ... | yes |
| E-LBHZ40UU | E-LBHZ40UU: the opposite-counterbore type E-LBHZ is offered for dr 6-30 (p.470) | E-LBHZ40UU: the opposite-counterbore type E-LBHZ is offered for dr 6-30 (p.470) | yes |
| E-LBHM20DUU | E-LBHM: the medium compact flanged bushing is ordered as E-LBH<dr>DUU, or E-LBH<dr>DMUU for electroless nickel plating (p.471); the Z and M type letters belong to the UU / LUU bushings | E-LBHM: the medium compact flanged bushing is ordered as E-LBH<dr>DUU, or E-LBH<dr>DMUU for electroless nickel plating (p.471); the Z and M type letters belong to the UU / LUU bushings | yes |
| E-LBH13DUU | E-LBH13DUU: the medium compact flanged bushing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] (p.471) | E-LBH13DUU: the medium compact flanged bushing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] (p.471) | yes |
| E-LBH5LUU | E-LBH5LUU: dr 5 is offered as a single bushing (UU) only (p.470) | E-LBH5LUU: dr 5 is offered as a single bushing (UU) only (p.470) | yes |
| E-LBHM5UU | E-LBHM5UU: dr 5 is offered only as the plain E-LBH5UU (p.470) | E-LBHM5UU: dr 5 is offered only as the plain E-LBH5UU (p.470) | yes |
| E-LBH20TUU | E-LBH has no short (TUU) version | E-LBH has no short (TUU) version | yes |
| E-LBFP35UU | E-LBFP35UU: flanged bushings with pilot are offered for dr [6, 8, 10, 12, 16, 20, 25, 30, 40] (p.472) | E-LBFP35UU: flanged bushings with pilot are offered for dr [6, 8, 10, 12, 16, 20, 25, 30, 40] (p.472) | yes |
| E-LBFP6DUU | E-LBFP: the medium bushing with pilot is ordered as E-LBFP<dr>DMUU only (the case is always nickel plated; no DUU, no M type letter on the medium series) | E-LBFP: the medium bushing with pilot is ordered as E-LBFP<dr>DMUU only (the case is always nickel plated; no DUU, no M type letter on the medium series) | yes |
| E-LBFPM20DMUU | E-LBFPM: the medium bushing with pilot is ordered as E-LBFP<dr>DMUU only (the case is always nickel plated; no DUU, no M type letter on the medium series) | E-LBFPM: the medium bushing with pilot is ordered as E-LBFP<dr>DMUU only (the case is always nickel plated; no DUU, no M type letter on the medium series) | yes |
| E-LBKP20DUU | E-LBKP: the medium bushing with pilot is ordered as E-LBKP<dr>DMUU only (the case is always nickel plated; no DUU, no M type letter on the medium series) | E-LBKP: the medium bushing with pilot is ordered as E-LBKP<dr>DMUU only (the case is always nickel plated; no DUU, no M type letter on the medium series) | yes |
| E-LBHPM20DMUU | E-LBHPM: the medium bushing with pilot is ordered as E-LBHP<dr>DMUU only (the case is always nickel plated; no DUU, no M type letter on the medium series) | E-LBHPM: the medium bushing with pilot is ordered as E-LBHP<dr>DMUU only (the case is always nickel plated; no DUU, no M type letter on the medium series) | yes |
| E-LBFC20UU | E-LBFC: the centre flanged bushing is a double bushing: LUU (long) or DMUU (medium, plain type E-LBFC only), not UU | E-LBFC: the centre flanged bushing is a double bushing: LUU (long) or DMUU (medium, plain type E-LBFC only), not UU | yes |
| E-LBKC20DUU | E-LBKC: the centre flanged bushing is a double bushing: LUU (long) or DMUU (medium, plain type E-LBKC only), not DUU | E-LBKC: the centre flanged bushing is a double bushing: LUU (long) or DMUU (medium, plain type E-LBKC only), not DUU | yes |
| E-LBKCM20DMUU | E-LBKCM: the medium centre flanged bushing is ordered as E-LBKC<dr>DMUU (nickel plated by the DMUU suffix), not with the M type letter | E-LBKCM: the medium centre flanged bushing is ordered as E-LBKC<dr>DMUU (nickel plated by the DMUU suffix), not with the M type letter | yes |
| E-LBHC50LUU | E-LBHC50LUU: centre flanged bushings are offered for dr [6, 8, 10, 12, 16, 20, 25, 30, 40] (p.480) | E-LBHC50LUU: centre flanged bushings are offered for dr [6, 8, 10, 12, 16, 20, 25, 30, 40] (p.480) | yes |
| E-LBFC13LUU | E-LBFC13LUU: centre flanged bushings are offered for dr [6, 8, 10, 12, 16, 20, 25, 30, 40] (p.478) | E-LBFC13LUU: centre flanged bushings are offered for dr [6, 8, 10, 12, 16, 20, 25, 30, 40] (p.478) | yes |
| E-LBFC35DMUU | E-LBFC35DMUU: the medium centre flanged bushing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] (p.478) | E-LBFC35DMUU: the medium centre flanged bushing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] (p.478) | yes |
| E-LBHP13LUU | E-LBHP13LUU: flanged bushings with pilot are offered for dr [6, 8, 10, 12, 16, 20, 25, 30, 40] (p.476) | E-LBHP13LUU: flanged bushings with pilot are offered for dr [6, 8, 10, 12, 16, 20, 25, 30, 40] (p.476) | yes |
| E-LBHP50DMUU | E-LBHP50DMUU: the medium bushing with pilot is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] (p.477) | E-LBHP50DMUU: the medium bushing with pilot is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] (p.477) | yes |
| E-LBK20TUU | E-LBK has no short (TUU) version: flanged bushings end in UU / LUU (long) or DUU / DMUU (medium) | E-LBK has no short (TUU) version: flanged bushings end in UU / LUU (long) or DUU / DMUU (medium) | yes |

| built | changed | to | changed in place vol / area / bbox / faces | direct code (inserted) | python | equal |
|---|---|---|---|---|---|---|
| E-LBF20UU | blen | E-LBF20LUU | 49521.5 / 18161.2 / 80x54x54 / 18 | 49521.5 / 18161.2 / 80x54x54 / 18 | 49521.5 / 18161.2 / 80x54x54 / 18 | yes |
| E-LBK16UU | blen | E-LBK16LUU | 32586.5 / 12655.2 / 70x48x48 / 25 | 32586.5 / 12655.2 / 70x48x48 / 25 | 32586.5 / 12655.2 / 70x48x48 / 25 | yes |
| E-LBHP16UU | blen | E-LBHP16LUU | 33385.1 / 12938.3 / 70x34x48 / 23 | 33385.1 / 12938.3 / 70x34x48 / 23 | 33385.1 / 12938.3 / 70x34x48 / 23 | yes |
| E-LBH10UU | blen | E-LBH10LUU | 14733.0 / 7238.5 / 55x25x40 / 15 | 14733.0 / 7238.5 / 55x25x40 / 15 | 14733.0 / 7238.5 / 55x25x40 / 15 | yes |
| E-LBF10UU | opp | E-LBFZ10UU | 10937.9 / 5760.7 / 29x40x40 / 18 | 10937.9 / 5760.7 / 29x40x40 / 18 | 10937.9 / 5760.7 / 29x40x40 / 18 | yes |
| E-LBHZ20UU | opp | E-LBH20UU | 27513.0 / 11038.3 / 42x38x54 / 21 | 27513.0 / 11038.3 / 42x38x54 / 21 | 27513.0 / 11038.3 / 42x38x54 / 21 | yes |
| E-LBK12DUU | plated | E-LBK12DMUU | 14118.5 / 7377.8 / 47x42x42 / 25 | 14118.5 / 7377.8 / 47x42x42 / 25 | 14118.5 / 7377.8 / 47x42x42 / 25 | yes |
| E-LB12DUU | plated | E-LB12DMUU | 10879.6 / 5459.8 / 47x21x21 / 12 | 10879.6 / 5459.8 / 47x21x21 / 12 | 10879.6 / 5459.8 / 47x21x21 / 12 | yes |

| round trip | printed | same configuration and parameters |
|---|---|---|
| E-LB6TUU | E-LB6TUU | yes |
| E-LB20TUU | E-LB20TUU | yes |
| E-LB12DUU | E-LB12DUU | yes |
| E-LB30DMUU | E-LB30DMUU | yes |
| E-LBF20LUU | E-LBF20LUU | yes |
| E-LBFZ10UU | E-LBFZ10UU | yes |
| E-LBFM50UU | E-LBFM50UU | yes |
| E-LBK16LUU | E-LBK16LUU | yes |
| E-LBKZ6UU | E-LBKZ6UU | yes |
| E-LBKM35LUU | E-LBKM35LUU | yes |
| E-LBF25DUU | E-LBF25DUU | yes |
| E-LBF20DUU | E-LBF20DUU | yes |
| E-LBK12DMUU | E-LBK12DMUU | yes |
| E-LBH5UU | E-LBH5UU | yes |
| E-LBH10LUU | E-LBH10LUU | yes |
| E-LBHZ20UU | E-LBHZ20UU | yes |
| E-LBHM50LUU | E-LBHM50LUU | yes |
| E-LBH16DUU | E-LBH16DUU | yes |
| E-LBH30DMUU | E-LBH30DMUU | yes |
| E-LBFP20LUU | E-LBFP20LUU | yes |
| E-LBFPM10UU | E-LBFPM10UU | yes |
| E-LBFP30DMUU | E-LBFP30DMUU | yes |
| E-LBKP6UU | E-LBKP6UU | yes |
| E-LBKPM40LUU | E-LBKPM40LUU | yes |
| E-LBKP12DMUU | E-LBKP12DMUU | yes |
| E-LBHP16LUU | E-LBHP16LUU | yes |
| E-LBHPM8UU | E-LBHPM8UU | yes |
| E-LBHP25DMUU | E-LBHP25DMUU | yes |
| E-LBFC20LUU | E-LBFC20LUU | yes |
| E-LBFCM40LUU | E-LBFCM40LUU | yes |
| E-LBFC30DMUU | E-LBFC30DMUU | yes |
| E-LBKC12LUU | E-LBKC12LUU | yes |
| E-LBKCM16LUU | E-LBKCM16LUU | yes |
| E-LBKC25DMUU | E-LBKC25DMUU | yes |
| E-LBHC10LUU | E-LBHC10LUU | yes |
| E-LBHCM40LUU | E-LBHCM40LUU | yes |
| E-LBHC6DMUU | E-LBHC6DMUU | yes |
| E-LB6DMUU | E-LB6DMUU | yes |
| E-LB6DUU | E-LB6DUU | yes |
| E-LB8TUU | E-LB8TUU | yes |
| E-LB8DMUU | E-LB8DMUU | yes |
| E-LB8DUU | E-LB8DUU | yes |
| E-LB10TUU | E-LB10TUU | yes |
| E-LB10DMUU | E-LB10DMUU | yes |
| E-LB10DUU | E-LB10DUU | yes |
| E-LB12TUU | E-LB12TUU | yes |
| E-LB12DMUU | E-LB12DMUU | yes |
| E-LB13TUU | E-LB13TUU | yes |
| E-LB16TUU | E-LB16TUU | yes |
| E-LB16DMUU | E-LB16DMUU | yes |
| E-LB16DUU | E-LB16DUU | yes |
| E-LB20DMUU | E-LB20DMUU | yes |
| E-LB20DUU | E-LB20DUU | yes |
| E-LB25DMUU | E-LB25DMUU | yes |
| E-LB25DUU | E-LB25DUU | yes |
| E-LB30DUU | E-LB30DUU | yes |
| E-LBF6DMUU | E-LBF6DMUU | yes |
| E-LBF6DUU | E-LBF6DUU | yes |
| E-LBF6LUU | E-LBF6LUU | yes |
| E-LBF6UU | E-LBF6UU | yes |
| E-LBF8DMUU | E-LBF8DMUU | yes |
| E-LBF8DUU | E-LBF8DUU | yes |
| E-LBF8LUU | E-LBF8LUU | yes |
| E-LBF8UU | E-LBF8UU | yes |
| E-LBF10DMUU | E-LBF10DMUU | yes |
| E-LBF10DUU | E-LBF10DUU | yes |
| E-LBF10LUU | E-LBF10LUU | yes |
| E-LBF10UU | E-LBF10UU | yes |
| E-LBF12DMUU | E-LBF12DMUU | yes |
| E-LBF12DUU | E-LBF12DUU | yes |
| E-LBF12LUU | E-LBF12LUU | yes |
| E-LBF12UU | E-LBF12UU | yes |
| E-LBF13LUU | E-LBF13LUU | yes |
| E-LBF13UU | E-LBF13UU | yes |
| E-LBF16DMUU | E-LBF16DMUU | yes |
| E-LBF16DUU | E-LBF16DUU | yes |
| E-LBF16LUU | E-LBF16LUU | yes |
| E-LBF16UU | E-LBF16UU | yes |
| E-LBF20DMUU | E-LBF20DMUU | yes |
| E-LBF20UU | E-LBF20UU | yes |
| E-LBF25DMUU | E-LBF25DMUU | yes |
| E-LBF25LUU | E-LBF25LUU | yes |
| E-LBF25UU | E-LBF25UU | yes |
| E-LBF30DMUU | E-LBF30DMUU | yes |
| E-LBF30DUU | E-LBF30DUU | yes |
| E-LBF30LUU | E-LBF30LUU | yes |
| E-LBF30UU | E-LBF30UU | yes |
| E-LBF35LUU | E-LBF35LUU | yes |
| E-LBF35UU | E-LBF35UU | yes |
| E-LBF40LUU | E-LBF40LUU | yes |
| E-LBF40UU | E-LBF40UU | yes |
| E-LBF50LUU | E-LBF50LUU | yes |
| E-LBF50UU | E-LBF50UU | yes |
| E-LBFZ6LUU | E-LBFZ6LUU | yes |
| E-LBFZ6UU | E-LBFZ6UU | yes |
| E-LBFZ8LUU | E-LBFZ8LUU | yes |
| E-LBFZ8UU | E-LBFZ8UU | yes |
| E-LBFZ10LUU | E-LBFZ10LUU | yes |
| E-LBFZ12LUU | E-LBFZ12LUU | yes |
| E-LBFZ12UU | E-LBFZ12UU | yes |
| E-LBFZ13LUU | E-LBFZ13LUU | yes |
| E-LBFZ13UU | E-LBFZ13UU | yes |
| E-LBFZ16LUU | E-LBFZ16LUU | yes |
| E-LBFZ16UU | E-LBFZ16UU | yes |
| E-LBFZ20LUU | E-LBFZ20LUU | yes |
| E-LBFZ20UU | E-LBFZ20UU | yes |
| E-LBFZ25LUU | E-LBFZ25LUU | yes |
| E-LBFZ25UU | E-LBFZ25UU | yes |
| E-LBFZ30LUU | E-LBFZ30LUU | yes |
| E-LBFZ30UU | E-LBFZ30UU | yes |
| E-LBFM6LUU | E-LBFM6LUU | yes |
| E-LBFM6UU | E-LBFM6UU | yes |
| E-LBFM8LUU | E-LBFM8LUU | yes |
| E-LBFM8UU | E-LBFM8UU | yes |
| E-LBFM10LUU | E-LBFM10LUU | yes |
| E-LBFM10UU | E-LBFM10UU | yes |
| E-LBFM12LUU | E-LBFM12LUU | yes |
| E-LBFM12UU | E-LBFM12UU | yes |
| E-LBFM13LUU | E-LBFM13LUU | yes |
| E-LBFM13UU | E-LBFM13UU | yes |
| E-LBFM16LUU | E-LBFM16LUU | yes |
| E-LBFM16UU | E-LBFM16UU | yes |
| E-LBFM20LUU | E-LBFM20LUU | yes |
| E-LBFM20UU | E-LBFM20UU | yes |
| E-LBFM25LUU | E-LBFM25LUU | yes |
| E-LBFM25UU | E-LBFM25UU | yes |
| E-LBFM30LUU | E-LBFM30LUU | yes |
| E-LBFM30UU | E-LBFM30UU | yes |
| E-LBFM35LUU | E-LBFM35LUU | yes |
| E-LBFM35UU | E-LBFM35UU | yes |
| E-LBFM40LUU | E-LBFM40LUU | yes |
| E-LBFM40UU | E-LBFM40UU | yes |
| E-LBFM50LUU | E-LBFM50LUU | yes |
| E-LBK6DMUU | E-LBK6DMUU | yes |
| E-LBK6DUU | E-LBK6DUU | yes |
| E-LBK6LUU | E-LBK6LUU | yes |
| E-LBK6UU | E-LBK6UU | yes |
| E-LBK8DMUU | E-LBK8DMUU | yes |
| E-LBK8DUU | E-LBK8DUU | yes |
| E-LBK8LUU | E-LBK8LUU | yes |
| E-LBK8UU | E-LBK8UU | yes |
| E-LBK10DMUU | E-LBK10DMUU | yes |
| E-LBK10DUU | E-LBK10DUU | yes |
| E-LBK10LUU | E-LBK10LUU | yes |
| E-LBK10UU | E-LBK10UU | yes |
| E-LBK12DUU | E-LBK12DUU | yes |
| E-LBK12LUU | E-LBK12LUU | yes |
| E-LBK12UU | E-LBK12UU | yes |
| E-LBK13LUU | E-LBK13LUU | yes |
| E-LBK13UU | E-LBK13UU | yes |
| E-LBK16DMUU | E-LBK16DMUU | yes |
| E-LBK16DUU | E-LBK16DUU | yes |
| E-LBK16UU | E-LBK16UU | yes |
| E-LBK20DMUU | E-LBK20DMUU | yes |
| E-LBK20DUU | E-LBK20DUU | yes |
| E-LBK20LUU | E-LBK20LUU | yes |
| E-LBK20UU | E-LBK20UU | yes |
| E-LBK25DMUU | E-LBK25DMUU | yes |
| E-LBK25DUU | E-LBK25DUU | yes |
| E-LBK25LUU | E-LBK25LUU | yes |
| E-LBK25UU | E-LBK25UU | yes |
| E-LBK30DMUU | E-LBK30DMUU | yes |
| E-LBK30DUU | E-LBK30DUU | yes |
| E-LBK30LUU | E-LBK30LUU | yes |
| E-LBK30UU | E-LBK30UU | yes |
| E-LBK35LUU | E-LBK35LUU | yes |
| E-LBK35UU | E-LBK35UU | yes |
| E-LBK40LUU | E-LBK40LUU | yes |
| E-LBK40UU | E-LBK40UU | yes |
| E-LBK50LUU | E-LBK50LUU | yes |
| E-LBK50UU | E-LBK50UU | yes |
| E-LBKZ6LUU | E-LBKZ6LUU | yes |
| E-LBKZ8LUU | E-LBKZ8LUU | yes |
| E-LBKZ8UU | E-LBKZ8UU | yes |
| E-LBKZ10LUU | E-LBKZ10LUU | yes |
| E-LBKZ10UU | E-LBKZ10UU | yes |
| E-LBKZ12LUU | E-LBKZ12LUU | yes |
| E-LBKZ12UU | E-LBKZ12UU | yes |
| E-LBKZ13LUU | E-LBKZ13LUU | yes |
| E-LBKZ13UU | E-LBKZ13UU | yes |
| E-LBKZ16LUU | E-LBKZ16LUU | yes |
| E-LBKZ16UU | E-LBKZ16UU | yes |
| E-LBKZ20LUU | E-LBKZ20LUU | yes |
| E-LBKZ20UU | E-LBKZ20UU | yes |
| E-LBKZ25LUU | E-LBKZ25LUU | yes |
| E-LBKZ25UU | E-LBKZ25UU | yes |
| E-LBKZ30LUU | E-LBKZ30LUU | yes |
| E-LBKZ30UU | E-LBKZ30UU | yes |
| E-LBKM6LUU | E-LBKM6LUU | yes |
| E-LBKM6UU | E-LBKM6UU | yes |
| E-LBKM8LUU | E-LBKM8LUU | yes |
| E-LBKM8UU | E-LBKM8UU | yes |
| E-LBKM10LUU | E-LBKM10LUU | yes |
| E-LBKM10UU | E-LBKM10UU | yes |
| E-LBKM12LUU | E-LBKM12LUU | yes |
| E-LBKM12UU | E-LBKM12UU | yes |
| E-LBKM13LUU | E-LBKM13LUU | yes |
| E-LBKM13UU | E-LBKM13UU | yes |
| E-LBKM16LUU | E-LBKM16LUU | yes |
| E-LBKM16UU | E-LBKM16UU | yes |
| E-LBKM20LUU | E-LBKM20LUU | yes |
| E-LBKM20UU | E-LBKM20UU | yes |
| E-LBKM25LUU | E-LBKM25LUU | yes |
| E-LBKM25UU | E-LBKM25UU | yes |
| E-LBKM30LUU | E-LBKM30LUU | yes |
| E-LBKM30UU | E-LBKM30UU | yes |
| E-LBKM35UU | E-LBKM35UU | yes |
| E-LBKM40LUU | E-LBKM40LUU | yes |
| E-LBKM40UU | E-LBKM40UU | yes |
| E-LBKM50LUU | E-LBKM50LUU | yes |
| E-LBKM50UU | E-LBKM50UU | yes |
| E-LBH6DMUU | E-LBH6DMUU | yes |
| E-LBH6DUU | E-LBH6DUU | yes |
| E-LBH6LUU | E-LBH6LUU | yes |
| E-LBH6UU | E-LBH6UU | yes |
| E-LBH8DMUU | E-LBH8DMUU | yes |
| E-LBH8DUU | E-LBH8DUU | yes |
| E-LBH8LUU | E-LBH8LUU | yes |
| E-LBH8UU | E-LBH8UU | yes |
| E-LBH10DMUU | E-LBH10DMUU | yes |
| E-LBH10DUU | E-LBH10DUU | yes |
| E-LBH10UU | E-LBH10UU | yes |
| E-LBH12DMUU | E-LBH12DMUU | yes |
| E-LBH12DUU | E-LBH12DUU | yes |
| E-LBH12LUU | E-LBH12LUU | yes |
| E-LBH12UU | E-LBH12UU | yes |
| E-LBH13LUU | E-LBH13LUU | yes |
| E-LBH13UU | E-LBH13UU | yes |
| E-LBH16DMUU | E-LBH16DMUU | yes |
| E-LBH16LUU | E-LBH16LUU | yes |
| E-LBH16UU | E-LBH16UU | yes |
| E-LBH20DMUU | E-LBH20DMUU | yes |
| E-LBH20DUU | E-LBH20DUU | yes |
| E-LBH20LUU | E-LBH20LUU | yes |
| E-LBH20UU | E-LBH20UU | yes |
| E-LBH25DMUU | E-LBH25DMUU | yes |
| E-LBH25DUU | E-LBH25DUU | yes |
| E-LBH25LUU | E-LBH25LUU | yes |
| E-LBH25UU | E-LBH25UU | yes |
| E-LBH30DUU | E-LBH30DUU | yes |
| E-LBH30LUU | E-LBH30LUU | yes |
| E-LBH30UU | E-LBH30UU | yes |
| E-LBH35LUU | E-LBH35LUU | yes |
| E-LBH35UU | E-LBH35UU | yes |
| E-LBH40LUU | E-LBH40LUU | yes |
| E-LBH40UU | E-LBH40UU | yes |
| E-LBH50LUU | E-LBH50LUU | yes |
| E-LBH50UU | E-LBH50UU | yes |
| E-LBHZ6LUU | E-LBHZ6LUU | yes |
| E-LBHZ6UU | E-LBHZ6UU | yes |
| E-LBHZ8LUU | E-LBHZ8LUU | yes |
| E-LBHZ8UU | E-LBHZ8UU | yes |
| E-LBHZ10LUU | E-LBHZ10LUU | yes |
| E-LBHZ10UU | E-LBHZ10UU | yes |
| E-LBHZ12LUU | E-LBHZ12LUU | yes |
| E-LBHZ12UU | E-LBHZ12UU | yes |
| E-LBHZ13LUU | E-LBHZ13LUU | yes |
| E-LBHZ13UU | E-LBHZ13UU | yes |
| E-LBHZ16LUU | E-LBHZ16LUU | yes |
| E-LBHZ16UU | E-LBHZ16UU | yes |
| E-LBHZ20LUU | E-LBHZ20LUU | yes |
| E-LBHZ25LUU | E-LBHZ25LUU | yes |
| E-LBHZ25UU | E-LBHZ25UU | yes |
| E-LBHZ30LUU | E-LBHZ30LUU | yes |
| E-LBHZ30UU | E-LBHZ30UU | yes |
| E-LBHM6LUU | E-LBHM6LUU | yes |
| E-LBHM6UU | E-LBHM6UU | yes |
| E-LBHM8LUU | E-LBHM8LUU | yes |
| E-LBHM8UU | E-LBHM8UU | yes |
| E-LBHM10LUU | E-LBHM10LUU | yes |
| E-LBHM10UU | E-LBHM10UU | yes |
| E-LBHM12LUU | E-LBHM12LUU | yes |
| E-LBHM12UU | E-LBHM12UU | yes |
| E-LBHM13LUU | E-LBHM13LUU | yes |
| E-LBHM13UU | E-LBHM13UU | yes |
| E-LBHM16LUU | E-LBHM16LUU | yes |
| E-LBHM16UU | E-LBHM16UU | yes |
| E-LBHM20LUU | E-LBHM20LUU | yes |
| E-LBHM20UU | E-LBHM20UU | yes |
| E-LBHM25LUU | E-LBHM25LUU | yes |
| E-LBHM25UU | E-LBHM25UU | yes |
| E-LBHM30LUU | E-LBHM30LUU | yes |
| E-LBHM30UU | E-LBHM30UU | yes |
| E-LBHM35LUU | E-LBHM35LUU | yes |
| E-LBHM35UU | E-LBHM35UU | yes |
| E-LBHM40LUU | E-LBHM40LUU | yes |
| E-LBHM40UU | E-LBHM40UU | yes |
| E-LBHM50UU | E-LBHM50UU | yes |
| E-LBFP6DMUU | E-LBFP6DMUU | yes |
| E-LBFP6LUU | E-LBFP6LUU | yes |
| E-LBFP6UU | E-LBFP6UU | yes |
| E-LBFP8DMUU | E-LBFP8DMUU | yes |
| E-LBFP8LUU | E-LBFP8LUU | yes |
| E-LBFP8UU | E-LBFP8UU | yes |
| E-LBFP10DMUU | E-LBFP10DMUU | yes |
| E-LBFP10LUU | E-LBFP10LUU | yes |
| E-LBFP10UU | E-LBFP10UU | yes |
| E-LBFP12DMUU | E-LBFP12DMUU | yes |
| E-LBFP12LUU | E-LBFP12LUU | yes |
| E-LBFP12UU | E-LBFP12UU | yes |
| E-LBFP16DMUU | E-LBFP16DMUU | yes |
| E-LBFP16LUU | E-LBFP16LUU | yes |
| E-LBFP16UU | E-LBFP16UU | yes |
| E-LBFP20DMUU | E-LBFP20DMUU | yes |
| E-LBFP20UU | E-LBFP20UU | yes |
| E-LBFP25DMUU | E-LBFP25DMUU | yes |
| E-LBFP25LUU | E-LBFP25LUU | yes |
| E-LBFP25UU | E-LBFP25UU | yes |
| E-LBFP30LUU | E-LBFP30LUU | yes |
| E-LBFP30UU | E-LBFP30UU | yes |
| E-LBFP40LUU | E-LBFP40LUU | yes |
| E-LBFP40UU | E-LBFP40UU | yes |
| E-LBFPM6LUU | E-LBFPM6LUU | yes |
| E-LBFPM6UU | E-LBFPM6UU | yes |
| E-LBFPM8LUU | E-LBFPM8LUU | yes |
| E-LBFPM8UU | E-LBFPM8UU | yes |
| E-LBFPM10LUU | E-LBFPM10LUU | yes |
| E-LBFPM12LUU | E-LBFPM12LUU | yes |
| E-LBFPM12UU | E-LBFPM12UU | yes |
| E-LBFPM16LUU | E-LBFPM16LUU | yes |
| E-LBFPM16UU | E-LBFPM16UU | yes |
| E-LBFPM20LUU | E-LBFPM20LUU | yes |
| E-LBFPM20UU | E-LBFPM20UU | yes |
| E-LBFPM25LUU | E-LBFPM25LUU | yes |
| E-LBFPM25UU | E-LBFPM25UU | yes |
| E-LBFPM30LUU | E-LBFPM30LUU | yes |
| E-LBFPM30UU | E-LBFPM30UU | yes |
| E-LBFPM40LUU | E-LBFPM40LUU | yes |
| E-LBFPM40UU | E-LBFPM40UU | yes |
| E-LBKP6DMUU | E-LBKP6DMUU | yes |
| E-LBKP6LUU | E-LBKP6LUU | yes |
| E-LBKP8DMUU | E-LBKP8DMUU | yes |
| E-LBKP8LUU | E-LBKP8LUU | yes |
| E-LBKP8UU | E-LBKP8UU | yes |
| E-LBKP10DMUU | E-LBKP10DMUU | yes |
| E-LBKP10LUU | E-LBKP10LUU | yes |
| E-LBKP10UU | E-LBKP10UU | yes |
| E-LBKP12LUU | E-LBKP12LUU | yes |
| E-LBKP12UU | E-LBKP12UU | yes |
| E-LBKP16DMUU | E-LBKP16DMUU | yes |
| E-LBKP16LUU | E-LBKP16LUU | yes |
| E-LBKP16UU | E-LBKP16UU | yes |
| E-LBKP20DMUU | E-LBKP20DMUU | yes |
| E-LBKP20LUU | E-LBKP20LUU | yes |
| E-LBKP20UU | E-LBKP20UU | yes |
| E-LBKP25DMUU | E-LBKP25DMUU | yes |
| E-LBKP25LUU | E-LBKP25LUU | yes |
| E-LBKP25UU | E-LBKP25UU | yes |
| E-LBKP30DMUU | E-LBKP30DMUU | yes |
| E-LBKP30LUU | E-LBKP30LUU | yes |
| E-LBKP30UU | E-LBKP30UU | yes |
| E-LBKP40LUU | E-LBKP40LUU | yes |
| E-LBKP40UU | E-LBKP40UU | yes |
| E-LBKPM6LUU | E-LBKPM6LUU | yes |
| E-LBKPM6UU | E-LBKPM6UU | yes |
| E-LBKPM8LUU | E-LBKPM8LUU | yes |
| E-LBKPM8UU | E-LBKPM8UU | yes |
| E-LBKPM10LUU | E-LBKPM10LUU | yes |
| E-LBKPM10UU | E-LBKPM10UU | yes |
| E-LBKPM12LUU | E-LBKPM12LUU | yes |
| E-LBKPM12UU | E-LBKPM12UU | yes |
| E-LBKPM16LUU | E-LBKPM16LUU | yes |
| E-LBKPM16UU | E-LBKPM16UU | yes |
| E-LBKPM20LUU | E-LBKPM20LUU | yes |
| E-LBKPM20UU | E-LBKPM20UU | yes |
| E-LBKPM25LUU | E-LBKPM25LUU | yes |
| E-LBKPM25UU | E-LBKPM25UU | yes |
| E-LBKPM30LUU | E-LBKPM30LUU | yes |
| E-LBKPM30UU | E-LBKPM30UU | yes |
| E-LBKPM40UU | E-LBKPM40UU | yes |
| E-LBHP6DMUU | E-LBHP6DMUU | yes |
| E-LBHP6LUU | E-LBHP6LUU | yes |
| E-LBHP6UU | E-LBHP6UU | yes |
| E-LBHP8DMUU | E-LBHP8DMUU | yes |
| E-LBHP8LUU | E-LBHP8LUU | yes |
| E-LBHP8UU | E-LBHP8UU | yes |
| E-LBHP10DMUU | E-LBHP10DMUU | yes |
| E-LBHP10LUU | E-LBHP10LUU | yes |
| E-LBHP10UU | E-LBHP10UU | yes |
| E-LBHP12DMUU | E-LBHP12DMUU | yes |
| E-LBHP12LUU | E-LBHP12LUU | yes |
| E-LBHP12UU | E-LBHP12UU | yes |
| E-LBHP16DMUU | E-LBHP16DMUU | yes |
| E-LBHP16UU | E-LBHP16UU | yes |
| E-LBHP20DMUU | E-LBHP20DMUU | yes |
| E-LBHP20LUU | E-LBHP20LUU | yes |
| E-LBHP20UU | E-LBHP20UU | yes |
| E-LBHP25LUU | E-LBHP25LUU | yes |
| E-LBHP25UU | E-LBHP25UU | yes |
| E-LBHP30DMUU | E-LBHP30DMUU | yes |
| E-LBHP30LUU | E-LBHP30LUU | yes |
| E-LBHP30UU | E-LBHP30UU | yes |
| E-LBHP40LUU | E-LBHP40LUU | yes |
| E-LBHP40UU | E-LBHP40UU | yes |
| E-LBHPM6LUU | E-LBHPM6LUU | yes |
| E-LBHPM6UU | E-LBHPM6UU | yes |
| E-LBHPM8LUU | E-LBHPM8LUU | yes |
| E-LBHPM10LUU | E-LBHPM10LUU | yes |
| E-LBHPM10UU | E-LBHPM10UU | yes |
| E-LBHPM12LUU | E-LBHPM12LUU | yes |
| E-LBHPM12UU | E-LBHPM12UU | yes |
| E-LBHPM16LUU | E-LBHPM16LUU | yes |
| E-LBHPM16UU | E-LBHPM16UU | yes |
| E-LBHPM20LUU | E-LBHPM20LUU | yes |
| E-LBHPM20UU | E-LBHPM20UU | yes |
| E-LBHPM25LUU | E-LBHPM25LUU | yes |
| E-LBHPM25UU | E-LBHPM25UU | yes |
| E-LBHPM30LUU | E-LBHPM30LUU | yes |
| E-LBHPM30UU | E-LBHPM30UU | yes |
| E-LBHPM40LUU | E-LBHPM40LUU | yes |
| E-LBHPM40UU | E-LBHPM40UU | yes |
| E-LBFC6DMUU | E-LBFC6DMUU | yes |
| E-LBFC6LUU | E-LBFC6LUU | yes |
| E-LBFC8DMUU | E-LBFC8DMUU | yes |
| E-LBFC8LUU | E-LBFC8LUU | yes |
| E-LBFC10DMUU | E-LBFC10DMUU | yes |
| E-LBFC10LUU | E-LBFC10LUU | yes |
| E-LBFC12DMUU | E-LBFC12DMUU | yes |
| E-LBFC12LUU | E-LBFC12LUU | yes |
| E-LBFC16DMUU | E-LBFC16DMUU | yes |
| E-LBFC16LUU | E-LBFC16LUU | yes |
| E-LBFC20DMUU | E-LBFC20DMUU | yes |
| E-LBFC25DMUU | E-LBFC25DMUU | yes |
| E-LBFC25LUU | E-LBFC25LUU | yes |
| E-LBFC30LUU | E-LBFC30LUU | yes |
| E-LBFC40LUU | E-LBFC40LUU | yes |
| E-LBFCM6LUU | E-LBFCM6LUU | yes |
| E-LBFCM8LUU | E-LBFCM8LUU | yes |
| E-LBFCM10LUU | E-LBFCM10LUU | yes |
| E-LBFCM12LUU | E-LBFCM12LUU | yes |
| E-LBFCM16LUU | E-LBFCM16LUU | yes |
| E-LBFCM20LUU | E-LBFCM20LUU | yes |
| E-LBFCM25LUU | E-LBFCM25LUU | yes |
| E-LBFCM30LUU | E-LBFCM30LUU | yes |
| E-LBKC6DMUU | E-LBKC6DMUU | yes |
| E-LBKC6LUU | E-LBKC6LUU | yes |
| E-LBKC8DMUU | E-LBKC8DMUU | yes |
| E-LBKC8LUU | E-LBKC8LUU | yes |
| E-LBKC10DMUU | E-LBKC10DMUU | yes |
| E-LBKC10LUU | E-LBKC10LUU | yes |
| E-LBKC12DMUU | E-LBKC12DMUU | yes |
| E-LBKC16DMUU | E-LBKC16DMUU | yes |
| E-LBKC16LUU | E-LBKC16LUU | yes |
| E-LBKC20DMUU | E-LBKC20DMUU | yes |
| E-LBKC20LUU | E-LBKC20LUU | yes |
| E-LBKC25LUU | E-LBKC25LUU | yes |
| E-LBKC30DMUU | E-LBKC30DMUU | yes |
| E-LBKC30LUU | E-LBKC30LUU | yes |
| E-LBKC40LUU | E-LBKC40LUU | yes |
| E-LBKCM6LUU | E-LBKCM6LUU | yes |
| E-LBKCM8LUU | E-LBKCM8LUU | yes |
| E-LBKCM10LUU | E-LBKCM10LUU | yes |
| E-LBKCM12LUU | E-LBKCM12LUU | yes |
| E-LBKCM20LUU | E-LBKCM20LUU | yes |
| E-LBKCM25LUU | E-LBKCM25LUU | yes |
| E-LBKCM30LUU | E-LBKCM30LUU | yes |
| E-LBKCM40LUU | E-LBKCM40LUU | yes |
| E-LBHC6LUU | E-LBHC6LUU | yes |
| E-LBHC8DMUU | E-LBHC8DMUU | yes |
| E-LBHC8LUU | E-LBHC8LUU | yes |
| E-LBHC10DMUU | E-LBHC10DMUU | yes |
| E-LBHC12DMUU | E-LBHC12DMUU | yes |
| E-LBHC12LUU | E-LBHC12LUU | yes |
| E-LBHC16DMUU | E-LBHC16DMUU | yes |
| E-LBHC16LUU | E-LBHC16LUU | yes |
| E-LBHC20DMUU | E-LBHC20DMUU | yes |
| E-LBHC20LUU | E-LBHC20LUU | yes |
| E-LBHC25DMUU | E-LBHC25DMUU | yes |
| E-LBHC25LUU | E-LBHC25LUU | yes |
| E-LBHC30DMUU | E-LBHC30DMUU | yes |
| E-LBHC30LUU | E-LBHC30LUU | yes |
| E-LBHC40LUU | E-LBHC40LUU | yes |
| E-LBHCM6LUU | E-LBHCM6LUU | yes |
| E-LBHCM8LUU | E-LBHCM8LUU | yes |
| E-LBHCM10LUU | E-LBHCM10LUU | yes |
| E-LBHCM12LUU | E-LBHCM12LUU | yes |
| E-LBHCM16LUU | E-LBHCM16LUU | yes |
| E-LBHCM20LUU | E-LBHCM20LUU | yes |
| E-LBHCM25LUU | E-LBHCM25LUU | yes |
| E-LBHCM30LUU | E-LBHCM30LUU | yes |

| what was tried (SolidCraft 0.50.0) | error | result |
|---|---|---|
| insert_design with a free `parameters` map (blen 35 mm) | None | {'bbox_max': [[42.0, 27.0, 27.0], [42.0, 27.0, 27.0]], 'bodies': ['BodyRound0', 'BodyRound0 (2)']} |
| component.set_link_parameters | {"command": "component.set_link_parameters", "error": "unknown command `component.set_link_parameters`", "step": 1} | None |
| generator.parse | {"command": "generator.parse", "error": "unknown command `generator.parse`", "step": 1} | None |
| generator.insert | {"command": "generator.insert", "error": "unknown command `generator.insert` (did you mean `canvas.insert`, `parts.insert` or `pointcloud.insert`?)", "step": 1} | None |
| blen 40 mm (not an allowed length of the row) by an ordinary parameters.change | None | {'bbox_max': [[40.00000000000001, 27.0, 27.0]], 'bodies': ['BodyRound0']} |
| blen 40 mm in a configuration row | {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `L of flanged_long-round-20 (S11 p.466 p.468 tables)` restricts the final value", "step": 1} | None |
| opp 1 in a row that has no opposite-counterbore type | {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `counterbore side of flanged_medium-round-20 (S11 p.467 p.469 tables)` restricts the final value", "step": 1} | None |
| unknown row | {"command": "component.insert_design", "error": "invalid parameters for `component.insert_design`: configuration `no-such-row` does not exist in the source design", "step": 1} | None |

## What SolidCraft 0.50.0 could not express (exact errors) and the workarounds

1. **A hole keeps the face it was picked on.** One `solid.hole` feature made on the round-flange body fails on the square-flange body:
   `configuration X would fail to rebuild: <Hole>: the reference `F8:side:l4` no longer exists as it was picked; reselect it`. Workaround
   (labelled): one set of hole features per body variant (a suppression column each). Proposal: a hole whose position expression is re-resolved
   to the face at that position on every rebuild (the doc says the position is followed; the face reference is what breaks).
2. **A free parameter value on an inserted part requires the #23175 surface (unavailable on 0.50.0/0.51.1).** `component.insert_design {configuration, parameters}` is accepted and the key ignored,
   `component.set_link_parameters` and `generator.parse|insert` are `unknown command` (see the probe table). Workaround (labelled): a row for
   the code in a working copy of the model (`config.row {from: <catalogue row>, values: {...}}`), inserted by `configuration`; to change the
   length, change it in the working copy and insert again. requires the #23175 surface (unavailable on 0.50.0/0.51.1).
3. **A rule cannot name a configuration row.** The per-row allowed lengths and the hole-set switches need a condition; there is none on the row, so
   each row carries a unitless `rowno` (and `kind` for the body variant) and the rules test that. Proposal: a `row` condition.
4. **Expression depth.** The sandbox allows a depth of 16 inside a function; a `refuse` call with a message built from `${}` interpolation or an
   array of 8 parts inside two nested `if` blocks fails to compile with `Expression exceeds maximum complexity (line 61, position 45)`, and the
   error names the first line only. Workaround: flat functions, `cat([...])`. Proposal: raise the depth to 32 or count blocks less.
5. **The field template ignores separators.** `E-LBF20-UU` reads as `E-LBF20UU` (the Python regex refuses it), see `rhai_equiv.json`. The
   template cannot say "no separator here" except by a required one (`\-`, added to the stand-in for the oil free bushing code).
6. **A code that matches no template** gets the engine's message, not the generator's: a second template `{raw: text 1..80 [...]}` catches
   it and `resolve` raises the Python message. Proposal: an optional `fn no_match(raw)`.
7. **Arcs and point expressions.** Arc points come from `sketch.point` ids with expression coordinates so that the arcs follow the
   parameters (the arc's centre is solved, not stored).

The optional link proof is declared in `link_checks.json` and run by `ci.sh` through `runtime.parametric.links`. It adds insertion, link-edit, and out-of-range refusal rows only when the command catalogue lists `component.set_link_parameters`. Release builds retain their existing rows and link dependency item.

### #23175 checks

The 0.50.0/0.51.1 results above remain release observations. The #23175 CI artifact records 480 valid, 57 rejects, 11 rebuild checks and 0 blocked records. The next CI run also checks link overrides and ordinary edit refusal with `enforce_on_edit` where limit rules exist; these new checks are pending. Differences remain differences.

The supplied #23175 artifact includes 3 link checks; the added ordinary-edit enforcement check awaits CI.
