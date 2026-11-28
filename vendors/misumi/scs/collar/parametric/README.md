# misumi.scs.collar as a parametric SolidCraft generator

Using free parameters on inserted links, `component.set_link_parameters`, `generator.parse` / `generator.insert`, field templates, Rhai, and rules addressed by feature name requires the #23175 surface (unavailable on 0.50.0/0.51.1). The exact command errors quoted below are observations from SolidCraft 0.50.0. On capable hosts, link overrides and ordinary source `parameters.change` enforce limit rules marked `enforce_on_edit`.

The MISUMI Economy Series shaft collars modelled ONCE in SolidCraft (`scs-collar/scs-collar.sc`), a configuration table of the 102 catalogue rows, the ordering
code as field templates and the logic as plain Rhai, following SolidCraft's generator interface (`docs/formats/generator.md`, version 2, issue 22331). The Python
generator in `../src` is untouched and is the reference every code below is compared with. Four bodies are one design: the aluminium ring (slit, split, two
through or two counterbored fixing holes), the collar for a bearing inner ring (ring plus boss), and the steel collars with a urethane damper (slit, compact
slit, compact split).

```
scs-collar/                    the package layout of the interface document
  generator.toml               [[template]] x4 and [rows."<key>"] source / page / status per configuration row
  scs-collar.sc                the parametric model + its configuration table + its rules (built by build.py)
  generator.rhai               resolve(fields) -> #{configuration, parameters, properties}; fields(configuration, parameters) -> fields
  tables/*.csv                 sizes, bearing, urethane, types, params: generated from ../data/*.csv by pkgfiles.py (rows keep source, page, status)
build.py  pkgfiles.py          builds the model with solidcraft-cli; writes the tables and generator.toml
run_codes.py  report.py        the end-to-end proof (results.json) and the tables below
faithfulness.py  ci.sh         the verdict file for tools/parametric-verdict, and the one command CI runs
```

## How the model is built

- **One model, 23 parameters.** `od bore z0 ring_h ht boss_dia boss_h cut_w p_fix s_fix d1f d2f tcb ud ur ux uy ure_t` (mm), the unitless switches `kind` (0 ring,
  1 bearing mount, 2 urethane), `split`, `fix` (0 none, 1 two through holes, 2 two counterbored), `msize` (clamp thread size) and the text `part_type`; `yh1`, `yh2`,
  `xh`, `zc` are derived (the clamp screw axis on the mid-wall radius and where it meets the outer cylinder, `xh = od / 2 * sqrt(1 - ((bore + od) / (2 * od))^2)`).
- **Four bodies, one feature list.** The steel part is one cylinder `Collar` (base `z0`, height `ring_h`; the urethane types start at `z0 = t`), its bearing `Boss`
  (joined before the bore, as in Python), one `Bore`, one `Slit` whose width is `cut_w` and whose length is `(1 + split) * (od / 2 + 1)`: the same box is a slit
  or, with `split = 1`, the gap that cuts the ring into two bodies. The urethane damper is its own body `Urethane damper`.
- **Topology = suppression columns of the rows AND `drive_suppression` rules** on `kind`, `split`, `fix` and `msize`: the boss (bearing), the second clamp screw (split
  ring), the fixing holes (through or counterbored), the damper and its bore, the head seat of screw A (clearance hole, slot, round) and of screw B (split).
- **A thread size cannot come from a parameter**: one tapped-hole feature per size (`RThr_M3..M6` x 2 screws for the ring and bearing, `UThrA_M3..M10` for the slit
  urethane types, `UThrAs` / `UThrBs` M4 and M6 for the split urethane type, which taps the half the kernel names `Collar (1)`, as the Python builder does).
- **Rows = the catalogue rows** (`C-SCSAW-12-10`, `C-SCSBNAW-12`, `slit-compact-12`): 61 ring, 8 bearing, 33 urethane. Compatible C-SCSAW widths share a row using `ring_h` and `ht` overrides. The text parameter `part_type` carries the plating for the code printer.
- The clamp screw holes use `position` on the outer cylinder with the derived `xh`, `yh1`, `yh2`; the fixing holes `position` on the top face.

