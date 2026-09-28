"""Auto-analysis: deterministic input detection -> recipe (a chain of Studio jobs) -> chained run with artifact
references between steps -> summary.json + report.md per run under data/auto_runs/<run_id>/.

Detection is deterministic (extension + header sniffing):
  * NIfTI/NRRD/MHA volumes: dims/dtype/intensity range -> CT (HU < -500 present) vs MRI
  * PNG/JPG/TIF/BMP: size/channels + a blob heuristic -> microscopy (many small bright objects) vs generic medical 2-D
  * .npz with an 'imgs' key -> MedSAM demo npz
  * video (ffprobe) -> the PNG frame folder made at upload time (or made here with ffmpeg)
  * folders: MSD TaskXX_Name (dataset.json + imagesTr/labelsTr), nnU-Net DatasetXXX_Name (v2 dataset.json), DICOM
    series, folder of video frames (frame_*.png), folder of 2-D images
  * a bare MedMNIST flag such as "pathmnist"
An optional LLM refinement step exists but is disabled by default (env AUTO_LLM_REFINE=1) and can only change the
modality guess / notes, never the tool bindings.

Recipes bind only to tool names/parameters that exist on the live MCP servers (tests/fixtures/tool_schemas.json is a
snapshot of GET /api/agents/{name}/tools). Step arguments may reference earlier steps; references are resolved just
before a step is submitted and an unresolvable reference fails the step:
    ${input}                          the (converted) input path
    ${run_dir}                        this run's folder (data/auto_runs/<run_id>)
    ${step[0].artifacts[<regex>]}     path of the first artifact of step 0 whose path or description matches <regex>
    ${step[0].result.a.b}             dotted lookup in step 0's result JSON (typed value when the whole string is one ref)
    ${step[0].job_id}                 Studio job id of step 0
Steps with agent "auto" run in-process (folder preparation, per-frame CSV, DICOM/video conversion); every other step is
an ordinary Studio job (POST /api/jobs semantics) so it shows up in the job history too.
"""
from __future__ import annotations

import asyncio
import csv
import json
import logging
import os
import re
import shutil
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

log = logging.getLogger("paper2agent.web.auto")

# --------------------------------------------------------------------------------------------------------------------
# constants
# --------------------------------------------------------------------------------------------------------------------
VOLUME_EXT = (".nii.gz", ".nii", ".nrrd", ".mha", ".mhd", ".nii.gz")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp")
VIDEO_EXT = (".avi", ".mp4", ".mov", ".mkv", ".wmv", ".mpg", ".mpeg", ".m4v", ".webm")
DICOM_EXT = (".dcm", ".dicom", ".ima")
MEDMNIST_FLAGS = ("pathmnist", "chestmnist", "dermamnist", "octmnist", "pneumoniamnist", "retinamnist", "breastmnist",
                  "bloodmnist", "tissuemnist", "organamnist", "organcmnist", "organsmnist", "organmnist3d",
                  "nodulemnist3d", "adrenalmnist3d", "fracturemnist3d", "vesselmnist3d", "synapsemnist3d")
MEDMNIST_2D = MEDMNIST_FLAGS[:12]
KINDS = ("mri_volume", "ct_volume", "microscopy_2d", "medical_2d", "medsam_npz", "video", "frames_folder", "image_folder",
         "msd_task", "nnunet_dataset", "dicom_series", "medmnist_flag", "unknown")
N_VIDEO_FRAMES = 5
IMAGE_FOLDER_CAP = 20
FLARE_ORGANS = ["liver", "spleen", "left kidney", "right kidney", "pancreas", "aorta", "stomach", "gallbladder"]

_CT_HINT = re.compile(r"(^|[_\-./ ])(ct|flare|abdomen|abd|lung|chest_ct|kidney)([_\-./ ]|$)", re.I)
_MR_HINT = re.compile(r"(t1w?|t2w?|flair|mri|_mr|mprage|brain|mni|head|hippocampus|bet)", re.I)
_MICRO_HINT = re.compile(r"(cell|nuclei|nucleus|cyto|fluor|microscop|dapi|gfp|phase|tissuenet|livecell|cellpose)", re.I)
_MEDICAL_HINT = re.compile(r"(ct|mri|xray|x-ray|cxr|chest|slice|scan|frame|endoscop|dermoscop|derm|fundus|oct|ultrasound|us_|mammo|medsam)", re.I)
_REF = re.compile(r"\$\{([^}]*)\}")


def _lower_ext(p: Path) -> str:
    n = p.name.lower()
    if n.endswith(".nii.gz"):
        return ".nii.gz"
    return p.suffix.lower()


# --------------------------------------------------------------------------------------------------------------------
# detection
# --------------------------------------------------------------------------------------------------------------------
@dataclass
class Detection:
    path: str                       # what the user gave
    kind: str                       # one of KINDS
    modality_guess: str | None      # MRI | CT | microscopy | endoscopy | ... | None
    input_path: str                 # what the recipes operate on (converted frames folder, NIfTI, ...)
    details: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def sniff_volume(path: Path) -> dict[str, Any]:
    """Read a medical volume header + intensity statistics (SimpleITK; subsampled for big volumes)."""
    import numpy as np
    import SimpleITK as sitk
    img = sitk.ReadImage(str(path))
    arr = sitk.GetArrayFromImage(img)
    info: dict[str, Any] = {"size_xyz": list(img.GetSize()), "spacing_xyz": [round(float(s), 4) for s in img.GetSpacing()],
                            "dimension": int(img.GetDimension()), "pixel_type": img.GetPixelIDTypeAsString(),
                            "n_components": int(img.GetNumberOfComponentsPerPixel()), "dtype": str(arr.dtype)}
    if arr.ndim == 4:  # (T, Z, Y, X)
        info["n_volumes"] = int(arr.shape[0])
        arr = arr[0]
    step = max(1, int(round((arr.size / 4_000_000) ** (1 / 3)))) if arr.size > 4_000_000 else 1
    sub = arr[::step, ::step, ::step] if arr.ndim == 3 else arr[::step, ::step]
    subf = sub.astype(np.float32)
    subf = subf[np.isfinite(subf)]
    if subf.size == 0:
        subf = np.zeros(1, dtype=np.float32)
    p1, p50, p99 = (float(x) for x in np.percentile(subf, [1, 50, 99]))
    info.update({"min": float(subf.min()), "max": float(subf.max()), "mean": round(float(subf.mean()), 3), "p1": p1, "p50": p50, "p99": p99,
                 "frac_below_-500": round(float((subf < -500).mean()), 4), "frac_zero": round(float((subf == 0).mean()), 4),
                 "fov_mm": [round(float(s * sp), 1) for s, sp in zip(img.GetSize()[:3], img.GetSpacing()[:3])]})
    return info


def classify_volume(info: dict[str, Any], name: str = "") -> tuple[str, str, float]:
    """-> (kind, modality, confidence). CT when Hounsfield air (< -500 HU) is present; otherwise MRI."""
    ct_hint, mr_hint = bool(_CT_HINT.search(name)), bool(_MR_HINT.search(name))
    frac_air = info.get("frac_below_-500", 0.0)
    vmin, vmax = info.get("min", 0.0), info.get("max", 0.0)
    if frac_air >= 0.005 or (vmin <= -500 and vmax >= 200):
        return "ct_volume", "CT", 0.95 if not mr_hint else 0.7
    if ct_hint and not mr_hint and vmin < -100:
        return "ct_volume", "CT", 0.6
    if info.get("dtype", "").startswith("uint8") and vmax <= 255 and not mr_hint:
        # video stacks / already windowed data: not HU, treat as MRI-like non-quantitative volume
        return "mri_volume", "MRI" if mr_hint else "MRI?", 0.4
    return "mri_volume", "MRI", 0.85 if (mr_hint or vmin >= 0) else 0.6


