# misumi.ofb.oil-free-bushing as a parametric SolidCraft generator

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai, and rules addressed by feature name needs #23175 (our draft, being finished). The exact command errors quoted below are observations from SolidCraft 0.50.0. The draft checks ranges on link overrides; ordinary source `parameters.change` still does not enforce range restrictions.

The bushing modelled ONCE in SolidCraft (`oil-free-bushing/oil-free-bushing.sc`), 159 configuration rows (one per type and table row), the ordering code as a field
template and the logic as plain Rhai, following SolidCraft's generator interface (`docs/formats/generator.md`, version 2, issue 22331). The Python generator in `../src` is
untouched and is the reference everything below is compared with.

```
oil-free-bushing/          generator.toml, oil-free-bushing.sc, generator.rhai, tables/*.csv (the 7 data tables, types, params, lists, rows)
build.py rows.py pkgfiles.py   build the model with solidcraft-cli; the rows and tables come from ../data/*.csv
rhai_equiv.py              no SolidCraft: 9130 codes (12 types x bore sizes x lengths, and shape errors) through template + Rhai and through oilfree.parse
run_codes.py report.py faithfulness.py ci.sh   every valid code of the generator both ways (results.json, faithfulness.json)
```

## The model

- Parameters: `od blen bore fl_h fl_t hole_d cb_d cb_t pcd sq_w cp_a cp_f cp_w`, `rowno`; derived hole radii and flange corner points.
- Revolve profiles as alternative features: plain barrel (straight, square and compact flange types) and barrel with shoulder (shouldered, thrust, round flange); square
  and compact flanges are sketches joined to the barrel; a hole set per body variant (round, square, compact), two or four holes by `cp_f` (a `drive_suppression` rule, suppress-if).
- **The free parameter is the length `blen`.** Each row carries its printed lengths as allowed values (one `allow_parameter_values` rule per row, up to 13 values: brackets
  and stars of the catalogue are resolved per wall type and flange by Rhai and by `rows.py`); 163 rules.
- Thin wall types have their own rows (D, N, H, t of the thin columns); rows are named `<type>-<d>`, the default rule of the interface.

## Ordering code

`{otype: C-MUBZU|C-MUBZ|...}{d: text 1..3 [0-9]}\-{l: text 1..3 [0-9]}` (the required separator `\-` and listed values that contain separators were added to
`runtime/fieldtemplate.py`; MG and HFS read the same codes as before) and a fallback `{raw: ...}` template for the shape errors. Every refusal of `oilfree.parse`, in order, with its
message, is in `generator.rhai`; the part description is built in Rhai and equals the Python one for all 784 codes; `fields()` prints the code back (round trip the same for all 784).

**Documented deviation.** Separators ` -_/.` are ignored when a code is read, so a code with a stray space is read where the Python regex refuses it (none in the 9130 tested).

## What was run

`ci.sh` (GitHub CI, SolidCraft 0.50.0): `rhai_equiv.py`, `build.py`, then `run_codes.py`: the 29 valid codes of `codes.txt` and every other valid code (784 in all) ->
Rhai -> row for the code (length set) -> inserted -> `inspect.measure` + the unchanged `src/check.py` -> the same code from the Python generator; the `!` codes and 43 more
refusals; 10 rebuilds (length changed on a built part, compared with the code built directly and with Python).
`oil-free-bushing/oil-free-bushing.sc` is the model CI built (`oil-free-bushing.sc.json` in its output).

## Result: side by side

Volume mm3 / area mm2 / bbox mm / faces. Equal = same bodies, volume and area within 1e-6 relative, same bbox and face count (the rule of `tools/parametric-verdict`).

| code | row | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec python | spec parametric | description same | equal |
|---|---|---|---|---|---|---|---|
| C-MUBZ5-10 | C-MUBZ-5 | 439.8 / 527.8 / 10x9x9 / 4 | 439.8 / 527.8 / 10x9x9 / 4 | 11/11 | 11/11 | yes | yes |
| C-MUBZ20-30 | C-MUBZ-20 | 9047.8 / 5127.1 / 30x28x28 / 4 | 9047.8 / 5127.1 / 30x28x28 / 4 | 11/11 | 11/11 | yes | yes |
| C-MUBZ100-100 | C-MUBZ-100 | 345575.2 / 76026.5 / 100x120x120 / 4 | 345575.2 / 76026.5 / 100x120x120 / 4 | 11/11 | 11/11 | yes | yes |
| C-MUBZU35-15 | C-MUBZU-35 | 4417.9 / 4123.3 / 15x40x40 / 4 | 4417.9 / 4123.3 / 15x40x40 / 4 | 11/11 | 11/11 | yes | yes |
| C-MUBZU12-20 | C-MUBZU-12 | 1272.3 / 1823.7 / 20x15x15 / 4 | 1272.3 / 1823.7 / 20x15x15 / 4 | 11/11 | 11/11 | yes | yes |
| C-MUFZ5-10 | C-MUFZ-5 | 620.5 / 739.8 / 10x14x14 / 6 | 620.5 / 739.8 / 10x14x14 / 6 | 13/13 | 13/13 | yes | yes |
| C-MUFZ100-100 | C-MUFZ-100 | 409192.4 / 89692.5 / 100x150x150 / 6 | 409192.4 / 89692.5 / 100x150x150 / 6 | 13/13 | 13/13 | yes | yes |
| C-MUFZ18-20 | C-MUFZ-18 | 5014.0 / 3813.9 / 20x32x32 / 6 | 5014.0 / 3813.9 / 20x32x32 / 6 | 13/13 | 13/13 | yes | yes |
| C-MUFZU30-30 | C-MUFZU-30 | 7941.9 / 7489.6 / 30x42x42 / 6 | 7941.9 / 7489.6 / 30x42x42 / 6 | 13/13 | 13/13 | yes | yes |
| C-MUFZU12-15 | C-MUFZU-12 | 1463.2 / 1795.4 / 15x21x21 / 6 | 1463.2 / 1795.4 / 15x21x21 / 6 | 13/13 | 13/13 | yes | yes |
| C-MUTZ6-10 | C-MUTZ-6 | 1992.9 / 1700.4 / 10x25x25 / 12 | 1992.9 / 1700.4 / 10x25x25 / 12 | 15/15 | 15/15 | yes | yes |
| C-MUTZ16-30 | C-MUTZ-16 | 9097.3 / 6243.9 / 30x40x40 / 18 | 9097.3 / 6243.9 / 30x40x40 / 18 | 15/15 | 15/15 | yes | yes |
| C-MUTZ50-100 | C-MUTZ-50 | 140341.2 / 47092.5 / 100x94x94 / 18 | 140341.2 / 47092.5 / 100x94x94 / 18 | 15/15 | 15/15 | yes | yes |
| C-MUTSZ6-10 | C-MUTSZ-6 | 1425.2 / 1562.6 / 10x25x25 / 25 | 1425.2 / 1562.6 / 10x25x25 / 25 | 16/16 | 16/16 | yes | yes |
| C-MUTSZ16-40 | C-MUTSZ-16 | 9333.5 / 6774.2 / 40x40x40 / 25 | 9333.5 / 6774.2 / 40x40x40 / 25 | 16/16 | 16/16 | yes | yes |
| C-MUTSZ50-100 | C-MUTSZ-50 | 123349.8 / 43500.4 / 100x94x94 / 25 | 123349.8 / 43500.4 / 100x94x94 / 25 | 16/16 | 16/16 | yes | yes |
| C-MUTNZ6-15 | C-MUTNZ-6 | 1763.6 / 1689.8 / 15x16x25 / 15 | 1763.6 / 1689.8 / 15x16x25 / 15 | 17/17 | 17/17 | yes | yes |
| C-MUTNZ13-25 | C-MUTNZ-13 | 6267.4 / 4328.5 / 25x25x37 / 15 | 6267.4 / 4328.5 / 25x25x37 / 15 | 17/17 | 17/17 | yes | yes |
| C-MUTNZ30-70 | C-MUTNZ-30 | 38929.1 / 19760.7 / 70x44x63 / 21 | 38929.1 / 19760.7 / 70x44x63 / 21 | 17/17 | 17/17 | yes | yes |
| C-MUTNZ50-80 | C-MUTNZ-50 | 107627.2 / 37600.1 / 80x68x94 / 21 | 107627.2 / 37600.1 / 80x68x94 / 21 | 17/17 | 17/17 | yes | yes |
| E-MUGZ10-15 | E-MUGZ-10 | 2707.3 / 2134.7 / 15x25x25 / 6 | 2707.3 / 2134.7 / 15x25x25 / 6 | 12/12 | 12/12 | yes | yes |
| E-MUGZ50-60 | E-MUGZ-50 | 90075.7 / 30611.7 / 60x90x90 / 6 | 90075.7 / 30611.7 / 60x90x90 / 6 | 12/12 | 12/12 | yes | yes |
| E-SHBZ10-12 | E-SHBZ-10 | 904.8 / 1055.6 / 12x14x14 / 4 | 904.8 / 1055.6 / 12x14x14 / 4 | 11/11 | 11/11 | yes | yes |
| E-SHBZ13-20 | E-SHBZ-13 | 3015.9 / 2312.2 / 20x19x19 / 4 | 3015.9 / 2312.2 / 20x19x19 / 4 | 11/11 | 11/11 | yes | yes |
| E-SHFZ8-10 | E-SHFZ-8 | 1030.4 / 1206.4 / 10x20x20 / 6 | 1030.4 / 1206.4 / 10x20x20 / 6 | 13/13 | 13/13 | yes | yes |
| E-SHFZ30-50 | E-SHFZ-30 | 31023.2 / 13665.9 / 50x50x50 / 6 | 31023.2 / 13665.9 / 50x50x50 / 6 | 13/13 | 13/13 | yes | yes |
| E-SHTZ25-35 | E-SHTZ-25 | 20204.3 / 10759.3 / 35x54x54 / 18 | 20204.3 / 10759.3 / 35x54x54 / 18 | 15/15 | 15/15 | yes | yes |
| E-SHTNZ10-25 | E-SHTNZ-10 | 3230.2 / 3040.6 / 25x20x29 / 15 | 3230.2 / 3040.6 / 25x20x29 / 15 | 17/17 | 17/17 | yes | yes |
| E-SHTNZ16-40 | E-SHTNZ-16 | 9706.0 / 6932.4 / 40x28x40 / 21 | 9706.0 / 6932.4 / 40x28x40 / 21 | 17/17 | 17/17 | yes | yes |

Sweep of every other valid code of the generator: 755 codes, identical to the Python part 755/755, same spec check rows and all passed 755/755, same description 755/755.