## The ordering code

`generator.toml` has five templates: `C-{type: SCSAW|SCNPAW|SCSMAW|SCSGAW}{d: int 0..99}\-{b: int 0..99}`, `C-{kind: SCSBNAW}{d}\-{ds}`, `E-[{plat: P|S}]{fam: SCSPD|SCD}{d}`,
`E-[{plat: P|S}]{fam: SCDJ}{d}[\-{b}]` and the catch-all `{raw: text 1..64 [A-Za-z0-9-]}`. The `\-` is a required separator, so a code without its `-` is refused as the Python
regular expressions do. The one-value choice fields (`kind`, `fam`) let the template printer tell the templates apart. Every Python refusal, in its order and with its
message, is a `refuse(kind, message)`; a code that matches only the catch-all gets the shape message quoting it as typed.

## Result: side by side

Volume mm3 / area mm2 / bbox mm / faces and bodies; the spec check column is passed rows / rows. Equal = same bodies, volume and area within 1e-6 relative,
same bbox, face and body counts.

| code | python vol / area / bbox / faces | parametric vol / area / bbox / faces | spec check python | spec check parametric | equal |
|---|---|---|---|---|---|
| C-SCSAW6-8 | 2162.2 / 1397.0 / 20x19.9875x8 / 9f 1b | 2162.2 / 1397.0 / 20x19.9875x8 / 9f 1b | 12/12 | 12/12 | yes |
| C-SCSAW12-10 | 5675.2 / 2820.7 / 30x29.9917x10 / 9f 1b | 5675.2 / 2820.7 / 30x29.9917x10 / 9f 1b | 12/12 | 12/12 | yes |
| C-SCSAW30-15 | 24191.1 / 8094.9 / 55x54.9955x15 / 9f 1b | 24191.1 / 8094.9 / 55x54.9955x15 / 9f 1b | 12/12 | 12/12 | yes |
| C-SCNPAW6-8 | 2160.4 / 1515.3 / 20x19.9937x8 / 16f 2b | 2160.4 / 1515.3 / 20x19.9937x8 / 16f 2b | 12/12 | 12/12 | yes |
| C-SCNPAW16-12 | 8703.1 / 4106.5 / 35x34.9964x12 / 16f 2b | 8703.1 / 4106.5 / 35x34.9964x12 / 16f 2b | 12/12 | 12/12 | yes |
| C-SCNPAW25-15 | 21278.5 / 7597.3 / 50x49.9975x15 / 16f 2b | 21278.5 / 7597.3 / 50x49.9975x15 / 16f 2b | 12/12 | 12/12 | yes |
| C-SCSMAW8-8 | 3216.3 / 2068.8 / 25x24.99x8 / 11f 1b | 3216.3 / 2068.8 / 25x24.99x8 / 11f 1b | 16/16 | 16/16 | yes |
| C-SCSMAW20-15 | 17347.6 / 6799.1 / 45x44.9944x15 / 11f 1b | 17347.6 / 6799.1 / 45x44.9944x15 / 11f 1b | 16/16 | 16/16 | yes |
| C-SCSMAW30-15 | 23164.7 / 8580.1 / 55x54.9955x15 / 11f 1b | 23164.7 / 8580.1 / 55x54.9955x15 / 11f 1b | 16/16 | 16/16 | yes |
| C-SCSGAW8-10 | 4761.3 / 2912.0 / 28x27.9911x10 / 15f 1b | 4761.3 / 2912.0 / 28x27.9911x10 / 15f 1b | 17/17 | 17/17 | yes |
| C-SCSGAW12-10 | 7179.4 / 3967.6 / 35x34.9929x10 / 15f 1b | 7179.4 / 3967.6 / 35x34.9929x10 / 15f 1b | 17/17 | 17/17 | yes |
| C-SCSGAW30-15 | 22374.0 / 8759.8 / 55x54.9955x15 / 15f 1b | 22374.0 / 8759.8 / 55x54.9955x15 / 15f 1b | 17/17 | 17/17 | yes |
| C-SCSBNAW6-9 | 2196.0 / 1445.2 / 20x19.9875x9 / 11f 1b | 2196.0 / 1445.2 / 20x19.9875x9 / 11f 1b | 15/15 | 15/15 | yes |
| C-SCSBNAW12-16 | 5804.1 / 2955.6 / 30x29.9917x11.5 / 11f 1b | 5804.1 / 2955.6 / 30x29.9917x11.5 / 11f 1b | 15/15 | 15/15 | yes |
| C-SCSBNAW30-35 | 24822.9 / 8612.9 / 55x54.9955x17.5 / 11f 1b | 24822.9 / 8612.9 / 55x54.9955x17.5 / 11f 1b | 15/15 | 15/15 | yes |
| E-SCSPD6 | 2723.3 / 2603.8 / 20x20x12 / 28f 3b | 2723.3 / 2603.8 / 20x20x12 / 28f 3b | 20/20 | 20/20 | yes |
| E-SCSPD13 | 11893.4 / 7276.8 / 35x35x18 / 28f 3b | 11893.4 / 7276.8 / 35x35x18 / 28f 3b | 20/20 | 20/20 | yes |
| E-PSCSPD20 | 21831.6 / 10762.3 / 45x45x20 / 28f 3b | 21831.6 / 10762.3 / 45x45x20 / 28f 3b | 20/20 | 20/20 | yes |
| E-SSCSPD25 | 25960.7 / 12208.7 / 50x50x20 / 28f 3b | 25960.7 / 12208.7 / 50x50x20 / 28f 3b | 20/20 | 20/20 | yes |
| E-SCSPD30 | 29451.8 / 13738.9 / 55x55x20 / 28f 3b | 29451.8 / 13738.9 / 55x55x20 / 28f 3b | 20/20 | 20/20 | yes |
| E-PSCD4 | 1470.2 / 1390.0 / 15x15x10 / 16f 2b | 1470.2 / 1390.0 / 15x15x10 / 16f 2b | 20/20 | 20/20 | yes |
| E-SCD12 | 13753.3 / 6689.9 / 35x35x18 / 16f 2b | 13753.3 / 6689.9 / 35x35x18 / 16f 2b | 20/20 | 20/20 | yes |
| E-SSCD16 | 17396.5 / 8100.8 / 40x40x18 / 16f 2b | 17396.5 / 8100.8 / 40x40x18 / 16f 2b | 20/20 | 20/20 | yes |
| E-PSCD35 | 35378.2 / 14265.6 / 60x60x20 / 16f 2b | 35378.2 / 14265.6 / 60x60x20 / 16f 2b | 20/20 | 20/20 | yes |
| E-SCD50 | 93597.0 / 28221.4 / 85x85x27 / 16f 2b | 93597.0 / 28221.4 / 85x85x27 / 16f 2b | 20/20 | 20/20 | yes |
| E-SCDJ8-10 | 4088.8 / 3028.1 / 25x25x10 / 16f 2b | 4088.8 / 3028.1 / 25x25x10 / 16f 2b | 20/20 | 20/20 | yes |
| E-SCDJ12-10 | 5547.8 / 3963.2 / 30x30x10 / 16f 2b | 5547.8 / 3963.2 / 30x30x10 / 16f 2b | 20/20 | 20/20 | yes |
| E-PSCDJ20-13 | 11305.2 / 6694.2 / 40x40x13 / 16f 2b | 11305.2 / 6694.2 / 40x40x13 / 16f 2b | 20/20 | 20/20 | yes |
| E-SSCDJ30-15 | 17790.6 / 9311.3 / 50x50x15 / 16f 2b | 17790.6 / 9311.3 / 50x50x15 / 16f 2b | 20/20 | 20/20 | yes |
| E-SCDJ40-15 | 22325.9 / 11522.0 / 60x60x15 / 16f 2b | 22325.9 / 11522.0 / 60x60x15 / 16f 2b | 20/20 | 20/20 | yes |

