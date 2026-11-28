# misumi.hfs.extrusion as a parametric SolidCraft generator

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai, and rules addressed by feature name requires the #23175 surface (unavailable on 0.50.0/0.51.1). The exact command errors quoted below are observations from SolidCraft 0.50.0. On capable hosts, link overrides and ordinary source `parameters.change` enforce limit rules marked `enforce_on_edit`.

The extrusion modelled ONCE in SolidCraft (`hfs-extrusion/hfs-extrusion.sc`), a configuration table of the catalogue rows, the ordering code as a
field template and the logic as plain Rhai, following SolidCraft's generator interface (`docs/formats/generator.md`, version 2, issue 22331). The
Python generator in `../src` is untouched and is the reference every code below is compared with.

```
hfs-extrusion/                 the package layout of the interface document
  generator.toml               [parameters], [[template]], [rows."<profile>"] source / page / status per configuration row
  hfs-extrusion.sc             the parametric model + its configuration table + its rules (built by build.py)
  generator.rhai               resolve(fields) -> #{configuration, parameters, properties}; fields(configuration, parameters) -> fields
  tables/*.csv                 sections, types, params: generated from ../data/*.csv by pkgfiles.py (rows keep source, page, status)
build.py                       builds the model with solidcraft-cli
pkgfiles.py  lin.py            tables and generator.toml; expression helper for the sketch points
run_codes.py  report.py        the end-to-end proof (results.json) and the tables below
../../../../runtime/fieldtemplate.py   stand-in for the field-template parser and printer (doc section 3), shared with the HIWIN MG proof; this
                                       generator added the inline per-field escape class and separators skipped (not stripped) in the code
../../../../runtime/rhai-run/          stand-in host for generator.rhai, shared with the MG proof: the real Rhai engine (crate rhai 1.27), the
                                       documented sandbox limits, typed table cells, table() / refuse() / code_template(), JSON in and out
```

## How the model is built (all of it worked on SolidCraft 0.50.0)

- **One model, parameters.** 26 user parameters: the section dimensions (`w h corner_r tip_r mouth lip cavity d0 floor_half depth`), `profile`,
  `part_type` (a text parameter: catalogue type, only material / finish), `length`, `fixed`, the end options (`tap_l tap_r`), the wrench-hole options
  (`wl_rows wl_dir wl_shift wr_rows wr_dir wr_shift`) and the hole table (`wh_h wh_j wh_k wh_d`); the hole positions `wl_x1..` / `wr_x1..` are
  derived user parameters (`wr_x1 = length - (wh_h - wr_shift)`).
- **Section sketches are parametric.** Every outline coordinate of the four sketches is an expression over the section parameters
  (`"0.5*w - depth + 10"`), the corner and lip-tip rounds are `corner_r` / `tip_r`. The central voids of the 2040 / 4040 and the bores are the
  drawing's fixed numbers (not parametric: they are not printed dimensions, see `generator.toml` of the generator, "not guaranteed").
- **Configuration table = the catalogue rows.** One row per profile (`2020 2040 4040 3030`, from `data/profiles.csv`, source and page in
  `generator.toml [rows."..."]`). Its parameter cells are the section dimensions, `profile`, the hole table; its **suppression columns** switch the
  per-profile topology: `Profile<k>` / `Extrusion<k>` (the sketch and extrusion of that section: 2020 and 3030 have one slot per side, 2040 two
  slots on two sides and a hexagonal void, 4040 two slots per side and the four-arm void with its bore notches) and the end-tap features
  `Tap<L|R><k>_<n>` (2020 one M5 bore per end, 2040 two, 4040 four, 3030 one M8). Activating the row switches the whole section in one step.
