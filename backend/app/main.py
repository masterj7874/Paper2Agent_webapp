"""Paper2Agent Studio backend — FastAPI gateway to Paper2Agent-generated MCP servers.

Endpoints
  GET  /api/agents                       agents + status + display metadata
  GET  /api/agents/{name}/tools          tool list with JSON input schemas
  POST /api/agents/{name}/restart        restart a stdio server
  POST /api/upload                       multipart file upload -> server path usable as a tool argument
  GET  /api/samples                      bundled sample inputs per agent
  POST /api/jobs                         {agent, tool, arguments} -> job (runs in background)
  GET  /api/jobs, /api/jobs/{id}         job list / status+result
  GET  /api/files?path=...               serve an artifact (only under allowed roots)
  GET  /api/papers/{skill}, /section, /search, /asset/{cat}/{name}
  GET  /api/stats                        GPU/host stats for the dashboard
  POST /api/auto/plan {path}             deterministic detection + recipes (chains of tool calls) for a file/folder/flag
  POST /api/auto/run {path, recipe_id?, project?}  run a recipe as chained jobs -> {run_id, jobs, steps...}
  GET  /api/auto/runs, /api/auto/runs/{id}          run list / live progress + final report (summary.json, report.md)
"""
from __future__ import annotations

import asyncio
import logging
import json
import mimetypes
import os
import shutil
import subprocess
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .auto import MEDMNIST_FLAGS, AutoService
from .config import ALLOWED_ROOTS, PAPER_RUNS_DIR, SKILLS_DIR, UPLOAD_DIR, load_agents
from .jobs import JobRunner
from .mcp_manager import MCPManager
from .papers import paper_overview, paper_search, paper_section
from .paper_automation import PaperAutomation
from .paper_documents import MAX_UPLOAD_BYTES, repository_url
from .manuscript_api import create_manuscript_router
from .manuscript_service import MANUSCRIPT_DIR, ManuscriptService
from .research_resources import RESEARCH_DIR, ResearchInventory

log = logging.getLogger("paper2agent.web")

AGENTS = load_agents()
MANAGER = MCPManager(AGENTS)
RUNNER = JobRunner(MANAGER)
WEBAPP_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = WEBAPP_ROOT / "frontend" / "dist"
SERVE_ROOTS = [*ALLOWED_ROOTS, UPLOAD_DIR, WEBAPP_ROOT / "data", SKILLS_DIR, PAPER_RUNS_DIR, MANUSCRIPT_DIR, RESEARCH_DIR]
AUTO_DIR = Path(os.environ.get("PAPER2AGENT_AUTO_DIR", WEBAPP_ROOT / "data" / "auto_runs"))


def _tools_of(agent: str) -> dict[str, dict] | None:
    """{tool_name: {inputSchema}} for a running agent (None when the agent is unknown or not started)."""
    try:
        s = MANAGER.get(agent)
    except KeyError:
        return None
    return {t["name"]: t for t in s.tools} if s.tools else None


