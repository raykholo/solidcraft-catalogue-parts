# Ordering-code grammar

Sources S1-S10 are in each generator's sources.toml. Spacing in MISUMI examples is "PN - L - ALT"; the web shop writes the same
code with hyphens: `HFS5-2020-800-LTP-RTP`.

## MISUMI 5 and 6 series aluminium extrusion

```
[K]<type>5|6-<profile>-<length>[-<alteration>]...
```

5 series profiles 2020, 2040, 4040 and 6 series profile 3030 are drawn (sources.toml rows 45-75 of misumi.hfs.extrusion). Four-slot types of the 6 series drawn: `HFS6` `HFSB6`
`CAF6` `HFSY6`; the other 6 series types (`NEFS6`, `EFS6`, `GFS6`, `NFSL6`, `HFSL6`, the flat/three-slot variants...) are different sections and refused as not
modelled. `HFSY5` exists for 2020 only. End tapping `LTP`/`RTP`/`TPW`: 2020 one M5 hole per end, 2040 two, 4040 four (all M5 depth 15), 3030 one M8
depth 24 (S2 p.757). Wrench holes: 5 series H 10 / J 20 / K 20 d 7.35; 6 series H 15 / J 30 / K 30 and d 5 or 8, which the code must state: `-X5` or `-X8`
(`HFS6-3030-500-LCH-X5`, S3 p.759).

| Field | Allowed values | Source |
|-------|---------------|--------|
| `K` prefix | fixed-length extrusion; length must be 1000 or 4000 (effective length); no alterations | S1 p.529 |
| type | four-slot: `NFS5` `NFSB5` `HFS5` `HFSB5` `CAF5` `HFSY5`. Other 5 series types in the catalogue (`NFSF5` `HFSF5` `HFSFB5` three-side slot, `NFST5` `HFST5` `HFSTB5` two-side slots two flats, `HFSH5`, `HFSC5`, `HFSR5` curved) are recognised and refused as "not modelled" | S1 p.529-530 |
| `B` in type | black anodize (`HFSB5`, `NFSB5`) | S1 |
| profile | `2020`, `2040`, `4040` (drawn); other sizes (2525, 2060, 4080...) appear in the p.757 table and are refused until their drawing is read | S1 p.529-530, S2 p.757 |
| length | configurable: 50 to 4000 mm in 0.5 mm steps (6000 mm by special order, not accepted). Length tolerance L +-0.5; `SC` makes it +-0.2 for L <= 1500 | S1, S5 |
| `LTP` / `RTP` / `TPW` | end tapping left / right / both ends: M5 depth 15, one hole in the centre bore, HFS5-2020 | S2 p.757 |
| `LHP` / `RHP` / `HPW` | same with a heli-coil insert (M3 depth 6 for 2020). Parsed, refused as not modelled | S2 p.757 |
| wrench access hole `<L|R><C|W|E><H|V|P>` | L/R: left or right end; C/W/E: one, two or three holes in a line; H horizontal, V vertical, P crisscross. HFS5: first hole H = 10 from the end, then J = 20, K = 20; diameter 7.35. `P` is refused: the catalogue text does not say how a one-row crisscross is laid out | S3 p.759 |
| `FL` / `FR` | moves the wrench hole of that side 3 mm toward the end (end cap clearance); only valid with a wrench hole on that side | S3 p.760 |
| `FL`/`FR` caveat | S3 p.760 lists 6 and 8 series only; on the 5 series FL/FR is unverified, so the parser adds a note | S3 |
| `SC` | high precision cut, tolerance only | S5, S2 |
| `CW` | end face C chamfer; parsed, refused as not modelled | S5 p.756 |
| not accepted | `L_T45` / `R_T45` 45 degree cuts, `LSP/RSP/SPW` four-side-hole tapping, `LDH` D/S/M/L holes, `Z6/XA100`, `AH/BH/AV/BV`, `ZZZ` labelling: listed in S5 p.755-756, unsupported (clear error) | S5 |

Validation errors: bad shape, unknown type, profile or alteration, length out of range or off the 0.5 grid,
K with a length other than 1000/4000, duplicate options, FL/FR without a hole, holes that do not fit the length.
`CodeError` = invalid code; `NotModelled` (a subclass) = valid MISUMI code this prototype does not build.

## HIWIN MGN (S4)

```
MGN <size> <C|H> [E] <blocks> R <length> [E] [Z0|Z1|ZF] [C|H|P] [M|HC|NC] [I..IV] [+ options]
```

Examples: `MGN12H2R500Z0C` (size 12, long block H, 2 blocks, rail 500 mm, Z0 preload, normal accuracy C),
`MGN9C1R195ZFH`. Size 7, 9, 12, 15. Rail holes: `L = (n-1)P + 2E`, E <= P/2 (S4 p.85).

## HIWIN HG (S7)

```
set    HG<H|W><size><C|H><A|B|C>[E]<blocks>R|T<length>[E][Z0|ZA|ZB][C|H|P|SP|UP][M][I..IV][+ options]
rail   HGR<size>R|T<length>[E][C|H|P|SP|UP][M]
block  HG<H|W><size><C|H><A|B|C>[E][Z0|ZA][C|H|P][M]
```

Examples: `HGH20CA2R1000ZAH` (size 20, heavy load square block, mounted from the top, 2 blocks, rail 1000 mm from the top, preload ZA, accuracy H),
`HGW25CC1R640ZAP`, `HGR25T640` (rail mounted from the bottom), `HGW45CB`. Sizes 15, 20, 25, 30, 35, 45, 55, 65. HGH is A only; HG15 has the C (heavy) block only;
HGW-CB drills O through holes, CA/CC tap M from the top. Rail: `L = (n-1)P + 2E`, Es <= E <= P/2, maximum 4000 mm (stainless M, HG15/20/25 only: 2000). `HGL` (low) and
other options after `+` are parsed or refused as not modelled; blocks that do not fit the rail are refused.

## MISUMI linear shafts (S8)

```
<type><D>-<L>[-LKC][-SC<n> | -WSC<n>-X<m>][-FC<l>-A<a>|E<e> | -WFC<l>-A<a>-E<e>]
<type>T<D>-<L>-M<thread>[-alterations]          one end tapped
type: E-SFJ  E-SSFJ  E-PSFJ  E-PSSFJ (g7)   E-PSFG (f8)
```

Examples: `E-PSFJ6-20` (the catalogue's own), `E-PSFJT6-30-M3`, `E-SFJ20-300-SC5`, `E-PSFG16-250-FC20-A10`, `E-SSFJ10-123.4-LKC-WSC12-X8`, `E-PSSFJ30-200-WFC40-A10-E20`.
D in 3, 4, 5, 6, 8, 10, 12, 13, 15, 16, 20, 25, 30, 35, 40, 50; length range per diameter from the table; 1 mm steps (0.1 mm with LKC). The tolerance class comes from the type (g7 or f8) and is
written into the part description. Refused with a message: a length or thread outside the table, D3/4/5 or D35-50 on E-PSFG, SC with WSC, FC with WFC, flats closer than 2 mm to each other or to the tap, wrench flats on D < 6.

## MISUMI 5 series pre-assembly T-nuts (S9)

```
<type>-<M>        type: HNTT5 HNTTV5 HNTTZ5 HNTTSN5 HNTTSS5      M: 3, 4, 5 (HNTT5, HNTTSN5) or 5 (the others)
```

`HNTT5` alone is `HNTT5-5` (catalogue note). The other 5 series nut families (`HNTU5` spring, `HNST5` stoppers, ...) are recognised and refused as not modelled.