def image_profile(path: Path) -> dict[str, Any]:
    """Size/channels + blob statistics on a <=512px grayscale copy (Otsu -> connected components)."""
    import numpy as np
    import SimpleITK as sitk
    from PIL import Image
    im = Image.open(str(path))
    im.load()
    w, h = im.size
    prof: dict[str, Any] = {"width": w, "height": h, "mode": im.mode, "n_frames": int(getattr(im, "n_frames", 1))}
    if im.mode in ("I;16", "I", "F"):
        a = np.asarray(im).astype(np.float32)
        a = 255 * (a - a.min()) / max(1e-9, float(a.max() - a.min()))
        gray = Image.fromarray(a.astype(np.uint8))
        prof["channels"] = 1
        prof["bit_depth"] = 16 if im.mode == "I;16" else 32
    else:
        rgb = im.convert("RGB")
        arr = np.asarray(rgb).astype(np.int16)
        spread = float(np.abs(arr[..., 0] - arr[..., 1]).mean() + np.abs(arr[..., 1] - arr[..., 2]).mean())
        prof["channels"] = 3 if im.mode in ("RGB", "RGBA", "P", "CMYK", "YCbCr") else 1
        prof["is_colour"] = spread > 4.0
        prof["channel_spread"] = round(spread, 2)
        gray = rgb.convert("L")
        prof["bit_depth"] = 8
    scale = max(w, h) / 512.0
    if scale > 1:
        gray = gray.resize((max(1, int(w / scale)), max(1, int(h / scale))))
    g = np.asarray(gray).astype(np.uint8)
    prof["mean_intensity"] = round(float(g.mean()), 2)
    prof["dark_background"] = bool(np.median(g) < 60)
    try:
        best = None
        for polarity, arr in (("bright", g), ("dark", (255 - g).astype(np.uint8))):
            sg = sitk.GetImageFromArray(arr)
            binary = sitk.OtsuThreshold(sg, 0, 1)
            cc = sitk.ConnectedComponent(binary)
            st = sitk.LabelShapeStatisticsImageFilter()
            st.Execute(cc)
            sizes = sorted((int(st.GetNumberOfPixels(l)) for l in st.GetLabels()), reverse=True)
            area = g.size
            fg = sum(sizes) or 1
            blobs = [s for s in sizes if 0.0002 * area <= s <= 0.05 * area]
            cand = {"polarity": polarity, "n_components": len(sizes), "n_blobs": len(blobs), "largest_component_frac": round(sizes[0] / fg, 3) if sizes else 0.0,
                    "foreground_frac": round(fg / area, 3)}
            score = cand["n_blobs"] * (1 - cand["largest_component_frac"])
            if best is None or score > best[0]:
                best = (score, cand)
        prof.update(best[1])  # objects can be bright on dark (fluorescence) or dark on bright (brightfield)
    except Exception as e:  # noqa: BLE001
        prof["blob_error"] = str(e)
    return prof


def classify_image(prof: dict[str, Any], name: str = "") -> tuple[str, str, float]:
    """-> (kind, modality, confidence): many small bright objects => microscopy, otherwise generic medical 2-D."""
    micro_hint, med_hint = bool(_MICRO_HINT.search(name)), bool(_MEDICAL_HINT.search(name))
    n_blobs, largest = prof.get("n_blobs", 0), prof.get("largest_component_frac", 1.0)
    blobby = n_blobs >= 20 and largest < 0.6
    if micro_hint and not med_hint:
        return "microscopy_2d", "microscopy", 0.9
    if med_hint and not micro_hint:
        return "medical_2d", _modality_from_name(name), 0.85
    if blobby:
        return "microscopy_2d", "microscopy", 0.8
    if n_blobs >= 12 and largest < 0.45:
        return "microscopy_2d", "microscopy", 0.6
    return "medical_2d", _modality_from_name(name), 0.6


def _modality_from_name(name: str) -> str:
    low = name.lower()
    for key, mod in (("endoscop", "endoscopy"), ("cxr", "X-ray"), ("xray", "X-ray"), ("x-ray", "X-ray"), ("chest", "X-ray"),
                     ("derm", "dermoscopy"), ("fundus", "fundus"), ("oct", "OCT"), ("ultrasound", "ultrasound"), ("us_", "ultrasound"),
                     ("mammo", "mammography"), ("ct", "CT"), ("mri", "MRI"), ("frame", "video frame"), ("clip", "video frame")):
        if key in low:
            return mod
    return "2-D medical image"


def ffprobe(path: Path) -> dict[str, Any]:
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=width,height,nb_frames,r_frame_rate,duration,codec_name", "-of", "default=nw=1", str(path)],
                             capture_output=True, text=True, timeout=60).stdout
        return dict(line.split("=", 1) for line in out.strip().splitlines() if "=" in line)
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


def _is_dicom_file(p: Path) -> bool:
    if _lower_ext(p) in DICOM_EXT:
        return True
    try:
        with p.open("rb") as fh:
            fh.seek(128)
            return fh.read(4) == b"DICM"
    except Exception:  # noqa: BLE001
        return False


def _list_images(folder: Path) -> list[Path]:
    return sorted(p for p in folder.iterdir() if p.is_file() and _lower_ext(p) in IMAGE_EXT)


def _find_reference_mask(path: Path) -> Path | None:
    """A *_mask / *_gt / *_label / *_seg NIfTI next to the input that shares its stem prefix (TemplateFlow desc-brain_mask,
    NFBS *_brainmask, nnU-Net labels)."""
    stem = path.name[: -len(_lower_ext(path))]
    prefix = re.sub(r"(_T1w|_T2w|_FLAIR|_0000|_ce-.*|_t1|_t2|_flair)$", "", stem, flags=re.I)
    cands = []
    for p in sorted(path.parent.iterdir()):
        if p == path or not p.is_file() or _lower_ext(p) not in (".nii.gz", ".nii"):
            continue
        n = p.name.lower()
        if not (n.startswith(prefix.lower()) or n.startswith(stem.lower())):
            continue
        if re.search(r"(mask|_gt|label|_seg|brainmask)", n):
            cands.append(p)
    return cands[0] if cands else None


def _read_json(p: Path) -> dict[str, Any] | None:
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:  # noqa: BLE001
        return None


