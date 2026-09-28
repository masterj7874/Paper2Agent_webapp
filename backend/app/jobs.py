"""Background tool-call jobs with an in-memory registry + JSON persistence, so the UI can poll progress and reload results."""
from __future__ import annotations

import asyncio
import json
import time
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .config import JOB_DIR
from .mcp_manager import MCPManager


@dataclass
class Job:
    id: str
    agent: str
    tool: str
    arguments: dict[str, Any]
    status: str = "queued"  # queued | running | done | error
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    finished_at: float | None = None
    result: Any = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["duration_s"] = round((self.finished_at or time.time()) - (self.started_at or self.created_at), 2) if self.started_at else None
        return d


class JobRunner:
    def __init__(self, manager: MCPManager):
        self.manager = manager
        self.jobs: dict[str, Job] = {}
        JOB_DIR.mkdir(parents=True, exist_ok=True)
        for f in sorted(JOB_DIR.glob("*.json")):
            try:
                d = json.loads(f.read_text())
                self.jobs[d["id"]] = Job(**{k: d[k] for k in Job.__dataclass_fields__ if k in d})
            except Exception:
                pass

    def _persist(self, job: Job) -> None:
        (JOB_DIR / f"{job.id}.json").write_text(json.dumps(job.to_dict(), ensure_ascii=False, default=str, indent=1))

    def submit(self, agent: str, tool: str, arguments: dict[str, Any]) -> Job:
        job = Job(id=uuid.uuid4().hex[:12], agent=agent, tool=tool, arguments=arguments)
        self.jobs[job.id] = job
        self._persist(job)
        asyncio.create_task(self._run(job))
        return job

    async def _run(self, job: Job) -> None:
        job.status, job.started_at = "running", time.time()
        self._persist(job)
        try:
            job.result = await self.manager.get(job.agent).call(job.tool, job.arguments)
            job.status = "done"
        except Exception as e:
            msg = str(e)
            job.error = msg if msg else f"{type(e).__name__}"
            job.status = "error"
            job.result = {"traceback": traceback.format_exc()[-4000:], "hint": error_hint(msg, job.arguments)}
        finally:
            job.finished_at = time.time()
            self._persist(job)

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        return [j.to_dict() for j in sorted(self.jobs.values(), key=lambda j: j.created_at, reverse=True)[:limit]]


_HINTS = [
    (("Unable to determine ImageIO reader", "could not be read by SimpleITK", "not a NIfTI", "Unsupported extension"),
     "The tool expects a medical volume/image file (NIfTI .nii/.nii.gz, NRRD, MHA, or PNG/JPG/TIF for 2-D tools). "
     "Videos (.avi/.mp4), DICOM and zip archives are converted automatically when uploaded through this app - "
     "pick the converted frames/NIfTI path from the chips under the field instead of the original file."),
    (("Missing required argument", "Field required", "missing 1 required", "validation error", "is required for", "is required when"),
     "A required parameter is empty. Fields marked with * must be filled before running."),
    (("already taken",), "This dataset id already exists in nnU-Net's raw folder; choose another overwrite_target_id or reuse the existing dataset."),
    (("No such file", "does not exist", "not found"), "The path does not exist on this machine. Upload the file or pick a sample chip; paths must be absolute server paths."),
    (("CUDA out of memory",), "The GPU ran out of memory; retry with device=cpu, TTA off or a smaller input."),
]


def error_hint(msg: str, arguments: dict[str, Any] | None = None) -> str | None:
    low = (msg or "").lower()
    for needles, hint in _HINTS:
        if any(n.lower() in low for n in needles):
            ext = ""
            for v in (arguments or {}).values():
                if isinstance(v, str) and "." in v[-8:]:
                    ext = v.rsplit(".", 1)[-1].lower()
            if needles[0].startswith("Unable") and ext in ("avi", "mp4", "mov", "mkv", "wmv", "mpg", "webm"):
                return f"'{ext}' is a video format. " + hint
            return hint
    return None