AUTO = AutoService(RUNNER, AUTO_DIR, _tools_of)
PAPERS = PaperAutomation(PAPER_RUNS_DIR, AGENTS, MANAGER)
MANUSCRIPTS = ManuscriptService()
RESEARCH = ResearchInventory(agents=AGENTS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    await MANAGER.start_all()
    try:
        yield
    finally:
        await PAPERS.close()
        await MANUSCRIPTS.close()
        await MANAGER.stop_all()


app = FastAPI(title="Paper2Agent Studio", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.include_router(create_manuscript_router(MANUSCRIPTS, RESEARCH, RUNNER))


def _safe_path(p: str) -> Path:
    rp = Path(p).expanduser().resolve()
    if not any(rp.is_relative_to(r.resolve()) for r in SERVE_ROOTS):
        raise HTTPException(403, "path outside the allowed roots")
    if not rp.exists():
        raise HTTPException(404, "file not found")
    return rp


@app.get('/api/paper-runs/capabilities')
async def paper_capabilities():
    return PAPERS.capabilities()


@app.post('/api/paper-runs', status_code=202)
async def upload_paper(file: UploadFile = File(...), repository: str = Form(''), goal: str = Form('')):
    filename = Path(file.filename or '').name
    if not filename.lower().endswith('.pdf'):
        raise HTTPException(400, '논문 PDF 파일을 선택해 주세요.')
    if len(goal) > 2000 or len(repository) > 500:
        raise HTTPException(400, '추가 요청은 2,000자, 저장소 주소는 500자 이내로 입력해 주세요.')
    try:
        repository = repository_url(repository) if repository.strip() else ''
    except ValueError as error:
        raise HTTPException(400, str(error))
    if PAPERS.capabilities()['active_runs'] >= 10:
        raise HTTPException(429, '생성 대기 작업이 많습니다. 기존 작업이 완료된 후 업로드해 주세요.')
    folder = PAPERS.root / uuid.uuid4().hex[:12]
    folder.mkdir(parents=True)
    try:
        total = 0
        with (folder / 'source.pdf').open('wb') as target:
            while chunk := await file.read(1024 * 1024):
                if total == 0 and not chunk.startswith(b'%PDF-'):
                    raise HTTPException(400, 'PDF 형식이 아닙니다. 원본 PDF를 업로드해 주세요.')
                total += len(chunk)
                if total > MAX_UPLOAD_BYTES:
                    raise HTTPException(413, '최대 30 MB까지 업로드할 수 있습니다.')
                target.write(chunk)
        if not total:
            raise HTTPException(400, '빈 파일은 업로드할 수 없습니다.')
        return PAPERS.create(folder, filename[:180], repo=repository, goal=goal.strip())
    except BaseException:
        shutil.rmtree(folder, ignore_errors=True)
        raise
    finally:
        await file.close()


@app.get('/api/paper-runs')
async def list_paper_runs(limit: int = Query(30, ge=1, le=100)):
    return PAPERS.list(limit)


def _paper_run(run_id):
    run = PAPERS.get(run_id)
    if not run:
        raise HTTPException(404, '논문 생성 작업을 찾을 수 없습니다.')
    return run


@app.get('/api/paper-runs/{run_id}')
async def get_paper_run(run_id: str):
    return _paper_run(run_id)


@app.post('/api/paper-runs/{run_id}/cancel')
async def cancel_paper_run(run_id: str):
    _paper_run(run_id)
    try:
        return await PAPERS.cancel(run_id)
    except ValueError as error:
        raise HTTPException(409, str(error))


class PaperRetryIn(BaseModel):
    repository: str | None = Field(default=None, max_length=500)
    goal: str | None = Field(default=None, max_length=2000)


@app.post('/api/paper-runs/{run_id}/retry', status_code=202)
async def retry_paper_run(run_id: str, body: PaperRetryIn):
    _paper_run(run_id)
    try:
        return PAPERS.retry(run_id, repo=body.repository, goal=body.goal)
    except ValueError as error:
        raise HTTPException(409, str(error))


@app.get("/api/agents")
async def list_agents():
    out = []
    for name, spec in AGENTS.items():
        s = MANAGER.get(name)
        out.append({"name": name, "status": s.status, "error": s.error, "n_tools": len(s.tools),
                    "tools": [t["name"] for t in s.tools], "display": spec.display, "package_dir": str(spec.package_dir),
                    "has_paper": spec.skill_dir is not None, "skill": spec.display.get("skill")})
    return out


@app.get("/api/agents/{name}/tools")
async def agent_tools(name: str):
    try:
        s = MANAGER.get(name)
    except KeyError:
        raise HTTPException(404, "unknown agent")
    if s.status != "running":
        try:
            await s.start()
        except Exception as e:
            raise HTTPException(503, f"agent not running: {e}")
    return {"agent": name, "tools": s.tools}


@app.post("/api/agents/{name}/restart")
async def agent_restart(name: str):
    try:
        s = MANAGER.get(name)
    except KeyError:
        raise HTTPException(404, "unknown agent")
    await s.stop()
    try:
        await s.start()
    except Exception as e:
        s.status, s.error = "error", str(e)
        raise HTTPException(503, str(e))
    return {"agent": name, "status": s.status, "n_tools": len(s.tools)}


@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in (file.filename or "upload"))
    dest = UPLOAD_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}_{uuid.uuid4().hex[:6]}_{safe}"
    with dest.open("wb") as fh:
        shutil.copyfileobj(file.file, fh)
    from .convert import convert_upload
    conv = await asyncio.to_thread(convert_upload, dest)
    return {"path": str(dest), "name": safe, "bytes": dest.stat().st_size, **conv}


