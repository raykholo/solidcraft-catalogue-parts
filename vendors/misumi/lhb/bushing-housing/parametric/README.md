# misumi.lhb.bushing-housing as a parametric SolidCraft generator

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai, and rules addressed by feature name needs #23175 (our draft, being finished). The exact command errors quoted below are observations from SolidCraft 0.50.0. The draft checks ranges on link overrides; ordinary source `parameters.change` still does not enforce range restrictions.

The housing modelled ONCE in SolidCraft (`bushing-housing/bushing-housing.sc`), a configuration table of the catalogue rows, the ordering code as a field template and
the logic as plain Rhai, following SolidCraft's generator interface (`docs/formats/generator.md`, version 2, issue 22331). The Python generator in `../src`
is untouched and is the reference every code below is compared with. CI (`.github/workflows/parametric.yml`) builds the model and runs everything below on
SolidCraft 0.50.0 for every change: `ci.sh OUTDIR` writes `OUTDIR/faithfulness.json` and `tools/parametric-verdict` decides.

```
bushing-housing/                  the package layout of the interface document
  generator.toml               [parameters], two [[template]] entries, [rows."<configuration row>"] source / page / status per row
  bushing-housing.sc                    the parametric model + its configuration table + its rules (built by build.py; CI rebuilds it on every run)
  generator.rhai               resolve(fields) -> #{configuration, parameters, properties}; fields(configuration, parameters) -> fields
  tables/*.csv                 the catalogue rows (copies of ../data/*.csv with a key column; each row keeps source, page, status)
build.py                       writes tables/ and generator.toml, then builds the model with solidcraft-cli (--package-only: no SolidCraft)
run_codes.py  report.py        the end-to-end proof (results.json) and the tables below
faithfulness.py  ci.sh         results.json -> faithfulness.json for tools/parametric-verdict; the one command CI runs
../../../../../-m runtime.parametric.kit       harness shared with the other lhb housings (solidcraft-cli runs, the model build in two stages, rebuilds, README tables)
../../../../../runtime/fieldtemplate.py  stand-in for the field-template parser and printer (doc section 3), shared with the HFS and MG proofs; these
                                          generators added the required separator `\-` (a character that must be present as written)
../../../../../runtime/rhai-run/         stand-in host for generator.rhai (the real Rhai engine, the documented sandbox limits, table() / refuse() / code_template())
```

## How the model is built (all of it worked on SolidCraft 0.50.0)

- **One model, parameters.** 17 user parameters per catalogue row (`dr bl l1 bw bh hb h1 h2 w1 td pd dp dl dwx dwy dowel dowel_ok`: bore, length, hole spacings, width, height, the
  catalogue H1 / H2, thread depth, pilot and dowel sizes), plus the appearance constants `wall_step` (1 mm) and `foot_frac` (0.16), which are the Python generator's
  (appearance, approximate) choices and not catalogue values. The profile is one closed ten-point sketch of expressions (`"bw / 2 - wall_step"`, `"bh - h1"`), extruded
  over `bl` from a sketch plane at `bl / 2`. The shaft bore is a cylinder cut at `bh - hb`.
- **Configuration table = the catalogue rows.** 40 rows named `<series>-<dr>` (single 12, medium 8, double 11, medium long 4, long 5; `data/single.csv`, `data/double.csv`, source and page
  per row in `generator.toml`). 31 columns: the 17 parameters and 14 suppression columns for the features that differ between rows.
- **Thread size and the third mounting row = suppression columns.** The tapped holes are one `solid.hole` feature per size (`Mounting thread M4 / M5 / M6 / M8 / M10`, thread
  designation is not a parameter), only the row's size is live. The Long type has a third mounting row: its two holes are separate features (`... mid M<k>`, `Pilot hole 5`, `Pilot hole 6`)
  live on the Long rows only, instead of a pattern whose count is 2 or 3. The pilot holes `d` run through the full height.
