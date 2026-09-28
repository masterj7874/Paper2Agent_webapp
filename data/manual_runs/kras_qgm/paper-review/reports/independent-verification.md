# Independent verification — quantum-kras-paper

Fresh verifier, no prior involvement in the page reviews. Package treated as read-only.
Originals: `originals/s001-03.pdf` (21 pp) and `originals/s002-si-v0.pdf` (37 pp), re-extracted and
re-rendered with pymupdf rather than trusting `documents/*/evidence` or `verification.json`.

**Overall: fit to deliver after one recommended fix (D1) and two documentation corrections (D2, D3).
No factual corruption of data was found. Transcription fidelity of the prose is excellent.**

---

## Verdict per claim

### 1. Every figure crop is complete — **CONFIRMED** (on a 47-of-55 sample)

The known vector-outside-raster defect is genuinely repaired in everything I opened.

| Group | Checked | Result |
| --- | --- | --- |
| `extended-data-figure-1..5` | all 5, against rendered source pp. 14-18 | complete: all panels, all panel letters, both axes, legends, colour bar, and the green-dashed / dotted vector frames on ED 3, 4, 5 are fully inside the crop |
| `scheme-s1` .. `scheme-s13`, plus both `scheme-s8-*` | all 14, against source pp. 2, 4, 6, 8, 11, 15, 18, 21, 24, 26, 29, 30, 32, 34 | complete: starting material, every arrow with its reagents/conditions above and below, every intermediate and product label |
| `si-nmr-*` | 8 of 14 (`-1`, `-11`, `-12`, `-15`, `-16`, `-18-and-ism061-18-2`, `-22`, `-24-2`) | complete: full ppm axis, full intensity axis, peak-label combs, integral marks; `-1` also keeps the acquisition-parameter box and the structure/formula inset |
| `figure-1`, `figure-2` | both, against source pp. 2 and 4 | complete: Fig. 1 panels a-d with the bottom Classical / Quantum(HW) / Quantum(SIM) legend; Fig. 2 panels a-g with both compound banners |
| `formula-1` .. `formula-15` | all 15 | see claim 3 |
| `figure-s1`, `figure-s2` | both, against source p. 37 | complete, including the `K_D (M):5.83e-12` annotation and both panel letters |
| `reporting-summary-page-3` | 1 of 3 | full page |

- **No caption text is baked into any crop.** Every Extended Data crop stops above the
  `Extended Data Fig. N |` caption block; both `scheme-s8` crops stop above `Scheme S8 …`.
- **No content is cut off at an edge** in any asset I opened. Two things that look like clipping
  are **source artefacts, not crop errors**, and I verified both by re-rendering the source page:
  - `si-nmr-ism061-22.jpg`: the top intensity tick `3.8×10¹¹` has its exponent shaved — the source
    plot frame on p. 32 does exactly the same.
  - several NMR crops show a leftmost x-tick reading `).5` — the source clips the `1` of `10.5`
    behind the plot box on pp. 14, 32 and elsewhere.

Not opened: `reporting-summary-page-1`, `-2`, and `si-nmr-ism061-3-2 / -6 / -13 / -14 / -21 / -24`
(8 of 55 assets). See coverage statement.

### 2. `scheme-s8-ism061-22` starting material restored — **CONFIRMED**

Compared against source p. 30. The delivered JPEG shows the complete two-step scheme:
2-chloropyrimidin-4-amine (Cl / N-N / NH₂) at the far left, the boronic-acid reagent drawn above
arrow 1 with `Pd(dppf)Cl₂, K₂CO₃, dioxane-H₂O, 100 °C, 1 h` below it, intermediate **22-1**, the
4-bromo-1-methylindole reagent above arrow 2 with `xantphosPdG₄, Cs₂CO₃, dioxane, 110 °C, 3 h`
below, and the labelled product **ISM061-22**. Nothing amputated; caption excluded.

### 3. Fifteen equation images — **CONFIRMED**

