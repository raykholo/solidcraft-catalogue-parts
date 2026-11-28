# misumi.hbl.bracket as a parametric SolidCraft generator

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai, and rules addressed by feature name requires the #23175 surface (unavailable on 0.50.0/0.51.1). The exact command errors quoted below are observations from SolidCraft 0.50.0. On capable hosts, link overrides and ordinary source `parameters.change` enforce limit rules marked `enforce_on_edit`.

The MISUMI 5 series extruded brackets modelled ONCE in SolidCraft (`hbl-bracket/hbl-bracket.sc`), a configuration table of the 19 catalogue rows, the ordering
code as a field template and the logic as plain Rhai, following SolidCraft's generator interface (`docs/formats/generator.md`, version 2, issue 22331).
The Python generator in `../src` is untouched and is the reference every code below is compared with.

```
hbl-bracket/                   the package layout of the interface document
  generator.toml               [[template]] and [rows."<type>"] source / page / status per configuration row
  hbl-bracket.sc               the parametric model + its configuration table + its rules (built by build.py)
  generator.rhai               resolve(fields) -> #{configuration, parameters, properties}; fields(configuration, parameters) -> fields
  tables/*.csv                 types, alterations, params: generated from ../data/*.csv by pkgfiles.py (rows keep source, page, status)
build.py  pkgfiles.py          builds the model with solidcraft-cli; writes the tables and generator.toml
run_codes.py  report.py        the end-to-end proof (results.json) and the tables below
faithfulness.py  ci.sh         the verdict file for tools/parametric-verdict, and the one command CI runs
../../../../runtime/fieldtemplate.py   stand-in for the field-template parser and printer (doc section 3), shared with the other parametric proofs
../../../../runtime/rhai-run/          stand-in host for generator.rhai: the real Rhai engine, the documented sandbox limits, table() / refuse() / code_template()
```

## How the model is built (all of it worked on SolidCraft 0.50.0)

- **One model, 16 parameters.** `width foot_len wall_len foot_t wall_t hole_d hole_off tab_w tab_h fh1 fh2 wh1 wh2` (mm) and the unitless `tabs foot_n wall_n`;
  `hole_x = width / 2 + hole_off` is derived (the eccentric types HBLTH5 / HBLTHB5 put the holes 5 from one side: `hole_off = -1` on a 12 wide plate).
- **The L section is one parametric sketch** (six points, every coordinate an expression) extruded by `width`.
- **Optional features are suppression columns AND `drive_suppression` rules.** The two tabs of the HBK types (`tabs = 1`), the second foot hole (`foot_n >= 2`)
  and the second wall hole (`wall_n >= 2`). Each row carries the suppression of its own optional features, and a rule per feature switches it on a unitless
  parameter, so a user who edits `tabs` on an inserted part gets the tabs. The first foot and wall hole are always there.
- **Configuration table = the catalogue rows.** 19 rows (one per type, `HBLTS5-4` included), from `data/types.csv`; source and page per row in `generator.toml`.
  Where the row has no tab, `tab_w` and `tab_h` keep inert positive values (6 and 1) so the suppressed box features stay valid; the tabs are off by `tabs = 0`.
- **Table-derived hole diameter.** HBLTS5 and HBLTS5-4 share HBLTS5 with `hole_d` overrides. An alteration (`-C`, `-SET`, ...) only adds accessory text to the description (the Python generator does the same), so the code
  resolves to a row plus its table-derived hole diameter.

## The ordering code

`generator.toml`: `{base: text 1..24 [A-Za-z0-9]}[\-{rest: text 1..40 [A-Za-z0-9-]}]`, then `{raw: text 1..64 [A-Za-z0-9-]}` for a dangling or doubled `-` (`HBLTS5-`, `HBLTS5--C`), which `resolve` reads as typed. `resolve` splits `rest` on `-`, takes a leading `4` as the type's own `-4`
(`HBLTS5-4`), and every Python refusal, in its order and with its message, is a `refuse(kind, message)` in `generator.rhai` (`invalid` / `not_modelled` mirror
`CodeError` / `NotModelled`). The description, material and surface are plain Rhai over `tables/*.csv`, and the harness compares the description with the Python
one character for character. `fields(configuration, parameters)` is the inverse (the alteration is accessory text, not a parameter, so it is not printed).

## Result: side by side