- **The dowel option (-P) = a parameter + `drive_suppression` rules.** `dowel` (0 or 1) switches the two dowel cylinders; their position is two row parameters `(dwx, dwy)`: on the mounting-hole row
  at mid-length for single, medium and double (`dwx = W1 / 2, dwy = 0`), on the centre line at the end mounting holes for medium long and long (`dwx = 0, dwy = L1 / 2`), as the Python
  generator reads the figures (appearance, approximate). `dowel_ok = 0` on the two rows with no dowel data (dr 6 single and medium) and an `allow_parameter_values` rule then allows only 0.

## The ordering code

`generator.toml`, first template (the second one, `{raw: text 1..128 [ -~]}`, takes any other text so that `generator.rhai` can refuse it with the
Python shape message, `'<code>': expected ...`):

```
E\-LBHN[W:double]{dr: text 1..2 [0-9]}[{length: D|L}][\-P:dowel]
```

`E-LBHN[W]<dr>[D|L][-P]`: `E-LBHN16D-P`, `E-LBHNW20L`; `dr` (one or two digits) is checked against the tables in `generator.rhai` (series by suffix: none single / double, `D` medium / medium long, `L` long).

Every Python refusal, in its order and with its message, is a `refuse(kind, message)` in `generator.rhai`. `fields(configuration, parameters)` is the
inverse (code printing for a bill of materials): for every valid code parse(print(parse(code))) gives the same configuration and parameters
(13/13 codes). The part description (`properties.description`, written to the component metadata) is written in Rhai too, with Python's `{:g}` and
`{:+.3f}` formatting: 13/13 of the descriptions are identical to the Python ones.

Not the same, by design of field templates: separators and case are skipped when a code is read, so `E-LBH...` typed with a stray space inside
(`E-LBHN 16`) parses where the Python regular expression refuses it. A required separator (`\-`) is not skipped. `codes.txt` has no such code.

## What was run

For every line of `../codes.txt` (13 valid codes, 8 `!` rejects) plus 17 extra refusals: code -> template -> Rhai `resolve` -> a row for the
code (`config.row from=<configuration row>`, the free parameter set) in a working copy of the model -> a design inserts that copy with
`component.insert_design {configuration}` -> `inspect.measure` (volume, area, bbox, faces) + `model.threads` + the unchanged `../src/check.py` spec check (run on the
inserted part, with the `Housing` it needs rebuilt from the Rhai result and the package tables, never from the Python parser) -> the same code built by the Python
generator and measured the same way. The thread lists (`model.threads` start / end) are identical for all 13 codes.

```
# CI does exactly this (SC_CLI = solidcraft-cli 0.50.0, RHAI_RUN = runtime/rhai-run built with cargo):
bash vendors/misumi/lhb/bushing-housing/parametric/ci.sh OUT        # build.py, run_codes.py, faithfulness.py
tools/parametric-verdict OUT/faithfulness.json              # exit 1 when anything differs
python3 vendors/misumi/lhb/bushing-housing/parametric/run_codes.py --rhai-only --out OUT   # no SolidCraft: only the refusals and the descriptions
```

## Result: side by side

Volume mm3 / area mm2 / bbox mm / faces; the spec check columns are passed rows / rows. Equal = same bodies, volume and area within 1e-6 relative, same bbox
and face count (decided by `tools/parametric-verdict`, not by the harness).