| rejected code | python message | parametric message | same |
|---|---|---|---|
| C-SCSAW7-10 | C-SCSAW is offered for I.D. D in 6, 8, 10, 12, 15, 16, 20, 25, 30 mm, not 7 (p.544 table) | C-SCSAW is offered for I.D. D in 6, 8, 10, 12, 15, 16, 20, 25, 30 mm, not 7 (p.544 table) | yes |
| C-SCSAW6-15 | C-SCSAW6 is offered in width B = 8, 10 mm, not 15 (p.544 table) | C-SCSAW6 is offered in width B = 8, 10 mm, not 15 (p.544 table) | yes |
| C-SCNPAW6-10 | C-SCNPAW6 is offered in width B = 8 mm, not 10 (p.544 table) | C-SCNPAW6 is offered in width B = 8 mm, not 10 (p.544 table) | yes |
| C-SCSMAW6-8 | C-SCSMAW is offered for I.D. D in 8, 10, 12, 15, 16, 20, 25, 30 mm, not 6 (p.545 table) | C-SCSMAW is offered for I.D. D in 8, 10, 12, 15, 16, 20, 25, 30 mm, not 6 (p.545 table) | yes |
| C-SCSGAW10-8 | C-SCSGAW10 is offered in width B = 10, 12 mm, not 8 (p.545 table) | C-SCSGAW10 is offered in width B = 10, 12 mm, not 8 (p.545 table) | yes |
| C-SCSAW12 | 'C-SCSAW12': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'C-SCSAW12': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |
| C-SCSBNAW12-10 | C-SCSBNAW12 is offered with selection Ds = 16 mm only, not 10 (p.546 table; the ordering example is C-SCSBNAW12-16) | C-SCSBNAW12 is offered with selection Ds = 16 mm only, not 10 (p.546 table; the ordering example is C-SCSBNAW12-16) | yes |
| C-SCSBNAW7-9 | C-SCSBNAW is offered for I.D. D in 6, 8, 10, 12, 15, 20, 25, 30 mm, not 7 (p.546 table) | C-SCSBNAW is offered for I.D. D in 6, 8, 10, 12, 15, 20, 25, 30 mm, not 7 (p.546 table) | yes |
| E-SCSPD7 | E-SCSPD is offered for D in 6, 8, 10, 12, 13, 15, 16, 20, 25, 30 mm, not 7 (p.546 table) | E-SCSPD is offered for D in 6, 8, 10, 12, 13, 15, 16, 20, 25, 30 mm, not 7 (p.546 table) | yes |
| E-SSCSPD6 | E-SSCSPD (stainless steel) is only available for D in 15, 16, 20, 25 mm, not 6 (p.546 note) | E-SSCSPD (stainless steel) is only available for D in 15, 16, 20, 25 mm, not 6 (p.546 note) | yes |
| E-SCSPD6-10 | 'E-SCSPD6-10': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'E-SCSPD6-10': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |
| E-SCD4 | E-SCD4: for D = 4 only the electroless nickel plated E-PSCD4 is available (p.547 note) | E-SCD4: for D = 4 only the electroless nickel plated E-PSCD4 is available (p.547 note) | yes |
| E-SSCD13 | E-SSCD (stainless steel) is only available for D in 6, 10, 12, 16, 20, 25, 30, 35 mm, not 13 (p.547 standard type note) | E-SSCD (stainless steel) is only available for D in 6, 10, 12, 16, 20, 25, 30, 35 mm, not 13 (p.547 standard type note) | yes |
| E-SCD45 | E-SCD is offered for D in 4, 5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30, 35, 40, 50 mm, not 45 (p.547 standard type table) | E-SCD is offered for D in 4, 5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30, 35, 40, 50 mm, not 45 (p.547 standard type table) | yes |
| E-SCDJ12 | 'E-SCDJ12': the compact slit type needs the width selection, <type><D>-<B>, e.g. E-SCDJ12-10 (p.547) | 'E-SCDJ12': the compact slit type needs the width selection, <type><D>-<B>, e.g. E-SCDJ12-10 (p.547) | yes |
| E-SCDJ12-12 | E-SCDJ12 is offered in width B = 10 mm only, not 12 (p.547 compact type table, B selection) | E-SCDJ12 is offered in width B = 10 mm only, not 12 (p.547 compact type table, B selection) | yes |
| E-SSCDJ25-15 | E-SSCDJ (stainless steel) is only available for D in 8, 10, 12, 16, 20, 30, 40 mm, not 25 (p.547 compact type note) | E-SSCDJ (stainless steel) is only available for D in 8, 10, 12, 16, 20, 30, 40 mm, not 25 (p.547 compact type note) | yes |
| E-XSCD12 | 'E-XSCD12': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'E-XSCD12': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |
| C-SCSAW1210 | 'C-SCSAW1210': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'C-SCSAW1210': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |
| C-SCSAW123-4 | 'C-SCSAW123-4': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'C-SCSAW123-4': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |
| E-SCDJ12-1 | E-SCDJ12 is offered in width B = 10 mm only, not 1 (p.547 compact type table, B selection) | E-SCDJ12 is offered in width B = 10 mm only, not 1 (p.547 compact type table, B selection) | yes |
| E-SCDJ1210 | 'E-SCDJ1210': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'E-SCDJ1210': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |
| E-SCSPD6-10 | 'E-SCSPD6-10': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'E-SCSPD6-10': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |
| E-SCSBNAW6 | 'E-SCSBNAW6': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'E-SCSBNAW6': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |
| C-SCSBNAW12-1 | C-SCSBNAW12 is offered with selection Ds = 16 mm only, not 1 (p.546 table; the ordering example is C-SCSBNAW12-16) | C-SCSBNAW12 is offered with selection Ds = 16 mm only, not 1 (p.546 table; the ordering example is C-SCSBNAW12-16) | yes |
| X | 'X': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'X': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |
| E-SCSPD | 'E-SCSPD': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'E-SCSPD': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |
| C-SCNPAW6-10 | C-SCNPAW6 is offered in width B = 8 mm, not 10 (p.544 table) | C-SCNPAW6 is offered in width B = 8 mm, not 10 (p.544 table) | yes |
| E-SCSPD99 | E-SCSPD is offered for D in 6, 8, 10, 12, 13, 15, 16, 20, 25, 30 mm, not 99 (p.546 table) | E-SCSPD is offered for D in 6, 8, 10, 12, 13, 15, 16, 20, 25, 30 mm, not 99 (p.546 table) | yes |
| C-SCSBNAW9-9 | C-SCSBNAW is offered for I.D. D in 6, 8, 10, 12, 15, 20, 25, 30 mm, not 9 (p.546 table) | C-SCSBNAW is offered for I.D. D in 6, 8, 10, 12, 15, 20, 25, 30 mm, not 9 (p.546 table) | yes |
| C-SCSMAW30-10 | C-SCSMAW30 is offered in width B = 15 mm, not 10 (p.545 table) | C-SCSMAW30 is offered in width B = 15 mm, not 10 (p.545 table) | yes |
| C-SCSGAW16-8 | C-SCSGAW16 is offered in width B = 10, 12 mm, not 8 (p.545 table) | C-SCSGAW16 is offered in width B = 10, 12 mm, not 8 (p.545 table) | yes |
| E-PSCSPD7 | E-PSCSPD is offered for D in 6, 8, 10, 12, 13, 15, 16, 20, 25, 30 mm, not 7 (p.546 table) | E-PSCSPD is offered for D in 6, 8, 10, 12, 13, 15, 16, 20, 25, 30 mm, not 7 (p.546 table) | yes |
| E-SCDJ40-14 | E-SCDJ40 is offered in width B = 15 mm only, not 14 (p.547 compact type table, B selection) | E-SCDJ40 is offered in width B = 15 mm only, not 14 (p.547 compact type table, B selection) | yes |
| E-SSCD4 | E-SSCD (stainless steel) is only available for D in 6, 10, 12, 16, 20, 25, 30, 35 mm, not 4 (p.547 standard type note) | E-SSCD (stainless steel) is only available for D in 6, 10, 12, 16, 20, 25, 30, 35 mm, not 4 (p.547 standard type note) | yes |
| E-SCD12- | 'E-SCD12-': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'E-SCD12-': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |
| E-SCSPD6- | 'E-SCSPD6-': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'E-SCSPD6-': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |
| C-SCSAW-10 | 'C-SCSAW-10': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'C-SCSAW-10': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |
| C-SCSAW12- | 'C-SCSAW12-': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'C-SCSAW12-': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |
| E-SCDJ12-10- | 'E-SCDJ12-10-': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | 'E-SCDJ12-10-': expected <type><I.D. D>-<width B>, e.g. C-SCSAW12-10 (types: C-SCSAW, C-SCNPAW, C-SCSMAW, C-SCSGAW); C-SCSBNAW<D>-<Ds>, E-SCD<D>, E-SCSPD<D> and E-SCDJ<D>-<B> (and their E-P.. / E-S.. variants) are the other forms | yes |

