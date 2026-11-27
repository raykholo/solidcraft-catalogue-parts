# hiwin.hg.guideway as a parametric generator (SolidCraft 0.50.0)

The HG guideway (HIWIN Linear Guideway catalogue G99TE24-2410, HG series, section 2-1) in the new generator form of issue tangency-labs/solidcraft#22331: ONE parametric `.sc` modelled once, a configuration table of the catalogue rows, field templates for the ordering code and `generator.rhai`. Every code of `codes.txt` is built both ways (this package and the Python generator) and compared by `tools/parametric-verdict`.

Result of the CI run: **9/9 valid codes identical** (volume, area, bbox, faces, bodies), **5/5 refusals with the Python message word for word**, spec check (`src/check.py`) with the same pass count on both parts for 9/9 codes. The table below is the harness' own output.

## Layout

```
parametric/
  hg-guideway/                  the package (docs/formats/generator.md, "Generators: interface (version 2)")
    generator.toml          [parameters], four [[template]] (rail, set, block, raw refusal), [rows.*] provenance (generated from ../data/*.csv)
    hg-guideway.sc          the parametric model + configuration table + rules (built by gw_build.py)
    generator.rhai          resolve(fields), describe(fields): plain Rhai with table() and refuse()
    tables/                 rails.csv, blocks.csv, params.csv (the catalogue rows, with source / page / status)
  package.toml.head         the hand-written head of generator.toml
  ci.sh OUTDIR              build the model, run every code both ways, write OUTDIR/faithfulness.json (tools/parametric-verdict)
../../guideway-parametric/   what the EG, HG and RG generators share: gw_model.py (the model as a command list), gw_package.py, gw_build.py,
                            gw_harness.py / gw_faith.py / gw_stub.py delegate to runtime/parametric/; gw_parity.py tests Rhai
```

Commands, from the repository root (`SC_CLI` = solidcraft-cli 0.50.0, `RHAI_RUN` = `runtime/rhai-run` built with cargo):

```
bash vendors/hiwin/hg/guideway/parametric/ci.sh out        # build + every code both ways + out/faithfulness.json
tools/parametric-verdict out/faithfulness.json                     # the verdict
python3 vendors/hiwin/guideway-parametric/gw_parity.py HG 3000   # no SolidCraft: Python parse vs template + Rhai on codes.txt and 3000 generated codes
```

## What the design is

- **Scope.** HGH and HGW blocks, load C or H, mounting A and C (tapped) or B (through, HGW only). Sizes 15 to 65. HGR rails mounted from the top (R, counterbored) or from the bottom (T, tapped): both are drawn, the mounting is part of the row (`-R` / `-T`) and switches the hole feature. HGL (low square) is refused (not drawn).
- **User parameters.** Row-driven (configuration columns): `size rail WR HR D h d P Es Elo minlen maxlen W H H1 L1 L B C Mdepth hole_d hT tap`, one value per catalogue row. Free: `length`, `blocks` (columns too, so the rules range-check them and the row holds the defaults: 400 mm, 1 block). Derived: `n = floor((length - 2 * Elo + 0.000001 mm) / P) + 1` holes, `E = (length - (n - 1) * P) / 2` the end distance, `x0` the start of the first block. `gap` (10 mm) is the illustration choice the Python generator also has.
- **Rail.** `solid.box length=length width=WR height=HR`, a counterbore `solid.hole` at `x = E` from the top or a tapped hole of the size's thread from the bottom (one feature per thread designation), and a feature pattern with `count1 = n`, `spacing1 = P`: the hole count follows `length`.
- **Blocks.** A U-profile sketch (the rail channel cut in, every coordinate an expression) extruded over `L1`, the mounting holes of the row, and a feature pattern of the block and its holes with `count1 = blocks`, `spacing1 = L + gap` (centred on the rail through `x0`).
- **Rows: 196**, three products of the catalogue rows. 120 rail-with-blocks rows `<block>-<size>-<R|T>` (e.g. `HGH-CA-15-R`), 60 block-alone rows `<block>-<size>-block` (rail features suppressed, `rail = 0` puts the block at x = 0 as the Python part does), 16 rail-alone rows (`HGR-15-R`: block features suppressed).
- **Suppression columns** (20 features): per row, the hole alternatives that do not apply are suppressed. Block holes: `Block threads M4`, `Block threads M5`, `Block threads M6`, `Block threads M8`, `Block threads M10`, `Block threads M12`, `Block threads M14`, `Block threads M16`, `Block through holes`. Rail holes: counterbore `Rail hole 1` or the tap of the size (M5, M6, M8, M12, M14, M20). The thread designation is not a parameter in 0.50.0, hence one feature per designation.
- **Rules (`config.rule`).** `length` within the catalogue minimum and the largest single rail (columns `minlen`, `maxlen`); `blocks` from 1 to the number that fits (`floor((length + gap) / (L + gap))`, the Python refusal "do not fit"). Checked when a row is activated (0.50.0): see "Where the limits apply".
- **Templates.** Rail, set, block, then a raw refusal catcher (`generator.toml`). Size (two digits), block kind, load, mounting, `E` flags, number of blocks, rail mounting, `length` (decimal), preload, accuracy, material, rails and a `+` option tail are fields; everything the catalogue refuses is refused in `generator.rhai` so that the message is the Python generator's, in the same order.
- **Dimensioned geometry only:** no appearance bodies (chamfers, grooves, end caps and seals, nipple, screws, looks). The Python generator is run with `appearance=False` for the comparison (`build.commands(s, appearance=False)`, `check.check(..., appearance=False)`); the default output of both is unchanged.

