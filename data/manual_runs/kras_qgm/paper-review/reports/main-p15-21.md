# Main paper (s001-03) — pages 15–21 review report

Reviewer scope: `documents/s001-03/pages/page-0015.json` … `page-0021.json` only.
No other file was modified (`plan.json`, `bundle.json`, `adjudications.json`, `evidence/`, `previews/`,
`source.pdf` untouched; no `paper_bundle.py` run).

Method for every page: opened `previews/page-NNNN.png` with the Read tool and looked at it; compared
against the PDF native text layer and image/drawing bounding boxes pulled from `source.pdf` with
PyMuPDF (read-only); re-rendered candidate crops from `source.pdf` at 120–400 dpi into the scratchpad
and visually checked all four edges before committing a bbox.

---

## Per-page

### page-0015.json — Extended Data Fig. 2 (protein-detected NMR)

**Inspected.** Full-page figure plate + two-column caption. PDF embedded-image extents on this page:
x 47.3–553.9, y 49.0–316.1 pt; the panel letters, axis labels and colour-bar numbers are *vector*
artwork (0 text blocks outside the caption), so they are not in any image bbox.

**Changed.**
- Merged the extractor's three unrelated picture regions into **one** figure crop.
  Was: `figure-p0015-002` [419,60,559,153] (panel B inset), `figure-p0015-003` [100,89,384,322]
  (panel A HSQC), `figure-p0015-004` [418,158,556,307] (panel C ribbon).
  Now: single item `p0015-b002`, bbox **[37, 46, 562, 320]**.
  Render-verified to contain: panel letters `A)` `B)` `C)`; all five residue insets
  (10Gly, 77Gly, 89Ser, 92Asp, 78Phe); the `KRAS G12D` / `KRASG12D + Compound 18-2` legend;
  both axis labels `¹H (ppm)` and `¹⁵N (ppm)`; the CSP colour bar with **both** end labels 0.01 and 0.2.
  Top edge widened to 46 pt because the vector `A)` label starts at ≈54 pt and the 10Gly inset image at
  49.0 pt — the old crops cut them. Bottom held at 320 pt (caption first line starts 322.4 pt) so no
  caption text is baked into the JPEG.
- `asset_name` `figure-p0015-002` → **`extended-data-figure-2`**, `label` → `Extended Data Fig. 2`,
  **`asset_category: "supp_figs"`**.
- Caption: the two column fragments `p0015-b005` (ends "…(B) The CSP values") and `p0015-b006`
  (begins "are mapped onto…") were **merged into one item** `p0015-b005` and re-kinded
  `text` → `caption`. It sits outside the image crop and stays searchable.
- Text verified against the native layer: Compound 18-2, Gly10, P-loop, Phe78, Gly77, Ser89, Asp92,
  Switch-I / Switch-II, α-1 / α-2 / α-4, β-4 all confirmed. Repaired extractor emphasis-spacing only:
  `( **A** )` → `(**A**)`, `_α_ -2` → `_α_-2`, `_β_ -4` → `_β_-4`, `_α_ -1`, `_α_ -4`. No wording changed.
- `p0015-b000` (running header "Brief Communication"), `p0015-b001` (DOI running header) and
  `p0015-b007` (footer "Nature Biotechnology") → `omit` with explicit reasons.
- Reading order: headers → figure → caption → footer.

### page-0016.json — Extended Data Fig. 3 (quantum-enhanced generative model)

**Inspected.** Full-page plate ("Architecture of Hybrid Quantum-Classical Model") + two-column caption.

