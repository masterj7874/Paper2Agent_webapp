"""Real PDF parsing and MCP calls; only the external model is replaced in automated tests."""
import asyncio
import json
import os
import sys
import sysconfig
import time
import zipfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app import jobs as jobs_module
from app.jobs import JobRunner
from app.mcp_manager import MCPManager
from app.paper_automation import PaperAutomation, validate_manifest
from app.paper_documents import extract_pdf, repository_url, validate_analysis
from app.paper_worker import WorkerError


def pdf_bytes(lines=None):
    lines = lines or ['A Source Grounded Research Agent', 'Abstract',
                      'This paper studies source grounded retrieval from research documents.',
                      'The method ranks passages by query terms and returns page citations.',
                      'Experiments used a small synthetic collection of twenty documents.',
                      'The study does not evaluate clinical outcomes or external validity.']
    escape = lambda s: s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    stream = ('BT /F1 12 Tf 50 750 Td 18 TL ' + ' T* '.join(f'({escape(line)}) Tj' for line in lines) + ' ET').encode()
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               f'<< /Length {len(stream)} >>\nstream\n'.encode() + stream + b'\nendstream']
    body = b'%PDF-1.4\n'
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(body))
        body += f'{index} 0 obj\n'.encode() + obj + b'\nendobj\n'
    start = len(body)
    body += f'xref\n0 {len(objects) + 1}\n0000000000 65535 f \n'.encode()
    body += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    return body + f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF'.encode()


def analysis():
    return {'title': 'A Source Grounded Research Agent', 'summary': '연구 문서에서 페이지 근거를 반환하는 검색 방법을 연구합니다.',
            'methods': ['키워드 기반 검색'], 'limitations': ['작은 합성 데이터셋만 평가했습니다.'],
            'repository_url': None, 'evidence': [{'claim': '페이지 근거를 반환합니다.', 'page': 1,
                                               'quote': 'The method ranks passages by query terms and returns page citations.'}]}


class FakeWorker:
    executable = 'claude'
    async def run(self, prompt, cwd, **kwargs):
        return analysis()


@pytest.fixture
def client(tmp_path, monkeypatch):
    agents = {}
    manager = MCPManager(agents)
    saved = {}
    service = PaperAutomation(tmp_path / 'runs', agents, manager, worker=FakeWorker(),
                              persist_agent=lambda spec: saved.update({spec.name: spec}))
    monkeypatch.setattr(main, 'AGENTS', agents)
    monkeypatch.setattr(main, 'MANAGER', manager)
    monkeypatch.setattr(main, 'PAPERS', service)
    monkeypatch.setattr(main, 'SERVE_ROOTS', [tmp_path])
    monkeypatch.setattr(jobs_module, 'JOB_DIR', tmp_path / 'jobs')
    monkeypatch.setattr(main, 'RUNNER', JobRunner(manager))
    with TestClient(main.app) as c:
        c.saved = saved
        yield c


def wait_terminal(client, run_id):
    for _ in range(300):
        value = client.get('/api/paper-runs/' + run_id).json()
        if value['status'] not in ('queued', 'running'):
            return value
        time.sleep(.05)
    pytest.fail('paper pipeline did not terminate')


def test_upload_to_registered_real_mcp_and_download(client):
    response = client.post('/api/paper-runs', files={'file': ('paper.pdf', pdf_bytes(), 'application/pdf')})
    assert response.status_code == 202, response.text
    run = wait_terminal(client, response.json()['id'])
    assert run['status'] == 'ready', run.get('error')
    assert all(stage['status'] == 'done' for stage in run['stages'])
    assert run['verification']['tool_count'] == 3
    assert len(run['verification']['calls']) == 2
    name = run['agent_name']
    assert name in client.saved
    assert client.get('/api/agents').json()[0]['name'] == name
    tools = client.get('/api/agents/' + name + '/tools').json()['tools']
    assert {t['name'] for t in tools} == {'paper_overview', 'paper_page', 'paper_search'}
    job = client.post('/api/jobs', json={'agent': name, 'tool': 'paper_search', 'arguments': {'query': 'citations'}}).json()
    for _ in range(100):
        result = client.get('/api/jobs/' + job['id']).json()
        if result['status'] not in ('queued', 'running'):
            break
        time.sleep(.02)
    assert result['status'] == 'done', result
    assert result['result']['hits'][0]['page'] == 1
    assert 'citations' in result['result']['hits'][0]['text']
    skill = client.get('/api/agents').json()[0]['skill']
    assert client.get('/api/papers/' + skill).status_code == 200
    assert 'page citations' in client.get(f'/api/papers/{skill}/section').json()['markdown']
    for artifact in run['artifacts']:
        assert client.get('/api/files', params={'path': artifact['path']}).status_code == 200
    assert client.post('/api/paper-runs/' + run['id'] + '/retry', json={}).status_code == 409
    assert client.post('/api/paper-runs/' + run['id'] + '/cancel').status_code == 409


