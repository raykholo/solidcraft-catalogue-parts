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
| `runtime/package.py` | the evaluator (and `x-lists`): grammar tokens, defaults, lookups, vars, rules, steps with `when` / `repeat`, `${}` substitution, checks, limits; plus `validate()` (schema, expression names and order, RFC 0019 examples, steps) |
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

Only for `hiwin.mg.rail-set` (the sweep of `tools/package-equiv` stays inside what is not listed here):

7. Several spaces, tabs and leading or trailing blanks between the parts of an MGN code are not read (one optional space per gap is); the
   part is named with the code as typed, so a code with one space per gap and no `caps` keeps its spaces in the name, as the Python one does.
8. The free-text tail `+ SS/U/EL+RC/-O` (HIWIN's own options, ignored by the Python generator) is refused: the grammar has no token for
   arbitrary text (spec gap 18).
9. The package draws 1 to 4 blocks (`n_blocks` rule; the Python generator takes any number, its `[inputs]` say 1 to 4, and builds a rail alone
   for 0), and refuses a rail shorter than two end distances (the Python generator builds a rail with no hole and a hole sketch beyond the
   rail end; `holes_for` accepts it). Both look like gaps of the Python generator: the package states what the manifest already says.
10. The build option `caps` of `codes.txt` (bolt caps in the rail holes, no symbol in the HIWIN model number) is the trailing word ` caps` of
    the package code (`runtime/package_export/hiwin_mg_rail_set.py` `code_with_options`; `tools/package-equiv` and the export hand the package
    that text). With it the part is named by the fields (`concat`), because the typed text would include the word (spec gap 16).

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

Found with `hiwin.mg.rail-set` (the rail with N blocks). Gaps 1 to 12 above were met again where the MG generator needed them: 3 (number
to text), 4 (blank Gn / G cells as 0), 6 (a block of about 40 steps copied four times under `when n_blocks > i`; 175 of the 256 steps, at
most 261 of the 512 commands), 7 (the order the lookups need), 8 (the allow-list now also needs `appearance.assign`, `material.assign` and
`parts.insert`; `package.validate()` notes each), 9 (per-column status: the derived `cap_d` / `cap_h` / `bolt_*` columns share the row's
`labelled`), 11 (`faces`). New:

13. **Lists built by a loop. NEW, `x-lists`, implemented.** `parts.insert` takes all screw positions as one `at` array and `material.assign`
    takes all cap body names as one `bodies` array; their length is the hole count (up to 80). `repeat` emits one command per index, so it
    cannot build an array parameter, the expression language has no list literal or `map`, and a table cannot hold a length that depends on
    the typed rail length. Wanted: a list-valued `repeat` in a template, or `range(n)` plus `map`. Used (top level, the evaluator runs it
    after the rules, the result is a variable): `"x-lists": [{"name": "screw_at", "repeat": {"var": "j", "count": "holes", "max": 128},
    "each": ["${end_d + j * r.P + r.d / 2}", 0, "${r.HR - r.h - 0.5}"]}]` and then `"at": "${screw_at}"`.
14. **Round to n digits. NEW.** `round(x)` is whole numbers only; the Python generator rounds its estimated sizes with `round(x, 2)` / `round(x, 3)`
    (half to even, so `round(0.5625, 3)` is 0.562). Expressed in the format with two variables per value (`t = x * 1000`, then floor and the
    half-even test, nine times). Wanted: `round(x, digits)` with the rule written down (half to even or half up: the two differ here).
15. **Split text, text to number. NEW.** The table cell `M3x8` gives the screw size `M3` and the length 8; there is no `split`, `substr` or
    `num(text)`. Worked around with derived columns `bolt_m`, `bolt_len` next to `bolt` (same row, split by the exporter). Wanted:
    `at(split(r.bolt, "x"), 0)` and `num(text)`.
16. **Options beside the code. NEW.** A generator may take a build option that is not part of the ordering code (here `caps`). The package has the
    code only, so it is a trailing optional token of the grammar (`{"optional": [{"lit": " "}, {"field": "caps", "enum": ["caps"]}], "default": {"caps": ""}}`),
    and because `code_in` then contains the word, the part name needs "the code without that token": Used `caps == "" ? code_in : concat(<fields>)`.
    Wanted: `inputs` (name, type, default) next to the grammar, or a way to name the text a group of tokens matched (`"capture": "base"`).
17. **Grammar: whitespace, optional groups with defaults, backtracking. NEW.** (a) The MGN code allows blanks between every part, which is
    an optional-space token before each of 12 tokens; wanted `{"ws": true}`. (b) An alternative that has no `optional` for a field has no value
    for it; a zero-length `chars` token (`{"field": "precision", "chars": "digits", "min_len": 0, "max_len": 0}`) was used to set it to "". Wanted:
    `"defaults"` on the grammar, or say that a `default` outside `optional` is allowed. (c) The tokens are greedy with no backtracking: the
    precision letter `H` and the material `HC` are both prefixes of `HC`; solved with two alternatives (one with, one without the precision).
    Please state that alternatives are tried in order and each must consume the whole code (the evaluator does that).
18. **Free text token. NEW.** `+ SS/U/EL+RC/-O` is "the rest of the code, any characters"; `chars` only has `digits` / `alpha` / `alnum`.
    Wanted `{"field": "options", "chars": "any", "min_len": 0}` (or `rest`). Not expressed: the package refuses a code with that tail.
19. **Newline in a text.** An expression string literal has no escape for a newline (`\n` reads as `n` in our tokenizer, since the spec says
    a backslash quotes the next character). The description has two paragraph breaks; they are a real line feed inside the literal in the JSON
    (`"concat(\"...\n...\")"`, JSON-escaped). Wanted: `\n` in string literals, or say that a raw newline is allowed. (Unlisted before: NEW.)
20. **512 characters per expression.** The part description is about 2,000 characters; it is built as 6 variables of at most 460 characters and one
    `concat` of them. Wanted: raise the limit for `concat`, or a `text` var type that is a list of parts. (NEW, workaround in the format.)
