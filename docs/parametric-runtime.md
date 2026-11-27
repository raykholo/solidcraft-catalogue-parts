# Parametric runtime

All 15 parametric harnesses use `runtime/parametric/`. Generator folders retain geometry construction, catalogue mapping, fixtures and entry points; CLI execution, Rhai calls, measurement adapters and faithfulness conversion live in the shared package. `runtime/fieldtemplate.py` and `runtime/rhai-run` are unchanged.

`ci.sh` first runs the original build and proof and converts its results. Its final `python3 -m runtime.parametric.links GENERATOR OUTDIR` call inspects `solidcraft-cli commands` once per process. If `component.set_link_parameters` is absent, the existing faithfulness file is left byte-for-byte unchanged by this final step. No version-number heuristic enables link checks.

On a supporting build the link proof inserts the fixture code's resolved configuration and parameter map into an empty assembly, measures it against that code built directly by Python, then changes the returned component id with `merge: true` and compares against the second code built directly. HIWIN reference builds disable appearance, screws, caps and the base plate, as its original harness does. The source `.sc` is never edited by these tests.

The third command attempts the fixture's invalid value. Since the draft specifies the refusal semantics but no fixed error string, the row uses `direct={"refused": true}` and preserves the verbatim CLI refusal under `changed.message`. `changed.refused` is true only if the command refuses and its message names the parameter and a rule/restriction. Acceptance, unrelated topology errors and unknown commands fail. `tools/parametric-verdict` recognizes this sentinel; numeric tolerances, spec counts and rejection-message equality retain their existing rules. A failed link proof records a failing rebuild row.

Historical errors in READMEs remain literal 0.50.0 observations. Link and generator-command dependencies say "needs #23175 (our draft, being finished)". Parameter-driven thread designations are follow-ups outside that draft, as its documentation states. Ordinary source parameter edits still do not enforce range restrictions; the draft checks link overrides.

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

- `Package.__init__(self, folder, no_match=None)`: Retained harness operation using the shared runtime.
- `Package.rhai(self, fn, arg)`: Retained harness operation using the shared runtime.
- `Package.parse(self, code)`: -> {ok, parameters, configuration, template, fields, provenance} or {ok: False, reason, message}
- `Package.code(self, fields)`: Retained harness operation using the shared runtime.

### runtime/parametric/process.py

- `run_build(cmds, src=None, save=None, workdir=None, detailed=False, executable=None)`: Adapter preserving the existing harness calling convention.
- `drop_default(source, target, workdir, executable)`: Try removing the seeded Default row, retaining the original design on refusal.

### runtime/parametric/results.py

- `dependencies(blocked)`: Describe draft-provided link features separately from thread follow-ups.
- `measurement(value, absolute=False)`: Normalize a measurement, retaining HIWIN's absolute bounds and MISUMI's extents.
- `spec(value)`: Format the existing passed/total spec count.
- `convert(results, gid, blocked, layout='standard')`: Convert a results dictionary without changing its row order or numeric values.
- `convert_hiwin(directory)`: Convert HIWIN report.json and rebuild.json with their original absolute bounding boxes.
- `write_faithfulness(source, target, gid, blocked, layout='standard')`: Read results and write the common verdict schema; performs no CLI calls.

## Local verification

`python tools/test-parametric-runtime` exercises capability gating and caching, byte preservation on unsupported builds, returned component ids, merge maps, refusal validation, existing verdict comparisons, fixture code validity and HIWIN absolute bounds. It never invokes SolidCraft or Rhai. All six committed results files also convert and pass the verdict tool with their numeric rows unchanged. SolidCraft execution, real link measurements, draft refusal text and CI artifact download remain for CI.

## Changed files

