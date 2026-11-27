# Generator packages (data-only generators)

Status: **provisional**. The format is the SolidCraft generator package, `solidcraft-generator/1`, draft v0, specified upstream in
`docs/formats/generator-package.md` and `generator-package.schema.json` of the SolidCraft repository (draft pull request
tangency-labs/solidcraft#23175, part of RFC 0017). This repository does not define a format of its own: it reads that spec, ships
`schema/generator-package.schema.json` (a copy of the draft schema, see NOTICE) and implements the spec in a reference evaluator.
When the spec moves, change the evaluator and the exporter descriptions here; the packages are regenerated, never hand-edited.

A package is one file, `packages/<id>.generator.json`: grammar, tables with `source` / `page` / `status` columns, lookups, variables,
rules, command template, checks, provenance and guarantee level. No code. SolidCraft (later) runs it with `generator.build`; until
then `runtime/package.py` does, over the same JSON.

## What is here

| File | Does |
|---|---|
| `packages/*.generator.json` | the exported packages (committed; CI fails when they differ from the exporter's output) |
| `schema/generator-package.schema.json` | the upstream draft schema, unchanged |
| `runtime/expr.py` | the spec's expression language (section 4): tokenizer and parser written by hand, no `eval`, no `ast`, bounded (512 characters, depth 32, 10000 steps per expression, 1,000,000 per build) |
| `runtime/package.py` | the evaluator: grammar tokens, defaults, lookups, vars, rules, steps with `when` / `repeat`, `${}` substitution, checks, limits; plus `validate()` (schema, expression names and order, RFC 0019 examples, steps) |
| `runtime/package_export/<id>.py` | the per-generator export description (hand-written): what the Python logic is, said declaratively |
| `tools/export-package GENERATOR_DIR --out packages` | writes the package; `--check` validates and fails on a stale or orphaned file |
| `tools/package-equiv [GENERATOR_DIR ...]` | for every code in `codes.txt` (and a seeded sweep) the package must give the Python generator's command list, and refuse what it refuses; `--build` also builds both with solidcraft-cli |

```
tools/export-package                       # rewrite packages/
tools/export-package --check               # CI: packages are current and valid
tools/package-equiv                        # cheap equivalence, no SolidCraft
tools/package-equiv --build --record DIR   # on a build host: volume / bbox / faces of both, the Python spec check on the package-built part
```

`--build` needs solidcraft-cli, so it runs on a build host (in CI, on the runner), not on a laptop by default. `--record` writes `checks/<ver>/package-measured.json` (volume,
bounding box, face count per code as SolidCraft built the package), which `tools/export-package` puts into the package `checks`.

## How a generator maps to the format

* **Grammar**: `alternatives` of tokens (`lit`, `enum`, `int`, `decimal`, `chars`, `optional` with `default`, `flags`). The
  RFC 0019 regexes stay in `declares.matches` as search hints; `validate()` requires every `examples` code to parse and every
  `negative` code to be refused.
* **Tables**: `data/*.csv` rows with their provenance columns, typed (`text`, `number`, `list`, `points`). Where the format has no
  loops or list building, the exporter adds derived columns (outline polygons, fillet references, void paths, bore and tap points per
  profile; the T-nut section polygon per type) computed from the same row by the Python generator's own geometry; the row's `note`
  says so. The number a derived column comes from stays in the row.
* **Lookups / defaults / vars / rules**: the spec's pipeline. A constant such as `params.plan` is looked up through a `defaults`
  constant used as the key.
* **Steps**: the Python command list as a template. Parts that depend on the code are `when` / `repeat` steps (extrusion wrench holes);
  profile-dependent counts (voids, bores, tapped bores) are a fixed number of `when` steps over derived columns.
* **Provenance**: `sources` from `sources.toml`, `guarantee` from the generator's level (`tools/provenance` rules), the review
  evidence under `x-generator`.

## Deviations from the Python generators

The package is checked against the Python generator on every `codes.txt` code and a sweep. These differences are known and accepted:

1. Input is case-sensitive (the spec's `enum` has no case folding); the Python generators upper-case first.
2. `HNTT5-04` style numbers with leading zeros, and `100.0` style length text, are not normalised: the package refuses the former and
   keeps the written text in the part name for the latter.
3. `-X5` together with `-X8`: the Python generator takes the last one, the package refuses.
4. Refusals that the package's grammar makes (unknown alteration, repeated alteration, unlisted M such as `3.5`) carry the grammar's single
   `refuse` text; the Python messages name the cause. `tools/package-equiv` prints every message that differs.
5. Which of several problems in one code is reported first can differ (the package runs its rules in a fixed order).
6. The package's own checks cover the geometry the spec can state (volume, bounding box, faces, dimensions = variables). The
   dimension-by-dimension spec check stays the Python `src/check.py` and is run on the package-built part by `--build`.

## Gaps for the spec

Each is something these two generators needed that spec v0 cannot say. Where noted, the evaluator implements it under an `x-` key so
the equivalence runs; the rest were worked around inside the format.

1. **`x-early-rules`, implemented.** A `not_modelled` refusal for a code that has no table row. Rules run after lookups, so a valid-but-
   not-drawn type (`HNTU5`, `NEFS6`) hits `missing` first, and `missing` cannot carry a `kind`. Wanted: `kind` on a lookup, or
   `"phase": "before_lookups"` on a rule. Example:
   `"x-early-rules": [{"when": "type == \"HNTU5\" || type == \"HNST5\"", "refuse": "{type}: a valid 5 series nut, not drawn here", "kind": "not_modelled"}]`
2. **Case folding.** Codes are typed in any case; the Python generators upper-case. Wanted: `"nocase": true` on `enum` / `chars`, or
   `"grammar": {"normalize": ["upper"]}`.
3. **Number to text.** `${}` and `{}` need a defined format. Used: whole numbers without `.0`, others shortest round-trip (so
   `497.5`, `1000`, `4.2`). `fmt(x, digits)` gives fixed digits only; wanted `fmt(x)` = this default, or the C `%g`.
4. **Empty cells.** A profile has no void, no fifth bore, no third tap. Used: empty `points` / `list` cell = empty list; `number` columns
   hold 0 for "none". Wanted: say that empty is legal for `list` / `points` (and optionally `number` = absent with `has(x)`).
5. **Numeric lists and nested loops.** Bores (x, y, d) and taps (y, z, label) are per-profile lists of 0 to 5 items. `list` holds text
   and `points` holds pairs, so a diameter per bore does not fit; unrolled into `when` steps over columns `b0_c b0_d ... b4_c b4_d`.
   Wanted: a `numbers` column type, or `points` with 3 values, so one `repeat` with `at(...)` does it:
   `{"command": "sketch.circle.center", "repeat": {"var": "i", "count": "len(pr.bores)", "max": 5}, "params": {"center": "${at(pr.bores, i)}", "diameter": "${at(pr.bore_d, i)}"}}`.
6. **Repeating a group of steps.** The 4040 centre void is four times (open polyline run, three-point arc) in that order; one `repeat`
   per command would emit all runs and then all arcs, which is a different command list. Unrolled into eight `when` steps. Wanted:
   `repeat` on a block: `{"repeat": {...}, "steps": [{"command": "sketch.line"...}, {"command": "sketch.arc.three_point"...}]}`.
7. **Evaluation order.** The spec says rules run after lookups and a var may use lookups; it does not say where `defaults` sit. Assumed:
   parse, `defaults` (fields only), lookups, vars, rules, steps. Please state it; constant lookups (`params`) rely on `defaults` being
   usable as lookup keys. A direct constant key (`"key": {"name": {"const": "plan"}}`) would be clearer.
8. **Command allow-list.** The steps use `browser.visibility` (hide the construction sketch), `component.metadata.set` and
   `document.metadata.set` (part number, description, material). Are they allowed? Also: `insert` creates the component; the evaluator
   emits `component.create` from `insert.component` as the first command: confirm that is the command it maps to.
9. **Row status vs column status.** `status` is per row, but a profile row mixes labelled numbers (mouth 6), measured ones (d0) and an
   approximate one (tip round). Wanted: optional per-column status, or a `status` that may list columns (`"measured:d0,floor_half"`).
10. **Guarantee evidence.** `guarantee` is a label the index verifies; there is nowhere to put what it was verified from (reviewer kind,
    date, sources hash). Kept under `x-generator`. Wanted: a `review` object next to `guarantee`.
11. **`checks`.** `volume_mm3` / `bbox_mm` / `faces` can only be produced by running SolidCraft; we record them with
    `tools/package-equiv --build --record`. Please say how `faces` is counted (we use the length of `model.faces`) and the default
    tolerances for the box.
12. **Small things.** The `decimal` `step` is taken relative to `min`; `chars` takes at most `max_len` characters and needs at least
    `min_len`; `flags` options are matched longest first and `max` counts options given; `{code}` in `grammar.refuse` is the code as typed;
    `x-` keys are accepted at the top level only (the schema closes every inner object), so `x-early-rules` and `x-generator` live there.
