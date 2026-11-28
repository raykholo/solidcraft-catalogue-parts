# misumi.sth.pilot-flanged-shaft-support as a parametric SolidCraft generator

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai, and rules addressed by feature name requires the #23175 surface (unavailable on 0.50.0/0.51.1). The exact command errors quoted below are observations from SolidCraft 0.50.0. On capable hosts, link overrides and ordinary source `parameters.change` enforce limit rules marked `enforce_on_edit`.

The support modelled ONCE in SolidCraft (`pilot-flanged-shaft-support/pilot-flanged-shaft-support.sc`), a configuration table of the catalogue
rows, the ordering code as field templates and the logic as plain Rhai, following SolidCraft's generator interface (`docs/formats/generator.md`,
version 2, issue 22331). The Python generator in `../src` is untouched and is the reference every code below is compared with.

```
pilot-flanged-shaft-support/                 the package layout of the interface document
  generator.toml               [[template]] x2, [rows."<row>"] source / page / status per configuration row
  pilot-flanged-shaft-support.sc    the parametric model + its configuration table (built by build.py)
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

- **One model, 17 user parameters** (`bore body_d fl_d fl_t len mh_d pcd cw cp1 cf cl_b cl_s1 cl_slit cl_x cl_y cl_clear cl_cb`, each a column of
  the table) and 5 derived ones (`cl_ro cl_xo cl_ring0 cl_g0 cl_z1`: the clamp screw axis, the slit, the groove, written as the Python builder
  computes them). Drawn in the order of the Python builder: the pilot-and-sleeve cylinder `body_d x len` (the body, named `Body`), the
  flange, the shaft bore `bore`, four mounting holes, groove, slit, clamp screw clearance hole and counterbore, the threaded clamp hole.
- **The flange is two features, one per shape.** `Flange round` (a circle `fl_d`) and `Flange compact` (a rectangle `cw x fl_d`, four corner
  rounds of `0.25 * cw`), each a sketch and an extrude with `start_offset = fl_t` (the flange stands on the pilot, from z = T to 2 T; the Python
  builder puts the sketch plane there). The mounting holes are two sets of four (`Mounting hole Round 1..4` on the circle `pcd`,
  `Mounting hole Compact 1..4` on `cf x cp1`), each at `z = fl_t - 1`, height `fl_t + 2`.
- **One thread feature per clamp screw size** (M4 M5 M6 M8): `solid.hole` at the point where the screw axis meets the sleeve
  (`cl_xo, cl_x, cl_z1`), depth up to the slit (`cl_xo - cl_slit / 2`). A designation cannot be a parameter (see below).
- **Configuration table = the catalogue rows.** 18 rows, one per (shape, D) of `data/dims.csv` (`round-8` .. `compact-40`; `data/types.csv`
  only adds the material and the surface, which are properties, not geometry). The 17 parameter cells of a row are the table's numbers;
  the suppression cells say which flange, which hole set and which thread size exist. Source, page and status of every row are in
  `generator.toml` `[rows."round-8"]` ... (from the `source`, `page`, `status` columns of the CSV row).

## The ordering code

`generator.toml` has two templates: `E-STHWI{shape: R=round, C=compact}B{d: text 1..6 [0-9]}` (the type letters printed back by the template
printer) and the generic `E-{type: text 1..12 [A-Za-z]}{d: text 1..6 [0-9]}`, which hands every other type text to Rhai. `generator.rhai` does what
`pilot.parse` does, with its messages word for word: an unknown type (`'E-STHWISB10': expected <type><D>, e.g. E-STHWIRB8, with type one
of E-STHWIRB, E-STHWICB`), a D outside the table (`E-STHWIRB6: hole diameter D must be one of [8, 10, ...] (p.540 table)`), and a code that
matches no template (`fn no_match(raw)`). It returns the row (`round-12`), no parameter override (a row carries every dimension), and the
properties of the component: part number, the description (the Python text, word for word), material and surface.

## What was run

For every line of `../codes.txt` (18 valid codes, 8 rejected codes of the file plus 7 extra refusals): code -> field template -> Rhai `resolve` ->
a configuration row of the package model -> a host design inserts the model with `component.insert_design {{configuration}}` -> `inspect.measure`
(volume, area, bbox, faces, bodies) + the unchanged `src/check.py` spec check (run on the inserted part, on a `Support` rebuilt from the Rhai
result and the package tables, never from the Python parser; its `description` is the text Rhai made, and one extra row of both spec checks
requires it to equal the Python description) -> the same code built by the Python generator and measured and checked the same way.
`tools/parametric-verdict` decides equality (volume and area within 1e-6 relative, the same bbox, faces and bodies, the same number of
passed spec rows, the same refusal message).

```
# on a build host (solidcraft-cli 0.50.0 and the Rhai host built from runtime/rhai-run), in the repository root:
export SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run binary>
bash vendors/misumi/sth/pilot-flanged-shaft-support/parametric/ci.sh OUT          # builds the model, runs every code both ways, writes OUT/results.json and OUT/faithfulness.json
tools/parametric-verdict OUT/faithfulness.json
python3 runtime/parametric/harness.py report OUT/results.json     # the tables below
```

## Result: side by side

Volume mm3 / area mm2 / bbox mm / faces. Equal = same bodies, volume and area within 1e-6 relative, same bbox and face count; the spec check
columns are passed rows / rows.

| code | row | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec check python | spec check parametric | equal |
|---|---|---|---|---|---|---|
| E-STHWIRB8 | round-8 | 12498.7 / 5890.2 / 39x39x23 / 25 | 12498.7 / 5890.2 / 39x39x23 / 25 | 26/26 | 26/26 | yes |
| E-STHWIRB10 | round-10 | 19830.0 / 8403.4 / 49x49x25 / 25 | 19830.0 / 8403.4 / 49x49x25 / 25 | 26/26 | 26/26 | yes |
| E-STHWIRB12 | round-12 | 25359.8 / 9771.6 / 52x52x28 / 25 | 25359.8 / 9771.6 / 52x52x28 / 25 | 26/26 | 26/26 | yes |
| E-STHWIRB15 | round-15 | 32621.6 / 11885.1 / 56x56x33 / 25 | 32621.6 / 11885.1 / 56x56x33 / 25 | 26/26 | 26/26 | yes |
| E-STHWIRB16 | round-16 | 34123.2 / 12385.7 / 56x56x36 / 25 | 34123.2 / 12385.7 / 56x56x36 / 25 | 26/26 | 26/26 | yes |
| E-STHWIRB20 | round-20 | 49919.0 / 16083.2 / 64x64x40 / 25 | 49919.0 / 16083.2 / 64x64x40 / 25 | 26/26 | 26/26 | yes |
| E-STHWIRB25 | round-25 | 63961.5 / 19629.7 / 69x69x46 / 25 | 63961.5 / 19629.7 / 69x69x46 / 25 | 26/26 | 26/26 | yes |
| E-STHWIRB30 | round-30 | 102999.7 / 26188.2 / 79x79x50 / 25 | 102999.7 / 26188.2 / 79x79x50 / 25 | 26/26 | 26/26 | yes |
| E-STHWIRB40 | round-40 | 219021.5 / 44746.1 / 104x104x67 / 25 | 219021.5 / 44746.1 / 104x104x67 / 25 | 26/26 | 26/26 | yes |
| E-STHWICB8 | compact-8 | 11595.3 / 5518.7 / 27x39x23 / 32 | 11595.3 / 5518.7 / 27x39x23 / 32 | 25/25 | 25/25 | yes |
| E-STHWICB10 | compact-10 | 17967.0 / 7630.4 / 32x49x25 / 32 | 17967.0 / 7630.4 / 32x49x25 / 32 | 25/25 | 25/25 | yes |
| E-STHWICB12 | compact-12 | 22853.8 / 8901.0 / 34x52x28 / 32 | 22853.8 / 8901.0 / 34x52x28 / 32 | 25/25 | 25/25 | yes |
| E-STHWICB15 | compact-15 | 29835.2 / 10922.0 / 37x56x33 / 32 | 29835.2 / 10922.0 / 37x56x33 / 32 | 25/25 | 25/25 | yes |
| E-STHWICB16 | compact-16 | 31336.8 / 11422.5 / 37x56x36 / 32 | 31336.8 / 11422.5 / 37x56x36 / 32 | 25/25 | 25/25 | yes |
| E-STHWICB20 | compact-20 | 44930.3 / 14779.9 / 42x64x40 / 32 | 44930.3 / 14779.9 / 42x64x40 / 32 | 25/25 | 25/25 | yes |
| E-STHWICB25 | compact-25 | 59043.5 / 18361.1 / 47x69x46 / 32 | 59043.5 / 18361.1 / 47x69x46 / 32 | 25/25 | 25/25 | yes |
| E-STHWICB30 | compact-30 | 97270.4 / 25036.5 / 57x79x50 / 32 | 97270.4 / 25036.5 / 57x79x50 / 32 | 25/25 | 25/25 | yes |
| E-STHWICB40 | compact-40 | 208213.9 / 42953.7 / 76x104x67 / 32 | 208213.9 / 42953.7 / 76x104x67 / 32 | 25/25 | 25/25 | yes |

| rejected code | python message | parametric message | same |
|---|---|---|---|
| E-STHWIRB6 | E-STHWIRB6: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.540 table) | E-STHWIRB6: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.540 table) | yes |
| E-STHWICB35 | E-STHWICB35: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.540 table) | E-STHWICB35: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.540 table) | yes |
| E-STHWIRB50 | E-STHWIRB50: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.540 table) | E-STHWIRB50: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.540 table) | yes |
| E-STHWIRB | 'E-STHWIRB': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | 'E-STHWIRB': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | yes |
| E-STHWISB10 | 'E-STHWISB10': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | 'E-STHWISB10': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | yes |
| E-STHWIRBL16 | 'E-STHWIRBL16': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | 'E-STHWIRBL16': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | yes |
| E-STHWRB10 | 'E-STHWRB10': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | 'E-STHWRB10': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | yes |
| E-STHWIRB9 | E-STHWIRB9: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.540 table) | E-STHWIRB9: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.540 table) | yes |
| E-STHWIRB0 | E-STHWIRB0: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.540 table) | E-STHWIRB0: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.540 table) | yes |
| E-STHWIRB09 | E-STHWIRB9: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.540 table) | E-STHWIRB9: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.540 table) | yes |
| E-STHWIRB100 | E-STHWIRB100: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.540 table) | E-STHWIRB100: hole diameter D must be one of [8, 10, 12, 15, 16, 20, 25, 30, 40] (p.540 table) | yes |
| E-STHWISB8 | 'E-STHWISB8': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | 'E-STHWISB8': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | yes |
| E-STHWI8 | 'E-STHWI8': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | 'E-STHWI8': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | yes |
| E-STHWIRBK12 | 'E-STHWIRBK12': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | 'E-STHWIRBK12': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | yes |
| E-SSTHWIRB12 | 'E-SSTHWIRB12': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | 'E-SSTHWIRB12': expected <type><D>, e.g. E-STHWIRB8, with type one of E-STHWIRB, E-STHWICB | yes |

| row switched on a built design | to | switched vol / area / bbox / faces | direct code (inserted) | equal |
|---|---|---|---|---|
| E-STHWIRB8 | E-STHWICB40 | 208213.9 / 42953.7 / 76x104x67 / 32 | 208213.9 / 42953.7 / 76x104x67 / 32 | yes |
| E-STHWICB30 | E-STHWIRB12 | 25359.8 / 9771.6 / 52x52x28 / 25 | 25359.8 / 9771.6 / 52x52x28 / 25 | yes |
| E-STHWIRB40 | E-STHWIRB8 | 12498.7 / 5890.2 / 39x39x23 / 25 | 12498.7 / 5890.2 / 39x39x23 / 25 | yes |

| code | printed by the template from its fields | same |
|---|---|---|
| E-STHWIRB8 | E-STHWIRB8 | yes |
| E-STHWIRB10 | E-STHWIRB10 | yes |
| E-STHWIRB12 | E-STHWIRB12 | yes |
| E-STHWIRB15 | E-STHWIRB15 | yes |
| E-STHWIRB16 | E-STHWIRB16 | yes |
| E-STHWIRB20 | E-STHWIRB20 | yes |
| E-STHWIRB25 | E-STHWIRB25 | yes |
| E-STHWIRB30 | E-STHWIRB30 | yes |
| E-STHWIRB40 | E-STHWIRB40 | yes |
| E-STHWICB8 | E-STHWICB8 | yes |
| E-STHWICB10 | E-STHWICB10 | yes |
| E-STHWICB12 | E-STHWICB12 | yes |
| E-STHWICB15 | E-STHWICB15 | yes |
| E-STHWICB16 | E-STHWICB16 | yes |
| E-STHWICB20 | E-STHWICB20 | yes |
| E-STHWICB25 | E-STHWICB25 | yes |
| E-STHWICB30 | E-STHWICB30 | yes |
| E-STHWICB40 | E-STHWICB40 | yes |


## SolidCraft 0.50.0 observations (exact errors) and workarounds

1. **A thread designation cannot come from a parameter.** `solid.hole` with `thread: "msize"` (a user parameter) -> `invalid parameters for
   `solid.hole`: unknown tapped thread `msize` (ISO metric or a catalogued UNC/UNF, G, Rp, Rc or NPT size)`. Workaround (labelled): one thread
   feature per screw size (M4 M5 M6 M8), each suppressed in the rows whose screw is another size; they are `temp` units of the build
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
   written without `targets` and the inserted body is named after the model (`pilot-flanged-shaft-support`), not after the code; the spec check is run with its
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

The 0.50.0/0.51.1 results above remain release observations. The #23175 CI artifact records 18 valid, 16 rejects, 3 rebuild checks and 2 blocked records. The next CI run also checks link overrides and ordinary edit refusal with `enforce_on_edit` where limit rules exist; these new checks are pending. Differences remain differences.

Unmatched-code diagnostic: follow-up after #23175: optional no_match(raw) in generator.rhai.

The supplied #23175 artifact includes 0 link checks; the added ordinary-edit enforcement check awaits CI.