| rejected code | python message | parametric message | same |
|---|---|---|---|
| C-MUBZ5-20 | C-MUBZ5-20: C-MUBZ5 is offered in L [8, 9, 10, 12, 15] (p.514) | C-MUBZ5-20: C-MUBZ5 is offered in L [8, 9, 10, 12, 15] (p.514) | yes |
| C-MUBZ5-6 | C-MUBZ5-6: C-MUBZ5 is offered in L [8, 9, 10, 12, 15] (L 6 is printed for the thin wall type only) (p.514) | C-MUBZ5-6: C-MUBZ5 is offered in L [8, 9, 10, 12, 15] (L 6 is printed for the thin wall type only) (p.514) | yes |
| C-MUBZU5-9 | C-MUBZU5-9: C-MUBZU5 is offered in L [6, 8, 10, 12] (L 9 is printed for the standard wall type only) (p.514) | C-MUBZU5-9: C-MUBZU5 is offered in L [6, 8, 10, 12] (L 9 is printed for the standard wall type only) (p.514) | yes |
| C-MUBZU32-30 | C-MUBZU32-30: the thin wall type C-MUBZU is not offered for d 32; thin wall d is [5, 6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 35, 40, 50] (p.514) | C-MUBZU32-30: the thin wall type C-MUBZU is not offered for d 32; thin wall d is [5, 6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 35, 40, 50] (p.514) | yes |
| C-MUBZ110-100 | C-MUBZ110-100: C-MUBZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 32, 35, 38, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100] (p.514) | C-MUBZ110-100: C-MUBZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 32, 35, 38, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100] (p.514) | yes |
| C-MUFZU18-20 | C-MUFZU18-20: the thin wall type C-MUFZU is not offered for d 18; thin wall d is [5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30] (p.514) | C-MUFZU18-20: the thin wall type C-MUFZU is not offered for d 18; thin wall d is [5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30] (p.514) | yes |
| C-MUFZ14-10 | C-MUFZ14-10: C-MUFZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100] (p.514) | C-MUFZ14-10: C-MUFZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100] (p.514) | yes |
| C-MUTSZ6-15 | C-MUTSZ6-15: C-MUTSZ6 is offered in L [10, 20] (L 15 is printed in brackets: round and compact flanges only, not the square flange) (p.515) | C-MUTSZ6-15: C-MUTSZ6 is offered in L [10, 20] (L 15 is printed in brackets: round and compact flanges only, not the square flange) (p.515) | yes |
| C-MUTZ60-50 | C-MUTZ60-50: C-MUTZ is offered for I.D. d [6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.515) | C-MUTZ60-50: C-MUTZ is offered for I.D. d [6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.515) | yes |
| E-SHTZ35-40 | E-SHTZ35-40: E-SHTZ is offered for I.D. d [6, 8, 10, 12, 16, 20, 25, 30] (p.520) | E-SHTZ35-40: E-SHTZ is offered for I.D. d [6, 8, 10, 12, 16, 20, 25, 30] (p.520) | yes |
| E-SHBZ32-30 | E-SHBZ32-30: E-SHBZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30] (p.519) | E-SHBZ32-30: E-SHBZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30] (p.519) | yes |
| E-SHFZ18-20 | E-SHFZ18-20: E-SHFZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30] (p.519) | E-SHFZ18-20: E-SHFZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30] (p.519) | yes |
| E-MUGZ6-10 | E-MUGZ6-10: E-MUGZ6 is offered in L [12] (p.516) | E-MUGZ6-10: E-MUGZ6 is offered in L [12] (p.516) | yes |
| E-MUSZ10-15 | 'E-MUSZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | 'E-MUSZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | yes |
| C-MUFZ10 | 'C-MUFZ10': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | 'C-MUFZ10': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | yes |
| C-MUBZ110-100 | C-MUBZ110-100: C-MUBZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 32, 35, 38, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100] (p.514) | C-MUBZ110-100: C-MUBZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 32, 35, 38, 40, 45, 50, 55, 60, 65, 70, 80, 90, 100] (p.514) | yes |
| C-MUBZ5-3 | C-MUBZ5-3: C-MUBZ5 is offered in L [8, 9, 10, 12, 15] (p.514) | C-MUBZ5-3: C-MUBZ5 is offered in L [8, 9, 10, 12, 15] (p.514) | yes |
| C-MUBZ5-11 | C-MUBZ5-11: C-MUBZ5 is offered in L [8, 9, 10, 12, 15] (p.514) | C-MUBZ5-11: C-MUBZ5 is offered in L [8, 9, 10, 12, 15] (p.514) | yes |
| C-MUBZ5-100 | C-MUBZ5-100: C-MUBZ5 is offered in L [8, 9, 10, 12, 15] (p.514) | C-MUBZ5-100: C-MUBZ5 is offered in L [8, 9, 10, 12, 15] (p.514) | yes |
| C-MUBZU32-30 | C-MUBZU32-30: the thin wall type C-MUBZU is not offered for d 32; thin wall d is [5, 6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 35, 40, 50] (p.514) | C-MUBZU32-30: the thin wall type C-MUBZU is not offered for d 32; thin wall d is [5, 6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 35, 40, 50] (p.514) | yes |
| C-MUBZU14-10 | C-MUBZU14-10: C-MUBZU is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 35, 40, 50] (p.514) | C-MUBZU14-10: C-MUBZU is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 35, 40, 50] (p.514) | yes |
| C-MUFZU18-20 | C-MUFZU18-20: the thin wall type C-MUFZU is not offered for d 18; thin wall d is [5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30] (p.514) | C-MUFZU18-20: the thin wall type C-MUFZU is not offered for d 18; thin wall d is [5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30] (p.514) | yes |
| C-MUFZ14-10 | C-MUFZ14-10: C-MUFZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100] (p.514) | C-MUFZ14-10: C-MUFZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100] (p.514) | yes |
| C-MUFZ5-15 | C-MUFZ5-15: C-MUFZ5 is offered in L [8, 10, 12] (p.514) | C-MUFZ5-15: C-MUFZ5 is offered in L [8, 10, 12] (p.514) | yes |
| C-MUFZU6-8 | C-MUFZU6-8: C-MUFZU6 is offered in L [10, 12, 15] (L 8 is printed for the standard wall type only) (p.514) | C-MUFZU6-8: C-MUFZU6 is offered in L [10, 12, 15] (L 8 is printed for the standard wall type only) (p.514) | yes |
| C-MUTSZ6-15 | C-MUTSZ6-15: C-MUTSZ6 is offered in L [10, 20] (L 15 is printed in brackets: round and compact flanges only, not the square flange) (p.515) | C-MUTSZ6-15: C-MUTSZ6 is offered in L [10, 20] (L 15 is printed in brackets: round and compact flanges only, not the square flange) (p.515) | yes |
| C-MUTZ60-50 | C-MUTZ60-50: C-MUTZ is offered for I.D. d [6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.515) | C-MUTZ60-50: C-MUTZ is offered for I.D. d [6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.515) | yes |
| C-MUTNZ20-90 | C-MUTNZ20-90: C-MUTNZ20 is offered in L [20, 25, 30, 35, 40, 50] (p.515) | C-MUTNZ20-90: C-MUTNZ20 is offered in L [20, 25, 30, 35, 40, 50] (p.515) | yes |
| C-MUTNZ18-20 | C-MUTNZ18-20: C-MUTNZ is offered for I.D. d [6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.515) | C-MUTNZ18-20: C-MUTNZ is offered for I.D. d [6, 8, 10, 12, 13, 16, 20, 25, 30, 35, 40, 50] (p.515) | yes |
| E-MUGZ6-10 | E-MUGZ6-10: E-MUGZ6 is offered in L [12] (p.516) | E-MUGZ6-10: E-MUGZ6 is offered in L [12] (p.516) | yes |
| E-MUGZ6-13 | E-MUGZ6-13: E-MUGZ6 is offered in L [12] (p.516) | E-MUGZ6-13: E-MUGZ6 is offered in L [12] (p.516) | yes |
| E-MUGZ14-20 | E-MUGZ14-20: E-MUGZ is offered for I.D. d [6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 40, 50] (p.516) | E-MUGZ14-20: E-MUGZ is offered for I.D. d [6, 8, 10, 12, 13, 15, 16, 18, 20, 25, 30, 40, 50] (p.516) | yes |
| E-SHTZ35-40 | E-SHTZ35-40: E-SHTZ is offered for I.D. d [6, 8, 10, 12, 16, 20, 25, 30] (p.520) | E-SHTZ35-40: E-SHTZ is offered for I.D. d [6, 8, 10, 12, 16, 20, 25, 30] (p.520) | yes |
| E-SHTNZ35-40 | E-SHTNZ35-40: E-SHTNZ is offered for I.D. d [6, 8, 10, 12, 16, 20, 25, 30] (p.520) | E-SHTNZ35-40: E-SHTNZ is offered for I.D. d [6, 8, 10, 12, 16, 20, 25, 30] (p.520) | yes |
| E-SHBZ32-30 | E-SHBZ32-30: E-SHBZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30] (p.519) | E-SHBZ32-30: E-SHBZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30] (p.519) | yes |
| E-SHBZ5-9 | E-SHBZ5-9: E-SHBZ5 is offered in L [8, 10, 12, 15] (p.519) | E-SHBZ5-9: E-SHBZ5 is offered in L [8, 10, 12, 15] (p.519) | yes |
| E-SHFZ18-20 | E-SHFZ18-20: E-SHFZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30] (p.519) | E-SHFZ18-20: E-SHFZ is offered for I.D. d [5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30] (p.519) | yes |
| E-SHFZ5-11 | E-SHFZ5-11: E-SHFZ5 is offered in L [10, 12] (p.519) | E-SHFZ5-11: E-SHFZ5 is offered in L [10, 12] (p.519) | yes |
| E-MUSZ10-15 | 'E-MUSZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | 'E-MUSZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | yes |
| E-MUKZ10-15 | 'E-MUKZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | 'E-MUKZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | yes |
| E-MUCTZ10-15 | 'E-MUCTZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | 'E-MUCTZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | yes |
| E-MUIZ10-15 | 'E-MUIZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | 'E-MUIZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | yes |
| C-MUIZ10-15 | 'C-MUIZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | 'C-MUIZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | yes |
| E-MJBZ10-15 | 'E-MJBZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | 'E-MJBZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | yes |
| E-MGFZ10-15 | 'E-MGFZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | 'E-MGFZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | yes |
| E-MXBZ10-15 | 'E-MXBZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | 'E-MXBZ10-15': this oil free bushing type is not generated (types E-MUSZ, E-MUKZ, E-MUCZ, E-MUCTZ, E-MUIZ, E-MUITZ and the resin types E-MJ.., E-MG.., E-MX.. are on other pages; this generator covers p.514-p.516 and p.519-p.520) | yes |
| C-MUFZ10 | 'C-MUFZ10': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | 'C-MUFZ10': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | yes |
| C-MUFZ-10 | 'C-MUFZ-10': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | 'C-MUFZ-10': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | yes |
| C-MUFZ5- | 'C-MUFZ5-': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | 'C-MUFZ5-': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | yes |
| C-MUTXZ10-20 | 'C-MUTXZ10-20': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | 'C-MUTXZ10-20': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | yes |
| E-SHBZU10-12 | 'E-SHBZU10-12': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | 'E-SHBZU10-12': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | yes |
| E-MUGZ10-15-X | 'E-MUGZ10-15-X': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | 'E-MUGZ10-15-X': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | yes |
| E-LBF20LUU | 'E-LBF20LUU': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | 'E-LBF20LUU': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | yes |
| C-SHA10 | 'C-SHA10': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | 'C-SHA10': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | yes |
| C-MUFZ5 10 | 'C-MUFZ5 10': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | 'C-MUFZ5 10': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | yes |
| E-MUGZ | 'E-MUGZ': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | 'E-MUGZ': expected <type><d>-<L>, type C-MUBZ, C-MUBZU, C-MUFZ, C-MUFZU, C-MUTZ, C-MUTSZ, C-MUTNZ, E-MUGZ, E-SHBZ, E-SHFZ, E-SHTZ or E-SHTNZ, e.g. C-MUFZ5-10, C-MUTNZ6-15, E-SHTZ25-35 | yes |

