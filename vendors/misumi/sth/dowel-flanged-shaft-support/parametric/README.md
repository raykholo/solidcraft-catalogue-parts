# misumi.sth.dowel-flanged-shaft-support as a parametric SolidCraft generator

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai, and rules addressed by feature name needs #23175 (our draft, being finished). The exact command errors quoted below are observations from SolidCraft 0.50.0. The draft checks ranges on link overrides; ordinary source `parameters.change` still does not enforce range restrictions.

The support modelled ONCE in SolidCraft (`dowel-flanged-shaft-support/dowel-flanged-shaft-support.sc`), a configuration table of the catalogue
rows, the ordering code as field templates and the logic as plain Rhai, following SolidCraft's generator interface (`docs/formats/generator.md`,
version 2, issue 22331). The Python generator in `../src` is untouched and is the reference every code below is compared with.

```
dowel-flanged-shaft-support/                 the package layout of the interface document
  generator.toml               [[template]] x2, [rows."<row>"] source / page / status per configuration row
  dowel-flanged-shaft-support.sc    the parametric model + its configuration table (built by build.py)
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

- **One model, 18 user parameters** (`bore body_d fl_d fl_t len mh_d pcd cw cp1 cf dw_d cl_b cl_s1 cl_slit cl_x cl_y cl_clear cl_cb`, each a column
  of the table) and 5 derived ones (the clamp screw axis, the slit and the groove, as the Python builder computes them). Drawn in the order
  of the Python builder: the sleeve cylinder (`Body`), the round flange `fl_d` (sketch and extrude `fl_t`), two flat cuts, the shaft bore, the
  four mounting holes, the two positioning holes, groove, slit, clamp screw clearance hole and counterbore, the threaded clamp hole.
- **Round and compact differ by suppression only.** The compact flange is the round flange cut to the width `cw` by two flat boxes
  (`Flange flat side +X / -X`, suppressed on the round shape); the mounting holes (`Mounting hole Round 1..4` on `pcd`, `Mounting hole
  Compact 1..4` on `cf x cp1`) and the two positioning holes (`Positioning hole Round 1..2` at 45 and 225 degrees on the circle `pcd`,
  `Positioning hole Compact 1..2` on the Y axis, `pcd` apart) each exist as one set per shape: "position columns" of the analysis are the
  expressions of the two sets, the other set is suppressed.
- **One thread feature per clamp screw size** (M5, M6), at the point where the screw axis meets the sleeve, depth up to the slit.
- **Configuration table = the catalogue rows.** 10 rows, one per (shape, D) of `data/dims.csv` (`round-12` .. `compact-30`); `data/types.csv`
  adds the material and the surface (the black oxide, nickel and stainless types of a shape share one row). Source, page and status of every row are in
  `generator.toml` `[rows."round-12"]` ...

## The ordering code

`generator.toml` has two templates: `E-[S:stainless]STHW{shape: R=round, C=compact}[B:black]K{d: text 1..6 [0-9]}` (five types: E-STHWRBK, E-STHWRK,
E-SSTHWRK, E-STHWCBK, E-SSTHWCK; the printer writes the type back from the shape and the two flags) and the generic `E-{type: text 1..12
[A-Za-z]}{d: text 1..6 [0-9]}`, which hands every other type text to Rhai. `generator.rhai` does what `dowel.parse` does, with its messages word for word
(unknown type, D outside the table, a code that matches no template through `fn no_match(raw)`), and returns the row (`round-12`), no
parameter override, and the properties: part number, description (the Python text word for word), material and surface.

## What was run

For every line of `../codes.txt` (17 valid codes, 9 rejected codes of the file plus 9 extra refusals): code -> field template -> Rhai `resolve` ->
a configuration row of the package model -> a host design inserts the model with `component.insert_design {{configuration}}` -> `inspect.measure`
(volume, area, bbox, faces, bodies) + the unchanged `src/check.py` spec check (run on the inserted part, on a `Support` rebuilt from the Rhai
result and the package tables, never from the Python parser; its `description` is the text Rhai made, and one extra row of both spec checks
requires it to equal the Python description) -> the same code built by the Python generator and measured and checked the same way.
`tools/parametric-verdict` decides equality (volume and area within 1e-6 relative, the same bbox, faces and bodies, the same number of
passed spec rows, the same refusal message).

```
# on a build host (solidcraft-cli 0.50.0 and the Rhai host built from runtime/rhai-run), in the repository root:
export SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run binary>
bash vendors/misumi/sth/dowel-flanged-shaft-support/parametric/ci.sh OUT          # builds the model, runs every code both ways, writes OUT/results.json and OUT/faithfulness.json
tools/parametric-verdict OUT/faithfulness.json
python3 runtime/parametric/harness.py report OUT/results.json     # the tables below
```

## Result: side by side

Volume mm3 / area mm2 / bbox mm / faces. Equal = same bodies, volume and area within 1e-6 relative, same bbox and face count; the spec check
columns are passed rows / rows.

| code | row | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec check python | spec check parametric | equal |
|---|---|---|---|---|---|---|
| E-STHWRBK12 | round-12 | 21062.2 / 9042.8 / 52x52x22 / 25 | 21062.2 / 9042.8 / 52x52x22 / 25 | 27/27 | 27/27 | yes |
| E-STHWRBK16 | round-16 | 29321.4 / 11534.4 / 56x56x30 / 25 | 29321.4 / 11534.4 / 56x56x30 / 25 | 27/27 | 27/27 | yes |
| E-STHWRBK20 | round-20 | 42065.1 / 14748.1 / 64x64x32 / 25 | 42065.1 / 14748.1 / 64x64x32 / 25 | 27/27 | 27/27 | yes |
| E-STHWRBK25 | round-25 | 54712.7 / 18059.1 / 69x69x38 / 25 | 54712.7 / 18059.1 / 69x69x38 / 25 | 27/27 | 27/27 | yes |
| E-STHWRBK30 | round-30 | 85744.6 / 23782.0 / 79x79x40 / 25 | 85744.6 / 23782.0 / 79x79x40 / 25 | 27/27 | 27/27 | yes |
| E-STHWRK12 | round-12 | 21062.2 / 9042.8 / 52x52x22 / 25 | 21062.2 / 9042.8 / 52x52x22 / 25 | 27/27 | 27/27 | yes |
| E-STHWRK20 | round-20 | 42065.1 / 14748.1 / 64x64x32 / 25 | 42065.1 / 14748.1 / 64x64x32 / 25 | 27/27 | 27/27 | yes |
| E-STHWRK30 | round-30 | 85744.6 / 23782.0 / 79x79x40 / 25 | 85744.6 / 23782.0 / 79x79x40 / 25 | 27/27 | 27/27 | yes |
| E-SSTHWRK16 | round-16 | 29321.4 / 11534.4 / 56x56x30 / 25 | 29321.4 / 11534.4 / 56x56x30 / 25 | 27/27 | 27/27 | yes |
| E-SSTHWRK25 | round-25 | 54712.7 / 18059.1 / 69x69x38 / 25 | 54712.7 / 18059.1 / 69x69x38 / 25 | 27/27 | 27/27 | yes |
| E-STHWCBK12 | compact-12 | 18114.5 / 7997.4 / 34x52x22 / 28 | 18114.5 / 7997.4 / 34x52x22 / 28 | 26/26 | 26/26 | yes |
| E-STHWCBK16 | compact-16 | 26000.1 / 10361.8 / 37x56x30 / 28 | 26000.1 / 10361.8 / 37x56x30 / 28 | 26/26 | 26/26 | yes |
| E-STHWCBK20 | compact-20 | 36170.7 / 13172.3 / 42x64x32 / 28 | 36170.7 / 13172.3 / 42x64x32 / 28 | 26/26 | 26/26 | yes |
| E-STHWCBK25 | compact-25 | 48566.7 / 16424.4 / 47x69x38 / 28 | 48566.7 / 16424.4 / 47x69x38 / 28 | 26/26 | 26/26 | yes |
| E-STHWCBK30 | compact-30 | 77468.8 / 22013.1 / 57x79x40 / 28 | 77468.8 / 22013.1 / 57x79x40 / 28 | 26/26 | 26/26 | yes |
| E-SSTHWCK12 | compact-12 | 18114.5 / 7997.4 / 34x52x22 / 28 | 18114.5 / 7997.4 / 34x52x22 / 28 | 26/26 | 26/26 | yes |
| E-SSTHWCK30 | compact-30 | 77468.8 / 22013.1 / 57x79x40 / 28 | 77468.8 / 22013.1 / 57x79x40 / 28 | 26/26 | 26/26 | yes |

| rejected code | python message | parametric message | same |
|---|---|---|---|
| E-STHWRBK10 | E-STHWRBK10: hole diameter D must be one of [12, 16, 20, 25, 30] (p.537 table) | E-STHWRBK10: hole diameter D must be one of [12, 16, 20, 25, 30] (p.537 table) | yes |
| E-STHWCBK8 | E-STHWCBK8: hole diameter D must be one of [12, 16, 20, 25, 30] (p.537 table) | E-STHWCBK8: hole diameter D must be one of [12, 16, 20, 25, 30] (p.537 table) | yes |
| E-STHWRBK40 | E-STHWRBK40: hole diameter D must be one of [12, 16, 20, 25, 30] (p.537 table) | E-STHWRBK40: hole diameter D must be one of [12, 16, 20, 25, 30] (p.537 table) | yes |
| E-STHWRBK | 'E-STHWRBK': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | 'E-STHWRBK': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | yes |
| E-STHWCK20 | 'E-STHWCK20': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | 'E-STHWCK20': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | yes |
| E-SSTHWCBK20 | 'E-SSTHWCBK20': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | 'E-SSTHWCBK20': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | yes |
| E-STHWSBK16 | 'E-STHWSBK16': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | 'E-STHWSBK16': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | yes |
| E-STHWRB16 | 'E-STHWRB16': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | 'E-STHWRB16': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | yes |
| E-STHWRBK13 | E-STHWRBK13: hole diameter D must be one of [12, 16, 20, 25, 30] (p.537 table) | E-STHWRBK13: hole diameter D must be one of [12, 16, 20, 25, 30] (p.537 table) | yes |
| E-STHWRBK0 | E-STHWRBK0: hole diameter D must be one of [12, 16, 20, 25, 30] (p.537 table) | E-STHWRBK0: hole diameter D must be one of [12, 16, 20, 25, 30] (p.537 table) | yes |
| E-STHWRBK09 | E-STHWRBK9: hole diameter D must be one of [12, 16, 20, 25, 30] (p.537 table) | E-STHWRBK9: hole diameter D must be one of [12, 16, 20, 25, 30] (p.537 table) | yes |
| E-STHWRBK100 | E-STHWRBK100: hole diameter D must be one of [12, 16, 20, 25, 30] (p.537 table) | E-STHWRBK100: hole diameter D must be one of [12, 16, 20, 25, 30] (p.537 table) | yes |
| E-STHWSBK16 | 'E-STHWSBK16': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | 'E-STHWSBK16': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | yes |
| E-STHWRK | 'E-STHWRK': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | 'E-STHWRK': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | yes |
| E-SSTHWCBK12 | 'E-SSTHWCBK12': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | 'E-SSTHWCBK12': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | yes |
| E-STHWCK12 | 'E-STHWCK12': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | 'E-STHWCK12': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | yes |
| E-STHWRBKL16 | 'E-STHWRBKL16': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | 'E-STHWRBKL16': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | yes |
| E-STHWIRBK12 | 'E-STHWIRBK12': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | 'E-STHWIRBK12': expected <type><D>, e.g. E-STHWRBK12, with type one of E-STHWRBK, E-STHWRK, E-SSTHWRK, E-STHWCBK, E-SSTHWCK | yes |

| row switched on a built design | to | switched vol / area / bbox / faces | direct code (inserted) | equal |
|---|---|---|---|---|
| E-STHWRBK12 | E-STHWCBK30 | 77468.8 / 22013.1 / 57x79x40 / 28 | 77468.8 / 22013.1 / 57x79x40 / 28 | yes |
| E-STHWCBK16 | E-SSTHWRK25 | 54712.7 / 18059.1 / 69x69x38 / 25 | 54712.7 / 18059.1 / 69x69x38 / 25 | yes |
| E-STHWRBK30 | E-STHWRBK12 | 21062.2 / 9042.8 / 52x52x22 / 25 | 21062.2 / 9042.8 / 52x52x22 / 25 | yes |

| code | printed by the template from its fields | same |
|---|---|---|
| E-STHWRBK12 | E-STHWRBK12 | yes |
| E-STHWRBK16 | E-STHWRBK16 | yes |
| E-STHWRBK20 | E-STHWRBK20 | yes |
| E-STHWRBK25 | E-STHWRBK25 | yes |
| E-STHWRBK30 | E-STHWRBK30 | yes |
| E-STHWRK12 | E-STHWRK12 | yes |
| E-STHWRK20 | E-STHWRK20 | yes |
| E-STHWRK30 | E-STHWRK30 | yes |
| E-SSTHWRK16 | E-SSTHWRK16 | yes |
| E-SSTHWRK25 | E-SSTHWRK25 | yes |
| E-STHWCBK12 | E-STHWCBK12 | yes |
| E-STHWCBK16 | E-STHWCBK16 | yes |
| E-STHWCBK20 | E-STHWCBK20 | yes |
| E-STHWCBK25 | E-STHWCBK25 | yes |
| E-STHWCBK30 | E-STHWCBK30 | yes |
| E-SSTHWCK12 | E-SSTHWCK12 | yes |
| E-SSTHWCK30 | E-SSTHWCK30 | yes |


## SolidCraft 0.50.0 observations (exact errors) and workarounds

1. **A thread designation cannot come from a parameter.** `solid.hole` with `thread: "msize"` (a user parameter) -> `invalid parameters for
   `solid.hole`: unknown tapped thread `msize` (ISO metric or a catalogued UNC/UNF, G, Rp, Rc or NPT size)`. Workaround (labelled): one thread
   feature per screw size (M5 M6), each suppressed in the rows whose screw is another size; they are `temp` units of the build
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
   written without `targets` and the inserted body is named after the model (`dowel-flanged-shaft-support`), not after the code; the spec check is run with its
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
