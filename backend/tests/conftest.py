"""Shared fixtures: synthetic inputs (no real data, no MCP servers) + the tool-schema snapshot of the live Studio."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

FIXTURES = Path(__file__).parent / "fixtures"

# Importing the application must never recover or connect a real user's runs.
_APP_TEST_DIRECTORY = tempfile.TemporaryDirectory(prefix='p2a-test-state-')
for _key, _subdir in {
    'PAPER2AGENT_PAPER_DIR': 'papers', 'PAPER2AGENT_REGISTRY': 'agents.json',
    'PAPER2AGENT_CLAUDE_JSON': 'no-claude.json', 'PAPER2AGENT_JOB_DIR': 'jobs',
    'PAPER2AGENT_UPLOAD_DIR': 'uploads', 'PAPER2AGENT_AUTO_DIR': 'auto',
    'PAPER2AGENT_ALLOWED_ROOTS': 'allowed',
    'PAPER2AGENT_MANUSCRIPT_DIR': 'manuscripts', 'PAPER2AGENT_RESEARCH_DIR': 'research',
    'PAPER2AGENT_RESEARCH_ROOTS': 'research-roots', 'PAPER2AGENT_CORPUS_DB': 'no-corpus.sqlite',
    'PAPER2AGENT_PAPER_PLATFORM': 'no-platform',
}.items():
    os.environ[_key] = str(Path(_APP_TEST_DIRECTORY.name) / _subdir)


@pytest.fixture(scope="session")
def tool_schemas() -> dict[str, dict[str, dict]]:
    return json.loads((FIXTURES / "tool_schemas.json").read_text())


def write_nifti(path: Path, arr: np.ndarray, spacing=(1.0, 1.0, 1.0)) -> Path:
    import SimpleITK as sitk
    img = sitk.GetImageFromArray(arr)
    img.SetSpacing(spacing)
    sitk.WriteImage(img, str(path))
    return path


def write_png(path: Path, arr: np.ndarray) -> Path:
    from PIL import Image
    Image.fromarray(arr).save(str(path))
    return path


def blob_image(w=256, h=256, n=60, r=6, seed=0, rgb=False) -> np.ndarray:
    """Many small bright discs on a dark background (fluorescence-like)."""
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w), dtype=np.uint8)
    yy, xx = np.mgrid[:h, :w]
    for _ in range(n):
        cx, cy = rng.integers(r, w - r), rng.integers(r, h - r)
        img[(xx - cx) ** 2 + (yy - cy) ** 2 <= r * r] = 200
    if rgb:
        out = np.zeros((h, w, 3), dtype=np.uint8)
        out[..., 1] = img
        return out
    return img


def gradient_image(w=320, h=240) -> np.ndarray:
    """Smooth gradient with one big bright ellipse: nothing cell-like (generic 2-D medical image)."""
    yy, xx = np.mgrid[:h, :w]
    img = (60 + 80 * xx / w).astype(np.uint8)
    img[((xx - w / 2) / (w * 0.3)) ** 2 + ((yy - h / 2) / (h * 0.3)) ** 2 <= 1] = 220
    return img


@pytest.fixture
def ct_volume(tmp_path) -> Path:
    rng = np.random.default_rng(0)
    arr = rng.normal(40, 30, size=(24, 48, 48)).astype(np.float32)
    arr[:, :8, :] = -1000.0  # air
    arr[:, -8:, :] = -1000.0
    return write_nifti(tmp_path / "abdomen_ct.nii.gz", arr, (0.8, 0.8, 2.5))


@pytest.fixture
def mri_volume(tmp_path) -> Path:
    rng = np.random.default_rng(1)
    arr = np.clip(rng.normal(300, 80, size=(30, 40, 40)), 0, None).astype(np.int16)
    return write_nifti(tmp_path / "sub-01_T1w.nii.gz", arr, (2.0, 2.0, 2.0))


@pytest.fixture
def mri_with_mask(tmp_path) -> tuple[Path, Path]:
    rng = np.random.default_rng(2)
    arr = np.clip(rng.normal(300, 80, size=(30, 40, 40)), 0, None).astype(np.int16)
    vol = write_nifti(tmp_path / "tpl-Test_res-02_T1w.nii.gz", arr, (2.0, 2.0, 2.0))
    mask = np.zeros_like(arr, dtype=np.uint8)
    mask[5:25, 8:32, 8:32] = 1
    ref = write_nifti(tmp_path / "tpl-Test_res-02_desc-brain_mask.nii.gz", mask, (2.0, 2.0, 2.0))
    return vol, ref


@pytest.fixture
def microscopy_png(tmp_path) -> Path:
    return write_png(tmp_path / "sample_a.png", blob_image(rgb=True))


@pytest.fixture
def medical_png(tmp_path) -> Path:
    return write_png(tmp_path / "slice_a.png", gradient_image())


@pytest.fixture
def frames_dir(tmp_path) -> Path:
    d = tmp_path / "clip_frames"
    d.mkdir()
    for i in range(1, 13):
        write_png(d / f"frame_{i:05d}.png", gradient_image(160, 120))
    return d


@pytest.fixture
def image_folder(tmp_path) -> Path:
    d = tmp_path / "cells"
    d.mkdir()
    for i in range(25):
        write_png(d / f"img{i:02d}.png", blob_image(seed=i))
    return d


@pytest.fixture
def msd_task(tmp_path) -> Path:
    d = tmp_path / "Task99_Toy"
    for sub in ("imagesTr", "labelsTr", "imagesTs"):
        (d / sub).mkdir(parents=True)
    for i in range(3):
        write_nifti(d / "imagesTr" / f"toy_{i:03d}.nii.gz", np.random.default_rng(i).normal(100, 10, (8, 16, 16)).astype(np.float32))
        write_nifti(d / "labelsTr" / f"toy_{i:03d}.nii.gz", (np.random.default_rng(i).random((8, 16, 16)) > 0.7).astype(np.uint8))
    write_nifti(d / "imagesTs" / "toy_100.nii.gz", np.zeros((8, 16, 16), dtype=np.float32))
    (d / "dataset.json").write_text(json.dumps({"name": "Toy", "modality": {"0": "MRI"}, "labels": {"0": "background", "1": "thing"}, "numTraining": 3, "numTest": 1,
                                                "training": [{"image": f"./imagesTr/toy_{i:03d}.nii.gz", "label": f"./labelsTr/toy_{i:03d}.nii.gz"} for i in range(3)], "test": ["./imagesTs/toy_100.nii.gz"]}))
    return d


@pytest.fixture
def nnunet_dataset(tmp_path) -> Path:
    d = tmp_path / "Dataset099_Toy"
    for sub in ("imagesTr", "labelsTr"):
        (d / sub).mkdir(parents=True)
    write_nifti(d / "imagesTr" / "toy_000_0000.nii.gz", np.zeros((8, 16, 16), dtype=np.float32))
    write_nifti(d / "labelsTr" / "toy_000.nii.gz", np.zeros((8, 16, 16), dtype=np.uint8))
    (d / "dataset.json").write_text(json.dumps({"channel_names": {"0": "MRI"}, "labels": {"background": 0, "thing": 1}, "numTraining": 1, "file_ending": ".nii.gz"}))
    return d


@pytest.fixture
def medsam_npz(tmp_path) -> Path:
    p = tmp_path / "2DBox_CXR_demo.npz"
    np.savez(p, imgs=np.zeros((256, 256, 3), dtype=np.uint8), boxes=np.array([[10, 10, 100, 100]]), gts=np.zeros((256, 256), dtype=np.uint8))
    return p