| built | changed | to | changed in place vol / area / bbox / faces | direct code (inserted) | python | equal |
|---|---|---|---|---|---|---|
| C-MUBZ20-30 | blen | C-MUBZ20-40 | 12063.7 / 6635.0 / 40x28x28 / 4 | 12063.7 / 6635.0 / 40x28x28 / 4 | 12063.7 / 6635.0 / 40x28x28 / 4 | yes |
| C-MUBZU12-20 | blen | C-MUBZU12-25 | 1590.4 / 2247.8 / 25x15x15 / 4 | 1590.4 / 2247.8 / 25x15x15 / 4 | 1590.4 / 2247.8 / 25x15x15 / 4 | yes |
| C-MUFZ5-10 | blen | C-MUFZ5-12 | 708.4 / 827.8 / 12x14x14 / 6 | 708.4 / 827.8 / 12x14x14 / 6 | 708.4 / 827.8 / 12x14x14 / 6 | yes |
| C-MUFZU16-12 | blen | C-MUFZU16-30 | 4043.2 / 4109.2 / 30x26x26 / 6 | 4043.2 / 4109.2 / 30x26x26 / 6 | 4043.2 / 4109.2 / 30x26x26 / 6 | yes |
| C-MUTZ6-10 | blen | C-MUTZ6-20 | 2495.6 / 2203.0 / 20x25x25 / 12 | 2495.6 / 2203.0 / 20x25x25 / 12 | 2495.6 / 2203.0 / 20x25x25 / 12 | yes |
| C-MUTSZ16-40 | blen | C-MUTSZ16-25 | 6647.4 / 4983.5 / 25x40x40 / 25 | 6647.4 / 4983.5 / 25x40x40 / 25 | 6647.4 / 4983.5 / 25x40x40 / 25 | yes |
| C-MUTNZ13-25 | blen | C-MUTNZ13-35 | 7775.4 / 5333.8 / 35x25x37 / 15 | 7775.4 / 5333.8 / 35x25x37 / 15 | 7775.4 / 5333.8 / 35x25x37 / 15 | yes |
| E-MUGZ10-15 | blen | E-MUGZ10-20 | 3319.9 / 2543.1 / 20x25x25 / 6 | 3319.9 / 2543.1 / 20x25x25 / 6 | 3319.9 / 2543.1 / 20x25x25 / 6 | yes |
| E-SHBZ10-12 | blen | E-SHBZ10-25 | 1885.0 / 2035.8 / 25x14x14 / 4 | 1885.0 / 2035.8 / 25x14x14 / 4 | 1885.0 / 2035.8 / 25x14x14 / 4 | yes |
| E-SHTZ25-35 | blen | E-SHTZ25-60 | 29314.9 / 15314.6 / 60x54x54 / 18 | 29314.9 / 15314.6 / 60x54x54 / 18 | 29314.9 / 15314.6 / 60x54x54 / 18 | yes |

