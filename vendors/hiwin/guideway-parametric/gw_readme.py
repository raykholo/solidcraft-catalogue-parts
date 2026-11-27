#!/usr/bin/env python3
"""Writes <generator>/parametric/README.md from the model description and the CI results (report.json, rebuild.json of gw_harness).
    python3 gw_readme.py SERIES HARNESS_OUTDIR            (the side-by-side table is the harness' own output, so the README cannot drift from it)"""
import json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gw_model as gm

TEXT = {
"EG": dict(name="EG low-profile guideway", cat="EG series, section 2-2", sizes="15 to 35", blk="EGH and EGW blocks, load S (short, two holes) or C (long, four holes), mounting A (tapped) or B (through, EGW only)",
           rails="EGR rails, mounted from the top (R, or U: the same); the bottom-mounted T rail is refused (the catalogue prints no tapped-hole dimensions)",
           extra="The short S block has one column of two holes: the second hole column is a suppression column of the row. The dust-protection codes ZZ, DD, KK are refused (not drawn)."),
"HG": dict(name="HG guideway", cat="HG series, section 2-1", sizes="15 to 65", blk="HGH and HGW blocks, load C or H, mounting A and C (tapped) or B (through, HGW only)",
           rails="HGR rails mounted from the top (R, counterbored) or from the bottom (T, tapped): both are drawn, the mounting is part of the row (`-R` / `-T`) and switches the hole feature",
           extra="HGL (low square) is refused (not drawn)."),
"RG": dict(name="RG roller guideway", cat="RG series, section 2-9", sizes="15 to 65", blk="RGH (mounting A) and RGW (mounting C) blocks, load C or H, six tapped holes (four on C x B, two on the rail axis: C1 apart on RGW, C apart on RGH)",
           rails="RGR rails mounted from the top (R); T is refused (no tapped-hole dimensions in the catalogue)",
           extra="A dust-protection code (+ZZ, +DD, +KK) replaces the block length L (Table 2-9-22): the answer of the Rhai script carries it as the parameter `L`. RGL, RGS and RGF are refused (not drawn)."),
}

def fmt(m):
    if not m or "error" in m: return "ERROR"
    return f"{m['vol']:.2f} / {m['area']:.2f} / {m['faces']}f {m['bodies']}b"