| change | on | changed in place vol / area / bbox / faces | direct code (inserted) | python | equal (changed = direct = python) |
|---|---|---|---|---|---|
| width -> 12 mm | C-SCSAW16-10 (= C-SCSAW16-12) | 8706.1 / 3865.1 / 35x34.9929x12 / 9f 1b | 8706.1 / 3865.1 / 35x34.9929x12 / 9f 1b | 8706.1 / 3865.1 / 35x34.9929x12 / 9f 1b | yes |
| width -> 12 mm | C-SCNPAW16-10 (= C-SCNPAW16-12) | 8703.1 / 4106.5 / 35x34.9964x12 / 16f 2b | 8703.1 / 4106.5 / 35x34.9964x12 / 16f 2b | 8703.1 / 4106.5 / 35x34.9964x12 / 16f 2b | yes |

| probe | result |
|---|---|
| insert_design with a free `parameters` map (ring_h 12 mm) | {'bodies': ['Collar', 'Collar (2)'], 'volume': 11350.316261471819} |
| component.set_link_parameters | {"command": "component.set_link_parameters", "error": "unknown command `component.set_link_parameters`", "step": 1} |
| generator.parse | {"command": "generator.parse", "error": "unknown command `generator.parse`", "step": 1} |
| split = 1 on the slit row (rules switch the second clamp screw on, the gap replaces the slit) | {'bodies': ['Collar', 'Collar (1)'], 'volume': 5672.537639169012} |
| unknown row | {"command": "component.insert_design", "error": "invalid parameters for `component.insert_design`: configuration `no-such-row` does not exist in the source design", "step": 1} |