Volume mm3 / area mm2 / bbox mm / faces and bodies; the spec check column is passed rows / rows. Equal = same bodies, volume and area within 1e-6 relative,
same bbox, face and body counts.

| code | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec check python | spec check parametric | equal |
|---|---|---|---|---|---|
| HBLTS5 | 4312.4 / 2687.8 / 14x35x35 / 10f 1b | 4312.4 / 2687.8 / 14x35x35 / 10f 1b | 12/12 | 12/12 | yes |
| HBLTS5-4 | 4391.0 / 2687.8 / 14x35x35 / 10f 1b | 4391.0 / 2687.8 / 14x35x35 / 10f 1b | 12/12 | 12/12 | yes |
| HBLTSB5 | 4312.4 / 2687.8 / 14x35x35 / 10f 1b | 4312.4 / 2687.8 / 14x35x35 / 10f 1b | 12/12 | 12/12 | yes |
| CHBLTS5 | 4312.4 / 2687.8 / 14x35x35 / 10f 1b | 4312.4 / 2687.8 / 14x35x35 / 10f 1b | 12/12 | 12/12 | yes |
| NBLTS5 | 4312.4 / 2687.8 / 14x35x35 / 10f 1b | 4312.4 / 2687.8 / 14x35x35 / 10f 1b | 12/12 | 12/12 | yes |
| HBLTV5 | 5937.4 / 3387.8 / 19x35x35 / 10f 1b | 5937.4 / 3387.8 / 19x35x35 / 10f 1b | 12/12 | 12/12 | yes |
| HBLTVB5 | 5937.4 / 3387.8 / 19x35x35 / 10f 1b | 5937.4 / 3387.8 / 19x35x35 / 10f 1b | 12/12 | 12/12 | yes |
| HBLTSW5 | 7154.8 / 4437.5 / 14x57x57 / 12f 1b | 7154.8 / 4437.5 / 14x57x57 / 12f 1b | 12/12 | 12/12 | yes |
| HBLTVW5 | 9879.8 / 5577.5 / 19x57x57 / 12f 1b | 9879.8 / 5577.5 / 19x57x57 / 12f 1b | 12/12 | 12/12 | yes |
| HBLTF5 | 5873.6 / 3638.6 / 14x37x57 / 11f 1b | 5873.6 / 3638.6 / 14x37x57 / 11f 1b | 12/12 | 12/12 | yes |
| HBKTST5 | 4684.9 / 2886.3 / 14x36x36 / 20f 1b | 4684.9 / 2886.3 / 14x36x36 / 20f 1b | 14/14 | 14/14 | yes |
| HBKTS5 | 4684.9 / 2886.3 / 14x36x36 / 20f 1b | 4684.9 / 2886.3 / 14x36x36 / 20f 1b | 14/14 | 14/14 | yes |
| HBKTSB5 | 4684.9 / 2886.3 / 14x36x36 / 20f 1b | 4684.9 / 2886.3 / 14x36x36 / 20f 1b | 14/14 | 14/14 | yes |
| HBKUS5 | 11854.8 / 5008.5 / 14x52x52 / 20f 1b | 11854.8 / 5008.5 / 14x52x52 / 20f 1b | 14/14 | 14/14 | yes |
| HBKUSB5 | 11854.8 / 5008.5 / 14x52x52 / 20f 1b | 11854.8 / 5008.5 / 14x52x52 / 20f 1b | 14/14 | 14/14 | yes |
| NBLUS5 | 11290.4 / 4746.0 / 14x51x51 / 10f 1b | 11290.4 / 4746.0 / 14x51x51 / 10f 1b | 12/12 | 12/12 | yes |
| HBLUS5 | 11290.4 / 4746.0 / 14x51x51 / 10f 1b | 11290.4 / 4746.0 / 14x51x51 / 10f 1b | 12/12 | 12/12 | yes |
| HBLTH5 | 3662.4 / 2407.8 / 12x35x35 / 10f 1b | 3662.4 / 2407.8 / 12x35x35 / 10f 1b | 12/12 | 12/12 | yes |
| HBLTHB5 | 3662.4 / 2407.8 / 12x35x35 / 10f 1b | 3662.4 / 2407.8 / 12x35x35 / 10f 1b | 12/12 | 12/12 | yes |
| HBLTS5-C | 4312.4 / 2687.8 / 14x35x35 / 10f 1b | 4312.4 / 2687.8 / 14x35x35 / 10f 1b | 12/12 | 12/12 | yes |
| HBLTS5-4-C | 4391.0 / 2687.8 / 14x35x35 / 10f 1b | 4391.0 / 2687.8 / 14x35x35 / 10f 1b | 12/12 | 12/12 | yes |
| HBKUS5-C | 11854.8 / 5008.5 / 14x52x52 / 20f 1b | 11854.8 / 5008.5 / 14x52x52 / 20f 1b | 14/14 | 14/14 | yes |
| HBLTF5-SEC | 5873.6 / 3638.6 / 14x37x57 / 11f 1b | 5873.6 / 3638.6 / 14x37x57 / 11f 1b | 12/12 | 12/12 | yes |
| HBLTSW5-SET | 7154.8 / 4437.5 / 14x57x57 / 12f 1b | 7154.8 / 4437.5 / 14x57x57 / 12f 1b | 12/12 | 12/12 | yes |
| HBKTS5-SST | 4684.9 / 2886.3 / 14x36x36 / 20f 1b | 4684.9 / 2886.3 / 14x36x36 / 20f 1b | 14/14 | 14/14 | yes |

