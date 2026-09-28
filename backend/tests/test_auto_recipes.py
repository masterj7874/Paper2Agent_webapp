"""Recipes bind only to real tools/parameters (schema snapshot of the live Studio) and chain through references."""
from __future__ import annotations

import re

import pytest

from app import auto

ALL_KIND_FIXTURES = ["ct_volume", "mri_volume", "mri_with_mask", "microscopy_png", "medical_png", "medsam_npz", "frames_dir", "image_folder", "msd_task", "nnunet_dataset"]


def _detect(request, name):
    v = request.getfixturevalue(name)
    if isinstance(v, tuple):
        v = v[0]
    return auto.detect(str(v))


@pytest.mark.parametrize("fixture", ALL_KIND_FIXTURES)
def test_every_step_binds_to_a_real_tool(request, fixture, tool_schemas):
    det = _detect(request, fixture)
    recipes = auto.build_recipes(det)
    assert recipes, f"no recipe for {det.kind}"
    problems = auto.validate_recipes(recipes, tool_schemas)
    assert problems == [], problems
    for r in recipes:
        assert r.steps[-1].agent == "MedKG" and r.steps[-1].tool == "medkg_related_work" and r.steps[-1].optional
        for s in r.steps:
            if s.agent != "auto":
                assert s.tool in tool_schemas[s.agent]
            else:
                assert s.tool in auto.INTERNAL


def test_medmnist_recipes_bind(tool_schemas):
    for flag in ("pathmnist", "organmnist3d"):
        recipes = auto.build_recipes(auto.detect(flag))
        assert auto.validate_recipes(recipes, tool_schemas) == []
    r = auto.build_recipes(auto.detect("pathmnist"))[0]
    assert [s.tool for s in r.steps] == ["medmnist_download_dataset", "medmnist_train_baseline", "medmnist_evaluate_predictions", "medkg_related_work"]
    assert r.steps[1].arguments["epochs"] == 2


def test_dicom_recipe_is_internal_then_volume(tmp_path, tool_schemas):
    d = tmp_path / "series"
    d.mkdir()
    (d / "a.dcm").write_bytes(b"\0" * 132)
    recipes = auto.build_recipes(auto.detect(str(d)))
    assert [s.tool for s in recipes[0].steps] == ["auto_dicom_to_nifti", "auto_plan_volume"]


def test_references_are_well_formed(request, tool_schemas):
    ref = re.compile(r"\$\{(input|run_dir|step\[\d+\]\.(artifacts\[.+\]|result\.[\w.]+|job_id|output_dir))\}")
    for fixture in ALL_KIND_FIXTURES:
        for r in auto.build_recipes(_detect(request, fixture)):
            for i, s in enumerate(r.steps):
                for m in auto._REF.finditer(__import__("json").dumps(s.arguments)):
                    assert ref.fullmatch("${" + m.group(1) + "}"), f"{r.id}[{i}] bad reference {m.group(0)}"
                    sm = re.search(r"step\[(\d+)\]", m.group(1))
                    if sm:
                        assert int(sm.group(1)) < i, f"{r.id}[{i}] references a later/same step"


def test_mri_recipe_adds_evaluation_when_reference_mask_exists(mri_with_mask, mri_volume):
    with_ref = auto.build_recipes(auto.detect(str(mri_with_mask[0])))[0]
    without = auto.build_recipes(auto.detect(str(mri_volume)))[0]
    assert [s.tool for s in with_ref.steps] == ["hdbet_extract_brain", "hdbet_inspect_brain_mask", "hdbet_evaluate_brain_mask", "medkg_related_work"]
    assert [s.tool for s in without.steps] == ["hdbet_extract_brain", "hdbet_inspect_brain_mask", "medkg_related_work"]
    assert with_ref.steps[2].arguments["reference_path"] == str(mri_with_mask[1])
    assert with_ref.steps[1].arguments["mask_path"].startswith("${step[0].artifacts[")


def test_ct_recipe_chains_npz(ct_volume):
    r = auto.build_recipes(auto.detect(str(ct_volume)))[0]
    assert [s.tool for s in r.steps] == ["medsam_preprocess_ct_mr", "medsam_segment_with_text", "medkg_related_work"]
    assert r.steps[0].arguments["modality"] == "CT"
    assert r.steps[1].arguments["image_path"] == "${step[0].artifacts[\\.npz$]}"
    assert "liver" in r.steps[1].arguments["prompts"]


