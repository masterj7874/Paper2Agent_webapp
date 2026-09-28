# Environment manager results — quantum-generative-models (KRAS QGM)

- **Project root:** `/media/jerisuh/4,0TBDisk1/Paper2Agent_webapp/data/manual_runs/kras_qgm/mcp-project`
- **Pinned source (read-only, unmodified):** `repo/quantum-generative-models` @ tag `1.0.0-beta.1`, commit `20cb407b228735dc479737cf765448e9c7d5a9cc`
- **Environment:** `/media/jerisuh/4,0TBDisk1/Paper2Agent_webapp/data/manual_runs/kras_qgm/mcp-project/.venv`
- **Interpreter:** `/media/jerisuh/4,0TBDisk1/Paper2Agent_webapp/data/manual_runs/kras_qgm/mcp-project/.venv/bin/python`
- **Host:** Linux 6.14, `uv` 0.8.11, CUDA 12.8 at `/usr/local/cuda-12.8`, 2× NVIDIA RTX PRO 6000 Blackwell Max-Q (95 GiB each, sm_120, driver 575.57.08)

---

## 1. Interpreter version and justification

**CPython 3.10.18**, created with:

```bash
uv venv --python 3.10 "$PROJECT_ROOT/.venv"
```

(uv downloaded the managed 3.10.18 build; system Python is 3.13.5 and was **not** used.)

Why 3.10 and not 3.13:

| Constraint | Effect |
|---|---|
| Repo's own SLURM launcher loads `python/3.10.4` (`README.md`) | 3.10 is the version the authors ran |
| `models/priors/qcbm_qiskit.py` and `models/{priors,error}/error*.py` use **Qiskit 0.x** APIs (`from qiskit import Aer, IBMQ, execute, assemble`, `qiskit.providers.aer`, `qiskit.ignis`) — all removed in Qiskit ≥ 1.0 | forces `qiskit-terra` 0.22.x + `qiskit-aer` 0.11.x + `qiskit-ignis` 0.7.1, whose last wheels target ≤ cp311 |
| `utils/filter_comp.py:47`, `stoned_algorithm/MCF_TEST.py:25`, `stoned_algorithm/stoned_hill_climming.py` use `DataFrame.append(...)`, removed in pandas 2.0 | forces `pandas<2` → `pandas==1.5.3`, last wheels cp310/cp311 |
| `qiskit-aer==0.11.2` is a numpy-1.x ABI build | forces `numpy<2` → `numpy==1.26.4` |
| `fastmcp==4.0.3` requires Python ≥ 3.10 | satisfied |

3.10 is the only version that satisfies all four simultaneously with binary wheels. `reports/python-version.txt` = `Python 3.10.18`.

> **Note on the Qiskit 2.x claim in `.pipeline/language.json`.** The recorded evidence says "qiskit 2.5.2 … present on PyPI". True, but irrelevant: the repository's quantum code cannot run on Qiskit ≥ 1.0. The route decision (Python) is correct; the *version* evidence needed correcting.

## 2. Exact install commands and resolved versions

```bash
PY="$PROJECT_ROOT/.venv/bin/python"

# 1. core scientific stack
uv pip install --python "$PY" \
  'numpy<2' 'scipy<1.14' 'pandas==1.5.3' 'tqdm' 'matplotlib' 'seaborn' \
  'rdkit==2023.9.6' 'selfies==2.1.1' 'ipython'

# 2. real SYBA (vendored — see §5)
uv pip install --python "$PY" "$PROJECT_ROOT/vendor/syba"

# 3. era-matched Qiskit 0.x stack
uv pip install --python "$PY" \
  'qiskit-terra==0.22.4' 'qiskit-aer==0.11.2' \
  'qiskit-ibmq-provider==0.19.2' 'qiskit-ignis==0.7.1'

# 4. torch, CUDA 12.8 / sm_120 (only for models/vqvae, see §8)
uv pip install --python "$PY" --index-url https://download.pytorch.org/whl/cu128 \
  'torch==2.7.0+cu128' 'torchvision==0.22.0+cu128'

# 5. tested MCP baseline (runtime.md stage 1)
uv pip install --python "$PY" 'fastmcp==4.0.3' pytest pytest-asyncio

uv pip check --python "$PY"    # -> "Checked 153 packages ... All installed packages are compatible"
```

