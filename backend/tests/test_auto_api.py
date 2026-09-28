"""/api/auto/* through the FastAPI app with no MCP servers (empty agent registry) and a fake job runner."""
from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix="p2a-auto-api-"))
os.environ["PAPER2AGENT_CLAUDE_JSON"] = str(_TMP / "no-claude.json")      # no agents -> lifespan starts nothing
os.environ["PAPER2AGENT_ALLOWED_ROOTS"] = str(_TMP)
os.environ["PAPER2AGENT_UPLOAD_DIR"] = str(_TMP / "uploads")
os.environ["PAPER2AGENT_JOB_DIR"] = str(_TMP / "jobs")
os.environ["PAPER2AGENT_AUTO_DIR"] = str(_TMP / "auto_runs")

from fastapi.testclient import TestClient  # noqa: E402

from app import main  # noqa: E402
from tests.conftest import blob_image, write_png  # noqa: E402
from tests.test_auto_runner import FakeRunner, _tools_lookup  # noqa: E402


@pytest.fixture
def client(tool_schemas):
    main.AUTO.runner = FakeRunner(_TMP)
    main.AUTO.tools_lookup = _tools_lookup(tool_schemas)
    main.AUTO.poll_s = 0.01
    with TestClient(main.app) as c:
        yield c


def test_plan_and_run_via_api(client):
    img = write_png(_TMP / "cells_a.png", blob_image(rgb=True))
    r = client.post("/api/auto/plan", json={"path": str(img)})
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["kind"] == "microscopy_2d" and p["recipes"][0]["id"] == "microscopy_cellpose"
    assert p["recipes"][0]["steps"][0]["tool"] == "cellpose_estimate_diameter"

    r = client.post("/api/auto/run", json={"path": str(img), "recipe_id": "microscopy_cellpose", "project": "proj-1"})
    assert r.status_code == 200, r.text
    run = r.json()
    assert run["run_id"] and run["status"] in ("queued", "running") and run["project"] == "proj-1"
    for _ in range(200):
        g = client.get(f"/api/auto/runs/{run['run_id']}").json()
        if g["status"] not in ("queued", "running"):
            break
        import time
        time.sleep(0.02)
    assert g["status"] == "done", g["warnings"]
    assert len(g["jobs"]) == 4 and all(s["status"] == "done" for s in g["steps"])
    assert Path(g["summary_path"]).exists() and Path(g["report_path"]).exists()
    lst = client.get("/api/auto/runs").json()
    assert lst[0]["id"] == run["run_id"] and lst[0]["status"] == "done"
    # the report is served through /api/files (data dir is a served root)
    f = client.get("/api/files", params={"path": g["report_path"]})
    assert f.status_code == 200 and "cellpose_segment_image" in f.text


def test_plan_medmnist_flag(client):
    p = client.post("/api/auto/plan", json={"path": "pathmnist"}).json()
    assert p["kind"] == "medmnist_flag" and p["recipes"][0]["steps"][1]["arguments"]["epochs"] == 2


def test_plan_rejects_outside_roots(client):
    assert client.post("/api/auto/plan", json={"path": "/etc/passwd"}).status_code == 403
    assert client.post("/api/auto/plan", json={"path": str(_TMP / "missing.nii.gz")}).status_code == 404
    assert client.post("/api/auto/plan", json={"path": ""}).status_code == 400


def test_run_unknown_kind_is_400(client):
    p = _TMP / "weird.bin"
    p.write_bytes(b"\0" * 10)
    r = client.post("/api/auto/run", json={"path": str(p)})
    assert r.status_code == 400 and "no recipe" in r.json()["detail"]
    assert client.get("/api/auto/runs/nope").status_code == 404