config.table: 102 rows, 61 columns, 73 rules

All 30 codes: the parametric part has the same volume, area, bbox, face and body count as the Python part (one body, two for the split ring, three for the split
urethane collar), and passes the same spec check with the same number of rows. Every refusal (the 18 of `codes.txt` and 22 more, compared with `collar.parse`) has the
Python message word for word. The table has 102 rows, 61 columns and 73 rules.

A code with a dangling separator or a missing one (`E-SCD12-`, `C-SCSAW1210`, `C-SCSAW-10`) is refused with the Python shape message, quoting the code as typed: the two sizes
are joined by the required separator `\-` and the last template (one free text field) catches everything else.

## Commands

```
# on a build host or in CI (the `parametric` workflow runs ci.sh): SC_CLI = solidcraft-cli 0.50.0, RHAI_RUN = the built runtime/rhai-run
bash vendors/misumi/scs/collar/parametric/ci.sh OUTDIR           # build.py, run_codes.py, faithfulness.py -> OUTDIR/faithfulness.json
python3 vendors/misumi/scs/collar/parametric/report.py OUTDIR/results.json    # the tables above
tools/parametric-verdict OUTDIR/faithfulness.json                # the verdict CI prints
```

## It stays parametric

A catalogue row is activated and the width (`ring_h` and `ht`) changed on the configured design with `parameters.change`; compared with the other width of the same
type built directly and with the Python part (table above, last block): C-SCSAW16-10 at 12 mm is C-SCSAW16-12, and the same for the split C-SCNPAW16.

