# hiwin.eg.guideway as a parametric generator (SolidCraft 0.50.0)

The EG low-profile guideway (HIWIN Linear Guideway catalogue G99TE24-2410, EG series, section 2-2) in the new generator form of issue tangency-labs/solidcraft#22331: ONE parametric `.sc` modelled once, a configuration table of the catalogue rows, field templates for the ordering code and `generator.rhai`. Every code of `codes.txt` is built both ways (this package and the Python generator) and compared by `tools/parametric-verdict`.

Result of the CI run: **21/21 valid codes identical** (volume, area, bbox, faces, bodies), **9/9 refusals with the Python message word for word**, spec check (`src/check.py`) with the same pass count on both parts for 21/21 codes. The table below is the harness' own output.

## Layout

```
parametric/
  eg-guideway/                  the package (docs/formats/generator.md, "Generators: interface (version 2)")
    generator.toml          [parameters], three [[template]] (rail, set, block), [rows.*] provenance (generated from ../data/*.csv)
    eg-guideway.sc          the parametric model + configuration table + rules (built by gw_build.py)
    generator.rhai          resolve(fields), describe(fields): plain Rhai with table() and refuse()
    tables/                 rails.csv, blocks.csv, params.csv (the catalogue rows, with source / page / status)
  package.toml.head         the hand-written head of generator.toml
  ci.sh OUTDIR              build the model, run every code both ways, write OUTDIR/faithfulness.json (tools/parametric-verdict)
../../guideway-parametric/   what the EG, HG and RG generators share: gw_model.py (the model as a command list), gw_package.py, gw_build.py,
                            gw_harness.py (codes both ways), gw_faith.py, gw_stub.py (template + Rhai host), gw_parity.py (local Rhai test)
```

Commands, from the repository root (`SC_CLI` = solidcraft-cli 0.50.0, `RHAI_RUN` = `runtime/rhai-run` built with cargo):

```
bash vendors/hiwin/eg/guideway/parametric/ci.sh out        # build + every code both ways + out/faithfulness.json
tools/parametric-verdict out/faithfulness.json                     # the verdict
python3 vendors/hiwin/guideway-parametric/gw_parity.py EG 3000   # no SolidCraft: Python parse vs template + Rhai on codes.txt and 3000 generated codes
```

## What the design is