| rejected code | python message | parametric message | same |
|---|---|---|---|
| HBLTS5-5 | HBLTS5-5: unknown alteration '5'; the catalogue lists C, SET, SST, SEU, SSU, SEP, SSP, SEC (no -5 or other suffix exists) | HBLTS5-5: unknown alteration '5'; the catalogue lists C, SET, SST, SEU, SSU, SEP, SSP, SEC (no -5 or other suffix exists) | yes |
| HBLTV5-4 | HBLTV5-4: HBLTV5 has no -4 version (an M4 screw version exists for HBLTS5 only; the plain code is the M5 one) | HBLTV5-4: HBLTV5 has no -4 version (an M4 screw version exists for HBLTS5 only; the plain code is the M5 one) | yes |
| HBKUS5-4 | HBKUS5-4: HBKUS5 has no -4 version (an M4 screw version exists for HBLTS5 only; the plain code is the M5 one) | HBKUS5-4: HBKUS5 has no -4 version (an M4 screw version exists for HBLTS5 only; the plain code is the M5 one) | yes |
| HBLTSWB5 | 'HBLTSWB5': expected a bracket code such as HBLTS5 or HBKUS5; drawn: HBLTS5, HBLTSB5, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTST5, HBKTS5, HBKTSB5, HBKUS5, HBKUSB5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | 'HBLTSWB5': expected a bracket code such as HBLTS5 or HBKUS5; drawn: HBLTS5, HBLTSB5, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTST5, HBKTS5, HBKTSB5, HBKUS5, HBKUSB5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | yes |
| HBLTX5 | 'HBLTX5': expected a bracket code such as HBLTS5 or HBKUS5; drawn: HBLTS5, HBLTSB5, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTST5, HBKTS5, HBKTSB5, HBKUS5, HBKUSB5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | 'HBLTX5': expected a bracket code such as HBLTS5 or HBKUS5; drawn: HBLTS5, HBLTSB5, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTST5, HBKTS5, HBKTSB5, HBKUS5, HBKUSB5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | yes |
| HBLTS6 | HBLTS6: only the 5 series (slot width 6 mm) brackets are drawn, e.g. HBLTS5 | HBLTS6: only the 5 series (slot width 6 mm) brackets are drawn, e.g. HBLTS5 | yes |
| HBLTSB5-C | HBLTSB5-C: alteration C (M5 taps for cover mounting) is not offered for HBLTSB5 on the catalogue page; offered for: HBLTS5, HBLTS5-4, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTS5, HBKUS5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | HBLTSB5-C: alteration C (M5 taps for cover mounting) is not offered for HBLTSB5 on the catalogue page; offered for: HBLTS5, HBLTS5-4, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTS5, HBKUS5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | yes |
| HBKTSB5-C | HBKTSB5-C: alteration C (M5 taps for cover mounting) is not offered for HBKTSB5 on the catalogue page; offered for: HBLTS5, HBLTS5-4, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTS5, HBKUS5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | HBKTSB5-C: alteration C (M5 taps for cover mounting) is not offered for HBKTSB5 on the catalogue page; offered for: HBLTS5, HBLTS5-4, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTS5, HBKUS5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | yes |
| HBLTS5-SET-C | HBLTS5-SET-C: one alteration at most (C, SET, SST, SEU, SSU, SEP, SSP, SEC); the catalogue lists them as alternatives | HBLTS5-SET-C: one alteration at most (C, SET, SST, SEU, SSU, SEP, SSP, SEC); the catalogue lists them as alternatives | yes |
| HBLTS5-XYZ | HBLTS5-XYZ: unknown alteration 'XYZ'; the catalogue lists C, SET, SST, SEU, SSU, SEP, SSP, SEC (no -5 or other suffix exists) | HBLTS5-XYZ: unknown alteration 'XYZ'; the catalogue lists C, SET, SST, SEU, SSU, SEP, SSP, SEC (no -5 or other suffix exists) | yes |
| HBLFSN5 | HBLFSN5: a valid MISUMI 5 series bracket, not drawn here; drawn: HBLTS5, HBLTSB5, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTST5, HBKTS5, HBKTSB5, HBKUS5, HBKUSB5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | HBLFSN5: a valid MISUMI 5 series bracket, not drawn here; drawn: HBLTS5, HBLTSB5, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTST5, HBKTS5, HBKTSB5, HBKUS5, HBKUSB5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | yes |
| HBLTS5-4-C-SET | HBLTS5-4-C-SET: one alteration at most (C, SET, SST, SEU, SSU, SEP, SSP, SEC); the catalogue lists them as alternatives | HBLTS5-4-C-SET: one alteration at most (C, SET, SST, SEU, SSU, SEP, SSP, SEC); the catalogue lists them as alternatives | yes |
| HBLTS5-4-5 | HBLTS5-4-5: unknown alteration '5'; the catalogue lists C, SET, SST, SEU, SSU, SEP, SSP, SEC (no -5 or other suffix exists) | HBLTS5-4-5: unknown alteration '5'; the catalogue lists C, SET, SST, SEU, SSU, SEP, SSP, SEC (no -5 or other suffix exists) | yes |
| HBLFSNK5 | HBLFSNK5: a valid MISUMI 5 series bracket, not drawn here; drawn: HBLTS5, HBLTSB5, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTST5, HBKTS5, HBKTSB5, HBKUS5, HBKUSB5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | HBLFSNK5: a valid MISUMI 5 series bracket, not drawn here; drawn: HBLTS5, HBLTSB5, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTST5, HBKTS5, HBKTSB5, HBKUS5, HBKUSB5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | yes |
| HBLTS8 | HBLTS8: only the 5 series (slot width 6 mm) brackets are drawn, e.g. HBLTS5 | HBLTS8: only the 5 series (slot width 6 mm) brackets are drawn, e.g. HBLTS5 | yes |
| HBLTSB5-4 | HBLTSB5-4: HBLTSB5 has no -4 version (an M4 screw version exists for HBLTS5 only; the plain code is the M5 one) | HBLTSB5-4: HBLTSB5 has no -4 version (an M4 screw version exists for HBLTS5 only; the plain code is the M5 one) | yes |
| HBKTST5-C | HBKTST5-C: alteration C (M5 taps for cover mounting) is not offered for HBKTST5 on the catalogue page; offered for: HBLTS5, HBLTS5-4, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTS5, HBKUS5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | HBKTST5-C: alteration C (M5 taps for cover mounting) is not offered for HBKTST5 on the catalogue page; offered for: HBLTS5, HBLTS5-4, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTS5, HBKUS5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | yes |
| HBKUSB5-C | HBKUSB5-C: alteration C (M5 taps for cover mounting) is not offered for HBKUSB5 on the catalogue page; offered for: HBLTS5, HBLTS5-4, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTS5, HBKUS5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | HBKUSB5-C: alteration C (M5 taps for cover mounting) is not offered for HBKUSB5 on the catalogue page; offered for: HBLTS5, HBLTS5-4, CHBLTS5, NBLTS5, HBLTV5, HBLTVB5, HBLTSW5, HBLTVW5, HBLTF5, HBKTS5, HBKUS5, NBLUS5, HBLUS5, HBLTH5, HBLTHB5 | yes |
| HBLTS5-SEC-SST | HBLTS5-SEC-SST: one alteration at most (C, SET, SST, SEU, SSU, SEP, SSP, SEC); the catalogue lists them as alternatives | HBLTS5-SEC-SST: one alteration at most (C, SET, SST, SEU, SSU, SEP, SSP, SEC); the catalogue lists them as alternatives | yes |
| HBLTV5-4-C | HBLTV5-4-C: HBLTV5 has no -4 version (an M4 screw version exists for HBLTS5 only; the plain code is the M5 one) | HBLTV5-4-C: HBLTV5 has no -4 version (an M4 screw version exists for HBLTS5 only; the plain code is the M5 one) | yes |
| HBLTS5-C-C | HBLTS5-C-C: one alteration at most (C, SET, SST, SEU, SSU, SEP, SSP, SEC); the catalogue lists them as alternatives | HBLTS5-C-C: one alteration at most (C, SET, SST, SEU, SSU, SEP, SSP, SEC); the catalogue lists them as alternatives | yes |
| HBLTS5-4-4 | HBLTS5-4-4: unknown alteration '4'; the catalogue lists C, SET, SST, SEU, SSU, SEP, SSP, SEC (no -5 or other suffix exists) | HBLTS5-4-4: unknown alteration '4'; the catalogue lists C, SET, SST, SEU, SSU, SEP, SSP, SEC (no -5 or other suffix exists) | yes |
| HBLUS5-4 | HBLUS5-4: HBLUS5 has no -4 version (an M4 screw version exists for HBLTS5 only; the plain code is the M5 one) | HBLUS5-4: HBLUS5 has no -4 version (an M4 screw version exists for HBLTS5 only; the plain code is the M5 one) | yes |
| HBLTH5-C-SET | HBLTH5-C-SET: one alteration at most (C, SET, SST, SEU, SSU, SEP, SSP, SEC); the catalogue lists them as alternatives | HBLTH5-C-SET: one alteration at most (C, SET, SST, SEU, SSU, SEP, SSP, SEC); the catalogue lists them as alternatives | yes |
| HBLTS5- | HBLTS5-: unknown alteration ''; the catalogue lists C, SET, SST, SEU, SSU, SEP, SSP, SEC (no -5 or other suffix exists) | HBLTS5-: unknown alteration ''; the catalogue lists C, SET, SST, SEU, SSU, SEP, SSP, SEC (no -5 or other suffix exists) | yes |
| HBLTS5--C | HBLTS5--C: one alteration at most (C, SET, SST, SEU, SSU, SEP, SSP, SEC); the catalogue lists them as alternatives | HBLTS5--C: one alteration at most (C, SET, SST, SEU, SSU, SEP, SSP, SEC); the catalogue lists them as alternatives | yes |
| HBLTS5-C- | HBLTS5-C-: one alteration at most (C, SET, SST, SEU, SSU, SEP, SSP, SEC); the catalogue lists them as alternatives | HBLTS5-C-: one alteration at most (C, SET, SST, SEU, SSU, SEP, SSP, SEC); the catalogue lists them as alternatives | yes |

