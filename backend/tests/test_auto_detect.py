"""Deterministic detection on synthetic inputs."""
from __future__ import annotations

from pathlib import Path

from app import auto


def test_ct_volume(ct_volume):
    d = auto.detect(str(ct_volume))
    assert d.kind == "ct_volume" and d.modality_guess == "CT"
    assert d.details["frac_below_-500"] > 0.1
    assert d.details["size_xyz"] == [48, 48, 24]


def test_mri_volume(mri_volume):
    d = auto.detect(str(mri_volume))
    assert d.kind == "mri_volume" and d.modality_guess == "MRI"
    assert "reference_mask" not in d.details


def test_mri_with_sibling_reference_mask(mri_with_mask):
    vol, ref = mri_with_mask
    d = auto.detect(str(vol))
    assert d.kind == "mri_volume"
    assert d.details["reference_mask"] == str(ref)
    assert any("reference brain mask" in n for n in d.notes)


def test_microscopy_png(microscopy_png):
    d = auto.detect(str(microscopy_png))
    assert d.kind == "microscopy_2d"
    assert d.details["n_blobs"] >= 20 and d.details["largest_component_frac"] < 0.6
    assert d.details["width"] == 256 and d.details["channels"] == 3


def test_medical_png(medical_png):
    d = auto.detect(str(medical_png))
    assert d.kind == "medical_2d"
    assert d.details["largest_component_frac"] > 0.6


def test_filename_hints_override(tmp_path, monkeypatch):
    from tests.conftest import blob_image, write_png
    p = write_png(tmp_path / "chest_xray_cxr.png", blob_image())
    assert auto.detect(str(p)).kind == "medical_2d"
    p2 = write_png(tmp_path / "nuclei_dapi.png", __import__("tests.conftest", fromlist=["gradient_image"]).gradient_image())
    assert auto.detect(str(p2)).kind == "microscopy_2d"


def test_medsam_npz(medsam_npz):
    d = auto.detect(str(medsam_npz))
    assert d.kind == "medsam_npz" and d.details["has_boxes"] and d.details["has_gts"]
    assert d.modality_guess == "X-ray"


def test_frames_folder(frames_dir):
    d = auto.detect(str(frames_dir))
    assert d.kind == "frames_folder" and d.details["n_frames"] == 12
    assert d.details["per_image_kind"] == "medical_2d"


def test_image_folder(image_folder):
    d = auto.detect(str(image_folder))
    assert d.kind == "image_folder" and d.details["n_images"] == 25
    assert d.details["per_image_kind"] == "microscopy_2d"
    assert len(d.details["votes"]) == 5


def test_msd_task(msd_task):
    d = auto.detect(str(msd_task))
    assert d.kind == "msd_task" and d.modality_guess == "MRI"
    assert d.details["n_imagesTr"] == 3 and d.details["n_imagesTs"] == 1 and d.details["has_imagesTs"]


def test_nnunet_dataset(nnunet_dataset):
    d = auto.detect(str(nnunet_dataset))
    assert d.kind == "nnunet_dataset" and d.modality_guess == "MRI"


def test_dicom_series(tmp_path):
    d = tmp_path / "series"
    d.mkdir()
    for i in range(3):
        (d / f"IM{i}").write_bytes(b"\0" * 128 + b"DICM" + b"\0" * 64)
    assert auto.detect(str(d)).kind == "dicom_series"


def test_medmnist_flag():
    d = auto.detect("pathmnist")
    assert d.kind == "medmnist_flag" and d.details["flag"] == "pathmnist" and d.details["is_2d"]
    assert auto.detect("OrganMNIST3D").details["is_2d"] is False


def test_unknown(tmp_path):
    p = tmp_path / "notes.docx"
    p.write_bytes(b"xx")
    assert auto.detect(str(p)).kind == "unknown"
    assert auto.detect(str(tmp_path / "missing.png")).kind == "unknown"


def test_video_stack_routes_to_frames(frames_dir):
    """<stem>_frames.nii.gz next to a <stem>_frames folder is analysed as the frame folder."""
    import numpy as np
    from tests.conftest import write_nifti
    nii = write_nifti(frames_dir.parent / "clip_frames.nii.gz", np.zeros((12, 120, 160), dtype=np.uint8))
    d = auto.detect(str(nii))
    assert d.kind == "frames_folder" and d.input_path == str(frames_dir)


def test_classify_volume_rules():
    assert auto.classify_volume({"frac_below_-500": 0.2, "min": -1024, "max": 1500, "dtype": "float32"}, "x.nii.gz")[0] == "ct_volume"
    assert auto.classify_volume({"frac_below_-500": 0.0, "min": 0, "max": 900, "dtype": "int16"}, "sub_T1w.nii.gz")[0] == "mri_volume"
    assert auto.classify_volume({"frac_below_-500": 0.0, "min": -200, "max": 400, "dtype": "float32"}, "abdomen_ct_0000.nii.gz")[0] == "ct_volume"


def test_llm_refine_disabled_by_default(monkeypatch, medical_png):
    monkeypatch.delenv("AUTO_LLM_REFINE", raising=False)
    d = auto.detect(str(medical_png))
    assert auto.refine_with_llm(d) is d and not any("LLM" in n for n in d.notes)