- **Scope.** EGH and EGW blocks, load S (short, two holes) or C (long, four holes), mounting A (tapped) or B (through, EGW only). Sizes 15 to 35. EGR rails, mounted from the top (R, or U: the same); the bottom-mounted T rail is refused (the catalogue prints no tapped-hole dimensions). The short S block has one column of two holes: the second hole column is a suppression column of the row. The dust-protection codes ZZ, DD, KK are refused (not drawn).
- **User parameters.** Row-driven (configuration columns): `size rail WR HR D h d P Es Elo minlen maxlen W H H1 L1 L B C Mdepth hole_d`, one value per catalogue row. Free: `length`, `blocks` (columns too, so the rules range-check them and the row holds the defaults: 400 mm, 1 block). Derived: `n = floor((length - 2 * Elo + 0.000001 mm) / P) + 1` holes, `E = (length - (n - 1) * P) / 2` the end distance, `x0` the start of the first block. `gap` (10 mm) is the illustration choice the Python generator also has.
- **Rail.** `solid.box length=length width=WR height=HR`, a counterbore `solid.hole` at `x = E` from the top, and a feature pattern with `count1 = n`, `spacing1 = P`: the hole count follows `length`.
- **Blocks.** A U-profile sketch (the rail channel cut in, every coordinate an expression) extruded over `L1`, the mounting holes of the row, and a feature pattern of the block and its holes with `count1 = blocks`, `spacing1 = L + gap` (centred on the rail through `x0`).
- **Rows: 65**, three products of the catalogue rows. 30 rail-with-blocks rows `<block>-<size>` (e.g. `EGH-SA-15`), 30 block-alone rows `<block>-<size>-block` (rail features suppressed, `rail = 0` puts the block at x = 0 as the Python part does), 5 rail-alone rows (`EGR-15`: block features suppressed).
- **Suppression columns** (17 features): per row, the hole alternatives that do not apply are suppressed. Block holes: `Block threads M4 col 1`, `Block threads M5 col 1`, `Block threads M6 col 1`, `Block threads M8 col 1`, `Block threads M10 col 1`, `Block through holes col 1`, `Block threads M4 col 2`, `Block threads M5 col 2`, `Block threads M6 col 2`, `Block threads M8 col 2`, `Block threads M10 col 2`, `Block through holes col 2`. The thread designation is not a parameter in 0.50.0, hence one feature per designation.
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
| EGH15SA1R280ZAC | 63919.65 / 20594.43 / 35f 2b | 63919.65 / 20594.43 / 35f 2b | 26/27 / 26/27 | yes |
| EGH15CA1R280ZBP | 72885.11 / 22772.94 / 39f 2b | 72885.11 / 22772.94 / 39f 2b | 26/27 / 26/27 | yes |
| EGH20CA2R1000ZAH | 366227.83 / 95030.69 / 93f 3b | 366227.83 / 95030.69 / 93f 3b | 35/37 / 35/37 | yes |
| EGH25SA2R460ZBP | 250764.87 / 58619.24 / 58f 3b | 250764.87 / 58619.24 / 58f 3b | 35/37 / 35/37 | yes |
| EGH30CA1R640Z0C | 508339.74 / 89761.81 / 48f 2b | 508339.74 / 89761.81 / 48f 2b | 26/27 / 26/27 | yes |
| EGH35CA1R840ZAP | 910752.23 / 138766.27 / 57f 2b | 910752.23 / 138766.27 / 57f 2b | 26/27 / 26/27 | yes |
| EGW15CB1R160 | 63728.05 / 18727.30 / 29f 2b | 63728.05 / 18727.30 / 29f 2b | 24/25 / 24/25 | yes |
| EGW20SA1R220ZAC | 96855.44 / 25241.24 / 32f 2b | 96855.44 / 25241.24 / 32f 2b | 26/27 / 26/27 | yes |
| EGW25CA2R640ZAP | 443672.74 / 91881.43 / 75f 3b | 443672.74 / 91881.43 / 75f 3b | 35/37 / 35/37 | yes |
| EGW25SB1R340 | 189946.35 / 43389.42 / 36f 2b | 189946.35 / 43389.42 / 36f 2b | 24/25 / 24/25 | yes |
| EGW30CA1R760ZAH | 650281.92 / 108933.95 / 54f 2b | 650281.92 / 108933.95 / 54f 2b | 26/27 / 26/27 | yes |
| EGW35CB2R1000ZBH | 1369020.08 / 203573.79 / 73f 3b | 1369020.08 / 203573.79 / 73f 3b | 28/30 / 28/30 | yes |
| EGW35SA | 140120.10 / 20627.07 / 14f 1b | 140120.10 / 20627.07 / 14f 1b | 12/13 / 12/13 | yes |
| EGW15CBZAP | 34340.66 / 9091.66 / 14f 1b | 34340.66 / 9091.66 / 14f 1b | 10/11 / 10/11 | yes |
| EGH20CA | 34917.48 / 8908.15 / 18f 1b | 34917.48 / 8908.15 / 18f 1b | 12/13 / 12/13 | yes |
| EGR15R160 | 29387.39 / 9635.64 / 15f 1b | 29387.39 / 9635.64 / 15f 1b | 16/16 / 16/16 | yes |
| EGR20R1000 | 296392.88 / 77214.39 / 57f 1b | 296392.88 / 77214.39 / 57f 1b | 16/16 / 16/16 | yes |
| EGR25R640 | 251741.75 / 58059.66 / 39f 1b | 251741.75 / 58059.66 / 39f 1b | 16/16 / 16/16 | yes |
| EGR30R1000 | 625876.94 / 110333.02 / 45f 1b | 625876.94 / 110333.02 / 45f 1b | 16/16 / 16/16 | yes |
| EGR35R840 | 754233.44 / 114416.86 / 39f 1b | 754233.44 / 114416.86 / 39f 1b | 16/16 / 16/16 | yes |
| EGR15R160M | 29387.39 / 9635.64 / 15f 1b | 29387.39 / 9635.64 / 15f 1b | 16/16 / 16/16 | yes |
| !EGW35CA2R220 | 2 blocks of 108 mm with 10 mm gaps do not fit on a 220 mm rail | REFUSED: 2 blocks of 108 mm with 10 mm gaps do not fit on a 220 mm rail | - | same message |
| !EGH20CB | EGH is mounted from the top only: EGH20CA (the catalogue lists EGH-SA / EGH-CA) | REFUSED: EGH is mounted from the top only: EGH20CA (the catalogue lists EGH-SA / EGH-CA) | - | same message |
| !EGR20T640 | EGR rail mounted from the bottom (T) is valid HIWIN grammar, but the catalogue prints no tapped-hole dimensions for it (tables (1)-(3) on p.57-59 are the top-mounted R rail), so it is not drawn | REFUSED: EGR rail mounted from the bottom (T) is valid HIWIN grammar, but the catalogue prints no tapped-hole dimensions for it (tables (1)-(3) on p.57-59 are the top-mounted R rail), so it is not drawn | - | same message |
| !EGR15R5000 | rail length 5000 mm above the maximum 4000 mm | REFUSED: rail length 5000 mm above the maximum 4000 mm | - | same message |
| !EGR25R60 | rail length 60 mm below the catalogue minimum 100 mm (Table 2-2-1) | REFUSED: rail length 60 mm below the catalogue minimum 100 mm (Table 2-2-1) | - | same message |
| !EGW20SA1R500 | rail length 500 leaves end distance 40.00 mm, above P/2 = 30 mm (unstable rail end, p.56) | REFUSED: rail length 500 leaves end distance 40.00 mm, above P/2 = 30 mm (unstable rail end, p.56) | - | same message |
| !EGW20SAM | stainless steel (M) exists for EG15C only (model number note 4, p.45) | REFUSED: stainless steel (M) exists for EG15C only (model number note 4, p.45) | - | same message |
| !EGW25CAZB | 'EGW25CAZB': expected a set EG<H|W><size><C|S><A|B><n>R<length>[Z0|ZA|ZB][C|H|P], e.g. EGH20CA2R1000ZAH, a rail EGR<size>R<length>, e.g. EGR25R1600, or a block EGW25CA | REFUSED: 'EGW25CAZB': expected a set EG<H|W><size><C|S><A|B><n>R<length>[Z0|ZA|ZB][C|H|P], e.g. EGH20CA2R1000ZAH, a rail EGR<size>R<length>, e.g. EGR25R1600, or a block EGW25CA | - | same message |
| !EGW25CA2R640ZAP+DD | dust-protection codes ZZ, DD and KK are valid HIWIN grammar; they change the overall block length (p.53), which is not drawn: leave the option out for the standard end seal and bottom seal length | REFUSED: dust-protection codes ZZ, DD and KK are valid HIWIN grammar; they change the overall block length (p.53), which is not drawn: leave the option out for the standard end seal and bottom seal length | - | same message |

