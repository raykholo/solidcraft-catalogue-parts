# Parametric runtime

All 18 parametric harnesses use `runtime/parametric/`. Generator folders retain geometry construction, catalogue mapping, fixtures and entry points; CLI execution, Rhai calls, measurement adapters and faithfulness conversion live in the shared package. `runtime/fieldtemplate.py` and `runtime/rhai-run` are unchanged.

`ci.sh` first runs the original build and proof and converts its results. Its final `python3 -m runtime.parametric.links GENERATOR OUTDIR` call inspects `solidcraft-cli commands` once per process. If `component.set_link_parameters` is absent, the existing faithfulness file is left byte-for-byte unchanged by this final step. No version-number heuristic enables link checks.

On a supporting build the link proof inserts the fixture code's resolved configuration and parameter map into an empty assembly, measures it against that code built directly by Python, then changes the returned component id with `merge: true` and compares against the second code built directly. HIWIN reference builds disable appearance, screws, caps and the base plate, as its original harness does. The source `.sc` is never edited by these tests.

The third command attempts the fixture's invalid value. Since the draft specifies the refusal semantics but no fixed error string, the row uses `direct={"refused": true}` and preserves the verbatim CLI refusal under `changed.message`. `changed.refused` is true only if the command refuses and its message names the parameter and a rule/restriction. Acceptance, unrelated topology errors and unknown commands fail. `tools/parametric-verdict` recognizes this sentinel; numeric tolerances, spec counts and rejection-message equality retain their existing rules. A failed link proof records a failing rebuild row.

Historical errors in READMEs remain literal 0.50.0 observations. Link and generator-command dependencies say "needs #23175 (our draft, being finished)". Parameter-driven thread designations are follow-ups outside that draft, as its documentation states. On #23175-capable hosts, limit rules opt into `enforce_on_edit`; CI checks ordinary edit refusals and link overrides. Release hosts retain the existing rules.

## Link fixtures

Values below are test inputs, not new catalogue dimensions. Valid values resolve through the package's field templates, Rhai and CSV tables; invalid values exceed the model's existing range or allowed-values rules.

| Generator | Parameter | Insert | Change | Refuse |
|---|---|---|---|---|
| hiwin.mg.rail-set | length | 400 mm | 300 mm | 3000 mm |
| misumi.hfs.extrusion | length | 300 mm | 1000 mm | 4001 mm |
| misumi.sfj.shaft | L | 100 mm | 60 mm | 1501 mm |
| misumi.shf.shaft-holder | h | 40 mm | 25 mm | 81 mm |
| misumi.ofb.oil-free-bushing | blen | 40 mm | 30 mm | 9999 mm |
| misumi.lb.linear-bushing | blen | 80 mm | 42 mm | 9999 mm |
| misumi.lhb.housing-g | hc | 25 mm | 15 mm | 60 mm |
| misumi.lhb.bushing-housing | dowel | 1 | 0 | 2 |
| misumi.lhb.tall-housing | dowel | 1 | 0 | 2 |

HBL brackets, SCS collars, HNT nuts and the three STH packages have no free ordering parameter and add no link rows. Their existing internal dimension and configuration-switch probes are preserved. In particular, the HBL width probe and SCS ring-width probe change the configured source design; their package manifests explicitly describe no free parameter.

## EG, HG and RG guideways

`runtime/parametric/guideway.py` runs the guideway proof, including its process pool, working-copy rebuilds, positional block-name adaptation for spec checks, and report writing. The vendor `gw_harness.py` retains only series-specific fixture plans. `gw_stub.py` selects the shared `Package` adapter's no-match message and typed-code field; `gw_faith.py` supplies dependency descriptions to the shared `guideway` conversion layout. Existing report measurements and faithfulness rows, including absolute bounding boxes, spec counts, labels and ordering, are preserved.

Each guideway adds two optional fixtures through the existing capability gate:

