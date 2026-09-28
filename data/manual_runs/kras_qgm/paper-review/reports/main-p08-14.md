# Main document `s001-03`, pages 8–14 — review report

Scope: `documents/s001-03/pages/page-0008.json` … `page-0014.json`. All seven pages are
`"reviewed": true` with specific `review_notes`. No file outside that range was touched.

Every page was opened as `previews/page-NNNN.png` and additionally re-rendered from
`source.pdf` at 300–900 dpi for the passages where the native text layer looked suspect.
Item text was cross-checked against `evidence/page-NNNN.json` and against the PDF's own
link annotations (`get_links`), which the extractor had ignored entirely.

---

## Per page

### Page 8 — Methods (SPR tail, MaMTH-DS, cell viability, protein purification, NMR, experimental validation)

Inspected: full preview; 300-dpi crops of the right column (protein purification, NMR
experiments, experimental validation) and of the left-column CO2 line.

Changed:
- Reading order already correct (left column `b002`–`b008`, then right column `b009`–`b028`); no reorder.
- `b000` / `b001` / `b029` → `omit` (running header "Brief Communication", running DOI header, running footer "Nature Biotechnology").
- Heading level: `b003`, `b005`, `b007`, `b010`, `b012` demoted `#` → `##` so they sit under `# Methods` (`p0007-b002`), matching the `##` already used on page 7 for *Benchmark setup* / *SPR conditions*. Bold `**…**` left in place per coordinator instruction.
- `join_previous: "space"` on `b002` (page 7 ends "…prepared samples by serial twofold", page 8 opens "dilutions from 200 μM…").
- Text repairs: `[<sup>15</sup> N]H4Cl` → `[<sup>15</sup>N]H<sub>4</sub>Cl`; `2% DMSO- _d_ 6` → `2% DMSO-*d*<sub>6</sub>`; `1H–15N TROSY HSQC` → `<sup>1</sup>H–<sup>15</sup>N TROSY HSQC`; `on both<sup>1</sup> H and<sup>15</sup> N dimensions` → `on both <sup>1</sup>H and <sup>15</sup>N dimensions`; removed the stray space before punctuation in `ReRSA model<sup>58</sup> .` and `kcal mol<sup>−1</sup> ).`
- Subscripts restored (400-dpi verified): `5% CO<sub>2</sub>` ×4, `Na<sub>2</sub>HPO<sub>4</sub>`, `KH<sub>2</sub>PO<sub>4</sub>`, `MgCl<sub>2</sub>`.
- Link restored: `(PDB [7EW9](https://doi.org/10.2210/pdb7EW9/pdb))` in `b018` — exactly the annotation the coordinator flagged.

### Page 9 — Methods (live-cell results tail, data acquisition, quantum-assisted algorithm, workflow)

Inspected: full preview; 350-dpi crops of the STONED–SELFIES paragraph, the `X_i` passage and the IC50 line.

Changed:
- Reading order already correct; no reorder. `b000`/`b001`/`b018` → `omit`.
- `b007`, `b012`, `b015` demoted `#` → `##` (Methods subsections).
- `join_previous: "space"` on `b002` (page 8 ends "…gauged through cell-based", page 9 opens "assays.").
- `b010`: the STONED–SELFIES URL had been split by the line wrap into `https:// github.com/...`; rejoined and restored as a Markdown link.
- `b011`: `PDB [5US4](https://doi.org/10.2210/pdb5US4/pdb)` link restored; `Å<sup>3</sup> .` → `Å<sup>3</sup>.`
- `b014`: `designated as _Xi_ .` → `_X_<sub>i</sub>.` and `for each _Xi_ , where _i_ ∈ [1, _N_ ].` → `for each _X_<sub>i</sub>, where _i_ ∈ [1, _N_].`
- Stray spaces before punctuation after superscripts 28–34, 36, 60–63 removed.
- `with IC50 values` → `with IC<sub>50</sub> values` (400-dpi verified).

### Page 10 — Methods (generation of new molecules, Algorithm 1, LSTM, QCBM)

Inspected: full preview; 350-dpi crops of the Algorithm 1 pseudocode, the equation block, the ket notation (900-dpi zoom) and equation (7).