All 15 opened and matched line-by-line against the source text of pp. 10-11.

- Real displayed equations, all from main pp. 10 (1-7) and 11 (8-15). Correct.
- Printed equation number inside every crop: `(1)` … `(15)`, right-aligned, none clipped.
- Correct order, none duplicated, none missing. The discriminating detail is right:
  (10)-(14) carry the primed `x′_t` that distinguishes them from the otherwise identical
  (1)-(5), and (13)/(15) correctly repeat (4)/(6) verbatim as the source does.
- Link order in `paper.md` (lines 277-287, 293, 299, 305-317) matches the source's placement:
  (1)-(6) after "The following equations can describe the LSTM's operations", (7) after
  "The NLL loss for a single data point is given by", (8) after "the mean of the individual
  losses", (9)-(15) after "updated with the following operations".

### 4. Reading order and prose continuity — **PARTIAL**

**The specific claim is CONFIRMED.** Source p. 3 ends mid-sentence at
`… ISM061-022 did not show binding to KRAS-G12D`; p. 4 is the full-page Fig. 2 float; p. 5
resumes `according to SPR. The compound also demonstrated activity against WT HRAS and NRAS …`.
`references/paper.md` line 43 reads continuously across that break, the Fig. 2 image link and
caption are relocated to lines 45-47 immediately after that paragraph closes, and they appear
exactly once — not dropped, not duplicated. The following paragraph (line 49) is the p. 5
"Overall, these live-cell experimental observations…" continuation, in the right place.

**But an equivalent defect at the p. 1 → p. 2 boundary was not repaired.** See D1 below.
Because the claim is about the class of defect, not just one instance, I grade this PARTIAL.

### 5. Numbers and identifiers — **CONFIRMED**

| Item | Source | Package |
| --- | --- | --- |
| ISM061-018-2 affinity for KRAS-G12D | `registered at 1.4 μM` (p. 3, p. 9); `high binding affinity of 1.4 μM` (p. 5) | `1.4 μM`, 3 occurrences, lines 39 / 49 / 209 |
| Mutants ISM061-022 is selective for | `particularly KRAS-G12R and KRAS-Q61H` (pp. 3, 9) | identical, lines 43 and 213 |
| `IC50` | plain `IC50` in the text layer, subscript in print (pp. 3, 9) | `IC<sub>50</sub>`, 3 occurrences |
| `10^60` | `~1060` in the text layer, superscript in print (p. 1) | `~10<sup>60</sup>` |
| Compound identifiers | main uses **ISM061-018-2** / **ISM061-022**; supplement uses **ISM061-18-2** / **ISM061-22** | both conventions preserved in the file that uses them; `ISM061-18-2` never appears in `paper.md`, `ISM061-022` never appears in `supplement.md` |
| Source typo `ISM018-2` (main p. 8) | present | preserved verbatim (line 171) |
| Source typos `ISM023-18` / `ISM023-18-2` (SI p. 27) | present | preserved verbatim (lines 343, 347) |

**Hyphen audit (automated, both files).** I extracted every hyphenated token from both reference
files' prose and tested it against the source text in both a hyphen-kept and a hyphen-swallowed
normalisation. Result: **zero invented hyphens** in `paper.md` and **zero** in `supplement.md`
(the two `paper.md` hits were false positives caused by superscript citation markers — `Aspuru-Guzik¹`
and `SELFIES–VAE³⁹`). Spot-checks of the claimed repairs:

- `ISM061-018-2` in the Fig. 2 caption: the source prints `ISM061-` at the end of one line and
  `018-2` on the next, so the hyphen is genuine. Repair correct.
- `artificial-intelligence-driven` (p. 10): genuine compound broken over a line. Correct.
- `(M)QCBM–LSTM` and `SELFIES–VAE`: en dashes, and the package kept them as en dashes rather than
  flattening to hyphens. Correct.

### 6. Documented limitations — **CONFIRMED except one note, which is REFUTED, plus one gap**