- **Suffix options = parameters + `drive_suppression` rules.** `tap_l` / `tap_r` switch the tap features of the active profile; the wrench holes
  are 12 cylinder cuts (left/right x row 1..3 x horizontal/vertical, a cylinder's axis cannot be a parameter), each with an on-rule and an off-rule
  over `wl_rows` / `wl_dir` (`wl_rows >= 2 and wl_dir == 0`). The holes are cut through the whole section, `diameter = wh_d`, centre `wl_x1` ...
  Limits are rules: `length` 50..4000 mm, `K` types allow 1000 / 4000 only, `wh_d` 7.35 on the 5 series and 5 / 8 on the 6 series, rows 0..3.
  62 columns (26 parameters + 36 features), 62 rules, 5 rows (the three suffix families need no row of their own).
- **Cosmetic end threads** (`solid.thread`, M5 depth 15 / M8 depth 24 on the printed pilot bores) sit before the wrench cuts in the timeline.

## The ordering code

`generator.toml`:
`[K:fixed]{part_type: text 3..8 [A-Za-z0-9]}-{profile: text 4..6 [0-9]}[-{length: decimal}][-{alts: text 1..80 [A-Za-z0-9-]}]`.
The alterations are one text field (`LTP-RTP-LCH`, any order, any count) that `generator.rhai` splits; every Python refusal, in its order and with
its message, is a `refuse(kind, message)` in `generator.rhai` (`invalid` / `not_modelled` mirror `CodeError` / `NotModelled`). Defaults, derived
values (wrench hole diameter by series, the `FL`/`FR` shift of 3 mm, tolerance, description, material and surface by type and profile) are plain Rhai
over `tables/*.csv`. `fields(configuration, parameters)` is the inverse (code printing for a bill of materials; canonical order, `LTP-RTP` prints
`TPW`): for all 16 codes parse(print(parse(code))) gives the same configuration and parameters.

## What was run

For every line of `../codes.txt` (all 16 valid codes, including `HFS5-2020-1000-LTP-RTP` and `HFS5-2020-300-TPW-RWV`; the 6 `!` rejects) plus 20
extra refusals: code -> template -> Rhai `resolve` -> a row for the code (`config.row from=<profile row>`) in a working copy of the model -> a
design inserts that copy with `component.insert_design {configuration}` -> `inspect.measure` (volume, area, bbox, faces) + `model.threads` + the
unchanged `src/check.py` spec check (run on the inserted part, with the `ext.Extrusion` it needs rebuilt from the Rhai result, never from the Python
parser) -> the same code built by the Python generator and measured the same way.

```
# build the model, the tables, run everything (on a build host, not on a workstation); SC_CLI = solidcraft-cli 0.50.0
<queue-runner> run <project> <worktree> --work --output wk/res --max-runtime 1h -- bash -c 'set -e; B=<solidcraft bin dir>; export SC_CLI=$B/solidcraft-cli;
  (cd runtime/rhai-run && CARGO_TARGET_DIR=<dir> cargo build --release); export RHAI_RUN=<dir>/release/rhai-run;
  python3 vendors/misumi/hfs/extrusion/parametric/build.py;                      # hfs-extrusion.sc (and tables, generator.toml)
  python3 vendors/misumi/hfs/extrusion/parametric/run_codes.py --out wk/res/run;   # results.json
  python3 vendors/misumi/hfs/extrusion/parametric/report.py wk/res/run/results.json'
```

## Result: side by side

Volume mm3 / area mm2 / bbox mm / faces; the spec check column is passed rows / rows. Equal = same bodies, volume and area within 1e-6 relative,
same bbox and face count.

| code | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec check python | spec check parametric | equal |
|---|---|---|---|---|---|
| HFS5-2020-1000-LTP-RTP | 182832.3 / 172426.5 / 1000x20x20 / 59 | 182832.3 / 172426.5 / 1000x20x20 / 59 | 25/25 | 25/25 | yes |
| HFS5-2020-120-LTP-RTP-LCH | 21679.9 / 20989.6 / 120x20x20 / 75 | 21679.9 / 20989.6 / 120x20x20 / 75 | 28/28 | 28/28 | yes |
| HFS5-2020-300-TPW-RWV | 54329.8 / 51937.3 / 300x20x20 / 91 | 54329.8 / 51937.3 / 300x20x20 / 91 | 29/29 | 29/29 | yes |
| HFS5-2020-497.5-TPW-LEV-REH | 89399.4 / 85825.9 / 497.5x20x20 / 155 | 89399.4 / 85825.9 / 497.5x20x20 / 155 | 35/35 | 35/35 | yes |
| HFS5-2040-1000-TPW-RWV | 322742.4 / 312749.8 / 1000x20x40 / 136 | 322742.4 / 312749.8 / 1000x20x40 / 136 | 31/31 | 31/31 | yes |
| HFS5-2040-300-LTP-RTP-LCH | 96906.3 / 94247.1 / 300x20x40 / 104 | 96906.3 / 94247.1 / 300x20x40 / 104 | 30/30 | 30/30 | yes |
| HFS5-4040-300-TPW | 141729.5 / 143209.5 / 300x40x40 / 146 | 141729.5 / 143209.5 / 300x40x40 / 146 | 32/32 | 32/32 | yes |
| HFS5-4040-497.5-LTP-RCV | 234814.5 / 236814.5 / 497.5x40x40 / 154 | 234814.5 / 236814.5 / 497.5x40x40 / 154 | 33/33 | 33/33 | yes |
| HFS6-3030-500-LCH-X5-TPW | 166459.0 / 156875.1 / 500x30x30 / 65 | 166459.0 / 156875.1 / 500x30x30 / 65 | 33/33 | 33/33 | yes |
| HFSB6-3030-120-LTP-RTP-RWV-X8 | 39292.8 / 38122.9 / 120x30x30 / 67 | 39292.8 / 38122.9 / 120x30x30 / 67 | 34/34 | 34/34 | yes |
| KHFS5-2020-1000 | 182832.3 / 172426.5 / 1000x20x20 / 59 | 182832.3 / 172426.5 / 1000x20x20 / 59 | 22/22 | 22/22 | yes |
| KHFS5-2040-1000 | 323750.4 / 312822.0 / 1000x20x40 / 96 | 323750.4 / 312822.0 / 1000x20x40 / 96 | 23/23 | 23/23 | yes |
| KHFS6-3030-1000 | 333141.8 / 313051.7 / 1000x30x30 / 63 | 333141.8 / 313051.7 / 1000x30x30 / 63 | 27/27 | 27/27 | yes |
| NFSB5-2020-250 | 45708.1 / 43380.9 / 250x20x20 / 59 | 45708.1 / 43380.9 / 250x20x20 / 59 | 22/22 | 22/22 | yes |
| NFSB5-4040-250 | 118107.9 / 119498.7 / 250x40x40 / 146 | 118107.9 / 119498.7 / 250x40x40 / 146 | 26/26 | 26/26 | yes |
| NFS5-2040-300 | 97125.1 / 94299.8 / 300x20x40 / 96 | 97125.1 / 94299.8 / 300x20x40 / 96 | 23/23 | 23/23 | yes |

| rejected code | python message | parametric message | same |
|---|---|---|---|
| HFS5-2020-49-LTP | length 49 mm outside 50-4000 mm | length 49 mm outside 50-4000 mm | yes |
| KHFS5-2020-800 | fixed-length (K) extrusions come only in [1000, 4000] mm, not 800 | fixed-length (K) extrusions come only in [1000, 4000] mm, not 800 | yes |
| HFS5-2020-100-LTP-LTP | alteration LTP given twice | alteration LTP given twice | yes |
| HFS5-2020-100-ZZZ | unknown or unsupported alteration 'ZZZ' | unknown or unsupported alteration 'ZZZ' | yes |
| HFS5-2020-100.3 | length 100.3 mm is not a multiple of 0.5 mm | length 100.3 mm is not a multiple of 0.5 mm | yes |
| HFS6-3030-100-LTP-RWV-X7 | unknown or unsupported alteration 'X7' | unknown or unsupported alteration 'X7' | yes |
| HFS5-2020 | a length is required: the last number before the alterations, in mm | a length is required: the last number before the alterations, in mm | yes |
| HFS5-2020-LTP | a length is required: the last number before the alterations, in mm | a length is required: the last number before the alterations, in mm | yes |
| HFS7-2020-100 | 'HFS7-2020-100': expected [K]<type>5|6-<profile>-<length>[-<alteration>...], e.g. HFS5-2040-800-LTP-RTP | 'HFS7-2020-100': expected [K]<type>5|6-<profile>-<length>[-<alteration>...], e.g. HFS5-2040-800-LTP-RTP | yes |
| HFS5-6060-100 | profile '6060' not available for HFS5 here; verified for the 5 series: ['2020', '2040', '4040'] | profile '6060' not available for HFS5 here; verified for the 5 series: ['2020', '2040', '4040'] | yes |
| HFSY5-2040-100 | HFSY5 is listed for 2020 only (S1 p.530 type table has no HFSY5 for 2040) | HFSY5 is listed for 2020 only (S1 p.530 type table has no HFSY5 for 2040) | yes |
| NFSF5-2020-100 | NFSF5: valid 5 series type, but only ['CAF5', 'HFS5', 'HFSB5', 'HFSY5', 'NFS5', 'NFSB5'] are drawn | NFSF5: valid 5 series type, but only ['CAF5', 'HFS5', 'HFSB5', 'HFSY5', 'NFS5', 'NFSB5'] are drawn | yes |
| XYZ5-2020-100 | unknown 5 series type 'XYZ5'; known: ['CAF5', 'CAF6', 'EFS6', 'EFSB6', 'EFSC6', 'EFSF6', 'EFSH6', 'EFST6', 'GFS6', 'HFS5', 'HFS6', 'HFSB5', 'HFSB6', 'HFSC5', 'HFSC6', 'HFSF5', 'HFSF6', 'HFSFB5', 'HFSFB6', 'HFSH5', 'HFSH6', 'HFSL6', 'HFSLB6', 'HFSR5', 'HFST5', 'HFST6', 'HFSTB5', 'HFSTB6', 'HFSY5', 'HFSY6', 'NEFS6', 'NEFSB6', 'NEFSF6', 'NEFST6', 'NFS5', 'NFSB5', 'NFSF5', 'NFSL6', 'NFST5'] | unknown 5 series type 'XYZ5'; known: ['CAF5', 'CAF6', 'EFS6', 'EFSB6', 'EFSC6', 'EFSF6', 'EFSH6', 'EFST6', 'GFS6', 'HFS5', 'HFS6', 'HFSB5', 'HFSB6', 'HFSC5', 'HFSC6', 'HFSF5', 'HFSF6', 'HFSFB5', 'HFSFB6', 'HFSH5', 'HFSH6', 'HFSL6', 'HFSLB6', 'HFSR5', 'HFST5', 'HFST6', 'HFSTB5', 'HFSTB6', 'HFSY5', 'HFSY6', 'NEFS6', 'NEFSB6', 'NEFSF6', 'NEFST6', 'NFS5', 'NFSB5', 'NFSF5', 'NFSL6', 'NFST5'] | yes |
| HFS5-2020-100-SC-SC | alteration SC given twice | alteration SC given twice | yes |
| HFS5-2020-2000-SC | SC (high precision cut) applies to L <= 1500 mm only | SC (high precision cut) applies to L <= 1500 mm only | yes |
| HFS5-2020-100-LHP | LHP: heli-coil end tapping: parsed, not modelled | LHP: heli-coil end tapping: parsed, not modelled | yes |
| HFS5-2020-100-LCP | LCP: crisscross (P) layout is ambiguous in the catalogue text; use H or V | LCP: crisscross (P) layout is ambiguous in the catalogue text; use H or V | yes |
| HFS6-3030-100-RWV | the 6 series wrench hole diameter is selectable: add -X5 or -X8 (S3 p.759 footnote) | the 6 series wrench hole diameter is selectable: add -X5 or -X8 (S3 p.759 footnote) | yes |
| HFS5-2020-100-RWV-X5 | X5/X8 (wrench hole diameter) applies to the 6 series; the 5 series hole is d7.35 | X5/X8 (wrench hole diameter) applies to the 6 series; the 5 series hole is d7.35 | yes |
| HFS5-2020-100-X5 | X5/X8 sets the wrench hole diameter; there is no wrench hole alteration in this code | X5/X8 sets the wrench hole diameter; there is no wrench hole alteration in this code | yes |
| HFS5-2020-100-FL | FL shifts a wrench hole on the left end, but there is none | FL shifts a wrench hole on the left end, but there is none | yes |
| HFS5-2020-30-LTP-RTP | length 30 mm outside 50-4000 mm | length 30 mm outside 50-4000 mm | yes |
| HFS5-2020-100-LCH-LCV | two wrench-hole options for the left end | two wrench-hole options for the left end | yes |
| HFS5-2020-100-LWH-RWH-RCH | two wrench-hole options for the right end | two wrench-hole options for the right end | yes |
| KHFS5-2020-1000-LTP | alterations apply to configurable-length extrusions only (fixed-length K types have none) | alterations apply to configurable-length extrusions only (fixed-length K types have none) | yes |
| HFS5-2020-4001 | length 4001 mm outside 50-4000 mm | length 4001 mm outside 50-4000 mm | yes |

| change length of | to | changed-in-place vol / area / bbox / faces | direct code (inserted) | python | equal (changed = direct = python) |
|---|---|---|---|---|---|
| HFS5-2020-1000-LTP-RTP | 300 | 54849.7 / 51983.9 / 300x20x20 / 59 | 54849.7 / 51983.9 / 300x20x20 / 59 | 54849.7 / 51983.9 / 300x20x20 / 59 | yes |
| HFS5-2020-300-TPW-RWV | 800 | 145745.9 / 137967.7 / 800x20x20 / 91 | 145745.9 / 137967.7 / 800x20x20 / 91 | 145745.9 / 137967.7 / 800x20x20 / 91 | yes |
| HFS5-4040-300-TPW | 1500 | 708647.4 / 712267.9 / 1500x40x40 / 146 | 708647.4 / 712267.9 / 1500x40x40 / 146 | 708647.4 / 712267.9 / 1500x40x40 / 146 | yes |

All 16 codes: the parametric part has the same volume, area, bbox and face count as the Python part, and all 16 pass the same spec check with
the same number of rows. Every refusal (the 6 of `codes.txt` and 20 more, compared with `ext.parse`) has the Python message word for word, shape errors included (the stand-in
reports a code that matches no template through the `a length is required` / `expected [K]<type>...` rules of `generator.rhai`, because the template is lenient).

**One difference, cosmetic.** The cosmetic thread annotations of a tapped end that a wrench hole crosses: the Python build places the thread
after the hole cut, so its length is shortened (`[0, 6.984]`, `[293.016, 300]`); the parametric model has to place the thread BEFORE the cuts (see
"SolidCraft 0.50.0 observations", first item) so it stays full length (`[0, 15]`, `[285, 300]`). The bores and the solid are identical (the spec
check, whose rule for tapped ends crossed by a wrench hole is "depth <= 15", passes); the other tapped-end codes (no wrench hole on that end) have
identical thread ranges.

## It stays parametric (item 4)

Row for the code, activate it, then `parameters.change length` on the configured design; compared with the direct code inserted the same way and
with the Python part: identical in all three cases (the table's last block), including the right wrench holes (`wr_x1 = length - ...`
moves) and the right-end taps, which follow the new end.

## SolidCraft 0.50.0 observations (exact errors) and workarounds

1. **A cosmetic thread cannot take its face or its end from a parameter, and does not follow a later cut.** `solid.thread` with
   `face: ["length-0.5", 2.1, 0]` -> `invalid parameters for solid.thread: face must be a point [x, y, z] on a cylindrical face`. A thread created
   after a cut that splits its bore later fails to rebuild when that cut is switched on: `config.row ... configuration T1 would fail to rebuild:
   TapL2020_1: the reference F4:side:c1 no longer exists as it was picked; reselect it`. Workaround (labelled, closest faithful): the threads come
   first in the timeline with a point 0.5 mm inside the end of a 1000 mm model, and follow `length` through the face reference; they are then not
   shortened by a crossing hole (above).
2. **A free parameter value on an inserted part requires the #23175 surface (unavailable on 0.50.0/0.51.1).** `component.insert_design {path, configuration: "2020", parameters: {length: "777 mm"}}` is
   accepted and the key ignored (the part comes in 1000 mm long, no error); `component.set_link_parameters` -> `unknown command`;
   `generator.parse` / `generator.insert` -> `unknown command`. `parameters.change length 777 mm` in the host design returns `recomputed: 0` and
   leaves the inserted part unchanged. Workaround (labelled): a row for the code in a working copy of the model (`config.row {from: <profile row>,
   values: {...}}`), inserted with `configuration`; to change the length, change it in the working copy (or its row) and insert again.
3. **Limits on ordinary edits and the 0.5 mm grid.** `parameters.change length 20 mm` is accepted (the range rule 50..4000 only acts on rows:
   `config.row ... values {param:length: "20 mm"}` -> `rule Length 50 to 4000 mm ... restricts the final value`); `777.3 mm` in a row is accepted: a
   `parameter_range` has no step, so the 0.5 mm grid is only enforced by `resolve`.
4. **A cylinder's axis, and a count of different features, cannot be a parameter.** Horizontal / vertical wrench holes and left / right, rows 1..3
   are 12 cut features with 24 on/off rules; `solid.pattern.rectangular` with `count1 = wl_rows` would do rows of equal spacing J = K but not the
   catalogue's separate J and K, and a count of 0 is not allowed (so a suppression rule is needed anyway).
5. **Rules addressed by feature name need #23175 (our draft, being finished).** In 0.50.0, rules name features by integer id (`config.rule` schema: `feature` is an integer), so the generated model is built in two passes (the ids come
   from the replies); a name would keep the rules readable.
