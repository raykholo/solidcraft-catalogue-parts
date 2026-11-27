# Parametric generators: what fits and what does not

Status: analysis, nothing built. It answers the SolidCraft proposal (tangency-labs/solidcraft#22331) that a generator be one
parametric `.sc` modelled once, driven by named user parameters, plus a configuration table of catalogue rows
(`component.insert_design` takes a `configuration`), with the ordering code a plain field template and the logic in sandboxed Rhai
(`code_template`, `table`, `refuse`).

Method: every generator's `src/`, `data/`, `generator.toml` and `codes.txt` were read, and the valid codes were enumerated by calling
each parser (counts below are valid codes found, not estimates). What SolidCraft supports today was read from the SolidCraft sources
of release 0.50.0 (the docs listed in section 1, the generated command reference printed by `solidcraft-cli commands`, and the
command schemas in the source tree). Nothing was run in SolidCraft for this note. RFC 0019 is not in the SolidCraft checkout that
was read; section 5 uses the declaration schema of this repository (`schema/generator.schema.json`) and the matcher in
`runtime/registry.py` instead.

## 1. What SolidCraft supports today

Paths are in the SolidCraft repository. "Registry" is the command reference from `solidcraft-cli commands`.

| Capability | Today | Where |
|---|---|---|
| Named user parameters, units, expressions | exists | `docs/book/src/guide/parameters.md` |
| Expression functions `sin cos tan asin acos atan atan2 sinh cosh tanh asinh acosh atanh sqrt abs sign min max floor ceil round trunc mod exp ln log log10 pow hypot` | exists | `docs/book/src/guide/parameters.md` |
| A conditional (`if`, `select`) or a table lookup inside an expression | missing | not in the function list above |
| Text parameters (`unit: text`); used by `sketch.text` `text_expression` | exists | registry `parameters.add`, `sketch.text` |
| Parameter-driven metadata (`component.metadata.set` part number, description, material take text; only `bom_quantity` takes an expression) | missing | registry `component.metadata.set` |
| Configuration table: rows, parameter columns, suppression columns, material and appearance columns, `config.activate`, `config.preview` | exists | `docs/configurations.md` |
| A source id and page per configuration row | missing (rows carry a name and an id only) | `docs/configurations.md`, registry `config.row` |
| Ordered rules: conditions `parameter` (eq ne lt le gt ge against an expression), `suppression`, `all`, `any`, `not`; effects `drive_parameter`, `drive_suppression`, `parameter_range`, `allow_parameter_values` (at most 128 values, 2048 rules). Plain parameter edits re-run the suppression rules live | exists | `docs/configurations.md`, `crates/engine/src/schema/config.rs` |
| Limit on configuration rows | not documented | `docs/configurations.md` |
| `component.insert_design {path, configuration?, document?, translate, reuse, ...}` | exists | registry; `docs/book/src/guide/assemblies.md` documents `path`, `translate`, `reuse` only |
| A parameter override on `component.insert_design` (free values such as `length`) | missing; `document` (the design as JSON) is the workaround | registry |
| A linked component keeps the part's bodies only; its timeline and parameters stay in the part's own design | as documented, so a parameter cannot be changed on the inserted occurrence | `docs/book/src/guide/assemblies.md` |
| Pattern counts that are expressions: `sketch.pattern.rectangular/circular` (count 2..500), `solid.pattern.rectangular` (`count1`), features, bodies and components as sources | exists | registry; `crates/engine/src/cmd/features.rs`; `docs/feature-patterns.md` does not mention expression counts |
| Pattern alignment `right` (copies run on from the original), `center` (original stays fixed, copies on both sides: four instances sit at 0, +1, -1, +2 spacings, so an even count is not centred) | exists | `docs/feature-patterns.md` |
| Feature suppression per row or by rule | exists | `docs/configurations.md`, `timeline.suppress` |
| Thread and hole designation (`M5`, `thread:`) from a parameter | missing (plain text; `solid.thread` can size itself from the face it is laid on, which would follow a tap-drill diameter) | registry `solid.thread`, `solid.hole` |
| Drive a design from the command line: `solidcraft-cli run ... --param NAME=EXPR --params-file F.json` | exists | `solidcraft-cli run` usage |
| Check a design over a parameter range: `inspect.parameter_sweep` (failed and warned features, lost joints, rebuild time), `inspect.parameter_variants` (volume, mass, body count for up to 12 variants) | exists | `docs/book/src/guide/parameters.md`, registry |
| Measure: `inspect.measure` (per body bbox, volume, area, mass; face and edge distances, diameters), `model.faces`, `model.threads`, `inspect.interference`, `inspect.hole_stacks`, `component.metadata`, `document.metadata`, `assembly.mass_properties` | exists | registry |
| Per-face appearance in a configuration: stable roles only (box axis faces, cylinder caps and unsplit side, profile-plane extrude caps); chamfer and groove faces are not certified roles | partly | `docs/configurations.md` |
| Rhai runtime with `code_template`, `table`, `refuse`; field templates | proposal only, not in the docs | issue comment |
| RFC 0019 text | not in this checkout | - |

## 2. Notation

Field templates use the proposal's syntax: `{f}` a choice field whose allowed values come from the parameter, `{f: A=x, B=y}` letters
mapped to values, `[...]` optional (absent means the default), `{n: int a..b}`, separators and case ignored. Kinds the proposal does
not list are marked (*): `{n: dec a..b step s}` a decimal with a step, `{opts: set(...)}` an unordered set of options some of which
take an argument, `{*}` trailing free text.

Three needs apply to all 18 and are not repeated per row:

* S7 metadata: every generator writes `part_number`, `description` and `material` from the code and the row.
* S9 provenance: every row of every `data/*.csv` has a source id, page and status (AGENTS.md rule). The configuration table has no
  place for them, so the CSVs stay the source of truth and the table (and `PROVENANCE.md`) is generated from them.
* S11 valid combinations: each template field is checked against its own allowed values, but the catalogue is a set of valid
  combinations (type with size, size with length range, option with type). "No row for this key" must be a `refuse` with a message,
  which every `!` line in `codes.txt` tests.

"Fits as is" means every other capability the generator needs exists today (section 1). "Fits with X" means one named gap.
"Needs Y" means a larger gap or a re-model of the part.

## 3. The 18 generators

Counts of valid codes come from running the parsers. Rows are the configuration-table rows if the part's catalogue table is joined on
the key shown.

| Generator | Parameters | Configuration table | Field template(s) | Loops, options, topology, derived values | Verdict |
|---|---|---|---|---|---|
| hiwin.mg.rail-set | `size` {7,9,12,15}, `block` {C,H}, `blocks` 1..4, `length` 40..2000 (int), `caps` bool (default off) | 8 rows (size x block) from `blocks.csv`; `rails.csv` (4) and `caps.csv` (2) join on size | `MGN{size}{block}[E]{blocks: int 1..4}R{length: int 40..2000}[E][{preload}][{accuracy}][{material: M=stainless, HC=hard chrome, NC=coating}][{rails}][+{*}(*)]` | Rail holes: pattern count `n = floor((length - 2*Es)/P) + 1`, `E = (length - (n-1)*P)/2` (the Python `while` in `holes_for` never iterates: `E < Es + P/2` by construction); blocks: pattern of the block bodies, first block at `length/2 - (blocks-1)*(L+gap)/2` (the `center` alignment would shift an even count); rail screws: pattern of the ISO 4762 component, count = holes; caps: suppressed unless `caps`; block mounting thread (text) by size; max length per size. Appearance bodies are extra features | fits with S6 (`length`, `blocks` are free values, no insert-time input) |
| hiwin.eg.guideway | `series` {H,W} (R = rail only), `size` {15,20,25,30,35}, `load` {C,S}, `mount` {A,B}, `blocks` 1..n, `rail_mount` {R, U} (T is refused: no tapped-hole dimensions printed), `length` 100..4000 | 30 block rows (H 10, W 20) + 5 rail-only rows; `rails.csv` (5) joins on size | set `EG{series}{size}{load}{mount}[E]{blocks}{rail_mount: R, U}{length: dec 100..4000 (*)}[E][{preload}][{accuracy}][M][{rails}][+{*}(*)]`; block `EG{series}{size}{load}{mount}[E][{preload}][{accuracy}][M]`; rail `EGR{size}{rail_mount: R, U}{length}[E][{accuracy}][M][+{*}(*)]` | Three products in one design: rail suppressed for a block, blocks suppressed for a rail (pattern count >= 2 rule). S block: 2 holes, C block: 4 (second column suppressed). A: tapped, B: through (two hole features switched by `mount`). Rail holes and blocks as MG; end distance must be `<= P/2` (refuse). Stainless only EG15 C. Block gap 10 mm is an illustration constant | fits with S6 |
| hiwin.hg.guideway | as EG plus `mount` {A,B,C}, `size` up to 65, `load` {C,H}, rail mount R (counterbore from top) or T (tapped from bottom) | 60 block rows (H, W x size x load x mount) + 8 rail rows | as EG with `size` 15..65, `{mount: A,B,C}`, `{rail_mount: R, T}` (both drawn); block-only and rail-only templates | As EG; rail mount R or T switches the hole feature and the bottom plane (two suppressed hole features); HGH is A only, HG15 has C only (S11); stainless M for 15/20/25 only with max length 2000 (a row-dependent range) | fits with S6 |
| hiwin.rg.guideway | as HG with `mount` {A,C}, `dust` {none,SS,ZZ,DD,KK} | 30 block rows (RGH and RGW x size x load) + 8 rails; `dust.csv` (15 x 4) adds 4 length columns | as EG with `{mount: A, C}` and `{rail_mount: R}` (T refused); the `+KK/E2+RC` tail is a set of `/`- and `+`-joined options (*) | Six holes per block (RGH: C x B plus the rail axis; RGW: C x B flange holes plus two on the axis `C1` apart: two hole layouts, switched). Dust code replaces the block length `L` by a column of `dust.csv`: a conditional value, done with `drive_parameter` rules. End distance rule: `lo = min(Es, P/2)`, `n = floor((length - 2*lo)/P) + 1`, `E` must equal `Es` or lie in `lo..P/2` (refuse) | fits with S6 and the option set (*) for the `+` tail |
| misumi.hbl.bracket | `type` (19 values), `alteration` {none, C, SET, SST, SEU, SSU, SEP, SSP, SEC} | 19 rows from `types.csv` (167 valid codes = 19 x alterations, which only add text) | `{type}[-{alteration}]`; `HBLTS5-4` contains a hyphen inside a choice value; `-4` valid for HBLTS5 only, `-C` only where `alt_c` is 1 (S11) | One L-section sketch extruded `width`. Holes: 1 or 2 per arm (`25` or `30|50`: second suppressed or pattern count with spacing 20); tabs on HBK types: suppressed otherwise; eccentric `hole_x`. Alterations are accessory text only | fits as is |
| misumi.hfs.extrusion | `type` {NFS,NFSB,HFS,HFSB,CAF,HFSY} x series {5,6}, `profile` {2020,2040,4040,3030}, `length` 50..4000 step 0.5 (K prefix: 1000 or 4000 only, no alterations), end taps, wrench holes (side L/R, rows 1..3, H or V, shift FL/FR, `X5`/`X8` on 6 series) | 4 profile rows (`profiles.csv`) x 20 valid (type, profile) pairs; `types.csv` 12 rows set material and surface text | `[K]{type}-{profile}-{length: dec 50..4000 step 0.5 (*)}{alterations: set(LTP, RTP, TPW, {L\|R}{C\|W\|E}{H\|V}, FL, FR, SC, X5\|X8) (*)}` joined by `-` in any order | Four different cross-sections: 2020 (one slot per side, one bore), 2040 (two slots on each long side, one on each short side, two bores, a hexagonal void), 4040 (two slots on every side, a central void whose arcs are the four O4.2 bores), 3030 (6 series, one slot per side, five bores: four corners and a centre O6.8). Slots per side (1 or 2) is a sketch pattern count; voids and bores are not. Wrench holes: rows 1..3 at `H`, `H+J`, `H+J+K` (J = K in all four rows), left or right (mirrored from `length`), H or V (two features); end taps: one tapped bore per bore of the profile (1, 2, 4, 1), thread `M5` or `M8` | needs S4 (per-profile sketch: four alternative extrude features, three suppressed per row), the option-set field (*), decimal step (*), S6 (`length`) |
| misumi.hnt.t-nut | `type` (5), `thread` {M3,M4,M5}, default M5 when absent | 9 rows = valid (type, M) pairs; `types.csv` (5) and `tap.csv` (3) join | `{type}[-{m: 3, 4, 5}]` (default 5) | One profile; fillet radius `min(R_FLANK_TOP, (E - R_EDGE - FLANK_H)/tan(17.5 deg))` (min, tan exist); pilot bore from `tap.csv`; thread `M3/M4/M5` is text, so three thread features switched by row (or `solid.thread` sized from the bore) | fits as is |
| misumi.lb.linear-bushing | `shape` {straight, round, square, compact}, `layout` {standard, pilot, centre}, `counterbore` {standard, opposite}, `plated` bool, `dr` (13 values), `suffix` {TUU, DUU, DMUU, UU, LUU} | 480 valid codes from 158 dimension rows in 10 CSVs (`short`, `medium`, `flanged_*`, `compact_*`, `pilot_*`, `center_*`) | `E-LB[{shape: F=round, K=square, H=compact}[{layout: P=pilot, C=centre}\|{opposite: Z}][{plated: M}]]{dr}{suffix}` (22 type strings; the letters decompose into real parameters; `Z` excludes `P` and `C`: S11); `suffix` needs longest match (UU inside LUU, DUU, DMUU) | Revolve profile with a variable number of vertices (ring grooves add 8 points, the flange 3 to 5): the sketch cannot suppress entities, so the part is re-modelled as a barrel revolve plus optional features (grooves cut, round flange, square flange, compact flange as separate sketches). Flange position `x0` is a column; counterbore on the near or far face is `x0` or `x0 + T`; holes 4 on the PCD, or 2 or 4 in the compact flange (`F` empty or not); single or double length by suffix; plating changes the tolerance text only | needs S4 (flange kind per row) and a re-modelled profile; 480 rows is the largest table |
| misumi.lhb.bushing-housing | `family` {N, NW}, `dr`, `length` {single, D, L}, `dowel` bool | 40 rows without dowel (78 valid codes); `single.csv` 12, `double.csv` 11 | `E-LBHN[W]{dr}[{length: D=medium, L=long}][-P]`; D and L only exist for some `dr` (S11) | One profile extrusion; 2 or 3 mounting rows (`long`: three, pattern count 3 vs 2), pilot bores of diameter `d` below the thread; dowel holes suppressed unless `-P`, positioned either on the mounting rows or on the centre line by series (position columns) | fits as is |
| misumi.lhb.housing-g | `family` {G, GW}, `dr` {12,16,20,25,30}, `centre_height` | 30 rows (dr x height x single/double) from `housing-g.csv` (5 rows, `H_choices` lists the heights) | `E-LBHG[W]{dr}-{h}` with `h` valid per `dr` (S11) | One profile (`H1 = H + offset`), four mounting holes, nothing optional | fits as is |
| misumi.lhb.tall-housing | `family` {S, SW}, `dr`, `length` {single, D, S, L}, `dowel` | 41 rows without dowel (61 valid codes) from `blocks.csv` (41 rows) and `dowel.csv` (20) | `E-LBHS[W]{dr}[{length: D, S, L}][-P]` | Vertical `M1` pair and horizontal `M2` holes (2, or 3 on the long type: count), counterbores, dowels only on the long type by diagonal or centre line (columns), dowel suppressed otherwise | fits as is |
| misumi.ofb.oil-free-bushing | `type` (12: straight, shouldered, thrust, round, square, compact flange; thin or standard wall), `d` (25 values), `length` 3..100 from a list per (type, d) | 159 (type, d) rows from 7 CSVs (784 valid codes: `length` is the free number, 1 to 13 values per row) | `{type}{d}-{l: int 3..100}` | Revolve profile with 4 points (straight) or 6 (flanged): same re-model as `lb`; round, square and compact flanges are separate sketches; mounting holes 2 or 4 by flange and `d`; `D_thin`, `N_thin` columns by wall | needs S4 (six families), S5 (allowed `length` values per row: `allow_parameter_values` rules, up to 13 values per row) |
| misumi.scs.collar | `family` {ring, bearing, urethane, urethane-compact}, `type`, `d`, `b` or `ds`, plating | 153 rows (type, D, B) from `sizes.csv` 61, `bearing.csv` 8, `urethane.csv` 33 | five templates: `C-{type: SCSAW, SCNPAW, SCSMAW, SCSGAW}{d}-{b}`; `C-SCSBNAW{d}-{ds}`; `E-[{P\|S}]SCSPD{d}`; `E-[{P\|S}]SCD{d}`; `E-[{P\|S}]SCDJ{d}-{b}` | Four different bodies. Ring: slit (one clamp hole) or split (gap, two clamp holes, **two bodies**), fixing holes none, through or counterbored (3 variants: suppressed features). Bearing mount: boss cylinder. Urethane: a second body (damper disc), head seat slot and R cut, split gives two bodies named `(1)`, `(2)` by the kernel and later cuts target them by name | needs S4 (4 designs or one design with 4 branches) and care with body names after a split |
| misumi.sfj.shaft | `type` (29 strings = base {SFJ, SSFJ, PSFJ, PSSFJ, PSFG, ...} x family {plain, T, C, Z, W, PG, PH}), `d` (16 values), `length` 10..1500 (step 1, or 0.1 with `LKC`), options `M N F P T SC SX WSC+X FC+A/E WFC+A+E LFC+A LKC` | 64 valid straight (type, D) pairs; the tapped, stepped and flat families add the family tables `tap*.csv` 4, `stepped_*.csv` 2, `diameters.csv` 16, `wrench.csv` 13: ranges per D and family | `E-{base}[{family: T, C, Z, W}]{d}-{length: dec 10..1500 (*)}{options: set(...) (*)}` and `E-{base: SFPG, ...}{d}-{length}-F{f}-P{p}-M{m}...`; options in any order, `WSC12-X8`, `FC10-A8`, `WFC10-A8-E20` carry arguments; presence rules per family (SC required for C, PG, PH) | One cylinder. Up to six optional features, each with its own parameters: stepped ends (joined cylinders of diameter `P`), tapped ends, flats `SC`/`SX`/`WSC` (wrench flats, two perpendicular), `FC`/`WFC`/`LFC` (flat surfaces, position from the left or right end: a conditional position). "Absent" is a parameter value (for example `sc = -1`), with a rule `sc ge 0` driving the suppression. About 30 cross-option refusals (SC with WSC, FC with WFC, flats closer than 2 mm, length range, `M x 2 + N x 2 <= L`): all stay in Rhai | needs the option-set field (*) and decimal step (*); S6; the refusal logic is the bulk |
| misumi.shf.shaft-holder | `family` {slit, side, thick, csha}, `d`, `height` per `d`, plating | 24 (family, D) rows of `dims.csv` + 6 of `csha.csv`; `height` lists in `h_all` and `h_alu` (240 valid codes) | `E-SH{type: STB, STM, STA, WTB, WTA, STBN, STMN}{d}-{h: int 10..80}`; `C-SHA{d}` | Four builds: slit and thick (slit across, horizontal screws), side (side slit, vertical screw), T-shaped `C-SHA` (own sketch). Base holes 2 or 4, clamp screws 1 or 2 (D 30 to 50), counterbore and clearance by row; height is a free value from a per-row list | fits with S4 (family branches) and S5 (height list per row) |
| misumi.sth.flanged-shaft-support | flange `round`/`square`/`compact`, body kind (std, thick `N`, end-mounting `X`, slit `W`, clamp `MR`), `long` bool, `B` black or plated, `d` | 412 valid (type, D) pairs (47 types) from 59 dimension rows in 6 CSVs | six templates, for example `E-[S]STH[{series: X=end, W=slit, M=clamp}][N]{shape: R, S, C}[B][L]{d}` | Three flange sketches (circle, cut-corner square, filleted rectangle) x five bodies. Set-screw stations 1 or 2 (spacing `l1`, two screws each, 90 degrees apart), clamp stations 1 or 2 (long slit sleeve): pattern counts. Blind or through bore, counterbore | fits with S4 (flange sketches, body kinds) |
| misumi.sth.dowel-flanged-shaft-support | `shape` {R, C}, plating, `d` 12..30 | 25 valid codes from `dims.csv` (5 rows) | `E-[S]STHW{shape: R, C}[B]K{d}` (5 types) | Round flange; compact = two flat cuts (suppressed on round); four mounting holes and two positioning holes in both shapes, their positions differing by shape (position columns); one clamp screw | fits as is |
| misumi.sth.pilot-flanged-shaft-support | `shape` {R, C}, `d` 8..40 | 18 rows from `dims.csv` (9 rows) | `E-STHWI{shape: R, C}B{d}` | Flange is a circle or a rounded rectangle (two alternative sketches), pilot-and-sleeve cylinder, holes from the top face | fits with S4 (two flange sketches) |

Reading the S4 label: it is the per-row choice between mutually exclusive features (suppress all but one per row). The suppression
columns and rules exist; what is untested is whether a later feature can target "the body" when the feature that creates it differs
by row (the Python builders give every alternative the same body name), and how a split that makes two bodies is named.

## 4. Capabilities needed, ranked

| # | Capability | Generators needing it | Status | Where / note |
|---|---|---|---|---|
| S7 | Metadata text (part number, description, material) bound to the code and row | 18 | missing | no expression on `component.metadata.set`; a text parameter column in the table plus a binding, or Rhai at insert time |
| S9 | Source id, page and status per configuration row | 18 | missing | generate rows from the CSVs; keep `PROVENANCE.md` generated from them |
| S11 | Cross-field validity with a message ("no such row") | 18 | proposal only (Rhai `table`, `refuse`) | the template checks one field at a time; the table has no "no row" |
| S1 | Per-row feature suppression and suppress-if (rule on a parameter) | 17 (all but housing-g) | exists | `docs/configurations.md` |
| S8 | Thread / hole designation from a parameter | 14 | missing | one thread feature per size, suppressed by row; or `solid.thread` automatic size from a tap-drill bore |
| S3 | Arithmetic functions in expressions (`floor`, `min`, `tan`, `sqrt`, `mod`) | 13 | exists | `docs/book/src/guide/parameters.md` |
| S2 | Parameter-driven pattern count (rail holes, blocks, wrench rows, screw stations) | 10 | exists | registry; a count of 1 is suppression (the Python builders guard `> 1` too) |
| S5 | Allowed values or ranges for a free number per row (max length per size, length lists, heights) | 8 (mg, eg, hg, rg, hfs, ofb, sfj, shf) | exists | `allow_parameter_values`, `parameter_range` rules, one set per key |
| S4 | Per-row sketch or feature-set choice (different cross-sections) | 7 (hfs, lb, ofb, scs, shf, sth-flanged, sth-pilot) | exists in principle, needs a test | suppression of alternative extrude and revolve features; sketch entities cannot be suppressed |
| S6 | `component.insert_design` with free parameter values (`length`, `blocks`) | 6 (mg, eg, hg, rg, hfs, sfj) | missing | `document` (the design as JSON) after `--param`, or one configuration row per code |
| S10 | Template kinds beyond the proposal: unordered option set with arguments (hfs, sfj); decimal with step (hfs, sfj, eg, hg, rg); trailing free text `+...` (mg, eg, hg, rg) | 6 | missing in the proposal | the package format already has `flags`; step/decimal are in `runtime/package.py` |
| S12 | Conditional value (`if`) | 6 (hfs, sfj, lb, rg, lhb x2) | missing in expressions; exists as `drive_parameter` rules | or a 0/1 or +1/-1 parameter times the term |

Other gaps that are not capabilities of the list above:

* Rows at scale: lb 480, sth-flanged 412, shf 240, ofb 159 (type, d) rows, scs 153. A suppression column per optional feature on
  that many rows is untested; the row limit is not documented (rules are limited to 2048).
* Per-face appearance in a configuration is restricted to certified face roles (`docs/configurations.md`). The HIWIN appearance
  (ground and raceway faces, chamfers, grooves) is by point today; body-level appearance columns exist, face-level ones do not
  cover chamfer or groove faces. Appearance is not a catalogue dimension and is never checked.
* A linked component holds bodies only (`docs/book/src/guide/assemblies.md`). The claim that the inserted part "stays parametric"
  needs either that doc to change or the part to be edited via Open Linked Design.
* Picked references: the Python builders chamfer and recolour by point (`solid.chamfer edges=[[x,y,z]]`, `appearance.assign
  faces=[[x,y,z]]`, `solid.thread face=[x,y,z]`). In a `.sc` modelled once these become stored feature references; they must be
  re-picked, not translated.

## 5. Answers to the three questions

### (1) What cannot be a table plus parameters, and what it would need

None is impossible; three groups need something. Loops: block counts and rail hole counts (MG, EG, HG, RG) are a pattern whose count
is an expression, which exists; the same holds for wrench-hole rows (HFS), mounting-hole rows (LHB), screw and clamp stations (STH,
SHF). Optional features (taps, flats, caps, dowels, tabs, fixing holes) are suppress-if on a parameter, which exists (rules,
`docs/configurations.md`); the open point is the "absent" convention for options that carry a number (SFJ `SC0` is present at 0).
What does not fit as is: profiles with a different topology (HFS four sections, LB and OFB barrel plus flange kinds, SCS, SHF, STH
flanges) need a per-row choice between alternative features (S4) and, for LB and OFB, a re-modelled revolve profile because a sketch
polyline cannot drop vertices; and any free number (length, block count) needs a value at insert time (S6), because
`component.insert_design` takes a configuration row and nothing else, and the linked part keeps no parameters.

### (2) Can `tools/check` keep working

Yes, with the measurement side unchanged: `inspect.measure`, `model.faces`, `model.threads`, `inspect.interference`,
`component.metadata` and `document.metadata` are what `src/check.py` already calls. Two ways, both usable: (a) build per configuration
row in the design itself, one `solidcraft-cli run` that chains `config.activate {row}`, the parameter values of the code
(`--param NAME=EXPR` or `parameters.change`), then the measurement commands, with the expected values read from the same CSV rows (not
circular for the wiring: a parameter bound to the wrong feature shows as a wrong bbox, hole diameter or position); (b) insert per
code with `component.insert_design {path, configuration}` (or `document` carrying the changed parameters) into an empty assembly and
measure the bodies, to prove that what a user inserts matches (a), by comparing volume and bbox from `inspect.measure`. In (b) the
inserted component holds bodies only, so thread and parameter-level facts are read in (a). New checks come for free:
`inspect.parameter_sweep` over `length` (40..2000) reports which values fail or warn, and checks the limits a generator declares.
`codes.txt` stays the contract: valid lines must parse through the template to parameters and build, `!` lines must be refused.

### (3) Does RFC 0019 search work with a field template instead of a regex

Yes, and it can be compiled to the same index entries. A match entry today is `{id, generator, pattern, flags, confidence
(exact | prefix | possible), params, examples, negative_examples}` (at most 32 per generator, `schema/generator.schema.json`); the
registry applies it with `re.search`. A template compiles mechanically: a choice field to an alternation sorted longest first, a letter
map likewise, `[x]` to `(?:x)?`, `int a..b` to `\d+` (the range is checked outside the regex, as the hand-written `\d{2,4}` already
does), separators to `\s*`, case to the `i` flag, `params` from the field names (`size = "{size}"`), several templates to several
entries. What the index needs from a template is a literal prefix for lookup (the leading literal, or each leading choice expanded:
`MGN`, `HFS5`, `E-LBH`), a handful of positive and negative examples (kept authored and checked by running the template, as
`validate()` does now), and a confidence: `exact` when every field parsed against its allowed values, `prefix` when the template ran
out of input after a valid start (a template gives this for free, a regex does not), `possible` otherwise. Three limits: a template
checks fields one at a time, so it over-accepts valid-looking combinations (as the regexes do now: the `!` lines in `codes.txt`), and
the index should run the generator's parse (`code_template` then `refuse`) as the authority on the candidates it found; separators
that carry meaning (`E-SFJ12-5` against `E-SFJ125`, the `-` between `d` and `l` in OFB, SCS, SHF) need a "required separator" mark
or search accepts a spaceless run of digits; and the unordered option tails (HFS, SFJ) and the free `+...` tail (HIWIN) need the
kinds marked (*) above, otherwise those generators declare only the prefix up to the tail.
