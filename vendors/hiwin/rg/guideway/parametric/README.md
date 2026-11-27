# hiwin.rg.guideway as a parametric generator (SolidCraft 0.50.0)

The RG roller guideway (HIWIN Linear Guideway catalogue G99TE24-2410, RG series, section 2-9) in the new generator form of issue tangency-labs/solidcraft#22331: ONE parametric `.sc` modelled once, a configuration table of the catalogue rows, field templates for the ordering code and `generator.rhai`. Every code of `codes.txt` is built both ways (this package and the Python generator) and compared by `tools/parametric-verdict`.

Result of the CI run: **29/29 valid codes identical** (volume, area, bbox, faces, bodies), **16/16 refusals with the Python message word for word**, spec check (`src/check.py`) with the same pass count on both parts for 29/29 codes. The table below is the harness' own output.

## Layout

```
parametric/
  rg-guideway/                  the package (docs/formats/generator.md, "Generators: interface (version 2)")
    generator.toml          [parameters], three [[template]] (rail, set, block), [rows.*] provenance (generated from ../data/*.csv)
    rg-guideway.sc          the parametric model + configuration table + rules (built by gw_build.py)
    generator.rhai          resolve(fields), describe(fields): plain Rhai with table() and refuse()
    tables/                 rails.csv, blocks.csv, dust.csv, params.csv (the catalogue rows, with source / page / status)
  package.toml.head         the hand-written head of generator.toml
  ci.sh OUTDIR              build the model, run every code both ways, write OUTDIR/faithfulness.json (tools/parametric-verdict)
../../guideway-parametric/   what the EG, HG and RG generators share: gw_model.py (the model as a command list), gw_package.py, gw_build.py,
                            gw_harness.py (codes both ways), gw_faith.py, gw_stub.py (template + Rhai host), gw_parity.py (local Rhai test)
```

Commands, from the repository root (`SC_CLI` = solidcraft-cli 0.50.0, `RHAI_RUN` = `runtime/rhai-run` built with cargo):

```
bash vendors/hiwin/rg/guideway/parametric/ci.sh out        # build + every code both ways + out/faithfulness.json
tools/parametric-verdict out/faithfulness.json                     # the verdict
python3 vendors/hiwin/guideway-parametric/gw_parity.py RG 3000   # no SolidCraft: Python parse vs template + Rhai on codes.txt and 3000 generated codes
```

## What the design is

- **Scope.** RGH (mounting A) and RGW (mounting C) blocks, load C or H, six tapped holes (four on C x B, two on the rail axis: C1 apart on RGW, C apart on RGH). Sizes 15 to 65. RGR rails mounted from the top (R); T is refused (no tapped-hole dimensions in the catalogue). A dust-protection code (+ZZ, +DD, +KK) replaces the block length L (Table 2-9-22): the answer of the Rhai script carries it as the parameter `L`. RGL, RGS and RGF are refused (not drawn).
- **User parameters.** Row-driven (configuration columns): `size rail WR HR D h d P Es Elo minlen maxlen W H H1 L1 L B C Mdepth hole_d C1`, one value per catalogue row. Free: `length`, `blocks` (columns too, so the rules range-check them and the row holds the defaults: 400 mm, 1 block). Derived: `n = floor((length - 2 * Elo + 0.000001 mm) / P) + 1` holes, `E = (length - (n - 1) * P) / 2` the end distance, `x0` the start of the first block. `gap` (10 mm) is the illustration choice the Python generator also has.
- **Rail.** `solid.box length=length width=WR height=HR`, a counterbore `solid.hole` at `x = E` from the top, and a feature pattern with `count1 = n`, `spacing1 = P`: the hole count follows `length`.
- **Blocks.** A U-profile sketch (the rail channel cut in, every coordinate an expression) extruded over `L1`, the mounting holes of the row, and a feature pattern of the block and its holes with `count1 = blocks`, `spacing1 = L + gap` (centred on the rail through `x0`).
- **Rows: 68**, three products of the catalogue rows. 30 rail-with-blocks rows `<block>-<size>` (e.g. `RGH-CA-15`), 30 block-alone rows `<block>-<size>-block` (rail features suppressed, `rail = 0` puts the block at x = 0 as the Python part does), 8 rail-alone rows (`RGR-15`: block features suppressed).
- **Suppression columns** (13 features): per row, the hole alternatives that do not apply are suppressed. Block holes: `Block threads M4`, `Block threads M5`, `Block threads M6`, `Block threads M8`, `Block threads M10`, `Block threads M12`, `Block threads M14`, `Block threads M16`. The thread designation is not a parameter in 0.50.0, hence one feature per designation.
- **Rules (`config.rule`).** `length` within the catalogue minimum and the largest single rail (columns `minlen`, `maxlen`); `blocks` from 1 to the number that fits (`floor((length + gap) / (L + gap))`, the Python refusal "do not fit"). Checked when a row is activated (0.50.0): see "Where the limits apply".
- **Templates.** Three, tried in order: rail, set, block (`generator.toml`). Size (two digits), block kind, load, mounting, `E` flags, number of blocks, rail mounting, `length` (decimal), preload, accuracy, material, rails and a `+` option tail are fields; everything the catalogue refuses is refused in `generator.rhai` so that the message is the Python generator's, in the same order.
- **Dimensioned geometry only:** no appearance bodies (chamfers, grooves, end caps and seals, nipple, screws, looks). The Python generator is run with `appearance=False` for the comparison (`build.commands(s, appearance=False)`, `check.check(..., appearance=False)`); the default output of both is unchanged.

