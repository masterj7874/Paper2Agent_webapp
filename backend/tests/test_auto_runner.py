"""Reference resolution + chained execution with a fake job runner (no MCP servers)."""
from __future__ import annotations

import asyncio
import csv
import json
from pathlib import Path

import pytest

from app import auto


# ---------------------------------------------------------------- references
def _ctx(tmp_path):
    return {"input": "/in/x.nii.gz", "run_dir": str(tmp_path),
            "steps": [{"status": "done", "job_id": "j0", "result": {"estimated_diameter": 27.8, "output_dir": "/o", "nested": {"a": [1, 2]}},
                       "artifacts": [{"description": "binary brain mask", "path": "/o/case_bet.nii.gz"}, {"description": "overlay", "path": "/o/case_overlay.png"}]},
                      {"status": "error", "job_id": "j1", "result": None, "artifacts": []}]}


def test_resolve_references(tmp_path):
    ctx = _ctx(tmp_path)
    assert auto.resolve_value("${input}", ctx) == "/in/x.nii.gz"
    assert auto.resolve_value("${run_dir}/outputs", ctx) == str(tmp_path) + "/outputs"
    assert auto.resolve_value("${step[0].artifacts[_bet\\.nii(\\.gz)?$]}", ctx) == "/o/case_bet.nii.gz"
    assert auto.resolve_value("${step[0].artifacts[overlay]}", ctx) == "/o/case_overlay.png"   # description match
    assert auto.resolve_value("${step[0].result.estimated_diameter}", ctx) == 27.8            # typed
    assert auto.resolve_value("${step[0].result.nested.a.1}", ctx) == 2
    assert auto.resolve_value("${step[0].job_id}", ctx) == "j0"
    assert auto.resolve_value("${step[0].output_dir}", ctx) == "/o"
    assert auto.resolve_value("${step[0].result.output_dir}/imagesTs", ctx) == "/o/imagesTs"
    assert auto.resolve_value([{"x": "${input}"}, 3], ctx) == [{"x": "/in/x.nii.gz"}, 3]
    assert auto.resolve_arguments({"a": None, "b": "${input}"}, ctx) == {"b": "/in/x.nii.gz"}


@pytest.mark.parametrize("expr", ["${step[1].artifacts[x]}", "${step[5].result.a}", "${step[0].artifacts[nomatch]}", "${step[0].result.missing}", "${bogus}"])
def test_bad_references_raise(tmp_path, expr):
    with pytest.raises(auto.RefError):
        auto.resolve_value(expr, _ctx(tmp_path))


def test_key_numbers():
    kn = auto.key_numbers({"message": "m", "artifacts": [], "n_masks": 99, "diameter_used": 27.80029, "device": "cuda:1", "settings": {"x": 1},
                           "validation": {"foreground_mean_dice": 0.87, "per_label": {"1": 0.9}}, "output_dir": "/o", "long": "x" * 80})
    assert kn["n_masks"] == 99 and kn["diameter_used"] == 27.80029 and kn["device"] == "cuda:1"
    assert kn["validation.foreground_mean_dice"] == 0.87 and kn["validation.per_label.1"] == 0.9
    assert "settings" not in kn and "output_dir" not in kn and "long" not in kn
    assert list(kn)[0] == "n_masks"  # preferred keys first


# ---------------------------------------------------------------- fake Studio runner
class FakeJob:
    def __init__(self, id_, agent, tool, args):
        self.id, self.agent, self.tool, self.arguments = id_, agent, tool, args
        self.status, self.result, self.error = "queued", None, None