| code | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec check python | spec check parametric | equal |
|---|---|---|---|---|---|
| E-LBHN6 | 10927.9 / 4281.6 / 30x25x18 / 25 | 10927.9 / 4281.6 / 30x25x18 / 25 | 17/17 | 17/17 | yes |
| E-LBHN16 | 67046.8 / 14453.2 / 50x44x38.5 / 25 | 67046.8 / 14453.2 / 50x44x38.5 / 25 | 17/17 | 17/17 | yes |
| E-LBHN16D-P | 96730.9 / 18710.2 / 50x63x38.5 / 29 | 96730.9 / 18710.2 / 50x63x38.5 / 29 | 18/18 | 18/18 | yes |
| E-LBHN20D | 123632.2 / 23429.6 / 54x73x41 / 25 | 123632.2 / 23429.6 / 54x73x41 / 25 | 17/17 | 17/17 | yes |
| E-LBHN13 | 39694.9 / 10348.6 / 44x39x30 / 25 | 39694.9 / 10348.6 / 44x39x30 / 25 | 17/17 | 17/17 | yes |
| E-LBHN30-P | 249364.5 / 37003.3 / 78x72x59.5 / 29 | 249364.5 / 37003.3 / 78x72x59.5 / 29 | 18/18 | 18/18 | yes |
| E-LBHN50 | 1017908.8 / 90611.6 / 122x110x102 / 25 | 1017908.8 / 90611.6 / 122x110x102 / 25 | 17/17 | 17/17 | yes |
| E-LBHNW8 | 35175.8 / 9513.6 / 34x58x22 / 25 | 35175.8 / 9513.6 / 34x58x22 / 25 | 17/17 | 17/17 | yes |
| E-LBHNW12L | 89712.5 / 20001.2 / 42x96x28 / 31 | 89712.5 / 20001.2 / 42x96x28 / 31 | 17/17 | 17/17 | yes |
| E-LBHNW16D | 154907.3 / 26629.9 / 50x100x38.5 / 25 | 154907.3 / 26629.9 / 50x100x38.5 / 25 | 17/17 | 17/17 | yes |
| E-LBHNW20L-P | 227776.2 / 39515.6 / 54x134x41 / 35 | 227776.2 / 39515.6 / 54x134x41 / 35 | 18/18 | 18/18 | yes |
| E-LBHNW30D | 600164.0 / 71349.9 / 78x170x59.5 / 25 | 600164.0 / 71349.9 / 78x170x59.5 / 25 | 17/17 | 17/17 | yes |
| E-LBHNW50-P | 2008287.1 / 150963.2 / 122x215x102 / 29 | 2008287.1 / 150963.2 / 122x215x102 / 29 | 18/18 | 18/18 | yes |

