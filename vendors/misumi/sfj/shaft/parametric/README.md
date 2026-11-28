# misumi.sfj.shaft as a parametric SolidCraft generator

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai, and rules addressed by feature name requires the #23175 surface (unavailable on 0.50.0/0.51.1). The exact command errors quoted below are observations from SolidCraft 0.50.0. On capable hosts, link overrides and ordinary source `parameters.change` enforce limit rules marked `enforce_on_edit`.

The shaft modelled ONCE in SolidCraft (`sfj-shaft/sfj-shaft.sc`), a configuration table of the diameter rows, the ordering code as a field template
(an unordered option set with arguments, a decimal length) and the logic, about 30 cross-option refusals included, as plain Rhai, following
SolidCraft's generator interface (`docs/formats/generator.md`, version 2, issue 22331). The Python generator in `../src` is untouched and is the
reference every code below is compared with.

```
sfj-shaft/                     the package layout of the interface document
  generator.toml               [parameters], two [[template]] (the code, a catch-all), [rows."<D>"] source / page / status per configuration row
  sfj-shaft.sc                 the parametric model + its configuration table + its rules (built by build.py)
  generator.rhai               resolve(fields) -> #{configuration, parameters, properties}; fields(configuration, parameters) -> fields
  tables/*.csv                 types, diameters, tap*, stepped_*, wrench, params: copied from ../data/*.csv (rows keep source, page, status);
                               params.csv gains derived rows (the D lists, the catalogue page of each family) written by build.py
build.py                       builds the model with solidcraft-cli
run_codes.py  report.py        the end-to-end proof (results.json) and the tables below
faithfulness.py  ci.sh         faithfulness.json for tools/parametric-verdict (what the `parametric` workflow runs)
../../../../runtime/fieldtemplate.py   the field-template stand-in, shared with the HIWIN MG and HFS proofs; this generator added `\-` (a required
                                       separator) and the option bag `{opts: bag(M:num, F:int, LKC, ...)}` (see "The ordering code")
../../../../runtime/parametric/        helpers shared by the harnesses (solidcraft-cli, the Rhai host, measuring, the spec check on an inserted part)
```

## How the model is built (all of it worked on SolidCraft 0.50.0)

- **One model, 26 parameters and 2 derived ones.** `D L` (length; the main body of the stepped types), the row cells `W l1 H` (wrench flat width and
  length, flat surface depth), `part_type` (a text parameter: material, tolerance class and finish, no geometry), `lkc` (0.1 mm steps: text only),
  the steps `F P T` (left step length, step diameter, right step length), the tapped ends `m_left m_right md` (nominal thread of the left and right end, MD),
  and the flats `sc sx wsc xw fc fa fe wfc wa we lfc la lfd`. **Absent is a parameter value**: a step length of 0, a thread of 0, a flat
  position of -1 mm; the rules below switch on `F > 0`, `m_left = 3 mm`, `sc >= 0 mm`. The tap depths `tl_depth = m_left * (2 + md)` and `tr_depth = 2 * m_right`
  are derived parameters.
- **Features.** Python's commands, in Python's order: the cylinder `Shaft` (`D x L`, along X), `Left step` (`P x F`, base `-F`) and `Right step`
  (`P x T`, base `L`), the tapped ends (`solid.hole` with `thread = M<size>`), the flats as `solid.box` cuts whose corner, length and thickness are
  expressions over the parameters (`SC a/b`, `SX a/b`, `WSC Y a/b`, `WSC Z a/b`, `FC from left`, `FC from right`, `WFC Y`, `WFC Z`, `LFC`: a
  wrench flat pair is two boxes, the `A` / `E` choice of FC is two features, each flat kind has its own features so that no conditional expression is
  needed). 60 named features, 85 columns, 121 rules, 16 rows (3 4 5 6 8 10 12 13 15 16 20 25 30 35 40 50).
- **Tapped ends: one hole feature per size and per host face.** A thread designation cannot come from a parameter (M3 and M30 are different
  features), and a `solid.hole` stores the face it was picked on (`F4:bottom`: the end face of the left step), which does not exist when the step
  is suppressed (`the reference `F4:bottom` no longer exists as it was picked; reselect it`). So there are four sets, each size once:
  `Tap L shaft M<m>` (on the shaft end x = 0, step absent), `Tap L step M<m>` (on the end of the left step), `Tap R shaft M<m>` (x = L), `Tap R step M<m>`
  (end of the right step), 12 + 12 + 10 + 10 = 44 features; each is on when its thread parameter equals its size and its step is present (or
  absent). The sizes are the union of the tables (`tap.csv`, `tap_j*.csv`, `stepped_*.csv`); `M2.6` (D5, both ends tapped) is left out: SolidCraft has
  no coarse pitch for it (`M2.6 has no coarse ISO pitch: give one, e.g. M2.6x0.25 or M2.6x0.2`), so the Python generator cannot build that code either.
- **Configuration table = the diameter rows.** One row per D of `data/diameters.csv` (`D`, `H` from `params.csv`, `W l1` from `data/wrench.csv` for
  D 6 and over; D 3 to 5 have no wrench flat, their `W l1` stay at the model default). Everything else is a parameter of the code, set in a row for
  the code (`config.row from=<D>`) by the harness. Rules: `L` 10 to 1500 mm, the allowed values of `m_left` / `m_right` (0 or a catalogue thread size), and an
  on-rule and an off-rule (`drive_suppression`) for each of the 59 optional features.
- **Creation order matters in SolidCraft.** A feature of length 0 is refused at creation (`invalid input: extrude distance is zero`), so the model
  is drawn with a stepped, tapped, flatted D 50 shaft and each optional feature is created with the others suppressed (a hole picks the plain end
  face), then every row starts from the bare shaft.

For an existing pre-0.2.1 container, `python3 build.py --migrate-tap-parameters` updates the whole-word tap parameter names to
`m_left` and `m_right` without running SolidCraft. It preserves the document except for those tokens and removes the geometry cache so
SolidCraft rebuilds it on opening. The normal `build.py` command builds the model with the same names from scratch.

## The ordering code

`generator.toml` has two templates. The first reads the code:
`E\-{type: text 1..10 [A-Z]}{d: int 0..99}\-{length: decimal}{opts: bag(M:num, N:num, MD:num, F:int, P:int, T:int, SC:int, SX:int, WSC:int, X:int, FC:int, WFC:int, LFC:int, A:int, E:int, LKC)}`.
The second, `{raw: text 1..128 [A-Za-z0-9._ /-]}`, matches everything else, so the script can give Python's `expected <type><D>-<L>[...]` refusal for
a code that is not a code at all. `E-` and the `-` before the length are required separators (`\-`: `E-SFJ12-5` reads, `E-SFJ125` does not).