| round trip | printed | same configuration and parameters |
|---|---|---|
| C-MUBZ5-10 | C-MUBZ5-10 | yes |
| C-MUBZ20-30 | C-MUBZ20-30 | yes |
| C-MUBZ100-100 | C-MUBZ100-100 | yes |
| C-MUBZU35-15 | C-MUBZU35-15 | yes |
| C-MUBZU12-20 | C-MUBZU12-20 | yes |
| C-MUFZ5-10 | C-MUFZ5-10 | yes |
| C-MUFZ100-100 | C-MUFZ100-100 | yes |
| C-MUFZ18-20 | C-MUFZ18-20 | yes |
| C-MUFZU30-30 | C-MUFZU30-30 | yes |
| C-MUFZU12-15 | C-MUFZU12-15 | yes |
| C-MUTZ6-10 | C-MUTZ6-10 | yes |
| C-MUTZ16-30 | C-MUTZ16-30 | yes |
| C-MUTZ50-100 | C-MUTZ50-100 | yes |
| C-MUTSZ6-10 | C-MUTSZ6-10 | yes |
| C-MUTSZ16-40 | C-MUTSZ16-40 | yes |
| C-MUTSZ50-100 | C-MUTSZ50-100 | yes |
| C-MUTNZ6-15 | C-MUTNZ6-15 | yes |
| C-MUTNZ13-25 | C-MUTNZ13-25 | yes |
| C-MUTNZ30-70 | C-MUTNZ30-70 | yes |
| C-MUTNZ50-80 | C-MUTNZ50-80 | yes |
| E-MUGZ10-15 | E-MUGZ10-15 | yes |
| E-MUGZ50-60 | E-MUGZ50-60 | yes |
| E-SHBZ10-12 | E-SHBZ10-12 | yes |
| E-SHBZ13-20 | E-SHBZ13-20 | yes |
| E-SHFZ8-10 | E-SHFZ8-10 | yes |
| E-SHFZ30-50 | E-SHFZ30-50 | yes |
| E-SHTZ25-35 | E-SHTZ25-35 | yes |
| E-SHTNZ10-25 | E-SHTNZ10-25 | yes |
| E-SHTNZ16-40 | E-SHTNZ16-40 | yes |
| C-MUBZ5-8 | C-MUBZ5-8 | yes |
| C-MUBZ5-9 | C-MUBZ5-9 | yes |
| C-MUBZ5-12 | C-MUBZ5-12 | yes |
| C-MUBZ5-15 | C-MUBZ5-15 | yes |
| C-MUBZ6-8 | C-MUBZ6-8 | yes |
| C-MUBZ6-9 | C-MUBZ6-9 | yes |
| C-MUBZ6-10 | C-MUBZ6-10 | yes |
| C-MUBZ6-12 | C-MUBZ6-12 | yes |
| C-MUBZ6-15 | C-MUBZ6-15 | yes |
| C-MUBZ6-16 | C-MUBZ6-16 | yes |
| C-MUBZ6-19 | C-MUBZ6-19 | yes |
| C-MUBZ6-20 | C-MUBZ6-20 | yes |
| C-MUBZ8-8 | C-MUBZ8-8 | yes |
| C-MUBZ8-9 | C-MUBZ8-9 | yes |
| C-MUBZ8-10 | C-MUBZ8-10 | yes |
| C-MUBZ8-12 | C-MUBZ8-12 | yes |
| C-MUBZ8-15 | C-MUBZ8-15 | yes |
| C-MUBZ8-16 | C-MUBZ8-16 | yes |
| C-MUBZ8-19 | C-MUBZ8-19 | yes |
| C-MUBZ8-20 | C-MUBZ8-20 | yes |
| C-MUBZ8-25 | C-MUBZ8-25 | yes |
| C-MUBZ10-8 | C-MUBZ10-8 | yes |
| C-MUBZ10-9 | C-MUBZ10-9 | yes |
| C-MUBZ10-10 | C-MUBZ10-10 | yes |
| C-MUBZ10-12 | C-MUBZ10-12 | yes |
| C-MUBZ10-15 | C-MUBZ10-15 | yes |
| C-MUBZ10-16 | C-MUBZ10-16 | yes |
| C-MUBZ10-19 | C-MUBZ10-19 | yes |
| C-MUBZ10-20 | C-MUBZ10-20 | yes |
| C-MUBZ10-25 | C-MUBZ10-25 | yes |
| C-MUBZ10-30 | C-MUBZ10-30 | yes |
| C-MUBZ12-8 | C-MUBZ12-8 | yes |
| C-MUBZ12-9 | C-MUBZ12-9 | yes |
| C-MUBZ12-10 | C-MUBZ12-10 | yes |
| C-MUBZ12-12 | C-MUBZ12-12 | yes |
| C-MUBZ12-15 | C-MUBZ12-15 | yes |
| C-MUBZ12-16 | C-MUBZ12-16 | yes |
| C-MUBZ12-19 | C-MUBZ12-19 | yes |
| C-MUBZ12-20 | C-MUBZ12-20 | yes |
| C-MUBZ12-25 | C-MUBZ12-25 | yes |
| C-MUBZ12-30 | C-MUBZ12-30 | yes |
| C-MUBZ12-35 | C-MUBZ12-35 | yes |
| C-MUBZ13-9 | C-MUBZ13-9 | yes |
| C-MUBZ13-10 | C-MUBZ13-10 | yes |
| C-MUBZ13-12 | C-MUBZ13-12 | yes |
| C-MUBZ13-15 | C-MUBZ13-15 | yes |
| C-MUBZ13-16 | C-MUBZ13-16 | yes |
| C-MUBZ13-19 | C-MUBZ13-19 | yes |
| C-MUBZ13-20 | C-MUBZ13-20 | yes |
| C-MUBZ13-25 | C-MUBZ13-25 | yes |
| C-MUBZ13-30 | C-MUBZ13-30 | yes |
| C-MUBZ13-35 | C-MUBZ13-35 | yes |
| C-MUBZ15-9 | C-MUBZ15-9 | yes |
| C-MUBZ15-10 | C-MUBZ15-10 | yes |
| C-MUBZ15-12 | C-MUBZ15-12 | yes |
| C-MUBZ15-15 | C-MUBZ15-15 | yes |
| C-MUBZ15-16 | C-MUBZ15-16 | yes |
| C-MUBZ15-19 | C-MUBZ15-19 | yes |
| C-MUBZ15-20 | C-MUBZ15-20 | yes |
| C-MUBZ15-25 | C-MUBZ15-25 | yes |
| C-MUBZ15-30 | C-MUBZ15-30 | yes |
| C-MUBZ15-35 | C-MUBZ15-35 | yes |
| C-MUBZ15-40 | C-MUBZ15-40 | yes |
| C-MUBZ16-9 | C-MUBZ16-9 | yes |
| C-MUBZ16-10 | C-MUBZ16-10 | yes |
| C-MUBZ16-12 | C-MUBZ16-12 | yes |
| C-MUBZ16-15 | C-MUBZ16-15 | yes |
| C-MUBZ16-16 | C-MUBZ16-16 | yes |
| C-MUBZ16-19 | C-MUBZ16-19 | yes |
| C-MUBZ16-20 | C-MUBZ16-20 | yes |
| C-MUBZ16-25 | C-MUBZ16-25 | yes |
| C-MUBZ16-30 | C-MUBZ16-30 | yes |
| C-MUBZ16-35 | C-MUBZ16-35 | yes |
| C-MUBZ16-40 | C-MUBZ16-40 | yes |
| C-MUBZ18-9 | C-MUBZ18-9 | yes |
| C-MUBZ18-10 | C-MUBZ18-10 | yes |
| C-MUBZ18-12 | C-MUBZ18-12 | yes |
| C-MUBZ18-15 | C-MUBZ18-15 | yes |
| C-MUBZ18-16 | C-MUBZ18-16 | yes |
| C-MUBZ18-19 | C-MUBZ18-19 | yes |
| C-MUBZ18-20 | C-MUBZ18-20 | yes |
| C-MUBZ18-25 | C-MUBZ18-25 | yes |
| C-MUBZ18-30 | C-MUBZ18-30 | yes |
| C-MUBZ18-35 | C-MUBZ18-35 | yes |
| C-MUBZ18-40 | C-MUBZ18-40 | yes |
| C-MUBZ20-9 | C-MUBZ20-9 | yes |
| C-MUBZ20-10 | C-MUBZ20-10 | yes |
| C-MUBZ20-12 | C-MUBZ20-12 | yes |
| C-MUBZ20-15 | C-MUBZ20-15 | yes |
| C-MUBZ20-16 | C-MUBZ20-16 | yes |
| C-MUBZ20-19 | C-MUBZ20-19 | yes |
| C-MUBZ20-20 | C-MUBZ20-20 | yes |
| C-MUBZ20-25 | C-MUBZ20-25 | yes |
| C-MUBZ20-35 | C-MUBZ20-35 | yes |
| C-MUBZ20-40 | C-MUBZ20-40 | yes |
| C-MUBZ20-50 | C-MUBZ20-50 | yes |
| C-MUBZ20-60 | C-MUBZ20-60 | yes |
| C-MUBZ25-12 | C-MUBZ25-12 | yes |
| C-MUBZ25-15 | C-MUBZ25-15 | yes |
| C-MUBZ25-16 | C-MUBZ25-16 | yes |
| C-MUBZ25-19 | C-MUBZ25-19 | yes |
| C-MUBZ25-20 | C-MUBZ25-20 | yes |
| C-MUBZ25-25 | C-MUBZ25-25 | yes |
| C-MUBZ25-30 | C-MUBZ25-30 | yes |
| C-MUBZ25-35 | C-MUBZ25-35 | yes |
| C-MUBZ25-40 | C-MUBZ25-40 | yes |
| C-MUBZ25-50 | C-MUBZ25-50 | yes |
| C-MUBZ25-60 | C-MUBZ25-60 | yes |
| C-MUBZ30-12 | C-MUBZ30-12 | yes |
| C-MUBZ30-15 | C-MUBZ30-15 | yes |
| C-MUBZ30-16 | C-MUBZ30-16 | yes |
| C-MUBZ30-19 | C-MUBZ30-19 | yes |
| C-MUBZ30-20 | C-MUBZ30-20 | yes |
| C-MUBZ30-25 | C-MUBZ30-25 | yes |
| C-MUBZ30-30 | C-MUBZ30-30 | yes |
| C-MUBZ30-35 | C-MUBZ30-35 | yes |
| C-MUBZ30-40 | C-MUBZ30-40 | yes |
| C-MUBZ30-50 | C-MUBZ30-50 | yes |
| C-MUBZ30-60 | C-MUBZ30-60 | yes |
| C-MUBZ30-70 | C-MUBZ30-70 | yes |
| C-MUBZ32-20 | C-MUBZ32-20 | yes |
| C-MUBZ32-30 | C-MUBZ32-30 | yes |
| C-MUBZ32-40 | C-MUBZ32-40 | yes |
| C-MUBZ35-20 | C-MUBZ35-20 | yes |
| C-MUBZ35-25 | C-MUBZ35-25 | yes |
| C-MUBZ35-30 | C-MUBZ35-30 | yes |
| C-MUBZ35-35 | C-MUBZ35-35 | yes |
| C-MUBZ35-40 | C-MUBZ35-40 | yes |
| C-MUBZ35-50 | C-MUBZ35-50 | yes |
| C-MUBZ35-60 | C-MUBZ35-60 | yes |
| C-MUBZ35-70 | C-MUBZ35-70 | yes |
| C-MUBZ38-40 | C-MUBZ38-40 | yes |
| C-MUBZ40-20 | C-MUBZ40-20 | yes |
| C-MUBZ40-25 | C-MUBZ40-25 | yes |
| C-MUBZ40-30 | C-MUBZ40-30 | yes |
| C-MUBZ40-35 | C-MUBZ40-35 | yes |
| C-MUBZ40-40 | C-MUBZ40-40 | yes |
| C-MUBZ40-50 | C-MUBZ40-50 | yes |
| C-MUBZ40-60 | C-MUBZ40-60 | yes |
| C-MUBZ40-70 | C-MUBZ40-70 | yes |
| C-MUBZ40-80 | C-MUBZ40-80 | yes |
| C-MUBZ45-30 | C-MUBZ45-30 | yes |
| C-MUBZ45-35 | C-MUBZ45-35 | yes |
| C-MUBZ45-40 | C-MUBZ45-40 | yes |
| C-MUBZ45-50 | C-MUBZ45-50 | yes |
| C-MUBZ45-60 | C-MUBZ45-60 | yes |
| C-MUBZ50-30 | C-MUBZ50-30 | yes |
| C-MUBZ50-35 | C-MUBZ50-35 | yes |
| C-MUBZ50-40 | C-MUBZ50-40 | yes |
| C-MUBZ50-50 | C-MUBZ50-50 | yes |
| C-MUBZ50-60 | C-MUBZ50-60 | yes |
| C-MUBZ50-70 | C-MUBZ50-70 | yes |
| C-MUBZ50-80 | C-MUBZ50-80 | yes |
| C-MUBZ55-30 | C-MUBZ55-30 | yes |
| C-MUBZ55-35 | C-MUBZ55-35 | yes |
| C-MUBZ55-40 | C-MUBZ55-40 | yes |
| C-MUBZ55-50 | C-MUBZ55-50 | yes |
| C-MUBZ55-60 | C-MUBZ55-60 | yes |
| C-MUBZ55-70 | C-MUBZ55-70 | yes |
| C-MUBZ60-50 | C-MUBZ60-50 | yes |
| C-MUBZ60-60 | C-MUBZ60-60 | yes |
| C-MUBZ60-70 | C-MUBZ60-70 | yes |
| C-MUBZ60-80 | C-MUBZ60-80 | yes |
| C-MUBZ65-50 | C-MUBZ65-50 | yes |
| C-MUBZ65-60 | C-MUBZ65-60 | yes |
| C-MUBZ65-70 | C-MUBZ65-70 | yes |
| C-MUBZ65-80 | C-MUBZ65-80 | yes |
| C-MUBZ70-50 | C-MUBZ70-50 | yes |
| C-MUBZ70-60 | C-MUBZ70-60 | yes |
| C-MUBZ70-70 | C-MUBZ70-70 | yes |
| C-MUBZ70-80 | C-MUBZ70-80 | yes |
| C-MUBZ80-50 | C-MUBZ80-50 | yes |
| C-MUBZ80-60 | C-MUBZ80-60 | yes |
| C-MUBZ80-70 | C-MUBZ80-70 | yes |
| C-MUBZ80-80 | C-MUBZ80-80 | yes |
| C-MUBZ90-80 | C-MUBZ90-80 | yes |
| C-MUBZ90-90 | C-MUBZ90-90 | yes |
| C-MUBZ100-80 | C-MUBZ100-80 | yes |
| C-MUBZU5-6 | C-MUBZU5-6 | yes |
| C-MUBZU5-8 | C-MUBZU5-8 | yes |
| C-MUBZU5-10 | C-MUBZU5-10 | yes |
| C-MUBZU5-12 | C-MUBZU5-12 | yes |
| C-MUBZU6-6 | C-MUBZU6-6 | yes |
| C-MUBZU6-8 | C-MUBZU6-8 | yes |
| C-MUBZU6-10 | C-MUBZU6-10 | yes |
| C-MUBZU6-12 | C-MUBZU6-12 | yes |
| C-MUBZU6-15 | C-MUBZU6-15 | yes |
| C-MUBZU6-16 | C-MUBZU6-16 | yes |
| C-MUBZU8-6 | C-MUBZU8-6 | yes |
| C-MUBZU8-8 | C-MUBZU8-8 | yes |
| C-MUBZU8-10 | C-MUBZU8-10 | yes |
| C-MUBZU8-12 | C-MUBZU8-12 | yes |
| C-MUBZU8-15 | C-MUBZU8-15 | yes |
| C-MUBZU8-16 | C-MUBZU8-16 | yes |
| C-MUBZU8-20 | C-MUBZU8-20 | yes |
| C-MUBZU10-8 | C-MUBZU10-8 | yes |
| C-MUBZU10-10 | C-MUBZU10-10 | yes |
| C-MUBZU10-12 | C-MUBZU10-12 | yes |
| C-MUBZU10-15 | C-MUBZU10-15 | yes |
| C-MUBZU10-16 | C-MUBZU10-16 | yes |
| C-MUBZU10-20 | C-MUBZU10-20 | yes |
| C-MUBZU10-25 | C-MUBZU10-25 | yes |
| C-MUBZU12-8 | C-MUBZU12-8 | yes |
| C-MUBZU12-10 | C-MUBZU12-10 | yes |
| C-MUBZU12-12 | C-MUBZU12-12 | yes |
| C-MUBZU12-15 | C-MUBZU12-15 | yes |
| C-MUBZU12-16 | C-MUBZU12-16 | yes |
| C-MUBZU12-25 | C-MUBZU12-25 | yes |
| C-MUBZU13-8 | C-MUBZU13-8 | yes |
| C-MUBZU13-10 | C-MUBZU13-10 | yes |
| C-MUBZU13-12 | C-MUBZU13-12 | yes |
| C-MUBZU13-15 | C-MUBZU13-15 | yes |
| C-MUBZU13-16 | C-MUBZU13-16 | yes |
| C-MUBZU13-20 | C-MUBZU13-20 | yes |
| C-MUBZU13-25 | C-MUBZU13-25 | yes |
| C-MUBZU15-8 | C-MUBZU15-8 | yes |
| C-MUBZU15-10 | C-MUBZU15-10 | yes |
| C-MUBZU15-12 | C-MUBZU15-12 | yes |
| C-MUBZU15-15 | C-MUBZU15-15 | yes |
| C-MUBZU15-16 | C-MUBZU15-16 | yes |
| C-MUBZU15-20 | C-MUBZU15-20 | yes |
| C-MUBZU15-25 | C-MUBZU15-25 | yes |
| C-MUBZU15-30 | C-MUBZU15-30 | yes |
| C-MUBZU16-10 | C-MUBZU16-10 | yes |
| C-MUBZU16-12 | C-MUBZU16-12 | yes |
| C-MUBZU16-15 | C-MUBZU16-15 | yes |
| C-MUBZU16-16 | C-MUBZU16-16 | yes |
| C-MUBZU16-20 | C-MUBZU16-20 | yes |
| C-MUBZU16-25 | C-MUBZU16-25 | yes |
| C-MUBZU16-30 | C-MUBZU16-30 | yes |
| C-MUBZU18-10 | C-MUBZU18-10 | yes |
| C-MUBZU18-12 | C-MUBZU18-12 | yes |
| C-MUBZU18-15 | C-MUBZU18-15 | yes |
| C-MUBZU18-16 | C-MUBZU18-16 | yes |
| C-MUBZU18-20 | C-MUBZU18-20 | yes |
| C-MUBZU18-25 | C-MUBZU18-25 | yes |
| C-MUBZU18-30 | C-MUBZU18-30 | yes |
| C-MUBZU20-12 | C-MUBZU20-12 | yes |
| C-MUBZU20-15 | C-MUBZU20-15 | yes |
| C-MUBZU20-16 | C-MUBZU20-16 | yes |
| C-MUBZU20-20 | C-MUBZU20-20 | yes |
| C-MUBZU20-25 | C-MUBZU20-25 | yes |
| C-MUBZU20-30 | C-MUBZU20-30 | yes |
| C-MUBZU20-40 | C-MUBZU20-40 | yes |
| C-MUBZU25-15 | C-MUBZU25-15 | yes |
| C-MUBZU25-16 | C-MUBZU25-16 | yes |
| C-MUBZU25-20 | C-MUBZU25-20 | yes |
| C-MUBZU25-25 | C-MUBZU25-25 | yes |
| C-MUBZU25-30 | C-MUBZU25-30 | yes |
| C-MUBZU25-40 | C-MUBZU25-40 | yes |
| C-MUBZU30-15 | C-MUBZU30-15 | yes |
| C-MUBZU30-16 | C-MUBZU30-16 | yes |
| C-MUBZU30-20 | C-MUBZU30-20 | yes |
| C-MUBZU30-25 | C-MUBZU30-25 | yes |
| C-MUBZU30-30 | C-MUBZU30-30 | yes |
| C-MUBZU30-40 | C-MUBZU30-40 | yes |
| C-MUBZU35-16 | C-MUBZU35-16 | yes |
| C-MUBZU35-20 | C-MUBZU35-20 | yes |
| C-MUBZU35-25 | C-MUBZU35-25 | yes |
| C-MUBZU35-30 | C-MUBZU35-30 | yes |
| C-MUBZU35-40 | C-MUBZU35-40 | yes |
| C-MUBZU40-15 | C-MUBZU40-15 | yes |
| C-MUBZU40-16 | C-MUBZU40-16 | yes |
| C-MUBZU40-20 | C-MUBZU40-20 | yes |
| C-MUBZU40-25 | C-MUBZU40-25 | yes |
| C-MUBZU40-30 | C-MUBZU40-30 | yes |
| C-MUBZU40-40 | C-MUBZU40-40 | yes |
| C-MUBZU40-50 | C-MUBZU40-50 | yes |
| C-MUBZU50-30 | C-MUBZU50-30 | yes |
| C-MUBZU50-40 | C-MUBZU50-40 | yes |
| C-MUBZU50-50 | C-MUBZU50-50 | yes |
| C-MUBZU50-60 | C-MUBZU50-60 | yes |
| C-MUFZ5-8 | C-MUFZ5-8 | yes |
| C-MUFZ5-12 | C-MUFZ5-12 | yes |
| C-MUFZ6-8 | C-MUFZ6-8 | yes |
| C-MUFZ6-10 | C-MUFZ6-10 | yes |
| C-MUFZ6-12 | C-MUFZ6-12 | yes |
| C-MUFZ6-15 | C-MUFZ6-15 | yes |
| C-MUFZ8-8 | C-MUFZ8-8 | yes |
| C-MUFZ8-10 | C-MUFZ8-10 | yes |
| C-MUFZ8-12 | C-MUFZ8-12 | yes |
| C-MUFZ8-15 | C-MUFZ8-15 | yes |
| C-MUFZ8-20 | C-MUFZ8-20 | yes |
| C-MUFZ10-8 | C-MUFZ10-8 | yes |
| C-MUFZ10-10 | C-MUFZ10-10 | yes |
| C-MUFZ10-12 | C-MUFZ10-12 | yes |
| C-MUFZ10-15 | C-MUFZ10-15 | yes |
| C-MUFZ10-20 | C-MUFZ10-20 | yes |
| C-MUFZ10-25 | C-MUFZ10-25 | yes |
| C-MUFZ10-30 | C-MUFZ10-30 | yes |
| C-MUFZ12-8 | C-MUFZ12-8 | yes |
| C-MUFZ12-10 | C-MUFZ12-10 | yes |
| C-MUFZ12-12 | C-MUFZ12-12 | yes |
| C-MUFZ12-15 | C-MUFZ12-15 | yes |
| C-MUFZ12-20 | C-MUFZ12-20 | yes |
| C-MUFZ12-25 | C-MUFZ12-25 | yes |
| C-MUFZ12-30 | C-MUFZ12-30 | yes |
| C-MUFZ13-10 | C-MUFZ13-10 | yes |
| C-MUFZ13-12 | C-MUFZ13-12 | yes |
| C-MUFZ13-15 | C-MUFZ13-15 | yes |
| C-MUFZ13-20 | C-MUFZ13-20 | yes |
| C-MUFZ13-25 | C-MUFZ13-25 | yes |
| C-MUFZ13-30 | C-MUFZ13-30 | yes |
| C-MUFZ15-10 | C-MUFZ15-10 | yes |
| C-MUFZ15-12 | C-MUFZ15-12 | yes |
| C-MUFZ15-15 | C-MUFZ15-15 | yes |
| C-MUFZ15-20 | C-MUFZ15-20 | yes |
| C-MUFZ15-25 | C-MUFZ15-25 | yes |
| C-MUFZ15-30 | C-MUFZ15-30 | yes |
| C-MUFZ16-12 | C-MUFZ16-12 | yes |
| C-MUFZ16-15 | C-MUFZ16-15 | yes |
| C-MUFZ16-20 | C-MUFZ16-20 | yes |
| C-MUFZ16-25 | C-MUFZ16-25 | yes |
| C-MUFZ16-30 | C-MUFZ16-30 | yes |
| C-MUFZ16-35 | C-MUFZ16-35 | yes |
| C-MUFZ16-40 | C-MUFZ16-40 | yes |
| C-MUFZ18-12 | C-MUFZ18-12 | yes |
| C-MUFZ18-15 | C-MUFZ18-15 | yes |
| C-MUFZ18-25 | C-MUFZ18-25 | yes |
| C-MUFZ18-30 | C-MUFZ18-30 | yes |
| C-MUFZ18-35 | C-MUFZ18-35 | yes |
| C-MUFZ18-40 | C-MUFZ18-40 | yes |
| C-MUFZ20-12 | C-MUFZ20-12 | yes |
| C-MUFZ20-15 | C-MUFZ20-15 | yes |
| C-MUFZ20-20 | C-MUFZ20-20 | yes |
| C-MUFZ20-25 | C-MUFZ20-25 | yes |
| C-MUFZ20-30 | C-MUFZ20-30 | yes |
| C-MUFZ20-35 | C-MUFZ20-35 | yes |
| C-MUFZ20-40 | C-MUFZ20-40 | yes |
| C-MUFZ25-15 | C-MUFZ25-15 | yes |
| C-MUFZ25-20 | C-MUFZ25-20 | yes |
| C-MUFZ25-25 | C-MUFZ25-25 | yes |
| C-MUFZ25-30 | C-MUFZ25-30 | yes |
| C-MUFZ25-35 | C-MUFZ25-35 | yes |
| C-MUFZ25-40 | C-MUFZ25-40 | yes |
| C-MUFZ25-50 | C-MUFZ25-50 | yes |
| C-MUFZ25-60 | C-MUFZ25-60 | yes |
| C-MUFZ30-20 | C-MUFZ30-20 | yes |
| C-MUFZ30-25 | C-MUFZ30-25 | yes |
| C-MUFZ30-30 | C-MUFZ30-30 | yes |
| C-MUFZ30-35 | C-MUFZ30-35 | yes |
| C-MUFZ30-40 | C-MUFZ30-40 | yes |
| C-MUFZ30-50 | C-MUFZ30-50 | yes |
| C-MUFZ30-60 | C-MUFZ30-60 | yes |
| C-MUFZ35-20 | C-MUFZ35-20 | yes |
| C-MUFZ35-25 | C-MUFZ35-25 | yes |
| C-MUFZ35-30 | C-MUFZ35-30 | yes |
| C-MUFZ35-35 | C-MUFZ35-35 | yes |
| C-MUFZ35-40 | C-MUFZ35-40 | yes |
| C-MUFZ35-50 | C-MUFZ35-50 | yes |
| C-MUFZ35-60 | C-MUFZ35-60 | yes |
| C-MUFZ40-20 | C-MUFZ40-20 | yes |
| C-MUFZ40-25 | C-MUFZ40-25 | yes |
| C-MUFZ40-30 | C-MUFZ40-30 | yes |
| C-MUFZ40-35 | C-MUFZ40-35 | yes |
| C-MUFZ40-40 | C-MUFZ40-40 | yes |
| C-MUFZ40-50 | C-MUFZ40-50 | yes |
| C-MUFZ40-60 | C-MUFZ40-60 | yes |
| C-MUFZ45-30 | C-MUFZ45-30 | yes |
| C-MUFZ45-35 | C-MUFZ45-35 | yes |
| C-MUFZ45-40 | C-MUFZ45-40 | yes |
| C-MUFZ45-50 | C-MUFZ45-50 | yes |
| C-MUFZ45-60 | C-MUFZ45-60 | yes |
| C-MUFZ50-30 | C-MUFZ50-30 | yes |
| C-MUFZ50-35 | C-MUFZ50-35 | yes |
| C-MUFZ50-40 | C-MUFZ50-40 | yes |
| C-MUFZ50-50 | C-MUFZ50-50 | yes |
| C-MUFZ50-60 | C-MUFZ50-60 | yes |
| C-MUFZ60-40 | C-MUFZ60-40 | yes |
| C-MUFZ60-50 | C-MUFZ60-50 | yes |
| C-MUFZ60-60 | C-MUFZ60-60 | yes |
| C-MUFZ60-80 | C-MUFZ60-80 | yes |
| C-MUFZ70-50 | C-MUFZ70-50 | yes |
| C-MUFZ70-80 | C-MUFZ70-80 | yes |
| C-MUFZ80-60 | C-MUFZ80-60 | yes |
| C-MUFZ80-80 | C-MUFZ80-80 | yes |
| C-MUFZ80-100 | C-MUFZ80-100 | yes |
| C-MUFZ90-60 | C-MUFZ90-60 | yes |
| C-MUFZ90-80 | C-MUFZ90-80 | yes |
| C-MUFZ100-80 | C-MUFZ100-80 | yes |
| C-MUFZU5-10 | C-MUFZU5-10 | yes |
| C-MUFZU5-12 | C-MUFZU5-12 | yes |
| C-MUFZU6-10 | C-MUFZU6-10 | yes |
| C-MUFZU6-12 | C-MUFZU6-12 | yes |
| C-MUFZU6-15 | C-MUFZU6-15 | yes |
| C-MUFZU8-10 | C-MUFZU8-10 | yes |
| C-MUFZU8-12 | C-MUFZU8-12 | yes |
| C-MUFZU8-15 | C-MUFZU8-15 | yes |
| C-MUFZU8-20 | C-MUFZU8-20 | yes |
| C-MUFZU10-10 | C-MUFZU10-10 | yes |
| C-MUFZU10-12 | C-MUFZU10-12 | yes |
| C-MUFZU10-15 | C-MUFZU10-15 | yes |
| C-MUFZU10-20 | C-MUFZU10-20 | yes |
| C-MUFZU12-10 | C-MUFZU12-10 | yes |
| C-MUFZU12-12 | C-MUFZU12-12 | yes |
| C-MUFZU12-20 | C-MUFZU12-20 | yes |
| C-MUFZU12-25 | C-MUFZU12-25 | yes |
| C-MUFZU12-30 | C-MUFZU12-30 | yes |
| C-MUFZU13-12 | C-MUFZU13-12 | yes |
| C-MUFZU13-15 | C-MUFZU13-15 | yes |
| C-MUFZU13-20 | C-MUFZU13-20 | yes |
| C-MUFZU15-10 | C-MUFZU15-10 | yes |
| C-MUFZU15-12 | C-MUFZU15-12 | yes |
| C-MUFZU15-15 | C-MUFZU15-15 | yes |
| C-MUFZU15-20 | C-MUFZU15-20 | yes |
| C-MUFZU15-25 | C-MUFZU15-25 | yes |
| C-MUFZU16-12 | C-MUFZU16-12 | yes |
| C-MUFZU16-15 | C-MUFZU16-15 | yes |
| C-MUFZU16-20 | C-MUFZU16-20 | yes |
| C-MUFZU16-25 | C-MUFZU16-25 | yes |
| C-MUFZU16-30 | C-MUFZU16-30 | yes |
| C-MUFZU20-15 | C-MUFZU20-15 | yes |
| C-MUFZU20-20 | C-MUFZU20-20 | yes |
| C-MUFZU20-25 | C-MUFZU20-25 | yes |
| C-MUFZU20-30 | C-MUFZU20-30 | yes |
| C-MUFZU20-40 | C-MUFZU20-40 | yes |
| C-MUFZU25-30 | C-MUFZU25-30 | yes |
| C-MUFZU25-40 | C-MUFZU25-40 | yes |
| C-MUFZU25-50 | C-MUFZU25-50 | yes |
| C-MUFZU30-40 | C-MUFZU30-40 | yes |
| C-MUFZU30-50 | C-MUFZU30-50 | yes |
| C-MUTZ6-15 | C-MUTZ6-15 | yes |
| C-MUTZ6-20 | C-MUTZ6-20 | yes |
| C-MUTZ8-15 | C-MUTZ8-15 | yes |
| C-MUTZ8-20 | C-MUTZ8-20 | yes |
| C-MUTZ8-25 | C-MUTZ8-25 | yes |
| C-MUTZ10-15 | C-MUTZ10-15 | yes |
| C-MUTZ10-20 | C-MUTZ10-20 | yes |
| C-MUTZ10-25 | C-MUTZ10-25 | yes |
| C-MUTZ10-30 | C-MUTZ10-30 | yes |
| C-MUTZ12-15 | C-MUTZ12-15 | yes |
| C-MUTZ12-20 | C-MUTZ12-20 | yes |
| C-MUTZ12-25 | C-MUTZ12-25 | yes |
| C-MUTZ12-30 | C-MUTZ12-30 | yes |
| C-MUTZ13-20 | C-MUTZ13-20 | yes |
| C-MUTZ13-25 | C-MUTZ13-25 | yes |
| C-MUTZ13-30 | C-MUTZ13-30 | yes |
| C-MUTZ13-35 | C-MUTZ13-35 | yes |
| C-MUTZ16-20 | C-MUTZ16-20 | yes |
| C-MUTZ16-25 | C-MUTZ16-25 | yes |
| C-MUTZ16-35 | C-MUTZ16-35 | yes |
| C-MUTZ16-40 | C-MUTZ16-40 | yes |
| C-MUTZ20-20 | C-MUTZ20-20 | yes |
| C-MUTZ20-25 | C-MUTZ20-25 | yes |
| C-MUTZ20-30 | C-MUTZ20-30 | yes |
| C-MUTZ20-35 | C-MUTZ20-35 | yes |
| C-MUTZ20-40 | C-MUTZ20-40 | yes |
| C-MUTZ20-50 | C-MUTZ20-50 | yes |
| C-MUTZ25-25 | C-MUTZ25-25 | yes |
| C-MUTZ25-30 | C-MUTZ25-30 | yes |
| C-MUTZ25-35 | C-MUTZ25-35 | yes |
| C-MUTZ25-40 | C-MUTZ25-40 | yes |
| C-MUTZ25-50 | C-MUTZ25-50 | yes |
| C-MUTZ25-60 | C-MUTZ25-60 | yes |
| C-MUTZ30-30 | C-MUTZ30-30 | yes |
| C-MUTZ30-35 | C-MUTZ30-35 | yes |
| C-MUTZ30-40 | C-MUTZ30-40 | yes |
| C-MUTZ30-50 | C-MUTZ30-50 | yes |
| C-MUTZ30-60 | C-MUTZ30-60 | yes |
| C-MUTZ30-70 | C-MUTZ30-70 | yes |
| C-MUTZ35-35 | C-MUTZ35-35 | yes |
| C-MUTZ35-40 | C-MUTZ35-40 | yes |
| C-MUTZ35-50 | C-MUTZ35-50 | yes |
| C-MUTZ35-60 | C-MUTZ35-60 | yes |
| C-MUTZ35-70 | C-MUTZ35-70 | yes |
| C-MUTZ40-40 | C-MUTZ40-40 | yes |
| C-MUTZ40-50 | C-MUTZ40-50 | yes |
| C-MUTZ40-60 | C-MUTZ40-60 | yes |
| C-MUTZ40-70 | C-MUTZ40-70 | yes |
| C-MUTZ40-80 | C-MUTZ40-80 | yes |
| C-MUTZ50-50 | C-MUTZ50-50 | yes |
| C-MUTZ50-60 | C-MUTZ50-60 | yes |
| C-MUTZ50-70 | C-MUTZ50-70 | yes |
| C-MUTZ50-80 | C-MUTZ50-80 | yes |
| C-MUTSZ6-20 | C-MUTSZ6-20 | yes |
| C-MUTSZ8-15 | C-MUTSZ8-15 | yes |
| C-MUTSZ8-25 | C-MUTSZ8-25 | yes |
| C-MUTSZ10-15 | C-MUTSZ10-15 | yes |
| C-MUTSZ10-20 | C-MUTSZ10-20 | yes |
| C-MUTSZ10-30 | C-MUTSZ10-30 | yes |
| C-MUTSZ12-15 | C-MUTSZ12-15 | yes |
| C-MUTSZ12-20 | C-MUTSZ12-20 | yes |
| C-MUTSZ12-25 | C-MUTSZ12-25 | yes |
| C-MUTSZ12-30 | C-MUTSZ12-30 | yes |
| C-MUTSZ13-20 | C-MUTSZ13-20 | yes |
| C-MUTSZ13-25 | C-MUTSZ13-25 | yes |
| C-MUTSZ13-30 | C-MUTSZ13-30 | yes |
| C-MUTSZ13-35 | C-MUTSZ13-35 | yes |
| C-MUTSZ16-20 | C-MUTSZ16-20 | yes |
| C-MUTSZ16-25 | C-MUTSZ16-25 | yes |
| C-MUTSZ16-30 | C-MUTSZ16-30 | yes |
| C-MUTSZ16-35 | C-MUTSZ16-35 | yes |
| C-MUTSZ20-20 | C-MUTSZ20-20 | yes |
| C-MUTSZ20-25 | C-MUTSZ20-25 | yes |
| C-MUTSZ20-30 | C-MUTSZ20-30 | yes |
| C-MUTSZ20-35 | C-MUTSZ20-35 | yes |
| C-MUTSZ20-40 | C-MUTSZ20-40 | yes |
| C-MUTSZ20-50 | C-MUTSZ20-50 | yes |
| C-MUTSZ25-25 | C-MUTSZ25-25 | yes |
| C-MUTSZ25-30 | C-MUTSZ25-30 | yes |
| C-MUTSZ25-35 | C-MUTSZ25-35 | yes |
| C-MUTSZ25-40 | C-MUTSZ25-40 | yes |
| C-MUTSZ25-50 | C-MUTSZ25-50 | yes |
| C-MUTSZ25-60 | C-MUTSZ25-60 | yes |
| C-MUTSZ30-30 | C-MUTSZ30-30 | yes |
| C-MUTSZ30-35 | C-MUTSZ30-35 | yes |
| C-MUTSZ30-40 | C-MUTSZ30-40 | yes |
| C-MUTSZ30-50 | C-MUTSZ30-50 | yes |
| C-MUTSZ30-60 | C-MUTSZ30-60 | yes |
| C-MUTSZ30-70 | C-MUTSZ30-70 | yes |
| C-MUTSZ35-35 | C-MUTSZ35-35 | yes |
| C-MUTSZ35-40 | C-MUTSZ35-40 | yes |
| C-MUTSZ35-50 | C-MUTSZ35-50 | yes |
| C-MUTSZ35-60 | C-MUTSZ35-60 | yes |
| C-MUTSZ35-70 | C-MUTSZ35-70 | yes |
| C-MUTSZ40-40 | C-MUTSZ40-40 | yes |
| C-MUTSZ40-50 | C-MUTSZ40-50 | yes |
| C-MUTSZ40-60 | C-MUTSZ40-60 | yes |
| C-MUTSZ40-70 | C-MUTSZ40-70 | yes |
| C-MUTSZ40-80 | C-MUTSZ40-80 | yes |
| C-MUTSZ50-50 | C-MUTSZ50-50 | yes |
| C-MUTSZ50-60 | C-MUTSZ50-60 | yes |
| C-MUTSZ50-70 | C-MUTSZ50-70 | yes |
| C-MUTSZ50-80 | C-MUTSZ50-80 | yes |
| C-MUTNZ6-10 | C-MUTNZ6-10 | yes |
| C-MUTNZ6-20 | C-MUTNZ6-20 | yes |
| C-MUTNZ8-15 | C-MUTNZ8-15 | yes |
| C-MUTNZ8-20 | C-MUTNZ8-20 | yes |
| C-MUTNZ8-25 | C-MUTNZ8-25 | yes |
| C-MUTNZ10-15 | C-MUTNZ10-15 | yes |
| C-MUTNZ10-20 | C-MUTNZ10-20 | yes |
| C-MUTNZ10-25 | C-MUTNZ10-25 | yes |
| C-MUTNZ10-30 | C-MUTNZ10-30 | yes |
| C-MUTNZ12-15 | C-MUTNZ12-15 | yes |
| C-MUTNZ12-20 | C-MUTNZ12-20 | yes |
| C-MUTNZ12-25 | C-MUTNZ12-25 | yes |
| C-MUTNZ12-30 | C-MUTNZ12-30 | yes |
| C-MUTNZ13-20 | C-MUTNZ13-20 | yes |
| C-MUTNZ13-30 | C-MUTNZ13-30 | yes |
| C-MUTNZ13-35 | C-MUTNZ13-35 | yes |
| C-MUTNZ16-20 | C-MUTNZ16-20 | yes |
| C-MUTNZ16-25 | C-MUTNZ16-25 | yes |
| C-MUTNZ16-30 | C-MUTNZ16-30 | yes |
| C-MUTNZ16-35 | C-MUTNZ16-35 | yes |
| C-MUTNZ16-40 | C-MUTNZ16-40 | yes |
| C-MUTNZ20-20 | C-MUTNZ20-20 | yes |
| C-MUTNZ20-25 | C-MUTNZ20-25 | yes |
| C-MUTNZ20-30 | C-MUTNZ20-30 | yes |
| C-MUTNZ20-35 | C-MUTNZ20-35 | yes |
| C-MUTNZ20-40 | C-MUTNZ20-40 | yes |
| C-MUTNZ20-50 | C-MUTNZ20-50 | yes |
| C-MUTNZ25-25 | C-MUTNZ25-25 | yes |
| C-MUTNZ25-30 | C-MUTNZ25-30 | yes |
| C-MUTNZ25-35 | C-MUTNZ25-35 | yes |
| C-MUTNZ25-40 | C-MUTNZ25-40 | yes |
| C-MUTNZ25-50 | C-MUTNZ25-50 | yes |
| C-MUTNZ25-60 | C-MUTNZ25-60 | yes |
| C-MUTNZ30-30 | C-MUTNZ30-30 | yes |
| C-MUTNZ30-35 | C-MUTNZ30-35 | yes |
| C-MUTNZ30-40 | C-MUTNZ30-40 | yes |
| C-MUTNZ30-50 | C-MUTNZ30-50 | yes |
| C-MUTNZ30-60 | C-MUTNZ30-60 | yes |
| C-MUTNZ35-35 | C-MUTNZ35-35 | yes |
| C-MUTNZ35-40 | C-MUTNZ35-40 | yes |
| C-MUTNZ35-50 | C-MUTNZ35-50 | yes |
| C-MUTNZ35-60 | C-MUTNZ35-60 | yes |
| C-MUTNZ35-70 | C-MUTNZ35-70 | yes |
| C-MUTNZ40-40 | C-MUTNZ40-40 | yes |
| C-MUTNZ40-50 | C-MUTNZ40-50 | yes |
| C-MUTNZ40-60 | C-MUTNZ40-60 | yes |
| C-MUTNZ40-70 | C-MUTNZ40-70 | yes |
| C-MUTNZ40-80 | C-MUTNZ40-80 | yes |
| C-MUTNZ50-50 | C-MUTNZ50-50 | yes |
| C-MUTNZ50-60 | C-MUTNZ50-60 | yes |
| C-MUTNZ50-70 | C-MUTNZ50-70 | yes |
| C-MUTNZ50-100 | C-MUTNZ50-100 | yes |
| E-MUGZ6-12 | E-MUGZ6-12 | yes |
| E-MUGZ8-10 | E-MUGZ8-10 | yes |
| E-MUGZ8-15 | E-MUGZ8-15 | yes |
| E-MUGZ10-10 | E-MUGZ10-10 | yes |
| E-MUGZ10-12 | E-MUGZ10-12 | yes |
| E-MUGZ10-20 | E-MUGZ10-20 | yes |
| E-MUGZ12-10 | E-MUGZ12-10 | yes |
| E-MUGZ12-12 | E-MUGZ12-12 | yes |
| E-MUGZ12-15 | E-MUGZ12-15 | yes |
| E-MUGZ12-20 | E-MUGZ12-20 | yes |
| E-MUGZ12-25 | E-MUGZ12-25 | yes |
| E-MUGZ13-12 | E-MUGZ13-12 | yes |
| E-MUGZ13-15 | E-MUGZ13-15 | yes |
| E-MUGZ13-20 | E-MUGZ13-20 | yes |
| E-MUGZ15-12 | E-MUGZ15-12 | yes |
| E-MUGZ15-15 | E-MUGZ15-15 | yes |
| E-MUGZ15-20 | E-MUGZ15-20 | yes |
| E-MUGZ16-15 | E-MUGZ16-15 | yes |
| E-MUGZ16-25 | E-MUGZ16-25 | yes |
| E-MUGZ18-14 | E-MUGZ18-14 | yes |
| E-MUGZ18-20 | E-MUGZ18-20 | yes |
| E-MUGZ20-14 | E-MUGZ20-14 | yes |
| E-MUGZ20-20 | E-MUGZ20-20 | yes |
| E-MUGZ20-25 | E-MUGZ20-25 | yes |
| E-MUGZ20-30 | E-MUGZ20-30 | yes |
| E-MUGZ20-40 | E-MUGZ20-40 | yes |
| E-MUGZ25-14 | E-MUGZ25-14 | yes |
| E-MUGZ25-20 | E-MUGZ25-20 | yes |
| E-MUGZ25-25 | E-MUGZ25-25 | yes |
| E-MUGZ25-30 | E-MUGZ25-30 | yes |
| E-MUGZ25-40 | E-MUGZ25-40 | yes |
| E-MUGZ30-20 | E-MUGZ30-20 | yes |
| E-MUGZ30-30 | E-MUGZ30-30 | yes |
| E-MUGZ30-40 | E-MUGZ30-40 | yes |
| E-MUGZ40-30 | E-MUGZ40-30 | yes |
| E-MUGZ40-50 | E-MUGZ40-50 | yes |
| E-MUGZ50-40 | E-MUGZ50-40 | yes |
| E-SHBZ5-8 | E-SHBZ5-8 | yes |
| E-SHBZ5-10 | E-SHBZ5-10 | yes |
| E-SHBZ5-12 | E-SHBZ5-12 | yes |
| E-SHBZ5-15 | E-SHBZ5-15 | yes |
| E-SHBZ6-8 | E-SHBZ6-8 | yes |
| E-SHBZ6-10 | E-SHBZ6-10 | yes |
| E-SHBZ6-12 | E-SHBZ6-12 | yes |
| E-SHBZ6-15 | E-SHBZ6-15 | yes |
| E-SHBZ6-20 | E-SHBZ6-20 | yes |
| E-SHBZ8-8 | E-SHBZ8-8 | yes |
| E-SHBZ8-10 | E-SHBZ8-10 | yes |
| E-SHBZ8-12 | E-SHBZ8-12 | yes |
| E-SHBZ8-15 | E-SHBZ8-15 | yes |
| E-SHBZ8-20 | E-SHBZ8-20 | yes |
| E-SHBZ8-25 | E-SHBZ8-25 | yes |
| E-SHBZ10-8 | E-SHBZ10-8 | yes |
| E-SHBZ10-10 | E-SHBZ10-10 | yes |
| E-SHBZ10-15 | E-SHBZ10-15 | yes |
| E-SHBZ10-20 | E-SHBZ10-20 | yes |
| E-SHBZ10-25 | E-SHBZ10-25 | yes |
| E-SHBZ12-10 | E-SHBZ12-10 | yes |
| E-SHBZ12-12 | E-SHBZ12-12 | yes |
| E-SHBZ12-15 | E-SHBZ12-15 | yes |
| E-SHBZ12-20 | E-SHBZ12-20 | yes |
| E-SHBZ12-25 | E-SHBZ12-25 | yes |
| E-SHBZ13-15 | E-SHBZ13-15 | yes |
| E-SHBZ15-10 | E-SHBZ15-10 | yes |
| E-SHBZ15-12 | E-SHBZ15-12 | yes |
| E-SHBZ15-15 | E-SHBZ15-15 | yes |
| E-SHBZ15-20 | E-SHBZ15-20 | yes |
| E-SHBZ15-25 | E-SHBZ15-25 | yes |
| E-SHBZ16-10 | E-SHBZ16-10 | yes |
| E-SHBZ16-12 | E-SHBZ16-12 | yes |
| E-SHBZ16-15 | E-SHBZ16-15 | yes |
| E-SHBZ16-20 | E-SHBZ16-20 | yes |
| E-SHBZ16-25 | E-SHBZ16-25 | yes |
| E-SHBZ16-30 | E-SHBZ16-30 | yes |
| E-SHBZ16-40 | E-SHBZ16-40 | yes |
| E-SHBZ20-15 | E-SHBZ20-15 | yes |
| E-SHBZ20-20 | E-SHBZ20-20 | yes |
| E-SHBZ20-25 | E-SHBZ20-25 | yes |
| E-SHBZ20-30 | E-SHBZ20-30 | yes |
| E-SHBZ20-40 | E-SHBZ20-40 | yes |
| E-SHBZ20-50 | E-SHBZ20-50 | yes |
| E-SHBZ25-20 | E-SHBZ25-20 | yes |
| E-SHBZ25-25 | E-SHBZ25-25 | yes |
| E-SHBZ25-30 | E-SHBZ25-30 | yes |
| E-SHBZ25-40 | E-SHBZ25-40 | yes |
| E-SHBZ25-50 | E-SHBZ25-50 | yes |
| E-SHBZ30-25 | E-SHBZ30-25 | yes |
| E-SHBZ30-30 | E-SHBZ30-30 | yes |
| E-SHBZ30-40 | E-SHBZ30-40 | yes |
| E-SHBZ30-50 | E-SHBZ30-50 | yes |
| E-SHBZ30-60 | E-SHBZ30-60 | yes |
| E-SHFZ5-10 | E-SHFZ5-10 | yes |
| E-SHFZ5-12 | E-SHFZ5-12 | yes |
| E-SHFZ6-10 | E-SHFZ6-10 | yes |
| E-SHFZ6-12 | E-SHFZ6-12 | yes |
| E-SHFZ6-15 | E-SHFZ6-15 | yes |
| E-SHFZ8-12 | E-SHFZ8-12 | yes |
| E-SHFZ8-15 | E-SHFZ8-15 | yes |
| E-SHFZ8-20 | E-SHFZ8-20 | yes |
| E-SHFZ10-10 | E-SHFZ10-10 | yes |
| E-SHFZ10-12 | E-SHFZ10-12 | yes |
| E-SHFZ10-15 | E-SHFZ10-15 | yes |
| E-SHFZ10-20 | E-SHFZ10-20 | yes |
| E-SHFZ12-10 | E-SHFZ12-10 | yes |
| E-SHFZ12-12 | E-SHFZ12-12 | yes |
| E-SHFZ12-15 | E-SHFZ12-15 | yes |
| E-SHFZ12-20 | E-SHFZ12-20 | yes |
| E-SHFZ12-25 | E-SHFZ12-25 | yes |
| E-SHFZ12-30 | E-SHFZ12-30 | yes |
| E-SHFZ13-12 | E-SHFZ13-12 | yes |
| E-SHFZ13-15 | E-SHFZ13-15 | yes |
| E-SHFZ13-20 | E-SHFZ13-20 | yes |
| E-SHFZ15-10 | E-SHFZ15-10 | yes |
| E-SHFZ15-12 | E-SHFZ15-12 | yes |
| E-SHFZ15-15 | E-SHFZ15-15 | yes |
| E-SHFZ15-20 | E-SHFZ15-20 | yes |
| E-SHFZ15-25 | E-SHFZ15-25 | yes |
| E-SHFZ16-12 | E-SHFZ16-12 | yes |
| E-SHFZ16-15 | E-SHFZ16-15 | yes |
| E-SHFZ16-20 | E-SHFZ16-20 | yes |
| E-SHFZ16-25 | E-SHFZ16-25 | yes |
| E-SHFZ16-30 | E-SHFZ16-30 | yes |
| E-SHFZ20-15 | E-SHFZ20-15 | yes |
| E-SHFZ20-20 | E-SHFZ20-20 | yes |
| E-SHFZ20-25 | E-SHFZ20-25 | yes |
| E-SHFZ20-30 | E-SHFZ20-30 | yes |
| E-SHFZ20-40 | E-SHFZ20-40 | yes |
| E-SHFZ25-30 | E-SHFZ25-30 | yes |
| E-SHFZ25-40 | E-SHFZ25-40 | yes |
| E-SHFZ25-50 | E-SHFZ25-50 | yes |
| E-SHFZ30-30 | E-SHFZ30-30 | yes |
| E-SHFZ30-40 | E-SHFZ30-40 | yes |
| E-SHTZ6-15 | E-SHTZ6-15 | yes |
| E-SHTZ8-20 | E-SHTZ8-20 | yes |
| E-SHTZ8-25 | E-SHTZ8-25 | yes |
| E-SHTZ10-25 | E-SHTZ10-25 | yes |
| E-SHTZ10-30 | E-SHTZ10-30 | yes |
| E-SHTZ12-25 | E-SHTZ12-25 | yes |
| E-SHTZ12-30 | E-SHTZ12-30 | yes |
| E-SHTZ16-25 | E-SHTZ16-25 | yes |
| E-SHTZ16-30 | E-SHTZ16-30 | yes |
| E-SHTZ16-35 | E-SHTZ16-35 | yes |
| E-SHTZ16-40 | E-SHTZ16-40 | yes |
| E-SHTZ20-30 | E-SHTZ20-30 | yes |
| E-SHTZ20-35 | E-SHTZ20-35 | yes |
| E-SHTZ20-40 | E-SHTZ20-40 | yes |
| E-SHTZ20-50 | E-SHTZ20-50 | yes |
| E-SHTZ25-30 | E-SHTZ25-30 | yes |
| E-SHTZ25-40 | E-SHTZ25-40 | yes |
| E-SHTZ25-50 | E-SHTZ25-50 | yes |
| E-SHTZ25-60 | E-SHTZ25-60 | yes |
| E-SHTZ30-35 | E-SHTZ30-35 | yes |
| E-SHTZ30-40 | E-SHTZ30-40 | yes |
| E-SHTZ30-50 | E-SHTZ30-50 | yes |
| E-SHTZ30-60 | E-SHTZ30-60 | yes |
| E-SHTZ30-70 | E-SHTZ30-70 | yes |
| E-SHTNZ6-15 | E-SHTNZ6-15 | yes |
| E-SHTNZ8-20 | E-SHTNZ8-20 | yes |
| E-SHTNZ8-25 | E-SHTNZ8-25 | yes |
| E-SHTNZ10-30 | E-SHTNZ10-30 | yes |
| E-SHTNZ12-25 | E-SHTNZ12-25 | yes |
| E-SHTNZ12-30 | E-SHTNZ12-30 | yes |
| E-SHTNZ16-25 | E-SHTNZ16-25 | yes |
| E-SHTNZ16-30 | E-SHTNZ16-30 | yes |
| E-SHTNZ16-35 | E-SHTNZ16-35 | yes |
| E-SHTNZ20-30 | E-SHTNZ20-30 | yes |
| E-SHTNZ20-35 | E-SHTNZ20-35 | yes |
| E-SHTNZ20-40 | E-SHTNZ20-40 | yes |
| E-SHTNZ20-50 | E-SHTNZ20-50 | yes |
| E-SHTNZ25-30 | E-SHTNZ25-30 | yes |
| E-SHTNZ25-35 | E-SHTNZ25-35 | yes |
| E-SHTNZ25-40 | E-SHTNZ25-40 | yes |
| E-SHTNZ25-50 | E-SHTNZ25-50 | yes |
| E-SHTNZ25-60 | E-SHTNZ25-60 | yes |
| E-SHTNZ30-35 | E-SHTNZ30-35 | yes |
| E-SHTNZ30-40 | E-SHTNZ30-40 | yes |
| E-SHTNZ30-50 | E-SHTNZ30-50 | yes |
| E-SHTNZ30-60 | E-SHTNZ30-60 | yes |
| E-SHTNZ30-70 | E-SHTNZ30-70 | yes |

