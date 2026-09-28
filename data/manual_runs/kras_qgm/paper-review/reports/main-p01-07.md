# Main paper (s001-03) — pages 1–7 review

Reviewer scope: `documents/s001-03/pages/page-0001.json` … `page-0007.json` only.
Every page preview was opened and looked at; ambiguous glyphs were additionally checked with
400–450 dpi PyMuPDF crops of the original `source.pdf` (read-only). No `paper_bundle.py`
command was run, and nothing outside the seven assigned page files was edited.

All seven pages now have `"reviewed": true` with page-specific notes.

## Asset names claimed

| Page | Item | Kind | Label | `asset_name` | Category | bbox (pt) |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | `p0002-b002` | figure | `Fig. 1` | `figure-1` | main `figure` (default) | `[96, 45, 504, 550]` |
| 4 | `p0004-b002` | figure | `Fig. 2` | `figure-2` | main `figure` (default) | `[33, 43, 565, 646]` |

No tables and no formulas exist on pages 1–7 (see page 1 below — the one item the extractor
called a table was not one). I checked the whole document for collisions: `figure-1` and
`figure-2` are used nowhere else in `documents/s001-03/pages/`.

## Per page

### Page 1 — title page

Inspected: masthead, banner, title, byline, publication-history sidebar, abstract, both body
columns, the 21-entry affiliation footnote block, the correspondence line and the running foot.

- **`p0001-b000` "nature biotechnology" → `omit`.** It was extracted as an `## ` heading; it is
  the journal masthead logo, not a section heading. Reason recorded.
- **Title heading de-bolded**: `# **Quantum-computing-enhanced…**` → `# Quantum-computing-enhanced
  algorithm unveils potential KRAS inhibitors`, and moved to be the first item on the page
  (see *Reading order* below).
- **`p0001-b004` was misclassified as a `table`.** It was the publication-history sidebar plus
  the author byline forced into a 2×2 grid with `<br>`-laden cells. Dropped the `table` kind and
  the `rows`, and split it into two `text` items:
  - `p0001-b004` — the full author byline, with the affiliation superscripts rebuilt from the
    fragmented evidence lines (1,2 / 3,4 / 5 / 6 / 7 / 8 / 7 / 9 / 10,11 / 11 / 5 / 5,12 / 5 /
    5,13 / 5,14 / 14,15 / 7 / 7 / 7 / 7 / 7 / 16 / 5,12,14,17 / 1,2,18,19,20,21 / 7).
  - `p0001-b004a` (new id) — Received / Accepted / Published online / Check for updates.
  - ORCID and ✉ glyphs are graphics with no native text and are not transcribed; the
    corresponding-author addresses survive in `p0001-b008a`.
- **Affiliations `p0001-b008`**: markers 1 and 2 were plain text and 3–21 had a stray space after
  `</sup>`; all 21 are now uniform `<sup>N</sup>` immediately before the department name. The
  `e-mail:` line was split out as `p0001-b008a` (new id).
- **Citation punctuation**: removed the spurious space before the sentence period after every
  superscript marker in `b006`/`b007` (risks1–3, design4–7, design8–10, efficiently11,
  strategies12, entanglement13,14, data15).
- Verified en dashes in the citation ranges and in *quantum–classical* / *classical–quantum*, and
  that `~10<sup>60</sup>` kept its exponent.
- **Reading order** now: title → Brief Communication → doi → byline → dates → affiliations →
  e-mail → abstract → left body column → right body column → foot. Two deliberate moves:
  1. The title is first so the emitted document opens with an H1 whose canonical form equals the
     generated package title; otherwise `reading_package.py` prepends a second identical H1.
  2. The affiliation block and e-mail line were lifted to sit under the byline they annotate.
     This also leaves the page ending on body prose (`…and overcome`) so the page 1 → page 2
     sentence can be joined. Verified by simulation (below).

### Page 2 — Fig. 1

- `p0002-b002` relabelled from `Figure on PDF page 2 (3)` / `figure-p0002-002` to **`Fig. 1` /
  `figure-1`**.