class FakeRunner:
    """Returns canned results per tool after a short delay; records every submission (with resolved arguments)."""

    def __init__(self, tmp_path: Path, fail: set[str] | None = None):
        self.tmp, self.fail, self.calls = tmp_path, fail or set(), []
        self.n = 0

    def submit(self, agent, tool, args):
        self.n += 1
        job = FakeJob(f"job{self.n}", agent, tool, args)
        self.calls.append((agent, tool, args))
        asyncio.get_event_loop().create_task(self._run(job))
        return job

    async def _run(self, job):
        job.status = "running"
        await asyncio.sleep(0.01)
        if job.tool in self.fail:
            job.status, job.error, job.result = "error", f"{job.tool} exploded", {"hint": "try again"}
            return
        job.result = self.canned(job)
        job.status = "done"

    def canned(self, job):
        out = self.tmp / "out" / job.tool
        out.mkdir(parents=True, exist_ok=True)
        t = job.tool
        if t == "cellpose_estimate_diameter":
            return {"message": "ok", "estimated_diameter": 27.8, "artifacts": []}
        if t == "cellpose_segment_image":
            seg = out / "img_seg.npy"; seg.write_bytes(b"0")
            ov = out / "img_outlines.png"; ov.write_bytes(b"\x89PNG")
            return {"message": "ok", "n_masks": 42, "diameter_used": job.arguments.get("diameter"), "artifacts": [{"description": "GUI-loadable segmentation", "path": str(seg)}, {"description": "image with red mask outlines", "path": str(ov)}]}
        if t == "cellpose_masks_to_rois":
            return {"message": "ok", "n_objects": 42, "artifacts": [{"description": "rois", "path": str(out / "rois.zip")}]}
        if t == "hdbet_extract_brain":
            m = out / "case_bet.nii.gz"; m.write_bytes(b"0")
            return {"message": "ok", "n_cases": 1, "artifacts": [{"description": "case: binary brain mask", "path": str(m)}, {"description": "overlay", "path": str(out / "case_overlay.png")}]}
        if t == "hdbet_inspect_brain_mask":
            return {"message": "ok", "statistics": {"volume_ml": 1400.5, "n_components": 1}, "artifacts": [{"description": "mask statistics JSON", "path": str(out / "stats.json")}]}
        if t == "medsam_segment_with_box":
            ov = out / f"overlay_{self.n}.png"; ov.write_bytes(b"\x89PNG")
            return {"message": "ok", "total_foreground_pixels": 1000 + self.n, "n_boxes": 1, "artifacts": [{"description": "Overlay figure", "path": str(ov)}]}
        if t == "medkg_related_work":
            return {"message": "ok", "summary": {"n_rows": 10, "n_q1": 7}, "rows": [{"title": "x"}], "artifacts": [{"description": "markdown", "path": str(out / "rw.md")}]}
        return {"message": "ok", "artifacts": []}


def _tools_lookup(schemas):
    return lambda agent: schemas.get(agent)


async def _run_and_wait(svc, path, recipe_id=None):
    run = svc.start(path, recipe_id)
    task = svc.tasks[run["id"]]
    await asyncio.wait_for(task, 20)
    return svc.get(run["id"])


def test_microscopy_chain_resolves_references(tmp_path, microscopy_png, tool_schemas):
    fake = FakeRunner(tmp_path)
    svc = auto.AutoService(fake, tmp_path / "auto_runs", _tools_lookup(tool_schemas), poll_s=0.01)
    run = asyncio.run(_run_and_wait(svc, str(microscopy_png)))
    assert run["status"] == "done", run["warnings"]
    assert [s["status"] for s in run["steps"]] == ["done"] * 4
    seg_args = fake.calls[1][2]
    assert seg_args["diameter"] == 27.8 and seg_args["image_path"] == str(microscopy_png)
    assert seg_args["output_dir"] == str(tmp_path / "auto_runs" / run["id"] / "outputs")
    assert fake.calls[2][2]["masks_path"].endswith("img_seg.npy")
    assert run["steps"][1]["key_numbers"]["n_masks"] == 42
    assert run["jobs"] == ["job1", "job2", "job3", "job4"]
    run_dir = Path(run["run_dir"])
    summary = json.loads((run_dir / "summary.json").read_text())
    assert summary["status"] == "done" and summary["kind"] == "microscopy_2d" and len(summary["steps"]) == 4
    assert summary["steps"][1]["key_numbers"]["n_masks"] == 42
    report = (run_dir / "report.md").read_text()
    assert "hdbet" not in report and "cellpose_segment_image" in report and "n_masks=42" in report and "## Artifacts" in report
    assert (run_dir / "run.json").exists()
    assert {a["description"] for a in run["artifacts"]} >= {"run summary (JSON)", "run report (markdown)"}


def test_required_failure_stops_chain(tmp_path, mri_with_mask, tool_schemas):
    fake = FakeRunner(tmp_path, fail={"hdbet_extract_brain"})
    svc = auto.AutoService(fake, tmp_path / "auto_runs", _tools_lookup(tool_schemas), poll_s=0.01)
    run = asyncio.run(_run_and_wait(svc, str(mri_with_mask[0])))
    assert run["status"] == "error"
    assert [s["status"] for s in run["steps"]] == ["error", "skipped", "skipped", "skipped"]
    assert "exploded" in run["steps"][0]["error"] and run["steps"][0]["hint"] == "try again"
    assert len(fake.calls) == 1
    assert "error" in (Path(run["run_dir"]) / "report.md").read_text()