@app.get("/api/samples")
async def samples():
    """Sample inputs that ship with the working projects (so a first click works without uploading)."""
    out: dict[str, list[dict[str, Any]]] = {}
    for name, spec in AGENTS.items():
        # <project>/dist/<x>-agent/mcp/<pkg>  ->  <project>
        pd = spec.package_dir
        proj = next((a for a in pd.parents if (a / 'data').is_dir() and (a / 'reports').is_dir()), pd)
        items: list[dict[str, Any]] = []
        cands = {
            "MedSAM": [("data/MedSAM_checkpoints/test_demo/imgs", "*.npz", "2D/3D demo (npz with imgs+boxes)"), ("data/MedSAM_checkpoints/test_demo/gts", "*.npz", "ground truth"),
                       ("dist/medsam-agent/mcp/MedSAM-mcp/repo/MedSAM/assets", "img_demo.png", "abdomen CT slice (box [95,255,190,350])"), ("data/MedSAM_checkpoints", "FLARE22_Tr_0046_0000.nii.gz", "abdominal CT volume")],
            "MedMNIST": [("data/medmnist", "*.npz", "MedMNIST dataset npz (data_root)")],
            "Cellpose": [("data/samples", "img*.png", "cellpose.org sample image"), ("data/samples", "rgb_3D.tif", "3D stack (channels [2,1], diameter 25)")],
            "nnUNet": [("data/msd", "Task04_Hippocampus", "MSD task folder (convert_msd_dataset)"), ("data/nnUNet_raw", "Dataset*", "nnU-Net raw dataset folder"),
                       ("data/nnUNet_raw/Dataset004_Hippocampus/imagesTs", "hippocampus_00*.nii.gz", "unlabelled test image (predict)"),
                       ("data/nnUNet_results/Dataset004_Hippocampus", "nnUNetTrainer_5epochs__nnUNetPlans__*", "trained model folder (5-epoch debug)"),
                       ("data/nnUNet_results/Dataset004_Hippocampus/nnUNetTrainer_5epochs__nnUNetPlans__3d_fullres/crossval_results_folds_0", "postprocessing.pkl", "postprocessing decision (apply_postprocessing)")],
            "HDBET": [("data/samples", "*_T1w.nii.gz", "MNI152 T1w template with skull (TemplateFlow)"), ("data/samples", "*_T2w.nii.gz", "MNI152 T2w template with skull (TemplateFlow)"),
                      ("data/samples", "*_desc-brain_mask.nii.gz", "reference brain mask (ground truth)"),
                      ("data/nfbs/subjects", "*/*_T1w.nii.gz", "NFBS subject T1w (skull)"), ("data/nfbs/subjects", "*/*_T1w_brainmask.nii.gz", "NFBS reference brain mask (ground truth)")],
        }.get(name, [])
        for rel, pat, desc in cands:
            d = proj / rel
            if d.is_dir():
                for p in sorted(d.glob(pat))[:16]:
                    items.append({"path": str(p), "name": p.name, "description": desc, "bytes": p.stat().st_size, "is_dir": p.is_dir()})
        out[name] = items
    return out


class JobIn(BaseModel):
    agent: str
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


@app.post("/api/jobs")
async def create_job(body: JobIn):
    try:
        s = MANAGER.get(body.agent)
    except KeyError:
        raise HTTPException(404, "unknown agent")
    if body.tool not in {t["name"] for t in s.tools}:
        raise HTTPException(400, f"unknown tool {body.tool!r} for agent {body.agent}")
    args = {k: v for k, v in body.arguments.items() if v is not None and v != ""}
    return RUNNER.submit(body.agent, body.tool, args).to_dict()