## Rebuild on a free parameter change

A free parameter changed on a built part (`parameters.change` on the instance) against the code built directly, both as a fresh parametric instance and as the Python part:

- EGH20CA2R1000ZAH length 1000 -> 1240 vs EGH20CA2R1240ZAH: equals the fresh instance **True**, equals the Python part **True** (437426.16 / 113387.02 / 105f 3b)
- EGW25CA1R640ZAP blocks 1 -> 2 vs EGW25CA2R640ZAP: equals the fresh instance **True**, equals the Python part **True** (443672.74 / 91881.43 / 75f 3b)

## What 0.50.0 does with a link, and where the limits apply (measured)

- insert_design configuration=EGH-CA-20: ok
- row EGH-CA-20 inserted == Python EGH20CA1R400: True; python 153314.54 / 40231.72 / [0.000..400.000] x [-21.000..21.000] x [0.000..28.000] / 45f 2b; inserted 153314.54 / 40231.72 / [0.000..400.000] x [-21.000..21.000] x [0.000..28.000] / 45f 2b
- insert_design configuration=EGH-CA-20 parameters={length: 800 mm}: accepted, rail x extent is 400.0 (400 = the parameters key is ignored)
- component.set_link_parameters: {"command": "component.set_link_parameters", "error": "unknown command `component.set_link_parameters`", "step": 2}
- parameters.change length in the assembly that holds the link: {"command": "parameters.change", "error": "unknown parameter `length`", "step": 2}
- insert_design configuration=nope: {"command": "component.insert_design", "error": "invalid parameters for `component.insert_design`: configuration `nope` does not exist in the source design", "step": 1}

- ordinary edit: length 9000 mm (max 4000): accepted: {"changed": {"length": 9000.0}, "errors": [], "recomputed": 11, "restored": 0}
- ordinary edit: blocks 40 on a 400 mm rail: accepted: {"changed": {"blocks": 40.0}, "errors": [], "recomputed": 7, "restored": 0}
- row with length 9000 mm, config.activate: REFUSED {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `Rail length: the catalogue minimum and the largest single rail` restricts the final value", "step": 1}
- row with 40 blocks on 400 mm, config.activate: REFUSED {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `Blocks that fit on the rail with the gap between them` restricts the final value", "step": 1}
- row with length 30 mm, config.activate: REFUSED {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `Rail length: the catalogue minimum and the largest single rail` restricts the final value", "step": 1}

## What 0.50.0 could not express (the `blocked` list of faithfulness.json)

| Wanted | Result on 0.50.0 | Workaround used (labelled) |
|---|---|---|
| Free parameter values on insert | `component.insert_design` accepts a `parameters` key and ignores it silently; `component.set_link_parameters` is unknown (see the measured lines above) | the instance file: `config.activate` + `parameters.change` on a copy of the model, which is then the file that gets inserted |
| Thread designation from a parameter | `thread: "M5"` is a literal | one hole feature per designation (M4, M5, M6, M8, M10), the row suppresses all but its own |
| Names of pattern copies | the copies of a feature pattern are named `Body<N>` | the harness renames them `Block 1..n` by position before `src/check.py` reads them |

What SolidCraft needs (proposals): `component.insert_design {parameters}` stored and applied, `component.set_link_parameters`; `solid.pattern.rectangular {body_names}`; a thread designation that can come from a parameter or a choice; rules by feature name; range rules enforced on `parameters.change` with an opt-in. See tangency-labs/solidcraft#23175.