Changed — this page had the **worst reading-order damage in the range**:
- The extractor interleaved the columns (`b002`–`b008` left, `b009`–`b015` right, `b016`–`b026` left, `b027`–`b030` right). Rebuilt as **full left column** (`b002`, `b003`, `b004`, `b005`, Algorithm 1 code, `b026`) then **full right column** (`b009`–`b014`, equations 1–6, `b027`–`b030`). This matters because left-column `b026` ends "To optimize these parameters *θ*, the model is" and right-column `b009` continues "initially configured with randomly assigned parameters |ψ(θ)⟩" — `b009` now carries `join_previous: "space"`.
- **Algorithm 1** was 13 separate list items (`b006`, `b007`, `b008`, `b016`–`b025`; `b025` was not even marked a list item). Merged into one `code` item `p0010-b006` (bbox `[39, 518, 292, 660]`), bullets and `**` stripped, two indentation levels restored from the crop. Dropped `b007`, `b008`, `b016`–`b025`.
- **Equations (1)–(6)** were a single misclassified `table` (`p0010-b015`) whose cells were corrupted (stray combining tilde in `Candidate values:̃ _Ct_`, all operator spacing lost). Table removed; replaced by six `formula` items `p0010-b015a`–`f`.
- `p0010-b029` renamed from the placeholder to `Equation (7)` / `formula-7`.
- Text: `artificialintelligence-driven` → `artificial-intelligence-driven` (a **real compound hyphen** swallowed at the line wrap); `_X_<sup>′</sup> ( _t_ )` → `_X_′(_t_)`; `_P_ ( _x_ ) = softmax( _R_ ( _x_ ))` → `_P_(_x_) = softmax(_R_(_x_))`; `|| _ψ_ ( _θ_ )⟩` → `|_ψ_(_θ_)⟩` (twice — the doubled ket bar); `_θn_` → `_θ_<sub>n</sub>` ×2; `_xt_` → `_x_<sub>t</sub>`; `and ̂ _yy_` → `_ŷ_<sub>y</sub>`; `**Forget gate** :` / `**Input gate** :` / `**Output gate** :` → `…**:`; stray spaces after superscripts 24, 67–72.
- `b000`/`b001`/`b031` → `omit`.

### Page 11 — Methods (batch loss, LSTM equations with prior, Algorithm 2, QCBM model) + **Data/Code availability**

Inspected: full preview; 350–900 dpi crops of equation (8), the (9)–(15) block, the QCBM paragraph, Algorithm 2 and the availability block.

Changed:
- Columns were interleaved again; rebuilt as full left column (`b002`, eq 8, `b004`, `b005`, eqs 9–15, `b007`, `b024`, `b025`) then full right column (`b008`–`b011`, Algorithm 2 code, `b027`–`b032`). `join_previous: "space"` on `b008` (left column ends "…between the generated and target", right column opens "distributions.").
- `p0011-b003` renamed to `Equation (8)` / `formula-8`.
- `p0011-b006` was **one** formula region covering **seven** displayed equations; replaced by `p0011-b006a`–`g` = `formula-9` … `formula-15`. bboxes kept at x 82–299 so the leftmost label ("Candidate values:" starts at x = 87.6) and the equation numbers (right edge 293.4) are both inside every crop.
- **Algorithm 2** was 13 separate items (`b012`, `b013` as text; `b014`–`b023`, `b026` as list items, with `b026` "end while" stranded after the left-column paragraphs). Merged into one `code` item `p0011-b012` (bbox `[306, 464, 560, 607]`).
- `b005` held the worst single extraction failure in the range: `_xt_<sup>′=</sup><sup>_X_(</sup><sup>_i_) ++</sup><sup>_xt_in the LSTM cell. This combina-</sup> tion constituted` → `_x_′<sub>t</sub> = _X_(_i_) ++ _x_<sub>t</sub> in the LSTM cell. This combination constituted`.
- Other text: `_yi_` → `_y_<sub>i</sub>`; `and ̂ _yyi_` → `_ŷ_<sub>y<sub>i</sub></sub>`; `_i_ th data point` → `*i*th data point` ×2; `NLL ( _θ_ ) = −∑ _x_ ∈ _D_ log _pθ_ ( _x_ )` → `NLL (_θ_) = −∑<sub>_x_∈_D_</sub> log _p_<sub>_θ_</sub>(_x_)` (and the second `_pθ_ ( _x_ )`); `_P_ ( _X_ ( _i_ ))` → `_P_(_X_(_i_))`; `softmax` → `` `softmax` `` (the page sets it monospace); `**Algorithm 2** .` → `**Algorithm 2**.`; `|| _ψ_ ( _θ_ )⟩` → `|_ψ_(_θ_)⟩` and `∣〈 _x_ ∣ _ψ_ ( _θ_ )〉∣<sup>2</sup> .` → `|⟨_x_|_ψ_(_θ_)⟩|<sup>2</sup>.`
- Zenodo DOI in `b030` was split by the line wrap; rejoined, and both `b030` and `b032` now carry Markdown links.
- Heading levels confirmed from the crop: `Data availability` and `Code availability` are set larger than `Reporting summary`, so they stay `#` and `Reporting summary` stays `##`.