- **bbox tightened** `[96, 46, 504, 552]` → `[96, 45, 504, 550]`. The old bottom sat on the first
  caption line (top = 552.6 pt). I rendered the new crop at 140 dpi and confirmed it holds all
  four panels with their bold letters **a–d**, the rotated "Increasing structural diversity"
  label, the VirtualFlow and Chemistry42 logos, the "Selected 3/8/4 compounds" labels at the
  right edge (text ends x = 490.4 pt) and the Classical / Quantum (HW) / Quantum (SIM) legend at
  y = 540–547.5 pt.
- `p0002-b003` / `p0002-b004` (the two column halves of the Fig. 1 caption) are now kind
  `caption`; `b004` carries `join_previous: "space"`.
- Caption text: removed the extractor's space before each bold panel-letter comma
  (`**a** ,` → `**a**,`) for a, b, c, d. En dashes in *quantum–classical* and *STONED–SELFIES*
  confirmed against the native text.
- `p0002-b005`: removed the space before the period after `effectiveness<sup>17,18</sup>`;
  confirmed the `show-/cased` and `high-/lighting` line-wrap hyphens were correctly dropped.
- **Float relocation (within-page, so done here):** the Fig. 1 float now sits between
  `p0002-b006` ("…extra qubits.") and `p0002-b007` ("Here, we propose…"), which is the nearest
  true paragraph boundary. That single move lets the prose run unbroken page 1 → page 2 and
  page 2 → page 3.
- Joins set: `b005 ← p0001-b007` (space), `b006 ← b005` (space), `b004 ← b003` (space).

### Page 3 — text only

- Removed the space before the period/comma after every superscript marker: efforts21,22 /
  scores23 / set24 / workflow25 / discovery26 / models27 / models17 / interactions28–35 /
  (ALFA prey)36.
- `approxi mately` → `approximately` (a soft hyphen U+00AD in the source became a space). The
  other soft-hyphen wrap on the page (`mole­cular`) was already joined correctly.
- `_P_ ( _x_ ) = softmax( _R_ ( _x_ ))` → `_P_(_x_) = softmax(_R_(_x_))` (emphasis-induced spaces
  inside the expression).
- `(M)QCBM– LSTM)` → `(M)QCBM–LSTM)` — a line-wrap space after a real compound en dash.
- **IC₅₀ is printed as a subscript** (confirmed on a 400 dpi crop); now `IC<sub>50</sub>` in
  `b007` and `b008`.
- Joins: `b002 ← p0002-b007` (space), `b005 ← b004` (space).
- **Left as printed, deliberately:** the source really sets `Raf1 ‘prey‘` with a LEFT single
  quote at both ends (U+2018 twice, confirmed in the native text and on a crop). I reproduced it
  rather than silently correcting it. Flagging it here in case the coordinator prefers `’`.

### Page 4 — Fig. 2 (full-page float)

- `p0004-b002` relabelled from `Figure on PDF page 4 (3)` / `figure-p0004-002` to **`Fig. 2` /
  `figure-2`**; bbox `[33, 43, 565, 648]` → `[33, 43, 565, 646]` so the bottom clears the first
  caption line (top = 648.1 pt). Rendered and verified: both blue section banners
  (ISM061-018-2, ISM061-022), all seven panel letters **a–g**, the rotated "% Activity" and
  "Cell viability (% of control)" axis titles at x = 38.2 pt, every `log [uM]` label including
  the bottom row at y = 643 pt, and the right-most tick at x = 559.6 pt.
- Caption (`b003` left, `b004` right, both already `caption`): removed the spaces around every
  bold panel letter (`**a** , **e** ,` → `**a**,**e**,`; `( **a** )` → `(**a**)`) for a–g, and
  **restored a real compound hyphen**: the extractor merged the line-wrapped `ISM061-` / `018-2`
  into `ISM061018-2`; it is now `ISM061-018-2`.
- `b004` carries `join_previous: "space"`.

### Page 5 — end of Results, Online content, References 1–18

- **NMR isotope labels were mis-parsed and are the most substantive text fix on my pages.**
  `spectroscopy.<sup>15</sup> N-labeled` attached the superscript to the preceding full stop and
  stranded the N; `record<sup>1</sup> H–<sup>15</sup> N` did the same. Corrected to
  `spectroscopy. <sup>15</sup>N-labeled` and `record <sup>1</sup>H–<sup>15</sup>N`, verified on a
  400 dpi crop of the lines at y = 262 and y = 273 pt.