| change | on | changed in place vol / area / bbox / faces | direct code (inserted) | python | equal (changed = direct = python) |
|---|---|---|---|---|---|
| width -> 19 mm | HBLTS5 (= HBLTV5) | 5937.4 / 3387.8 / 19x35x35 / 10f 1b | 5937.4 / 3387.8 / 19x35x35 / 10f 1b | 5937.4 / 3387.8 / 19x35x35 / 10f 1b | yes |
| hole_d -> 4.5 mm | HBLTS5 (= HBLTS5-4) | 4391.0 / 2687.8 / 14x35x35 / 10f 1b | 4391.0 / 2687.8 / 14x35x35 / 10f 1b | 4391.0 / 2687.8 / 14x35x35 / 10f 1b | yes |

| probe | result |
|---|---|
| insert_design with a free `parameters` map (width 19 mm) | {'bodies': ['Bracket', 'Bracket (2)'], 'volume': 8624.834111144544} |
| component.set_link_parameters | {"command": "component.set_link_parameters", "error": "unknown command `component.set_link_parameters`", "step": 1} |
| generator.parse | {"command": "generator.parse", "error": "unknown command `generator.parse`", "step": 1} |
| unknown row | {"command": "component.insert_design", "error": "invalid parameters for `component.insert_design`: configuration `no-such-row` does not exist in the source design", "step": 1} |
| tabs = 1 on an HBLTS5 row (rules switch the tab features on) | {'bodies': ['Bracket'], 'volume': 4684.900466686726} |

