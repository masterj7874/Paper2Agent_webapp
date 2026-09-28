"""Upload-time media conversion so files land in formats the Paper2Agent tools accept.

- video (avi/mp4/mov/mkv/wmv/mpg/mpeg/m4v/webm) -> PNG frame folder (ffmpeg) + a 3-D NIfTI stack of the
  grayscale frames (frames x H x W, uint8) for volume tools
- DICOM (.dcm single file, or a zip/folder holding a series) -> NIfTI (.nii.gz) via SimpleITK
- zip archives -> extracted folder (+ DICOM detection inside)
Every conversion is best effort: failures are reported in `notice`, the original upload is always kept.
"""
from __future__ import annotations

import logging
import shutil
import subprocess
import zipfile
from pathlib import Path

log = logging.getLogger("paper2agent.web.convert")

VIDEO_EXT = {".avi", ".mp4", ".mov", ".mkv", ".wmv", ".mpg", ".mpeg", ".m4v", ".webm"}
DICOM_EXT = {".dcm", ".dicom", ".ima"}


def _ffprobe(path: Path) -> dict:
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                              "stream=width,height,nb_frames,r_frame_rate,duration,codec_name", "-of", "default=nw=1",
                              str(path)], capture_output=True, text=True, timeout=60).stdout
        return dict(line.split("=", 1) for line in out.strip().splitlines() if "=" in line)
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)}


def video_to_frames(src: Path, max_frames: int = 600, fps: float | None = None) -> dict:
    """Extract PNG frames with ffmpeg and build a NIfTI stack; returns {frames_dir, n_frames, nifti, info}."""
    info = _ffprobe(src)
    frames_dir = src.with_suffix("").with_name(src.stem + "_frames")
    frames_dir.mkdir(parents=True, exist_ok=True)
    vf = []
    if fps:
        vf.append(f"fps={fps}")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(src)]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += ["-frames:v", str(max_frames), str(frames_dir / "frame_%05d.png")]
    subprocess.run(cmd, check=True, capture_output=True, timeout=600)
    frames = sorted(frames_dir.glob("frame_*.png"))
    result = {"frames_dir": str(frames_dir), "n_frames": len(frames), "info": info, "first_frame": str(frames[0]) if frames else None}
    if frames:
        try:
            import numpy as np
            import SimpleITK as sitk
            from PIL import Image
            arr = np.stack([np.asarray(Image.open(f).convert("L"), dtype=np.uint8) for f in frames])  # (T, H, W)
            img = sitk.GetImageFromArray(arr)
            img.SetSpacing((1.0, 1.0, 1.0))
            nii = src.with_name(src.stem + "_frames.nii.gz")
            sitk.WriteImage(img, str(nii))
            result["nifti"] = str(nii)
            result["shape_zyx"] = list(arr.shape)
        except Exception as e:  # noqa: BLE001
            result["nifti_error"] = str(e)
    return result


def dicom_to_nifti(src: Path) -> dict:
    """Convert a DICOM series directory (or a single .dcm) to NIfTI with SimpleITK."""
    import SimpleITK as sitk
    if src.is_dir():
        reader = sitk.ImageSeriesReader()
        ids = reader.GetGDCMSeriesIDs(str(src))
        if not ids:
            # search one level deeper (zip extractions often nest)
            for sub in sorted(p for p in src.rglob("*") if p.is_dir()):
                ids = reader.GetGDCMSeriesIDs(str(sub))
                if ids:
                    src = sub
                    break
        if not ids:
            raise ValueError("no DICOM series found")
        files = reader.GetGDCMSeriesFileNames(str(src), ids[0])
        reader.SetFileNames(files)
        img = reader.Execute()
        out = src.with_name(src.name.rstrip("/") + "_dicom.nii.gz")
        n = len(files)
    else:
        img = sitk.ReadImage(str(src))
        out = src.with_name(src.stem + "_dicom.nii.gz")
        n = 1
    sitk.WriteImage(img, str(out))
    return {"nifti": str(out), "n_files": n, "size_xyz": list(img.GetSize()), "spacing": list(img.GetSpacing())}


def extract_zip(src: Path) -> dict:
    dest = src.with_name(src.stem + "_extracted")
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(src) as z:
        members = [m for m in z.namelist() if not m.startswith("__MACOSX") and not Path(m).name.startswith("._")]
        for m in members:
            target = (dest / m).resolve()
            if not str(target).startswith(str(dest.resolve())):
                continue  # zip-slip guard
            z.extract(m, dest)
    files = [p for p in dest.rglob("*") if p.is_file()]
    return {"folder": str(dest), "n_files": len(files), "examples": [str(p) for p in files[:5]]}


def convert_upload(path: Path) -> dict:
    """Dispatch on extension; returns {kind, converted: [{kind, path, description}], notice}."""
    ext = path.suffix.lower()
    conv: list[dict] = []
    notice = ""
    kind = "file"
    try:
        if ext in VIDEO_EXT:
            kind = "video"
            r = video_to_frames(path)
            conv.append({"kind": "folder", "path": r["frames_dir"], "description": f"{r['n_frames']} PNG frames extracted from the video (use with 2-D image tools such as MedSAM segment_with_box, one frame at a time, or folder tools)"})
            if r.get("first_frame"):
                conv.append({"kind": "image", "path": r["first_frame"], "description": "first frame (PNG)"})
            if r.get("nifti"):
                conv.append({"kind": "volume", "path": r["nifti"], "description": f"NIfTI stack of the grayscale frames {r.get('shape_zyx')} (frames x H x W) for 3-D volume tools; note: not a CT/MR scan, so CT/MR-specific preprocessing is not meaningful"})
            notice = (f"Video detected ({r['info'].get('codec_name','?')} {r['info'].get('width','?')}x{r['info'].get('height','?')}, "
                      f"{r['n_frames']} frames extracted). Medical-imaging tools cannot read .avi/.mp4 directly; the converted frames/NIfTI below were created automatically.")
        elif ext == ".zip":
            kind = "zip"
            r = extract_zip(path)
            conv.append({"kind": "folder", "path": r["folder"], "description": f"extracted archive ({r['n_files']} files)"})
            try:
                d = dicom_to_nifti(Path(r["folder"]))
                conv.append({"kind": "volume", "path": d["nifti"], "description": f"DICOM series converted to NIfTI (size {d['size_xyz']}, spacing {d['spacing']})"})
                kind = "dicom-zip"
            except Exception:  # noqa: BLE001 — not a DICOM archive
                pass
            notice = f"Archive extracted to a folder ({r['n_files']} files)."
        elif ext in DICOM_EXT:
            kind = "dicom"
            d = dicom_to_nifti(path)
            conv.append({"kind": "volume", "path": d["nifti"], "description": "DICOM converted to NIfTI"})
            notice = "DICOM converted to NIfTI for the volume tools."
    except Exception as e:  # noqa: BLE001
        log.warning("conversion of %s failed: %s", path, e)
        notice = f"Automatic conversion failed ({e}); the original upload is kept."
    return {"kind": kind, "converted": conv, "notice": notice}
