# misumi.scs.collar: MISUMI Economy Series shaft collars

Ordering code in (`C-SCSAW12-10`, `C-SCSBNAW12-16`, `E-SCD12`, `E-SCDJ12-10`, `E-SCSPD6`), native SolidCraft design out. All collar pages of the Economy Series
catalogue 2025 (p.544-547; p.548 starts chapter 05) are covered: the aluminium collars of p.544-546 and the steel / stainless collars with urethane of
p.546-547.

## Ordering code

```
aluminium (S20, S21)
<type><I.D. D>-<width B>
type: C-SCSAW   slit type                                   (p.544)
      C-SCNPAW  split type (two halves)                     (p.544)
      C-SCSMAW  slit type, 2 through fixing holes           (p.545)
      C-SCSGAW  slit type, 2 counterbored fixing holes      (p.545)
<type><I.D. D>-<Ds>      C-SCSBNAW  slit type for bearing inner mount, Ds = boss diameter, one value per D (p.546)

steel (E-), electroless nickel (E-P) or stainless (E-S), with a urethane damper (S21)
<type><D>        E-SCSPD / E-PSCSPD / E-SSCSPD  split type, compact, 2 screws (p.546)
                 E-SCD / E-PSCD / E-SSCD        slit type, standard (p.547)
<type><D>-<B>   E-SCDJ / E-PSCDJ / E-SSCDJ     slit type, compact, B selection one value per D (p.547)
```

Examples: `C-SCSAW12-10` (the catalogue's own), `C-SCNPAW16-12`, `C-SCSMAW20-15`, `C-SCSGAW8-10`, `C-SCSBNAW12-16` (the catalogue's own), `E-SCSPD6` (own),
`E-SCDJ12-10` (own), `E-PSCD35`, `E-SSCSPD25`. The table rows are in `data/sizes.csv` (p.544-545), `data/bearing.csv` (p.546) and `data/urethane.csv`
(p.546-547). Refused with a message: a D, B or Ds that the table does not list, a missing or surplus width, stainless steel for a D that is not offered in
stainless, and E-SCD4 (D4 only exists electroless nickel plated: E-PSCD4).

Geometry of the E types: a steel ring of width B1 on z = t..B with a urethane damper disc of thickness t on z = 0..t (B = B1 + t in every row); a slit of width W
(split gap for E-SCSPD) from the bore to the outside; the clamp screw axis across it at X from the axis, centred on B1, M tapped in the -X half, the clearance hole d in
the +X half from the slit to the floor of the head seat at Y, the head seat a U-shaped slot of width 2R open to the outside. E-SCSPD has two such screws (top and bottom).

## Dimensioned and appearance-only

**Dimensioned**: I.D. D (nominal; the printed +0.05/+0.01 is the tolerance before cutting and goes into the description), width B, outer diameter D1, the clamp
screw thread M, and for C-SCSMAW / C-SCSGAW the pitch P, through diameter (S, or d1), counterbore diameter d2 and depth t. Axis along Z, one end face on z = 0.
In `data/sizes.csv` the column S is the through hole of C-SCSMAW.

**Also dimensioned (S21)**: for C-SCSBNAW D, Ds, ring width b, total width B, D1, M; for the E types D, B, D1, B1, t, W, M, d, R, X, Y (all printed per row) with the
printed bore tolerance in the description. The bracketed reference range Z of the slit tables is stored but not drawn.

**Not guaranteed**:

- The slit width (not printed; drawn 1 mm) and the gap between the two halves of C-SCNPAW (not printed; drawn 0.5 mm)
- Position and depth of the clamp screw hole (the catalogue prints only its thread size M; drawn on the mid-wall radius at mid width, tapped right through)
- Which half of C-SCNPAW is tapped and which has the clearance hole (both are drawn tapped)
- Chamfers and edge breaks (none printed)
- The clamp and fixing screws themselves (not drawn)
- The bore is drawn at the nominal D; the printed +0.05/+0.01 is the tolerance before cutting
- C-SCSBNAW: the slit width (drawn 1 mm), the clamp screw hole position (mid-wall radius, mid ring width b), the diagonal notch of its front view (not drawn)
- E types: the damper as a plain unslit disc of thickness t; which half is tapped and the tapped length; the head seat depth and floor shape (U-shaped slot, floor at the printed Y); the bracketed range Z; chamfers (printed without a size); the screws; D1 +-0.1 and the bore tolerance (drawn nominal)

The slit and the split gap are named `... (appearance, approximate)` in the design.

## Run

```
tools/gen C-SCSAW12-10                 # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/misumi/scs/collar   # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/shots C-SCSAW12-10                # English and German screenshots into shots/
tools/preview vendors/misumi/scs/collar # re-render preview.png
tools/provenance vendors/misumi/scs/collar   # re-write PROVENANCE.md (never edit it by hand)
```

`SC_VER` (default 0.49.1) picks the SolidCraft release; `SC_CLI`, `SC_APP` or `SC_RELEASES` say where the binaries are.
Invalid codes stop with a message (`CodeError: ...`). `NotModelled` is kept for future valid but undrawn collars; none is left on p.544-547.

## Open questions

- The two tables are printed with merged cells; each row's D1, M, P and hole sizes were read against the row grid. C-SCSAW, C-SCNPAW and C-SCSMAW agree on D1 and M wherever the same D and B occur; C-SCSGAW has its own larger D1 for some rows (e.g. D12-B10: 35 against 30).
- p.546-547 (S21): the hatched strip of the side views is read as the urethane damper (B = B1 + t holds in all 33 rows), Y as the distance from the slit to the head seat floor and R as the radius of the U-shaped seat. The compact slit's "B Selection" is read as one B per D (the ordering example E-SCDJ12-10 agrees). The slit tables print the D tolerance +0.06/+0.01 (E-SCD note: +0.01~+0.08); the split type +0.05/+0.01.
- The catalogue's section 04-158 gives holding-force test figures and material notes for these collars; none of that is geometry and none is used.

See `PROVENANCE.md` (generated) for where every number comes from and how it was verified, and `sources.toml` for the full citations.