**Changed.**
- Merged the blue title banner (`figure-p0016-002` [37,46,347,72]) and the diagram
  (`figure-p0016-003` [58,69,568,379]) into **one** figure `p0016-b002`, bbox **[38, 47, 566, 372]**.
  Render-verified to contain: title banner; panel letters `(A)` `(B)` `(C)`; the LSTM cell with
  ADD OR CONCAT / SELFIES / x(t) / x′(t) / h(t−1) / C(t−1) / C(t) / h(t) / Sigmoid / tanh / Input,
  Forget, Output Gate labels; Ligand 1.1 M / Target / Data set / Loss / Prediction / Output sequences;
  Decoding / Hidden Layer / Input Layer / Token Emb. / Input Samples / Input size; N.N., Xi, QCBM,
  Softmax, P(Xi), R(Xi), Compute Rewards, Update weights; the vertical **Chemistry42** logo at the
  right margin; and the panel-(C) circuit ending `|0⟩ —U(θ)→ |ψ(θ)⟩ —measure→ outcome`.
- Bottom edge set by rendering the 355–385 pt strip: the green dashed panel-C border ends ≈367 pt,
  caption first line starts 377.2 pt → 372 pt clips nothing and bakes in no caption.
- `asset_name` → **`extended-data-figure-3`**, `label` → `Extended Data Fig. 3`,
  **`asset_category: "supp_figs"`**.
- Caption fragments `p0016-b004` (ends "…in SELFIES") + `p0016-b005` (begins "encoding)…") merged
  into one `caption` item `p0016-b004`; `b005` had been mis-kinded `text`.
- **Not "fixed":** the printed caption really labels its panels in the order **(B), (A), (C)**.
  Confirmed against the native text layer and the render; left exactly as printed.
  `X’(t)` keeps the typographic apostrophe U+2019; `P (x)=Softmax(R(x))` keeps the printed space after `P`.
- Headers/footer → `omit` with reasons.

### page-0017.json — Extended Data Fig. 4 (pharmacophore model)

**Inspected.** Single plate + two-column caption. Embedded raster is only x 95.0–506.0, y 49.0–315.2 pt,
but the plate has a dotted vector frame drawn *outside* that raster.

**Changed.**
- Figure `p0017-b002` bbox [89,43,511,321] → **[88, 42, 512, 318]**. Render-verified: all four dotted
  borders inside the crop; 2D structure of TH-Z816 with its `N–CH₃`, `H₃C`, `CH₃`, `NH` labels; the
  left pharmacophore/interaction map with residue tags; the right grey KRAS ribbon with the green
  ligand; the `Switch 2 Binding Site` box and its dashed leader lines. Bottom pulled to 318 pt
  (caption starts 319.2 pt).
- `asset_name` → **`extended-data-figure-4`**, `label` → `Extended Data Fig. 4`,
  **`asset_category: "supp_figs"`**.
- Caption fragments `p0017-b003` + `p0017-b004` merged into one `caption`; `b004` re-kinded from `text`.
- **Link restored.** The extractor dropped a live link annotation. `7EW9` on this page is a link to
  `https://doi.org/10.2210/pdb7EW9/pdb` (annotation rect [178.1, 339.3, 196.3, 348.0]); it is now a
  Markdown link in the caption. This is the only hyperlink in my range other than the footer branding.
- Headers/footer → `omit` with reasons.

### page-0018.json — Extended Data Fig. 5 (QCBM circuit)

**Inspected.** Single plate + two-column caption. Embedded raster only x 101.9–491.2, y 121.7–258.9 pt;
the "Classical Optimizer" box and the green dashed frame are vector and lie outside it.

**Changed.**
- Figure `p0018-b002` bbox [92,47,509,294] → **[90, 45, 511, 294]**. Render-verified: yellow
  `Classical Optimizer` box and both feedback arrows; all four sides of the green dashed border;
  `q₀–q₃` wire labels; every Rx/Rz/Rxx gate with subscripts `theta_0 … theta_18`; the barrier; all four
  measurement meters with classical-bit arrows `0 1 2 3`; the `meas` register with width marker `4`;
  and `|0⟩ —U(θ)→ |ψ(θ)⟩ —measure→ outcome`.