All five commands exited 0. `uv pip check` is clean.

Resolved versions of the load-bearing packages:

| Package | Version | Note |
|---|---|---|
| python | 3.10.18 | uv-managed |
| rdkit | 2023.9.6 | `rdkit.__version__` reports `2023.09.6` |
| selfies | 2.1.1 | dist 2.1.1, module `__version__` says 2.1.0 (upstream metadata bug) |
| syba | 1.0.2a0 | **from `vendor/syba`, not PyPI** |
| qiskit-terra | 0.22.4 | provides `import qiskit`, `qiskit.__version__ == 0.22.4` |
| qiskit-aer | 0.11.2 | provides the `qiskit.providers.aer` alias the source needs |
| qiskit-ignis | 0.7.1 | provides `qiskit.ignis.mitigation.measurement` |
| qiskit-ibmq-provider | 0.19.2 | provides the lazy `qiskit.IBMQ` |
| numpy | 1.26.4 | pinned `<2` for the aer 0.11 ABI |
| pandas | 1.5.3 | pinned `<2` for `DataFrame.append` |
| scipy | 1.13.1 | |
| matplotlib | 3.10.9 | `from matplotlib.pylab import plt` verified working |
| seaborn | 0.13.2 | |
| torch / torchvision | 2.7.0+cu128 / 0.22.0+cu128 | sm_120 verified |
| fastmcp | 4.0.3 | tested baseline, no resolver conflict |

Qiskit API surface actually exercised — every import the source uses resolves:
`QuantumCircuit, Aer, transpile, assemble` · `qiskit.providers.aer.noise` · `qiskit.providers.aer.QasmSimulator` · `qiskit.circuit.Parameter` · `IBMQ` · `execute` · `QuantumRegister, ClassicalRegister` · `qiskit.circuit.library.{XGate,YGate,ZGate}` · `qiskit.ignis.mitigation.measurement.{CompleteMeasFitter, complete_meas_cal}` — all PASS.

## 3. Lockfile

- **`$PROJECT_ROOT/requirements.lock`** — 153 exact pins + a documented header.
- `$PROJECT_ROOT/reports/environment-requirements.txt` — raw `uv pip freeze` snapshot.
- `$PROJECT_ROOT/reports/python-version.txt` — `Python 3.10.18`.

Two entries are not plain PyPI pins, deliberately:

- `torch` / `torchvision` are pinned to **explicit wheel URLs** on `download.pytorch.org/whl/cu128` rather than via `--extra-index-url`. uv refuses a bare extra-index (dependency-confusion guard) and the rebuild fails; direct URLs avoid that and are Linux-x86_64/cp310-specific.
- `syba` is `./vendor/syba` (relative → **rebuild must run from `$PROJECT_ROOT`**).

**Rebuild verified from scratch**, not just written:

```bash
uv venv --python 3.10 "$TMP_ENV"
cd "$PROJECT_ROOT" && uv pip install --python "$TMP_ENV/bin/python" -r requirements.lock   # exit 0
uv pip check --python "$TMP_ENV/bin/python"   # "Checked 153 packages ... All ... compatible"
# -> qiskit 0.22.4 | rdkit 2023.09.6 | pandas 1.5.3 | numpy 1.26.4 | torch 2.7.0+cu128 | cuda True
```

## 4. Orquestra availability verdict — **CONFIRMED UNAVAILABLE**

Evidence gathered independently (2026-09-23):

| Check | Result |
|---|---|
| `GET https://pypi.org/pypi/orquestra-qml-core/json` | **HTTP 404** (`{"message": "Not Found"}`) |
| `GET https://pypi.org/pypi/orquestra-qml/json` | **HTTP 404** |
| GitHub repo search `orquestra-qml OR orquestra_qml` | `total_count: 0` — no fork, no mirror |
| `api.github.com/repos/zapatacomputing/orquestra-qml` | 404 |
| `api.github.com/repos/zapatacomputing/orquestra-qml-core` | 404 |
| `api.github.com/repos/zapatacomputing/z-quantum-qml` | 404 |
| `orquestra-quantum` / `orquestra-opt` / `orquestra-sdk` | HTTP 200 (still published) |

