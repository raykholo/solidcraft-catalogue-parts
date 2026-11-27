# The parts-library release (SolidCraft parts index, Workshop)

SolidCraft's Parts Library panel and the Workshop (workshop.solidcraft.io) list parts libraries from the community index
`tangency-labs/solidcraft-parts`. A library there is a GitHub release `.zip` in the author's own public repository plus one manifest
file in the index (`libraries/<publisher>/<library>.json`); the Workshop reads the index every hour and lists the library under
`/part/<publisher>/<library>`. It does not copy the zip: clients download the release asset and check its SHA-256.

This repository ships such a release. The generators themselves (Python, host-side) never go in it: the index allows parts,
pictures and notes only, never programs or scripts. What goes in is their output, every valid code of every Checked generator's
`codes.txt`, as a native design and a STEP file, each spec-checked on the file shipped.

## Make a release

```
tools/release                 # -> dist/catalogue-parts-<version>.zip, .zip.sha256, dist/raykholo/catalogue-parts.json
tools/release --keep          # also keep the unpacked folder to look at
```

- `library.toml` holds the library's id (`raykholo.catalogue-parts`), name, licence, description, tags and `version`.
  Bump `version` for every release; the tag is `v<version>`.
- `tools/release` refuses when any packed code fails its spec check, when no generator is Checked, when the folder breaks the
  index's rules (no scripts, no symbolic links, at least one part), or when the manifest does not match
  `schema/parts-library.schema.json` (a copy of the index's schema).
- The zip is reproducible: sorted entries, the commit time as every timestamp.
- `min_solidcraft` is the SolidCraft release the designs were built and checked with (`SC_VER`).
- `.github/workflows/release.yml` does the same on a pushed tag and attaches the zip, its `.sha256` and the manifest to the
  GitHub release.

Layout of the zip:

```
catalogue-parts-0.1.0.zip
└── Catalogue parts/
    ├── README.md  LICENSE
    ├── HIWIN/MG rail-set/      MGN12H2R300Z0C.sc  MGN12H2R300Z0C.step  ...  README.md (its PROVENANCE.md)  preview.png
    ├── HIWIN/HG guideway/
    └── MISUMI/HFS extrusion/  SFJ shaft/  HNT t-nut/  ...
```

## List it (not yet)

Not submitted yet. The index's CI checks that `repo` is a public repository owned by the publisher.
When the repository is public and its home is settled:

1. Push tag `v<version>`; the release workflow publishes the release.
2. Fork `tangency-labs/solidcraft-parts`, add the release's `catalogue-parts.json` as `libraries/raykholo/catalogue-parts.json`,
   open a pull request. CI there downloads the asset and checks its hash and contents; a maintainer reviews the provenance.
3. Every later release: bump `version`, tag, and open a pull request that changes `release` in the manifest.

If the generators move to a `tangency-labs` repository instead, `publisher`, `repo` and the id change before the first listing
(an id never changes once listed).
