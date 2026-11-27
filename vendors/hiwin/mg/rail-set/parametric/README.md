# hiwin.mg.rail-set as a parametric generator (prototype, SolidCraft 0.50.0)

Question (issue tangency-labs/solidcraft#22331): can a generator be ONE parametric `.sc` plus a configuration table plus an
ordering-code template and a few lines of Rhai, instead of `build.py` emitting fixed numbers? Answer on MG: **the model, the table,
the pattern counts, the optional features and the limits all work on 0.50.0 and give the same solids as the Python generator.
What does not exist yet is a parametric LINK: an inserted part is bodies only, `insert_design` ignores a `parameters` key, and
there is no field-template or Rhai host.** Details, exact errors and the interface SolidCraft needs are below. Full measurements:
[RESULTS.md](RESULTS.md).

## Layout (docs/formats/generator.md, "Generators: interface (version 2)")

```
parametric/
  mg-rail-set/               the package
    generator.toml           [parameters], [[template]], [rows."C-12"] provenance (written by build_package.py from ../data/*.csv)
    mg-rail-set.sc           the parametric model + configuration table + rules (92 KB, built by run_template.sh)
    generator.rhai           resolve(fields), describe(fields): plain Rhai with table() and refuse()
    tables/{rails,blocks,caps}.csv   the catalogue rows (copies of ../data with source/page/status; blocks keyed "<block>-<size>")
  build_template.py          the model as a command list (what is modelled once)
  run_template.sh            builds the .sc: stage 1 parameters, geometry, table; stage 2 rules (they need feature ids)
  harness/                   the end-to-end run: stub.py (parse/code), run_all.py, rhai-resolve/ (a 100-line Rust wrapper of the rhai crate)
  probes.py, run_probes.sh, exp/   the small experiments behind the findings below
  ../../../../../runtime/fieldtemplate.py   Python reference of the field-template syntax
```

Rebuild everything (from the repo root, with `SC_CLI` and `SC_APP` pointing at the SolidCraft 0.50.0 binaries):

```
(cd vendors/hiwin/mg/rail-set/parametric/harness/rhai-resolve && cargo build --release)   # then: export RHAI_RESOLVE=<that binary>
bash vendors/hiwin/mg/rail-set/parametric/run_all.sh out
```

`run_all.sh` builds the template and the package `.sc`, then `harness/run_all.py` takes EVERY line of `codes.txt` through
template -> Rhai -> configuration row + parameters -> parametric design, builds the Python part for the same code, measures both and
runs `src/check.py` on both. About 7 minutes.

## What the design is

- **User parameters.** Row-driven (configuration columns): `size WR HR D h d P Es maxlen W H H1 L1 L B C Mdepth capH`, one value per
  catalogue row, plus the free ones `length blocks caps` (also columns, so rules can range-check them and the row holds the defaults).
  Derived: `n = floor((length - 2*Es)/P) + 1`, `E = (length - (n-1)*P)/2`, `x0` (first block). `gap` (10 mm) is the illustration
  choice the Python generator also has.
- **Rail:** `solid.box length=length width=WR height=HR`, a counterbore `solid.hole` at `x = E` and `solid.pattern.rectangular
  count1="n" spacing1="P"`: the hole count follows `length`.
- **Blocks:** U-profile sketch (rail channel cut in, coordinates are expressions) extruded over `L1`; four threaded holes; the block
  and its holes are patterned with `count1="blocks" spacing1="L + gap"` (blocks centred on the rail through `x0`).
- **Rows:** 8, named `<block>-<size>` (`H-12`): the default rule of the interface doc. Row columns set the size parameters and
  suppress `Block threads M2` or `M3` (the thread designation is not a parameter, see "does not work").
- **Rules (`config.rule`):** `length` range `2*Es .. max_len` per size, `blocks` 1..4, `caps` allowed values `{0}` below size 12,
  and suppress-if: `caps = 0` suppresses `Rail cap 1` and `Rail caps`, `caps = 1` brings them back (hole caps, the catalogue's
  Table 2-4-9 option, MGN12 / MGN15 only).
- Dimensioned geometry only: no appearance bodies, no end caps / seals, so `L` of the block is not in the model (see the check).

## What worked on 0.50.0 (all measured, RESULTS.md)

1. **Expressions in every input.** `solid.box`, sketch points and line ends, `solid.hole` diameters/depths, sketch plane origin,
   extrude distance: `"length"`, `"-WR / 2"`, `"x0 + L1/2 + (-1) * C/2"` all work (probes p01, p02, p04, p05).
2. **Pattern count from an expression.** `count1: "n"` with `n = floor((length - 2*Es)/P) + 1` (unitless user parameter, `unit: ""`):
   p03 gives 12 holes at length 300. A parameter with the default length unit as count is refused (`parameters.add blocks`
   without `unit:""` then `blocks - 1` fails with `expression: cannot subtract a length and a value in length^2`).
3. **Feature pattern of a new-body feature** (`features: ["Block", "Block threads M2", "Block threads M3"]`, `count1: "blocks"`):
   copies come out as separate bodies WITH their holes (p08, 8 threads for two blocks). Caveat: a hole with `targets: ["Block"]`
   replays on the original only (p07: copy `Body1` has no holes); leave `targets` off.
4. **Configuration table:** `config.configure {params, features}`, `config.row {name, values}`, `config.activate {row}` set 21 parameters
   and the two thread suppressions at once.
5. **Suppress-if as a rule:** `drive_suppression` on `caps`; a plain `parameters.change caps=1` switches the two cap features
   (`switched: [{name: "Rail cap 1", suppressed: false}, ...]`).
6. **Limits as rules:** `config.activate` of a row with `length = 900 mm` on MGN7 is refused:
   `configuration rules: rule `MGNR7 lengths, S4 p.85 Table 2-4-15` restricts the final value`; likewise caps on MGN9 and 5 blocks.
7. **`component.insert_design {path, configuration}`:** `configuration: "H-12"` inserts the row at its stored defaults (length 300,
   1 block) and equals the Python `MGN12H1R300Z0C` (volume, area, bbox, faces). An unknown row:
   `invalid parameters for `component.insert_design`: configuration `nope` does not exist in the source design`.
8. **Rebuild on a length change.** On the configured design, `parameters.change length 300 -> 400 mm` rebuilds to exactly
   a fresh `MGN12H2R400Z0C` instance and to the Python part (vol 49296.02, area 24360.16, 90 faces, 3 bodies). In an assembly that
   links the part, editing the linked file's `length` and `component.update_links` gives the same (`updated: [...]`).
9. **Every `codes.txt` line equals the Python part** (volume, area, bbox, faces, bodies): see the table in RESULTS.md. The two
   invalid codes are refused with the Python generator's message, verbatim, from `generator.rhai`.

## What did NOT work / does not exist in 0.50.0

| Wanted | Result on 0.50.0 | Exact text |
|---|---|---|
| Free parameter values on insert | `component.insert_design` accepts a `parameters` key and **ignores it silently** (rail stays 300 mm, no error) | measured x extent 300.0 after `parameters: {length: "400 mm"}` |
| Parametric link | the inserted component holds bodies only; no user parameter reaches the assembly | `parameters.change` in the assembly: `unknown parameter `length``; `component.links` lists `configuration: <row id>` only |
| Change `length` of an inserted part | no command | `unknown command `component.set_link_parameters`` |
| Workaround used (labelled): instance file | `config.activate` + `parameters.change` on a copy of the template, saved, then `component.insert_design` that file; change `length` in the file and `component.update_links` | the inserted part is a static copy of the instance, not the parametric template |
| Limits on an ordinary edit | `parameter_range` / allowed-values are checked at `config.activate` only (documented). `parameters.change length=3000 mm` on MGN12 (max 2000), `blocks=9`, `caps=1` on MGN9 are all accepted | `{"changed": {"length": 3000.0}, "errors": []}` |
| Feature names in rules | `config.rule` wants a numeric feature id | `invalid type: string "Rail cap 1", expected u64` (so the build has two stages: ids come from stage 1's results) |
| Rule target not a column | rule targets must be configured columns | `rule `No hole caps unless caps = 1` target is not configured` (so `caps`, `length`, `blocks` and the two cap features are columns) |
| Thread designation from a parameter | `thread: "M3"` is a literal | two features `Block threads M2` / `M3`, one suppressed per row |
| Body names of pattern copies | features pattern names copies `Body1, Body2, ...` (global counter: `Body20` after a rebuild); a body pattern names `Block (2)` and loses the thread list (`model.threads` 4 instead of 8) | `src/check.py` looks for `Block 1..n`, so the harness renames by x position |
| Hole-count edge | `length` < `2*Es`: n = 0, `parameters.change length=30 mm` is accepted | the pattern count then fails only at rebuild; the Python generator quirk is the same (no hole) |
| Field template, Rhai, `generator.*` | not in 0.50.0 (interface doc: 0.52) | stand-ins below |

## Stand-ins until SolidCraft ships the host

- `runtime/fieldtemplate.py` implements section 3 of the interface doc (longest-match choices, letter maps, typed numbers,
  optional parts, `[E:flag]`, free text with an escape class, separators and case ignored, backtracking, several templates, the
  documented limits). MG's template, in `generator.toml`:
  `MGN{size: int 1..99}{block: C|H}[E:special_block]{blocks: int 1..9}R{length: int 1..9999}[E:special_rail][{preload: Z0|ZF|Z1}][{precision: C|H|P}][{material: M|HC|NC}][{rails: I|II|III|IIII}][+{options: text 1..64}]`
  covers `MGN12H2R300Z0C`, `MGN9C1R195ZFH` and the catalogue's own `MGN 12 C E 2 R1600 E Z1 P M II + SS/U/EL+RC/-O`; it prints
  every `codes.txt` code back unchanged. Size and length are plain integers on purpose: the refusals belong to Rhai so that they carry
  the Python generator's wording (`MGNR12 max single length is 2000 mm`).
- `generator.rhai` is run by the real Rhai engine (`harness/rhai-resolve`, rhai 1.27, the doc's limits, only `table()` and
  `refuse()` registered), not mirrored in Python. `caps` is not in the code (HIWIN has no symbol): it is an option the caller sets
  (`parameters.caps = 1`), refused for sizes below 12 by the allowed-values rule.
- The `check`: `src/check.py check_mgn_dimensioned` runs unchanged on the instance file through a wrapper (harness/run_all.py) that
  renames pattern bodies to `Block i`, ignores the cap bodies and answers the two `component.metadata` rows from the design's
  `document.metadata` (no component exists in the instance). Result 22/23 and 29/31: the only failing row is `Block i length L`,
  the catalogue's block length WITH end caps and seals, which exist only as appearance bodies in the Python generator; the Python
  part with appearance off fails the same row (the table in RESULTS.md has both columns). It is not a parametric-vs-Python difference.

## What SolidCraft needs (interface proposals)

1. **`component.insert_design {path, configuration?, parameters?}` must store and apply `parameters`** (the doc's plan) AND refuse
   unknown keys today (`"unknown parameter `parameters`"`): silently ignoring `parameters` made a 400 mm request build a 300 mm part.
   The link keeps `{configuration, parameters}`; `component.set_link_parameters {component, parameters}` rebuilds. Without it the
   whole proposal collapses back to "bake the values".
2. **Range rules and allowed values on every write path of a link** (insert, set_link_parameters, update_links) and a way to ask
   `parameters.change {..., enforce_rules: true}` in the source design. Today `length=3000 mm` is accepted on MGN12.
3. **Name pattern copies:** `solid.pattern.rectangular {..., body_names: "Block {i}"}` (1-based, `{i}` index) for feature patterns.
   Names like `Block 2` are what checks, BOMs and the assembly browser want; `Body20` changes with the rebuild.
4. **Rules by feature name** (`effect: {feature: "Rail caps"}` instead of a numeric id) and rule targets that do not need a column.
5. **Thread designation as a configurable value:** `solid.hole {thread: "<expression or choice parameter>"}` or a `text` parameter,
   so M2/M3 is one cell instead of two suppressible features.
6. **Hole count < 1:** `n = 0` should be a range error at `parameters.change` (a rule `length >= 2*Es` per row is expressible, but
   not enforced there, point 2).
7. **Measure by occurrence:** `generator.check` needs per-component body names and the thread list of pattern copies
   (`model.threads` returns 4 threads for a body pattern of 2 blocks, 8 for a feature pattern).
8. **Interface doc details that do not fit MG:** (a) a letter map `{block: C=standard, H=heavy}` hands `resolve` the VALUE; this
   package uses a plain choice `{block: C|H}` so the row name is `H-12`; say whether `fields.block` holds the letter or the value;
   (b) `[E:flag]` (a named boolean optional literal) is used twice in one code (`E` after the block and after the length), the doc's
   `[E:flag]` form covers it but the field list returned to `resolve` should say that absent flags are `false`, absent optional
   fields `()`; (c) options outside the code (`caps`) have no place in `generator.parse {code}`; propose `generator.parse {code,
   options: {caps: true}}` handed to `resolve(fields)` as `fields.options`; (d) `table(name, key)` must accept an integer key
   (`table("rails", 12)`): the stand-in registers that overload; (e) per-row provenance in `generator.toml` is generated from the
   CSVs here: the `.csv` `source/page/status` columns are enough for `table()`, but `[rows.*]` repeats them.