The surviving Orquestra packages do **not** help. Import census of the repo by namespace:

```
31× orquestra.qml.api          27× orquestra.qml.models.qcbm      16× orquestra.qml.optimizers.th
10× orquestra.qml.data_loaders  9× orquestra.qml.models.rbm.th     8× orquestra.qml.models.samplers.th
 8× orquestra.opt.optimizers…   8× orquestra.integrations.qulacs   7× orquestra.qml.trainers
 6× orquestra.quantum.circuits  6× orquestra.qml.models.qcbm.layer_builders   … etc
```

The overwhelming majority is `orquestra.qml.*`, which only `orquestra-qml` / `orquestra-qml-core` provide. **32 of 71** `.py` files import orquestra (the pipeline note said 31; the measured figure is 32). No installable public source exists. **Verdict: genuine, permanent blocker. Nothing to expand scope with.**

## 5. SYBA outcome — **INSTALLED AND WORKING, but the PyPI `syba` is the wrong project**

This is the single most important correction to the recorded evidence.

`.pipeline/language.json` states `syba 0.0.5 … present on PyPI`. That distribution is:

```
name        = SyBA
version     = 0.0.5
summary     = SyBA: a tool and database for standardizing gene names from the
              main bacterial pathogens causing food contamination
author      = Luan Rabelo
home_page   = https://github.com/luanrabelo/SyBA
```

It is an **unrelated bacterial-gene-name tool** and does **not** provide `syba.syba.SybaClassifier`. Installing it would have silently produced a broken environment. The real dependency is the **SYnthetic BAyesian classifier**, `lich-uct/syba` (49 ★, "Synthetic Bayesian Classification"), distributed via conda channel `lich` and GitHub only — **never on PyPI**.

What was done:

1. `git clone --depth 1 https://github.com/lich-uct/syba.git` → HEAD = `30929eb2d3b9a03bef326a1f5180f26f55b19a29` (2021-01-18), version `1.0.2.alpha`.
2. Direct `uv pip install 'syba @ git+…@30929eb…'` **fails**: uv's bare-clone + `git reset --hard` trips git-LFS with `Smudge error … remote missing object 32c6b73f…`, exit 128. Reproduced twice with a cleared uv cache. This is a uv/git-lfs interaction problem, **not** a missing artifact — a normal `git clone` fetches the same OID fine (the vendored `syba.csv.gz` hashes to exactly `32c6b73f…`).
3. Vendored the checkout to `$PROJECT_ROOT/vendor/syba` (`.git`/`docs` stripped) and installed from that path (`uv pip install --python "$PY" "$PROJECT_ROOT/vendor/syba"`, exit 0).

LFS model data materialised (271 MB on disk):

| File | Size | sha256 |
|---|---|---|
| `syba/resources/syba.csv.gz` | 25,795,242 B | `32c6b73f0f4bfddffd00d497fa79702d06f575d413f9a74ea92d91ef41cac679` |
| `syba/resources/syba4.csv.gz` | 115,706,773 B | `2f9ecae968a649d3de629505fe241ad1a1a084232f2a1f1a33ffbf5641441a11` |

Functional proof (not a bare import):

```
SybaClassifier().fitDefaultScore()   -> 28.1 s  (reads syba4.csv.gz, ~5.5 GB resident)
syba.predict("CC(=O)Oc1ccccc1C(=O)O")                                     ->   30.45
syba.predict("CN1CCN(CC1)C(=O)c1ccc(cc1)Nc1ncnc2cc(OC)c(OC)cc12")         ->  160.99
```

**Operational cost to flag for the implementer:** every `fitDefaultScore()` costs ~28 s and ~5.5 GB RSS. A tool must load the classifier once at module scope, never per call.