def detect_folder(path: Path) -> Detection:
    dj = _read_json(path / "dataset.json") if (path / "dataset.json").is_file() else None
    has_tr, has_lb, has_ts = (path / "imagesTr").is_dir(), (path / "labelsTr").is_dir(), (path / "imagesTs").is_dir()
    if dj is not None and has_tr and has_lb:
        n_tr = len([p for p in (path / "imagesTr").iterdir() if p.is_file()])
        n_ts = len([p for p in (path / "imagesTs").iterdir() if p.is_file()]) if has_ts else 0
        is_v2 = "channel_names" in dj or "file_ending" in dj
        is_msd = ("modality" in dj and "training" in dj) or re.match(r"^Task\d+_", path.name) is not None
        det = {"dataset_json": {k: dj.get(k) for k in ("name", "description", "modality", "channel_names", "labels", "numTraining", "numTest", "file_ending") if k in dj},
               "n_imagesTr": n_tr, "n_imagesTs": n_ts, "has_imagesTs": has_ts}
        modality = None
        mods = dj.get("modality") or dj.get("channel_names") or {}
        if isinstance(mods, dict) and mods:
            modality = str(list(mods.values())[0])
        if is_v2 and re.match(r"^Dataset\d{3}_", path.name):
            return Detection(str(path), "nnunet_dataset", modality, str(path), det, ["nnU-Net v2 dataset folder (already converted): pipeline starts at verify_dataset_integrity"])
        if is_msd:
            notes = ["Medical Segmentation Decathlon task folder: converted into a private nnU-Net tree under the run folder"]
            if not re.match(r"^Task\d+_", path.name):
                notes.append("nnU-Net's MSD converter expects the folder to be named TaskXX_Name (e.g. Task04_Hippocampus)")
            if not has_ts:
                notes.append("no imagesTs folder: the predict step is skipped")
            return Detection(str(path), "msd_task", modality, str(path), det, notes)
        return Detection(str(path), "nnunet_dataset" if is_v2 else "msd_task", modality, str(path), det, ["dataset.json + imagesTr/labelsTr found"])
    files = [p for p in path.iterdir() if p.is_file()]
    dcm = [p for p in files[:50] if _is_dicom_file(p)]
    if dcm and len(dcm) >= max(1, len(files[:50]) // 2):
        return Detection(str(path), "dicom_series", None, str(path), {"n_files": len(files), "n_dicom_sampled": len(dcm)}, ["DICOM series: converted to NIfTI first"])
    imgs = _list_images(path)
    if imgs:
        frames = [p for p in imgs if re.match(r"^frame_\d+\.(png|jpg|jpeg)$", p.name, re.I)]
        votes: list[tuple[str, str, float]] = []
        for p in _evenly_spaced(imgs, 5):
            try:
                votes.append(classify_image(image_profile(p), p.name if not frames else path.name))
            except Exception as e:  # noqa: BLE001
                log.warning("image profile failed for %s: %s", p, e)
        n_micro = sum(1 for v in votes if v[0] == "microscopy_2d")
        kind2d = "microscopy_2d" if (n_micro * 2 >= len(votes) and votes) else "medical_2d"  # ties go to Cellpose (folder of images)
        mod2d = next((v[1] for v in votes if v[0] == kind2d), "2-D medical image")
        conf = round(max(n_micro, len(votes) - n_micro) / max(1, len(votes)), 2)
        det = {"n_images": len(imgs), "example": str(imgs[0]), "votes": [v[0] for v in votes], "per_image_kind": kind2d, "per_image_confidence": conf}
        if frames and len(frames) >= max(3, len(imgs) // 2):
            det["n_frames"] = len(frames)
            return Detection(str(path), "frames_folder", mod2d if mod2d != "2-D medical image" else "video frame", str(path), det,
                             [f"{len(frames)} video frames: {N_VIDEO_FRAMES} evenly spaced frames are analysed ({'Cellpose' if kind2d == 'microscopy_2d' else 'MedSAM box'})"])
        return Detection(str(path), "image_folder", mod2d, str(path), det, [f"{len(imgs)} 2-D images (first {IMAGE_FOLDER_CAP} are processed)"])
    sub = [p for p in path.iterdir() if p.is_dir()]
    if len(sub) == 1 and not files:
        return detect_folder(sub[0])
    return Detection(str(path), "unknown", None, str(path), {"n_files": len(files), "n_dirs": len(sub)}, ["folder layout not recognised (expected MSD Task, nnU-Net Dataset, DICOM series or 2-D images)"])


def detect(path_str: str, convert_video: bool = True) -> Detection:
    """Deterministic detection of what an input is. `path_str` may also be a MedMNIST flag."""
    s = path_str.strip()
    if s.lower() in MEDMNIST_FLAGS and not Path(s).exists():
        return Detection(s, "medmnist_flag", "MedMNIST", s.lower(), {"flag": s.lower(), "is_2d": s.lower() in MEDMNIST_2D},
                         ["MedMNIST dataset flag: download -> 2-epoch baseline CNN -> official evaluation"])
    path = Path(s).expanduser()
    if not path.exists():
        return Detection(s, "unknown", None, s, {}, ["path does not exist on this machine"])
    path = path.resolve()
    if path.is_dir():
        return detect_folder(path)
    ext = _lower_ext(path)
    name = path.name
    if ext in VIDEO_EXT:
        info = ffprobe(path)
        frames_dir = path.with_name(path.stem + "_frames")
        notes = [f"video ({info.get('codec_name', '?')} {info.get('width', '?')}x{info.get('height', '?')})"]
        if not frames_dir.is_dir() and convert_video:
            try:
                from .convert import video_to_frames
                r = video_to_frames(path)
                frames_dir = Path(r["frames_dir"])
                notes.append(f"{r['n_frames']} frames extracted with ffmpeg")
            except Exception as e:  # noqa: BLE001
                return Detection(str(path), "video", "video", str(path), {"ffprobe": info, "error": str(e)}, notes + [f"frame extraction failed: {e}"])
        if frames_dir.is_dir():
            sub = detect_folder(frames_dir)
            sub.path, sub.kind = str(path), "video"
            sub.details["ffprobe"] = info
            sub.notes = notes + sub.notes
            return sub
        return Detection(str(path), "video", "video", str(path), {"ffprobe": info}, notes + ["no frame folder next to the video"])
    if ext in VOLUME_EXT:
        if name.lower().endswith("_frames.nii.gz") and path.with_name(name[: -len(".nii.gz")]).is_dir():
            sub = detect_folder(path.with_name(name[: -len(".nii.gz")]))
            sub.notes.insert(0, "grayscale frame stack of a video: analysed as its PNG frame folder")
            return sub
        try:
            info = sniff_volume(path)
        except Exception as e:  # noqa: BLE001
            return Detection(str(path), "unknown", None, str(path), {"error": str(e)}, [f"could not read the volume: {e}"])
        kind, modality, conf = classify_volume(info, name)
        info["confidence"] = conf
        notes = [f"{info['dimension']}-D volume {info['size_xyz']} @ {info['spacing_xyz']} mm, {info['dtype']}, intensity [{info['min']:.0f}, {info['max']:.0f}]"]
        if info.get("n_volumes", 1) > 1:
            notes.append(f"4-D file with {info['n_volumes']} volumes: only the first is meaningful for the 3-D tools")
        if kind == "ct_volume":
            notes.append(f"{info['frac_below_-500'] * 100:.1f}% of voxels below -500 HU: Hounsfield air present -> CT")
        else:
            notes.append("no Hounsfield air (< -500) -> MRI-like volume; HD-BET brain extraction (skull-stripping) is applied")
            ref = _find_reference_mask(path)
            if ref:
                info["reference_mask"] = str(ref)
                notes.append(f"reference brain mask found next to the input ({ref.name}): Dice/IoU/Hausdorff are computed")
        return Detection(str(path), kind, modality, str(path), info, notes)
    if ext == ".npz":
        try:
            import numpy as np
            with np.load(str(path)) as z:
                keys = list(z.files)
                shapes = {k: list(z[k].shape) for k in keys[:8]}
        except Exception as e:  # noqa: BLE001
            return Detection(str(path), "unknown", None, str(path), {"error": str(e)}, [f"unreadable npz: {e}"])
        if "imgs" in keys:
            det = {"keys": keys, "shapes": shapes, "has_boxes": "boxes" in keys, "has_gts": "gts" in keys}
            mod = _modality_from_name(name)
            return Detection(str(path), "medsam_npz", mod, str(path), det, ["MedSAM demo npz ('imgs'" + (" + 'boxes'" if "boxes" in keys else "") + ")"])
        if "train_images" in keys:
            flag = re.sub(r"(_\d+)?\.npz$", "", name.lower())
            if flag in MEDMNIST_FLAGS:
                return Detection(str(path), "medmnist_flag", "MedMNIST", flag, {"flag": flag, "keys": keys, "data_root": str(path.parent), "is_2d": flag in MEDMNIST_2D},
                                 ["MedMNIST npz file: its flag is used"])
        return Detection(str(path), "unknown", None, str(path), {"keys": keys}, ["npz without 'imgs' key"])
    if ext in IMAGE_EXT:
        try:
            prof = image_profile(path)
        except Exception as e:  # noqa: BLE001
            return Detection(str(path), "unknown", None, str(path), {"error": str(e)}, [f"unreadable image: {e}"])
        if prof.get("n_frames", 1) > 1 and ext in (".tif", ".tiff"):
            prof["stack"] = True
        kind, modality, conf = classify_image(prof, name)
        prof["confidence"] = conf
        notes = [f"2-D image {prof['width']}x{prof['height']} ({prof['mode']}), {prof.get('n_blobs', 0)} bright objects, largest component {prof.get('largest_component_frac', 0):.0%} of the foreground"]
        notes.append("many small bright objects -> microscopy (Cellpose)" if kind == "microscopy_2d" else "no cell-like texture -> generic medical 2-D image (MedSAM box prompt)")
        return Detection(str(path), kind, modality, str(path), prof, notes)
    if _is_dicom_file(path):
        return Detection(str(path), "dicom_series", None, str(path), {"single_file": True}, ["single DICOM file: converted to NIfTI first"])
    if ext == ".zip":
        return Detection(str(path), "unknown", None, str(path), {}, ["zip archives are extracted at upload time: give the extracted folder"])
    return Detection(str(path), "unknown", None, str(path), {"ext": ext}, [f"unsupported file type {ext or '(none)'}"])


def refine_with_llm(det: Detection) -> Detection:
    """Optional LLM refinement (disabled unless AUTO_LLM_REFINE=1): may only adjust modality_guess/notes."""
    if os.environ.get("AUTO_LLM_REFINE", "0") != "1":
        return det
    try:
        prompt = ("You are given a deterministic detection of a biomedical input. Reply with ONE line 'modality: <name>' "
                  "that best describes the imaging modality, nothing else.\n" + json.dumps({"kind": det.kind, "details": det.details, "notes": det.notes}, default=str)[:4000])
        out = subprocess.run(["claude", "-p", prompt, "--output-format", "text"], capture_output=True, text=True, timeout=90).stdout
        m = re.search(r"modality:\s*(.+)", out)
        if m:
            det.notes.append(f"LLM refinement: modality '{m.group(1).strip()}' (deterministic guess: {det.modality_guess})")
            det.modality_guess = m.group(1).strip()[:40]
    except Exception as e:  # noqa: BLE001
        det.notes.append(f"LLM refinement skipped: {e}")
    return det


# --------------------------------------------------------------------------------------------------------------------
# recipes
# --------------------------------------------------------------------------------------------------------------------
@dataclass
class Step:
    agent: str
    tool: str
    arguments: dict[str, Any]
    label: str = ""
    optional: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Recipe:
    id: str
    title: str
    steps: list[Step]
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "title": self.title, "steps": [s.to_dict() for s in self.steps], "notes": self.notes}


OUT = "${run_dir}/outputs"


def centred_box(width: int, height: int, frac: float = 0.8) -> list[int]:
    """xyxy box covering `frac` of the image, centred."""
    m = (1 - frac) / 2
    x0, y0 = int(round(width * m)), int(round(height * m))
    x1, y1 = int(round(width * (1 - m))), int(round(height * (1 - m)))
    return [x0, y0, max(x1, x0 + 1), max(y1, y0 + 1)]


def _medkg_step(topic: str, modality: str | None = None, task: str | None = None, k: int = 10) -> Step:
    args: dict[str, Any] = {"topic": topic, "k": k, "summarise": True}
    if modality:
        args["modality"] = modality
    if task:
        args["task"] = task
    return Step("MedKG", "medkg_related_work", args, label="literature context (MedKG related work)", optional=True)


def _evenly_spaced(items: list[Any], n: int) -> list[Any]:
    if len(items) <= n:
        return list(items)
    return [items[int(round(i * (len(items) - 1) / (n - 1)))] for i in range(n)]


def _frame_steps(imgs: list[Path], per_image_kind: str, cap: int, evenly: bool) -> tuple[list[Step], str]:
    chosen = _evenly_spaced(imgs, cap) if evenly else imgs[:cap]
    steps: list[Step] = []
    tool = "cellpose" if per_image_kind == "microscopy_2d" else "medsam"
    for p in chosen:
        if tool == "cellpose":
            steps.append(Step("Cellpose", "cellpose_segment_image", {"image_path": str(p), "model_type": "cyto2", "channels": [0, 0], "device": "auto", "output_dir": OUT},
                              label=f"Cellpose segment {p.name}"))
        else:
            try:
                from PIL import Image
                with Image.open(str(p)) as im:
                    w, h = im.size
            except Exception:  # noqa: BLE001
                w, h = 512, 512
            steps.append(Step("MedSAM", "medsam_segment_with_box", {"image_path": str(p), "boxes": [centred_box(w, h)], "device": "auto", "output_dir": OUT},
                              label=f"MedSAM box {p.name}"))
    return steps, tool


def build_recipes(det: Detection) -> list[Recipe]:
    """Deterministic recipes for a detection; the first recipe is the default. Only real tool names/parameters are used."""
    kind, inp, d = det.kind, det.input_path, det.details
    recipes: list[Recipe] = []
    if kind == "mri_volume":
        steps = [Step("HDBET", "hdbet_extract_brain", {"input_path": "${input}", "device": "auto", "use_tta": True, "save_mask": True, "save_brain_image": True, "output_dir": OUT}, label="HD-BET brain extraction"),
                 Step("HDBET", "hdbet_inspect_brain_mask", {"mask_path": "${step[0].artifacts[_bet\\.nii(\\.gz)?$]}", "image_path": "${input}", "three_views": True, "output_dir": OUT}, label="mask QC (volume, components, overlays)")]
        if d.get("reference_mask"):
            steps.append(Step("HDBET", "hdbet_evaluate_brain_mask", {"prediction_path": "${step[0].artifacts[_bet\\.nii(\\.gz)?$]}", "reference_path": d["reference_mask"], "output_dir": OUT}, label="Dice/IoU/Hausdorff vs reference mask"))
        steps.append(_medkg_step("automated brain extraction skull stripping MRI deep learning", modality="MRI", task="segmentation"))
        recipes.append(Recipe("mri_brain_extraction", "MRI volume -> HD-BET skull-stripping -> mask QC" + (" -> evaluation" if d.get("reference_mask") else ""), steps,
                              ["HD-BET v2 (nnU-Net) brain mask + skull-stripped image, QC overlays, mask statistics"]))
        recipes.append(Recipe("volume_medsam_3d", "MRI volume -> MedSAM 3-D box (whole-volume centred box)",
                              [Step("MedSAM", "medsam_preprocess_ct_mr", {"image_path": "${input}", "modality": "MR", "output_dir": OUT}, label="MedSAM MR normalisation"),
                               Step("MedSAM", "medsam_segment_3d_with_box", {"volume_path": "${step[0].artifacts[MR_.*\\.npz$|\\.npz$]}", "boxes_3d": [_box3d(d)], "device": "auto", "output_dir": OUT}, label="MedSAM 3-D box segmentation"),
                               _medkg_step("foundation model promptable segmentation MRI volumes", modality="MRI", task="segmentation")],
                              ["alternative: MedSAM slice-wise box propagation on the MR-normalised volume"]))
    elif kind == "ct_volume":
        steps = [Step("MedSAM", "medsam_preprocess_ct_mr", {"image_path": "${input}", "modality": "CT", "window_level": 40, "window_width": 400, "output_dir": OUT}, label="MedSAM CT window + uint8 npz"),
                 Step("MedSAM", "medsam_segment_with_text", {"image_path": "${step[0].artifacts[\\.npz$]}", "prompts": FLARE_ORGANS, "device": "auto", "output_dir": OUT}, label="text-prompt abdominal organs (middle slice)"),
                 _medkg_step("abdominal organ segmentation CT deep learning foundation model", modality="CT", task="segmentation")]
        recipes.append(Recipe("ct_abdominal_organs", "CT volume -> MedSAM preprocess (soft-tissue window) -> text-prompt organ segmentation", steps,
                              ["the FLARE22 text-prompt decoder knows 13 abdominal organs; the middle slice of the windowed volume is segmented"]))
        recipes.append(Recipe("ct_medsam_3d", "CT volume -> MedSAM 3-D box (centred box, slice propagation)",
                              [Step("MedSAM", "medsam_segment_3d_with_box", {"volume_path": "${input}", "boxes_3d": [_box3d(d)], "clip_intensities": True, "device": "auto", "output_dir": OUT}, label="MedSAM 3-D box segmentation"),
                               _medkg_step("abdominal CT segmentation foundation model", modality="CT", task="segmentation")]))
    elif kind == "microscopy_2d":
        steps = [Step("Cellpose", "cellpose_estimate_diameter", {"image_path": "${input}", "model_type": "cyto2", "channels": [0, 0], "device": "auto", "output_dir": OUT}, label="diameter estimate (size model)"),
                 Step("Cellpose", "cellpose_segment_image", {"image_path": "${input}", "model_type": "cyto2", "channels": [0, 0], "diameter": "${step[0].result.estimated_diameter}", "device": "auto", "output_dir": OUT}, label="Cellpose cyto2 segmentation"),
                 Step("Cellpose", "cellpose_masks_to_rois", {"masks_path": "${step[1].artifacts[_seg\\.npy$]}", "imagej_rois": True, "per_object_csv": True, "output_dir": OUT}, label="ImageJ ROIs + per-object stats"),
                 _medkg_step("generalist cell segmentation microscopy deep learning", modality="microscopy", task="segmentation")]
        recipes.append(Recipe("microscopy_cellpose", "2-D microscopy -> Cellpose diameter -> segmentation -> ROIs", steps, ["cyto2 model, grayscale channels [0,0]"]))
        recipes.append(Recipe("microscopy_medsam_box", "2-D image -> MedSAM centred box (80 %)",
                              [Step("MedSAM", "medsam_segment_with_box", {"image_path": "${input}", "boxes": [centred_box(d.get("width", 512), d.get("height", 512))], "device": "auto", "output_dir": OUT}, label="MedSAM box segmentation"),
                               _medkg_step("promptable segmentation microscopy images", modality="microscopy", task="segmentation")]))
    elif kind == "medical_2d":
        box = centred_box(d.get("width", 512), d.get("height", 512))
        steps = [Step("MedSAM", "medsam_segment_with_box", {"image_path": "${input}", "boxes": [box], "device": "auto", "output_dir": OUT}, label=f"MedSAM box {box} (centred 80 %)"),
                 _medkg_step(f"promptable segmentation {det.modality_guess or 'medical images'} foundation model", task="segmentation")]
        recipes.append(Recipe("medical_2d_medsam_box", "2-D medical image -> MedSAM centred box (80 %)", steps, ["one box covering the central 80 % of the image; edit the box in the manual MedSAM form for a specific target"]))
        recipes.append(Recipe("medical_2d_cellpose", "2-D image -> Cellpose (if it is actually microscopy)",
                              [Step("Cellpose", "cellpose_segment_image", {"image_path": "${input}", "model_type": "cyto2", "channels": [0, 0], "device": "auto", "output_dir": OUT}, label="Cellpose cyto2"),
                               _medkg_step("cell segmentation microscopy", modality="microscopy", task="segmentation")]))
    elif kind == "medsam_npz":
        args: dict[str, Any] = {"image_path": "${input}", "device": "auto", "output_dir": OUT}
        if not d.get("has_boxes"):
            sh = (d.get("shapes") or {}).get("imgs") or [512, 512]
            args["boxes"] = [centred_box(int(sh[1]), int(sh[0]))]
        steps = [Step("MedSAM", "medsam_segment_with_box", args, label="MedSAM box prompts from the npz" if d.get("has_boxes") else "MedSAM centred box")]
        if d.get("has_gts"):
            steps.append(Step("MedSAM", "medsam_evaluate_dsc_nsd", {"prediction_path": "${step[0].artifacts[segs.*\\.npz$|\\.npz$]}", "ground_truth_path": "${input}", "output_dir": OUT}, label="DSC / NSD vs npz ground truth"))
        steps.append(_medkg_step(f"promptable segmentation {det.modality_guess or 'medical images'} MedSAM", task="segmentation"))
        recipes.append(Recipe("medsam_npz_box", "MedSAM demo npz -> box segmentation" + (" -> DSC/NSD" if d.get("has_gts") else ""), steps))
    elif kind in ("video", "frames_folder", "image_folder"):
        folder = Path(inp)
        imgs = _list_images(folder) if folder.is_dir() else []
        if kind == "image_folder":
            per_kind = d.get("per_image_kind", "microscopy_2d")
            steps, tool = _frame_steps(imgs, per_kind, IMAGE_FOLDER_CAP, evenly=False)
            title = f"folder of {len(imgs)} images -> {'Cellpose' if tool == 'cellpose' else 'MedSAM box'} per image (cap {IMAGE_FOLDER_CAP}) -> table"
            rid = "image_folder_" + tool
        else:
            imgs = [p for p in imgs if re.match(r"^frame_\d+\.", p.name, re.I)] or imgs
            per_kind = d.get("per_image_kind", "medical_2d")
            steps, tool = _frame_steps(imgs, per_kind, N_VIDEO_FRAMES, evenly=True)
            title = f"video -> {len(steps)} evenly spaced frames -> {'Cellpose' if tool == 'cellpose' else 'MedSAM box'} -> per-frame CSV + overlays"
            rid = "video_frames_" + tool
        n = len(steps)
        steps.append(Step("auto", "auto_frames_table", {"steps": list(range(n)), "tool": tool, "run_dir": "${run_dir}"}, label="per-frame CSV + overlay gallery"))
        topic = "video frame segmentation endoscopy deep learning" if tool == "medsam" else "time-lapse microscopy cell segmentation tracking"
        steps.append(_medkg_step(topic, modality=("endoscopy" if tool == "medsam" else "microscopy"), task="segmentation"))
        recipes.append(Recipe(rid, title, steps, [f"{'Cellpose cyto2' if tool == 'cellpose' else 'MedSAM with a centred 80 % box'} on each selected frame"]))
        alt_kind = "medical_2d" if per_kind == "microscopy_2d" else "microscopy_2d"
        alt_steps, alt_tool = _frame_steps(imgs, alt_kind, N_VIDEO_FRAMES if kind != "image_folder" else IMAGE_FOLDER_CAP, evenly=kind != "image_folder")
        alt_steps.append(Step("auto", "auto_frames_table", {"steps": list(range(len(alt_steps))), "tool": alt_tool, "run_dir": "${run_dir}"}, label="per-frame CSV + overlay gallery"))
        alt_steps.append(_medkg_step(topic, task="segmentation"))
        recipes.append(Recipe(rid.rsplit("_", 1)[0] + "_" + alt_tool, f"alternative: {'Cellpose' if alt_tool == 'cellpose' else 'MedSAM box'} on the same frames", alt_steps))
    elif kind in ("msd_task", "nnunet_dataset"):
        tree = {"nnunet_raw": "${run_dir}/nnunet/nnUNet_raw", "nnunet_preprocessed": "${run_dir}/nnunet/nnUNet_preprocessed", "nnunet_results": "${run_dir}/nnunet/nnUNet_results"}
        steps = [Step("auto", "auto_prepare_nnunet_tree", {"run_dir": "${run_dir}", "dataset_folder": "${input}" if kind == "nnunet_dataset" else None}, label="private nnU-Net tree under the run folder")]
        if kind == "msd_task":
            steps.append(Step("nnUNet", "nnunet_convert_msd_dataset", {"msd_folder": "${input}", **tree, "output_dir": OUT}, label="MSD -> nnU-Net v2 dataset"))
            ds, ds_folder = "${step[1].result.dataset_name}", "${step[1].result.dataset_folder}"
        else:
            ds, ds_folder = "${step[0].result.dataset_name}", "${step[0].result.dataset_folder}"
        steps += [Step("nnUNet", "nnunet_verify_dataset_integrity", {"dataset": ds, "nnunet_raw": tree["nnunet_raw"], "output_dir": OUT}, label="verify dataset integrity"),
                  Step("nnUNet", "nnunet_plan_and_preprocess", {"dataset": ds, "configurations": ["2d", "3d_fullres"], "check_dataset_integrity": False, **tree, "output_dir": OUT}, label="fingerprint, plans, preprocessing (2d, 3d_fullres)"),
                  Step("nnUNet", "nnunet_train_model", {"dataset": ds, "configuration": "2d", "fold": 0, "trainer": "nnUNetTrainer_5epochs", "export_validation_probabilities": True, "device": "auto", **tree, "output_dir": OUT}, label="train 2d fold 0 (nnUNetTrainer_5epochs)")]
        has_ts = d.get("has_imagesTs", True) and d.get("n_imagesTs", 1) > 0
        if has_ts:
            steps.append(Step("nnUNet", "nnunet_predict", {"input_path": ds_folder + "/imagesTs", "dataset": ds, "configuration": "2d", "trainer": "nnUNetTrainer_5epochs", "folds": [0], "device": "auto", **tree, "output_dir": OUT}, label="predict imagesTs with the 2d model"))
        steps.append(Step("nnUNet", "nnunet_find_best_configuration", {"dataset": ds, "trainers": ["nnUNetTrainer_5epochs"], "configurations": ["2d"], "folds": [0], "allow_ensembling": False, **tree, "output_dir": OUT}, label="find best configuration + postprocessing"))
        name = (d.get("dataset_json") or {}).get("name") or Path(inp).name
        steps.append(_medkg_step(f"{name} segmentation {det.modality_guess or ''} nnU-Net self-configuring".strip(), modality=det.modality_guess, task="segmentation"))
        recipes.append(Recipe("nnunet_pipeline_2d_5epochs", ("MSD task" if kind == "msd_task" else "nnU-Net dataset") + " -> convert/verify -> plan & preprocess -> train 2d (5 epochs) -> predict -> best configuration",
                              steps, ["debug-length training (nnUNetTrainer_5epochs, fold 0) in a private nnU-Net tree under the run folder; the workspace datasets are untouched"]))
    elif kind == "dicom_series":
        steps = [Step("auto", "auto_dicom_to_nifti", {"path": "${input}", "run_dir": "${run_dir}"}, label="DICOM -> NIfTI"),
                 Step("auto", "auto_plan_volume", {"nifti": "${step[0].artifacts[\\.nii\\.gz$]}", "run_dir": "${run_dir}"}, label="detect CT vs MRI and continue")]
        recipes.append(Recipe("dicom_to_volume", "DICOM series -> NIfTI -> CT/MRI recipe", steps, ["the CT or MRI recipe is chosen after conversion and appended to this run"]))
    elif kind == "medmnist_flag":
        flag = d.get("flag", inp)
        if flag in MEDMNIST_2D:
            dl: dict[str, Any] = {"flag": flag, "size": 28, "download": True}
            if d.get("data_root"):
                dl["data_root"] = d["data_root"]
            steps = [Step("MedMNIST", "medmnist_download_dataset", dl, label="download / verify npz"),
                     Step("MedMNIST", "medmnist_train_baseline", {"flag": flag, "epochs": 2, "device": "auto", "data_root": "${step[0].result.data_root}", "output_dir": OUT}, label="baseline CNN, 2 epochs"),
                     Step("MedMNIST", "medmnist_evaluate_predictions", {"predictions_path": "${step[1].artifacts[test.*\\.csv$]}", "flag": flag, "split": "test", "data_root": "${step[0].result.data_root}", "run_name": "auto", "output_dir": OUT}, label="official Evaluator (AUC/ACC)"),
                     _medkg_step(f"{flag} MedMNIST lightweight biomedical image classification benchmark", task="classification")]
            recipes.append(Recipe("medmnist_baseline", f"{flag} -> download -> 2-epoch baseline -> evaluate", steps))
        else:
            steps = [Step("MedMNIST", "medmnist_download_dataset", {"flag": flag, "size": 28, "download": True}, label="download / verify npz"),
                     Step("MedMNIST", "medmnist_montage", {"flag": flag, "split": "test", "size": 28, "length": 8, "download": False, "output_dir": OUT}, label="montage"),
                     _medkg_step(f"{flag} 3-D biomedical image classification benchmark", task="classification")]
            recipes.append(Recipe("medmnist_3d_montage", f"{flag} (3-D) -> download -> montage", steps, ["the baseline CNN is 2-D only"]))
    return recipes


def _box3d(info: dict[str, Any]) -> list[int]:
    """Centred 3-D box (80 % in x/y, middle 60 % of slices) in (D,H,W) voxel indices: [x0, y0, z0, x1, y1, z1]."""
    sx, sy, sz = (info.get("size_xyz") or [64, 64, 32])[:3]
    x0, y0, x1, y1 = centred_box(int(sx), int(sy))
    z0, z1 = int(round(sz * 0.2)), max(int(round(sz * 0.8)), int(round(sz * 0.2)) + 1)
    return [x0, y0, z0, x1, y1, z1]


def plan(path_str: str, tools_by_agent: dict[str, dict[str, dict]] | None = None) -> dict[str, Any]:
    """Detection + recipes as returned by POST /api/auto/plan. When tool schemas are given, bindings are validated."""
    det = refine_with_llm(detect(path_str))
    recipes = build_recipes(det)
    problems = validate_recipes(recipes, tools_by_agent) if tools_by_agent else []
    return {"path": det.path, "input_path": det.input_path, "kind": det.kind, "modality_guess": det.modality_guess, "details": det.details,
            "recipes": [r.to_dict() for r in recipes], "notes": det.notes + problems, "n_recipes": len(recipes)}


def validate_recipes(recipes: list[Recipe], tools_by_agent: dict[str, dict[str, dict]]) -> list[str]:
    """Check that every non-internal step binds to a known tool and only uses parameters of its JSON schema."""
    problems: list[str] = []
    for r in recipes:
        for i, s in enumerate(r.steps):
            if s.agent == "auto":
                continue
            tools = tools_by_agent.get(s.agent)
            if tools is None:
                problems.append(f"{r.id}[{i}]: agent {s.agent} is not available")
                continue
            schema = tools.get(s.tool)
            if schema is None:
                problems.append(f"{r.id}[{i}]: unknown tool {s.agent}.{s.tool}")
                continue
            props = set((schema.get("inputSchema") or schema).get("properties", {}).keys())
            unknown = [k for k in s.arguments if k not in props]
            if unknown:
                problems.append(f"{r.id}[{i}]: {s.tool} has no parameter(s) {unknown}")
            required = (schema.get("inputSchema") or schema).get("required", [])
            missing = [k for k in required if k not in s.arguments]
            if missing:
                problems.append(f"{r.id}[{i}]: {s.tool} misses required {missing}")
    return problems


# --------------------------------------------------------------------------------------------------------------------
# reference resolution
# --------------------------------------------------------------------------------------------------------------------
class RefError(ValueError):
    pass


def _lookup(obj: Any, dotted: str) -> Any:
    cur = obj
    for part in [p for p in dotted.split(".") if p]:
        if isinstance(cur, dict):
            if part not in cur:
                raise RefError(f"key '{part}' not in result (keys: {list(cur.keys())[:12]})")
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit():
            cur = cur[int(part)]
        else:
            raise RefError(f"cannot descend into '{part}'")
    return cur


def resolve_ref(expr: str, ctx: dict[str, Any]) -> Any:
    expr = expr.strip()
    if expr == "input":
        return ctx["input"]
    if expr == "run_dir":
        return ctx["run_dir"]
    m = re.match(r"^step\[(\d+)\]\.(artifacts|result|job_id|output_dir)(.*)$", expr)
    if not m:
        raise RefError(f"bad reference '{expr}'")
    idx, what, rest = int(m.group(1)), m.group(2), m.group(3)
    steps = ctx.get("steps") or []
    if idx >= len(steps) or steps[idx] is None:
        raise RefError(f"step[{idx}] has not run")
    st = steps[idx]
    if st.get("status") != "done":
        raise RefError(f"step[{idx}] is {st.get('status')}")
    if what == "job_id":
        return st.get("job_id")
    if what == "output_dir":
        return (st.get("result") or {}).get("output_dir")
    if what == "result":
        return _lookup(st.get("result"), rest.lstrip("."))
    am = re.match(r"^\[(.*)\]$", rest)
    if not am:
        raise RefError(f"artifacts reference needs [regex]: '{expr}'")
    pat = re.compile(am.group(1), re.I)
    arts = st.get("artifacts") or []
    for a in arts:
        if pat.search(str(a.get("path", ""))) or pat.search(str(a.get("description", ""))):
            return a["path"]
    raise RefError(f"no artifact of step[{idx}] matches /{am.group(1)}/ (have: {[Path(a.get('path', '')).name for a in arts][:10]})")


def resolve_value(v: Any, ctx: dict[str, Any]) -> Any:
    if isinstance(v, str):
        m = _REF.fullmatch(v)
        if m:
            return resolve_ref(m.group(1), ctx)
        return _REF.sub(lambda mm: str(resolve_ref(mm.group(1), ctx)), v)
    if isinstance(v, list):
        return [resolve_value(x, ctx) for x in v]
    if isinstance(v, dict):
        return {k: resolve_value(x, ctx) for k, x in v.items()}
    return v


def resolve_arguments(args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for k, v in args.items():
        if v is None:
            continue
        out[k] = resolve_value(v, ctx)
    return out


# --------------------------------------------------------------------------------------------------------------------
# key numbers, summary, report
# --------------------------------------------------------------------------------------------------------------------
_PREFERRED = ("n_masks", "estimated_diameter", "diameter_used", "n_objects", "median_diameter_px", "total_foreground_pixels", "n_boxes",
              "n_cases", "foreground_voxels", "volume_ml", "volume_mm3", "n_components", "device", "n_rows", "n_q1", "dataset_name", "dataset_id",
              "passed", "n_segmentations", "foreground_mean_dice", "best_key", "num_epochs", "epochs_completed", "auc", "acc", "AUC", "ACC",
              "n_prompts", "n_slices", "shape", "mean_dice", "Dice", "IoU", "status", "n_training_cases", "kept_slices")
_SKIP = {"message", "reference", "reference_cli", "artifacts", "logs", "traceback", "hint", "sources", "settings", "upstream_call", "determinism_note", "output_dir", "warnings"}


def key_numbers(result: Any, limit: int = 24) -> dict[str, Any]:
    """Flatten the scalar fields of a tool result (top level + one nested level of summary-like dicts)."""
    if not isinstance(result, dict):
        return {}
    flat: dict[str, Any] = {}

    def add(k: str, v: Any) -> None:
        if isinstance(v, bool) or isinstance(v, (int, float)):
            flat[k] = round(v, 5) if isinstance(v, float) else v
        elif isinstance(v, str) and 0 < len(v) <= 48 and "/" not in v:
            flat[k] = v

    for k, v in result.items():
        if k in _SKIP:
            continue
        if isinstance(v, dict) and k in ("summary", "validation", "metrics", "mean", "foreground_mean", "dice", "mean_metrics", "statistics", "stats", "pixel_counts", "timing", "timings_s", "timing_s", "timing_seconds", "counts", "best", "final"):
            for kk, vv in v.items():
                if isinstance(vv, dict):
                    for k3, v3 in vv.items():
                        add(f"{k}.{kk}.{k3}", v3)
                else:
                    add(f"{k}.{kk}", vv)
        else:
            add(k, v)
    ordered = {k: flat[k] for k in flat if k.split(".")[-1] in _PREFERRED}
    for k in flat:
        if k not in ordered:
            ordered[k] = flat[k]
        if len(ordered) >= limit:
            break
    return ordered


def _fmt(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


def write_report(run: dict[str, Any], run_dir: Path) -> tuple[Path, Path]:
    """summary.json + report.md for a run (called after every step so partial reports exist while running)."""
    steps = run.get("steps", [])
    summary = {"run_id": run["id"], "status": run["status"], "path": run["path"], "input_path": run.get("input_path"), "project": run.get("project"),
               "kind": run.get("kind"), "modality_guess": run.get("modality_guess"), "detection_notes": (run.get("detection") or {}).get("notes", []),
               "recipe": {"id": (run.get("recipe") or {}).get("id"), "title": (run.get("recipe") or {}).get("title")},
               "created_at": run.get("created_at"), "finished_at": run.get("finished_at"), "duration_s": run.get("duration_s"),
               "steps": [{"index": s["index"], "label": s.get("label"), "agent": s["agent"], "tool": s["tool"], "status": s["status"], "job_id": s.get("job_id"),
                          "duration_s": s.get("duration_s"), "error": s.get("error"), "key_numbers": s.get("key_numbers") or {}, "artifacts": s.get("artifacts") or [],
                          "arguments": s.get("resolved_arguments") or s.get("arguments")} for s in steps],
               "artifacts": run.get("artifacts") or [], "warnings": run.get("warnings") or []}
    sp = run_dir / "summary.json"
    sp.write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=str))
    lines = [f"# Auto-analysis run {run['id']}", "",
             f"- **status**: {run['status']}" + (f" ({run.get('duration_s')} s)" if run.get("duration_s") is not None else ""),
             f"- **input**: `{run['path']}`" + (f" -> `{run.get('input_path')}`" if run.get("input_path") and run.get("input_path") != run["path"] else ""),
             f"- **detected**: {run.get('kind')} (modality guess: {run.get('modality_guess')})",
             f"- **recipe**: {(run.get('recipe') or {}).get('id')} - {(run.get('recipe') or {}).get('title')}",
             f"- **started**: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(run.get('created_at') or time.time()))}", ""]
    if (run.get("detection") or {}).get("notes"):
        lines += ["## Detection", ""] + [f"- {n}" for n in run["detection"]["notes"]] + [""]
    lines += ["## Steps", "", "| # | step | agent.tool | status | time | key numbers |", "|---|---|---|---|---|---|"]
    for s in steps:
        kn = "; ".join(f"{k}={_fmt(v)}" for k, v in list((s.get("key_numbers") or {}).items())[:8])
        err = f" - {s['error'][:160]}" if s.get("error") else ""
        lines.append(f"| {s['index']} | {s.get('label') or ''} | `{s['agent']}.{s['tool']}` | {s['status']}{err} | {s.get('duration_s') if s.get('duration_s') is not None else ''} | {kn} |")
    lines.append("")
    if any(s.get("artifacts") for s in steps):
        lines += ["## Artifacts", ""]
        for s in steps:
            if s.get("artifacts"):
                lines.append(f"### step {s['index']} - {s['agent']}.{s['tool']}")
                lines += [f"- `{a.get('path')}` - {a.get('description', '')}" for a in s["artifacts"][:40]]
                lines.append("")
    if run.get("artifacts"):
        lines += ["### run", ""] + [f"- `{a.get('path')}` - {a.get('description', '')}" for a in run["artifacts"]] + [""]
    if run.get("warnings"):
        lines += ["## Warnings", ""] + [f"- {w}" for w in run["warnings"]] + [""]
    rp = run_dir / "report.md"
    rp.write_text("\n".join(lines))
    return sp, rp


# --------------------------------------------------------------------------------------------------------------------
# internal ("auto") steps
# --------------------------------------------------------------------------------------------------------------------
def _internal_prepare_nnunet_tree(args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    base = Path(args["run_dir"]) / "nnunet"
    dirs = {k: base / k for k in ("nnUNet_raw", "nnUNet_preprocessed", "nnUNet_results")}
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    res: dict[str, Any] = {"message": f"private nnU-Net tree at {base}", "nnunet_raw": str(dirs["nnUNet_raw"]), "nnunet_preprocessed": str(dirs["nnUNet_preprocessed"]),
                           "nnunet_results": str(dirs["nnUNet_results"]), "artifacts": [{"description": "private nnU-Net tree (raw/preprocessed/results)", "path": str(base)}]}
    if args.get("dataset_folder"):
        src = Path(args["dataset_folder"]).resolve()
        link = dirs["nnUNet_raw"] / src.name
        if not link.exists():
            os.symlink(str(src), str(link))
        res.update({"dataset_name": src.name, "dataset_folder": str(link), "message": res["message"] + f"; {src.name} linked into nnUNet_raw"})
    return res


def _internal_frames_table(args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    run_dir = Path(args["run_dir"])
    steps = ctx.get("steps") or []
    rows: list[dict[str, Any]] = []
    overlays: list[dict[str, str]] = []
    gallery = run_dir / "overlays"
    gallery.mkdir(parents=True, exist_ok=True)
    for i in args.get("steps", []):
        st = steps[i] if i < len(steps) else None
        if not st:
            continue
        r = st.get("result") if isinstance(st.get("result"), dict) else {}
        a = st.get("resolved_arguments") or st.get("arguments") or {}
        frame = a.get("image_path", "")
        row = {"index": i, "frame": Path(frame).name, "frame_path": frame, "tool": f"{st['agent']}.{st['tool']}", "status": st.get("status"), "duration_s": st.get("duration_s"),
               "n_objects": r.get("n_masks"), "foreground_pixels": r.get("total_foreground_pixels"), "diameter_px": r.get("diameter_used"), "error": (st.get("error") or "")[:120]}
        ov = next((x for x in (st.get("artifacts") or []) if re.search(r"(overlay|outlines\.png|segmentation\.png|4-panel)", str(x.get("path", "")) + " " + str(x.get("description", "")), re.I) and str(x.get("path", "")).lower().endswith(".png")), None)
        if ov:
            dst = gallery / f"{i:02d}_{Path(frame).stem}_{Path(ov['path']).name}"
            try:
                shutil.copy2(ov["path"], dst)
                row["overlay"] = str(dst)
                overlays.append({"description": f"overlay for {Path(frame).name}", "path": str(dst)})
            except Exception as e:  # noqa: BLE001
                row["overlay"] = ov["path"]
                row["error"] = (row["error"] + f" copy failed: {e}").strip()
        rows.append(row)
    csv_path = run_dir / "frames.csv"
    cols = ["index", "frame", "tool", "status", "duration_s", "n_objects", "foreground_pixels", "diameter_px", "overlay", "frame_path", "error"]
    with csv_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    ok = sum(1 for r in rows if r["status"] == "done")
    nums = [r["n_objects"] if r["n_objects"] is not None else r["foreground_pixels"] for r in rows if r["status"] == "done"]
    nums = [n for n in nums if isinstance(n, (int, float))]
    return {"message": f"{ok}/{len(rows)} frames segmented; per-frame table written", "n_frames": len(rows), "n_done": ok,
            "mean_per_frame": round(sum(nums) / len(nums), 2) if nums else None, "metric": "n_objects" if args.get("tool") == "cellpose" else "foreground_pixels",
            "rows": rows, "artifacts": [{"description": "per-frame results (CSV)", "path": str(csv_path)}] + overlays}


def _internal_dicom_to_nifti(args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    from .convert import dicom_to_nifti
    src = Path(args["path"])
    r = dicom_to_nifti(src)
    out = Path(args["run_dir"]) / "converted" / Path(r["nifti"]).name
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(r["nifti"], out)
        r["nifti"] = str(out)
    except Exception:  # noqa: BLE001
        pass
    return {"message": f"DICOM converted ({r.get('n_files')} files, size {r.get('size_xyz')})", **{k: v for k, v in r.items() if k != "nifti"},
            "nifti": r["nifti"], "artifacts": [{"description": "DICOM series converted to NIfTI", "path": r["nifti"]}]}


def _internal_plan_volume(args: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    """Detect the converted volume and hand the CT/MRI recipe steps back to the runner (appended to the run)."""
    det = detect(args["nifti"])
    recipes = build_recipes(det)
    if not recipes:
        raise RuntimeError(f"no recipe for converted volume kind {det.kind}")
    return {"message": f"converted volume detected as {det.kind} ({det.modality_guess}); appending recipe {recipes[0].id}", "kind": det.kind, "modality_guess": det.modality_guess,
            "append_steps": [s.to_dict() for s in recipes[0].steps], "append_input": det.input_path, "artifacts": []}


INTERNAL: dict[str, Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]] = {
    "auto_prepare_nnunet_tree": _internal_prepare_nnunet_tree,
    "auto_frames_table": _internal_frames_table,
    "auto_dicom_to_nifti": _internal_dicom_to_nifti,
    "auto_plan_volume": _internal_plan_volume,
}


# --------------------------------------------------------------------------------------------------------------------
# service: plan + chained execution
# --------------------------------------------------------------------------------------------------------------------
class AutoService:
    """Plans and runs recipes. `runner.submit(agent, tool, args)` must return a job object with .id/.status/.result/.error
    (the Studio JobRunner); `tools_lookup(agent)` returns {tool_name: schema} or None."""

    def __init__(self, runner: Any, auto_dir: Path, tools_lookup: Callable[[str], dict[str, dict] | None] | None = None, poll_s: float = 0.5):
        self.runner = runner
        self.auto_dir = Path(auto_dir)
        self.tools_lookup = tools_lookup
        self.poll_s = poll_s
        self.runs: dict[str, dict[str, Any]] = {}
        self.tasks: dict[str, asyncio.Task] = {}
        self.auto_dir.mkdir(parents=True, exist_ok=True)
        for f in sorted(self.auto_dir.glob("*/run.json")):
            try:
                d = json.loads(f.read_text())
                if d.get("status") in ("queued", "running"):  # the backend restarted mid-run
                    d["status"] = "error"
                    d["warnings"] = (d.get("warnings") or []) + ["backend restarted while the run was in progress"]
                    for s in d.get("steps", []):
                        if s.get("status") in ("queued", "running"):
                            s["status"] = "error"
                            s["error"] = "backend restarted"
                self.runs[d["id"]] = d
            except Exception:  # noqa: BLE001
                pass

    # ---- planning ----
    def _tools_by_agent(self) -> dict[str, dict[str, dict]] | None:
        if not self.tools_lookup:
            return None
        out: dict[str, dict[str, dict]] = {}
        for agent in ("MedSAM", "MedMNIST", "Cellpose", "HDBET", "nnUNet", "MedKG"):
            t = self.tools_lookup(agent)
            if t:
                out[agent] = t
        return out or None

    def plan(self, path: str) -> dict[str, Any]:
        return plan(path, self._tools_by_agent())

    # ---- running ----
    def _persist(self, run: dict[str, Any]) -> None:
        run_dir = Path(run["run_dir"])
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run.json").write_text(json.dumps(run, indent=1, ensure_ascii=False, default=str))
        try:
            sp, rp = write_report(run, run_dir)
            run["summary_path"], run["report_path"] = str(sp), str(rp)
        except Exception as e:  # noqa: BLE001
            log.warning("report write failed for %s: %s", run["id"], e)

    def start(self, path: str, recipe_id: str | None = None, project: str | None = None, planned: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create and schedule a run (must be called on the event-loop thread); `planned` may carry a precomputed plan."""
        p = planned if planned and planned.get("path") == path else self.plan(path)
        recipes = p["recipes"]
        if not recipes:
            raise ValueError(f"no recipe for input kind '{p['kind']}': " + "; ".join(p["notes"]))
        recipe = next((r for r in recipes if r["id"] == recipe_id), None) if recipe_id else recipes[0]
        if recipe is None:
            raise ValueError(f"unknown recipe_id {recipe_id!r}; available: {[r['id'] for r in recipes]}")
        run_id = time.strftime("%Y%m%d-%H%M%S") + "_" + uuid.uuid4().hex[:6]
        run_dir = self.auto_dir / run_id
        run: dict[str, Any] = {"id": run_id, "path": p["path"], "input_path": p["input_path"], "project": project, "kind": p["kind"], "modality_guess": p["modality_guess"],
                               "detection": {"details": p["details"], "notes": p["notes"]}, "recipe": {"id": recipe["id"], "title": recipe["title"], "notes": recipe.get("notes", [])},
                               "status": "queued", "created_at": time.time(), "started_at": None, "finished_at": None, "duration_s": None, "run_dir": str(run_dir),
                               "steps": [{"index": i, "label": s.get("label", ""), "agent": s["agent"], "tool": s["tool"], "arguments": s["arguments"], "optional": bool(s.get("optional")),
                                          "status": "queued", "job_id": None, "started_at": None, "finished_at": None, "duration_s": None, "error": None, "hint": None,
                                          "message": None, "artifacts": [], "key_numbers": {}, "resolved_arguments": None} for i, s in enumerate(recipe["steps"])],
                               "jobs": [], "artifacts": [], "warnings": [], "summary_path": None, "report_path": None}
        self.runs[run_id] = run
        self._persist(run)
        self.tasks[run_id] = asyncio.create_task(self._execute(run))
        return self.public(run)

    def public(self, run: dict[str, Any]) -> dict[str, Any]:
        out = dict(run)
        out["steps"] = [dict(s) for s in run["steps"]]
        return out

    def get(self, run_id: str) -> dict[str, Any] | None:
        r = self.runs.get(run_id)
        return self.public(r) if r else None

    def list(self, limit: int = 30) -> list[dict[str, Any]]:
        rs = sorted(self.runs.values(), key=lambda r: r["created_at"], reverse=True)[:limit]
        return [{k: r.get(k) for k in ("id", "path", "input_path", "kind", "modality_guess", "status", "created_at", "finished_at", "duration_s", "project")} |
                {"recipe": (r.get("recipe") or {}).get("id"), "n_steps": len(r.get("steps", [])), "n_done": sum(1 for s in r.get("steps", []) if s["status"] == "done")} for r in rs]

    async def _wait_job(self, job: Any) -> Any:
        while getattr(job, "status", "done") in ("queued", "running"):
            await asyncio.sleep(self.poll_s)
        return job

    async def _execute(self, run: dict[str, Any]) -> None:
        run["status"], run["started_at"] = "running", time.time()
        ctx = {"input": run["input_path"], "run_dir": run["run_dir"], "steps": run["steps"]}
        Path(run["run_dir"], "outputs").mkdir(parents=True, exist_ok=True)
        self._persist(run)
        failed_required = False
        i = 0
        while i < len(run["steps"]):
            s = run["steps"][i]
            if failed_required:
                s["status"] = "skipped"
                i += 1
                continue
            s["status"], s["started_at"] = "running", time.time()
            self._persist(run)
            try:
                args = resolve_arguments(s["arguments"], ctx)
                s["resolved_arguments"] = args
                if s["agent"] == "auto":
                    fn = INTERNAL.get(s["tool"])
                    if fn is None:
                        raise RuntimeError(f"unknown internal step {s['tool']}")
                    result = await asyncio.to_thread(fn, args, ctx)
                    if isinstance(result, dict) and result.get("append_steps"):
                        for j, ns in enumerate(result["append_steps"]):
                            run["steps"].append({"index": len(run["steps"]), "label": ns.get("label", ""), "agent": ns["agent"], "tool": ns["tool"], "arguments": ns["arguments"],
                                                 "optional": bool(ns.get("optional")), "status": "queued", "job_id": None, "started_at": None, "finished_at": None, "duration_s": None,
                                                 "error": None, "hint": None, "message": None, "artifacts": [], "key_numbers": {}, "resolved_arguments": None})
                        if result.get("append_input"):
                            ctx["input"] = run["input_path"] = result["append_input"]
                        result = {k: v for k, v in result.items() if k != "append_steps"}
                else:
                    tools = self.tools_lookup(s["agent"]) if self.tools_lookup else None
                    if self.tools_lookup and (tools is None or s["tool"] not in tools):
                        raise RuntimeError(f"tool {s['agent']}.{s['tool']} is not available on the Studio")
                    job = self.runner.submit(s["agent"], s["tool"], args)
                    s["job_id"] = job.id
                    run["jobs"].append(job.id)
                    self._persist(run)
                    await self._wait_job(job)
                    if job.status != "done":
                        s["hint"] = (job.result or {}).get("hint") if isinstance(job.result, dict) else None
                        raise RuntimeError(job.error or "job failed")
                    result = job.result
                s["status"] = "done"
                s["result"] = result
                s["message"] = result.get("message") if isinstance(result, dict) else None
                s["artifacts"] = [a for a in (result.get("artifacts") or []) if isinstance(a, dict) and a.get("path")] if isinstance(result, dict) else []
                s["key_numbers"] = key_numbers(result)
            except Exception as e:  # noqa: BLE001
                s["status"], s["error"] = "error", f"{e}"
                if s.get("optional"):
                    run["warnings"].append(f"optional step {i} ({s['agent']}.{s['tool']}) failed: {e}")
                else:
                    failed_required = True
                    run["warnings"].append(f"step {i} ({s['agent']}.{s['tool']}) failed: {e}; later steps skipped")
            finally:
                s["finished_at"] = time.time()
                s["duration_s"] = round(s["finished_at"] - (s["started_at"] or s["finished_at"]), 2)
            self._persist(run)
            i += 1
        run["finished_at"] = time.time()
        run["duration_s"] = round(run["finished_at"] - run["started_at"], 2)
        if failed_required:
            run["status"] = "error"
        elif any(s["status"] == "error" for s in run["steps"]):
            run["status"] = "partial"
        else:
            run["status"] = "done"
        run["artifacts"] = [{"description": "run summary (JSON)", "path": str(Path(run["run_dir"]) / "summary.json")},
                            {"description": "run report (markdown)", "path": str(Path(run["run_dir"]) / "report.md")}]
        for s in run["steps"]:
            if s["agent"] == "auto" and s["status"] == "done":
                run["artifacts"] += [a for a in s.get("artifacts", []) if a.get("path", "").endswith(".csv")]
        self._persist(run)
