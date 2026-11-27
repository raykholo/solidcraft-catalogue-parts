# One repository, many generators

Every generator lives in its own folder, `vendors/<vendor>/<series>/<generator>/`, and is versioned, tagged, checked, reviewed and (if it
ever has to) moved on its own. The folder is the unit; the repository only shares the runtime, the schemas, the tools and the CI.

1. **History by path.** `git log -- vendors/misumi/hfs/extrusion/` is that generator's history; `git blame` and `git log -p` work the same way.
2. **Commit subjects name the generator.** A commit that touches one generator folder only starts its subject with that generator's id or a
   dotted prefix of it: `misumi.hfs.extrusion: area and Ix/Iy from the printed table`, or `misumi.hfs: ...`, or `misumi: ...`. Commits that touch shared code
   (`runtime/`, `tools/`, `docs/`, workflows) or several generators are free-form. `tools/commit-scope <range>` checks it, from the pre-push hook and the
   `privacy` workflow, on the new commits only; old history is not rewritten.
3. **Versions and tags per generator.** The `version` in a generator's `generator.toml` (x.Y.Z) is that generator's own. A pull request that changes a
   generator's files must raise it (`tools/versions check origin/main`, run by `generator.yml`): patch for a fix, minor for a new code or feature.
   Needing no bump: `checks/` (a re-check on a new SolidCraft release), `PROVENANCE.md`, `review.toml`, the folder's `README.md`, `preview.png`, `shots/`.
   After the merge, the `tag` workflow creates the tag `<id>/v<version>` (for example `misumi.hnt.t-nut/v0.1.1`) for each generator whose version changed.
   The tag is made by the workflow, never by hand. A fix bumps only that generator; the others keep their version and tag.
4. **CI runs only what changed.** On a pull request `generator.yml` takes the folders the diff touches and runs the spec check (`tools/check`) for those alone
   (all generators when `runtime/`, `schema/` or `tools/` changed); the cheap whole-tree checks (provenance, lint, index, packages) always run. Where a
   generator has a parametric form, `parametric.yml` builds a matrix with one job per touched generator (all when `runtime/` or `tools/` changed).
   Pushes to main and manual runs cover every generator.
5. **Owners per folder.** `.github/CODEOWNERS` lists the vendor folders with their maintainers, so GitHub asks them to review changes to their generators. The
   file explains how to add one.

## A fix after the fact

One small pull request, in one folder: the fix (data row, source citation, code), the new `checks/` and `PROVENANCE.md` that `tools/check` and
`tools/provenance` write, and the version bump in that `generator.toml`. Its subject starts with the generator id. A change to `sources.toml` or `data/`
voids the review until it is re-read (`docs/review.md`). When it is merged, the workflow tags `<id>/vX.Y.Z`; users of that generator take the tag, and no other
generator is touched.

## Moving a generator out

Nothing ties a folder to this repository. `git subtree split --prefix vendors/<vendor>/<series>/<generator> -b <branch>` writes a branch whose root is
the generator folder and whose history is exactly the commits that touched it (for `vendors/misumi/hnt/t-nut`: 3 commits, with their original authors and dates). Push the
branch to a new repository's `main` and that generator has its own repository; copy `runtime/`, `schema/` and `tools/` beside it as the other generators do.
`git subtree` ships with git's contrib files; some distributions package it separately.

Outside parties do the same without asking: publish a repository with a generator in this shape, and list it through the parts index
(`tangency-labs/solidcraft-parts`, the Parts Library listing) with a pull request that names the repository and a tag.
