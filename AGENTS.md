# solidcraft-parts: instructions for agents

A router. Hard rules first, then where to look. Humans: CONTRIBUTING.md and README.md.

## Hard rules
- Only the vendor's published catalogue pages. Never vendor CAD, logos or photos in the repo, and no tooling that compares against vendor CAD (MISUMI's CAD terms forbid analysing the data).
- Every dimension is a row in `data/*.csv` with a source id and page, cited in `sources.toml`. Code only reads tables.
- Anything not in the catalogue is appearance: named `... (appearance, approximate)`, listed in `generator.toml` `not_guaranteed`, never dimension-checked.
- `packages/*.generator.json` are generated (`tools/export-package`); never edit by hand. `PROVENANCE.md` and `index/catalog.json` are generated (`tools/provenance`, `tools/build-index`); never edit them by hand.
- Every code in `codes.txt` must pass `tools/check` on the current SolidCraft release before anything is committed. Invalid codes must be rejected with a message.
- No personal paths or addresses in any file. English only. Nothing is pushed, tagged or released without the maintainer's go.

## Where to look
| Working on | Read |
|---|---|
| A new generator or series | README.md "Add a generator", CONTRIBUTING.md, an existing `vendors/*/*/*/` folder |
| The manifest and `[declares]` | `schema/generator.schema.json`, RFC 0019 (global search) in the SolidCraft docs |
| Dimensions and citations | `data/*.csv`, `sources.toml`, `schema/sources.schema.json` |
| The spec check | `runtime/check`, the generator's `src/check.py` |
| Screenshots and previews | `tools/shots`, `tools/preview`, the generator's `src/shots.py` |
| Generator packages (`packages/`, SolidCraft `solidcraft-generator/1`) | `docs/generator-package.md`, `runtime/package.py`, `runtime/package_export/`, `tools/export-package`, `tools/package-equiv` |
| Commits, versions, tags, CI scope, owners | `docs/repository-layout.md`, `tools/commit-scope`, `tools/versions` |
| Provenance and the guarantee levels | `runtime/provenance.py`, `tools/provenance`, `tools/build-index` |