- Removed the space before the comma after every bold volume number in refs 1–18
  (`**47** , 20–33` → `**47**, 20–33`); 17 items touched.
- `b004 ← b003` join (space): the right column opens at the column margin x = 306.1 pt, not the
  323.1 pt paragraph indent, so it continues the left column's final paragraph.
- Left as printed: `(ref. 21)` — the 21 is a baseline blue cross-reference, **not** a superscript
  (crop-verified), so no `<sup>` was added. `α2 helix`, `β4 sheet`, `α1 helix`, `α4 regions` use
  U+03B1/U+03B2 with baseline numerals. `Aspuru Guzik` in ref. 8 genuinely has no hyphen.

### Page 6 — References 19–36, Publisher's note, Open Access

- Same bold-volume comma fix across 17 reference items.
- Ref. 23: the preprint DOI was split across a line and left with a space inside the URL;
  rejoined to `https://doi.org/10.1101/2023.04.25.537981`.
- Ref. 32: `_N_ -glycosylation` → `_N_-glycosylation`.
- Left as printed: ref. 20's title reads "hybrid quantum-classical framework" with a plain
  **hyphen** in the source, unlike the en dash the body text uses — verified in the native text
  and not normalised. `KRas<sup>G12D</sup>` (ref. 21) and `KRas(G12D)` (ref. 22) are both correct
  as printed.
- No join needed at either boundary (ref. 18 → ref. 19; copyright line → `Methods` heading).

### Page 7 — start of Methods

- Removed the space between the superscript marker and the following `.`/`,`/`;` throughout
  (REINVENT37 … JANUS44, epilepsy45; translation46; bronchodilation47. SMINA49, collection50,51,
  Optuna52. Tartarus26, score25. and the two min⁻¹ / ml⁻¹ units).
- `SELFIES– VAE<sup>39</sup>` → `SELFIES–VAE<sup>39</sup>`: a model name broken across a line
  after a real compound en dash (matches SMILES–VAE, SMILES–LSTM–HC, SELFIES–LSTM–HC, GB–GA in
  the same sentence).
- **`β2-adrenoceptor` → `β<sub>2</sub>-adrenoceptor`** — the 2 is a genuine subscript, verified
  on a 450 dpi crop of the line at y = 509 pt.
- `b010 ← b009` join (space).
- Left as printed: `(ref. 48)` is a baseline cross-reference; PDB codes 1SYH / 6Y2F / 4LDE are
  blue hyperlinks kept as plain text; `DATASET` is set in a typewriter face in the source and was
  kept as plain searchable text rather than re-marked as inline code; `purity ≥ 95%` keeps
  U+2265, `1× HBS-EP+` keeps U+00D7, and the exponents in `5 μl min<sup>−1</sup>` /
  `5 μg ml<sup>−1</sup>` keep a real MINUS SIGN (U+2212), not a hyphen.
- `p0007-b015` is the short running foot "Nature Biotechnology" (this page carries no printed page
  number); confirmed as furniture and left as `text`.

## Verification I ran locally (read-only)

I simulated `reading_package.compact_omission_reasons` and the join loop over the current
`pages/*.json` (no build, nothing written outside my seven files):

- **Line coverage:** for every page 1–7, 0 evidence lines are missing from the page's non-image
  output. (Lines whose bbox centre falls inside a `figure`/`omit` region were excluded, as the
  real checker does.)
- **Numeric tokens:** pages 2, 3, 5, 6, 7 are identical to the source. Two intentional
  differences remain, and the verifier will probably report them — they are corrections, not
  regressions:
  - page 1: source flattens `~10⁶⁰` to the token `1060`; my transcription is `~10<sup>60</sup>`,
    giving `10` + `60`.
  - page 4: source splits `ISM061-018-2` across a line, yielding a stray `018`; my repair gives
    one more `-018` and no bare `018`.