### Page 12 — References 37–73 + Acknowledgements

Inspected: full preview; 400-dpi crops of refs 54, 58, 63, 73.

Changed:
- Reading order already correct. **Verified by numbering**: after ordering, the leading numbers run 37, 38, 39 … 73 — 37 entries, strictly sequential, no gap or repeat.
- 30 occurrences of `** ,` (spurious space between the bold volume number and the comma) → `**,`.
- Ref 54: `Perczel, A.<sup>1</sup> H,<sup>15</sup> N` → `Perczel, A. <sup>1</sup>H, <sup>15</sup>N`.
- Ref 73: Zenodo DOI split mid-URL (`https://doi.org/10.5281/ zenodo.11137638`) → rejoined and made a Markdown link. **This is the only URL/DOI in the whole reference list on this page**; I re-swept and found no other.
- Ref 47: `β2-adrenoceptor` → `β<sub>2</sub>-adrenoceptor`.
- `b000`/`b001`/`b042` → `omit`.

### Page 13 — Author contributions / Competing interests / Additional information

Inspected: full preview (only the top third of the page carries content; the rest is blank).

Changed:
- `join_previous: "space"` on `b002` (Acknowledgements continue from page 12: "…Ontario Research Fund, Ontario" + "Genomics Institute" = "Ontario Genomics Institute").
- `join_previous: "space"` on `b007` (Competing interests continue across the column break: "…Zapata AI. C.G." + "is a cofounder…").
- Three dropped link annotations restored: `b009` and `b010` → `https://doi.org/10.1038/s41587-024-02526-3`, `b013` → `www.nature.com/reprints`.
- `b000`/`b001`/`b014` → `omit`. Heading levels `#` confirmed correct for the three end-matter sections.

### Page 14 — Extended Data Fig. 1

Inspected: full preview; page geometry queried directly with PyMuPDF; the merged crop re-rendered at 200 dpi and checked on all four edges.

Changed:
- **Figure merge.** The page holds exactly **one** raster image, at `[40.3, 49.0, 212.0, 66.1]` (the "Clasical vs. Quantum Modelling" banner). Everything else on the plate — panel frames, bars, error bars, fit line, the (A)/(B)/(C) panel letters, every axis number and label — is **vector** artwork spanning `[52.1, 53.0, 559.2, 406.5]` (367 paths, excluding the page-header rule at y = 38.0). `p0014-b002` (banner only) and `p0014-b003` were merged into one `figure` item `p0014-b002` with bbox **`[37.0, 45.0, 562.0, 408.5]`**; `p0014-b003` dropped. Re-render confirms: banner complete at top, (A) and (C) letters inside the left edge, panel B's frame (559.2) inside the right edge, "Number of Qubits" label inside the bottom edge above the caption (which starts at y = 410.4).
- `asset_name: "extended-data-figure-1"`, `asset_category: "supp_figs"`, `label: "Extended Data Fig. 1"`.
- **Caption merge.** The caption runs across both columns; `b004` (left) and `b005` (right) were both kinded `text`. Merged into one `caption` item `p0014-b004`, bbox `[39, 405, 562, 590]`, kept outside the image crop. `b005` dropped. Panel-letter spacing fixed: `( **A** , **B** )` → `(**A**, **B**)`, `( **C** )` → `(**C**)`, `Figure **A** ,` → `Figure **A**,`.
- `b000`/`b001`/`b006` → `omit`.

