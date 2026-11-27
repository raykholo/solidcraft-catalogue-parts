# Contributing these generators to the official repository

The proposed official repository is `tangency-labs/solidcraft-generators`. The generators here are offered there as **separate pull requests,
one generator per pull request**, not as a bulk transfer. The first pull request carries the repository skeleton and the shared code
it needs plus one generator; every later one adds exactly one generator folder.

## What is offered, and in what order

`docs/contribution-order.toml` lists all 18 generators, strongest evidence first, with one line of reason each (the first three were fixed by
the maintainer). `tools/split` reads it.

## The skeleton (pull request 1)

Everything is shared and small (about 1,100 lines of Python), so all of `runtime/` goes in with the first generator:
`sc`, `table`, `check`, `appearance`, `registry`, `provenance`, `schema`, `privacy`. With it:

- `schema/`: `generator`, `recipe` and `sources` schemas.
- `tools/`: `gen`, `check`, `shots`, `preview`, `render`, `provenance`, `lint`, `build-index`, `privacy`, `commit-scope`, `versions` and `hooks/pre-push`.
- `.github/workflows/`: `generator.yml` (spec check, version bump, provenance, lint, index), `privacy.yml` (also the commit-subject check) and `tag.yml` (per-generator tags).
- `.github/CODEOWNERS`: a template with no owners yet (the official maintainers fill in their handles; the file says how).
- `docs/repository-layout.md`: why one repository holds many generators.
- `LICENSE`, `NOTICE`, `.gitignore`, and `README.md`, `CONTRIBUTING.md`, `AGENTS.md` written for the new repository (`docs/upstream-skeleton/`),
  plus `docs/review.md` and `docs/grammar.md` (each generator brings its own section of it).

Left out on purpose: `library.toml`, `tools/release`, `release.yml`, `schema/parts-library.schema.json` and `docs/parts-library.md` (the
parts-library release of this repository is a separate packaging job, not part of a generator), `index.yml` (its publishing step is a
placeholder; `generator.yml` already checks that `index/catalog.json` is current), and the candidates and clean-room review notes of this
repository. `tools/lint` only checks `library.toml` when the file exists.

## Regenerate the series locally

```
tools/split --out /var/tmp/solidcraft-generators        # all 18; --upto N for the first N; rebuilding replaces the folder
```

It builds a fresh git repository with no remote. `main` and `gen/01-misumi.hnt.t-nut` are the skeleton plus generator 1; each later
branch `gen/NN-<id>` is the branch before it plus one generator folder, the regenerated `index/catalog.json`, its row in the README table
and its `docs/grammar.md` section. Every commit is by `Ray <...@users.noreply.github.com>` with no trailer. Unless `--no-verify`, it runs
`tools/lint`, `tools/provenance --check`, `tools/build-index --check` and `tools/privacy` over each branch's own commits and prints the table.
It does not run `tools/check` (heavy; needs SolidCraft). Run `tools/check vendors/<vendor>/<series>/<generator>` yourself on the current
release before opening a pull request if the release has moved since `checks/` was written; CI runs it anyway.

## Open the pull requests

Once the official repository exists (ask the maintainers for an empty `main` made of one empty commit, so the first branch applies without
conflicts; if they started it with a README or LICENSE, resolve those two files by keeping the repository's own):

```
cd /var/tmp/solidcraft-generators
git remote add upstream https://github.com/tangency-labs/solidcraft-generators.git      # or your fork, then open the PR from it
git fetch upstream
git rebase --onto upstream/main --root gen/01-misumi.hnt.t-nut                          # first branch only: replay on the new main
git push upstream gen/01-misumi.hnt.t-nut                                               # open pull request 1 against main
```

Then, one at a time:

1. Wait for pull request N-1 to merge (CI green, reviewer sign-off).
2. `git fetch upstream`, then rebase branch N onto the updated main: `git rebase --onto upstream/main gen/<N-1>-<id> gen/<N>-<id>`
   (the old tip of branch N-1 is the fork point; a squash merge changes the commits but not the tree, so the two rebases give the same files).
   Resolve any conflict in `README.md` (the generator table) or `index/catalog.json` (take upstream's, then run `tools/build-index`).
3. Re-run `tools/lint`, `tools/provenance --check` and `tools/build-index --check` on the rebased branch; run `tools/check` on the generator folder
   if SolidCraft has a newer release (commit the new `checks/<version>/` files and run `tools/provenance <dir>` and `tools/build-index`; a changed
   `checks/` does not touch the review, but any change to `sources.toml` or `data/` voids it until it is re-read).
4. `git push upstream gen/<N>-<id>` and open pull request N against main. The text says what was checked and what was not (the generator's
   "Not guaranteed" list) and which review it carries (independent AI re-read, not a person).

If upstream changes the skeleton (a tool, the schema, the runtime) before a later pull request, rebase the remaining branches onto it and let
`tools/lint` and `tools/build-index --check` show what no longer fits. If a pull request is rejected or changed, fix it on its own branch and rebase
the later ones; do not merge two generators into one pull request.

Nothing is pushed from this repository, and the scratch repository has no remote until the official one exists and a maintainer says to go.
