# misumi.hnt.t-nut: MISUMI 5 series pre-assembly T-nuts (HNTT family)

Ordering code in (`HNTT5-4`), native SolidCraft design out: the insertion nut for the 6 mm slot of the 5 series extrusions, with its tapped hole.
Types HNTT5, HNTTV5, HNTTZ5, HNTTSN5, HNTTSS5; thread M3, M4 or M5 (M5 when omitted).

## Ordering code

```
<type>-<M>        type: HNTT5 HNTTV5 HNTTZ5 HNTTSN5 HNTTSS5      M: 3, 4, 5 (HNTT5, HNTTSN5) or 5 (the others)
```

`HNTT5` alone is `HNTT5-5` (catalogue note). The other 5 series nut families (`HNTU5` spring, `HNST5` stoppers, ...) are recognised and refused as not modelled.

## Dimensioned and appearance-only

**Dimensioned**: plan 10 x 10, width of the bottom face and neck 5.8, E and T per type, thread M, the reference tightening torque (in the description).

**Not guaranteed**:

- The flank from the 5.8 mm bottom to the 10 mm body (measured from the vector side view, about 35 degrees from the nut axis)
- The edge rounds of the side view: R0.3 (bottom corners), R1.0 (flank / body, reduced on the E 3.3 types), R0.2 (shoulder and neck top). The drawing shows them but prints no radius; no chamfer is drawn
- The tap drill: the modelled hole is the pilot bore (O2.5 / O3.3 / O4.2 for M3 / M4 / M5, the ISO coarse tap drill; the page prints none), the thread is a cosmetic `solid.thread` of the nominal size through the thickness T (the repo convention, see misumi.hfs.extrusion "Tapped holes")

Not drawn: spring-loaded nuts (HNTU, HNTP, HNTA), stoppers (HNST, SHNST), integrated nuts (HNTE) and the other families on the same catalogue page.

## Run

```
tools/gen HNTT5-4                 # -> out/<code>.sc   (add --step for a STEP file)
tools/check vendors/misumi/hnt/t-nut   # build + spec-check every code in codes.txt, writes checks/<SolidCraft version>/
tools/shots HNTT5-4                      # English and German screenshots into shots/
tools/preview vendors/misumi/hnt/t-nut   # re-render preview.png
tools/provenance vendors/misumi/hnt/t-nut   # re-write PROVENANCE.md (never edit it by hand)
```

`SC_VER` (default 0.49.1) picks the SolidCraft release; `SC_CLI`, `SC_APP` or `SC_RELEASES` say where the binaries are.
Invalid codes stop with a message (`CodeError: ...`); valid options that are not drawn give `NotModelled`.

See `PROVENANCE.md` (generated) for where every number comes from and how it was verified, and `sources.toml` for the full citations.