**The option set, and what it could not do.** The interface document's `set(-LTP, -SC:int 0..99)` is an unordered set, each option at most once,
whose value is an object. The shaft codes need more than that, and the Python refusals depend on it: M, N, F, P, MD, T are read in order right
after the length (a thread after an `SC` is "unknown or unsupported"), and `A` and `E` are the arguments of whichever of FC, WFC, LFC precedes them
(`FC30-E50-LFC6-A2`; `WFC10-A8-E20-LFC5-A0` carries `A` twice). Python also has its own refusal for an option given twice
(`alteration FC given twice`). So the template kind used here is `bag(...)`: tokens each preceded by `-`, any order, any number of times, each
one of the listed options with its argument kind (`int`, `num` = digits and at most one decimal, none), every other token kept as option `?` with
its raw text; the value is the ordered list `[[name, argument text | null], ...]`. The script walks it exactly as Python walks its tokens
(`take_tok`, `alterations`). The proposal for the interface: `set(...)` gains a mode that keeps repeats and order (a list value). It is in
`runtime/fieldtemplate.py` (the stand-in) and printing it back writes the tokens in the given order.

**The refusals.** Every Python `CodeError`, in its order and with its message word for word, is a `refuse("invalid", message)` in `generator.rhai`
(all 62 `raise` sites of `shaft.py`: type and diameter, the family tables, M / N / F / P / T / MD, the 30 cross-option checks: SC with WSC, FC with WFC, flats closer
than 2 mm to each other or to a tap, `M x 2 + N x 2 <= L`, `SC + l1 <= L`, `LKC` with `D - P <= 2`, overall length (Y), D 35 to 50 on other types, ...).
All data (ranges per D and family, the wrench and flat tables, the LKC tolerances, the MD limits) is read from `tables/*.csv`. The Rhai sandbox allows
only a few nesting levels per function (`Expression exceeds maximum complexity`), so the script is a set of small flat functions; it is 28.5 KB of
the 32 KiB allowed. `fields(configuration, parameters)` is the inverse (code printing, canonical option order): for all 42 valid codes
resolve(print(fields(resolve(code)))) gives the same configuration and parameters.

## What was run