def main(key, d):
    S = gm.SERIES[key]; T = TEXT[key]; d = Path(d)
    rows = json.load(open(d / "report.json")); rb = json.load(open(d / "rebuild.json"))
    blocks = gm.blocks_of(S); rl = gm.row_list(S, blocks)
    rail_f, block_f, holes, taps, ms = gm.feature_names(S, blocks)
    cols = gm.columns(S)
    par = HERE.parents[0] / S.dirname / "guideway" / "parametric"
    pkg = f"{S.dirname}-guideway"
    nset = sum(1 for r in rl if r[0] == "set"); nblk = sum(1 for r in rl if r[0] == "block"); nrail = sum(1 for r in rl if r[0] == "rail")
    valid = [r for r in rows if not r["code"].startswith("!")]; rej = [r for r in rows if r["code"].startswith("!")]
    eq = sum(1 for r in valid if r["same"]); eqs = sum(1 for r in valid if r.get("check", "").split(" ")[0] == r.get("pycheck", "x").split(" ")[0] and r.get("check"))
    rq = sum(1 for r in rej if r["same"])
    L = []
    w = L.append
    w(f"# {S.gid} as a parametric generator (SolidCraft 0.50.0)")
    w("")
    w(f"The {T['name']} (HIWIN Linear Guideway catalogue G99TE24-2410, {T['cat']}) in the new generator form of issue tangency-labs/solidcraft#22331: "
      f"ONE parametric `.sc` modelled once, a configuration table of the catalogue rows, field templates for the ordering code and `generator.rhai`. "
      f"Every code of `codes.txt` is built both ways (this package and the Python generator) and compared by `tools/parametric-verdict`.")
    w("")
    w(f"Result of the CI run: **{eq}/{len(valid)} valid codes identical** (volume, area, bbox, faces, bodies), **{rq}/{len(rej)} refusals with the Python message word for word**, "
      f"spec check (`src/check.py`) with the same pass count on both parts for {eqs}/{len(valid)} codes. The table below is the harness' own output.")
    w("")
    w("## Layout")
    w("")
    w("```")
    w("parametric/")
    w(f"  {pkg}/                  the package (docs/formats/generator.md, \"Generators: interface (version 2)\")")
    w("    generator.toml          [parameters], three [[template]] (rail, set, block), [rows.*] provenance (generated from ../data/*.csv)")
    w(f"    {pkg}.sc          the parametric model + configuration table + rules (built by gw_build.py)")
    w("    generator.rhai          resolve(fields), describe(fields): plain Rhai with table() and refuse()")
    w("    tables/                 rails.csv, blocks.csv" + (", dust.csv" if key == "RG" else "") + ", params.csv (the catalogue rows, with source / page / status)")
    w("  package.toml.head         the hand-written head of generator.toml")
    w("  ci.sh OUTDIR              build the model, run every code both ways, write OUTDIR/faithfulness.json (tools/parametric-verdict)")
    w("../../guideway-parametric/   what the EG, HG and RG generators share: gw_model.py (the model as a command list), gw_package.py, gw_build.py,")
    w("                            gw_harness.py (codes both ways), gw_faith.py, gw_stub.py (template + Rhai host), gw_parity.py (local Rhai test)")
    w("```")
    w("")
    w("Commands, from the repository root (`SC_CLI` = solidcraft-cli 0.50.0, `RHAI_RUN` = `runtime/rhai-run` built with cargo):")
    w("")
    w("```")
    w(f"bash vendors/hiwin/{S.dirname}/guideway/parametric/ci.sh out        # build + every code both ways + out/faithfulness.json")
    w("tools/parametric-verdict out/faithfulness.json                     # the verdict")
    w(f"python3 vendors/hiwin/guideway-parametric/gw_parity.py {S.key} 3000   # no SolidCraft: Python parse vs template + Rhai on codes.txt and 3000 generated codes")
    w("```")
    w("")
    w("## What the design is")
    w("")
    w(f"- **Scope.** {T['blk']}. Sizes {T['sizes']}. {T['rails']}. {T['extra']}")
    w(f"- **User parameters.** Row-driven (configuration columns): `{' '.join(cols)}`, one value per catalogue row. Free: `length`, `blocks` (columns too, so the "
      f"rules range-check them and the row holds the defaults: 400 mm, 1 block). Derived: `n = floor((length - 2 * Elo + 0.000001 mm) / P) + 1` holes, "
      f"`E = (length - (n - 1) * P) / 2` the end distance, `x0` the start of the first block. `gap` (10 mm) is the illustration choice the Python generator also has.")
    w("- **Rail.** `solid.box length=length width=WR height=HR`, a counterbore `solid.hole` at `x = E` from the top" + (" or a tapped hole of the size's thread from the bottom (one feature per thread designation)" if taps else "") + ", and a feature pattern with `count1 = n`, `spacing1 = P`: the hole count follows `length`.")
    w("- **Blocks.** A U-profile sketch (the rail channel cut in, every coordinate an expression) extruded over `L1`, the mounting holes of the row, and a feature pattern of the block and its holes with `count1 = blocks`, `spacing1 = L + gap` (centred on the rail through `x0`).")
    w(f"- **Rows: {len(rl)}**, three products of the catalogue rows. {nset} rail-with-blocks rows `<block>-<size>" + ("-<R|T>" if S.rm_in_name else "") + f"` (e.g. `{gm.row_name(S, *next(r for r in rl if r[0] == 'set'))}`), {nblk} block-alone rows `<block>-<size>-block` (rail features suppressed, `rail = 0` puts the block at x = 0 as the Python part does), "
      f"{nrail} rail-alone rows (`{gm.row_name(S, *next(r for r in rl if r[0] == 'rail'))}`: block features suppressed).")
    w(f"- **Suppression columns** ({len(rail_f) + len(block_f)} features): per row, the hole alternatives that do not apply are suppressed. Block holes: " + ", ".join(f"`{h}`" for h in holes) + ". " + ("Rail holes: counterbore `Rail hole 1` or the tap of the size (" + ", ".join(taps) + "). " if taps else "") + "The thread designation is not a parameter in 0.50.0, hence one feature per designation.")
    w("- **Rules (`config.rule`).** `length` within the catalogue minimum and the largest single rail (columns `minlen`, `maxlen`); `blocks` from 1 to the number that fits (`floor((length + gap) / (L + gap))`, the Python refusal \"do not fit\"). Checked when a row is activated (0.50.0): see \"Where the limits apply\".")
    w("- **Templates.** Three, tried in order: rail, set, block (`generator.toml`). Size (two digits), block kind, load, mounting, `E` flags, number of blocks, rail mounting, `length` (decimal), preload, accuracy, material, rails and a `+` option tail are fields; everything the catalogue refuses is refused in `generator.rhai` so that the message is the Python generator's, in the same order.")
    w("- **Dimensioned geometry only:** no appearance bodies (chamfers, grooves, end caps and seals, nipple, screws, looks). The Python generator is run with `appearance=False` for the comparison (`build.commands(s, appearance=False)`, `check.check(..., appearance=False)`); the default output of both is unchanged.")
    w("")
    w("## Side by side: every code of codes.txt")
    w("")
    w("Measures: volume mm3 / area mm2 / faces / bodies (the bbox is compared too). `spec` = the generator's own `src/check.py` rows passed, on the parametric part and on the Python part (appearance off); the row `Block i length L` (the catalogue length WITH end caps and seals) cannot pass without the appearance bodies on either part.")
    w("")
    w("| code | Python | parametric | spec (parametric / Python) | identical |")
    w("|---|---|---|---|---|")
    for r in rows:
        if r["code"].startswith("!"):
            w(f"| {r['code']} | {r['python']} | {r['param']} | - | {'same message' if r['same'] else 'DIFFERS'} |")
        else:
            w(f"| {r['code']} | {fmt(r.get('python_m'))} | {fmt(r.get('param_m'))} | {r.get('check', '-').split(' ')[0]} / {r.get('pycheck', '-').split(' ')[0]} | {'yes' if r['same'] else 'NO'} |")
    w("")
    w("## Rebuild on a free parameter change")
    w("")
    w("A free parameter changed on a built part (`parameters.change` on the instance) against the code built directly, both as a fresh parametric instance and as the Python part:")
    w("")
    for x in rb["rebuild"]:
        if "error" in x: w(f"- {x['label']}: ERROR {json.dumps(x['error'])[:200]}")
        else: w(f"- {x['label']}: equals the fresh instance **{x['same_fresh']}**, equals the Python part **{x['same_python']}** ({fmt(x['rebuilt'])})")
    w("")
    w("## What 0.50.0 does with a link, and where the limits apply (measured)")
    w("")
    for k, v in rb["probes"].items(): w(f"- {k}: {v}")
    w("")
    for k, v in rb["limits"].items(): w(f"- {k}: {v}")
    w("")
    w("## What 0.50.0 could not express (the `blocked` list of faithfulness.json)")
    w("")
    w("| Wanted | Result on 0.50.0 | Workaround used (labelled) |")
    w("|---|---|---|")
    w("| Free parameter values on insert | `component.insert_design` accepts a `parameters` key and ignores it silently; `component.set_link_parameters` is unknown (see the measured lines above) | the instance file: `config.activate` + `parameters.change` on a copy of the model, which is then the file that gets inserted |")
    w("| Thread designation from a parameter | `thread: \"M5\"` is a literal | one hole feature per designation (" + ", ".join(ms) + (", " + ", ".join(taps) + " on the rail" if taps else "") + "), the row suppresses all but its own |")
    w("| Names of pattern copies | the copies of a feature pattern are named `Body<N>` | the harness renames them `Block 1..n` by position before `src/check.py` reads them |")
    w("")
    w("What SolidCraft needs (proposals): `component.insert_design {parameters}` stored and applied, `component.set_link_parameters`; `solid.pattern.rectangular {body_names}`; a thread designation that can come from a parameter or a choice; "
      "rules by feature name; range rules enforced on `parameters.change` with an opt-in. See tangency-labs/solidcraft#23175.")
    (par / "README.md").write_text("\n".join(L) + "\n")
    print("wrote", par / "README.md")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