@pytest.mark.parametrize('filename,content,code', [('bad.txt', b'hello', 400), ('fake.pdf', b'not a PDF', 400), ('empty.pdf', b'', 400)])
def test_rejects_invalid_uploads_without_queueing(client, filename, content, code):
    response = client.post('/api/paper-runs', files={'file': (filename, content, 'application/pdf')})
    assert response.status_code == code
    assert client.get('/api/paper-runs').json() == []
    assert not list(main.PAPERS.root.glob('*'))


def test_size_limit_cleans_partial_upload(client, monkeypatch):
    monkeypatch.setattr(main, 'MAX_UPLOAD_BYTES', 20)
    assert client.post('/api/paper-runs', files={'file': ('large.pdf', pdf_bytes())}).status_code == 413
    assert not list(main.PAPERS.root.glob('*'))


def test_corrupt_pdf_fails_and_retry_does_not_register(client):
    response = client.post('/api/paper-runs', files={'file': ('broken.pdf', b'%PDF-1.4\nbroken')})
    run = wait_terminal(client, response.json()['id'])
    assert run['status'] == 'failed'
    assert not client.saved
    retry = client.post(f'/api/paper-runs/{run["id"]}/retry', json={})
    assert retry.status_code == 202
    run = wait_terminal(client, run['id'])
    assert run['status'] == 'failed' and run['attempt'] == 2


def test_worker_failure_and_cancel_queued_job(client):
    class FailingWorker:
        async def run(self, *args, **kwargs):
            raise WorkerError('로그인이 필요합니다.')
    main.PAPERS.worker = FailingWorker()
    response = client.post('/api/paper-runs', files={'file': ('paper.pdf', pdf_bytes())})
    run = wait_terminal(client, response.json()['id'])
    assert run['status'] == 'needs_input' and not client.saved
    class WaitingWorker:
        async def run(self, *args, **kwargs):
            await asyncio.sleep(60)
    main.PAPERS.worker = WaitingWorker()
    for _ in range(2):
        response = client.post('/api/paper-runs', files={'file': ('paper.pdf', pdf_bytes())})
    run_id = response.json()['id']
    assert client.post(f'/api/paper-runs/{run_id}/cancel').json()['status'] == 'cancelled'


@pytest.mark.parametrize('outcome', ['ready', 'blocked', 'tool_error'])
def test_code_generation_contract_and_real_validation(client, outcome, monkeypatch):
    from app import paper_automation
    skill = main.PAPERS.root.parent / 'fixture-skill.md'
    skill.write_text('Fixture skill. External generation is replaced in this test.')
    monkeypatch.setattr(paper_automation, 'PAPER2AGENT_SKILL', skill)
    class BuildingWorker:
        async def run(self, prompt, cwd, **kwargs):
            if not kwargs.get('build'):
                return analysis()
            if outcome == 'blocked':
                (cwd / 'agent_manifest.json').write_text(json.dumps({'status': 'blocked', 'reason': '모델 가중치가 필요합니다.'}))
                return {}
            bindir = cwd / '.venv/bin'
            bindir.mkdir(parents=True)
            (bindir / 'python').symlink_to(sys.executable)
            (bindir.parent / 'pyvenv.cfg').write_text(f'home = {sys.base_prefix}/bin\ninclude-system-site-packages = false\n')
            lib = cwd / f'.venv/lib/python{sys.version_info.major}.{sys.version_info.minor}'
            lib.mkdir(parents=True)
            (lib / 'site-packages').symlink_to(sysconfig.get_path('purelib'))
            # A tiny source implementation and real MCP wrapper, not a fake MCP client.
            (cwd / 'upstream.py').write_text('def average(values):\n    return sum(values) / len(values)\n')
            result = '{"error": "weights unavailable"}' if outcome == 'tool_error' else '{"mean": average(values)}'
            (cwd / 'server.py').write_text('from fastmcp import FastMCP\nfrom upstream import average\nmcp = FastMCP("Fixture")\n@mcp.tool()\ndef mean(values: list[float]) -> dict:\n    return ' + result + '\nmcp.run(transport="stdio", show_banner=False)\n')
            with zipfile.ZipFile(cwd / 'agent.zip', 'w') as archive:
                archive.write(cwd / 'server.py', 'server.py')
                archive.write(cwd / 'upstream.py', 'upstream.py')
            (cwd / 'agent_manifest.json').write_text(json.dumps({
                'status': 'ready', 'command': str(bindir / 'python'), 'args': ['server.py'], 'cwd': str(cwd),
                'delivery_zip': 'agent.zip', 'smoke_calls': [{'tool': 'mean', 'arguments': {'values': [1, 2, 3]}}]}))
            return {}
    main.PAPERS.worker = BuildingWorker()
    response = client.post('/api/paper-runs', files={'file': ('paper.pdf', pdf_bytes())},
                           data={'repository': 'https://github.com/example/research'})
    run = wait_terminal(client, response.json()['id'])
    expected = {'ready': 'ready', 'blocked': 'needs_input', 'tool_error': 'failed'}[outcome]
    assert run['status'] == expected, run.get('error')
    assert bool(client.saved) == (outcome == 'ready')
    if outcome == 'ready':
        assert run['agent_kind'] == 'research_code'
        assert run['verification']['calls'] == [{'tool': 'mean', 'status': 'passed'}]
    else:
        assert not main.MANAGER.sessions