Independently re-derived, every sub-claim:

| Claimed limitation | Verdict | Evidence |
| --- | --- | --- |
| Main pp. 19-21 image-only, not searchable | **CONFIRMED, exactly** | raw extractable characters = 0, 4, 2 — precisely the numbers in the note; p. 20 = `'μ\nμ\n'`, p. 21 = `'₂\n'`. Page size 612×792 vs 595.276×790.866 for the article pages: confirmed. They are checkbox forms: confirmed by rendering p. 21 |
| Supplement p. 28 image-only | **CONFIRMED** | 0 characters, 1 embedded image, 713 vector drawings |
| Section S2 absent, numbering runs S1 then S3 | **CONFIRMED** | heading scan of all 37 pages: S1, S1.1 ×2, S1.2 … S1.13, then S3. No S2 anywhere |
| No reference list; ends cleanly | **CONFIRMED** | last content on p. 37 is the Figure S2 caption; no reference section on any page |
| No quantum/ML content | **CONFIRMED** | I reran the keyword scan (quantum, qubit, circuit, ansatz, VQE, QAOA, generative, neural, latent, hyperparameter, pseudocode, algorithm, STONED, SELFIES, QCBM, docking, Tanimoto, Lipinski, PAINS, SYBA + LSTM, machine learning): only p. 1's title line matches |
| S1.9 printed twice; Scheme S8 printed twice | **CONFIRMED** | S1.9 on pp. 24 (ISM061-16) and 30 (ISM061-22); Scheme S8 on pp. 21 (ISM061-15) and 30 (ISM061-22). The note's extra claims — S1.1 twice on pp. 1-2, ISM061-22 out of sequence between S1.11 and S1.12 — are also true |
| Supplement is an early author draft from the Zenodo archive, not the publisher's SI | **CONFIRMED on all offline-checkable evidence; PARTIAL on provenance** | SI PDF metadata: no title, no author, producer `macOS … Quartz PDFContext`, created **2024-02-11** — three months before the paper was *received* (7 May 2024). Page size A4 595×842, not the article's 595.276×790.866. Its title line is the Zenodo deposit title ("Quantum Computing-Enhanced Algorithm Unveils **Novel** Inhibitors for KRAS"), not the published title ("…unveils **potential** KRAS inhibitors"). Main PDF by contrast: creator `Springer`, subject `Nature Biotechnology, doi:10.1038/s41587-024-02526-3`. The specific Zenodo DOI and GitHub tag cannot be checked without network access — unfalsified, not independently verified |

**Preserved source defects — I verified each is genuinely in the source, so preserving them is
correct behaviour and none should be "fixed":**

- Main p. 8: `Biological Magnetic Resonance Bank 27719` carries a link annotation to
  `http://www.ebi.ac.uk/arrayexpress/experiments/E-MTAB-1975/`. Real. Correctly kept as plain text.
- Main p. 14: the Extended Data Fig. 1 caption really does restart itself after the word "We".
- Main p. 14 artwork: `Clasical vs. Quantum Modelling`, `Succcess Rate (SR)%`, `avrage of SR% with
  QCBM prior` — all confirmed by rendering; they are vector text inside the figure, so the crop, not
  the text, carries them.
- Main p. 11 `end If`; p. 12 `Game of Yhrones`, `Fedorchenko, S A.`, `Zavoronkovs, A.`;
  p. 18 `|Ψ(0)⟩` with a digit zero; pp. 10-11 doubled ket bar `||ψ(θ)⟩`; ED Fig. 3 caption ordering
  (B), (A), (C) — all confirmed present.
