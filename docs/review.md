# Independent review (the Reviewed level)

A generator is **Reviewed** when someone who did not write it has re-read every dimension row against the cited catalogue page, and
`review.toml` in the generator folder records that. `runtime/provenance.py` (`review_problems`) counts the review only when:

- every `[[dimension]]` id in `sources.toml` has a `[[row]]` whose verdict is `agree` or `corrected`;
- `reviewer` is set and differs from `author`, and `reviewer_kind` says what the reviewer was: `"ai"` or `"person"`;
- `sources_hash` equals the generator's current hash (`tools/provenance` prints it; any later change to `sources.toml` or `data/`
  voids the review until it is re-read).

```toml
reviewer_kind = "ai"                 # "ai" or "person": the generator page says "independent AI re-read" or names the person
reviewer = "who reviewed (a person, or an AI review lane named as such)"
author = "who wrote the generator"
date = "2026-11-27"
commit = "<the commit reviewed>"
sources_hash = "sha256:..."          # python3 -c 'from runtime import registry, provenance; ...' or PROVENANCE.md's recipe block
method = "Re-read each row against the cited page image; re-derived each table value; spot-built codes."

[[row]]
id = 89
verdict = "agree"                    # agree | corrected | disagree | unreadable
note = ""                            # what was compared; for "corrected", what changed and why (the fix itself is in data/ + sources.toml)
```

A `disagree` or `unreadable` row keeps the generator at Checked. A correction is made in `data/*.csv` / `sources.toml` with its
citation, `tools/check` re-run, and the row marked `corrected`; then `sources_hash` is taken from the corrected files.
Every generator page (PROVENANCE.md) carries a **Verified by** line built from this file: an AI review reads "independent AI re-read of every
dimension row against the cited pages (cell by cell, <date>); not reviewed by a person". A page never implies a person checked it
unless `reviewer_kind = "person"`.
