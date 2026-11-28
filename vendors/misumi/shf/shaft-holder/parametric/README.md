# misumi.shf.shaft-holder as a parametric SolidCraft generator

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai, and rules addressed by feature name requires the #23175 surface (unavailable on 0.50.0/0.51.1). The exact command errors quoted below are observations from SolidCraft 0.50.0. On capable hosts, link overrides and ordinary source `parameters.change` enforce limit rules marked `enforce_on_edit`.

The MISUMI Economy shaft supports (T-shaped with slit `E-SHSTB/M/A`, with side slit `E-SHWTB/A`, thickened `E-SHSTBN/MN`, and the aluminium `C-SHA`) modelled
ONCE in SolidCraft (`shf-shaft-holder/shf-shaft-holder.sc`), a configuration table of the 30 catalogue rows, the ordering code as field templates and the logic
as plain Rhai, following SolidCraft's generator interface (`docs/formats/generator.md`, version 2, issue 22331). The Python generator in `../src` is untouched
and is the reference every code below is compared with.

```
shf-shaft-holder/              the package layout of the interface document
  generator.toml               [[template]] x2 and [rows."<family>-<D>"] source / page / status per configuration row
  shf-shaft-holder.sc          the parametric model + its configuration table + its rules (built by build.py)
  generator.rhai               resolve(fields) -> #{configuration, parameters, properties}; fields(configuration, parameters) -> fields
  tables/*.csv                 dims, csha, types, tolerance, params: generated from ../data/*.csv by pkgfiles.py (rows keep source, page, status)
build.py  pkgfiles.py          builds the model with solidcraft-cli; writes the tables and generator.toml
run_codes.py  report.py        the end-to-end proof (results.json) and the tables below
faithfulness.py  ci.sh         the verdict file for tools/parametric-verdict, and the one command CI runs
```

## How the model is built (all of it worked on SolidCraft 0.50.0 unless "cannot express" says otherwise)

- **One model, the four families.** 22 user parameters: the section (`bore th base_len foot_t top_w h h1_off`), the hole table (`l1 d_base e_off m_depth d2 d1 l_cb c_slit`),
  the unitless switches `fam` (0 slit and thickened, 1 side slit, 2 C-SHA), `screws`, `base_n`, `msize` (thread size), `alu`, `sel` (row number) and the text
  `part_type`; `h1 = h + h1_off`, `sy1`, `sy2` and `thr_depth` are derived. One profile sketch (eight points, all expressions) serves every family, because C-SHA's
  reference outline has the same shape.
- **The free value is the height `h`.** Every row carries a list of allowed heights (`h_all`, and `h_alu` for the aluminium types E-SHSTA / E-SHWTA, which are
  switched by `alu = 1`) as `allow_parameter_values` rules on `sel`; C-SHA has one fixed height per D.
- **Family branches are suppression columns AND `drive_suppression` rules.** 25 features: the shaft bore, 2 + 4 base holes (`base_n`), the vertical slit with 2
  clearance holes, 2 counterbores and the tapped holes (families 0 and 2), the side slit with its clearance hole, counterbore and tapped hole (family 1). The
  second clamp screw of the thickened D30 to D50 types is `screws >= 2`.
- **A thread size cannot come from a parameter** (see below): one tapped-hole feature per thread size (M4, M5, M6, M8, M12 on the vertical slit, M4, M6, M8 on the
  side slit), each switched on by `msize`. The tapped depth is `thr_depth = m_depth + (1 - sign(m_depth / 1 mm)) * (top_w - c_slit) / 2`: `m_depth`, or the
  wall when it is 0 (through), with no conditional in the expression.