config.table: 19 rows, 20 columns, 11 rules

All 25 codes: the parametric part has the same volume, area, bbox, face and body count as the Python part, and passes the same spec check with the same number of
rows. Every refusal (the 11 of `codes.txt` and 16 more, compared with `br.parse`) has the Python message word for word.

## Commands

```
# on a build host or in CI (the `parametric` workflow runs ci.sh): SC_CLI = solidcraft-cli 0.50.0, RHAI_RUN = the built runtime/rhai-run
bash vendors/misumi/hbl/bracket/parametric/ci.sh OUTDIR          # build.py, run_codes.py, faithfulness.py -> OUTDIR/faithfulness.json
python3 vendors/misumi/hbl/bracket/parametric/report.py OUTDIR/results.json    # the tables above
tools/parametric-verdict OUTDIR/faithfulness.json                # the verdict CI prints
```

## It stays parametric

The table-derived hole diameter is also a link parameter: a row is activated and one parameter changed on the configured design
(`parameters.change`), then compared with the other code built directly (table above, last block): the width of an HBLTS5 set to 19 mm is an HBLTV5, and its
hole diameter set to 4.5 mm is an HBLTS5-4, in volume, area, bbox and faces. The probe `tabs = 1` on an HBLTS5 row shows the rules switching the two tab
features on (volume 4684.9 = HBKTS5).

