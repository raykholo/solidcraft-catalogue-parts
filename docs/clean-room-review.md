# Clean-room and trademark review

Date: 2026-11-27. Not legal advice; where terms are quoted, only what the terms say is reported.

## Scope and method

The whole tree: 18 generators (4 HIWIN, 14 MISUMI), every `sources.toml`, every image, `tools/release` output text, `library.toml`, the
CI workflows. Every distinct URL host in every `sources.toml` was listed; every `icon.svg` was read as source; every `preview.png` and
sample `shots/*.png` were viewed; the whole tree was searched for personal paths, addresses, email addresses and machine names.

## Findings

### 1. No vendor CAD, catalogue images, logos or photos: PASS

- No CAD or geometry file (STEP, IGES, Parasolid, native, STL, SAT, DXF) is in the repository, and none was used to make a part. The
  numbers come only from the catalogue tables and figures cited in `sources.toml`. `tools/lint` refuses CAD files, images outside
  `icon.svg` / `preview.png` / `shots/`, and `<image>` inside an svg.
- The only binary files are PNGs: screenshots and path-traced renders of the generated models inside SolidCraft's own window. None
  shows a vendor page, drawing, photo or logo.
- Icons are generic geometry (rails, bushings, collars, extrusion section, flanges) in grey; the HIWIN icons use green and red rectangles
  for the end seals and caps (a product-appearance choice, labelled appearance in `generator.toml`). No letters, nothing resembling a
  manufacturer's logo.

### 2. Every number cites a manufacturer source: PASS

`tools/lint` checks that every CSV row has a source id that exists, a page and a status, and that every source has a URL. Hosts:

| Host | Sources | Verdict |
|---|---|---|
| `th.c.misumi-ec.com` (MISUMI Economy Series 2025 e-catalogue) | S8, S11-S14, S16, S18-S21, S30, S50-S52 | MISUMI's own domain |
| `in.misumi-ec.com` (MISUMI FA catalogue PDFs) | S1-S3, S5, S9, S10, S40 | MISUMI's own domain |
| `hiwin.com` (HIWIN Linear Guideway catalogue G99TE24-2410, product pages) | S4, S6, S7, S15, S17 | HIWIN's own domain |

`docs/candidates.md` names other URLs as candidate future work only; none is a source of any current data.

### 3. Trademark use: PASS

- Names and codes are descriptive ("HIWIN HG heavy-load linear guideway", "MISUMI Economy ..."); nothing claims to be official.
- The non-affiliation line ("not made, endorsed or checked by the manufacturers") is in `README.md`, `NOTICE`, both `vendor.toml`
  files, every generated `PROVENANCE.md` (shipped as each folder's README in the release zip), the release zip's top-level README and
  `library.toml`'s description.

### 4. Site terms: RISK, summarised

What the MISUMI terms say (Thailand site; the US text is the same):

- Website terms, section 2: "You are not allowed to link to, reproduce, sell, publish, distribute, modify, or display this Web Site or
  any Content without the prior written permission of Misumi." "Content" is "All contents, text, images, data, information and other
  material". Read literally it covers catalogue pages as well as CAD. It is a general copyright-style clause; the repository reproduces
  no page, image or text, only numeric dimensions with citations.
- CAD terms (`cad.html`): CAD data is offered "for the purpose of informing customers of the characteristics of the products ... for
  use in their designs"; section 4 forbids "(4) Using or reproducing the Data beyond the scope of the above-stated Purpose of Use",
  "(7) Altering the content, reverse engineering, decompiling, disassembling, or analyzing the Data" and "(9) Using the Data for the
  purpose of ... products and services identical or similar to those of MISUMI". Hence no vendor CAD is used anywhere here. The
  library models parts for design use and sells nothing; keep it free of any ordering or shop function.
- Publishing numeric dimensions with citations is the usual way catalogue-derived libraries work; the terms regulate CAD downloads and
  reproduction of site content, not facts. A courtesy notice to both manufacturers, and the takedown path in `README.md`, are the
  prudent steps.

### 5. Licences and personal data: PASS

- Licence Apache-2.0 (`LICENSE`, `library.toml`). No GPL/LGPL text, headers or copied code.
- `schema/parts-library.schema.json` is MIT (Tangency Labs); its notice travels in `NOTICE` and the file's `$comment`.
- No personal path, home directory, email address or machine name in the tree (`tools/lint` checks the patterns on every file). The
  GitHub account name `raykholo` appears where a release must name its publisher (`library.toml`, `docs/parts-library.md`).

## Decisions (owner, 2026-11-27)

- **No vendor CAD, ever.** Nothing in the repository may depend on vendor CAD, and no tool compares against it.
- **AI reviews are labelled.** The Reviewed level is given for an independent AI re-read of every dimension row against the cited pages,
  and every page says so: "Verified by: ... independent AI re-read ... (cell by cell, <date>); not reviewed by a person"
  (`reviewer_kind` in review.toml, `docs/review.md`). A review by a person says so instead.
- **HIWIN site terms: needs a human read.** hiwin.com answers 403 to scripts, and no website terms-of-use page is indexed. To read:
  - https://hiwin.com/ (footer: look for "Terms of Use" / "Legal" / "Privacy Policy")
  - https://hiwin.com/resources/catalogs/ (the page that publishes the linear guideway catalogue we cite)
  - Found but not website terms (sales contracts only): https://hiwin.com/wp-content/uploads/HIWIN_Standard_Terms-Conditions-1.pdf,
    https://www.hiwin.com/wp-content/uploads/HIWIN_Sale_Terms_and_Conditions_20210630.pdf