def test_restore_marks_unfinished_runs_interrupted(tmp_path):
    folder = tmp_path / 'abc'
    folder.mkdir()
    record = {'id': 'abc', 'status': 'running', 'stages': [{'status': 'running'}]}
    (folder / 'run.json').write_text(json.dumps(record))
    service = PaperAutomation(tmp_path, {}, MCPManager({}))
    assert service.get('abc')['status'] == 'interrupted'
    assert json.loads((folder / 'run.json').read_text())['status'] == 'interrupted'


def test_extraction_and_citation_validation(tmp_path):
    pdf = tmp_path / 'paper.pdf'
    pdf.write_bytes(pdf_bytes())
    document = extract_pdf(pdf, tmp_path / 'paper.txt')
    assert document['page_count'] == 1 and len(document['sha256']) == 64
    assert validate_analysis(analysis(), document, None)['title']
    invalid = analysis()
    invalid['evidence'][0]['quote'] = 'Invented unsupported evidence.'
    with pytest.raises(ValueError, match='인용문'):
        validate_analysis(invalid, document, None)
    invalid = analysis()
    invalid['repository_url'] = 'https://github.com/someone/invented'
    with pytest.raises(ValueError, match='저장소'):
        validate_analysis(invalid, document, None)


@pytest.mark.parametrize('url', ['http://github.com/a/b', 'file:///tmp/a', 'https://github.com.evil.test/a/b',
                                 'https://user:secret@github.com/a/b', 'https://github.com/a/..', 'https://127.0.0.1/a/b'])
def test_reject_untrusted_repository_addresses(url):
    with pytest.raises(ValueError):
        repository_url(url)


def test_manifest_limits_commands_and_paths(tmp_path):
    workspace = tmp_path / 'work'
    bindir = workspace / '.venv/bin'
    bindir.mkdir(parents=True)
    (bindir / 'python').symlink_to(sys.executable)
    (bindir.parent / 'pyvenv.cfg').write_text('home = /usr/bin')
    (workspace / 'server.py').write_text('# server')
    with zipfile.ZipFile(workspace / 'agent.zip', 'w') as archive:
        archive.writestr('server.py', '# server')
    manifest = {'command': str(bindir / 'python'), 'args': ['server.py'], 'cwd': str(workspace),
                'delivery_zip': 'agent.zip', 'smoke_calls': [{'tool': 'test', 'arguments': {}}]}
    assert validate_manifest(manifest, workspace, 'test')[0].name == 'test'
    with pytest.raises(ValueError):
        validate_manifest({**manifest, 'command': '/bin/sh'}, workspace, 'test')
    (workspace / 'outside.py').symlink_to(tmp_path / 'outside.py')
    (tmp_path / 'outside.py').write_text('# outside')
    with pytest.raises(ValueError):
        validate_manifest({**manifest, 'args': ['outside.py']}, workspace, 'test')
    with pytest.raises(ValueError):
        validate_manifest({**manifest, 'env': {'LD_PRELOAD': '/tmp/bad.so'}}, workspace, 'test')


def test_path_prefix_is_not_authorization(client, tmp_path):
    sibling = tmp_path.parent / (tmp_path.name + '-other')
    sibling.mkdir(exist_ok=True)
    path = sibling / 'private.txt'
    path.write_text('test fixture')
    assert client.get('/api/files', params={'path': str(path)}).status_code == 403
