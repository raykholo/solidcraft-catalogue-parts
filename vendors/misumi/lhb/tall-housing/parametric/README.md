# misumi.lhb.tall-housing as a parametric SolidCraft generator

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai, and rules addressed by feature name needs #23175 (our draft, being finished). The exact command errors quoted below are observations from SolidCraft 0.50.0. The draft checks ranges on link overrides; ordinary source `parameters.change` still does not enforce range restrictions.

The housing modelled ONCE in SolidCraft (`tall-housing/tall-housing.sc`), a configuration table of the catalogue rows, the ordering code as a field template and
the logic as plain Rhai, following SolidCraft's generator interface (`docs/formats/generator.md`, version 2, issue 22331). The Python generator in `../src`
is untouched and is the reference every code below is compared with. CI (`.github/workflows/parametric.yml`) builds the model and runs everything below on
SolidCraft 0.50.0 for every change: `ci.sh OUTDIR` writes `OUTDIR/faithfulness.json` and `tools/parametric-verdict` decides.

```
tall-housing/                  the package layout of the interface document
  generator.toml               [parameters], two [[template]] entries, [rows."<configuration row>"] source / page / status per row
  tall-housing.sc                    the parametric model + its configuration table + its rules (built by build.py; CI rebuilds it on every run)
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

- **One model, parameters.** 18 user parameters per catalogue row (`dr bl l1 l2 hb bw bh tl m1d m2d cbd cbt dp dl dwx dwy dowel dowel_ok`: bore, length, M1 and M2 hole spacings, block, effective
  thread lengths, counterbore, dowel sizes), plus the appearance constant `m1_xf` (0.35, the x of the vertical M1 holes as a fraction of W, the Python generator's reading of the figure).
  The block is a rectangle sketch extruded over `bl`; the shaft bore is a cylinder cut at `hb` above the base.
- **Configuration table = the catalogue rows.** 41 rows named `<series>-<dr>` (single 10, double 10, medium 8, medium long 5, long 8; `data/blocks.csv` joined with `data/dowel.csv` by series and dr, source and
  page per row in `generator.toml`). 36 columns: the 18 parameters and 18 suppression columns.
- **Thread sizes and the third M2 hole = suppression columns.** Two vertical M1 holes in the top face (one `solid.hole` feature per size, `Thread M1 M4 ... M10`), two horizontal M2 holes from the +X face
  (`Thread M2 M<k>`), and for the Long type the middle M2 hole and its counterbore (`Thread M2 mid M<k>`, `Counterbore 3`) live on the Long rows only. The row sets which size is live. The counterbores `d1 x t`
  are cylinder cuts coaxial with the M2 holes.
- **The dowel option (-P) = a parameter + `drive_suppression` rules.** `dowel` (0 or 1) switches the two dowel cylinders; their position is two row parameters: the diagonal pair `(-F / 2, -E / 2), (F / 2, E / 2)` for the single
  type (`dwx = F / 2, dwy = E / 2`), the centre line `(0, +-E / 2)` for the others, from the dowel tables. `dowel_ok = 0` on the rows with no dowel data (medium, medium long, single and double dr 5 / 6, long dr 8 to 13) and an
  `allow_parameter_values` rule then allows only 0.

## The ordering code

`generator.toml`, first template (the second one, `{raw: text 1..128 [ -~]}`, takes any other text so that `generator.rhai` can refuse it with the
Python shape message, `'<code>': expected ...`):

```
E\-LBHS[W:double]{dr: text 1..2 [0-9]}[{length: D|S|L}][\-P:dowel]
```

`E-LBHS[W]<dr>[D|S|L][-P]`: `E-LBHS16L-P`, `E-LBHSW20-P`; `dr` (one or two digits) is checked against the tables in `generator.rhai` (series by suffix: none single, `D` medium, `S` medium long, `L` long, `E-LBHSW` double with no suffix).

Every Python refusal, in its order and with its message, is a `refuse(kind, message)` in `generator.rhai`. `fields(configuration, parameters)` is the
inverse (code printing for a bill of materials): for every valid code parse(print(parse(code))) gives the same configuration and parameters
(16/16 codes). The part description (`properties.description`, written to the component metadata) is written in Rhai too, with Python's `{:g}` and
`{:+.3f}` formatting: 16/16 of the descriptions are identical to the Python ones.

Not the same, by design of field templates: separators and case are skipped when a code is read, so `E-LBH...` typed with a stray space inside
(`E-LBHS 16`) parses where the Python regular expression refuses it. A required separator (`\-`) is not skipped. `codes.txt` has no such code.

## What was run

For every line of `../codes.txt` (16 valid codes, 10 `!` rejects) plus 18 extra refusals: code -> template -> Rhai `resolve` -> a row for the
code (`config.row from=<configuration row>`, the free parameter set) in a working copy of the model -> a design inserts that copy with
`component.insert_design {configuration}` -> `inspect.measure` (volume, area, bbox, faces) + `model.threads` + the unchanged `../src/check.py` spec check (run on the
inserted part, with the `Housing` it needs rebuilt from the Rhai result and the package tables, never from the Python parser) -> the same code built by the Python
generator and measured the same way. The thread lists (`model.threads` start / end) are identical for all 16 codes.

```
# CI does exactly this (SC_CLI = solidcraft-cli 0.50.0, RHAI_RUN = runtime/rhai-run built with cargo):
bash vendors/misumi/lhb/tall-housing/parametric/ci.sh OUT        # build.py, run_codes.py, faithfulness.py
tools/parametric-verdict OUT/faithfulness.json              # exit 1 when anything differs
python3 vendors/misumi/lhb/tall-housing/parametric/run_codes.py --rhai-only --out OUT   # no SolidCraft: only the refusals and the descriptions
```

## Result: side by side

Volume mm3 / area mm2 / bbox mm / faces; the spec check columns are passed rows / rows. Equal = same bodies, volume and area within 1e-6 relative, same bbox
and face count (decided by `tools/parametric-verdict`, not by the harness).

| code | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec check python | spec check parametric | equal |
|---|---|---|---|---|---|
| E-LBHS5 | 6460.8 / 3134.5 / 15x25x20 / 17 | 6460.8 / 3134.5 / 15x25x20 / 17 | 17/17 | 17/17 | yes |
| E-LBHS10 | 27857.1 / 8301.0 / 26x39x32 / 17 | 27857.1 / 8301.0 / 26x39x32 / 17 | 17/17 | 17/17 | yes |
| E-LBHS16-P | 70792.4 / 15240.8 / 36x47x49 / 21 | 70792.4 / 15240.8 / 36x47x49 / 21 | 21/21 | 21/21 | yes |
| E-LBHS30-P | 241677.6 / 37211.2 / 58x74x71 / 21 | 241677.6 / 37211.2 / 58x74x71 / 21 | 21/21 | 21/21 | yes |
| E-LBHS6D | 11400.5 / 4622.8 / 16x37x22 / 17 | 11400.5 / 4622.8 / 16x37x22 / 17 | 17/17 | 17/17 | yes |
| E-LBHS12D | 46231.8 / 12011.0 / 28x57x34 / 17 | 46231.8 / 12011.0 / 28x57x34 / 17 | 17/17 | 17/17 | yes |
| E-LBHS12S | 69721.1 / 16538.5 / 28x85x34 / 17 | 69721.1 / 16538.5 / 28x85x34 / 17 | 17/17 | 17/17 | yes |
| E-LBHS20S | 219612.1 / 35714.6 / 42x115x54 / 17 | 219612.1 / 35714.6 / 42x115x54 / 17 | 17/17 | 17/17 | yes |
| E-LBHS13L | 119469.1 / 24087.9 / 30x106x43 / 20 | 119469.1 / 24087.9 / 30x106x43 / 20 | 17/17 | 17/17 | yes |
| E-LBHS8L | 36543.7 / 11171.7 / 20x80x26 / 20 | 36543.7 / 11171.7 / 20x80x26 / 20 | 17/17 | 17/17 | yes |
| E-LBHS16L-P | 185435.1 / 32154.6 / 36x121x49 / 24 | 185435.1 / 32154.6 / 36x121x49 / 24 | 20/20 | 20/20 | yes |
| E-LBHS30L-P | 674039.5 / 83923.8 / 58x202x71 / 24 | 674039.5 / 83923.8 / 58x202x71 / 24 | 20/20 | 20/20 | yes |
| E-LBHSW5 | 10666.1 / 4424.2 / 15x40x20 / 17 | 10666.1 / 4424.2 / 15x40x20 / 17 | 17/17 | 17/17 | yes |
| E-LBHSW10 | 49705.1 / 12595.5 / 26x68x32 / 17 | 49705.1 / 12595.5 / 26x68x32 / 17 | 17/17 | 17/17 | yes |
| E-LBHSW20-P | 178431.0 / 30393.3 / 42x94x54 / 21 | 178431.0 / 30393.3 / 42x94x54 / 21 | 20/20 | 20/20 | yes |
| E-LBHSW30-P | 460010.3 / 59704.0 / 58x138x71 / 21 | 460010.3 / 59704.0 / 58x138x71 / 21 | 20/20 | 20/20 | yes |

| rejected code | python message | parametric message | same |
|---|---|---|---|
| E-LBHS5-P | E-LBHS5-P: no dowel hole version for dr 5: the single housing has dowel holes for dr 8 and up (p.488) | E-LBHS5-P: no dowel hole version for dr 5: the single housing has dowel holes for dr 8 and up (p.488) | yes |
| E-LBHSW6-P | E-LBHSW6-P: no dowel hole version for dr 6: the double housing has dowel holes for dr 8 and up (p.489) | E-LBHSW6-P: no dowel hole version for dr 6: the double housing has dowel holes for dr 8 and up (p.489) | yes |
| E-LBHS14 | E-LBHS14: the tall single housing E-LBHS (p.488) is offered for dr [5, 6, 8, 10, 12, 13, 16, 20, 25, 30] only | E-LBHS14: the tall single housing E-LBHS (p.488) is offered for dr [5, 6, 8, 10, 12, 13, 16, 20, 25, 30] only | yes |
| E-LBHS6S | E-LBHS6S: the medium long housing E-LBHS..S (p.490) is offered for dr [12, 16, 20, 25, 30] only | E-LBHS6S: the medium long housing E-LBHS..S (p.490) is offered for dr [12, 16, 20, 25, 30] only | yes |
| E-LBHS13D | E-LBHS13D: the medium housing E-LBHS..D (p.490) is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] only | E-LBHS13D: the medium housing E-LBHS..D (p.490) is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] only | yes |
| E-LBHS12D-P | E-LBHS12D-P: dowel holes are available on the long type only (p.490), not on the medium housing | E-LBHS12D-P: dowel holes are available on the long type only (p.490), not on the medium housing | yes |
| E-LBHS12L-P | E-LBHS12L-P: no dowel hole version for dr 12: the long housing has dowel holes for dr 16 and up (p.490) | E-LBHS12L-P: no dowel hole version for dr 12: the long housing has dowel holes for dr 16 and up (p.490) | yes |
| E-LBHSW10L | 'E-LBHSW10L': the double housing E-LBHSW has no length suffix (p.489) | 'E-LBHSW10L': the double housing E-LBHSW has no length suffix (p.489) | yes |
| E-LBHS5L | E-LBHS5L: the long housing E-LBHS..L (p.490) is offered for dr [8, 10, 12, 13, 16, 20, 25, 30] only | E-LBHS5L: the long housing E-LBHS..L (p.490) is offered for dr [8, 10, 12, 13, 16, 20, 25, 30] only | yes |
| E-LBHS16X | 'E-LBHS16X': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | 'E-LBHS16X': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | yes |
| E-LBHS | 'E-LBHS': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | 'E-LBHS': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | yes |
| E-LBHSW-P | 'E-LBHSW-P': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | 'E-LBHSW-P': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | yes |
| E-LBHS16-X | 'E-LBHS16-X': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | 'E-LBHS16-X': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | yes |
| E-LBHS20UU | 'E-LBHS20UU': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | 'E-LBHS20UU': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | yes |
| E-LBHS16LP | 'E-LBHS16LP': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | 'E-LBHS16LP': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | yes |
| E-LBHS160 | 'E-LBHS160': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | 'E-LBHS160': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | yes |
| E-LBHSW6L | 'E-LBHSW6L': the double housing E-LBHSW has no length suffix (p.489) | 'E-LBHSW6L': the double housing E-LBHSW has no length suffix (p.489) | yes |
| E-LBHS5D | E-LBHS5D: the medium housing E-LBHS..D (p.490) is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] only | E-LBHS5D: the medium housing E-LBHS..D (p.490) is offered for dr [6, 8, 10, 12, 16, 20, 25, 30] only | yes |
| E-LBHS6S | E-LBHS6S: the medium long housing E-LBHS..S (p.490) is offered for dr [12, 16, 20, 25, 30] only | E-LBHS6S: the medium long housing E-LBHS..S (p.490) is offered for dr [12, 16, 20, 25, 30] only | yes |
| E-LBHS6L | E-LBHS6L: the long housing E-LBHS..L (p.490) is offered for dr [8, 10, 12, 13, 16, 20, 25, 30] only | E-LBHS6L: the long housing E-LBHS..L (p.490) is offered for dr [8, 10, 12, 13, 16, 20, 25, 30] only | yes |
| E-LBHSW14 | E-LBHSW14: the tall double housing E-LBHSW (p.489) is offered for dr [5, 6, 8, 10, 12, 13, 16, 20, 25, 30] only | E-LBHSW14: the tall double housing E-LBHSW (p.489) is offered for dr [5, 6, 8, 10, 12, 13, 16, 20, 25, 30] only | yes |
| E-LBHSW5-P | E-LBHSW5-P: no dowel hole version for dr 5: the double housing has dowel holes for dr 8 and up (p.489) | E-LBHSW5-P: no dowel hole version for dr 5: the double housing has dowel holes for dr 8 and up (p.489) | yes |
| E-LBHS13S | E-LBHS13S: the medium long housing E-LBHS..S (p.490) is offered for dr [12, 16, 20, 25, 30] only | E-LBHS13S: the medium long housing E-LBHS..S (p.490) is offered for dr [12, 16, 20, 25, 30] only | yes |
| E-LBHS20D-P | E-LBHS20D-P: dowel holes are available on the long type only (p.490), not on the medium housing | E-LBHS20D-P: dowel holes are available on the long type only (p.490), not on the medium housing | yes |
| E-LBHS20S-P | E-LBHS20S-P: dowel holes are available on the long type only (p.490), not on the medium long housing | E-LBHS20S-P: dowel holes are available on the long type only (p.490), not on the medium long housing | yes |
| E-LBHS8L-P | E-LBHS8L-P: no dowel hole version for dr 8: the long housing has dowel holes for dr 16 and up (p.490) | E-LBHS8L-P: no dowel hole version for dr 8: the long housing has dowel holes for dr 16 and up (p.490) | yes |
| E-LBHN16 | 'E-LBHN16': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | 'E-LBHN16': expected E-LBHS<dr>[<length>][-P] (length none = single, D = medium, S = medium long, L = long) or E-LBHSW<dr>[-P] (double), e.g. E-LBHS10, E-LBHS12S, E-LBHS16L-P, E-LBHSW20-P | yes |
| E-LBHSW30D | 'E-LBHSW30D': the double housing E-LBHSW has no length suffix (p.489) | 'E-LBHSW30D': the double housing E-LBHSW has no length suffix (p.489) | yes |

| change | to | changed-in-place vol / area / bbox / faces | direct code (inserted) | python | equal |
|---|---|---|---|---|---|
| E-LBHS16: dowel | 1 | 70792.4 / 15240.8 / 36x47x49 / 21 | 70792.4 / 15240.8 / 36x47x49 / 21 (E-LBHS16-P) | 70792.4 / 15240.8 / 36x47x49 / 21 | yes |
| E-LBHS16L-P: dowel | 0 | 185560.8 / 32029.0 / 36x121x49 / 20 | 185560.8 / 32029.0 / 36x121x49 / 20 (E-LBHS16L) | 185560.8 / 32029.0 / 36x121x49 / 20 | yes |
| E-LBHSW20: dowel | 1 | 178431.0 / 30393.3 / 42x94x54 / 21 | 178431.0 / 30393.3 / 42x94x54 / 21 (E-LBHSW20-P) | 178431.0 / 30393.3 / 42x94x54 / 21 | yes |
| E-LBHS30L-P: dowel | 0 | 674275.1 / 83735.3 / 58x202x71 / 20 | 674275.1 / 83735.3 / 58x202x71 / 20 (E-LBHS30L) | 674275.1 / 83735.3 / 58x202x71 / 20 | yes |

## It stays parametric

The one free parameter is `dowel`. Row for the code, activate it, then `parameters.change dowel` (1 adds the two dowel holes through the `drive_suppression` rules, 0 removes them) on the
configured design; compared with the direct code inserted the same way and with the Python part: identical in all four cases (the rebuild table).

## SolidCraft 0.50.0 observations (exact errors) and workarounds

1. **A free parameter value on an inserted part needs #23175 (our draft, being finished).** `component.insert_design {path, configuration, parameters: {dowel: "1"}}` is accepted and the key
   ignored: the second part comes in with the same bounding box as the first, no error (`bbox max of both parts [[18.000000000000004, 23.500000000000004, 49.00000000000001], [18.000000000000004, 23.500000000000004, 49.00000000000001]]`).
   `component.set_link_parameters` -> `unknown command `component.set_link_parameters``; `generator.parse` -> `unknown command `generator.parse``;
   `generator.insert` -> `unknown command `generator.insert``. `parameters.change dowel 1` in the host design returns without error and leaves the inserted
   part unchanged (`bbox max [[18.000000000000004, 23.500000000000004, 49.00000000000001]]`). Workaround (labelled): a row for the code in a working copy of the model (`config.row {from: <configuration row>, values: {param:dowel: ...}}`),
   inserted with `configuration`; to change `dowel`, change it in the working copy (the rebuild table above) and insert again.
2. **Limits on ordinary edits.** `parameters.change dowel 2` is accepted (the range rule 0..1 only acts on rows: `config.row ... values {param:dowel: "1"}` on a medium housing -> `rule No dowel hole version for this series and dr (S14 p.488 to p.490 dowel tables) restricts the final value`); resolve refuses it with the Python message first.
3. **The thread designation cannot come from a parameter.** One `solid.hole` feature per thread size and per site (M1, M2 ends, M2 middle): 15 features of which 2 are live per Long row and 2 per other row. `solid.hole {thread: "M5"}` is a literal.
4. **Rules addressed by feature name need #23175 (our draft, being finished).** In 0.50.0, rules name features by integer id (`config.rule` schema: `feature` is an integer), so the model is built in two passes (the ids come from the replies of the
   first); a name would keep the rules readable. A rule target must be a configuration column: the dowel parameter and its features are columns.
5. **The seeded row.** `config.configure` seeds a row named `Default` from the first parameter values; `build.py` deletes it with `config.row {name: "Default", delete: true}`
   after the catalogue rows exist, so the table holds exactly the catalogue rows (41: single 10, double 10, medium 8, medium long 5, long 8).


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