- Supplement: `ISM023-18` (p. 27), `Step 3: Preparation of Compound 15-3` where it should be 16-3
  (p. 24 — the note's page is right; p. 22 has the legitimate 15-3), `3 µmol` (p. 14),
  `1.20 (s, 0H)` and the fullwidth comma (p. 17), `under reduce pressure` (p. 16),
  `yellow soild` (p. 35), `where synthesized` (p. 37), lowercase `Pd(pph3)2Cl2` (p. 22) — all real.
- Fig. 1 artwork also contains `Qunatum samples`; preserved (inside the image), not listed in the
  notes. Harmless.

**REFUTED note — see D3.** **Undocumented true limitation — see D2.**

### 7. Navigation index — **PARTIAL**

- All 15 listed headings exist **verbatim** in the file they point at (12 in `paper.md`,
  3 in `supplement.md`). Verified by exact string match.
- All 55 asset links in both reference files resolve to real files, and all 55 delivered assets
  are referenced — no broken links, no orphans.
- Two location descriptions are **wrong**: see D4 and D5.
- The index omits rows for two real Methods headings (`Cell viability assay`,
  `Protein purification and NMR: sample preparation`). Incomplete rather than wrong.
- The "Assets" block describes `assets/table/` and `assets/supp_table/` as though populated;
  both are empty. Part of D2.

---

## Ranked defects

### D1 — Running header embedded in body prose, sentence broken across pages 1→2 (**moderate**)

- **Source:** main PDF pp. 1-2. Page 1's last body line is `…which can produce cardinality
  distributions beyond the training set and overcome`; page 2's body continues
  `learning challenges such as barren plateaus.`
- **Package:** `references/paper.md`, end of line 25 and start of line 27.
- **What is wrong:** line 27 begins
  `Nature Biotechnology | Volume 43 | December 2025 | 1954–1959 learning challenges such as barren
  plateaus.` The page-2 running header has been left inside the body text, and the sentence that
  starts at the end of line 25 is split across a paragraph break with the header wedged in.
- **Why it matters:** this is the same class of defect the conversion explicitly claims to have
  repaired for the Fig. 2 float (note at line 495). It is the *only* running header left anywhere in
  the body — every other page's header was stripped — so it reads as a one-off miss rather than a
  policy. An agent grepping `barren plateaus` lands on a sentence that begins with a journal folio.

### D2 — The absence of all Supplementary Tables is undocumented, while the index advertises table assets (**moderate**)

- **Source:** main paper cites Supplementary Table 1 (×4), 2 (×2), 3 (×3), 4 (×2), 6 (×1),
  Supplementary Fig. 4 (×2), and `Supplementary Information Table S3.2` in the ED Fig. 1 caption
  (main pp. 3, 7, 9, 10, 14). The supplement itself cites `Table 2` and `Table 3` (SI p. 37).
- **Package:** `assets/table/` and `assets/supp_table/` are **empty**; no table exists anywhere in
  the package. Yet `references/index.md` (Assets block) says
  "`assets/table/`: main tables (CSV, or JPEG when transcription is unreliable)",
  "for a table, read its header and relevant rows first", "CSVs retain internal blank rows…",
  and `SKILL.md` says "For tables, read the relevant CSV header and rows; use the full CSV when
  analysis requires it." The skill description also promises "…figures and **tables**".
- **What is wrong:** the conversion notes explain away only the *computational* supplementary
  material ("contains no supplementary material for the paper's computational contribution").
  That does not cover **Supplementary Tables 3, 4 and 6**, which are the wet-lab tables holding the
  MaMTH-DS IC₅₀ values and the SPR affinities — precisely what a user will ask for. Nor does anything
  note that SI p. 37's own `Table 2` / `Table 3` are dangling references in the source.
  The result is that the package invites a search for tables it does not contain and never says so.
- **Suggested wording:** one line in both Conversion notes blocks —
  "This package contains no tables. Supplementary Tables 1-6 and Supplementary Fig. 4, cited by the
  main text, and Tables 2-3, cited by supplement S3, are not present in either source PDF."

### D3 — A Conversion note overstates link preservation; three PDB links were dropped (**minor-moderate**)

- **Source:** main p. 7 carries four PDB link annotations — `1SYH`, `6Y2F`, `4LDE` (×2), each
  pointing at `https://doi.org/10.2210/pdbXXXX/pdb`.
- **Package:** `references/paper.md` lines 147 and 149 carry `PDB 1SYH,` `PDB 6Y2F,` `PDB 4LDE`
  as plain text with no URL. The only Markdown-linked PDB accessions are 7EW9 and 5US4.
- **What is wrong:** the note at line 491 states "All other link annotations in the document were
  preserved as Markdown links, including six the extractor had dropped…". That is false. Per the
  brief, a false limitation note is as bad as a missing one. (The bioRxiv DOI in ref. 23 and the
  Creative Commons URL on p. 6 are present as bare URLs rather than Markdown links, which is
  defensible; the three PDB targets are lost outright.)

### D4 — `index.md` mislocates equations (1)-(15) (**minor**)

- **Package:** `references/index.md` line 11 — "Quantum-assisted algorithm | Under Methods: the LSTM
  and QCBM formulation, including displayed equations (1)-(15), which are preserved as images".
- **What is wrong:** `## Quantum-assisted algorithm` spans `paper.md` lines 229-234 and contains no
  equations and no LSTM/QCBM formulation. Equations (1)-(15), the `Classical model: LSTM model`
  block and the `Quantum generative model: QCBM model` block are all under
  `## Quantum-computing-enhanced workflow` (lines 235-345). An agent following the index to find the
  equations reads six lines of prose and finds nothing.

### D5 — `index.md` reverses the position of the assay protocols (**minor**)

- **Package:** `references/index.md` line 17 — "Experimental validation methods | Under Methods:
  parent heading for the assay protocols that **follow it**".
- **What is wrong:** the assay protocols all *precede* it. `paper.md` order is SPR conditions (155),
  MaMTH-DS (159), Cell viability assay (163), Protein purification and NMR (167), NMR experiments
  and analysis (173), then `## Experimental validation methods` (177), which is followed by the
  Chemistry42 selection criteria and a prose recap of the results. This ordering is faithful to the
  source (main pp. 7-9); only the index's description of it is wrong.

### D6-D9 — cosmetic, not worth fixing

- **D6** The stray `s` glyph the source prints between the Table 2 sentence and the Figure S1 caption
  (SI p. 37) is dropped from `supplement.md` but baked into the right edge of `figure-s1.jpg`.
  Inconsistent, harmless.
- **D7** The `si-nmr-*` and `scheme-s8-*` link labels ("1H NMR spectrum of ISM061-1") are editorial —
  the source prints no captions at all for the spectra. Consistent and useful, but not noted as
  authored text.
- **D8** `extended-data-figure-1.jpg`: the rounded left edge of the blue "Clasical vs. Quantum
  Modelling" banner sits flush at x=0 and may be shaved by a pixel or two. All content legible.
- **D9** `si-nmr-ism061-18-and-ism061-18-2.jpg` carries roughly 25% trailing whitespace from the
  bottom of source p. 28.

### Explicitly NOT defects (checked and cleared)

- The clipped `3.8×10¹¹` top tick in `si-nmr-ism061-22.jpg` and the clipped `10.5` x-tick in several
  NMR crops are clipped **in the source PDF**; the crops are faithful.
- Right-edge arrowheads that appear to point at nothing in `scheme-s2` and `scheme-s4` do exactly
  that in the source (the row wraps).
- Every "typo" listed in the Conversion notes was verified present in the originals.

---

## Retrieval question

> What binding affinity was measured for ISM061-018-2 against KRAS-G12D, by what method, and where
> in the paper is that stated?

**Answer, using only the delivered package:**

**1.4 μM**, measured by **surface plasmon resonance (SPR)**.

It is stated three times in `references/paper.md`:

- **line 39** (main text, printed p. 1956 / main-PDF p. 3) — the primary statement:
  "The compound ISM061-018-2, engineered through our hybrid quantum model (Fig. 2b and Supplementary
  Table 6), demonstrated substantial binding affinity to KRAS-G12D, registered at 1.4 μM." The same
  paragraph establishes the method: "the SPR determined their binding affinities."
