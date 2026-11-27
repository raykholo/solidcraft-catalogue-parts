# Next generator candidates

A grammar sketch for each, with the public sources to read. "Checked" means the page was found in a search;
none of these has been read to dimension level yet.

## MISUMI linear guides
- Family seen in the catalogue: miniature guides `SSEB`, `SSE2B`, `SSEBZ` (stainless), `SSEBL`/`SSE2BL` configurable; block types standard, long, extra long, wide; `-MX` lubrication unit.
- Sketch: `<series><size> [-<rail length>] [-MC | -RLC | -LLC | -WC | -B3 | -B4]`, e.g. `SSE2BL16-450-MC` (MC = rail holes tapped instead of counterbored; LLC/RLC = left/right end cut).
- Sources: https://uk.misumi-ec.com/pdf/fa/2014/P1_0533-0534_F08_EN_003.pdf , https://uk.misumi-ec.com/pdf/fa/2014/P1_0555-0556_F08_EN.pdf , https://my.misumi-ec.com/vona2/detail/110310458729/ (product pages for the miniature guides). Same builder as MGN: rail with hole pattern, N blocks.

## HIWIN MGN / HGR / HGH (rails and blocks)
- MGN done (this repo). HG/EG: block `HGH20CA` = series HG, flange/square H, size 20, load class C, mounting A; rail `HGR20R<length>`; set `HGH20CA2R1000ZAH` = blocks (2), rail length, preload (Z0/ZA/ZB), accuracy (C/H/P).
- Sources: HIWIN "Linear Guideway" catalogue https://hiwin.com/wp-content/uploads/2026/08/HIWIN-Linear-Guideway-Catalog-1.pdf (grammar and the HG dimension tables); MG series in the same HIWIN catalogue (G99TE24-2410, chapter 2-4). (done). (Done: the HG series catalogue 2-1-3 labels the digit as "No. of Blocks per Rail"; see catalogue.py.)
- Rail hole pattern and end distance rule is the same as MGN (`L=(n-1)P+2E`), so `vendors/hiwin/mg/rail-set/src/build.py` generalises with a table for HG.

## THK
- `HSR25A2UU+1000L`-style: series (HSR), size 25, block type (A/B/R), number of blocks on the rail (2), seal symbol (UU), clearance symbol, `+<rail length>L`, joint symbol. THK documents this as "Model Number Coding" (catalog page A1-186 for HSR).
- Sources: https://www.thk.com/eu/en/products/lm_guide/model_number/0001 , https://tech.thk.com/en/products/pdf/en_a01_575.pdf , https://tech.thk.com/en/products/pdf/en_a01_551.pdf . Dimension tables are in the same catalogue (A1-xxx pages), per series.

## igus
- drylin W: rail `WS-10-<width code>-<length>` (e.g. `WS-10-80-600`, `WS-10-300`), carriages `WJ...` / `WTUM-01-10-...`; stainless `WS-10-40-ES-FG`.
- Sources: https://www.igus.de/info/linear-guides-drylin-w-stainless-steel-guide-ca?C=US&L=en , the igus drylin W catalogue pages. The rail section and hole spacing must come from igus's own PDF; distributor listings were only used for the naming pattern.

## 80/20 and item profiles
- 80/20: `<series><nominal size>[-<length>]`: `1010`, `1020`, `1515`, `1010-48` (inch, 48 in cut), 10 series slot 0.236 in (6 mm) per a distributor overview; finishes `-S` (smooth), `-Black`. Sources: https://8020.net/1010.html , the 80/20 catalogue profile drawings (cross-section dimensions have to be read from the drawing as done for HFS5-2020). Anodised 1010 area, slot and bore values: not verified.
- item: `Profil 8 40x40 L` / `Profil X 8 40x40 2NO90 leicht` -> article 0.0.611.xx at https://www.item24.com/de-ch/profil-x-8-40x40-2no90-leicht-natur-61190 ; slot 8 mm; cross-section data sheet on item24 / item-online.de. Not verified.
- Reuse: `vendors/misumi/hfs/extrusion/src/ext.py`'s outline-by-sides generator (one slot, rotated four times, fillets) works for any four-slot profile once its drawing numbers are read.

## McMaster-style fasteners: ISO 4762 socket head cap screw (first-class generator)
- Grammar: `ISO 4762 M<d>x<L>` (also `M6x20-A2`, `M6x20-12.9`), e.g. `M6x20`. Fields: nominal diameter d (M1.6 ... M64), length L (nominal, standard length series), property class / material, finish.
- Dimensions (head dk, head height k, hex socket s, socket depth t, thread length b, pitch P): the standard's table. The ISO text is paid; public tables: https://us.misumi-ec.com/blog/metric-socket-head-cap-screws-dimensions/ , https://engineersedge.com/iso_socket_head_screw.htm (M6: dk 10, k 6, s 5, t 3 per supplier sheets). Read each from a manufacturer page and cite it per row.
- SolidCraft already has standard parts (`crates/engine/src/cmd/parts.rs`: `socket_head_cap_screw`, part number `ISO 4762 M6x20`); the generator can call that command and add only the code parser, the check and the metadata, which is cheaper than rebuilding the head.