- **Screw positions** `sy1 = -(screws - 1) * th / 4` and `sy2 = th / 4`: one screw on the centre plane, two at plus and minus T/4 (Python's `sy`).
- **Python's two builders became one**: `C-SHA`'s slit is `c_slit = 2` (the drawn 2 mm slit) and its clearance hole and counterbore are suppressed.

## The ordering code

`generator.toml`: `{pfx: E|C}-SH{fam: STBN|STMN|STB|STM|STA|WTB|WTA|A}{d: int 1..99}[\-{h: int 0..99999999}]`, then `{raw: text 1..64 [A-Za-z0-9-]}` for every
other shape. `generator.rhai` gives the Python message for each: the shape error (`'E-SHSTM8-25-3': expected <type><D>-<H> ...`), a missing height, a height
that is not offered, the `E-SHSTB15-25` note, `E-SHSTMN` on a `*` marked D, the aluminium types on a non-marked H, a C-SHA with a height or an unlisted D.
`fields(configuration, parameters)` is the inverse (code printing for a bill of materials): for all 16 codes parse(print(parse(code))) gives the same row and parameters.

## Result: side by side

Volume mm3 / area mm2 / bbox mm / faces and bodies; the spec check column is passed rows / rows. Equal = same bodies, volume and area within 1e-6 relative,
same bbox, face and body counts.

| code | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec check python | spec check parametric | equal |
|---|---|---|---|---|---|
| E-SHSTM8-25 | 7535.4 / 4031.6 / 42x10x41 / 20f 1b | 7535.4 / 4031.6 / 42x10x41 / 20f 1b | 21/21 | 21/21 | yes |
| E-SHSTB12-15 | 5467.3 / 3582.9 / 42x10x33 / 20f 1b | 5467.3 / 3582.9 / 42x10x33 / 20f 1b | 21/21 | 21/21 | yes |
| E-SHSTB15-20 | 10785.8 / 5251.6 / 54x10x40 / 21f 1b | 10785.8 / 5251.6 / 54x10x40 / 21f 1b | 21/21 | 21/21 | yes |
| E-SHSTA16-20 | 10552.4 / 5226.2 / 54x10x40 / 21f 1b | 10552.4 / 5226.2 / 54x10x40 / 21f 1b | 21/21 | 21/21 | yes |
| E-SHSTM20-60 | 44885.7 / 12968.8 / 67x16x86 / 20f 1b | 44885.7 / 12968.8 / 67x16x86 / 20f 1b | 21/21 | 21/21 | yes |
| E-SHSTB30-40 | 54479.1 / 15916.7 / 85x20x73 / 21f 1b | 54479.1 / 15916.7 / 85x20x73 / 21f 1b | 21/21 | 21/21 | yes |
| E-SHWTB8-10 | 5510.5 / 3255.1 / 44x12x17 / 21f 1b | 5510.5 / 3255.1 / 44x12x17 / 21f 1b | 21/21 | 21/21 | yes |
| E-SHWTA10-15 | 8763.6 / 4241.8 / 50x12x24 / 21f 1b | 8763.6 / 4241.8 / 50x12x24 / 21f 1b | 21/21 | 21/21 | yes |
| E-SHWTB20-30 | 31476.1 / 10080.7 / 75x16x45 / 21f 1b | 31476.1 / 10080.7 / 75x16x45 / 21f 1b | 21/21 | 21/21 | yes |
| E-SHWTB30-60 | 87834.5 / 19800.3 / 94x20x81 / 21f 1b | 87834.5 / 19800.3 / 94x20x81 / 21f 1b | 21/21 | 21/21 | yes |
| E-SHSTBN10-10 | 9602.7 / 5105.8 / 48x15x29 / 20f 1b | 9602.7 / 5105.8 / 48x15x29 / 20f 1b | 21/21 | 21/21 | yes |
| E-SHSTMN16-30 | 28498.2 / 9417.8 / 54x20x53 / 20f 1b | 28498.2 / 9417.8 / 54x20x53 / 20f 1b | 21/21 | 21/21 | yes |
| E-SHSTBN30-80 | 158150.8 / 30185.3 / 85x35x113 / 26f 1b | 158150.8 / 30185.3 / 85x35x113 / 26f 1b | 23/23 | 23/23 | yes |
| E-SHSTMN50-50 | 289222.2 / 51232.8 / 125x50x101 / 28f 1b | 289222.2 / 51232.8 / 125x50x101 / 28f 1b | 23/23 | 23/23 | yes |
| C-SHA10 | 7075.8 / 3746.6 / 42x11x35 / 17f 1b | 7075.8 / 3746.6 / 42x11x35 / 17f 1b | 8/8 | 8/8 | yes |
| C-SHA30 | 52554.7 / 14260.1 / 80x20x70 / 18f 1b | 52554.7 / 14260.1 / 80x20x70 / 18f 1b | 8/8 | 8/8 | yes |

| rejected code | python message | parametric message | same |
|---|---|---|---|
| E-SHSTB15-25 | E-SHSTB15 is not available with H = 25 (p.541 note) | E-SHSTB15 is not available with H = 25 (p.541 note) | yes |
| E-SHSTM8-35 | height 35 is not offered for E-SHSTM8: H = [10, 15, 20, 25, 30, 40] (p.541) | height 35 is not offered for E-SHSTM8: H = [10, 15, 20, 25, 30, 40] (p.541) | yes |
| E-SHSTA8-20 | the aluminium type E-SHSTA is applicable only to * marked dimensions: for D8 no height (p.541) | the aluminium type E-SHSTA is applicable only to * marked dimensions: for D8 no height (p.541) | yes |
| E-SHSTA10-25 | the aluminium type E-SHSTA is applicable only to * marked dimensions: for D10 only H = [20] (p.541) | the aluminium type E-SHSTA is applicable only to * marked dimensions: for D10 only H = [20] (p.541) | yes |
| E-SHSTMN10-10 | E-SHSTMN is not applicable to the * marked D10 (p.542 note) | E-SHSTMN is not applicable to the * marked D10 (p.542 note) | yes |
| E-SHSTM9-20 | E-SHSTM is not listed for D9: catalogue sizes are [8, 10, 12, 15, 16, 20, 25, 30] (p.541) | E-SHSTM is not listed for D9: catalogue sizes are [8, 10, 12, 15, 16, 20, 25, 30] (p.541) | yes |
| E-SHSTM8 | E-SHSTM8 needs its height: E-SHSTM8-<H> with H from [10, 15, 20, 25, 30, 40] (p.541) | E-SHSTM8 needs its height: E-SHSTM8-<H> with H from [10, 15, 20, 25, 30, 40] (p.541) | yes |
| C-SHA10-20 | C-SHA has one fixed height per hole diameter (no H in the part number): C-SHA10 | C-SHA has one fixed height per hole diameter (no H in the part number): C-SHA10 | yes |
| C-SHA8 | C-SHA is listed for hole D [10, 12, 16, 20, 25, 30], not 8 (p.540) | C-SHA is listed for hole D [10, 12, 16, 20, 25, 30], not 8 (p.540) | yes |
| E-SHWTB25-30 | E-SHWTB is not listed for D25: catalogue sizes are [8, 10, 12, 16, 20, 30] (p.541) | E-SHWTB is not listed for D25: catalogue sizes are [8, 10, 12, 16, 20, 30] (p.541) | yes |
| E-SHSTM8-25-3 | 'E-SHSTM8-25-3': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | 'E-SHSTM8-25-3': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | yes |
| E-SHA10 | 'E-SHA10': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | 'E-SHA10': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | yes |
| E-SHSTM100-20 | 'E-SHSTM100-20': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | 'E-SHSTM100-20': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | yes |
| E-SHSTA16-25 | the aluminium type E-SHSTA is applicable only to * marked dimensions: for D16 only H = [15, 20] (p.541) | the aluminium type E-SHSTA is applicable only to * marked dimensions: for D16 only H = [15, 20] (p.541) | yes |
| E-SHSTMN10-15 | E-SHSTMN is not applicable to the * marked D10 (p.542 note) | E-SHSTMN is not applicable to the * marked D10 (p.542 note) | yes |
| E-SHSTB15 | E-SHSTB15 needs its height: E-SHSTB15-<H> with H from [15, 20, 25, 30] (p.541) | E-SHSTB15 needs its height: E-SHSTB15-<H> with H from [15, 20, 25, 30] (p.541) | yes |
| C-SHA7 | C-SHA is listed for hole D [10, 12, 16, 20, 25, 30], not 7 (p.540) | C-SHA is listed for hole D [10, 12, 16, 20, 25, 30], not 7 (p.540) | yes |
| C-SHA10-5 | C-SHA has one fixed height per hole diameter (no H in the part number): C-SHA10 | C-SHA has one fixed height per hole diameter (no H in the part number): C-SHA10 | yes |
| E-SHWTB9-10 | E-SHWTB is not listed for D9: catalogue sizes are [8, 10, 12, 16, 20, 30] (p.541) | E-SHWTB is not listed for D9: catalogue sizes are [8, 10, 12, 16, 20, 30] (p.541) | yes |
| E-SHSTM8-0 | height 0 is not offered for E-SHSTM8: H = [10, 15, 20, 25, 30, 40] (p.541) | height 0 is not offered for E-SHSTM8: H = [10, 15, 20, 25, 30, 40] (p.541) | yes |
| E-SHWTA12-25 | the aluminium type E-SHWTA is applicable only to * marked dimensions: for D12 only H = [20] (p.541) | the aluminium type E-SHWTA is applicable only to * marked dimensions: for D12 only H = [20] (p.541) | yes |
| E-SHSTB8-45 | height 45 is not offered for E-SHSTB8: H = [10, 15, 20, 25, 30, 40] (p.541) | height 45 is not offered for E-SHSTB8: H = [10, 15, 20, 25, 30, 40] (p.541) | yes |
| E-SHSTA8-10 | the aluminium type E-SHSTA is applicable only to * marked dimensions: for D8 no height (p.541) | the aluminium type E-SHSTA is applicable only to * marked dimensions: for D8 no height (p.541) | yes |
| E-SHWTA8-10 | the aluminium type E-SHWTA is applicable only to * marked dimensions: for D8 no height (p.541) | the aluminium type E-SHWTA is applicable only to * marked dimensions: for D8 no height (p.541) | yes |
| E-SHSTBN9-10 | E-SHSTBN is not listed for D9: catalogue sizes are [10, 12, 15, 16, 20, 25, 30, 35, 40, 50] (p.542) | E-SHSTBN is not listed for D9: catalogue sizes are [10, 12, 15, 16, 20, 25, 30, 35, 40, 50] (p.542) | yes |
| E-SHSTMN15-25-1 | 'E-SHSTMN15-25-1': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | 'E-SHSTMN15-25-1': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | yes |
| C-SHA | 'C-SHA': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | 'C-SHA': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | yes |
| C-SHA25-20 | C-SHA has one fixed height per hole diameter (no H in the part number): C-SHA10 | C-SHA has one fixed height per hole diameter (no H in the part number): C-SHA10 | yes |
| X | 'X': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | 'X': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | yes |
| E-SHSTM8-25- | 'E-SHSTM8-25-': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | 'E-SHSTM8-25-': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | yes |
| E-SHSTM8--25 | 'E-SHSTM8--25': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | 'E-SHSTM8--25': expected <type><D>-<H> with type E-SHSTB, E-SHSTM, E-SHSTA, E-SHWTB, E-SHWTA, E-SHSTBN or E-SHSTMN (e.g. E-SHSTM8-25), or C-SHA<D> (e.g. C-SHA10) | yes |

| change | on | changed in place vol / area / bbox / faces | direct code (inserted) | python | equal (changed = direct = python) |
|---|---|---|---|---|---|
| h -> 40 mm | E-SHSTM8-25 (= E-SHSTM8-40) | 10235.4 / 4871.6 / 42x10x56 / 20f 1b | 10235.4 / 4871.6 / 42x10x56 / 20f 1b | 10235.4 / 4871.6 / 42x10x56 / 20f 1b | yes |
| h -> 60 mm | E-SHWTB20-30 (= E-SHWTB20-60) | 54996.1 / 13980.7 / 75x16x75 / 21f 1b | 54996.1 / 13980.7 / 75x16x75 / 21f 1b | 54996.1 / 13980.7 / 75x16x75 / 21f 1b | yes |
| h -> 25 mm | E-SHSTBN30-80 (= E-SHSTBN30-25) | 71525.8 / 21385.3 / 85x35x58 / 26f 1b | 71525.8 / 21385.3 / 85x35x58 / 26f 1b | 71525.8 / 21385.3 / 85x35x58 / 26f 1b | yes |
| h -> 15 mm | E-SHSTA16-20 (= E-SHSTA16-15) | 9052.4 / 4826.2 / 54x10x35 / 21f 1b | 9052.4 / 4826.2 / 54x10x35 / 21f 1b | 9052.4 / 4826.2 / 54x10x35 / 21f 1b | yes |
| h -> 30 mm | E-SHSTB15-20 (= E-SHSTB15-30) | 13785.8 / 6051.6 / 54x10x50 / 21f 1b | 13785.8 / 6051.6 / 54x10x50 / 21f 1b | 13785.8 / 6051.6 / 54x10x50 / 21f 1b | yes |

| probe | result |
|---|---|
| insert_design with a free `parameters` map (h 40 mm) | {'bodies': ['lim.model', 'lim.model (2)'], 'volume': 12370.736884240823} |
| component.set_link_parameters | {"command": "component.set_link_parameters", "error": "unknown command `component.set_link_parameters`", "step": 1} |
| generator.parse | {"command": "generator.parse", "error": "unknown command `generator.parse`", "step": 1} |
| row with h 35 mm for slit-8 (not in 10 15 20 25 30 40) | {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `slit-8: H from the p.541 table` restricts the final value", "step": 1} |
| row with h 15 mm for the aluminium slit-10 (only 20) | {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `slit-10: aluminium types only for the * marked H (p.541)` restricts the final value", "step": 1} |
| h 35 mm by an ordinary parameters.change | {'bodies': ['Body'], 'volume': 9335.368442120414} |
| unknown row | {"command": "component.insert_design", "error": "invalid parameters for `component.insert_design`: configuration `no-such-row` does not exist in the source design", "step": 1} |

config.table: 30 rows, 47 columns, 86 rules

All 16 codes: the parametric part has the same volume, area, bbox, face and body count as the Python part, and passes the same spec check with the same number of
rows (21, or 23 for the two-screw thickened types, or 8 for C-SHA). Every refusal (the 10 of `codes.txt` and 21 more, compared with `holder.parse`) has the
Python message word for word.

A code with a dangling or doubled separator (`E-SHSTM8-25-`, `E-SHSTM8--25`) is refused with the Python shape message, quoting the code as typed: the height is
preceded by the required separator `\-` and the second template (one free text field) catches everything else.

## Commands

```
# on a build host or in CI (the `parametric` workflow runs ci.sh): SC_CLI = solidcraft-cli 0.50.0, RHAI_RUN = the built runtime/rhai-run
bash vendors/misumi/shf/shaft-holder/parametric/ci.sh OUTDIR     # build.py, run_codes.py, faithfulness.py -> OUTDIR/faithfulness.json
python3 vendors/misumi/shf/shaft-holder/parametric/report.py OUTDIR/results.json    # the tables above
tools/parametric-verdict OUTDIR/faithfulness.json                # the verdict CI prints
```

## It stays parametric

Row for the code (`config.row from=<family-D row>` with the height), activate it, then `parameters.change h` on the configured design; compared with the direct
code inserted the same way and with the Python part: identical in all five cases (the table's last block; one of them an aluminium type and one a two-screw
thickened type). The screws, the slit, the counterbore and the bore centre all follow `h` through `h1 = h + h1_off`.

## SolidCraft 0.50.0 observations (exact errors) and workarounds

1. **A free parameter value on an inserted part requires the #23175 surface (unavailable on 0.50.0/0.51.1).** `component.insert_design {path, configuration: "slit-8", parameters: {h: "40 mm"}}` is accepted and the key ignored
   (the occurrence keeps the row's own height, not 40 mm; no error); `component.set_link_parameters` -> `unknown command`; `generator.parse` -> `unknown command`.
   Workaround (labelled): a row for the code in a working copy of the model (`config.row {from: <family-D row>, values: {param:h: "25 mm", ...}}`), inserted with
   `configuration`; to change the height, change it in the working copy and insert again. Listed under "blocked" in `faithfulness.json`
   (requires the #23175 surface (unavailable on 0.50.0/0.51.1)).
2. **Limits on ordinary edits.** `allow_parameter_values` is enforced on a row (`config.row ... values {param:h: "35 mm"}` on `slit-8` -> `rule `slit-8: H from the p.541
   table` restricts the final value`; the aluminium list `slit-10: aluminium types only for the * marked H (p.541)` the same) but `parameters.change h 35 mm` in the
   design is accepted. The list per row is therefore enforced by `resolve` for a code and by the rules for a row.
3. **A thread designation cannot come from a parameter**: `solid.hole {thread: "M8"}` is text. One tapped-hole feature per size (five sizes, seven features, on the vertical slit: M8 and M12 have a second screw; three on
   the side slit), each with its own rule. Cosmetic thread placement was not needed here: the tapped holes are `solid.hole` features.
4. **A conditional in an expression.** The tapped depth is `m_depth` or the wall `(top_w - c_slit) / 2` when `m_depth` is 0; `sign()` does it:
   `m_depth + (1 - sign(m_depth / 1 mm)) * (top_w - c_slit) / 2` (`sign` of a length must be made unitless first).
5. **The working "Default" row.** `config.configure` with no rows makes a `Default` row from the current values; when the model is left in a working state that is
   not a catalogue row, `config.rule` refuses: `row `Default`: invalid parameters for `config.activate`: configuration `Default` would fail to rebuild:
   VThread_M8_1: no cylindrical face there to thread`. `build.py` deletes it before adding the rules (`config.row {name: "Default", delete: true}`).
6. **A feature group is drawn in its own state.** The side-slit group (screw axis `e_off` across, not up) is drawn with the side D30 dimensions after the
   vertical-slit group is switched off, because the vertical group's default dimensions put its screw axis (`h + e_off`) above the top of the side-slit body; each thread feature is switched off right after it is created,
   because the next size drills the same place.
7. **Rules addressed by feature name need #23175 (our draft, being finished).** In 0.50.0, rules name features by integer id (`config.rule` `feature` is an integer), so `build.py` builds the model in two passes.

## What does not fit the interface document, and proposals

| Where | What the holder needs | Proposal |
|---|---|---|
| field template | the type contains a hyphen (`E-SHSTM`): a choice value with `-` does not match in the stand-in (it compares with the separators stripped) | split as `{pfx: E\|C}-SH{fam: ...}` (done here); or match choice values with their separators stripped on both sides |
| field template | a catch-all so that a code of the wrong shape gets the generator's message and not the engine's | a second `[[template]]` of one free text field (done here), or optional `fn no_match(raw)` in `generator.rhai` |
| `[parameters]` | a list of allowed values per row | `allow_parameter_values` rules (done here); a `values` column of the table would read better |
| `resolve` return | description, material, surface per code, the type as a text parameter for the inverse | `properties: #{...}` and a text parameter `part_type` (done here) |
| rules | name a feature by name; a suppress-if that reads a parameter in the feature itself | `feature` by name in `config.rule` |

The optional link proof is declared in `link_checks.json` and run by `ci.sh` through `runtime.parametric.links`. It adds insertion, link-edit, and out-of-range refusal rows only when the command catalogue lists `component.set_link_parameters`. Release builds retain their existing rows and link dependency item.

### #23175 checks

The 0.50.0/0.51.1 results above remain release observations. The #23175 CI artifact records 16 valid, 31 rejects, 8 rebuild checks and 0 blocked records. The next CI run also checks link overrides and ordinary edit refusal with `enforce_on_edit` where limit rules exist; these new checks are pending. Differences remain differences.

The supplied #23175 artifact includes 3 link checks; the added ordinary-edit enforcement check awaits CI.