def test_microscopy_recipe(microscopy_png):
    r = auto.build_recipes(auto.detect(str(microscopy_png)))[0]
    assert [s.tool for s in r.steps] == ["cellpose_estimate_diameter", "cellpose_segment_image", "cellpose_masks_to_rois", "medkg_related_work"]
    assert r.steps[1].arguments["diameter"] == "${step[0].result.estimated_diameter}"
    assert r.steps[2].arguments["masks_path"] == "${step[1].artifacts[_seg\\.npy$]}"


def test_centred_box_80_percent(medical_png):
    assert auto.centred_box(320, 240) == [32, 24, 288, 216]
    assert auto.centred_box(512, 512, 0.5) == [128, 128, 384, 384]
    r = auto.build_recipes(auto.detect(str(medical_png)))[0]
    assert r.steps[0].tool == "medsam_segment_with_box" and r.steps[0].arguments["boxes"] == [[32, 24, 288, 216]]


def test_video_frames_recipe(frames_dir):
    det = auto.detect(str(frames_dir))
    r = auto.build_recipes(det)[0]
    per_frame = [s for s in r.steps if s.tool == "medsam_segment_with_box"]
    assert len(per_frame) == auto.N_VIDEO_FRAMES
    names = [s.arguments["image_path"].split("/")[-1] for s in per_frame]
    assert names == ["frame_00001.png", "frame_00004.png", "frame_00007.png", "frame_00009.png", "frame_00012.png"]  # evenly spaced over 12
    assert per_frame[0].arguments["boxes"] == [[16, 12, 144, 108]]
    table = r.steps[len(per_frame)]
    assert table.agent == "auto" and table.tool == "auto_frames_table" and table.arguments["steps"] == list(range(5))
    alt = auto.build_recipes(det)[1]
    assert alt.id == "video_frames_cellpose" and sum(1 for s in alt.steps if s.tool == "cellpose_segment_image") == 5


def test_image_folder_cap(image_folder):
    r = auto.build_recipes(auto.detect(str(image_folder)))[0]
    assert r.id == "image_folder_cellpose"
    assert sum(1 for s in r.steps if s.tool == "cellpose_segment_image") == auto.IMAGE_FOLDER_CAP == 20


def test_msd_recipe_private_tree_and_trainer(msd_task):
    r = auto.build_recipes(auto.detect(str(msd_task)))[0]
    tools = [s.tool for s in r.steps]
    assert tools == ["auto_prepare_nnunet_tree", "nnunet_convert_msd_dataset", "nnunet_verify_dataset_integrity", "nnunet_plan_and_preprocess", "nnunet_train_model",
                     "nnunet_predict", "nnunet_find_best_configuration", "medkg_related_work"]
    for s in r.steps[1:7]:
        for k in ("nnunet_raw", "nnunet_preprocessed", "nnunet_results"):
            if k in s.arguments:
                assert s.arguments[k].startswith("${run_dir}/nnunet/"), (s.tool, k)
        assert "nnunet_raw" in s.arguments
    train = r.steps[4]
    assert train.arguments["trainer"] == "nnUNetTrainer_5epochs" and train.arguments["configuration"] == "2d" and train.arguments["fold"] == 0 and train.arguments["device"] == "auto"
    assert r.steps[3].arguments["configurations"] == ["2d", "3d_fullres"]
    assert r.steps[5].arguments["input_path"] == "${step[1].result.dataset_folder}/imagesTs"
    assert r.steps[6].arguments["trainers"] == ["nnUNetTrainer_5epochs"]


def test_nnunet_dataset_recipe_starts_at_verify(nnunet_dataset):
    r = auto.build_recipes(auto.detect(str(nnunet_dataset)))[0]
    assert [s.tool for s in r.steps[:3]] == ["auto_prepare_nnunet_tree", "nnunet_verify_dataset_integrity", "nnunet_plan_and_preprocess"]
    assert r.steps[0].arguments["dataset_folder"] == "${input}"
    assert r.steps[1].arguments["dataset"] == "${step[0].result.dataset_name}"


def test_plan_reports_binding_problems(medical_png, tool_schemas):
    broken = {k: dict(v) for k, v in tool_schemas.items()}
    broken["MedSAM"] = {k: v for k, v in broken["MedSAM"].items() if k != "medsam_segment_with_box"}
    p = auto.plan(str(medical_png), broken)
    assert any("unknown tool MedSAM.medsam_segment_with_box" in n for n in p["notes"])
    ok = auto.plan(str(medical_png), tool_schemas)
    assert ok["kind"] == "medical_2d" and ok["n_recipes"] == 2 and not any("unknown tool" in n for n in ok["notes"])
