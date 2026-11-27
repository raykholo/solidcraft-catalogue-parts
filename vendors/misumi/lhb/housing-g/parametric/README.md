# misumi.lhb.housing-g as a parametric SolidCraft generator

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai, and rules addressed by feature name needs #23175 (our draft, being finished). The exact command errors quoted below are observations from SolidCraft 0.50.0. The draft checks ranges on link overrides; ordinary source `parameters.change` still does not enforce range restrictions.

The housing modelled ONCE in SolidCraft (`housing-g/housing-g.sc`), a configuration table of the catalogue rows, the ordering code as a field template and
the logic as plain Rhai, following SolidCraft's generator interface (`docs/formats/generator.md`, version 2, issue 22331). The Python generator in `../src`
is untouched and is the reference every code below is compared with. CI (`.github/workflows/parametric.yml`) builds the model and runs everything below on
SolidCraft 0.50.0 for every change: `ci.sh OUTDIR` writes `OUTDIR/faithfulness.json` and `tools/parametric-verdict` decides.

```
housing-g/                  the package layout of the interface document
  generator.toml               [parameters], two [[template]] entries, [rows."<configuration row>"] source / page / status per row
  housing-g.sc                    the parametric model + its configuration table + its rules (built by build.py; CI rebuilds it on every run)
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

- **One model, parameters.** 11 user parameters from the catalogue row (`dr fw fs bw c1 l1 hd tl t1 hoff drk`), the free one `hc` (the centre height H, the
  ordering option, 15 to 50 mm) and the derived `h1 = hc + hoff` (the total height H1). The profile is ONE closed sketch of ten points, every coordinate an
  expression (`"bw / 2 - c1"`, `"h1 - c1"`), extruded over `tl` from a sketch plane whose origin is the expression `tl / 2` (so the body is centred on y = 0
  like the Python one). The shaft bore is a cylinder cut at `hc` above the base, the four mounting holes are cylinder cuts at `+-l1 / 2`, `+-t1 / 2`.
- **Configuration table = the catalogue rows.** 10 rows, `G-<dr>` (single) and `GW-<dr>` (double) for dr 12 / 16 / 20 / 25 / 30 (`data/housing-g.csv`, source
  and page per row in `generator.toml [rows."..."]`). The row cells are the parameter values (`tl`, `t1` differ between single and double); the free `hc`
  is a column too, its cell holds the first offered height. 12 columns (all parameters), 6 rules, no suppression column: nothing in this housing is optional.
- **`hc` and its limits are rules.** `parameter_range hc 15..50 mm` (always) and one `allow_parameter_values` rule per dr (condition `drk = <dr>`): dr 12 {15, 20, 25},
  16 {20, 25, 30}, 20 {20, 25, 30}, 25 {25, 30, 40}, 30 {30, 40, 50}. `config.row ... values {param:hc: "15 mm"}` on dr 30 is refused with the rule's name (below).

## The ordering code

`generator.toml`, first template (the second one, `{raw: text 1..128 [ -~]}`, takes any other text so that `generator.rhai` can refuse it with the
Python shape message, `'<code>': expected ...`):

```
E\-LBHG[W:double]{dr: text 1..2 [0-9]}\-{h: text 1..2 [0-9]}
```

`E-LBHG[W]<dr>-<H>`: `E-LBHG12-15`, `E-LBHGW30-40`; the text fields `dr` and `h` (one or two digits) are checked against the table in `generator.rhai` so the refusals carry the Python wording (dr offered, H offered for this dr).

Every Python refusal, in its order and with its message, is a `refuse(kind, message)` in `generator.rhai`. `fields(configuration, parameters)` is the
inverse (code printing for a bill of materials): for every valid code parse(print(parse(code))) gives the same configuration and parameters
(10/10 codes). The part description (`properties.description`, written to the component metadata) is written in Rhai too, with Python's `{:g}` and
`{:+.3f}` formatting: 10/10 of the descriptions are identical to the Python ones.

Not the same, by design of field templates: separators and case are skipped when a code is read, so `E-LBH...` typed with a stray space inside
(`E-LBHG 12-15`) parses where the Python regular expression refuses it. A required separator (`\-`) is not skipped. `codes.txt` has no such code.

## What was run

For every line of `../codes.txt` (10 valid codes, 6 `!` rejects) plus 10 extra refusals: code -> template -> Rhai `resolve` -> a row for the
code (`config.row from=<configuration row>`, the free parameter set) in a working copy of the model -> a design inserts that copy with
`component.insert_design {configuration}` -> `inspect.measure` (volume, area, bbox, faces) + `model.threads` + the unchanged `../src/check.py` spec check (run on the
inserted part, with the `Housing` it needs rebuilt from the Rhai result and the package tables, never from the Python parser) -> the same code built by the Python
generator and measured the same way. The thread lists (`model.threads` start / end) are identical for all 10 codes.

```
# CI does exactly this (SC_CLI = solidcraft-cli 0.50.0, RHAI_RUN = runtime/rhai-run built with cargo):
bash vendors/misumi/lhb/housing-g/parametric/ci.sh OUT        # build.py, run_codes.py, faithfulness.py
tools/parametric-verdict OUT/faithfulness.json              # exit 1 when anything differs
python3 vendors/misumi/lhb/housing-g/parametric/run_codes.py --rhai-only --out OUT   # no SolidCraft: only the refusals and the descriptions
```

## Result: side by side

Volume mm3 / area mm2 / bbox mm / faces; the spec check columns are passed rows / rows. Equal = same bodies, volume and area within 1e-6 relative, same bbox
and face count (decided by `tools/parametric-verdict`, not by the harness).

| code | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec check python | spec check parametric | equal |
|---|---|---|---|---|---|
| E-LBHG12-15 | 36785.8 / 10389.8 / 58x40x30 / 17 | 36785.8 / 10389.8 / 58x40x30 / 17 | 12/12 | 12/12 | yes |
| E-LBHG12-25 | 48785.8 / 11789.8 / 58x40x40 / 17 | 48785.8 / 11789.8 / 58x40x40 / 17 | 12/12 | 12/12 | yes |
| E-LBHG16-20 | 71744.0 / 15475.7 / 68x47x40 / 17 | 71744.0 / 15475.7 / 68x47x40 / 17 | 12/12 | 12/12 | yes |
| E-LBHG20-30 | 110846.3 / 20348.2 / 72x52x52 / 17 | 110846.3 / 20348.2 / 72x52x52 / 17 | 12/12 | 12/12 | yes |
| E-LBHG25-40 | 238800.5 / 33812.5 / 90x69x67.5 / 17 | 238800.5 / 33812.5 / 90x69x67.5 / 17 | 12/12 | 12/12 | yes |
| E-LBHG30-50 | 374652.1 / 45180.1 / 105x74x82.5 / 17 | 374652.1 / 45180.1 / 105x74x82.5 / 17 | 12/12 | 12/12 | yes |
| E-LBHGW12-20 | 75445.4 / 17502.0 / 58x70x35 / 17 | 75445.4 / 17502.0 / 58x70x35 / 17 | 12/12 | 12/12 | yes |
| E-LBHGW20-25 | 180617.1 / 31408.1 / 72x94x47 / 17 | 180617.1 / 31408.1 / 72x94x47 / 17 | 12/12 | 12/12 | yes |
| E-LBHGW25-30 | 374347.4 / 52265.3 / 90x128x57.5 / 17 | 374347.4 / 52265.3 / 90x128x57.5 / 17 | 12/12 | 12/12 | yes |
| E-LBHGW30-40 | 613377.2 / 69802.3 / 105x138x72.5 / 17 | 613377.2 / 69802.3 / 105x138x72.5 / 17 | 12/12 | 12/12 | yes |

| rejected code | python message | parametric message | same |
|---|---|---|---|
| E-LBHG12-30 | E-LBHG12-30: centre height H 30 is not offered for dr 12; the choices are [15, 20, 25] (p.491) | E-LBHG12-30: centre height H 30 is not offered for dr 12; the choices are [15, 20, 25] (p.491) | yes |
| E-LBHG30-25 | E-LBHG30-25: centre height H 25 is not offered for dr 30; the choices are [30, 40, 50] (p.491) | E-LBHG30-25: centre height H 25 is not offered for dr 30; the choices are [30, 40, 50] (p.491) | yes |
| E-LBHG12 | 'E-LBHG12': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | 'E-LBHG12': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | yes |
| E-LBHGW16-15 | E-LBHGW16-15: centre height H 15 is not offered for dr 16; the choices are [20, 25, 30] (p.491) | E-LBHGW16-15: centre height H 15 is not offered for dr 16; the choices are [20, 25, 30] (p.491) | yes |
| E-LBHG10-15 | E-LBHG10-15: dr 10 is not a catalogue size; E-LBHG / E-LBHGW are offered for dr [12, 16, 20, 25, 30] (p.491) | E-LBHG10-15: dr 10 is not a catalogue size; E-LBHG / E-LBHGW are offered for dr [12, 16, 20, 25, 30] (p.491) | yes |
| E-LBHG12-15-P | 'E-LBHG12-15-P': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | 'E-LBHG12-15-P': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | yes |
| E-LBHG12- | 'E-LBHG12-': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | 'E-LBHG12-': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | yes |
| E-LBHG1215 | 'E-LBHG1215': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | 'E-LBHG1215': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | yes |
| E-LBHGW-25 | 'E-LBHGW-25': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | 'E-LBHGW-25': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | yes |
| E-LBHGW12-15-P | 'E-LBHGW12-15-P': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | 'E-LBHGW12-15-P': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | yes |
| E-LBHG12X | 'E-LBHG12X': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | 'E-LBHG12X': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | yes |
| E-LBHG16-35 | E-LBHG16-35: centre height H 35 is not offered for dr 16; the choices are [20, 25, 30] (p.491) | E-LBHG16-35: centre height H 35 is not offered for dr 16; the choices are [20, 25, 30] (p.491) | yes |
| E-LBHGW25-50 | E-LBHGW25-50: centre height H 50 is not offered for dr 25; the choices are [25, 30, 40] (p.491) | E-LBHGW25-50: centre height H 50 is not offered for dr 25; the choices are [25, 30, 40] (p.491) | yes |
| E-LBHG013-15 | 'E-LBHG013-15': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | 'E-LBHG013-15': expected E-LBHG<dr>-<H> (single) or E-LBHGW<dr>-<H> (double), H the centre height, e.g. E-LBHG12-15, E-LBHGW30-40 | yes |
| E-LBHGW20-0 | E-LBHGW20-0: centre height H 0 is not offered for dr 20; the choices are [20, 25, 30] (p.491) | E-LBHGW20-0: centre height H 0 is not offered for dr 20; the choices are [20, 25, 30] (p.491) | yes |
| E-LBHG99-99 | E-LBHG99-99: dr 99 is not a catalogue size; E-LBHG / E-LBHGW are offered for dr [12, 16, 20, 25, 30] (p.491) | E-LBHG99-99: dr 99 is not a catalogue size; E-LBHG / E-LBHGW are offered for dr [12, 16, 20, 25, 30] (p.491) | yes |

| change | to | changed-in-place vol / area / bbox / faces | direct code (inserted) | python | equal |
|---|---|---|---|---|---|
| E-LBHG12-15: hc | 25 mm | 48785.8 / 11789.8 / 58x40x40 / 17 | 48785.8 / 11789.8 / 58x40x40 / 17 (E-LBHG12-25) | 48785.8 / 11789.8 / 58x40x40 / 17 | yes |
| E-LBHGW25-25: hc | 40 mm | 444747.4 / 55925.3 / 90x128x67.5 / 17 | 444747.4 / 55925.3 / 90x128x67.5 / 17 (E-LBHGW25-40) | 444747.4 / 55925.3 / 90x128x67.5 / 17 | yes |
| E-LBHG30-30: hc | 50 mm | 374652.1 / 45180.1 / 105x74x82.5 / 17 | 374652.1 / 45180.1 / 105x74x82.5 / 17 (E-LBHG30-50) | 374652.1 / 45180.1 / 105x74x82.5 / 17 | yes |

## It stays parametric

Row for the code, activate it, then `parameters.change hc` on the configured design; compared with the direct code inserted the same way and with the Python
part: identical in all three cases (the rebuild table), including the bore, which follows `hc`, and the total height H1 = hc + offset.

## SolidCraft 0.50.0 observations (exact errors) and workarounds

1. **A free parameter value on an inserted part needs #23175 (our draft, being finished).** `component.insert_design {path, configuration, parameters: {hc: "25 mm"}}` is accepted and the key
   ignored: the second part comes in with the same bounding box as the first, no error (`bbox max of both parts [[29.0, 20.0, 30.0], [29.0, 20.0, 30.0]]`).
   `component.set_link_parameters` -> `unknown command `component.set_link_parameters``; `generator.parse` -> `unknown command `generator.parse``;
   `generator.insert` -> `unknown command `generator.insert``. `parameters.change hc 25 mm` in the host design returns without error and leaves the inserted
   part unchanged (`bbox max [[29.0, 20.0, 30.0]]`). Workaround (labelled): a row for the code in a working copy of the model (`config.row {from: <configuration row>, values: {param:hc: ...}}`),
   inserted with `configuration`; to change `hc`, change it in the working copy (the rebuild table above) and insert again.
2. **Limits on ordinary edits.** `parameters.change hc 60 mm` is accepted (the range rule 15..50 only acts on rows: `config.row ... values {param:hc: "15 mm"}` on dr 30 ->
   `rule Centre heights offered for dr 30 (S14 p.491 table) restricts the final value`); an `allow_parameter_values` rule restricts a row, not an ordinary edit.
   The catalogue's own refusals (a height not offered for the dr) are `resolve`'s, with the Python message.
3. **The thread designation cannot come from a parameter.** Not needed here: this housing has no threaded hole (the four mounting holes are plain through holes in the flange).
4. **Rules addressed by feature name need #23175 (our draft, being finished).** In 0.50.0, rules name features by integer id (`config.rule` schema: `feature` is an integer), so the model is built in two passes (the ids come from the replies of the
   first); a name would keep the rules readable. A rule target must be a configuration column: `hc` and `drk` are columns.
5. **The seeded row.** `config.configure` seeds a row named `Default` from the first parameter values; `build.py` deletes it with `config.row {name: "Default", delete: true}`
   after the catalogue rows exist, so the table holds exactly the catalogue rows (10: G-12 ... GW-30).


## What does not fit the interface document, and proposals

| Where | What the housing needs | Proposal |
|---|---|---|
| 3 field templates | a refusal message that quotes the code as typed (`'E-LBHN16-X': expected ...`) for a code that matches no template | optional `fn no_match(raw)` in `generator.rhai`; used here: a second template `{raw: text 1..128 [ -~]}` that matches anything |
| 3 field templates | text fields come back upper-case in the stand-in, so a refusal shows the code upper-cased | text fields keep the case typed |
| 2 `[parameters]` | a flag such as `dowel` (0 or 1) as a value, and a bare `[\-P:dowel]` flag naming a user parameter | `type = "flag"` mapping to a unitless 0 / 1 user parameter |
| 4 `resolve` return | description, material and part number per code | `properties: #{...}` (done here, as in the HFS proof) written to the component's properties by `generator.insert` |
| 4 free parameter on a link | see observation 1 | `parameters` on `component.insert_design`, checked against the source's range and allowed-value rules |
| rules | name a feature by name | `feature` by name in `config.rule`, so the model needs no second build stage |

What fits the housing without change: per-series topology as suppression columns of the configuration rows (one activation switches the thread sizes, the
third mounting row, the dowel sites), the dowel option as a `drive_suppression` pair on a unitless parameter, limits as `parameter_range` / allowed values, per-row
source and page in `generator.toml`, `generator.rhai` with `table()` / `refuse()` / `code_template()`.

The optional link proof is declared in `link_checks.json` and run by `ci.sh` through `runtime.parametric.links`. It adds insertion, link-edit, and out-of-range refusal rows only when the command catalogue lists `component.set_link_parameters`. Release builds retain their existing rows and link dependency item.