## Documented deviations from the Python generator

- Separators (space, `-`, `_`, `/`, `.`) inside a code are ignored by the field-template engine by design; the Python regular expressions allow optional spaces only. A code with extra separators is accepted here where Python may refuse it (not in the reject battery).
- Generic shape refusals use a final `{raw: ...}` catch-all template, and the shared host passes the typed code as `raw_code` to Rhai. The message retains decimal spelling such as `1000.0`; the reject battery includes one such case per series. Accepted codes still use the original rail, set and block templates.
- `U` for the top-mounted rail (EG) and the `E` flags are parsed like Python (modelled as standard).

## Side by side: every code of codes.txt

Measures: volume mm3 / area mm2 / faces / bodies (the bbox is compared too). `spec` = the generator's own `src/check.py` rows passed, on the parametric part and on the Python part (appearance off); the row `Block i length L` (the catalogue length WITH end caps and seals) cannot pass without the appearance bodies on either part.

| code | Python | parametric | spec (parametric / Python) | identical |
|---|---|---|---|---|
| HGH20CA2R1000ZAH | 421586.14 / 102631.62 / 93f 3b | 421586.14 / 102631.62 / 93f 3b | 35/37 / 35/37 | yes |
| HGH65HA1R1270 | 5488695.73 / 443638.94 / 51f 2b | 5488695.73 / 443638.94 / 51f 2b | 26/27 / 26/27 | yes |
| HGR15R160M | 34834.74 / 10740.60 / 15f 1b | 34834.74 / 10740.60 / 15f 1b | 16/16 / 16/16 | yes |
| HGR20R1000 | 335431.55 / 81935.28 / 57f 1b | 335431.55 / 81935.28 / 57f 1b | 16/16 / 16/16 | yes |
| HGR25T640 | 321248.19 / 60685.45 / 28f 1b | 321248.19 / 60685.45 / 28f 1b | 15/15 / 15/15 | yes |
| HGW20HB2R820ZBC | 444279.99 / 102500.61 / 76f 3b | 444279.99 / 102500.61 / 76f 3b | 28/30 / 28/30 | yes |
| HGW25CC1R640ZAP | 409585.29 / 82097.88 / 57f 2b | 409585.29 / 82097.88 / 57f 2b | 26/27 / 26/27 | yes |
| HGW30CA1R445ZAH | 493203.28 / 81002.28 / 42f 2b | 493203.28 / 81002.28 / 42f 2b | 26/27 / 26/27 | yes |
| HGW45CB | 444220.80 / 54381.35 / 14f 1b | 444220.80 / 54381.35 / 14f 1b | 10/11 / 10/11 | yes |
| !HGH15HA2R200 | HGH15HA is not in the catalogue table (HG15 has the heavy load C block only) | REFUSED: HGH15HA is not in the catalogue table (HG15 has the heavy load C block only) | - | same message |
| !HGW20HC1R500 | rail length 500 leaves end distance 40.00 mm, above P/2 = 30 mm (unstable rail end, p.37) | REFUSED: rail length 500 leaves end distance 40.00 mm, above P/2 = 30 mm (unstable rail end, p.37) | - | same message |
| !HGH20CA1R10 | rail length 10 mm below 2 x Es = 40 mm | REFUSED: rail length 10 mm below 2 x Es = 40 mm | - | same message |
| !HGR15R5000 | rail length 5000 mm above the maximum 4000 mm | REFUSED: rail length 5000 mm above the maximum 4000 mm | - | same message |
| !HGH20CB | HGH is mounted from the top only: HGH20CA (the catalogue lists HGH-CA / HGH-HA) | REFUSED: HGH is mounted from the top only: HGH20CA (the catalogue lists HGH-CA / HGH-HA) | - | same message |