## SolidCraft 0.50.0 observations (exact errors) and workarounds

1. **A free parameter value on an inserted part requires the #23175 surface (unavailable on 0.50.0/0.51.1).** `component.insert_design {path, configuration: "HBLTS5", parameters: {width: "19 mm"}}` is accepted and the key
   ignored (the new occurrence has the volume of the HBLTS5, not of a 19 mm wide plate; no error); `component.set_link_parameters` -> `unknown command`;
   `generator.parse` -> `unknown command`. This generator needs none for its codes, so nothing is worked around; a user who wants a different width edits the
   configured design. Listed under "blocked" in `faithfulness.json` (requires the #23175 surface (unavailable on 0.50.0/0.51.1)).
2. **Rules addressed by feature name need #23175 (our draft, being finished).** In 0.50.0, rules name features by integer id (`config.rule` `feature` is an integer), so `build.py` builds the model in two passes (the ids come from the replies of the first).
3. **A suppressed feature still holds its inputs.** The tab boxes of the rows without tabs keep `tab_w = 6`, `tab_h = 1` (inert, switched off by `tabs = 0`): a size
   of 0 would be an invalid box, and a row must not rebuild an invalid feature. A conditional or a "zero means absent" feature would remove the placeholder.
4. **Face-picked features.** The Python builder picks nothing here (boxes and cylinders by corner and base), so the model needed no re-picking.

## What does not fit the interface document, and proposals

| Where | What the bracket needs | Proposal |
|---|---|---|
| field template | a type that contains a hyphen inside one code (`HBLTS5-4` is a type, `HBLTS5-C` is a type and an alteration) | resolved in Rhai (`rest` is split and a leading `4` joins the type); a `\-`-aware choice value would let the template say it |
| `resolve` return | description, material, surface per code | `properties: #{...}` written to the component's properties by `generator.insert` (done here, as in the HFS proof) |
| inverse | `generator.code {parameters}` needs parameters -> fields; an alteration is not a parameter | optional `fn fields(configuration, parameters)`; an alteration text parameter would let it print `-SET` |
| rules | name a feature by name | `feature` by name in `config.rule` |

Link insertion and editing compare two real catalogue codes with their Python generator builds. A separate existing limit rule supplies the refusal check; no new catalogue limits are introduced.

### #23175 checks

The 0.50.0/0.51.1 results above remain release observations. The #23175 CI artifact records 25 valid, 27 rejects, 2 rebuild checks and 1 blocked records. The next CI run also checks link overrides and ordinary edit refusal with `enforce_on_edit` where limit rules exist; these new checks are pending. Differences remain differences.

The supplied #23175 artifact includes 0 link checks; the added ordinary-edit enforcement check awaits CI.

The link fixture compares HBLTS5 → HBLTS5-4 (`hole_d`, same HBLTS5 row) against Python builds. Refusal uses the existing `tabs` rule with value 2.