@app.get("/api/jobs")
async def list_jobs(limit: int = 50):
    return RUNNER.list(limit)


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    j = RUNNER.jobs.get(job_id)
    if not j:
        raise HTTPException(404, "unknown job")
    return j.to_dict()


def _render_labels(rp: Path) -> bytes:
    """Colorise an integer label image (masks) so it is viewable in the browser.
    Also handles .npy label arrays and 16-bit/float images by min-max scaling."""
    import io
    import numpy as np
    from PIL import Image
    if rp.suffix.lower() == ".npy":
        arr = np.load(str(rp), allow_pickle=False)
    else:
        arr = np.asarray(Image.open(str(rp)))
    if arr.ndim == 3 and arr.shape[-1] in (3, 4):  # already RGB(A): only rescale if not uint8
        if arr.dtype != np.uint8:
            arr = (255 * (arr - arr.min()) / max(1e-9, float(arr.max() - arr.min()))).astype(np.uint8)
        img = Image.fromarray(arr)
    else:
        if arr.ndim > 2:
            arr = arr.reshape(-1, *arr.shape[-2:])[0]
        if np.issubdtype(arr.dtype, np.integer) and arr.max() > 0 and arr.max() < 1_000_000 and len(np.unique(arr[::4, ::4])) < 5000:
            lab = arr.astype(np.int64)
            rng = np.random.default_rng(7)
            lut = rng.integers(40, 255, size=(int(lab.max()) + 1, 3), dtype=np.uint8)
            lut[0] = 0
            img = Image.fromarray(lut[lab])
        else:
            a = arr.astype(np.float32)
            a = 255 * (a - a.min()) / max(1e-9, float(a.max() - a.min()))
            img = Image.fromarray(a.astype(np.uint8))
    buf = io.BytesIO(); img.save(buf, format="PNG"); return buf.getvalue()


@app.get("/api/files")
async def get_file(path: str = Query(...), download: bool = False, render: str | None = None):
    rp = _safe_path(path)
    if rp.is_dir():
        return {"dir": str(rp), "entries": [{"name": p.name, "path": str(p), "is_dir": p.is_dir(), "bytes": p.stat().st_size if p.is_file() else None} for p in sorted(rp.iterdir())]}
    if render == "labels" and rp.suffix.lower() in {".png", ".tif", ".tiff", ".npy"} and rp.stat().st_size < 200_000_000:
        try:
            data = await asyncio.to_thread(_render_labels, rp)
            return Response(content=data, media_type="image/png")
        except Exception as e:  # fall back to the raw file
            log.warning("label render failed for %s: %s", rp, e)
    mt, _ = mimetypes.guess_type(str(rp))
    return FileResponse(str(rp), media_type=mt or "application/octet-stream", filename=rp.name if download else None)


@app.get("/api/files/preview")
async def preview_file(path: str = Query(...), max_chars: int = 20000):
    """Text/JSON/CSV preview, or a numeric summary for .npy/.npz so the UI can show something for any artifact."""
    rp = _safe_path(path)
    suf = rp.suffix.lower()
    if suf in (".json", ".txt", ".csv", ".md", ".log", ".tsv"):
        text = rp.read_text(encoding="utf-8", errors="replace")
        return {"kind": "text", "text": text[:max_chars], "truncated": len(text) > max_chars}
    if suf in (".npy", ".npz"):
        import numpy as np
        d = np.load(rp, allow_pickle=False) if suf == ".npy" else np.load(rp)
        arrays = {"array": d} if suf == ".npy" else {k: d[k] for k in d.files}
        summ = {}
        for k, a in arrays.items():
            try:
                info = {"shape": list(a.shape), "dtype": str(a.dtype)}
                if a.dtype.kind in "iuf" and a.size:
                    info.update({"min": float(a.min()), "max": float(a.max()), "n_unique": int(min(len(np.unique(a)), 1_000_000)) if a.size < 5_000_000 else None})
                summ[k] = info
            except Exception as e:
                summ[k] = {"error": str(e)}
        return {"kind": "array", "arrays": summ}
    return {"kind": "binary", "bytes": rp.stat().st_size, "mime": mimetypes.guess_type(str(rp))[0]}


