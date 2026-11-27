# Contributing

## Clean-room and sources (the rules that cannot be broken)

- **Only the vendor's own published catalogue pages.** No vendor CAD (STEP, IGES, native files), no logos, no photos, in the repository or its history.
  `tools/lint` fails on CAD files, on images outside `icon.svg` / `preview.png` / `shots/`, and on `<image>` inside an svg.
- **No other CAD program or generator's code or data** was consulted. Do not copy a number from a distributor, a forum or another library: read it from the vendor page.
- **No comparison against vendor CAD.** MISUMI's CAD terms of use do not clearly allow analysing downloaded CAD data, so this repository has no tool for it and a dimension is never checked against vendor CAD.
  A dimension is only ever set or fixed from the published catalogue.
- **Every dimension cites a source**: `data/*.csv` rows carry a source id and page; `sources.toml` gives catalogue, edition, URL, page, and whether the
  number is printed ("labelled" / "published") or measured from the vector drawing ("measured"). A number that is neither is "approximate" and is shown as appearance only.
- **Appearance is separate and labelled.** Anything not in the catalogue (groove shapes, caps, colours, screws) is tagged "appearance, approximate" in the part
  and listed under `not_guaranteed` in `generator.toml`; it never gets a dimension check.
- **No personal paths or addresses** in any file (`tools/lint`, inflate-aware: PNG chunks are scanned too).
- English everywhere: code, comments, commit messages, docs.

## Pull request checklist

1. One generator (or one data change) per pull request.
2. `tools/check <your generator folder>` passes on the current SolidCraft release; commit the new `checks/<version>/` files.
3. `tools/preview <dir>` (rendered, never a vendor image) and `tools/provenance <dir>`; commit `preview.png` and `PROVENANCE.md`.
4. `tools/lint` and `tools/build-index --check` pass; commit `index/catalog.json` only if CI is not yet generating it.
5. The PR text says what was checked and what was not (the "Not guaranteed" list). Reviewers: re-read each dimension against the cited page and sign off in
   the PR; that sign-off is what raises a generator from Checked to Reviewed (`review.toml`).

## Guarantee levels

Checked (automatic spec check passes for every code in `codes.txt`), Reviewed (+ an independent reviewer who is not the author), Drawing-matched (+ a
comparison with the vendor's configured-part drawing, only where the vendor allows it). Nothing below Checked is published.

## Before you push

Run `git config core.hooksPath tools/hooks` once per clone. The pre-push hook runs `tools/lint` (files) and `tools/privacy`
(commit messages and author addresses) and refuses personal paths, development-session links or trailers, vendor CAD and stray
images; use your GitHub noreply address as the commit email. The `privacy` workflow runs the same checks on every pull request.
To keep your own words out too (machine names, say), list them, one regular expression per line, in
`~/.config/sc-parts/private-words` (or the file `$SC_PARTS_PRIVATE_WORDS` names); that file stays on your machine.