- **line 209** — Methods → *Experimental validation methods* → *Experimental evaluation methods of
  generated compounds*, which repeats the value and cites Supplementary Table 3 instead of 6
  (a source inconsistency, faithfully preserved).
- **line 49** — the closing summary: "ISM061-018-2 displaying a high binding affinity of 1.4 μM".

Supporting assets: the sensorgrams are **Fig. 2b** (`assets/figure/figure-2.jpg`, panel **b**,
titled `SPR: ISM061-018-2`), and the SPR protocol is `paper.md` line 157 under `## SPR conditions`
(Biacore 8K, biotinylated KRAS-G12D on a Sensor Chip SA, twofold dilutions 200 → 0.39 μM). The
supplement's `## S3. Surface Plasmon Resonance Affinity Measurements` gives the same protocol and
`Figure S2` shows multiple-cycle response curves for ISM061-18-2.

**How well the package supported it: well.** Two commands: `grep -n 'spr' references/index.md`
(which pointed at `SPR conditions` and `S3`), then `grep -n 'binding affinity' references/paper.md`,
which returned all three loci with enough surrounding text to answer without reading further. I
opened `index.md`, `paper.md` (three bounded passages), `figure-2.jpg` to confirm panel **b** is
labelled `SPR: ISM061-018-2`, and `supplement.md` line 443ff. Total: four files.