## Rebuild on a free parameter change

A free parameter changed on a built part (`parameters.change` on the instance) against the code built directly, both as a fresh parametric instance and as the Python part:

- HGH20CA2R1000ZAH length 1000 -> 1240 vs HGH20CA2R1240ZAH: equals the fresh instance **True**, equals the Python part **True** (502158.27 / 122098.74 / 105f 3b)
- HGW25CC1R640ZAP blocks 1 -> 2 vs HGW25CC2R640ZAP: equals the fresh instance **True**, equals the Python part **True** (510242.15 / 99864.49 / 75f 3b)
- HGW25CC1T640ZAP length 640 -> 760 (rail mounted from the bottom) vs HGW25CC1T760ZAP: equals the fresh instance **True**, equals the Python part **True** (482153.81 / 89629.05 / 50f 2b)

## What 0.50.0 does with a link, and where the limits apply (measured)

- insert_design configuration=HGH-CA-20-R: ok
- row HGH-CA-20-R inserted == Python HGH20CA1R400: True; python 177078.52 / 43615.64 / [0.000..400.000] x [-22.000..22.000] x [0.000..30.000] / 45f 2b; inserted 177078.52 / 43615.64 / [0.000..400.000] x [-22.000..22.000] x [0.000..30.000] / 45f 2b
- insert_design configuration=HGH-CA-20-R parameters={length: 800 mm}: accepted, rail x extent is 400.0 (400 = the parameters key is ignored)
- component.set_link_parameters: {"command": "component.set_link_parameters", "error": "unknown command `component.set_link_parameters`", "step": 2}
- parameters.change length in the assembly that holds the link: {"command": "parameters.change", "error": "unknown parameter `length`", "step": 2}
- insert_design configuration=nope: {"command": "component.insert_design", "error": "invalid parameters for `component.insert_design`: configuration `nope` does not exist in the source design", "step": 1}

- ordinary edit: length 9000 mm (max 4000): accepted: {"changed": {"length": 9000.0}, "errors": [], "recomputed": 15, "restored": 0}
- ordinary edit: blocks 40 on a 400 mm rail: accepted: {"changed": {"blocks": 40.0}, "errors": [], "recomputed": 5, "restored": 0}
- row with length 9000 mm, config.activate: REFUSED {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `Rail length: the catalogue minimum and the largest single rail` restricts the final value", "step": 1}
- row with 40 blocks on 400 mm, config.activate: REFUSED {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `Blocks that fit on the rail with the gap between them` restricts the final value", "step": 1}
- row with length 30 mm, config.activate: REFUSED {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `Rail length: the catalogue minimum and the largest single rail` restricts the final value", "step": 1}

## SolidCraft 0.50.0 observations and draft dependencies

| Wanted | Result on 0.50.0 | Workaround used (labelled) |
|---|---|---|
| Free parameter values on insert: needs #23175 (our draft, being finished) | `component.insert_design` accepts a `parameters` key and ignores it silently; `component.set_link_parameters` is unknown (see the measured lines above) | the instance file: `config.activate` + `parameters.change` on a copy of the model, which is then the file that gets inserted |
| Thread designation from a parameter | `thread: "M5"` is a literal | one hole feature per designation (M4, M5, M6, M8, M10, M12, M14, M16, M5, M6, M8, M12, M14, M20 on the rail), the row suppresses all but its own |
| Names of pattern copies | the copies of a feature pattern are named `Body<N>` | the harness renames them `Block 1..n` by position before `src/check.py` reads them |

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai and rules by feature name needs #23175 (our draft, being finished). Historical 0.50.0 errors above remain quoted verbatim. The draft checks link overrides against source range rules; ordinary source `parameters.change` still does not enforce restrictions. Parameter-driven thread designations and named pattern copies remain follow-ups outside #23175.

The optional link proof in `link_checks.json` runs through `runtime.parametric.links` after the legacy conversion. Only a command catalogue containing `component.set_link_parameters` enables its insertion, link-edit and out-of-range refusal rows. Unsupported builds retain the legacy faithfulness rows and dependency item.
