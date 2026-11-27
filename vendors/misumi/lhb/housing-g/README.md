# misumi.lhb.housing-g: MISUMI Economy linear bushing housing units, center hole height optional

Ordering code in (`E-LBHG12-15`, `E-LBHGW20-25`), native SolidCraft design out: the aluminium housing with a flange of width L and thickness S, the
chamfered body of width W up to the total height H1, the shaft bore at the nominal diameter dr at the chosen centre height H above the base, and the four
mounting holes d on L1 x T1. The housings hold the bushings of `misumi.lb.linear-bushing`. The built-in bushing is **not drawn**: the bore is left empty.

## Ordering code

```
E-LBHG<dr>-<H>    single (length T)      dr 12: H 15, 20, 25     dr 16: H 20, 25, 30     dr 20: H 20, 25, 30
E-LBHGW<dr>-<H>   double (longer T)      dr 25: H 25, 30, 40     dr 30: H 30, 40, 50
```

H is the centre height (the optional dimension of the part number), H1 = H + 15 / 20 / 22 / 27.5 / 32.5 for dr 12 / 16 / 20 / 25 / 30. Examples: `E-LBHG12-15`
(the catalogue's own), `E-LBHG30-50`, `E-LBHGW20-25`. Refused with a message: a dr not offered, an H not offered for that dr, a missing H, anything after the H (no dowel holes on these types).

## Dimensioned and appearance-only

**Dimensioned**: flange width L, length T, total height H1, bore dr and its centre height H (centred at L/2), flange thickness S, body width W, mounting holes 4-d on L1 x T1.
Tolerances (H +-0.05, H1 0 / -0.5) are written into the description, not drawn.

**Not guaranteed**:

- The built-in linear bushing is not drawn: the bore is an empty plain cylinder at the nominal shaft diameter dr (the catalogue gives no inner dimensions of the unit)
- Upper corner chamfers (appearance, approximate): the figure shows the body top cut at both upper corners; the printed C1 is read as the 45 degree chamfer size. The shape of the two 4-C / 2-C chamfers of the figures (flange edges, the (0.5) of column C) is not drawn
- The flange is drawn as a plain rectangular plate of width L (symmetric, thickness S): the figure's flange outline and the position of the datum surface edges are read from the drawing, with no further dimensions printed
- Mounting holes: 4-d are drawn as plain through holes in the flange on L1 x T1 (no counterbore is printed)
- Total height H1 = H + offset is printed with the tolerance 0 / -0.5 and the centre height H with +-0.05; both are echoed in the description, not drawn
- Load ratings, allowable static moments and masses are not modelled

## Run

```
tools/gen E-LBHGW20-25
tools/check vendors/misumi/lhb/housing-g
tools/preview vendors/misumi/lhb/housing-g
tools/provenance vendors/misumi/lhb/housing-g
```

Invalid codes stop with a message (`CodeError: ...`). See `PROVENANCE.md` (generated) and `sources.toml` for every citation (S14, catalogue page 491).