---

## Asset names claimed

| Page | `asset_name` | Kind / category | Item id | Printed label |
|---|---|---|---|---|
| 10 | `formula-1` | formula | `p0010-b015a` | Equation (1) — Forget gate |
| 10 | `formula-2` | formula | `p0010-b015b` | Equation (2) — Input gate |
| 10 | `formula-3` | formula | `p0010-b015c` | Equation (3) — Candidate values |
| 10 | `formula-4` | formula | `p0010-b015d` | Equation (4) — Update cell state |
| 10 | `formula-5` | formula | `p0010-b015e` | Equation (5) — Output gate |
| 10 | `formula-6` | formula | `p0010-b015f` | Equation (6) — Update hidden state |
| 10 | `formula-7` | formula | `p0010-b029` | Equation (7) — NLL for a single data point |
| 11 | `formula-8` | formula | `p0011-b003` | Equation (8) — batch loss |
| 11 | `formula-9` | formula | `p0011-b006a` | Equation (9) — Prior sampling |
| 11 | `formula-10` | formula | `p0011-b006b` | Equation (10) — Forget gate |
| 11 | `formula-11` | formula | `p0011-b006c` | Equation (11) — Input gate |
| 11 | `formula-12` | formula | `p0011-b006d` | Equation (12) — Candidate values |
| 11 | `formula-13` | formula | `p0011-b006e` | Equation (13) — Update cell state |
| 11 | `formula-14` | formula | `p0011-b006f` | Equation (14) — Output gate |
| 11 | `formula-15` | formula | `p0011-b006g` | Equation (15) — Update hidden state |
| 14 | `extended-data-figure-1` | figure / `supp_figs` | `p0014-b002` | Extended Data Fig. 1 |

Numbering deliberately follows the **printed equation numbers**, so `formula-N` = equation (N)
throughout the main document. The four placeholders the coordinator listed
(`formula-p0011-003`, `formula-p0011-006`, `figure-p0014-002`, `figure-p0014-003`) are all gone,
as is `formula-p0010-029` and the misclassified `table-p0010-015`.

**No tables are emitted from this range.** The only `table` item, `p0010-b015`, was not a table —
it was the displayed LSTM equation block — so it was removed rather than transcribed. There are
now zero `table` items on pages 8–14.

Document-wide check run after editing: no duplicate item ids, no duplicate asset names in any
category, no remaining `-pNNNN-NNN` placeholder names anywhere in the document.

---

## Data availability / Code availability statements (verbatim, page 11)

**Data availability** (`p0011-b029` heading, `p0011-b030` body):

> The datasets generated and analyzed during the current study, along with the generative model, are available via Zenodo at https://doi.org/10.5281/zenodo.11137638 (ref. 73).

**Code availability** (`p0011-b031` heading, `p0011-b032` body):

> The full code for running our generative model is available via Zenodo at https://doi.org/10.5281/zenodo.11137638 (ref. 73).

In the page JSON both URLs are stored as Markdown links
`[https://doi.org/10.5281/zenodo.11137638](https://doi.org/10.5281/zenodo.11137638)`, matching the
PDF's link annotations. Reference 73 itself (page 12, `p0012-b039`) reads:

> 73. Vakili, M. G. Quantum computing-enhanced algorithm unveils novel inhibitors for KRas. *Zenodo* https://doi.org/10.5281/zenodo.11137638 (2024).

---

## Source-side defects preserved, not "repaired"

These are printed that way in the published article; all were confirmed on a 200–400 dpi render,
not merely in the text layer. They are transcription-faithful and deliberately left alone:

1. **Page 14 — the Extended Data Fig. 1 caption duplicates itself.** The left column runs
   "…modeling priors for the QCBM. **We** Comparative Benchmarking of Quantum and Classical Ligand
   Design Methods. (A, B) Comparative analysis of our hybrid" and the right column then repeats the
   entire description before ending "…across the repetitions." The restart mid-sentence after "We"
   is a defect in the article. Transcribed as printed.