## Documented deviations from the Python generator

- Separators (space, `-`, `_`, `/`, `.`) inside a code are ignored by the field-template engine by design; the Python regular expressions allow optional spaces only. A code with extra separators is accepted here where Python may refuse it (not in the reject battery).
- The generic refusal of a code that no Python regular expression accepts quotes the code (`'EGW25CAZB': expected a set ...`). Rhai does not see the typed text, only the fields, so it quotes the canonical spelling (upper case, no separators, the length without a trailing `.0`). Identical for every code of `codes.txt`; it differs only for a code typed with separators, lower case or a decimal length such as `1000.0`.
- `U` for the top-mounted rail (EG) and the `E` flags are parsed like Python (modelled as standard).

## Side by side: every code of codes.txt

Measures: volume mm3 / area mm2 / faces / bodies (the bbox is compared too). `spec` = the generator's own `src/check.py` rows passed, on the parametric part and on the Python part (appearance off); the row `Block i length L` (the catalogue length WITH end caps and seals) cannot pass without the appearance bodies on either part.

| code | Python | parametric | spec (parametric / Python) | identical |
|---|---|---|---|---|
| RGH15CA1R340ZAP | 107362.52 / 32821.56 / 61f 2b | 107362.52 / 32821.56 / 61f 2b | 27/28 / 27/28 | yes |
| RGH20HA2R1000ZAH | 535304.36 / 129801.58 / 149f 3b | 535304.36 / 129801.58 / 149f 3b | 37/39 / 37/39 | yes |
| RGH25CA1R640Z0H | 396649.55 / 88601.89 / 91f 2b | 396649.55 / 88601.89 / 91f 2b | 27/28 / 27/28 | yes |
| RGH30HA1R1000ZBP | 870524.68 / 162127.33 / 103f 2b | 870524.68 / 162127.33 / 103f 2b | 27/28 / 27/28 | yes |
| RGH35CA2R840ZAUP | 1203269.08 / 187495.91 / 113f 3b | 1203269.08 / 187495.91 / 113f 3b | 37/39 / 37/39 | yes |
| RGH45HA1R885ZBSP | 1918497.70 / 239412.75 / 79f 2b | 1918497.70 / 239412.75 / 79f 2b | 27/28 / 27/28 | yes |
| RGH55CA1R780ZAP | 2291555.14 / 250320.65 / 67f 2b | 2291555.14 / 250320.65 / 67f 2b | 27/28 / 27/28 | yes |
| RGH65HA1R1270ZAP | 5505019.76 / 482053.92 / 79f 2b | 5505019.76 / 482053.92 / 79f 2b | 27/28 / 27/28 | yes |
| RGH20CA1R340ZAP+ZZ | 186589.78 / 46260.64 / 61f 2b | 186589.78 / 46260.64 / 61f 2b | 27/28 / 27/28 | yes |
| RGH45CA1R570ZAP+KK/E2+RC | 1296696.54 / 164986.59 / 61f 2b | 1296696.54 / 164986.59 / 61f 2b | 27/28 / 27/28 | yes |
| RGW15CC1R160ZAP | 70845.82 / 20985.89 / 43f 2b | 70845.82 / 20985.89 / 43f 2b | 28/29 / 28/29 | yes |
| RGW20HC2R820ZBP | 511230.00 / 118532.33 / 131f 3b | 511230.00 / 118532.33 / 131f 3b | 39/41 / 39/41 | yes |
| RGW25CC2R640ZAH | 535203.56 / 112300.07 / 113f 3b | 535203.56 / 112300.07 / 113f 3b | 39/41 / 39/41 | yes |
| RGW30HC1R760ZAP | 782200.02 / 137192.01 / 85f 2b | 782200.02 / 137192.01 / 85f 2b | 28/29 / 28/29 | yes |
| RGW35CC1R840ZAP | 1059511.26 / 163840.32 / 91f 2b | 1059511.26 / 163840.32 / 91f 2b | 28/29 / 28/29 | yes |
| RGW45HC1R1200ZAP | 2531434.53 / 310326.86 / 97f 2b | 2531434.53 / 310326.86 / 97f 2b | 28/29 / 28/29 | yes |
| RGW55CC1R780ZAP | 2465396.67 / 260775.06 / 67f 2b | 2465396.67 / 260775.06 / 67f 2b | 28/29 / 28/29 | yes |
| RGW65HC1R1270ZAP | 6268508.51 / 509069.71 / 79f 2b | 6268508.51 / 509069.71 / 79f 2b | 28/29 / 28/29 | yes |
| RGW25CC1R640ZAP+DD | 426417.47 / 92345.59 / 91f 2b | 426417.47 / 92345.59 / 91f 2b | 28/29 / 28/29 | yes |
| RGW45CC | 511340.88 / 55322.11 / 22f 1b | 511340.88 / 55322.11 / 22f 1b | 14/15 / 14/15 | yes |
| RGH20CA | 54304.99 / 12780.35 / 22f 1b | 54304.99 / 12780.35 / 22f 1b | 13/14 / 13/14 | yes |
| RGW65HC | 2360651.18 / 156053.66 / 22f 1b | 2360651.18 / 156053.66 / 22f 1b | 14/15 / 14/15 | yes |
| RGW25CCEZAP+ZZ | 108786.09 / 19954.48 / 22f 1b | 108786.09 / 19954.48 / 22f 1b | 14/15 / 14/15 | yes |
| RGR15R160 | 37482.08 / 11850.88 / 21f 1b | 37482.08 / 11850.88 / 21f 1b | 16/16 / 16/16 | yes |
| RGR25R990 | 490605.31 / 111672.54 / 105f 1b | 490605.31 / 111672.54 / 105f 1b | 16/16 / 16/16 | yes |
| RGR35R1000H | 951672.74 / 153332.25 / 81f 1b | 951672.74 / 153332.25 / 81f 1b | 16/16 / 16/16 | yes |
| RGR45R570P | 880392.53 / 116562.83 / 39f 1b | 880392.53 / 116562.83 / 39f 1b | 16/16 / 16/16 | yes |
| RGR55R780 | 1648205.01 / 185225.94 / 45f 1b | 1648205.01 / 185225.94 / 45f 1b | 16/16 / 16/16 | yes |
| RGR65R1270P | 3907857.33 / 353016.05 / 57f 1b | 3907857.33 / 353016.05 / 57f 1b | 16/16 / 16/16 | yes |
| !RGH20CC | RGH is mounted from the top only: RGH20CA (the catalogue lists RGH-CA / RGH-HA) | REFUSED: RGH is mounted from the top only: RGH20CA (the catalogue lists RGH-CA / RGH-HA) | - | same message |
| !RGW20CA | RGW has mounting code C (top or bottom): RGW20CC (the catalogue lists RGW-CC / RGW-HC) | REFUSED: RGW has mounting code C (top or bottom): RGW20CC (the catalogue lists RGW-CC / RGW-HC) | - | same message |
| !RGH15HA | RGH15HA is not in the catalogue table (no row for it: the RG15 tables list the heavy load C block only) | REFUSED: RGH15HA is not in the catalogue table (no row for it: the RG15 tables list the heavy load C block only) | - | same message |
| !RGW15HC1R160 | RGW15HC is not in the catalogue table (no row for it: the RG15 tables list the heavy load C block only) | REFUSED: RGW15HC is not in the catalogue table (no row for it: the RG15 tables list the heavy load C block only) | - | same message |
| !RGR20T640 | RGR rail mounted from the bottom (T) is valid HIWIN grammar, but the catalogue prints no tapped-hole dimensions for it (the rail columns on p.166-170 are the top-mounted R rail), so it is not drawn | REFUSED: RGR rail mounted from the bottom (T) is valid HIWIN grammar, but the catalogue prints no tapped-hole dimensions for it (the rail columns on p.166-170 are the top-mounted R rail), so it is not drawn | - | same message |
| !RGR25R4500 | rail length 4500 mm above the maximum 4000 mm (Table 2-9-29) | REFUSED: rail length 4500 mm above the maximum 4000 mm (Table 2-9-29) | - | same message |
| !RGR25R60 | rail length 60 mm below the catalogue minimum 100 mm (Table 2-9-2) | REFUSED: rail length 60 mm below the catalogue minimum 100 mm (Table 2-9-2) | - | same message |
| !RGR25R1010 | rail length 1010 leaves end distance 25.00 mm, above P/2 = 15 mm and not the standard Es = 20 mm (an unstable rail end, p.165) | REFUSED: rail length 1010 leaves end distance 25.00 mm, above P/2 = 15 mm and not the standard Es = 20 mm (an unstable rail end, p.165) | - | same message |
| !RGR25R995 | rail length 995 leaves end distance 17.50 mm, above P/2 = 15 mm and not the standard Es = 20 mm (an unstable rail end, p.165) | REFUSED: rail length 995 leaves end distance 17.50 mm, above P/2 = 15 mm and not the standard Es = 20 mm (an unstable rail end, p.165) | - | same message |
| !RGR30R1020 | rail length 1020 leaves end distance 30.00 mm, above P/2 = 20 mm and not the standard Es = 20 mm (an unstable rail end, p.165) | REFUSED: rail length 1020 leaves end distance 30.00 mm, above P/2 = 20 mm and not the standard Es = 20 mm (an unstable rail end, p.165) | - | same message |
| !RGW25CCZB | the interchangeable block form has preload Z0 or ZA only (model number, p.152); ZB belongs to a set (non-interchangeable) | REFUSED: the interchangeable block form has preload Z0 or ZA only (model number, p.152); ZB belongs to a set (non-interchangeable) | - | same message |
| !RGR25R640SP | accuracy class SP is not offered for a rail ordered alone (interchangeable rail): the RG series has H, P there (model number, p.152-153) | REFUSED: accuracy class SP is not offered for a rail ordered alone (interchangeable rail): the RG series has H, P there (model number, p.152-153) | - | same message |
| !RGH25CA1R640ZAC | accuracy class C is not offered for a rail with blocks (non-interchangeable set): the RG series has H, P, SP, UP there (model number, p.152-153) | REFUSED: accuracy class C is not offered for a rail with blocks (non-interchangeable set): the RG series has H, P, SP, UP there (model number, p.152-153) | - | same message |
| !RGW35CC2R240 | 2 blocks of 124 mm with 10 mm gaps do not fit on a 240 mm rail | REFUSED: 2 blocks of 124 mm with 10 mm gaps do not fit on a 240 mm rail | - | same message |
| !RGL25CA1R640 | RGL (square, low) is valid HIWIN grammar; its dimension table is not drawn here (RGH and RGW only) | REFUSED: RGL (square, low) is valid HIWIN grammar; its dimension table is not drawn here (RGH and RGW only) | - | same message |
| !RGH20CAM | 'RGH20CAM': expected a set RG<H|W><size><C|H><A|C><n>R<length>[Z0|ZA|ZB][H|P|SP|UP], e.g. RGH20CA2R1000ZAH, a rail RGR<size>R<length>, e.g. RGR25R1240, or a block RGW25CC | REFUSED: 'RGH20CAM': expected a set RG<H|W><size><C|H><A|C><n>R<length>[Z0|ZA|ZB][H|P|SP|UP], e.g. RGH20CA2R1000ZAH, a rail RGR<size>R<length>, e.g. RGR25R1240, or a block RGW25CC | - | same message |