6. **Body names collide:** four extrusions named alike get `Body1` / `Extrusion2020 (2)`, so each profile's extrusion has its own body name and
   cuts are written without `targets`.

## What does not fit the interface document, and proposals

| Where | What the extrusion needs | Proposal |
|---|---|---|
| 3 field templates | one repeatable, unordered suffix (`-LTP-RTP-LCH`, `-X5`): not a field kind | a list kind `{alts: list LTP\|RTP\|TPW\|LCH ...}` giving an array; or keep one free text field (what is done here) and split in Rhai |
| 3 escape pattern | the document has one `escape` per template, three text fields need three classes (`[A-Za-z0-9]`, `[0-9]`, `[A-Za-z0-9-]`) | a class after the length: `{alts: text 1..80 [A-Za-z0-9-]}` (implemented in the stand-in) |
| 3 / 4 shape errors | a code that matches no template gets the engine's message, not the generator's | optional `fn no_match(raw)` in `generator.rhai` returning the message |
| 4 `resolve` return | description, material, finish, tolerance, notes per code | `properties: #{...}` (done here) written to the component's properties by `generator.insert` |
| 4 inverse | `generator.code {parameters}` needs parameters -> fields; the interface only has the template printer | optional `fn fields(configuration, parameters)` (done here) |
| 2 `[parameters]` | a text parameter (`part_type`) and a decimal with a step (`length`, 0.5 mm) | `type = "text"` and `"decimal"` with `step` |
| 5 sandbox | the limit of 16 for expression depth inside a function is hit by a message built from 8 `+` terms, by an `if / else if` chain of 8, and by a closure in a nested block (`ExprTooDeep`); Rhai passes arguments by value, so helper functions return the map they change | document it; or raise the function depth to 32 |
| 4 free parameter on a link | see observation 2 | `parameters` on `component.insert_design`, checked against the source's range rules, plus `step` on `parameter_range` |
| model | thread follows its bore, threads placed by a parameter | `solid.thread` face / from as expressions or `end: left|right`; a cosmetic thread that follows a later cut |
| rules | name a feature by name; a suppress-if that reads a parameter in the feature itself | `feature` by name in `config.rule` |

What fits the extrusion without change: per-profile topology as suppression columns of the configuration rows (one activation switches sketch,
extrusion and taps), options as `drive_suppression` rules, limits as `parameter_range` / allowed values, per-row source and page in `generator.toml`,
`generator.rhai` with `table()` / `refuse()` / `code_template()` (all 26 rejects and 16 codes), the field template for the code shape, the round trip.


The optional link proof is declared in `link_checks.json` and run by `ci.sh` through `runtime.parametric.links`. It adds insertion, link-edit, and out-of-range refusal rows only when the command catalogue lists `component.set_link_parameters`. Release builds retain their existing rows and link dependency item.

### #23175 checks

The 0.50.0/0.51.1 results above remain release observations. The #23175 CI artifact records 16 valid, 26 rejects, 6 rebuild checks and 1 blocked records. The next CI run also checks link overrides and ordinary edit refusal with `enforce_on_edit` where limit rules exist; these new checks are pending. Differences remain differences.

A cosmetic thread created after a cross cut stops at the cut: follow-up: tangency-labs/solidcraft#23507.

The supplied #23175 artifact includes 3 link checks; the added ordinary-edit enforcement check awaits CI.