| Series | Parameter | Insert | Change | Refuse |
|---|---|---|---|---|
| EG / HG / RG | length | 1240 mm | 1000 mm | 4001 mm (above the 4000 mm series maximum) |
| EG / HG / RG | blocks | 2 on 640 mm | 1 on 640 mm | 100 (above the 1..99 fallback rule and the fit rule) |

Reference builds use `appearance=False`, matching the original guideway harness. Valid fixture values remain catalogue inputs resolved from each package; no source dimensions or geometry are changed.

All three packages have a final `{raw: ...}` refusal template. Invalid block grammar and RG's unsupported stainless suffix reach that catcher rather than reconstructing the code from canonical fields. The shared host can also supply `raw_code` without changing returned fields or round trips. Decimal spellings such as `1000.0` remain in shape-refusal messages. Each `codes.txt` includes a decimal rejection, and `gw_parity.py` compares generic shape messages without its former no-template exemption. `gw_readme.py` emits the same updated wording as the checked-in READMEs.

## CI

The workflow uses `matrix.sc_ver` for `0.50.0` and `0.51.1`. A manual `solidcraft_run` adds `pr23175` and downloads `solidcraft-cli` from that run in `raykholo/solidcraft` using `GH_TOKEN`. The artifact may contain the CLI directly or inside a `.tar.gz`. The cached origin/main ref had the original single-version workflow; this uses PR #16's requested matrix shape to ease rebasing. Remote merge status and artifact retrieval were not verified locally.

## API

The following list includes the retained orchestration adapters, so existing calling conventions are explicit.

### runtime/parametric/__init__.py

- `cli(cmds, src=None, save=None, name='step', workdir=None, error_style='legacy')`: Adapter preserving the existing harness calling convention.
- `rhai(pkg, fn, *args)`: Adapter preserving the existing harness calling convention.
- `measure(sc_path, out_dir, tag, threads=True, include_threads=True)`: Adapter preserving the existing harness calling convention.
- `subst(o, old, new)`: The spec check names the body after the code (the Python build does); the inserted body keeps the model's own name:
- `spec_check(mod, part, host_sc, out, body, code)`: Run `mod.check(part, host_sc, out)` with every body reference renamed from `code` to `body`.
- `supports_link_parameters()`: Inspect the JSON command catalogue once per harness process.

### runtime/parametric/absolute.py

- `summarize(m)`: retain absolute bounds and per-body names for guideway spec checks.
- `c(command, **params)`: Adapter preserving the existing harness calling convention.
- `AbsoluteHarness.__init__(self, out)`: Retained harness operation using the shared runtime.
- `AbsoluteHarness.run(self, cmds, name, base=None, save=None, allow_fail=False)`: solidcraft-cli run on `base` (a design) with these commands; -> (results or None, error or None)
- `AbsoluteHarness.measure(self, path, name)`: Retained harness operation using the shared runtime.
- `fmt(m)`: Adapter preserving the existing harness calling convention.
- `same(a, b, tol=1e-06)`: Adapter preserving the existing harness calling convention.

### runtime/parametric/build.py

- `cell(v)`: Adapter preserving the existing harness calling convention.
- `run(cli, cmds, workdir, src=None, save=None)`: Adapter preserving the existing harness calling convention.
- `build_model(spec: Spec, pkg: Path, cli: str)`: Adapter preserving the existing harness calling convention.

### runtime/parametric/bushing.py

- `cli(CLI, cmds, src=None, save=None)`: Adapter preserving the existing harness calling convention.
- `rhai(RHAI, pkg, root, fn, *args)`: Adapter preserving the existing harness calling convention.
- `measure(run_measure, sc_path, out_dir, tag)`: Adapter preserving the existing harness calling convention.
- `resolve(templates, RHAI, pkg, root, code)`: code -> (('ok', result) | ('refused', kind, message), fields)
- `spec_check(pycheck, part, host_sc, out, body)`: Adapter preserving the existing harness calling convention.
- `code_row_cmds(code, res)`: Adapter preserving the existing harness calling convention.
- `insert_code(CLI, pkg_sc, code, res, out, tag)`: Working copy of the package model + a row for the code; a host design inserts it by `configuration`. -> host .sc, working copy, error
- `probe(CLI, results, name, cmds, src)`: Adapter preserving the existing harness calling convention.