- `asset_name` → **`extended-data-figure-5`**, `label` → `Extended Data Fig. 5`,
  **`asset_category: "supp_figs"`**.
- Caption fragments `p0018-b003` + `p0018-b004` merged into one `caption`; `b004` re-kinded from `text`.
- **TEXT REPAIR (recorded here as required).** The PDF native text layer emits a **doubled ket bar**:
  `into a complex quantum state ||Ψ(0)⟩`. A 400 dpi render of the caption shows a **single** bar.
  Corrected to `|Ψ(0)⟩`.
- **Deliberately NOT repaired.** The glyph inside that ket is a printed **digit zero**, `Ψ(0)`, not `θ` —
  verified at 400 dpi. This is inconsistent with the `U(θ)` / `|ψ(θ)⟩` in the figure itself, i.e. it is
  the paper's own typo. Transcribed as printed rather than silently corrected.
- Also confirmed: "16 qubits", "(Rx, Rz)", "CNOT", "three layers and four qubits", italic `θ` in
  "the parameters _θ_,". Headers/footer → `omit` with reasons.

### page-0019.json / page-0020.json / page-0021.json — Nature Portfolio Reporting Summary (3 pages)

**Inspected.** All three previews viewed at full size; content identified page by page (see each
page's `review_notes`).

**Which option I took: IMAGE-ONLY, whole page retained as one figure item.** I did **not**
hand-transcribe them. Justification, verified rather than assumed:
- MuPDF returns **0 / 4 / 2** extractable characters for pages 19 / 20 / 21 respectively (the 4 and 2
  are stray `µ` and `₂` glyphs, no words). The extractor's own warning
  `OCR unavailable or failed: FzErrorLibrary` is accurate — there is **no usable native text layer**.
- These are checkbox forms. Meaning depends on ☒ vs ☐ state, which a text transcription loses.
- `mode: "image"` preserved on all three, as the plan requires.

**Changed.**
- Placeholder `asset_name` `page-0019/0020/0021` → **`reporting-summary-page-1 / -2 / -3`**;
  `label` `PDF page 19/20/21` → `Reporting Summary (page 1 of 3)` etc.
- bbox confirmed as the exact full MediaBox `[0, 0, 612, 792]`. **Note the page size difference:**
  pages 19–21 are US Letter **612 × 792 pt**, not the 595.276 × 790.866 pt of the article pages.
- Wrote specific `review_notes` on each page naming what is visible (authors + Statistics/Software/Data
  and the Zenodo URL on p19; PDB:7EW9 + enamine.net, human-participants N/A block, Life-sciences study
  design on p20; Materials/Methods checklists, HEK293 (T-REx) Cat# R71007 cell-line block and Plants on
  p21) **and** the image-only limitation.

---

## Asset names claimed by this reviewer

| Page | Item id | asset_name | asset_category | Label |
|---|---|---|---|---|
| 15 | `p0015-b002` | `extended-data-figure-2` | **`supp_figs`** | Extended Data Fig. 2 |
| 16 | `p0016-b002` | `extended-data-figure-3` | **`supp_figs`** | Extended Data Fig. 3 |
| 17 | `p0017-b002` | `extended-data-figure-4` | **`supp_figs`** | Extended Data Fig. 4 |
| 18 | `p0018-b002` | `extended-data-figure-5` | **`supp_figs`** | Extended Data Fig. 5 |
| 19 | `p0019-image` | `reporting-summary-page-1` | *(default / main `figure`)* | Reporting Summary (page 1 of 3) |
| 20 | `p0020-image` | `reporting-summary-page-2` | *(default / main `figure`)* | Reporting Summary (page 2 of 3) |
| 21 | `p0021-image` | `reporting-summary-page-3` | *(default / main `figure`)* | Reporting Summary (page 3 of 3) |

**Collision check for the coordinator:** four names routed to `supp_figs` —
`extended-data-figure-2`, `-3`, `-4`, `-5`. The supplement reviewers must not reuse these.
`extended-data-figure-1` is **NOT** mine: Extended Data Fig. 1 is printed on **page 14**, which belongs
to the pages 1–14 reviewer. That reviewer should claim `extended-data-figure-1` (+ `supp_figs`) and must
merge page 14's two placeholder crops `figure-p0014-002` (banner, [35,43,217,72]) and `figure-p0014-003`
([70,64,565,412]) the same way I merged pages 15/16 — they are the two halves of one plate.
No tables and no formulas occur in pages 15–21, so I claimed none.

---

## Proposed shared changes I could not make myself

1. **`plan.json` `reading_order`** — not needed for my range. Pages 15–21 contain no floating table or
   algorithm that interrupts a sentence; each page is one figure + its own caption, already in correct
   order within the page. No entry required from me.
2. **The 14/15 boundary join** — **no `join_previous` is needed.** I checked page 14's source: it ends
   with the *complete* Extended Data Fig. 1 caption ("…standard deviation across the repetitions."),
   and page 15 opens a new, self-contained Extended Data Fig. 2 caption. I deliberately left
   `join_previous` unset on page 15's first emitted item. Please do not add one.
3. **Reporting-summary asset routing — coordinator decision needed.** I left
   `reporting-summary-page-1..3` in the **default main `figure`** category, because the review plan
   names `reporting-summary-pageN` as a main-document pattern the compact builder already recognises,
   and my brief only mandated `supp_figs` for *Extended Data* figures. If the bundle convention is to
   keep `assets/figure/` limited to numbered main-text figures, move all three to
   `"asset_category": "supp_figs"`. It is a one-key edit per page and I flag it rather than guess.
4. **`plan.json` `notes` — two bundle-level notes I recommend adding** (I did not edit `plan.json`):
   - "Pages 19–21 are the Nature Portfolio Reporting Summary. The PDF carries no usable text layer for
     these pages (MuPDF: FzErrorLibrary; 0–4 extractable characters) and they are checkbox forms, so
     they are preserved as full-page images with no searchable transcription."
   - "Extended Data Figs. 1–5 are printed inside the main PDF (pages 14–18) and are routed to the
     supplementary figure directory."
5. **Possible navigational gap.** Because pages 19–21 are image-only, the string "Reporting Summary"
   will not appear anywhere in the generated Markdown, so an agent cannot text-search to it. I did
   **not** invent a heading item (the brief gave image-only or native-transcription as the two options).
   If the coordinator wants it findable, the cleanest fix is a `plan.json` note, or a short
   `heading` item added at bundle level — flagging rather than acting.

---

## Verification limits / what could not be fully verified

- **Pages 19–21 (image-only limitation — must be reported to the user).** These three pages carry no
  machine-readable text. Nothing on them is searchable in the built skill, and their checkbox answers
  (statistics items, field-specific reporting, cell-line and plant blocks) exist only as pixels. I read
  them by eye from the previews to write the notes, but that is **not** a verified transcription and I
  make no such claim. Line coverage and numeric checks will legitimately show no coverage for these
  pages; that is expected, not a defect.
- **Pages 15–18 are fully verified.** Every caption character was cross-checked against the PDF native
  text layer, and every stored bbox was re-rendered from `source.pdf` and visually inspected on all
  four edges. The only two places where I departed from the native text layer are recorded above:
  the doubled ket bar on page 18 (corrected) and the emphasis-marker spacing artefacts (normalised).
- **One item left intentionally "wrong-looking".** Page 16's caption panel order (B), (A), (C) and page
  18's `|Ψ(0)⟩` are faithful to print. If a downstream QA flags them, they are source defects, not
  transcription defects.
- JSON validity, unique item ids across the whole document, unique asset names, and in-page bbox bounds
  were all re-checked programmatically after writing. No duplicates.