For every line of `../codes.txt` (22 valid codes, 18 `!` rejects), 20 extra valid codes (every family and option, both ends of a flat, D 3 and D 50,
the corner cases of the positional tokens) and 76 extra refusals (one or more per Python message): code -> template -> Rhai `resolve` -> a row for
the code in a working copy of the model -> a design inserts that copy with `component.insert_design {configuration}` -> `inspect.measure` (volume,
area, bbox, faces) + `model.threads` + the unchanged `src/check.py` spec check (run on the inserted part, with the `Shaft` it needs rebuilt from the
Rhai result, never from the Python parser) -> the same code built by the Python generator and measured the same way. The thread spans, the
description and part number text, and the code -> parameters -> code -> parameters round trip are compared too. Seven rebuild checks (item "stays
parametric") change `L` of a built part with `parameters.change` and compare it with the code built directly and with the Python part.

```
SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run> bash ci.sh OUTDIR     # build.py, run_codes.py, faithfulness.py -> OUTDIR/faithfulness.json
tools/parametric-verdict OUTDIR/faithfulness.json
python3 report.py OUTDIR/results.json                             # the tables below
```

`RHAI_RUN` is the host built from `runtime/rhai-run` (`cargo build --release`).

## Result: side by side

Equal means volume and area within 1e-6 relative, the same bbox, face and body counts (decided by `tools/parametric-verdict`); the first table
also compares the thread spans, the description text and the round trip.

| code | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec python | spec parametric | same threads, text, round trip | equal |
|---|---|---|---|---|---|---|
| E-PSFG16-250-FC20-A10 | 50160.84 / 12972.16 / 250x16x16 / 6 | 50160.84 / 12972.16 / 250x16x16 / 6 | 14/14 | 14/14 | yes | yes |
| E-PSFJ3-10 | 70.69 / 108.38 / 10x3x3 / 3 | 70.69 / 108.38 / 10x3x3 / 3 | 11/11 | 11/11 | yes | yes |
| E-PSFJ6-20 | 565.49 / 433.54 / 20x6x6 / 3 | 565.49 / 433.54 / 20x6x6 / 3 | 11/11 | 11/11 | yes | yes |
| E-PSFJT12-60-M6 | 6550.22 / 2676.64 / 60x12x12 / 5 | 6550.22 / 2676.64 / 60x12x12 / 5 | 11/11 | 11/11 | yes | yes |
| E-PSFJT50-200-M30 | 359606.33 / 40338.05 / 200x50x50 / 5 | 359606.33 / 40338.05 / 200x50x50 / 5 | 11/11 | 11/11 | yes | yes |
| E-PSSFJ30-500-WFC40-A10-E20-LKC | 351810.15 / 48562.33 / 500x30x30 / 9 | 351810.15 / 48562.33 / 500x30x30 / 9 | 18/18 | 18/18 | yes | yes |
| E-SFJ20-300-SC5 | 94033.69 / 19509.48 / 300x20x20 / 9 | 94033.69 / 19509.48 / 300x20x20 / 9 | 14/14 | 14/14 | yes | yes |
| E-SSFJ10-123.4-LKC-WSC12-X8 | 9561.01 / 4052.58 / 123.4x10x10 / 15 | 9561.01 / 4052.58 / 123.4x10x10 / 15 | 18/18 | 18/18 | yes | yes |
| E-PSFJC6-40-M3-SC0 | 1083.51 / 854.49 / 40x6x6 / 9 | 1083.51 / 854.49 / 40x6x6 / 9 | 15/15 | 15/15 | yes | yes |
| E-SFJC20-300-M10-SC5-FC40-E20 | 92244.78 / 20041.45 / 300x20x20 / 14 | 92244.78 / 20041.45 / 300x20x20 / 14 | 19/19 | 19/19 | yes | yes |
| E-PSFJC12-200-M6-SC0-SX20-LKC | 22203.79 / 7956.72 / 200x12x12 / 15 | 22203.79 / 7956.72 / 200x12x12 / 15 | 19/19 | 19/19 | yes | yes |
| E-PSFJZ6-50-M3-N3-SC0 | 1336.81 / 1090.11 / 50x6x6 / 11 | 1336.81 / 1090.11 / 50x6x6 / 11 | 16/16 | 16/16 | yes | yes |
| E-PSSFJZ16-300-M8-N6-WSC20-X30-LKC | 59292.60 / 16040.33 / 300x16x16 / 19 | 59292.60 / 16040.33 / 300x16x16 / 19 | 20/20 | 20/20 | yes | yes |
| E-PSFJW6-50-M3-N3-LKC | 1354.81 / 1093.27 / 50x6x6 / 7 | 1354.81 / 1093.27 / 50x6x6 / 7 | 12/12 | 12/12 | yes | yes |
| E-SSFJW4-60-M2-N2 | 737.90 / 819.33 / 60x4x4 / 7 | 737.90 / 819.33 / 60x4x4 / 7 | 12/12 | 12/12 | yes | yes |
| E-PSFJW30-400-M20-N12-SC120-WFC30-A60-E60 | 269511.80 / 42166.56 / 400x30x30 / 19 | 269511.80 / 42166.56 / 400x30x30 / 19 | 24/24 | 24/24 | yes | yes |
| E-PSFPG8-200-F4-P6-M3-SC0 | 10115.81 / 5246.88 / 204x8x8 / 11 | 10115.81 / 5246.88 / 204x8x8 / 11 | 22/22 | 22/22 | yes | yes |
| E-PSSFPG20-500-F10-P12-M8-SC20-SX15-FC30-E50-LFC6-A2 | 156683.84 / 32839.49 / 510x20x20 / 25 | 156683.84 / 32839.49 / 510x20x20 / 25 | 34/34 | 34/34 | yes | yes |
| E-SFPG16-300-F8-P10-M6-SC5-LKC | 60606.63 / 15935.72 / 308x16x16 / 13 | 60606.63 / 15935.72 / 308x16x16 / 13 | 22/22 | 22/22 | yes | yes |
| E-PSFPG25-400-F20-P16-MD10-SC30-WFC20-A50-E50 | 197692.06 / 34284.87 / 420x25x25 / 19 | 197692.06 / 34284.87 / 420x25x25 / 19 | 30/30 | 30/30 | yes | yes |
| E-PSFPH8-200-F5-P6-M3-T5-SC0 | 10256.01 / 5407.10 / 210x8x8 / 15 | 10256.01 / 5407.10 / 210x8x8 / 15 | 24/24 | 24/24 | yes | yes |
| E-PFPGH30-800-F30-P20-M16-T25-SC40 | 572517.00 / 83121.79 / 855x30x30 / 17 | 572517.00 / 83121.79 / 855x30x30 / 17 | 24/24 | 24/24 | yes | yes |
| E-SFJ12-100-FC40-A5 (extra) | 11129.67 / 3989.31 / 100x12x12 / 6 | 11129.67 / 3989.31 / 100x12x12 / 6 | 14/14 | 14/14 | yes | yes |
| E-SFJ12-100-WFC20-A5-E5 (extra) | 11129.67 / 3998.31 / 100x12x12 / 9 | 11129.67 / 3998.31 / 100x12x12 / 9 | 18/18 | 18/18 | yes | yes |
| E-PSFPG8-200-F9-P6-M3-SC0 (extra) | 10257.18 / 5341.13 / 209x8x8 / 11 | 10257.18 / 5341.13 / 209x8x8 / 11 | 22/22 | 22/22 | yes | yes |
| E-PSFPG8-200-F4-P6-M3-SC0-SX20-FC10-E90 (extra) | 10058.62 / 5251.75 / 204x8x8 / 20 | 10058.62 / 5251.75 / 204x8x8 / 20 | 30/30 | 30/30 | yes | yes |
| E-PSFPH8-200-F5-P6-M3-T9-SC0 (extra) | 10369.10 / 5482.50 / 214x8x8 / 15 | 10369.10 / 5482.50 / 214x8x8 / 15 | 24/24 | 24/24 | yes | yes |
| E-SFJ3-400 (extra) | 2827.43 / 3784.05 / 400x3x3 / 3 | 2827.43 / 3784.05 / 400x3x3 / 3 | 11/11 | 11/11 | yes | yes |
| E-PSFG6-15 (extra) | 424.12 / 339.29 / 15x6x6 / 3 | 424.12 / 339.29 / 15x6x6 / 3 | 11/11 | 11/11 | yes | yes |
| E-PSFJ50-1500 (extra) | 2945243.11 / 239546.44 / 1500x50x50 / 3 | 2945243.11 / 239546.44 / 1500x50x50 / 3 | 11/11 | 11/11 | yes | yes |
| E-PSFJ12-100-LKC (extra) | 11309.73 / 3996.11 / 100x12x12 / 3 | 11309.73 / 3996.11 / 100x12x12 / 3 | 11/11 | 11/11 | yes | yes |
| E-PSFJT6-30-M3 (extra) | 818.78 / 669.16 / 30x6x6 / 5 | 818.78 / 669.16 / 30x6x6 / 5 | 11/11 | 11/11 | yes | yes |
| E-PSFG30-100-WFC20-A10-E10 (extra) | 69876.32 / 10891.33 / 100x30x30 / 9 | 69876.32 / 10891.33 / 100x30x30 / 9 | 18/18 | 18/18 | yes | yes |
| E-SFJ30-300-WSC12-X20 (extra) | 211264.70 / 29766.51 / 300x30x30 / 15 | 211264.70 / 29766.51 / 300x30x30 / 15 | 18/18 | 18/18 | yes | yes |
| E-PSFJC6-20-M3-SC0-LKC (extra) | 518.03 / 477.50 / 20x6x6 / 9 | 518.03 / 477.50 / 20x6x6 / 9 | 15/15 | 15/15 | yes | yes |
| E-PSFGZ12-200-M6-N8-SC10 (extra) | 21712.75 / 8306.42 / 200x12x12 / 13 | 21712.75 / 8306.42 / 200x12x12 / 13 | 16/16 | 16/16 | yes | yes |
| E-SFJW13-100-M4-N5 (extra) | 13066.26 / 4564.42 / 100x13x13 / 7 | 13066.26 / 4564.42 / 100x13x13 / 7 | 12/12 | 12/12 | yes | yes |
| E-PSFJW35-300-M12-N16 (extra) | 281708.06 / 37094.98 / 300x35x35 / 7 | 281708.06 / 37094.98 / 300x35x35 / 7 | 12/12 | 12/12 | yes | yes |
| E-SFPG12-100-F5-P8-M4-SC0-FC10-E20 (extra) | 11357.59 / 4201.86 / 105x12x12 / 14 | 11357.59 / 4201.86 / 105x12x12 / 14 | 26/26 | 26/26 | yes | yes |
| E-PSFPG16-300-F8-P12-MD8-SC10-LFC4-A2 (extra) | 60229.10 / 16317.63 / 308x16x16 / 16 | 60229.10 / 16317.63 / 308x16x16 / 16 | 26/26 | 26/26 | yes | yes |
| E-PSFPG20-400-F10-P17-M10-SC10-FC30-E20-LKC (extra) | 126094.01 / 26867.41 / 410x20x20 / 16 | 126094.01 / 26867.41 / 410x20x20 / 16 | 26/26 | 26/26 | yes | yes |
| E-SFPH30-600-F8-P27-M20-T9-SC20 (extra) | 414209.79 / 63841.84 / 617x30x30 / 17 | 414209.79 / 63841.84 / 617x30x30 / 17 | 24/24 | 24/24 | yes | yes |

| rejected code | python message | parametric message | same |
|---|---|---|---|
| E-PSFG3-50 | E-PSFG has no D3: the f8 type is listed for D 6-30 (p.432 note: D3, 4, 5 not applicable, 35/40/50 only E-PSFJ) | E-PSFG has no D3: the f8 type is listed for D 6-30 (p.432 note: D3, 4, 5 not applicable, 35/40/50 only E-PSFJ) | yes |
| E-SFJ6-5 | length 5 mm outside 20-800 mm for E-SFJ6 (p.432 table) | length 5 mm outside 20-800 mm for E-SFJ6 (p.432 table) | yes |
| E-SFJ6-900 | length 900 mm outside 20-800 mm for E-SFJ6 (p.432 table) | length 900 mm outside 20-800 mm for E-SFJ6 (p.432 table) | yes |
| E-SFJ6-20-WSC5 | WSC needs the distance between the two flats: WSC12-X8 | WSC needs the distance between the two flats: WSC12-X8 | yes |
| E-PSFJT6-20-M9 | M9 is not offered for D6 (coarse selection p.433: M3) | M9 is not offered for D6 (coarse selection p.433: M3) | yes |
| E-PSFJC6-40-M3 | E-PSFJC6 needs its wrench flat position SC after the thread, e.g. ...-SC0 (p.434 ordering example) | E-PSFJC6 needs its wrench flat position SC after the thread, e.g. ...-SC0 (p.434 ordering example) | yes |
| E-PSFJC5-40-M3-SC0 | E-PSFJC5: no such version of D5 in the p.434 table (D 6-50; D3 and D4/D5 are only on p.432-433/436) | E-PSFJC5: no such version of D5 in the p.434 table (D 6-50; D3 and D4/D5 are only on p.432-433/436) | yes |
| E-PSFJC50-100-M10-SC0 | M10 is not offered for D50 (coarse selection p.434: M12, M16, M20, M24, M30) | M10 is not offered for D50 (coarse selection p.434: M12, M16, M20, M24, M30) | yes |
| E-PSFJZ6-50-M3-N3-SC0-SX10 | alteration SX is not offered for E-PSFJZ (p.435); offered: FC, LKC, SC, WFC, WSC | alteration SX is not offered for E-PSFJZ (p.435); offered: FC, LKC, SC, WFC, WSC | yes |
| E-PSFJZ6-20-M3-N3-SC0 | length 20 mm outside 25-600 mm for E-PSFJZ6 (p.435 table) | length 20 mm outside 25-600 mm for E-PSFJZ6 (p.435 table) | yes |
| E-PSFJW50-100-M30-N30 | overall length L = 100 requires M x 2 + N x 2 <= L = 120 (p.436 note) | overall length L = 100 requires M x 2 + N x 2 <= L = 120 (p.436 note) | yes |
| E-SFJW35-100-M8-N8 | O.D. 35 is applicable only to E-PSFJW (p.436 note) | O.D. 35 is applicable only to E-PSFJW (p.436 note) | yes |
| E-PSFPG8-200-F4-P7-M3-SC0 | P7 is outside P 6-6 for D8 (p.437 table) | P7 is outside P 6-6 for D8 (p.437 table) | yes |
| E-PSFPG8-200-F1-P6-M3-SC0 | F1 is outside 2 <= F <= P x 4 = 24 (p.437) | F1 is outside 2 <= F <= P x 4 = 24 (p.437) | yes |
| E-PSFPG8-900-F4-P6-M3-SC0 | overall length (Y) = 904 mm exceeds the maximum 800 mm for D8 (p.437 table) | overall length (Y) = 904 mm exceeds the maximum 800 mm for D8 (p.437 table) | yes |
| E-PSFPG8-200-F4-P6-M3 | E-PSFPG8 needs its wrench flat position SC after the thread, e.g. ...-SC0 (p.437 ordering example) | E-PSFPG8 needs its wrench flat position SC after the thread, e.g. ...-SC0 (p.437 ordering example) | yes |
| E-PSFPG16-300-F8-P14-M6-SC5-LKC | LKC is not applicable when D - P <= 2 (D16, P14; p.437) | LKC is not applicable when D - P <= 2 (D16, P14; p.437) | yes |
| E-PSFPH8-200-F5-P6-M3-SC0 | both ends stepped: the right step length T follows M, e.g. E-PSFPH8-200-F4-P6-M3-T4-SC0 | both ends stepped: the right step length T follows M, e.g. E-PSFPH8-200-F4-P6-M3-T4-SC0 | yes |
| E-SFJ | 'E-SFJ': expected <type><D>-<L>[-<option>...], e.g. E-PSFJ6-20 (straight), E-PSFJT6-30-M3 (one end tapped), E-PSFJC6-40-M3-SC0, E-PSFJZ6-50-M3-N3-SC0, E-PSFJW6-50-M3-N3, E-PSFPG8-200-F4-P6-M3-SC0, E-PSFPH8-200-F5-P6-M3-T5-SC0 | 'E-SFJ': expected <type><D>-<L>[-<option>...], e.g. E-PSFJ6-20 (straight), E-PSFJT6-30-M3 (one end tapped), E-PSFJC6-40-M3-SC0, E-PSFJZ6-50-M3-N3-SC0, E-PSFJW6-50-M3-N3, E-PSFPG8-200-F4-P6-M3-SC0, E-PSFPH8-200-F5-P6-M3-T5-SC0 | yes |
| XYZ | 'XYZ': expected <type><D>-<L>[-<option>...], e.g. E-PSFJ6-20 (straight), E-PSFJT6-30-M3 (one end tapped), E-PSFJC6-40-M3-SC0, E-PSFJZ6-50-M3-N3-SC0, E-PSFJW6-50-M3-N3, E-PSFPG8-200-F4-P6-M3-SC0, E-PSFPH8-200-F5-P6-M3-T5-SC0 | 'XYZ': expected <type><D>-<L>[-<option>...], e.g. E-PSFJ6-20 (straight), E-PSFJT6-30-M3 (one end tapped), E-PSFJC6-40-M3-SC0, E-PSFJZ6-50-M3-N3-SC0, E-PSFJW6-50-M3-N3, E-PSFPG8-200-F4-P6-M3-SC0, E-PSFPH8-200-F5-P6-M3-T5-SC0 | yes |
| E-SFJ20 | 'E-SFJ20': expected <type><D>-<L>[-<option>...], e.g. E-PSFJ6-20 (straight), E-PSFJT6-30-M3 (one end tapped), E-PSFJC6-40-M3-SC0, E-PSFJZ6-50-M3-N3-SC0, E-PSFJW6-50-M3-N3, E-PSFPG8-200-F4-P6-M3-SC0, E-PSFPH8-200-F5-P6-M3-T5-SC0 | 'E-SFJ20': expected <type><D>-<L>[-<option>...], e.g. E-PSFJ6-20 (straight), E-PSFJT6-30-M3 (one end tapped), E-PSFJC6-40-M3-SC0, E-PSFJZ6-50-M3-N3-SC0, E-PSFJW6-50-M3-N3, E-PSFPG8-200-F4-P6-M3-SC0, E-PSFPH8-200-F5-P6-M3-T5-SC0 | yes |
| E-SFJ6- | 'E-SFJ6-': expected <type><D>-<L>[-<option>...], e.g. E-PSFJ6-20 (straight), E-PSFJT6-30-M3 (one end tapped), E-PSFJC6-40-M3-SC0, E-PSFJZ6-50-M3-N3-SC0, E-PSFJW6-50-M3-N3, E-PSFPG8-200-F4-P6-M3-SC0, E-PSFPH8-200-F5-P6-M3-T5-SC0 | 'E-SFJ6-': expected <type><D>-<L>[-<option>...], e.g. E-PSFJ6-20 (straight), E-PSFJT6-30-M3 (one end tapped), E-PSFJC6-40-M3-SC0, E-PSFJZ6-50-M3-N3-SC0, E-PSFJW6-50-M3-N3, E-PSFPG8-200-F4-P6-M3-SC0, E-PSFPH8-200-F5-P6-M3-T5-SC0 | yes |
| E-PSFJX6-20 | 'E-PSFJX' is not a type of the catalogue: E-SFJ, E-SSFJ, E-PSFJ, E-PSSFJ, E-PSFG (+ T, C, Z, W) and the stepped E-SFPG, E-SSFPG, E-PSFPG, E-PSSFPG, E-SFPH, E-SSFPH, E-PSFPH, E-PSSFPH, E-PFPGH | 'E-PSFJX' is not a type of the catalogue: E-SFJ, E-SSFJ, E-PSFJ, E-PSSFJ, E-PSFG (+ T, C, Z, W) and the stepped E-SFPG, E-SSFPG, E-PSFPG, E-PSSFPG, E-SFPH, E-SSFPH, E-PSFPH, E-PSSFPH, E-PFPGH | yes |
| E-PFPG8-200 | 'E-PFPG' is not a type of the catalogue: E-SFJ, E-SSFJ, E-PSFJ, E-PSSFJ, E-PSFG (+ T, C, Z, W) and the stepped E-SFPG, E-SSFPG, E-PSFPG, E-PSSFPG, E-SFPH, E-SSFPH, E-PSFPH, E-PSSFPH, E-PFPGH | 'E-PFPG' is not a type of the catalogue: E-SFJ, E-SSFJ, E-PSFJ, E-PSSFJ, E-PSFG (+ T, C, Z, W) and the stepped E-SFPG, E-SSFPG, E-PSFPG, E-PSSFPG, E-SFPH, E-SSFPH, E-PSFPH, E-PSSFPH, E-PFPGH | yes |
| E-SFPK8-200-F4-P6-M3-SC0 | 'E-SFPK' is not a type of the catalogue: E-SFJ, E-SSFJ, E-PSFJ, E-PSSFJ, E-PSFG (+ T, C, Z, W) and the stepped E-SFPG, E-SSFPG, E-PSFPG, E-PSSFPG, E-SFPH, E-SSFPH, E-PSFPH, E-PSSFPH, E-PFPGH | 'E-SFPK' is not a type of the catalogue: E-SFJ, E-SSFJ, E-PSFJ, E-PSSFJ, E-PSFG (+ T, C, Z, W) and the stepped E-SFPG, E-SSFPG, E-PSFPG, E-PSSFPG, E-SFPH, E-SSFPH, E-PSFPH, E-PSSFPH, E-PFPGH | yes |
| E-SFJ99-300 | diameter 99: catalogue sizes are [3, 4, 5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30, 35, 40, 50] | diameter 99: catalogue sizes are [3, 4, 5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30, 35, 40, 50] | yes |
| E-SFJ6-20-M3 | E-SFJ is the plain shaft; a thread needs the tapped type E-SFJT (or C, Z, W) | E-SFJ is the plain shaft; a thread needs the tapped type E-SFJT (or C, Z, W) | yes |
| E-PSFJT6-30 | a tapped shaft needs its thread after the length, e.g. E-PSFJT6-30-M3 (choices for D6: M3) | a tapped shaft needs its thread after the length, e.g. E-PSFJT6-30-M3 (choices for D6: M3) | yes |
| E-PSFJT6-30-M9 | M9 is not offered for D6 (coarse selection p.433: M3) | M9 is not offered for D6 (coarse selection p.433: M3) | yes |
| E-PSFJT4-30-M3 | M3 is not offered for D4 (coarse selection p.433: M2) | M3 is not offered for D4 (coarse selection p.433: M2) | yes |
| E-PSFGT5-30-M3 | E-PSFG has no D5: the f8 type is listed for D 6-30 (p.432 note: D3, 4, 5 not applicable, 35/40/50 only E-PSFJ) | E-PSFG has no D5: the f8 type is listed for D 6-30 (p.432 note: D3, 4, 5 not applicable, 35/40/50 only E-PSFJ) | yes |
| E-PSFJC3-30-M3-SC0 | E-PSFJC3: no such version of D3 in the p.434 table (D 6-50; D3 and D4/D5 are only on p.432-433/436) | E-PSFJC3: no such version of D3 in the p.434 table (D 6-50; D3 and D4/D5 are only on p.432-433/436) | yes |
| E-PSFJZ4-30-M3-N3-SC0 | E-PSFJZ4: no such version of D4 in the p.435 table (D 6-50; D3 and D4/D5 are only on p.432-433/436) | E-PSFJZ4: no such version of D4 in the p.435 table (D 6-50; D3 and D4/D5 are only on p.432-433/436) | yes |
| E-PSFJT6-4-M3 | length 4 mm outside 20-800 mm for E-PSFJT6 (p.433 table) | length 4 mm outside 20-800 mm for E-PSFJT6 (p.433 table) | yes |
| E-PSFJW6-50-M3 | both ends tapped: the second thread N follows M, e.g. E-PSFJW6-50-M3-N3 (choices for D6: N3) | both ends tapped: the second thread N follows M, e.g. E-PSFJW6-50-M3-N3 (choices for D6: N3) | yes |
| E-PSFJW6-50-M3-N9 | N9 is not offered for D6 (coarse selection p.436: N3) | N9 is not offered for D6 (coarse selection p.436: N3) | yes |
| E-PSFJZ6-50-M3-N3 | E-PSFJZ6 needs its wrench flat after N: SC<n> (one set) or WSC<n>-X<m> (two sets) (p.435) | E-PSFJZ6 needs its wrench flat after N: SC<n> (one set) or WSC<n>-X<m> (two sets) (p.435) | yes |
| E-PSFJZ6-50-M3-N3-SC0-SC5 | alteration SC given twice | alteration SC given twice | yes |
| E-SFJ6-20-WSC5 | WSC needs the distance between the two flats: WSC12-X8 | WSC needs the distance between the two flats: WSC12-X8 | yes |
| E-SFJ20-300-SC5-WSC12-X8 | SC cannot be combined with WSC (p.432) | SC cannot be combined with WSC (p.432) | yes |
| E-SFJ20-300-FC20-A5-WFC10-A5-E5 | FC cannot be combined with WFC (p.432) | FC cannot be combined with WFC (p.432) | yes |
| E-SFJ6-20-FC10 | FC needs its position from an end: FC10-A8 (from the left end) or FC10-E8 (from the right end) | FC needs its position from an end: FC10-A8 (from the left end) or FC10-E8 (from the right end) | yes |
| E-SFJ6-20-FC10-A1 | A(E) = 0 or A(E) >= 2 | A(E) = 0 or A(E) >= 2 | yes |
| E-SFJ6-20-WFC10-A8 | WFC needs both positions: WFC10-A8-E20 | WFC needs both positions: WFC10-A8-E20 | yes |
| E-SFJ6-20-SC0-SC1 | alteration SC given twice | alteration SC given twice | yes |
| E-SFJ6-20-SC5.5 | unknown or unsupported alteration 'SC5.5' (supported: FC, LKC, SC, WFC, WSC) | unknown or unsupported alteration 'SC5.5' (supported: FC, LKC, SC, WFC, WSC) | yes |
| E-SFJ6-20-A5 | unknown or unsupported alteration 'A5' (supported here: FC, LKC, SC, WFC, WSC) | unknown or unsupported alteration 'A5' (supported here: FC, LKC, SC, WFC, WSC) | yes |
| E-SFJ6-20-SX5 | alteration SX is not offered for E-SFJ (p.432); offered: FC, LKC, SC, WFC, WSC | alteration SX is not offered for E-SFJ (p.432); offered: FC, LKC, SC, WFC, WSC | yes |
| E-SFJ6-20.5 | length 20.5 mm: lengths are in 1 mm steps; 0.1 mm steps need the LKC alteration | length 20.5 mm: lengths are in 1 mm steps; 0.1 mm steps need the LKC alteration | yes |
| E-SFJ6-5.5-LKC | length 5.5 mm outside 20-800 mm for E-SFJ6 (p.432 table) | length 5.5 mm outside 20-800 mm for E-SFJ6 (p.432 table) | yes |
| E-SFJ6-20-LKC-LKC | alteration LKC given twice | alteration LKC given twice | yes |
| E-PSFJ4-30-SC0 | SC / WSC apply to D = 6 or more (p.432) | SC / WSC apply to D = 6 or more (p.432) | yes |
| E-SFJ12-100-SC95 | SC + l1 = 105 exceeds L = 100 (p.432: SC + l1 <= L) | SC + l1 = 105 exceeds L = 100 (p.432: SC + l1 <= L) | yes |
| E-SFJ12-100-SC0-SX90 | alteration SX is not offered for E-SFJ (p.432); offered: FC, LKC, SC, WFC, WSC | alteration SX is not offered for E-SFJ (p.432); offered: FC, LKC, SC, WFC, WSC | yes |
| E-SFJ12-100-WSC0-X90 | WSC + X + 2 x l1 = 110 must be less than L = 100 (p.432) | WSC + X + 2 x l1 = 110 must be less than L = 100 (p.432) | yes |
| E-SFJ12-100-FC70 | FC needs its position from an end: FC10-A8 (from the left end) or FC10-E8 (from the right end) | FC needs its position from an end: FC10-A8 (from the left end) or FC10-E8 (from the right end) | yes |
| E-SFJ40-100-FC20 | O.D. 40 is applicable only to E-PSFJ (p.432 note) | O.D. 40 is applicable only to E-PSFJ (p.432 note) | yes |
| E-SFJ12-100-FC10-A1 | A(E) = 0 or A(E) >= 2 | A(E) = 0 or A(E) >= 2 | yes |
| E-SFJ12-100-FC10-A95 | the flat does not fit in the length | the flat does not fit in the length | yes |
| E-SFJ12-100-WFC10-A60-E60 | the two flats overlap | the two flats overlap | yes |
| E-SFJ12-100-SC0-FC10-A9 | machined parts need more than 2 mm between them (p.432 note) | machined parts need more than 2 mm between them (p.432 note) | yes |
| E-PSFJC6-40-M3-SC0-SX1 | machined parts need more than 2 mm between them (p.434 note) | machined parts need more than 2 mm between them (p.434 note) | yes |
| E-PSFJC6-40-M3-SC0-SX90 | SC + SX + 2 x l1 = 106 must be less than L = 40 (p.434) | SC + SX + 2 x l1 = 106 must be less than L = 40 (p.434) | yes |
| E-PSFJC6-40-M3-SC0-WSC5-X5 | alteration WSC is not offered for E-PSFJC (p.434); offered: FC, LKC, SC, SX, WFC | alteration WSC is not offered for E-PSFJC (p.434); offered: FC, LKC, SC, SX, WFC | yes |
| E-PSFJC6-40-M3-SC50 | SC + l1 = 58 exceeds L = 40 (p.434: SC + l1 <= L) | SC + l1 = 58 exceeds L = 40 (p.434: SC + l1 <= L) | yes |
| E-PSFJT6-20-M6 | M6 is not offered for D6 (coarse selection p.433: M3) | M6 is not offered for D6 (coarse selection p.433: M3) | yes |
| E-PSFJZ6-20-M3-N3-SC0 | length 20 mm outside 25-600 mm for E-PSFJZ6 (p.435 table) | length 20 mm outside 25-600 mm for E-PSFJZ6 (p.435 table) | yes |
| E-PSFJW6-30-M3-N3-LKC-WSC5 | WSC needs the distance between the two flats: WSC12-X8 | WSC needs the distance between the two flats: WSC12-X8 | yes |
| E-SFJW35-300-M8-N8 | O.D. 35 is applicable only to E-PSFJW (p.436 note) | O.D. 35 is applicable only to E-PSFJW (p.436 note) | yes |
| E-PSFPG8-200-F4-P6-M3 | E-PSFPG8 needs its wrench flat position SC after the thread, e.g. ...-SC0 (p.437 ordering example) | E-PSFPG8 needs its wrench flat position SC after the thread, e.g. ...-SC0 (p.437 ordering example) | yes |
| E-PSFPG8-200-F4-M3-SC0 | a stepped shaft needs the step length F and diameter P after L, e.g. E-PSFPG8-200-F4-P6-M3-SC0 | a stepped shaft needs the step length F and diameter P after L, e.g. E-PSFPG8-200-F4-P6-M3-SC0 | yes |
| E-PSFPG8-200-P6-M3-SC0 | a stepped shaft needs the step length F and diameter P after L, e.g. E-PSFPG8-200-F4-P6-M3-SC0 | a stepped shaft needs the step length F and diameter P after L, e.g. E-PSFPG8-200-F4-P6-M3-SC0 | yes |
| E-PSFPG8-200-F4-P6-SC0 | a stepped shaft needs its thread M after P, e.g. E-PSFPG8-200-F4-P6-M3-SC0 (choices for D8: M3) | a stepped shaft needs its thread M after P, e.g. E-PSFPG8-200-F4-P6-M3-SC0 (choices for D8: M3) | yes |
| E-PSFPG8-200-F4-P6-M4-SC0 | M4 is not offered for D8 (coarse selection p.437: M3) | M4 is not offered for D8 (coarse selection p.437: M3) | yes |
| E-PSFPG8-200-F4-P6-M6-SC0 | M6 is not offered for D8 (coarse selection p.437: M3) | M6 is not offered for D8 (coarse selection p.437: M3) | yes |
| E-PSFPG8-200-F4-P5-M3-SC0 | P5 is outside P 6-6 for D8 (p.437 table) | P5 is outside P 6-6 for D8 (p.437 table) | yes |
| E-PSFPG8-200-F4-P6-MD3-SC0 | MD applies to D = 12-30 and M = 6-20 (p.437), not D8 M3 | MD applies to D = 12-30 and M = 6-20 (p.437), not D8 M3 | yes |
| E-PSFPG30-200-F10-P20-MD3-SC0 | M3 is not offered for D30 (coarse selection p.437: M5, M6, M8, M10, M12, M16, M20, M24) | M3 is not offered for D30 (coarse selection p.437: M5, M6, M8, M10, M12, M16, M20, M24) | yes |
| E-PSFPG12-200-F8-P10-MD4-SC0 | MD applies to D = 12-30 and M = 6-20 (p.437), not D12 M4 | MD applies to D = 12-30 and M = 6-20 (p.437), not D12 M4 | yes |
| E-PSFPG20-12-F8-P10-MD10-SC0 | M10 does not fit into the step P10 | M10 does not fit into the step P10 | yes |
| E-PSFPG8-200-F4-P6-M3-SC0-FC10-A5 | FC on a stepped shaft is given from the right end only: FC10-E8 (p.437) | FC on a stepped shaft is given from the right end only: FC10-E8 (p.437) | yes |
| E-PSFPG8-200-F4-P6-M3-SC0-LFC4 | LFC needs its distance from the step end: LFC10-A0 (p.437) | LFC needs its distance from the step end: LFC10-A0 (p.437) | yes |
| E-PSFPG8-200-F4-P6-M3-SC0-LFC9-A0 | LFC + A = 9 exceeds the step length F = 4 (p.437: LFC + A <= F) | LFC + A = 9 exceeds the step length F = 4 (p.437: LFC + A <= F) | yes |
| E-PSFPG8-200-F4-P6-M3-SC0-LFC1-A9 | LFC + A = 10 exceeds the step length F = 4 (p.437: LFC + A <= F) | LFC + A = 10 exceeds the step length F = 4 (p.437: LFC + A <= F) | yes |
| E-PSFPG8-200-F4-P6-M3-SC0-LFC0-A0 | LFC must be at least 1 mm | LFC must be at least 1 mm | yes |
| E-PSFPG8-900-F4-P6-M3-SC0 | overall length (Y) = 904 mm exceeds the maximum 800 mm for D8 (p.437 table) | overall length (Y) = 904 mm exceeds the maximum 800 mm for D8 (p.437 table) | yes |
| E-PSFPH8-200-F5-P6-M3-SC0 | both ends stepped: the right step length T follows M, e.g. E-PSFPH8-200-F4-P6-M3-T4-SC0 | both ends stepped: the right step length T follows M, e.g. E-PSFPH8-200-F4-P6-M3-T4-SC0 | yes |
| E-PSFPH8-200-F5-P6-M3-T5 | E-PSFPH8 needs its wrench flat position SC after the thread, e.g. ...-SC0 (p.438 ordering example) | E-PSFPH8 needs its wrench flat position SC after the thread, e.g. ...-SC0 (p.438 ordering example) | yes |
| E-PSFPH8-200-F5-P6-M3-T5-SC0-LKC | alteration LKC is not offered for E-PSFPH (p.438); offered: SC | alteration LKC is not offered for E-PSFPH (p.438); offered: SC | yes |
| E-PSFPH8-200-F5-P6-MD3-T5-SC0 | MD (effective tap length M x 3) is an alteration of p.437 only | MD (effective tap length M x 3) is an alteration of p.437 only | yes |
| E-PSFPG8-2-F4-P6-M3-SC0 | length 2 mm outside 25-998 mm for E-PSFPG8 (p.437 table) | length 2 mm outside 25-998 mm for E-PSFPG8 (p.437 table) | yes |
| E-PSFPG8-200-F4-P6-M3-SC0-WSC5-X5 | alteration WSC is not offered for E-PSFPG (p.437); offered: FC, LFC, LKC, SC, SX, WFC | alteration WSC is not offered for E-PSFPG (p.437); offered: FC, LFC, LKC, SC, SX, WFC | yes |
| E-PSFPG8-200-F4-P6-M3-SC0-SC1 | alteration SC given twice | alteration SC given twice | yes |
| E-PSFPG8-200-F4-P6-M3-SC0-WFC10-A8 | WFC needs both positions: WFC10-A8-E20 | WFC needs both positions: WFC10-A8-E20 | yes |

| change L of | to | changed in place vol / area / bbox / faces | direct code (inserted) | python | equal (changed = direct = python) |
|---|---|---|---|---|---|
| E-PSFJT12-60-M6 | 100 | 11074.11 / 4184.60 / 100x12x12 / 5 | 11074.11 / 4184.60 / 100x12x12 / 5 | 11074.11 / 4184.60 / 100x12x12 / 5 | yes |
| E-PSFJZ6-50-M3-N3-SC0 | 200 | 5577.96 / 3917.55 / 200x6x6 / 11 | 5577.96 / 3917.55 / 200x6x6 / 11 | 5577.96 / 3917.55 / 200x6x6 / 11 | yes |
| E-SFJC20-300-M10-SC5-FC40-E20 | 500 | 155076.64 / 32607.82 / 500x20x20 / 14 | 155076.64 / 32607.82 / 500x20x20 / 14 | 155076.64 / 32607.82 / 500x20x20 / 14 | yes |
| E-PFPGH30-800-F30-P20-M16-T25-SC40 | 600 | 431145.33 / 64272.23 / 655x30x30 / 17 | 431145.33 / 64272.23 / 655x30x30 / 17 | 431145.33 / 64272.23 / 655x30x30 / 17 | yes |
| E-PSFPG25-400-F20-P16-MD10-SC30-WFC20-A50-E50 | 700 | 344954.21 / 57846.81 / 720x25x25 / 19 | 344954.21 / 57846.81 / 720x25x25 / 19 | 344954.21 / 57846.81 / 720x25x25 / 19 | yes |
| E-PSSFJZ16-300-M8-N6-WSC20-X30-LKC | 450 | 89451.89 / 23580.16 / 450x16x16 / 19 | 89451.89 / 23580.16 / 450x16x16 / 19 | 89451.89 / 23580.16 / 450x16x16 / 19 | yes |
| E-SFJ20-300-SC5 | 150 | 46909.80 / 10084.70 / 150x20x20 / 9 | 46909.80 / 10084.70 / 150x20x20 / 9 | 46909.80 / 10084.70 / 150x20x20 / 9 | yes |

## What SolidCraft 0.50.0 could not express (exact errors) and the workarounds

1. **Free parameter values on an inserted part.** `component.insert_design {path, configuration, parameters: {L: "777 mm"}}` is accepted and
   ignored (the bodies keep L 60 / 100: no error, no effect); `component.set_link_parameters` and `generator.parse` / `generator.insert` are
   `unknown command`. So the harness inserts a row of the code (`config.row from=<D>` with the parameters as cells) and "stays parametric" is shown on
   the model itself with `parameters.change L` (table above). Needed from #23175: the `parameters` of the interface document (section 1).
2. **A thread designation from a parameter, and a hole that follows its face** (S8). One `solid.hole` per size and host face (44 features), because
   the designation is fixed and the hole is bound to the face it was picked on:
   `Tap L step M6: the reference `F4:bottom` no longer exists as it was picked; reselect it` when the step is suppressed. Needed: a hole whose
   designation (or size) is an expression and whose host is "the end face at this x".
3. **M2.6.** `solid.hole thread=M2.6` -> `invalid parameters for `solid.hole`: M2.6 has no coarse ISO pitch: give one, e.g. M2.6x0.25 or M2.6x0.2`.
   The Python generator lists M2.6 for E-PSFJW5 and cannot build it either; neither side is compared, the parametric model has no M2.6 feature, and
   `m_left = 2.6 mm` is outside the allowed values (rule `m_left-values`). Needed: the pitch in the table (`M2.6x0.45`), as the interface allows.
4. **A feature of zero size cannot exist while it is suppressed in the saved model.** `solid.cylinder height=F` with `F = 0 mm`:
   `invalid input: extrude distance is zero`. The model is drawn with F, T > 0 and its rows set them to 0 with the step suppressed by the rule `F > 0`.
5. **The option set.** See "The ordering code": `set(...)` is each-once with an object value; the bag with an ordered list is what the shaft needs.
6. **Limits stop at the row.** `config.row ... param:L = 5 mm` is refused (`configuration rules: rule `Length 10 to 1500 mm (S8 p.432 spec table)`
   restricts the final value`), as the interface says; the per-D and per-family ranges of the catalogue (different for each of the 7 families) are
   data of the script, not of the model: a rule's `parameter_range` has no per-row value, so they stay in Rhai, next to the other refusals.
7. **Trailing separator.** The template engine skips a trailing `-`: the bag refuses a dangling dash itself (`E-PSFJ6-20-` reads no code), the catch-all
   template then gives the `expected ...` refusal, as Python does.


This feature requires the #23175 surface (unavailable on 0.50.0/0.51.1); the errors above are from 0.50.0.
The optional link proof is declared in `link_checks.json` and run by `ci.sh` through `runtime.parametric.links`. It adds insertion, link-edit, and out-of-range refusal rows only when the command catalogue lists `component.set_link_parameters`. Release builds retain their existing rows and link dependency item.

### #23175 checks

The 0.50.0/0.51.1 results above remain release observations. The #23175 CI artifact records 42 valid, 94 rejects, 10 rebuild checks and 2 blocked records. The next CI run also checks link overrides and ordinary edit refusal with `enforce_on_edit` where limit rules exist; these new checks are pending. Differences remain differences.

Unordered option set with arguments: follow-up after #23175: an ordered bag/list option kind beside set(...). The local bag(...) remains.

The supplied #23175 artifact includes 3 link checks; the added ordinary-edit enforcement check awaits CI.
