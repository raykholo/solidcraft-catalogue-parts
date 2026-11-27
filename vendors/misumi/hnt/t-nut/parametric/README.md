# misumi.hnt.t-nut as a parametric SolidCraft generator

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai, and rules addressed by feature name needs #23175 (our draft, being finished). The exact command errors quoted below are observations from SolidCraft 0.50.0. The draft checks ranges on link overrides; ordinary source `parameters.change` still does not enforce range restrictions.

The T-nut modelled ONCE in SolidCraft (`hnt-t-nut/hnt-t-nut.sc`), a configuration table of the catalogue rows, the ordering code as a field template
and the logic as plain Rhai, following SolidCraft's generator interface (`docs/formats/generator.md`, version 2, issue 22331). The Python generator
in `../src` is untouched and is the reference every code below is compared with.

```
hnt-t-nut/                     the package layout of the interface document
  generator.toml               [parameters], [[template]], [rows."<type>-<M>"] source / page / status per configuration row
  hnt-t-nut.sc                 the parametric model + its configuration table (built by build.py)
  generator.rhai               resolve(fields) -> #{configuration, parameters, properties}; fields(configuration, parameters) -> fields
  tables/*.csv                 types, tap, params: copied from ../data/*.csv (rows keep source, page, status); params.csv gains `types` and `other_types`
build.py                       builds the model with solidcraft-cli
run_codes.py  report.py        the end-to-end proof (results.json) and the tables below
faithfulness.py  ci.sh         faithfulness.json for tools/parametric-verdict (what the `parametric` workflow runs)
../../../../runtime/parametric/  helpers shared by the harnesses (solidcraft-cli, the Rhai host, measuring, the spec check on an inserted part)
```

## How the model is built (all of it worked on SolidCraft 0.50.0)

- **Parameters.** `T` (total thickness) and `pilot` (the tap drill, the modelled hole of the tapped bore). Both are columns of the configuration table.
- **Section: one feature set per shoulder height E.** E is 3.3 on four types and 3.5 on HNTTSN5, and the Python generator sizes the R1.0 round of
  the flank so that it and the R0.2 round of the shoulder exactly use up the land (`min(R1.0, (E - 0.2 - 3) / tan 17.5 deg)`). A parameter change
  between the two sections is refused by 0.50.0 (`parameters.change E 3.5` on a model drawn at 3.3: "would flip the sketch over", see below), so the
  model has two sections (`Profile E3.3 T4.1`, `Profile E3.5 T4.3`, each with its extrusion named `Nut E.. T..`, both producing the body `Nut`) and each
  row suppresses the other (the per-row choice between alternative features, S4 of `docs/parametric-generators.md`). The pilot bore cuts the body
  `Nut` whichever section is live.
- **Thread: one cosmetic thread feature per size** (`Thread M3`, `Thread M4`, `Thread M5`, `solid.thread` of the nominal size on the pilot bore,
  length `T`): a thread designation cannot come from a parameter, so each row suppresses the other two.
- **Configuration table = the valid (type, M) pairs.** 9 rows from `data/types.csv` (`allowed_m`), named as the canonical code (`HNTT5-4`,
  `HNTTSN5-3`, ...): cells `T`, `pilot` and the suppression of the two sections and the three threads. No rules are needed: nothing is free.

## The ordering code

`generator.toml`: `{type: text 3..9 [A-Za-z0-9]}[\-{m: text 1..5 [0-9.]}]` and a catch-all second template. The type and M are text fields; `generator.rhai` carries every Python
refusal with its message word for word: the shape of the code (`S?HNT[A-Z]*5` and `\d+(\.\d)?`), the types of the 5 series that are valid but not drawn
(`not_modelled`), an unknown type, and "offered in M3, M4, M5, not M<m>" from the `allowed_m` cell of the type. `HNTT5` alone resolves to `HNTT5-5`
(`default_m` in `tables/params.csv`, catalogue note). The part number, description and material metadata are plain Rhai over the tables.
`fields(configuration, parameters)` is the inverse (code printing): for every valid code parse(print(parse(code))) gives the same configuration.

## What was run

For every line of `../codes.txt` (5 valid codes, 3 `!` rejects) plus the 4 other (type, M) rows of the table (all 9 rows) and 25 extra refusals:
code -> template -> Rhai `resolve` -> the configuration row named by the code -> a design inserts the package model with
`component.insert_design {configuration}` -> `inspect.measure` (volume, area, bbox, faces) + `model.threads` + the unchanged `src/check.py` spec check
(run on the inserted part, with the `Nut` it needs rebuilt from the Rhai result and the package tables, never from the Python parser) -> the same
code built by the Python generator and measured the same way. There is no free parameter (E, T and the tap drill are table cells), so there is no
rebuild check.