| what was tried (SolidCraft 0.50.0) | error | result |
|---|---|---|
| insert_design with a free `parameters` map (blen 12 mm) | None | {'bbox_max': [[10.000000000000002, 7.0, 7.0], [8.0, 7.0, 7.0]], 'bodies': ['BodyFlange', 'BodyFlange (2)']} |
| component.set_link_parameters | {"command": "component.set_link_parameters", "error": "unknown command `component.set_link_parameters`", "step": 1} | None |
| generator.parse | {"command": "generator.parse", "error": "unknown command `generator.parse`", "step": 1} | None |
| generator.insert | {"command": "generator.insert", "error": "unknown command `generator.insert` (did you mean `canvas.insert`, `parts.insert` or `pointcloud.insert`?)", "step": 1} | None |
| blen 11 mm (not a printed length of the row) by an ordinary parameters.change | None | {'bbox_max': [[11.000000000000002, 7.0, 7.0]], 'bodies': ['BodyFlange']} |
| blen 11 mm in a configuration row | {"command": "config.row", "error": "invalid parameters for `config.row`: invalid parameters for `config.activate`: configuration rules: rule `printed L of C-MUFZ-5 (S16 p.514 table (shouldered))` restricts the final value", "step": 1} | None |
| unknown row | {"command": "component.insert_design", "error": "invalid parameters for `component.insert_design`: configuration `no-such-row` does not exist in the source design", "step": 1} | None |