| rejected code | python message | parametric message | same |
|---|---|---|---|
| E-LBHN6-P | E-LBHN6: dr 6 has no dowel hole version, the dowel hole table starts at dr 8 (p.485 / p.487) | E-LBHN6: dr 6 has no dowel hole version, the dowel hole table starts at dr 8 (p.485 / p.487) | yes |
| E-LBHN13D | E-LBHN13D: the medium housing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] only; dr 13, 35, 40 and 50 are single only (p.485) | E-LBHN13D: the medium housing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] only; dr 13, 35, 40 and 50 are single only (p.485) | yes |
| E-LBHN16L | E-LBHN has Single (no suffix) and Medium (D) only; the Long length L belongs to E-LBHNW (p.485) | E-LBHN has Single (no suffix) and Medium (D) only; the Long length L belongs to E-LBHNW (p.485) | yes |
| E-LBHN9 | E-LBHN9: the wide single housing is offered for dr [6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.485) | E-LBHN9: the wide single housing is offered for dr [6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.485) | yes |
| E-LBHNW10D | E-LBHNW10D: the medium long housing is offered for dr [16, 20, 25, 30] (p.487) | E-LBHNW10D: the medium long housing is offered for dr [16, 20, 25, 30] (p.487) | yes |
| E-LBHNW6 | E-LBHNW6: the wide double housing is offered for dr [8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.487) | E-LBHNW6: the wide double housing is offered for dr [8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.487) | yes |
| E-LBHNW35L | E-LBHNW35L: the long housing is offered for dr [12, 16, 20, 25, 30] (p.487) | E-LBHNW35L: the long housing is offered for dr [12, 16, 20, 25, 30] (p.487) | yes |
| E-LBHN16-X | 'E-LBHN16-X': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | 'E-LBHN16-X': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | yes |
| E-LBHN | 'E-LBHN': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | 'E-LBHN': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | yes |
| E-LBHNW-P | 'E-LBHNW-P': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | 'E-LBHNW-P': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | yes |
| E-LBHN16X | 'E-LBHN16X': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | 'E-LBHN16X': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | yes |
| E-LBHN16-X | 'E-LBHN16-X': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | 'E-LBHN16-X': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | yes |
| E-LBHN16DP | 'E-LBHN16DP': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | 'E-LBHN16DP': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | yes |
| E-LBHN160 | 'E-LBHN160': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | 'E-LBHN160': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | yes |
| E-LBHN6D-P | E-LBHN6: dr 6 has no dowel hole version, the dowel hole table starts at dr 8 (p.485 / p.487) | E-LBHN6: dr 6 has no dowel hole version, the dowel hole table starts at dr 8 (p.485 / p.487) | yes |
| E-LBHN35D | E-LBHN35D: the medium housing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] only; dr 13, 35, 40 and 50 are single only (p.485) | E-LBHN35D: the medium housing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] only; dr 13, 35, 40 and 50 are single only (p.485) | yes |
| E-LBHNW6-P | E-LBHNW6: the wide double housing is offered for dr [8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.487) | E-LBHNW6: the wide double housing is offered for dr [8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.487) | yes |
| E-LBHNW13D | E-LBHNW13D: the medium long housing is offered for dr [16, 20, 25, 30] (p.487) | E-LBHNW13D: the medium long housing is offered for dr [16, 20, 25, 30] (p.487) | yes |
| E-LBHNW10L | E-LBHNW10L: the long housing is offered for dr [12, 16, 20, 25, 30] (p.487) | E-LBHNW10L: the long housing is offered for dr [12, 16, 20, 25, 30] (p.487) | yes |
| E-LBHNW35L | E-LBHNW35L: the long housing is offered for dr [12, 16, 20, 25, 30] (p.487) | E-LBHNW35L: the long housing is offered for dr [12, 16, 20, 25, 30] (p.487) | yes |
| E-LBHN8L | E-LBHN has Single (no suffix) and Medium (D) only; the Long length L belongs to E-LBHNW (p.485) | E-LBHN has Single (no suffix) and Medium (D) only; the Long length L belongs to E-LBHNW (p.485) | yes |
| E-LBHN9-P | E-LBHN9: the wide single housing is offered for dr [6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.485) | E-LBHN9: the wide single housing is offered for dr [6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.485) | yes |
| E-LBHP20LUU | 'E-LBHP20LUU': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | 'E-LBHP20LUU': expected <type><dr>[<length>][-P] with type E-LBHN (single, length none or D) or E-LBHNW (double, length none, D or L), -P for dowel holes, e.g. E-LBHN16, E-LBHN16D-P, E-LBHNW20L | yes |
| E-LBHNW50D | E-LBHNW50D: the medium long housing is offered for dr [16, 20, 25, 30] (p.487) | E-LBHNW50D: the medium long housing is offered for dr [16, 20, 25, 30] (p.487) | yes |
| E-LBHN40D-P | E-LBHN40D: the medium housing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] only; dr 13, 35, 40 and 50 are single only (p.485) | E-LBHN40D: the medium housing is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] only; dr 13, 35, 40 and 50 are single only (p.485) | yes |

| change | to | changed-in-place vol / area / bbox / faces | direct code (inserted) | python | equal |
|---|---|---|---|---|---|
| E-LBHN16: dowel | 1 | 66921.1 / 14578.8 / 50x44x38.5 / 29 | 66921.1 / 14578.8 / 50x44x38.5 / 29 (E-LBHN16-P) | 66921.1 / 14578.8 / 50x44x38.5 / 29 | yes |
| E-LBHNW20L-P: dowel | 0 | 227972.5 / 39358.5 / 54x134x41 / 31 | 227972.5 / 39358.5 / 54x134x41 / 31 (E-LBHNW20L) | 227972.5 / 39358.5 / 54x134x41 / 31 | yes |
| E-LBHN30D: dowel | 1 | 349525.6 / 46870.5 / 78x100x59.5 / 29 | 349525.6 / 46870.5 / 78x100x59.5 / 29 (E-LBHN30D-P) | 349525.6 / 46870.5 / 78x100x59.5 / 29 | yes |
| E-LBHNW50-P: dowel | 0 | 2008683.0 / 150699.3 / 122x215x102 / 25 | 2008683.0 / 150699.3 / 122x215x102 / 25 (E-LBHNW50) | 2008683.0 / 150699.3 / 122x215x102 / 25 | yes |

## It stays parametric

The one free parameter is `dowel`. Row for the code, activate it, then `parameters.change dowel` (1 adds the two dowel holes through the `drive_suppression` rules, 0 removes them) on the
configured design; compared with the direct code inserted the same way and with the Python part: identical in all four cases (the rebuild table).