```
SC_CLI=<solidcraft-cli> RHAI_RUN=<rhai-run> bash ci.sh OUTDIR     # build.py, run_codes.py, faithfulness.py -> OUTDIR/faithfulness.json
tools/parametric-verdict OUTDIR/faithfulness.json
python3 report.py OUTDIR/results.json                             # the tables below
```

`RHAI_RUN` is the host built from `runtime/rhai-run` (`cargo build --release`).

## Result: side by side

Equal means volume and area within 1e-6 relative, the same bbox, face and body counts (decided by `tools/parametric-verdict`); this table also
compares the thread span.

| code | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec check python | spec check parametric | equal (incl. thread span) |
|---|---|---|---|---|---|
| HNTT5 | 256.161 / 338.175 / 10x10x4.1 / 21 | 256.161 / 338.175 / 10x10x4.1 / 21 | 14/14 | 14/14 | yes |
| HNTT5-4 | 277.896 / 337.186 / 10x10x4.1 / 21 | 277.896 / 337.186 / 10x10x4.1 / 21 | 14/14 | 14/14 | yes |
| HNTTSN5-3 | 311.697 / 343.459 / 10x10x4.3 / 21 | 311.697 / 343.459 / 10x10x4.3 / 21 | 14/14 | 14/14 | yes |
| HNTTSS5-5 | 256.161 / 338.175 / 10x10x4.1 / 21 | 256.161 / 338.175 / 10x10x4.1 / 21 | 14/14 | 14/14 | yes |
| HNTTV5-5 | 256.161 / 338.175 / 10x10x4.1 / 21 | 256.161 / 338.175 / 10x10x4.1 / 21 | 14/14 | 14/14 | yes |
| HNTT5-3 | 292.838 / 334.170 / 10x10x4.1 / 21 | 292.838 / 334.170 / 10x10x4.1 / 21 | 14/14 | 14/14 | yes |
| HNTT5-5 | 256.161 / 338.175 / 10x10x4.1 / 21 | 256.161 / 338.175 / 10x10x4.1 / 21 | 14/14 | 14/14 | yes |
| HNTTZ5-5 | 256.161 / 338.175 / 10x10x4.1 / 21 | 256.161 / 338.175 / 10x10x4.1 / 21 | 14/14 | 14/14 | yes |
| HNTTSN5-4 | 296.027 / 346.977 / 10x10x4.3 / 21 | 296.027 / 346.977 / 10x10x4.3 / 21 | 14/14 | 14/14 | yes |
| HNTTSN5-5 | 273.231 / 348.532 / 10x10x4.3 / 21 | 273.231 / 348.532 / 10x10x4.3 / 21 | 14/14 | 14/14 | yes |