## What SolidCraft 0.50.0 could not express (exact errors) and the workarounds

1. **A hole keeps the face it was picked on.** One `solid.hole` feature made on the round-flange body fails on the square-flange body:
   `configuration X would fail to rebuild: <Hole>: the reference `F8:side:l4` no longer exists as it was picked; reselect it`. Workaround
   (labelled): one set of hole features per body variant (a suppression column each). Proposal: a hole whose position expression is re-resolved
   to the face at that position on every rebuild (the doc says the position is followed; the face reference is what breaks).
2. **A free parameter value on an inserted part needs #23175 (our draft, being finished).** `component.insert_design {configuration, parameters}` is accepted and the key ignored,
   `component.set_link_parameters` and `generator.parse|insert` are `unknown command` (see the probe table). Workaround (labelled): a row for
   the code in a working copy of the model (`config.row {from: <catalogue row>, values: {...}}`), inserted by `configuration`; to change the
   length, change it in the working copy and insert again. needs #23175 (our draft, being finished).
3. **A rule cannot name a configuration row.** The per-row allowed lengths and the hole-set switches need a condition; there is none on the row, so
   each row carries a unitless `rowno` (and `kind` for the body variant) and the rules test that. Proposal: a `row` condition.
4. **Expression depth.** The sandbox allows a depth of 16 inside a function; a `refuse` call with a message built from `${}` interpolation or an
   array of 8 parts inside two nested `if` blocks fails to compile with `Expression exceeds maximum complexity (line 61, position 45)`, and the
   error names the first line only. Workaround: flat functions, `cat([...])`. Proposal: raise the depth to 32 or count blocks less.
5. **The field template ignores separators.** `E-LBF20-UU` reads as `E-LBF20UU` (the Python regex refuses it), see `rhai_equiv.json`. The
   template cannot say "no separator here" except by a required one (`\-`, added to the stand-in for the oil free bushing code).
6. **A code that matches no template** gets the engine's message, not the generator's: a second template `{raw: text 1..80 [...]}` catches
   it and `resolve` raises the Python message. Proposal: an optional `fn no_match(raw)`.
7. **Arcs and point expressions.** Arc points come from `sketch.point` ids with expression coordinates so that the arcs follow the
   parameters (the arc's centre is solved, not stored).

The optional link proof is declared in `link_checks.json` and run by `ci.sh` through `runtime.parametric.links`. It adds insertion, link-edit, and out-of-range refusal rows only when the command catalogue lists `component.set_link_parameters`. Release builds retain their existing rows and link dependency item.