## 6. Per-module import table

Two columns, because the repository's layout makes the distinction load-bearing:

- **native** — plain `import X` the way the repo expects (`sys.path` = repo root + `repo/stoned_algorithm`; cwd = the module's own directory for `stoned_algorithm/*`, repo root otherwise).
- **isolated** — parent packages registered as synthetic namespace modules so `utils/__init__.py` / `models/__init__.py` (which import orquestra) are **not** executed. Relative imports (`from .mol_methods import …`, `from .error import …`) still resolve normally.

| Module | native | isolated | Detail |
|---|---|---|---|
| `stoned_algorithm/filter_.py` | **PASS** | n/a (flat) | Clean. Exports `apply_filters`, `lipinski_filter`, `maximum_ring_size`, `substructure_violations`, `filter_phosphorus`, `FindAromaticRings`. Zero module-level side effects. |
| `stoned_algorithm/stoned.py` | **FAIL** | n/a | `FileNotFoundError: 'KRAS_G12D_inhibitors_update2023.csv'` at **stoned.py:332**. All imports resolved; the file is a *script* — 70 lines of top-level driver after the defs. |
| `stoned_algorithm/stoned_sim.py` | **FAIL** | n/a | `IndentationError: expected an indented block after 'if' statement on line 447` at **stoned_sim.py:448**. **The pinned source does not parse.** Unfixable without editing read-only source. |
| `stoned_algorithm/stoned_hill_climming.py` | **FAIL** | n/a | `FileNotFoundError: './DATA/mcf.csv'` at **:45**. Imports + SYBA fit (28 s) succeed first. Script, not module. |
| `stoned_algorithm/PAINS_TEST.py` | **FAIL** | n/a | `FileNotFoundError: './DATA/sim_uniq_2023_res_short.csv'` at **:30**. |
| `stoned_algorithm/MCF_TEST.py` | **FAIL** | n/a | `FileNotFoundError: './DATA/mcf.csv'` at **:23**. Would also hit `DataFrame.append` at **:25**. |
| `stoned_algorithm/SYBA_TEST.py` | **FAIL** | n/a | `FileNotFoundError: './DATA/sim_uniq_2023_res_short.csv'` at **:18**. |
| `stoned_algorithm/TEST_GEN.py` | **FAIL** | n/a | `FileNotFoundError: 'output_unique_2023_02_02.csv'` at **:19**. |
| `utils/lipinski_utils.py` | **FAIL** | **PASS** | native: `utils/__init__.py:1` → `utils/callbacks.py:4` → `ModuleNotFoundError: No module named 'orquestra'` |
| `utils/mol_methods.py` | **FAIL** | **PASS** | same orquestra chain |
| `utils/stoned_utils.py` | **FAIL** | **PASS** | same orquestra chain |
| `utils/filter.py` | **FAIL** | **PASS** | same orquestra chain. **cwd-sensitive** — see caveat below. |
| `utils/filter_comp.py` | **FAIL** | **FAIL** | `FileNotFoundError: './DATA/mcf.csv'` at **:45**; also `DataFrame.append` at **:47** and flat `from filter_ import …` at **:10**. Script, not module. |
| `models/priors/qcbm_qiskit.py` | **FAIL** | **PASS** | native: `models/__init__.py:1` → `models/discrete_rgan.py:3` → `import orquestra.qml.models.adversarial.th` → `ModuleNotFoundError`. Isolated: exports `QCBMGenerator`, `RandomCardinalityGenerator`, `ExactNLL`. |
| `models/priors/error.py` | **FAIL** | **PASS** | same; needs `qiskit-ignis`, which is installed |
| `models/error/error_mitigation.py` | **FAIL** | **PASS** | same |
| `models/vqvae/{model,encoder,decoder,codebook,distance,loss,residual,trainer}.py` | **FAIL** (all) | **PASS** (all 8) | same orquestra chain natively; import cleanly when isolated. But see §8 — the code is broken. |

**Exact native traceback tail, shared by every `utils.*` target:**
```
File ".../utils/__init__.py", line 1, in <module>
    from .callbacks import DisplaySmilesCallback
File ".../utils/callbacks.py", line 4, in <module>
    from orquestra.qml.api import Callback, GenerativeModel, TrainResult, convert_to_numpy
ModuleNotFoundError: No module named 'orquestra'
```
**and by every `models.*` target:**
```
File ".../models/__init__.py", line 1, in <module>
    from .discrete_rgan import DiscreteRGAN
File ".../models/discrete_rgan.py", line 3, in <module>
    import orquestra.qml.models.adversarial.th as adversarial
ModuleNotFoundError: No module named 'orquestra'
```

### Functional smoke checks (environment proof, NOT scientific validation)

All PASS in the project interpreter:

```
filter_.apply_filters("CC(=O)Oc1ccccc1C(=O)O")  -> False     (aspirin: MW 180 < 300 cutoff)
filter_.apply_filters(<KRAS-like>)              -> True
utils.filter.passes_wehi_mcf(aspirin)           -> True
utils.filter.pains_filt(aspirin)                -> 0 hits
utils.filter.get_diversity([...])               -> 93.07
utils.stoned_utils.mutate_selfie(...)           -> "CC(=O)OC=CC=CC#CC(=O)O"
utils.stoned_utils.get_fp_scores([...], ECFP4)  -> [1.0, 0.1308]
utils.lipinski_utils.compute_lipinski(aspirin)  -> MW 180.159, logP 1.3101, 1 HBD / 3 HBA
syba.predict                                    -> 30.45 / 160.99
QCBMGenerator.generate(200) on Aer qasm_simulator -> ndarray (200, 4) int64
ErrorMitigation(Aer qasm_simulator)             -> constructs OK
```

### Caveats the implementer must handle

1. **`utils/filter.py` fails *silently* from the wrong cwd.** Lines 38–55 load `./database/{mcf.csv,wehi_pains.csv,pains.txt}` at module scope inside `try/except FileNotFoundError`, which only logs a warning. Import from any other directory and `_filters` / `dic` are never bound, so the first call raises `NameError: name '_filters' is not defined`. Reproduced. **The module must be imported with cwd = repo root**, or the paths resolved another way.
2. **`stoned_algorithm/alphabet.txt` is SELFIES v1 grammar** (`[Branch1_1]`, `[Branch2_1]`), incompatible with the installed `selfies==2.1.1`: `selfies.decoder(<first line>)` → `DecoderError: invalid symbol '[Branch1_1]'`. Only `stoned_algorithm/stoned.py:145` mixes this file into its mutation alphabet, and that module is not importable anyway. `utils/stoned_utils.py:161` uses `selfies.get_semantic_robust_alphabet()` only, so it is unaffected. selfies **2.x is correct** for this repo — `utils/chem.py` calls `sf.selfies_to_encoding`, `sf.encoding_to_selfies`, `sf.batch_selfies_to_flat_hot`, `sf.get_alphabet_from_selfies`, all 2.x-only.
3. **`QCBMGenerator.generate()` infinite-loops with default arguments.** With `sampeling_backend=None` (the default) the constructor's `else` branch never sets `self.sampeling_error_mitigation` (same for `train_error_mitigation`). `generate()` reads it inside a `try` guarded by a bare `except:` that prints `IBMQ ERROR SAMPELING` and **does not decrement `num_samples`** → unbounded loop, unbounded memory. Observed: 10 min at 100 % CPU, 5.7 GB RSS, then killed. Passing an explicit `sampeling_backend` works correctly. Verified both ways.
4. **The paper's QCBM ansatz is orquestra-built.** `QCBMGenerator` itself is pure Qiskit and importable, but the `qcbm_circuit` argument in the driver (`qDrug_generator_benchmark_parallel_v10.py:744`) comes from `EntanglingLayerAnsatz` + `LineEntanglingLayerBuilder` exported through `orquestra.integrations.qiskit.conversions.export_to_qiskit`. Reproducing the paper's circuit in pure Qiskit is a scientific-fidelity decision, not an environment one. (An ad-hoc RX/RZ + linear-CZ ansatz was used only to prove the class runs.)
5. That same driver calls `QCBMGenerator(..., backend=..., noise_model=...)` — parameters that **do not exist** in the class signature (`train_backend` / `sampeling_backend`, no `noise_model`). The v10 driver is out of sync with the pinned class.

## 7. Bundled data inventory

Present in the pinned repo:

| Path | Size | Lines | Content |
|---|---|---|---|
| `database/pains.txt` | 55,457 B | 481 | PAINS SMARTS + regId labels (`ene_six_het_A(483)`, …), space-separated |
| `database/wehi_pains.csv` | 207,418 B | 479 | WEHI PAINS SMARTS, quoted, `smarts,"<regId=…>"`, **no header** (read with `names=["smarts","names"]`) |
| `database/mcf.csv` | 739 B | 23 | 22 medicinal-chemistry filters, header `names,smarts` (`MCF1..MCF22`) |
| `stoned_algorithm/DATA/pains.txt` | 55,457 B | 481 | byte-identical duplicate of `database/pains.txt` |
| `stoned_algorithm/alphabet.txt` | 557,831 B | 7,439 | SELFIES **v1** fragment strings (see caveat 2) |
| `data/KRAS_G12D/KRAS_G12D_inhibitors_update202209_updated.csv` | 60,961 B | 645 | 644 known KRAS G12D inhibitors: `id,smiles,KRAS G12D SPR KD (nM),KRAS G12D binding IC50 (nM),pERK IC50 (nM)` |
| `data/KRAS_G12D/1Mstoned_vsc_initial_dataset_insilico_chemistry42_filtered.csv` | 56,558,455 B | 1,010,510 | ~1.01 M STONED-generated SMILES, Chemistry42-filtered; columns `,smiles` |

**Expected by code but ABSENT** (all are top-level reads in the script-style modules):

| Missing file | Referenced from |
|---|---|
| `stoned_algorithm/DATA/mcf.csv` | `MCF_TEST.py:23`, `stoned_hill_climming.py:45`, `stoned_sim.py` |
| `stoned_algorithm/DATA/wehi_pains.csv` | `MCF_TEST.py:24`, `stoned_hill_climming.py:46`, `stoned_sim.py` |
| `stoned_algorithm/DATA/sim_uniq_2023_res_short.csv` | `PAINS_TEST.py:30`, `MCF_TEST.py:33`, `SYBA_TEST.py:18` |
| `stoned_algorithm/KRAS_G12D_inhibitors_update2023.csv` | `stoned.py:332` (and a commented block in `filter_.py`) |
| `stoned_algorithm/DATA/KRAS_G12D_inhibitors_update2023.csv` | `stoned_hill_climming.py`, `stoned_sim.py`, `utils/filter_comp.py:376` |
| `stoned_algorithm/output_unique_2023_02_02.csv`, `output_unique_2023_CORRECTED.csv` | `TEST_GEN.py:19,~30` |
| `DATA/PASS_sim_uniq_2023_res_short_sascore.csv`, `DATA/PASS_uniq_2023_res_short_sascore.csv` | `stoned_hill_climming.py`, `stoned_sim.py`, `utils/filter_comp.py:380,383` |
| `utils/DATA/{mcf.csv,wehi_pains.csv,pains.txt}` | `utils/filter_comp.py:45,46,60` |
| `/home/mghazi/workspace/insilico-drug-discovery/benchmark_models/genereted_samples/ligands_1SYH_qcbm_sim.csv` | `stoned_hill_climming.py` — **hard-coded author-machine absolute path** |

The `DATA/mcf.csv` and `DATA/wehi_pains.csv` gaps are recoverable (byte-for-byte equivalents live in `database/`, as `DATA/pains.txt` already demonstrates). `sim_uniq_2023_res_short.csv`, `KRAS_G12D_inhibitors_update2023.csv`, `output_unique_2023_*.csv`, the `PASS_*_sascore.csv` files and the `/home/mghazi/...` path are **intermediate artifacts of the authors' runs and were never published**.

`data/KRAS_G12D/` — both files present and readable. Nothing in the orquestra-free subset reads them by path; they are inputs to the orquestra training drivers.

### Credentials

`utils/api.py` defines `RewardAPI(username, password, base_url="https://rip.chemistry42.com")` — the Insilico **Chemistry42** scoring service. It requires HTTP basic-auth credentials (and calls `requests.post(..., verify=False)`, i.e. TLS verification disabled). No credentials exist in this project and none were created. `utils/api.py` is also unreachable anyway — `utils/__init__.py` imports it after the orquestra chain. Any Chemistry42-scoring tool is **blocked on user-supplied credentials** and out of scope.

## 8. Device / GPU findings

**Nothing in the orquestra-free target subset touches a GPU.** `.pipeline/language.json`'s `requires_gpu: false` is correct.

- `grep -niE "cuda|gpu|\.to\(|device"` over `stoned_algorithm/`, `utils/{filter,stoned_utils,lipinski_utils,mol_methods}.py`, `models/error/` → **zero hits**.
- `models/priors/qcbm_qiskit.py` has a `device="cpu"` constructor parameter; it is stored as `self.device` at line 65 and **never read again**. Dead parameter.
- `qiskit-aer==0.11.2` from PyPI is the CPU build: `AerSimulator().available_devices()` → `('CPU',)`. GPU simulation would need `qiskit-aer-gpu`, which is not required and not installed.
- RDKit / SELFIES / SYBA are CPU-only by construction.

torch **was** installed and verified, for `models/vqvae/` only:

```
torch 2.7.0+cu128 | torchvision 0.22.0+cu128 | cuda build 12.8 | cuda available: True
arch list: ['sm_75','sm_80','sm_86','sm_90','sm_100','sm_120','compute_120']
dev0/dev1: NVIDIA RTX PRO 6000 Blackwell Max-Q, sm_120, 95 GiB each
512×512 matmul on sm_120: OK
```

The official `cu128` wheels already ship `sm_120`, so **no source rebuild of PyTorch is needed** on this host.

**But `models/vqvae/` should not become a tool.** It imports cleanly (isolated) yet is unfinished, unreferenced dead code:

- `models/vqvae/encoder.py::Encoder.__init__` references four names that are not parameters and never bound: `in_channels`, `hidden_dim`, `n_residual_layers`, `residual_layer_hidden_dim` → `NameError` on any instantiation. It also calls `nn.Embedding()` with no arguments.
- `models/vqvae/codebook.py::EMAVectorQuantizer.forward` uses `F` (`torch.nn.functional`), never imported in that module → `NameError` on any forward pass.
- Nothing anywhere in the repository references `vqvae`, `VQVAE` or `VectorQuantizer`. It is an image-domain (`nn.Conv2d`, `torchvision.utils.make_grid`) VQ-VAE with no connection to the KRAS molecular pipeline.

If `torch` is dropped from scope, ~4.5 GB of the 7.3 GB venv goes with it.

## 9. Blunt list: what is NOT installable / NOT toolable

**Hard external blockers (no fix exists):**

1. **`orquestra-qml` / `orquestra-qml-core`** — 404 on PyPI, no public fork or mirror. Zapata AI discontinued Orquestra. **32 of 71 `.py` files are dead**: every training driver (`benchmark_models_v0.py`, `benchmark_models_priors.py`, all `qDrug_generator_benchmark_parallel_*.py`, `vanilla_lstm_v0.py`, `sample_generation_from_pretrained_models_v0.py`), `models/discrete_rgan.py`, `models/transformer_mle.py`, `models/{recurrent,aan,gan,transformer}/`, `models/priors/{qcbm,rbm,multi,zeros,loss}.py`, `models/generators.py`, `models/layers/`, and `utils/{chem,data,callbacks,selfies_encoding_class,experiment}.py`.
2. **`orquestra.integrations.qulacs` / `qulacs`** — the paper's actual QCBM training simulator, reachable only through the orquestra stack.

**Source defects at the pinned commit (cannot be fixed without editing read-only source):**

3. **`stoned_algorithm/stoned_sim.py` does not parse** — `IndentationError` at line 448. Cannot be imported by any means, in any environment.
4. **`models/vqvae/encoder.py` and `codebook.py`** raise `NameError` on use (§8). Import-only, never callable.
5. **`QCBMGenerator.generate()`** infinite-loops on default construction (§6 caveat 3). Any wrapper *must* pass an explicit `sampeling_backend`.

**Blocked on data the authors never published:**

6. `stoned.py`, `stoned_hill_climming.py`, `PAINS_TEST.py`, `MCF_TEST.py`, `SYBA_TEST.py`, `TEST_GEN.py`, `utils/filter_comp.py` — all are **top-level scripts**, not importable modules, and all abort on missing intermediate CSVs (§7). Their *functions* can be reached only by AST-level extraction, not by import.

**Blocked on credentials:**

7. `utils/api.py` (`RewardAPI`) — needs Chemistry42 basic-auth credentials. None supplied, none fabricated.

**Version ceilings that constrain everything downstream:**

8. Qiskit is frozen at the 0.x line (`terra 0.22.4` / `aer 0.11.2` / `ignis 0.7.1` / `ibmq-provider 0.19.2`). `qiskit-ignis` was archived by IBM in 2021 and `qiskit-ibmq-provider` was retired in 2024 — neither receives fixes, and `IBMQ.get_provider(...)` no longer reaches a live IBM Quantum service. Any tool touching real IBM hardware is non-functional regardless of packaging.
9. pandas is frozen `<2` and numpy `<2`, so Python cannot move past 3.11 without breaking the stack.

---

## What IS usable

Realistically toolable after this work — imports clean, functions verified to run:

| Source | Usable surface |
|---|---|
| `stoned_algorithm/filter_.py` | `apply_filters`, `lipinski_filter`, `maximum_ring_size`, `substructure_violations`, `filter_phosphorus`, `FindAromaticRings` — import-clean, zero side effects, no data files |
| `utils/filter.py` | `apply_filters`, `legacy_apply_filters`, `passes_wehi_mcf`, `pains_filt`, `get_diversity`, `lipinski_filter` — needs cwd = repo root (caveat 1); uses the **present** `database/*` files |
| `utils/stoned_utils.py` | `mutate_selfie`, `get_mutated_SELFIES`, `get_fp_scores`, `get_fingerprint`, `randomize_smiles`, `sanitize_smiles` — the real STONED-SELFIES core |
| `utils/lipinski_utils.py` | `compute_lipinski`, `lipinski_filter`, `lipinski_hard_filter`, `compute_qed`, `compute_logp`, `draw_compounds` |
| `utils/mol_methods.py` | SMILES vocab/encode/decode/verify helpers |
| `models/priors/qcbm_qiskit.py` | `QCBMGenerator` (with explicit backend), `RandomCardinalityGenerator`, `ExactNLL` — runs on Aer |
| `models/{priors/error,error/error_mitigation}.py` | `ErrorMitigation` — constructs against an Aer backend |
| vendored `syba` | `SybaClassifier.predict` — load once, 28 s / 5.5 GB |

All of these require the **isolated-import** technique (synthetic namespace package for `utils` / `models` / `models.priors` / `models.error`) so the orquestra-importing `__init__.py` files never execute. That is the single most important structural constraint for the extraction stage.

---

### Artifacts produced

| Path | Contents |
|---|---|
| `.venv/` | project interpreter, CPython 3.10.18, 153 packages, 7.3 GB |
| `requirements.lock` | 153 exact pins, rebuild-verified |
| `vendor/syba/` | real `lich-uct/syba` @ `30929eb…`, LFS resources materialised, 271 MB |
| `reports/environment-requirements.txt` | raw `uv pip freeze` |
| `reports/python-version.txt` | `Python 3.10.18` |
| `reports/environment-manager_results.md` | this file |

No file under `repo/quantum-generative-models` was modified. Import probing created `__pycache__/` bytecode directories inside the repo tree; these were removed afterwards, and `find repo/ -type f -newermt <session start>` returns nothing (only a few directory mtimes changed).