- **Join chain resolves as intended** (auto-omitted furniture does not break the chain):
  `p0002-b005 ← p0001-b007`, `p0002-b006 ← p0002-b005`, `p0002-b004 ← p0002-b003`,
  `p0003-b002 ← p0002-b007`, `p0003-b005 ← p0003-b004`, `p0004-b004 ← p0004-b003`,
  `p0005-b004 ← p0005-b003`, `p0007-b010 ← p0007-b009`. No `join_previous` lands on a
  non-prose predecessor.
- The 19 header/footer items on pages 1–7 that the compact builder auto-omits are exactly the
  running furniture (`p0001-b009`, `p000{2..7}-b000/b001`, and each page's
  "Nature Biotechnology | Volume 43 …" foot). Page 1's `Brief Communication` and doi line sit
  below the 48 pt margin band and are **not** auto-omitted, so they survive as visible text —
  which is correct, they are the article banner there.
- IDs are unique across the whole document; `figure-1` / `figure-2` collide with nothing.

## Proposed shared changes I could not make myself

1. **`plan.json` `reading_order` — the page 3 → page 5 sentence.** Page 3 ends mid-sentence at
   "…ISM061-022 did not show binding to KRAS-G12D" and page 5 resumes with "according to SPR.",
   but the whole Fig. 2 float page (page 4) sits between them. I could not set
   `join_previous` on `p0005-b002` without gluing body prose onto the Fig. 2 caption (the builder
   appends to the immediately preceding emitted piece). Suggested `reading_order` move: place
   `p0004-b002`, `p0004-b003`, `p0004-b004` immediately **after `p0005-b002`** (which is where
   the Fig. 2 discussion ends and a new paragraph, `p0005-b003` "Overall, these live-cell…",
   begins), then add `"join_previous": "space"` to `p0005-b002`. If you take this, `p0005-b003`
   must NOT get a join, and `p0004-b004`'s existing join to `p0004-b003` stays valid.
2. **Heading level and bold, bundle-wide.** The extractor's convention is `# ` for top-level
   sections (Online content, References, Methods, Data availability, Code availability,
   Acknowledgements, Author contributions, Competing interests, Additional information) and `## `
   for subsections, with the heading text wrapped in `**…**`. It is internally consistent, so I
   left pages 5 and 7 alone rather than desynchronising them from pages 8–13. Two bundle-wide
   cleanups worth a single pass by the coordinator: strip the `**` from every heading (it leaks
   into `references/index.md` navigation entries verbatim), and optionally demote `# ` → `## ` so
   the sections sit under the document title. I already de-bolded only the page 1 title, because
   that one has to match the generated title exactly for dedup.
3. **Placeholder asset names still outstanding on other reviewers' pages** (flagging only, not
   mine to touch): `figure-p0014-002`, `figure-p0014-003`, `formula-p0011-003`,
   `formula-p0011-006`. Note that `extended-data-figure-2` … `extended-data-figure-5` already
   exist but `extended-data-figure-1` does not, while pages 3 and 7 cite "Extended Data Fig. 1a",
   "1b", "1c" and "1d" — the two `p0014` placeholders are the likely home for it.
4. **Page 7 → page 8 boundary:** page 7 ends mid-sentence at "…prepared samples by serial
   twofold". The page 8 reviewer has already set `p0008-b002` `join_previous: "space"`, and my
   simulation confirms it resolves to `p0007-b014`. Nothing further needed.
5. **Source typography quirk for a bundle note:** `Raf1 ‘prey‘` on page 3 uses a left single quote
   at both ends in the published PDF. Preserved verbatim. If the coordinator would rather
   normalise it to `‘prey’`, that is a one-character edit to `p0003-b007`.

## Anything I could not fully verify

Nothing on pages 1–7 was left unverified. Both figure crops were re-rendered from `source.pdf`
and inspected at panel-letter resolution; every page preview was viewed at full size; and every
ambiguous glyph (¹⁵N, ¹H, IC₅₀, β₂, ref. 21, ref. 48, ‘prey‘, μ vs µ, U+2212 vs hyphen) was
resolved against a high-dpi crop or the native text rather than guessed. The only judgement calls
I consciously left for the coordinator are the five items listed above.