## Rebuild on a free parameter change

A free parameter changed on a built part (`parameters.change` on the instance) against the code built directly, both as a fresh parametric instance and as the Python part:

- RGH20HA2R1000ZAH length 1000 -> 1240 vs RGH20HA2R1240ZAH: equals the fresh instance **True**, equals the Python part **True** (628456.94 / 152943.62 / 173f 3b)
- RGW25CC1R640ZAP blocks 1 -> 2 vs RGW25CC2R640ZAP: equals the fresh instance **True**, equals the Python part **True** (535203.56 / 112300.07 / 113f 3b)

## What 0.50.0 does with a link, and where the limits apply (measured)

- insert_design configuration=RGH-CA-20: ok
- row RGH-CA-20 inserted == Python RGH20CA1R400: True; python 209877.93 / 52046.15 / [0.000..400.000] x [-22.000..22.000] x [0.000..34.000] / 67f 2b; inserted 209877.93 / 52046.15 / [0.000..400.000] x [-22.000..22.000] x [0.000..34.000] / 67f 2b
- insert_design configuration=RGH-CA-20 parameters={length: 800 mm}: accepted, rail x extent is 400.0 (400 = the parameters key is ignored)
- component.set_link_parameters: {"command": "component.set_link_parameters", "error": "unknown command `component.set_link_parameters`", "step": 2}
- parameters.change length in the assembly that holds the link: {"command": "parameters.change", "error": "unknown parameter `length`", "step": 2}
- insert_design configuration=nope: {"command": "component.insert_design", "error": "invalid parameters for `component.insert_design`: configuration `nope` does not exist in the source design", "step": 1}