Two frictions worth recording:
- The index has **no row that leads to the results narrative at all** — the Brief Communication body
  carries no headings in the source, so the index can only route to Methods. A reader who trusts the
  index and reads `SPR conditions` gets the protocol and never sees the number. The answer is only
  reachable by keyword search, which `SKILL.md` does tell you to do.
- The paper points at **Supplementary Table 6** (and, in Methods, Table 3) for the underlying data.
  Neither exists in the package and nothing says so — D2. A user who wanted the full affinity table
  rather than the headline number would dead-end without explanation.

---

## Coverage statement

**Main PDF (s001-03, 21 pp).** Text layer extracted and read for **all 21 pages**. Pages 1-11 read in
full against `paper.md`; pp. 12-13 (references 37-73, end matter) checked by automated
sentence-matching; pp. 14-18 rendered at 150 dpi and compared visually against the five Extended Data
crops; pp. 19-21 checked for text-layer content (0/4/2 chars) and page geometry, and
`reporting-summary-page-3.jpg` opened. Pages 2 and 4 rendered and compared against `figure-1.jpg`
and `figure-2.jpg`. All link annotations on all 21 pages enumerated.

**Supplement PDF (s002-si-v0, 37 pp).** Structural scan (text-layer char count, embedded-image count,
vector-drawing count, heading regex) over **all 37 pages**. Pages 1, 2, 4, 8, 14, 21, 23-26, 28-32,
36, 37 read and/or rendered in full. Pages 3, 5, 7, 9, 10, 12, 13, 16-20, 22, 27, 33-35 covered by
automated sentence-matching only (they are continuous synthesis prose).

**Automated whole-document checks (both PDFs).** Sentence-level fidelity in both directions
(package→source and source→package), hyphenation audit, keyword scan, heading scan,
cross-reference scan, link-annotation enumeration, PDF metadata.

**Assets: 47 of 55 opened and compared.** Not opened:
`assets/figure/reporting-summary-page-1.jpg`, `reporting-summary-page-2.jpg`, and
`assets/supp_figs/si-nmr-ism061-3-2.jpg`, `-6`, `-13`, `-14`, `-21`, `-24`. Every one of the 55 was
checked for link resolution and for being referenced from a document.

**Not done.** I did not re-run `paper_bundle.py`, did not read `verification.json`, `build.json`,
`bundle.json` or the six page-review reports, did not use the pre-rendered `previews/` or
`evidence/` JSON, and did not verify the Zenodo DOI or the GitHub tag (no network).