### runtime/parametric/guideway.py

- `run(cmds, name, base=None, save=None)`: Shared guideway proof operation; series and plans are supplied by its vendor entry point.
- `measure(path, name)`: Shared guideway proof operation; series and plans are supplied by its vendor entry point.
- `clean(m)`: Shared guideway proof operation; series and plans are supplied by its vendor entry point.
- `python_part(code, tag)`: Shared guideway proof operation; series and plans are supplied by its vendor entry point.
- `instance(parsed, code, tag, extra=None)`: The parametric part at a configuration row and parameter values: 0.50.0 has no free parameters on insert_design, so the values are
- `param_check(s, path, tag)`: Shared guideway proof operation; series and plans are supplied by its vendor entry point.
- `python_check(s, path)`: Shared guideway proof operation; series and plans are supplied by its vendor entry point.
- `do_code(line)`: one line of codes.txt -> the report row
- `do_rebuild(plan)`: Shared guideway proof operation; series and plans are supplied by its vendor entry point.
- `probes()`: what 0.50.0 does with a link: insert a row at its defaults, a free parameter on insert, set_link_parameters, parameters.change in the assembly
- `limits()`: where the model's range rules apply on 0.50.0
- `main(S, plans, par, out)`: Shared guideway proof operation; series and plans are supplied by its vendor entry point.

### runtime/parametric/harness.py

- `measure(sc_path, out_dir, tag)`: Adapter preserving the existing harness calling convention.
- `Harness.__init__(self, gen_dir, pkg_dir, model, support_from, extra_refusals, rebuild, blocked, check_module='check', extra_valid=())`: Retained harness operation using the shared runtime.
- `Harness.rhai(self, fn, *args)`: Retained harness operation using the shared runtime.
- `Harness.resolve(self, code)`: code -> (('ok', result) | ('refused', kind, message), fields)
- `Harness.python_message(self, code)`: Retained harness operation using the shared runtime.
- `Harness.python_part(self, code, out)`: Retained harness operation using the shared runtime.
- `Harness.rows_summary(self, R)`: Retained harness operation using the shared runtime.
- `Harness.insert(self, code, res, out, tag)`: a host design inserting the package model with the row Rhai chose; the component is named after the code
- `Harness.spec_check(self, support, host_sc, out, body, tag)`: Retained harness operation using the shared runtime.
- `Harness.run(self, outdir, only=None)`: Retained harness operation using the shared runtime.
- `Harness.templates_index(self, code)`: Retained harness operation using the shared runtime.
- `faithfulness(results, gen_id, blocked, path)`: Adapter preserving the existing harness calling convention.
- `table_row(pkg, name, key)`: a row of the package's tables/<name>.csv with the cells typed as the Python generator types data/*.csv (empty is None)
- `with_description(cls, description, **kw)`: a Support of the generator (its dataclass) whose description is the text Rhai made
- `main(h: Harness, gen_id: str, blocked, argv=None)`: Adapter preserving the existing harness calling convention.
- `report_md(results)`: results.json -> the markdown tables of a generator's parametric README (python | parametric | spec check | equal?)

### runtime/parametric/kit.py