- `.github/workflows/parametric.yml`
- `COMMIT_MSG.txt`
- `docs/parametric-runtime.md`
- `runtime/parametric/__init__.py`
- `runtime/parametric/absolute.py`
- `runtime/parametric/build.py`
- `runtime/parametric/bushing.py`
- `runtime/parametric/harness.py`
- `runtime/parametric/kit.py`
- `runtime/parametric/links.py`
- `runtime/parametric/package.py`
- `runtime/parametric/process.py`
- `runtime/parametric/results.py`
- `runtime/parametric_build.py`
- `runtime/parametric_harness.py`
- `runtime/paramkit.py`
- `runtime/pharness.py`
- `tools/parametric-verdict`
- `tools/test-parametric-runtime`
- `vendors/hiwin/mg/rail-set/PROVENANCE.md`
- `vendors/hiwin/mg/rail-set/generator.toml`
- `vendors/hiwin/mg/rail-set/parametric/README.md`
- `vendors/hiwin/mg/rail-set/parametric/ci.sh`
- `vendors/hiwin/mg/rail-set/parametric/faithfulness.py`
- `vendors/hiwin/mg/rail-set/parametric/harness/run_all.py`
- `vendors/hiwin/mg/rail-set/parametric/harness/stub.py`
- `vendors/hiwin/mg/rail-set/parametric/link_checks.json`
- `vendors/misumi/hbl/bracket/PROVENANCE.md`
- `vendors/misumi/hbl/bracket/generator.toml`
- `vendors/misumi/hbl/bracket/parametric/README.md`
- `vendors/misumi/hbl/bracket/parametric/build.py`
- `vendors/misumi/hbl/bracket/parametric/ci.sh`
- `vendors/misumi/hbl/bracket/parametric/faithfulness.py`
- `vendors/misumi/hbl/bracket/parametric/pkgfiles.py`
- `vendors/misumi/hbl/bracket/parametric/run_codes.py`
- `vendors/misumi/hfs/extrusion/PROVENANCE.md`
- `vendors/misumi/hfs/extrusion/generator.toml`
- `vendors/misumi/hfs/extrusion/parametric/README.md`
- `vendors/misumi/hfs/extrusion/parametric/build.py`
- `vendors/misumi/hfs/extrusion/parametric/ci.sh`
- `vendors/misumi/hfs/extrusion/parametric/faithfulness.py`
- `vendors/misumi/hfs/extrusion/parametric/link_checks.json`
- `vendors/misumi/hfs/extrusion/parametric/pkgfiles.py`
- `vendors/misumi/hfs/extrusion/parametric/run_codes.py`
- `vendors/misumi/hnt/t-nut/PROVENANCE.md`
- `vendors/misumi/hnt/t-nut/generator.toml`
- `vendors/misumi/hnt/t-nut/parametric/README.md`
- `vendors/misumi/hnt/t-nut/parametric/build.py`
- `vendors/misumi/hnt/t-nut/parametric/ci.sh`
- `vendors/misumi/hnt/t-nut/parametric/faithfulness.py`
- `vendors/misumi/hnt/t-nut/parametric/run_codes.py`
- `vendors/misumi/lb/linear-bushing/PROVENANCE.md`
- `vendors/misumi/lb/linear-bushing/generator.toml`
- `vendors/misumi/lb/linear-bushing/parametric/README.md`
- `vendors/misumi/lb/linear-bushing/parametric/build.py`
- `vendors/misumi/lb/linear-bushing/parametric/ci.sh`
- `vendors/misumi/lb/linear-bushing/parametric/faithfulness.py`
- `vendors/misumi/lb/linear-bushing/parametric/link_checks.json`
- `vendors/misumi/lb/linear-bushing/parametric/pcommon.py`
- `vendors/misumi/lb/linear-bushing/parametric/pkgfiles.py`
- `vendors/misumi/lb/linear-bushing/parametric/rhai_equiv.py`
- `vendors/misumi/lb/linear-bushing/parametric/run_codes.py`
- `vendors/misumi/lhb/bushing-housing/PROVENANCE.md`
- `vendors/misumi/lhb/bushing-housing/generator.toml`
- `vendors/misumi/lhb/bushing-housing/parametric/README.md`
- `vendors/misumi/lhb/bushing-housing/parametric/build.py`
- `vendors/misumi/lhb/bushing-housing/parametric/ci.sh`
- `vendors/misumi/lhb/bushing-housing/parametric/faithfulness.py`
- `vendors/misumi/lhb/bushing-housing/parametric/link_checks.json`
- `vendors/misumi/lhb/bushing-housing/parametric/report.py`
- `vendors/misumi/lhb/bushing-housing/parametric/run_codes.py`
- `vendors/misumi/lhb/housing-g/PROVENANCE.md`
- `vendors/misumi/lhb/housing-g/generator.toml`
- `vendors/misumi/lhb/housing-g/parametric/README.md`
- `vendors/misumi/lhb/housing-g/parametric/build.py`
- `vendors/misumi/lhb/housing-g/parametric/ci.sh`
- `vendors/misumi/lhb/housing-g/parametric/faithfulness.py`
- `vendors/misumi/lhb/housing-g/parametric/link_checks.json`
- `vendors/misumi/lhb/housing-g/parametric/report.py`
- `vendors/misumi/lhb/housing-g/parametric/run_codes.py`
- `vendors/misumi/lhb/tall-housing/PROVENANCE.md`
- `vendors/misumi/lhb/tall-housing/generator.toml`
- `vendors/misumi/lhb/tall-housing/parametric/README.md`
- `vendors/misumi/lhb/tall-housing/parametric/build.py`
- `vendors/misumi/lhb/tall-housing/parametric/ci.sh`
- `vendors/misumi/lhb/tall-housing/parametric/faithfulness.py`
- `vendors/misumi/lhb/tall-housing/parametric/link_checks.json`
- `vendors/misumi/lhb/tall-housing/parametric/report.py`
- `vendors/misumi/lhb/tall-housing/parametric/run_codes.py`
- `vendors/misumi/ofb/oil-free-bushing/PROVENANCE.md`
- `vendors/misumi/ofb/oil-free-bushing/generator.toml`
- `vendors/misumi/ofb/oil-free-bushing/parametric/README.md`
- `vendors/misumi/ofb/oil-free-bushing/parametric/build.py`
- `vendors/misumi/ofb/oil-free-bushing/parametric/ci.sh`
- `vendors/misumi/ofb/oil-free-bushing/parametric/faithfulness.py`
- `vendors/misumi/ofb/oil-free-bushing/parametric/link_checks.json`
- `vendors/misumi/ofb/oil-free-bushing/parametric/pcommon.py`
- `vendors/misumi/ofb/oil-free-bushing/parametric/pkgfiles.py`
- `vendors/misumi/ofb/oil-free-bushing/parametric/rhai_equiv.py`
- `vendors/misumi/ofb/oil-free-bushing/parametric/run_codes.py`
- `vendors/misumi/scs/collar/PROVENANCE.md`
- `vendors/misumi/scs/collar/generator.toml`
- `vendors/misumi/scs/collar/parametric/README.md`
- `vendors/misumi/scs/collar/parametric/build.py`
- `vendors/misumi/scs/collar/parametric/ci.sh`
- `vendors/misumi/scs/collar/parametric/faithfulness.py`
- `vendors/misumi/scs/collar/parametric/pkgfiles.py`
- `vendors/misumi/scs/collar/parametric/run_codes.py`
- `vendors/misumi/sfj/shaft/PROVENANCE.md`
- `vendors/misumi/sfj/shaft/generator.toml`
- `vendors/misumi/sfj/shaft/parametric/README.md`
- `vendors/misumi/sfj/shaft/parametric/build.py`
- `vendors/misumi/sfj/shaft/parametric/ci.sh`
- `vendors/misumi/sfj/shaft/parametric/faithfulness.py`
- `vendors/misumi/sfj/shaft/parametric/link_checks.json`
- `vendors/misumi/sfj/shaft/parametric/run_codes.py`
- `vendors/misumi/shf/shaft-holder/PROVENANCE.md`
- `vendors/misumi/shf/shaft-holder/generator.toml`
- `vendors/misumi/shf/shaft-holder/parametric/README.md`
- `vendors/misumi/shf/shaft-holder/parametric/build.py`
- `vendors/misumi/shf/shaft-holder/parametric/ci.sh`
- `vendors/misumi/shf/shaft-holder/parametric/faithfulness.py`
- `vendors/misumi/shf/shaft-holder/parametric/link_checks.json`
- `vendors/misumi/shf/shaft-holder/parametric/pkgfiles.py`
- `vendors/misumi/shf/shaft-holder/parametric/run_codes.py`
- `vendors/misumi/sth/dowel-flanged-shaft-support/PROVENANCE.md`
- `vendors/misumi/sth/dowel-flanged-shaft-support/generator.toml`
- `vendors/misumi/sth/dowel-flanged-shaft-support/parametric/README.md`
- `vendors/misumi/sth/dowel-flanged-shaft-support/parametric/build.py`
- `vendors/misumi/sth/dowel-flanged-shaft-support/parametric/ci.sh`
- `vendors/misumi/sth/dowel-flanged-shaft-support/parametric/run_codes.py`
- `vendors/misumi/sth/flanged-shaft-support/PROVENANCE.md`
- `vendors/misumi/sth/flanged-shaft-support/generator.toml`
- `vendors/misumi/sth/flanged-shaft-support/parametric/README.md`
- `vendors/misumi/sth/flanged-shaft-support/parametric/build.py`
- `vendors/misumi/sth/flanged-shaft-support/parametric/ci.sh`
- `vendors/misumi/sth/flanged-shaft-support/parametric/run_codes.py`
- `vendors/misumi/sth/pilot-flanged-shaft-support/PROVENANCE.md`
- `vendors/misumi/sth/pilot-flanged-shaft-support/generator.toml`
- `vendors/misumi/sth/pilot-flanged-shaft-support/parametric/README.md`
- `vendors/misumi/sth/pilot-flanged-shaft-support/parametric/build.py`
- `vendors/misumi/sth/pilot-flanged-shaft-support/parametric/ci.sh`
- `vendors/misumi/sth/pilot-flanged-shaft-support/parametric/run_codes.py`