- ordinary edit: length 9000 mm (max 4000): accepted: {"changed": {"length": 9000.0}, "errors": [], "recomputed": 9, "restored": 0}
- ordinary edit: blocks 40 on a 400 mm rail: accepted: {"changed": {"blocks": 40.0}, "errors": [], "recomputed": 5, "restored": 0}
- row with length 9000 mm, config.activate: REFUSED {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `Rail length: the catalogue minimum and the largest single rail` restricts the final value", "step": 1}
- row with 40 blocks on 400 mm, config.activate: REFUSED {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `Blocks that fit on the rail with the gap between them` restricts the final value", "step": 1}
- row with length 30 mm, config.activate: REFUSED {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `Rail length: the catalogue minimum and the largest single rail` restricts the final value", "step": 1}

## What 0.50.0 could not express (the `blocked` list of faithfulness.json)

| Wanted | Result on 0.50.0 | Workaround used (labelled) |
|---|---|---|
| Free parameter values on insert | `component.insert_design` accepts a `parameters` key and ignores it silently; `component.set_link_parameters` is unknown (see the measured lines above) | the instance file: `config.activate` + `parameters.change` on a copy of the model, which is then the file that gets inserted |
| Thread designation from a parameter | `thread: "M5"` is a literal | one hole feature per designation (M4, M5, M6, M8, M10, M12, M14, M16), the row suppresses all but its own |
| Names of pattern copies | the copies of a feature pattern are named `Body<N>` | the harness renames them `Block 1..n` by position before `src/check.py` reads them |

What SolidCraft needs (proposals): `component.insert_design {parameters}` stored and applied, `component.set_link_parameters`; `solid.pattern.rectangular {body_names}`; a thread designation that can come from a parameter or a choice; rules by feature name; range rules enforced on `parameters.change` with an opt-in. See tangency-labs/solidcraft#23175.
