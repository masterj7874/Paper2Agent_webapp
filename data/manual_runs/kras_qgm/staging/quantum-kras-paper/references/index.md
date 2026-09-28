# Paper navigation

Use exact headings to locate current line numbers. Read relevant passages, not both complete documents. This index locates evidence; it does not summarize findings.

## Main paper — [paper.md](paper.md)

| Exact heading | Look here for |
| --- | --- |
| Methods | Full protocol section; the computational method, benchmark setup and all wet-lab assay conditions live under it |
| Quantum-assisted algorithm | Under Methods: the LSTM and QCBM formulation, including displayed equations (1)-(15), which are preserved as images |
| Quantum-computing-enhanced workflow | Under Methods: how the quantum prior is combined with the classical generator end to end, and the two algorithm listings |
| Computational benchmarks: classical versus quantum models | Under Methods: how the quantum and classical models were compared, including the qubit-count scaling study |
| Data acquisition and preprocessing | Under Methods: how the training set was assembled by virtual screening and STONED-SELFIES expansion |
| Benchmark setup | Under Methods: hardware, backend and evaluation configuration used for the reported runs |
| Experimental validation methods | Under Methods: parent heading for the assay protocols that follow it |
| SPR conditions | Under Methods: surface plasmon resonance binding-affinity protocol |
| MaMTH-DS dose–response assays | Under Methods: live-cell target-engagement assay protocol |
| NMR experiments and analysis | Under Methods: protein NMR acquisition and interpretation |
| Code availability | Where the authors deposited the generative-model code |
| Data availability | Where the authors deposited the datasets and the trained model |

For long sections, search a narrower subsection or prompt. Headings inside fenced quotations are source content, not document section boundaries.

## Supplementary information — [supplement.md](supplement.md)

| Exact heading | Look here for |
| --- | --- |
| S1. Chemistry | The whole synthetic-chemistry section; per-compound routes S1.1-S1.13 with schemes and 1H NMR spectra sit under it |
| S1.1. General Synthetic Procedures | Under S1: shared reagents, workup and analytical conditions applied across the individual syntheses |
| S3. Surface Plasmon Resonance Affinity Measurements | The supplement's only non-chemistry section, at its very end; SPR response curves for ISM061-18-2 |

For long sections, search a narrower subsection or prompt. Headings inside fenced quotations are source content, not document section boundaries.

## Assets

Figure and table captions in the documents link to the files below. Open only the needed image; for a table, read its header and relevant rows first.

- `assets/figure/`: main figures (JPEG).
- `assets/supp_figs/`: supplementary and extended-data figures (JPEG).
- `assets/table/`: main tables (CSV, or JPEG when transcription is unreliable).
- `assets/supp_table/`: supplementary tables (CSV, or JPEG fallback).

Asset paths are relative to the skill root. CSVs retain internal blank rows; captions and merged headers may also occupy rows. Consult the document notes before treating every row as data.
