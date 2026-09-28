"""HTTP interface for manuscript jobs and the read-only research inventory."""
from __future__ import annotations

import asyncio
import json
import re
import shutil
import uuid
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, ValidationError

from .manuscript_documents import ALLOWED_EXTENSIONS, MAX_FILE


class ManuscriptOptions(BaseModel):
    study_type: Literal['medical_ai', 'prediction', 'imaging', 'diagnostic', 'trial', 'review', 'other'] = 'medical_ai'
    journal: str = Field(default='', max_length=250)
    journal_requirements: str = Field(default='', max_length=14000)
    language: Literal['English', 'Korean'] = 'English'
    target_words: int = Field(default=2500, ge=1000, le=6000)
    instructions: str = Field(default='', max_length=4000)
    job_ids: list[str] = Field(default_factory=list, max_length=5)
    resource_paths: list[str] = Field(default_factory=list, max_length=5)


async def save_upload(folder, upload, role):
    original = Path((upload.filename or '').replace('\\', '/')).name
    suffix = Path(original).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, 'PDF·DOCX·MD·TXT·CSV·TSV·JSON 형식의 자료를 선택해 주세요.')
    path = folder / (uuid.uuid4().hex[:12] + suffix)
    total = 0
    try:
        with path.open('wb') as dest:
            while chunk := await upload.read(1024 * 1024):
                if total == 0 and suffix == '.pdf' and not chunk.startswith(b'%PDF-'):
                    raise HTTPException(400, 'PDF 형식이 아닙니다.')
                if total == 0 and suffix == '.docx' and not chunk.startswith(b'PK'):
                    raise HTTPException(400, 'DOCX 형식이 아닙니다.')
                total += len(chunk)
                if total > MAX_FILE:
                    raise HTTPException(413, '파일당 최대 30 MB입니다.')
                dest.write(chunk)
        if not total:
            raise HTTPException(400, '빈 자료는 업로드할 수 없습니다.')
        return {'path': str(path), 'name': original[:200], 'role': role}
    finally:
        await upload.close()


def create_manuscript_router(service, inventory, runner):
    router = APIRouter(prefix='/api')

    @router.get('/research/inventory')
    async def research_inventory():
        return inventory.get() or {'scanned_at': None, 'projects': [], 'artifacts': []}

    @router.post('/research/inventory/scan')
    async def scan_inventory():
        if inventory.lock.locked():
            raise HTTPException(409, '연구 폴더 조사 중입니다. 잠시 후 새로고침해 주세요.')
        return await inventory.refresh()

    @router.get('/research/journals')
    async def journals(q: str = Query('', max_length=250)):
        try:
            return await asyncio.to_thread(service.corpus.journals, q)
        except Exception:
            raise HTTPException(503, '로컬 저널 등급 수집본을 읽지 못했습니다.')

    @router.get('/manuscripts/capabilities')
    async def capabilities():
        return service.capabilities()

    @router.get('/manuscripts')
    async def runs(limit: int = Query(30, ge=1, le=100)):
        return service.list(limit)

    @router.post('/manuscripts', status_code=202)
    async def create(manuscript: UploadFile = File(...), results: list[UploadFile] = File(default=[]),
                     options: str = Form('{}')):
        try:
            opts = ManuscriptOptions.model_validate_json(options).model_dump()
        except (ValueError, ValidationError):
            raise HTTPException(400, '연구 유형·언어·목표 분량·입력 옵션을 확인해 주세요.')
        if 1 + len(results) + len(opts['job_ids']) + len(opts['resource_paths']) > 10:
            raise HTTPException(400, '초안과 기존 결과는 합쳐서 최대 10개입니다.')
        if service.capabilities()['active_runs'] >= 5:
            raise HTTPException(429, '대기 중인 원고가 많습니다. 기존 작업이 완료된 후 다시 시도해 주세요.')
        folder = service.root / uuid.uuid4().hex[:12]
        folder.mkdir(parents=True)
        inputs = folder / 'inputs'; inputs.mkdir()
        try:
            files = [await save_upload(inputs, manuscript, 'manuscript')]
            for file in results:
                files.append(await save_upload(inputs, file, 'results'))
            for job_id in opts.pop('job_ids'):
                job = runner.jobs.get(job_id)
                if not job or job.status != 'done':
                    raise HTTPException(400, '완료된 에이전트 실행 결과만 사용할 수 있습니다.')
                # An immutable result snapshot, never a fresh experiment.
                payload = job.to_dict()
                text = json.dumps({'job_id': job_id, 'agent': job.agent, 'tool': job.tool,
                                   'arguments': payload.get('arguments', {}), 'result': payload.get('result'),
                                   'finished_at': payload.get('finished_at')}, ensure_ascii=False, indent=2)
                if len(text.encode()) > 2_000_000:
                    raise HTTPException(413, '실행 결과가 너무 큽니다. 요약 CSV/JSON을 업로드해 주세요.')
                path = inputs / (uuid.uuid4().hex[:12] + '.json')
                path.write_text(text, encoding='utf-8')
                files.append({'path': str(path), 'name': f'{job.agent} · {job.tool} · {job_id}.json', 'role': 'results'})
            for value in opts.pop('resource_paths'):
                try:
                    path = inventory.resolve_artifact(value)
                except ValueError as error:
                    raise HTTPException(400, str(error))
                dest = inputs / (uuid.uuid4().hex[:12] + path.suffix.lower())
                await asyncio.to_thread(shutil.copyfile, path, dest)
                files.append({'path': str(dest), 'name': path.name, 'role': 'results'})
            return service.create(folder, files, opts)
        except BaseException:
            shutil.rmtree(folder, ignore_errors=True)
            raise
        finally:
            await manuscript.close()
            for file in results:
                await file.close()

    def get_run(run_id):
        run = service.get(run_id)
        if not run:
            raise HTTPException(404, '원고 작업을 찾을 수 없습니다.')
        return run

    @router.get('/manuscripts/{run_id}')
    async def get(run_id: str):
        return get_run(run_id)

    @router.post('/manuscripts/{run_id}/cancel')
    async def cancel(run_id: str):
        get_run(run_id)
        try:
            return await service.cancel(run_id)
        except ValueError as error:
            raise HTTPException(409, str(error))

    @router.post('/manuscripts/{run_id}/revise', status_code=202)
    async def revise(run_id: str, files: list[UploadFile] = File(default=[]), instructions: str = Form(''),
                     journal: str | None = Form(None), journal_requirements: str | None = Form(None)):
        run = get_run(run_id)
        if run['status'] in {'queued', 'running'}:
            raise HTTPException(409, '이미 원고 작성이 진행 중입니다.')
        if len(instructions) > 4000 or len(run['files']) + len(files) > 10:
            raise HTTPException(400, '추가 요청은 4,000자, 자료는 합쳐서 10개 이내로 입력해 주세요.')
        changes = {k: v for k, v in {'journal': journal, 'journal_requirements': journal_requirements}.items() if v is not None}
        try:
            ManuscriptOptions.model_validate({**run['options'], **changes})
        except ValueError:
            raise HTTPException(400, '저널명은 250자, 투고 규정은 14,000자 이내로 입력해 주세요.')
        folder = service.root / run_id / 'inputs' / uuid.uuid4().hex[:12]
        folder.mkdir(parents=True)
        try:
            items = [await save_upload(folder, file, 'results') for file in files]
            return service.revise(run_id, items, instructions.strip(), changes)
        except BaseException:
            shutil.rmtree(folder, ignore_errors=True)
            raise
        finally:
            for file in files:
                await file.close()

    return router