| rejected code | python message | parametric message | same |
|---|---|---|---|
| HNTT5-6 | HNTT5 is offered in M3, M4, M5, not M6 | HNTT5 is offered in M3, M4, M5, not M6 | yes |
| HNTTV5-4 | HNTTV5 is offered in M5, not M4 | HNTTV5 is offered in M5, not M4 | yes |
| HNTT5-3.5 | HNTT5 is offered in M3, M4, M5, not M3.5 | HNTT5 is offered in M3, M4, M5, not M3.5 | yes |
| HNTU5 | HNTU5: a valid 5 series nut, not drawn here; drawn: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5 | HNTU5: a valid 5 series nut, not drawn here; drawn: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5 | yes |
| HNTU5-5 | HNTU5: a valid 5 series nut, not drawn here; drawn: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5 | HNTU5: a valid 5 series nut, not drawn here; drawn: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5 | yes |
| SHNTU5 | SHNTU5: a valid 5 series nut, not drawn here; drawn: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5 | SHNTU5: a valid 5 series nut, not drawn here; drawn: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5 | yes |
| HNTTX5 | unknown nut type 'HNTTX5'; drawn: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5 | unknown nut type 'HNTTX5'; drawn: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5 | yes |
| HNTT5-0 | HNTT5 is offered in M3, M4, M5, not M0 | HNTT5 is offered in M3, M4, M5, not M0 | yes |
| HNTT5-5.5 | HNTT5 is offered in M3, M4, M5, not M5.5 | HNTT5 is offered in M3, M4, M5, not M5.5 | yes |
| HNTT5-3.0 | HNTT5 is offered in M3, M4, M5, not M3.0 | HNTT5 is offered in M3, M4, M5, not M3.0 | yes |
| HNTT5-6 | HNTT5 is offered in M3, M4, M5, not M6 | HNTT5 is offered in M3, M4, M5, not M6 | yes |
| HNTTSS5-3 | HNTTSS5 is offered in M5, not M3 | HNTTSS5 is offered in M5, not M3 | yes |
| HNTTZ5-4 | HNTTZ5 is offered in M5, not M4 | HNTTZ5 is offered in M5, not M4 | yes |
| HNTTV5-3 | HNTTV5 is offered in M5, not M3 | HNTTV5 is offered in M5, not M3 | yes |
| HNTTSN5-6 | HNTTSN5 is offered in M3, M4, M5, not M6 | HNTTSN5 is offered in M3, M4, M5, not M6 | yes |
| HNTT6-4 | 'HNTT6-4': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | 'HNTT6-4': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | yes |
| HNTT-4 | 'HNTT-4': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | 'HNTT-4': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | yes |
| XHNTT5 | 'XHNTT5': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | 'XHNTT5': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | yes |
| HNTT5-12 | HNTT5 is offered in M3, M4, M5, not M12 | HNTT5 is offered in M3, M4, M5, not M12 | yes |
| HNTTSN5-2 | HNTTSN5 is offered in M3, M4, M5, not M2 | HNTTSN5 is offered in M3, M4, M5, not M2 | yes |
| HNST5 | 'HNST5': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | 'HNST5': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | yes |
| HNTTBS5-5 | HNTTBS5: a valid 5 series nut, not drawn here; drawn: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5 | HNTTBS5: a valid 5 series nut, not drawn here; drawn: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5 | yes |
| HNTT5-06 | HNTT5 is offered in M3, M4, M5, not M06 | HNTT5 is offered in M3, M4, M5, not M06 | yes |
| HNTT5- | 'HNTT5-': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | 'HNTT5-': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | yes |
| HNTT5-4-4 | 'HNTT5-4-4': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | 'HNTT5-4-4': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | yes |
| HNTT5--4 | 'HNTT5--4': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | 'HNTT5--4': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | yes |
| HNTT5-4- | 'HNTT5-4-': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | 'HNTT5-4-': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | yes |
| HNTT | 'HNTT': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | 'HNTT': expected <type>-<M>, e.g. HNTT5-4 (types: HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5) | yes |

## What SolidCraft 0.50.0 could not express, and the workarounds

1. **A parameter change between two sketches whose fillets exactly consume an edge is refused.** The nut model drawn at E 3.3 (T 4.1):
   `parameters.change {"changes": {"E": "3.5 mm"}}` ->
   `sketch `Profile`: the new values would flip the sketch over (k10, k11, k20, k21 would change orientation); the values were not changed`;
   the same for `config.activate` of a row with E 3.5, and from E 3.5 back to 3.3 (`k7, k8, k10, k11, k15, k16, k20, k21`). E 3.4 is accepted. The
   Python generator's flank round is `min(R1.0, (E - 0.2 - 3) / tan 17.5 deg)`, which makes the rounds meet exactly, so the sketch sits on a
   degenerate boundary. Workaround (labelled): one section per E, suppressed per row (`Profile E3.3 T4.1` / `Profile E3.5 T4.3`). Needed from
   #23175: a sketch update that goes through the degenerate state (or reports the orientation test with a tolerance), so a parameter `E` can drive
   both types.
2. **Thread designation from a parameter** (S8): one `solid.thread` feature per size M3 / M4 / M5, suppressed by the row. Needed:
   `designation` as an expression or a size parameter (or `solid.thread` sized from the pilot bore).
3. **Template engine, dangling separators (fixed here).** The field template skipped separators, so `HNTT5-` read as `HNTT5` and `HNTT5--4` as
   `HNTT5-4`, and a code with an extra field (`HNTT5-4-4`) matched nothing. Now the template is
   `{type: text 3..9 [A-Za-z0-9]}[\-{m: text 1..5 [0-9.]}]` (the `-` before M is a required separator that the next field does not skip), the stand-in
   engine refuses a dangling separator at the end of a code, and a catch-all second template `{raw: text 1..128 [A-Za-z0-9._ /-]}` lets the script give
   Python's `expected <type>-<M>` refusal. `HNTT5-`, `HNTT5-4-4`, `HNTT5--4`, `HNTT5-4-` and `HNTT` are in the compared rejects. The engine change leaves the
   HFS, MG and shaft results unchanged.

This package has no free ordering parameter, so it adds no optional link-parameter checks. Internal dimension rebuild probes remain as recorded above.
