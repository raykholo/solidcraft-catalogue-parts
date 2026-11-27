# misumi.shf.shaft-holder: MISUMI Economy shaft supports

Ordering code in (`E-SHSTM8-25`, `C-SHA10`), native SolidCraft design out: a T-shaped clamp support with its shaft bore (H8), foot holes, slit
and clamp-screw thread. These hold the linear shafts of `misumi.sfj.shaft`.

## Ordering code

```
<type><D>-<H>        E-SHSTB  E-SHSTM  E-SHSTA        T-shaped with slit       (D 8-30)
                     E-SHWTB  E-SHWTA                 T-shaped with side slit  (D 8, 10, 12, 16, 20, 30)
                     E-SHSTBN E-SHSTMN                thickened, with slit     (D 10-50)
C-SHA<D>             T-shaped aluminium, fixed height  (D 10, 12, 16, 20, 25, 30; no H)
```

D is the shaft bore diameter (H8), H the bore centre height above the foot (selection per D from the catalogue). Examples: `E-SHSTM8-25` (the
catalogue's own), `E-SHSTBN10-10`, `E-SHWTA10-15`, `E-SHSTA16-20`, `C-SHA10`. Refused with a message: a height or size not in the table, E-SHSTB15 with
H25, the aluminium types (A) with a D / H pair that is not * marked, E-SHSTMN at D10, an H on C-SHA, a missing H.

## Dimensioned and appearance-only

**Dimensioned**: bore D and its H8 tolerance (written into the description), height H, thickness T, overall length L and height H1 (H + offset), foot
thickness S, top width W, foot-hole pitch L1 and diameter d (two holes, four on the thickened D30-50), slit width C, clamp screw position E, thread M
(through or depth n), clearance hole d2, counterbore d1 and its depth l.

**Not guaranteed**:

- The hex socket head cap screw (accessory) is not modelled; only its clearance hole, counterbore and the tapped thread are
- Edge chamfers and fillets (none printed); the corners of C-SHA are not rounded
- C-SHA: overall height H1, foot thickness S, foot length L, foot width B and top width W are reference values (+-0.5 mm), the slit and the clamp screw hole are approximate
- Positions of the second base hole row and the second screw of the thickened types (drawn at T/4 from the centre plane)
- Which D / H combinations are aluminium (read from the * marks; D and H both marked)
- The surface treatment of the B types is printed as Stainless steel and is given as printed

## Run

```
tools/gen E-SHSTM8-25                      # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/misumi/shf/shaft-holder   # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/shots E-SHSTM8-25                    # English and German screenshots into shots/
tools/preview vendors/misumi/shf/shaft-holder
tools/provenance vendors/misumi/shf/shaft-holder   # re-write PROVENANCE.md (never edit it by hand)
```

Invalid codes stop with a message (`CodeError: ...`). See `PROVENANCE.md` (generated) and `sources.toml` for every citation (S50, catalogue pages 540-542).