- `cli(cmds, src=None, save=None, workdir=None)`: Adapter preserving the existing harness calling convention.
- `cli_or_exit(cmds, src=None, save=None, workdir=None, what='solidcraft-cli')`: Adapter preserving the existing harness calling convention.
- `feature_ids(cmds, res)`: Feature ids by name from the creating commands' replies (rules take ids, not names).
- `build_model(pkg: Path, model: str, cmds, columns, feature_cols, rows, rules_fn, first_row)`: Stage 1: `cmds` (user parameters, geometry, suppression). Stage 2: the configuration table (columns = parameters and features, one
- `write_csv(path: Path, header, rows)`: Adapter preserving the existing harness calling convention.
- `package_files_json(pkg: Path, out: Path)`: Every file of the package (the built .sc included) as base64 in one JSON file: CI uploads *.json, so the built model can be committed.
- `tables_of(pkg: Path)`: tables/*.csv of the package as {name: {key: row}}, cells typed as the Python generators read them (runtime.table.num).
- `Runner.__init__(self, g: Gen)`: Retained harness operation using the shared runtime.
- `Runner.resolve(self, code)`: code -> (('ok', result) | ('refused', kind, message))
- `Runner.python_message(self, code)`: Retained harness operation using the shared runtime.
- `Runner.python_part(self, code, out)`: Retained harness operation using the shared runtime.
- `Runner.measure(self, sc_path, out_dir, tag)`: Retained harness operation using the shared runtime.
- `Runner.code_row_cmds(self, res)`: Retained harness operation using the shared runtime.
- `Runner.insert_code(self, res, out, tag)`: Working copy of the package model + a row for the code; a host design inserts it by `configuration`. -> host path, copy path, error
- `Runner.spec_check(self, part, host_sc, out, body)`: Retained harness operation using the shared runtime.
- `say(*a)`: Adapter preserving the existing harness calling convention.
- `main(g: Gen)`: Adapter preserving the existing harness calling convention.
- `rebuild_and_probes(g: Gen, R: Runner, results, work)`: Adapter preserving the existing harness calling convention.
- `report_md(results_path)`: results.json -> the markdown tables of a parametric README (python | parametric | spec check | equal), the refusals, the rebuilds.

### runtime/parametric/links.py

- `resolve(package, code)`: Resolve a fixture through the same field templates and Rhai as the harness.
- `direct(generator, code, work, tag, options=None)`: Build and measure the reference code directly with the Python generator.
- `link_rows(generator, package, model, fixture, work)`: Insert overrides, edit that saved link, and require a parameter-naming refusal.
- `check_links(generator_dir, outdir)`: Append optional link rows to faithfulness.json; unsupported builds keep it unchanged.

### runtime/parametric/package.py

- `Package.__init__(self, folder, no_match=None, no_match_reason="invalid", typed_code_field=None)`: Retained harness operation using the shared runtime.
- `Package.rhai(self, fn, arg)`: Retained harness operation using the shared runtime.
- `Package.parse(self, code)`: -> {ok, parameters, configuration, template, fields, provenance} or {ok: False, reason, message}
- `Package.code(self, fields, index=0)`: Retained harness operation using the shared runtime.

### runtime/parametric/process.py

- `run_build(cmds, src=None, save=None, workdir=None, detailed=False, executable=None)`: Adapter preserving the existing harness calling convention.
- `drop_default(source, target, workdir, executable)`: Try removing the seeded Default row, retaining the original design on refusal.

### runtime/parametric/results.py

- `dependencies(blocked)`: Describe draft-provided link features separately from thread follow-ups.
- `measurement(value, absolute=False)`: Normalize a measurement, retaining HIWIN's absolute bounds and MISUMI's extents.
- `spec(value)`: Format the existing passed/total spec count.
- `convert(results, gid, blocked, layout='standard')`: Convert a results dictionary without changing its row order or numeric values.
- `convert_hiwin(directory, gid="hiwin.mg.rail-set", blocked=None, guideway=False)`: Convert HIWIN report.json and rebuild.json with their original absolute bounding boxes.
- `write_faithfulness(source, target, gid, blocked, layout='standard')`: Read results and write the common verdict schema; performs no CLI calls.

## Local verification

`python tools/test-parametric-runtime` exercises capability gating and caching, byte preservation on unsupported builds, returned component ids, merge maps, refusal validation, existing verdict comparisons, fixture code validity and HIWIN absolute bounds. It never invokes SolidCraft or Rhai. All six committed results files also convert and pass the verdict tool with their numeric rows unchanged. SolidCraft execution, real link measurements, draft refusal text and CI artifact download remain for CI.

## Guideway verification

The targeted runtime contract tests pass, as do the three original-to-shared converter equivalence checks (including failed rebuilds). Real Rhai parity passes with zero differences for EG 3031, HG 3015 and RG 3046 codes: each includes its full rejection battery and 3000 seeded generated codes. All 12 new fixture codes resolve to valid Python builds and matching Rhai configurations/overrides. Actual SolidCraft geometry and link-refusal execution remain for CI.

Generated index and package metadata were refreshed with `tools/build-index` and `tools/export-package`; both `--check` commands pass. The legacy package exports already differed from source metadata on this branch before the guideway edits.

## Changed files

- `COMMIT_MSG.txt`
- `docs/parametric-runtime.md`
- `index/catalog.json`
- `packages/hiwin-mg-rail-set.generator.json`
- `packages/misumi-hfs-extrusion.generator.json`
- `packages/misumi-hnt-t-nut.generator.json`
- `runtime/parametric/absolute.py`
- `runtime/parametric/guideway.py`
- `runtime/parametric/package.py`
- `runtime/parametric/results.py`
- `tools/test-parametric-runtime`
- `vendors/hiwin/eg/guideway/PROVENANCE.md`
- `vendors/hiwin/eg/guideway/codes.txt`
- `vendors/hiwin/eg/guideway/generator.toml`
- `vendors/hiwin/eg/guideway/parametric/README.md`
- `vendors/hiwin/eg/guideway/parametric/ci.sh`
- `vendors/hiwin/eg/guideway/parametric/eg-guideway/generator.rhai`
- `vendors/hiwin/eg/guideway/parametric/eg-guideway/generator.toml`
- `vendors/hiwin/eg/guideway/parametric/link_checks.json`
- `vendors/hiwin/eg/guideway/parametric/package.toml.head`
- `vendors/hiwin/guideway-parametric/gw_faith.py`
- `vendors/hiwin/guideway-parametric/gw_harness.py`
- `vendors/hiwin/guideway-parametric/gw_parity.py`
- `vendors/hiwin/guideway-parametric/gw_readme.py`
- `vendors/hiwin/guideway-parametric/gw_stub.py`
- `vendors/hiwin/hg/guideway/PROVENANCE.md`
- `vendors/hiwin/hg/guideway/codes.txt`
- `vendors/hiwin/hg/guideway/generator.toml`
- `vendors/hiwin/hg/guideway/parametric/README.md`
- `vendors/hiwin/hg/guideway/parametric/ci.sh`
- `vendors/hiwin/hg/guideway/parametric/hg-guideway/generator.rhai`
- `vendors/hiwin/hg/guideway/parametric/hg-guideway/generator.toml`
- `vendors/hiwin/hg/guideway/parametric/link_checks.json`
- `vendors/hiwin/hg/guideway/parametric/package.toml.head`
- `vendors/hiwin/rg/guideway/PROVENANCE.md`
- `vendors/hiwin/rg/guideway/codes.txt`
- `vendors/hiwin/rg/guideway/generator.toml`
- `vendors/hiwin/rg/guideway/parametric/README.md`
- `vendors/hiwin/rg/guideway/parametric/ci.sh`
- `vendors/hiwin/rg/guideway/parametric/link_checks.json`
- `vendors/hiwin/rg/guideway/parametric/package.toml.head`
- `vendors/hiwin/rg/guideway/parametric/rg-guideway/generator.rhai`
- `vendors/hiwin/rg/guideway/parametric/rg-guideway/generator.toml`

The #23175 surface is capability-gated by the command catalogue. Remaining gaps: parameter thread designations (#9594), feature-pattern copy body names (#23457), optional `no_match(raw)` after #23175, an ordered bag/list beside `set(...)`, and cosmetic threads shortened by later cuts (repro sent; follow-up being filed). Hosts without `component.set_link_parameters` retain the inserted-link blocked record.