## SolidCraft 0.50.0 observations (exact errors) and workarounds

1. **A free parameter value on an inserted part needs #23175 (our draft, being finished).** `component.insert_design {path, configuration, parameters: {dowel: "1"}}` is accepted and the key
   ignored: the second part comes in with the same bounding box as the first, no error (`bbox max of both parts [[25.0, 22.000000000000004, 38.5], [25.0, 22.000000000000004, 38.5]]`).
   `component.set_link_parameters` -> `unknown command `component.set_link_parameters``; `generator.parse` -> `unknown command `generator.parse``;
   `generator.insert` -> `unknown command `generator.insert``. `parameters.change dowel 1` in the host design returns without error and leaves the inserted
   part unchanged (`bbox max [[25.0, 22.000000000000004, 38.5]]`). Workaround (labelled): a row for the code in a working copy of the model (`config.row {from: <configuration row>, values: {param:dowel: ...}}`),
   inserted with `configuration`; to change `dowel`, change it in the working copy (the rebuild table above) and insert again.
2. **Limits on ordinary edits.** `parameters.change dowel 2` is accepted (the range rule 0..1 only acts on rows: `config.row ... values {param:dowel: "1"}` on dr 6 -> `rule No dowel hole version for this dr (S12 p.485 / p.487: the dowel hole table starts at dr 8) restricts the final value`); resolve refuses it with the Python message first.
3. **The thread designation cannot come from a parameter.** One `solid.hole` feature per thread size and per site (end rows, middle row): 10 features of which 2 are live per Long row and 1 per other row. `solid.hole {thread: "M5"}` is a literal.
4. **Rules addressed by feature name need #23175 (our draft, being finished).** In 0.50.0, rules name features by integer id (`config.rule` schema: `feature` is an integer), so the model is built in two passes (the ids come from the replies of the
   first); a name would keep the rules readable. A rule target must be a configuration column: the dowel parameter and its features are columns.
5. **The seeded row.** `config.configure` seeds a row named `Default` from the first parameter values; `build.py` deletes it with `config.row {name: "Default", delete: true}`
   after the catalogue rows exist, so the table holds exactly the catalogue rows (40: single 12, medium 8, double 11, medium long 4, long 5).


## What does not fit the interface document, and proposals

| Where | What the housing needs | Proposal |
|---|---|---|
| 3 field templates | a refusal message that quotes the code as typed (`'E-LBHN16-X': expected ...`) for a code that matches no template | optional `fn no_match(raw)` in `generator.rhai`; used here: a second template `{raw: text 1..128 [ -~]}` that matches anything |
| 3 field templates | text fields come back upper-case in the stand-in, so a refusal shows the code upper-cased | text fields keep the case typed |
| 2 `[parameters]` | a flag such as `dowel` (0 or 1) as a value, and a bare `[\-P:dowel]` flag naming a user parameter | `type = "flag"` mapping to a unitless 0 / 1 user parameter |
| 4 `resolve` return | description, material and part number per code | `properties: #{...}` (done here, as in the HFS proof) written to the component's properties by `generator.insert` |
| 4 free parameter on a link | see observation 1 | `parameters` on `component.insert_design`, checked against the source's range and allowed-value rules |
| model | the thread designation as a value | `solid.hole {thread: <choice parameter>}` (the configuration row would then carry M4 / M5 / ...) |
| rules | name a feature by name | `feature` by name in `config.rule`, so the model needs no second build stage |

What fits the housing without change: per-series topology as suppression columns of the configuration rows (one activation switches the thread sizes, the
third mounting row, the dowel sites), the dowel option as a `drive_suppression` pair on a unitless parameter, limits as `parameter_range` / allowed values, per-row
source and page in `generator.toml`, `generator.rhai` with `table()` / `refuse()` / `code_template()`.

The optional link proof is declared in `link_checks.json` and run by `ci.sh` through `runtime.parametric.links`. It adds insertion, link-edit, and out-of-range refusal rows only when the command catalogue lists `component.set_link_parameters`. Release builds retain their existing rows and link dependency item.