def test_optional_medkg_failure_gives_partial(tmp_path, medical_png, tool_schemas):
    fake = FakeRunner(tmp_path, fail={"medkg_related_work"})
    svc = auto.AutoService(fake, tmp_path / "auto_runs", _tools_lookup(tool_schemas), poll_s=0.01)
    run = asyncio.run(_run_and_wait(svc, str(medical_png)))
    assert run["status"] == "partial"
    assert [s["status"] for s in run["steps"]] == ["done", "error"]
    assert any("optional step" in w for w in run["warnings"])


def test_unavailable_tool_is_an_error(tmp_path, medical_png, tool_schemas):
    schemas = {k: v for k, v in tool_schemas.items() if k != "MedSAM"}
    svc = auto.AutoService(FakeRunner(tmp_path), tmp_path / "auto_runs", _tools_lookup(schemas), poll_s=0.01)
    run = asyncio.run(_run_and_wait(svc, str(medical_png)))
    assert run["status"] == "error" and "not available" in run["steps"][0]["error"]


def test_video_frames_chain_writes_csv_and_gallery(tmp_path, frames_dir, tool_schemas):
    fake = FakeRunner(tmp_path)
    svc = auto.AutoService(fake, tmp_path / "auto_runs", _tools_lookup(tool_schemas), poll_s=0.01)
    run = asyncio.run(_run_and_wait(svc, str(frames_dir)))
    assert run["status"] == "done", run["warnings"]
    tools = [s["tool"] for s in run["steps"]]
    assert tools == ["medsam_segment_with_box"] * 5 + ["auto_frames_table", "medkg_related_work"]
    table = run["steps"][5]
    csv_path = next(a["path"] for a in table["artifacts"] if a["path"].endswith("frames.csv"))
    rows = list(csv.DictReader(open(csv_path)))
    assert len(rows) == 5 and rows[0]["frame"] == "frame_00001.png" and rows[0]["status"] == "done" and int(rows[0]["foreground_pixels"]) == 1001
    assert all(Path(r["overlay"]).exists() for r in rows)
    assert table["key_numbers"]["n_done"] == 5 and table["key_numbers"]["metric"] == "foreground_pixels"
    assert any(a["path"].endswith("frames.csv") for a in run["artifacts"])
    assert len([a for a in table["artifacts"] if a["path"].endswith(".png")]) == 5


def test_recipe_selection_and_listing(tmp_path, frames_dir, tool_schemas):
    fake = FakeRunner(tmp_path)
    svc = auto.AutoService(fake, tmp_path / "auto_runs", _tools_lookup(tool_schemas), poll_s=0.01)
    run = asyncio.run(_run_and_wait(svc, str(frames_dir), "video_frames_cellpose"))
    assert run["recipe"]["id"] == "video_frames_cellpose"
    assert [s["tool"] for s in run["steps"]][:5] == ["cellpose_segment_image"] * 5
    lst = svc.list()
    assert lst[0]["id"] == run["id"] and lst[0]["n_done"] == 7 and lst[0]["kind"] == "frames_folder"
    with pytest.raises(ValueError):
        svc.start(str(frames_dir), "does_not_exist")
    with pytest.raises(ValueError):
        svc.start(str(tmp_path / "nothing.xyz"))


def test_nnunet_tree_internal_step(tmp_path, nnunet_dataset):
    res = auto._internal_prepare_nnunet_tree({"run_dir": str(tmp_path / "r"), "dataset_folder": str(nnunet_dataset)}, {})
    assert Path(res["nnunet_raw"]).is_dir() and Path(res["nnunet_preprocessed"]).is_dir() and Path(res["nnunet_results"]).is_dir()
    assert res["dataset_name"] == "Dataset099_Toy" and Path(res["dataset_folder"]).is_symlink()
    assert (Path(res["dataset_folder"]) / "dataset.json").exists()


def test_reload_marks_interrupted_runs(tmp_path):
    d = tmp_path / "auto_runs" / "r1"
    d.mkdir(parents=True)
    (d / "run.json").write_text(json.dumps({"id": "r1", "status": "running", "created_at": 1, "steps": [{"index": 0, "status": "running", "agent": "a", "tool": "t"}], "path": "x"}))
    svc = auto.AutoService(FakeRunner(tmp_path), tmp_path / "auto_runs")
    r = svc.get("r1")
    assert r["status"] == "error" and r["steps"][0]["status"] == "error" and "restarted" in r["warnings"][0]