## SolidCraft 0.50.0 observations (exact errors) and workarounds

1. **A hole picks its face, and the pick does not survive a change of topology.** The clamp screw hole of the ring (`solid.hole {position}` on the outer cylinder)
   drawn on the slit ring fails when a row switches the slit to the through gap of the split type: `configuration C-SCNPAW-6-8 would fail to rebuild: RThr_M3_1: RThr_M3_1:
   the reference `F3:side#[F6:+x]` no longer exists as it was picked; reselect it`. Workaround (labelled): the split ring's two clamp screws are their own features
   (`RThrS_M<m>_<k>`), drawn in the split state, and the slit ring's screw is drawn in the slit state; rules switch the right set. The same would apply to the top
   face of the fixing holes, which exist only on the slit types.
2. **A thread designation cannot come from a parameter**: one tapped-hole feature per size (M3 to M6 on the ring, M3 to M10 on the urethane slit types, M4 and M6
   on the split urethane type), each with its own rule.
3. **The tapped half of a split collar is a body name.** The kernel names the halves `Collar (1)` and `Collar (2)`, and the urethane builder taps `Collar (1)`; a
   feature's `targets` is fixed in the feature, so the split types have their own tapped-hole features (`UThrAs`, `UThrBs`) targeting `Collar (1)`, and the slit types
   target `Collar`.