2. **Page 14 typography inside the image crop:** banner reads "Clasical" (one s); panel C's y-axis
   reads "Succcess Rate (SR)%" (three c's); legend reads "avrage of SR% with QCBM prior". Caption
   contains the ungrammatical "more detailed is reported in Supplementary Information Table S3.2."
3. **Page 11 — Algorithm 2 line 12 prints `end If`** (capital I) where Algorithm 1 prints `end if`.
   Preserved per the "do not silently repair pseudocode" rule.
4. **Page 12, ref 63** prints "KRas G12C Game of **Yhrones**" (for "Thrones").
5. **Page 12, ref 58** prints "Fedorchenko, **S A.**" (no period after the initial) and
   "**Zavoronkovs**, A."

## Flagged for coordinator adjudication — NOT applied

**Page 8, `p0008-b011`: a wrong link annotation in the published PDF.** The accession `27719`
in "The chemical shifts were transferred from Biological Magnetic Resonance Bank 27719 (ref. 54)"
carries a live link to `http://www.ebi.ac.uk/arrayexpress/experiments/E-MTAB-1975/` — an unrelated
ArrayExpress record, not a BMRB entry. I did **not** turn it into a Markdown link: propagating it
would actively mislead an agent following the skill, and inventing the correct BMRB URL would be
authoring rather than transcription. `27719` is left as plain text. If you want the source link
preserved for fidelity, the one-line change is in `p0008-b011`.

---

## Proposed shared changes I could not make myself

1. **`plan.json` `reading_order`** — not needed for my range. Every float I found (the two algorithm
   listings and all fifteen equations) sits in its own column at the point where the prose refers to
   it, so per-page item reordering was sufficient. I added **no** `reading_order` entries and
   recommend none for pages 8–14.
2. **Page 7/8 boundary** — resolved on my side: `p0008-b002` has `join_previous: "space"`, and the
   pages 1–7 reviewer has confirmed it resolves to `p0007-b014`. Nothing further.
3. **Page 14/15 boundary** — no join, per the pages 15–21 reviewer's check and my own: the
   Extended Data Fig. 1 caption ends a complete sentence.
4. **Global heading-bold pass** — I left every `# **Name**` / `## **Name**` bold marker in place as
   instructed and only corrected heading *levels*. Eight headings in my range were demoted `#` → `##`
   (page 8: `b003`, `b005`, `b007`, `b010`, `b012`; page 9: `b007`, `b012`, `b015`). After your bold
   pass, the intended hierarchy for the whole Methods block is: `# Methods` (p7) → `##` for all
   Methods subsections through page 11's `## Reporting summary`; then `#` again for
   `Data availability`, `Code availability` (p11), `References`, `Acknowledgements` (p12),
   `Author contributions`, `Competing interests`, `Additional information` (p13).
5. **Bundle-level note worth adding to `plan.json` `notes`** — the Extended Data Fig. 1 caption on
   page 14 is duplicated in the published source and is transcribed as printed; readers of the built
   skill will otherwise assume a conversion bug.
6. **Bundle-level note, optional** — `<sub>` markup now appears in the main document for the first
   time (chemical formulas, IC50, β2, and mathematical indices). If the line-coverage check strips
   HTML tags it is a non-event; if it does not, pages 8–12 will show coverage warnings on exactly
   those tokens. Worth a look at the first `verification.json` after the build.
7. **`table` category is now empty for the main document.** If any downstream step expects at least
   one main-document table asset, note that `table-p0010-015` was correctly deleted, not renamed.

## Anything I could not fully verify

- **Nothing was left unverified by eye.** All seven previews were opened, and every region I changed
  was additionally re-rendered from `source.pdf` at 200–900 dpi.
- Two residual judgement calls worth a second opinion:
  - **Equations as images.** Equations (1)–(15) are individually transcribable in principle, but the
    extractor's own attempt was corrupt (combining tildes, lost operator spacing) and the review plan
    prefers an image when faithful transcription is uncertain. I chose fifteen tightly-cropped
    formula images over hand-typed LaTeX-ish text. The consequence is that the LSTM/QCBM equations
    are not text-searchable in the built skill; the surrounding prose that names every symbol is.
  - **Page 8 `27719` link**, described above.