def _paper_directory(skill: str) -> Path:
    for spec in AGENTS.values():
        if spec.display.get('skill') == skill and spec.skill_dir and spec.skill_dir.is_dir():
            return spec.skill_dir
    d = SKILLS_DIR / skill
    if not d.resolve().is_relative_to(SKILLS_DIR.resolve()) or not d.is_dir() or not (d / 'SKILL.md').exists():
        raise HTTPException(404, "unknown paper skill")
    return d


@app.get("/api/papers/{skill}")
async def paper(skill: str):
    d = _paper_directory(skill)
    return paper_overview(d)


@app.get("/api/papers/{skill}/section")
async def paper_sec(skill: str, file: str = "paper.md", heading: str = ""):
    d = _paper_directory(skill)
    try:
        return paper_section(d, file, heading)
    except KeyError:
        raise HTTPException(404, "heading not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/papers/{skill}/search")
async def paper_q(skill: str, q: str, limit: int = 12):
    d = _paper_directory(skill)
    if not d.is_dir():
        raise HTTPException(404, "unknown paper skill")
    return {"skill": skill, "query": q, "hits": paper_search(d, q, limit)}


@app.get("/api/papers/{skill}/asset/{cat}/{name}")
async def paper_asset(skill: str, cat: str, name: str):
    root = (_paper_directory(skill) / 'assets').resolve()
    p = (root / cat / name).resolve()
    if not p.is_relative_to(root) or not p.is_file():
        raise HTTPException(404, "asset not found")
    return FileResponse(str(p))


class AutoPlanIn(BaseModel):
    path: str


class AutoRunIn(BaseModel):
    path: str
    recipe_id: str | None = None
    project: str | None = None


def _auto_input(p: str) -> str:
    """Inputs must be a MedMNIST flag or a path under the served roots (uploads, data, agent workspaces)."""
    p = (p or "").strip()
    if not p:
        raise HTTPException(400, "path is required")
    if p.lower() in MEDMNIST_FLAGS and not Path(p).exists():
        return p.lower()
    return str(_safe_path(p))


@app.post("/api/auto/plan")
async def auto_plan(body: AutoPlanIn):
    path = _auto_input(body.path)
    return await asyncio.to_thread(AUTO.plan, path)


@app.post("/api/auto/run")
async def auto_run(body: AutoRunIn):
    path = _auto_input(body.path)
    planned = await asyncio.to_thread(AUTO.plan, path)  # detection may read a volume / probe a video: keep it off the loop
    try:
        run = AUTO.start(path, body.recipe_id, body.project, planned)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"run_id": run["id"], **run}


@app.get("/api/auto/runs")
async def auto_runs(limit: int = 30):
    return AUTO.list(limit)


@app.get("/api/auto/runs/{run_id}")
async def auto_run_get(run_id: str):
    r = AUTO.get(run_id)
    if not r:
        raise HTTPException(404, "unknown run")
    return {"run_id": r["id"], **r}


@app.get("/api/stats")
async def stats():
    gpus: list[dict[str, Any]] = []
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=index,name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=5).stdout
        for line in out.strip().splitlines():
            i, n, u, t, util = [x.strip() for x in line.split(",")]
            gpus.append({"index": int(i), "name": n, "mem_used_mb": int(u), "mem_total_mb": int(t), "util": int(util)})
    except Exception:
        pass
    jobs = RUNNER.jobs.values()
    return {"gpus": gpus, "agents": {n: MANAGER.get(n).status for n in AGENTS}, "jobs_total": len(RUNNER.jobs),
            "jobs_running": sum(1 for j in jobs if j.status == "running"), "jobs_done": sum(1 for j in jobs if j.status == "done"), "time": time.time()}


if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