4. **A free parameter value on an inserted part requires the #23175 surface (unavailable on 0.50.0/0.51.1).** `component.insert_design {parameters: {...}}` is accepted and the key ignored; `component.set_link_parameters` and
   `generator.parse` -> `unknown command` (probes in the table above). Compatible C-SCSAW widths now resolve to one row plus width overrides; plating remains text. The historical width changes in "It stays parametric" are made on the configured design. The inserted-link gap remains under "blocked" on release hosts
   (requires the #23175 surface (unavailable on 0.50.0/0.51.1)).
5. **The working "Default" row** made by `config.configure` is dropped before the rules are added (see the shaft-holder README for the error it gives otherwise).
6. **Rules addressed by feature name need #23175 (our draft, being finished).** In 0.50.0, rules name features by integer id, so `build.py` builds the model in two passes; **a suppressed feature still holds its inputs**, so the rows without a boss,
   fixing holes or damper keep inert positive sizes for them.
7. **One conditional-free slit/gap box.** The slit and the split gap are one box whose length is `(1 + split) * (od / 2 + 1 mm)`, because the expression language
   has no conditional.

## What does not fit the interface document, and proposals

| Where | What the collar needs | Proposal |
|---|---|---|
| field template | print with the template that fits the fields | `TemplateSet.print` tries each template (done in `runtime/fieldtemplate.py`); one-value choice fields tell templates apart |
| field template | a catch-all for the shape error message | a second `[[template]]` of free text (done), or `fn no_match(raw)` |
| model | a feature that keeps its face pick across a slit -> gap change | re-pick by position on rebuild (a `position` hole already has the point), or accept a `position` hole without a stored face |
| rules | name a feature by name | `feature` by name in `config.rule` |

Link insertion and editing compare two real catalogue codes with their Python generator builds. A separate existing limit rule supplies the refusal check; no new catalogue limits are introduced.

### #23175 checks

The 0.50.0/0.51.1 results above remain release observations. The #23175 CI artifact records 30 valid, 40 rejects, 2 rebuild checks and 1 blocked records. The next CI run also checks link overrides and ordinary edit refusal with `enforce_on_edit` where limit rules exist; these new checks are pending. Differences remain differences.

The supplied #23175 artifact includes 0 link checks; the added ordinary-edit enforcement check awaits CI.

The link fixture compares C-SCSAW16-10 → C-SCSAW16-12 (`ring_h` and `ht`, same C-SCSAW-16-10 row) against Python builds. The size table gives the same outside diameter and M5 screw for both widths. Refusal uses the existing `split` rule with value 2.
