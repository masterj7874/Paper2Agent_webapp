"""Real file parsing/export/SQLite; the paid writer is replaced in automated tests."""
import asyncio
import copy
import json
import sqlite3
import time
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest
from docx import Document
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.jobs import Job
from app.manuscript_api import ManuscriptOptions, create_manuscript_router
from app.manuscript_documents import (CHECKS, SECTIONS, bibtex, export_docx, extract_source,
    markdown, validate_manuscript, validate_review)
from app.manuscript_service import ManuscriptService
from app.research_resources import ResearchCorpus, ResearchInventory
from tests.test_paper_automation import pdf_bytes

TEXT = 'This synthetic software validation used 42 records. Accuracy was 0.75. No clinical outcomes were evaluated.'


def draft():
    return {'title': 'Synthetic software validation', 'changes': ['문단별 근거를 연결했습니다.'], 'sections': [
        {'key': key, 'heading': key.title(), 'paragraphs': [
            {'text': TEXT, 'kind': 'observed', 'evidence': [{'source_id': 'S1', 'quote': TEXT}]}]}
        for key in SECTIONS]}


def review():
    return {'summary': '테스트 원고의 자료가 부족합니다.', 'checks': [
        {'id': key, 'status': 'satisfied', 'explanation': '제공된 발췌와 일치합니다.', 'manuscript_quote': TEXT,
         'action': ''} for key in CHECKS], 'revision_instructions': ['허용된 근거만 유지합니다.']}


class FixtureWriter:
    executable = 'claude'
    def __init__(self):
        self.calls = 0
    async def run(self, prompt, cwd, **kwargs):
        self.calls += 1
        title = kwargs['schema']['title']
        if title == 'ResearchBrief':
            return {'title': 'Synthetic software validation', 'research_question': 'A test only',
                    'contribution': '테스트 자료', 'search_query': 'synthetic validation',
                    'observed_facts': [{'source_id': 'S1', 'quote': TEXT}], 'missing_evidence': []}
        if title == 'Manuscript':
            return draft()
        return review()


class EmptyCorpus:
    db = Path('/no-test-corpus.sqlite')
    def search(self, query):
        return []
    def journals(self, query):
        return []
    def journal(self, title):
        return None
    def guideline(self):
        return None


@pytest.fixture
def client(tmp_path):
    service = ManuscriptService(tmp_path / 'runs', worker=FixtureWriter(), corpus=EmptyCorpus())
    inventory = ResearchInventory(tmp_path / 'inventory', roots=[tmp_path / 'research'])
    jobs = {'completed': Job('completed', 'Fixture', 'measure', {}, status='done', result={'accuracy': .75}),
            'running': Job('running', 'Fixture', 'measure', {}, status='running')}
    @asynccontextmanager
    async def lifespan(app):
        yield
        await service.close()
    app = FastAPI(lifespan=lifespan)
    app.include_router(create_manuscript_router(service, inventory, SimpleNamespace(jobs=jobs)))
    with TestClient(app) as c:
        c.service, c.inventory = service, inventory
        yield c


def wait_run(client, run_id):
    for _ in range(300):
        run = client.get('/api/manuscripts/' + run_id).json()
        if run['status'] not in {'queued', 'running'}:
            return run
        time.sleep(.01)
    pytest.fail('manuscript did not terminate')


def submit(client, **kwargs):
    return client.post('/api/manuscripts', files={'manuscript': ('draft.md', TEXT)}, **kwargs)


def test_complete_pipeline_exports_real_word_and_preserves_versions(client):
    response = submit(client)
    assert response.status_code == 202, response.text
    run = wait_run(client, response.json()['id'])
    assert run['status'] == 'needs_evidence', run.get('error')
    assert all(s['status'] == 'done' for s in run['stages'])
    assert client.service.worker.calls == 5  # brief, draft, independent review, revision, re-review
    assert run['readiness']['author_review_required']
    assert next(c for c in run['review']['checks'] if c['id'] == 'journal')['status'] == 'missing'
    files = {Path(a['path']).name: Path(a['path']) for a in run['artifacts']}
    assert len(files) == 7
    word = Document(files['manuscript.docx'])
    assert any(p.text == TEXT for p in word.paragraphs)
    with zipfile.ZipFile(files['manuscript-package.zip']) as z:
        assert {'manuscript.docx', 'draft-v1.json', 'draft-v2.json', 'review-v1.json', 'review.json', 'evidence.json'} <= set(z.namelist())
    previous = files['manuscript.docx'].read_bytes()
    response = client.post(f'/api/manuscripts/{run["id"]}/revise',
                           files={'files': ('results.csv', 'metric,value\naccuracy,0.75\n')},
                           data={'instructions': '추가 표를 유지하세요.', 'journal': 'Test Journal',
                                 'journal_requirements': 'Provided test submission requirements.'})
    assert response.status_code == 202
    new = wait_run(client, run['id'])
    assert new['attempt'] == 2 and len(new['history']) == 1
    assert new['options']['journal'] == 'Test Journal'
    assert new['options']['journal_requirements'].startswith('Provided')
    assert files['manuscript.docx'].read_bytes() == previous
    doc = Document(next(a['path'] for a in new['artifacts'] if a['path'].endswith('.docx')))
    assert doc.tables[0].cell(1, 1).text == '0.75'
    assert new['files'][0]['name'] == 'draft.md' and len(new['files']) == 2


@pytest.mark.parametrize('filename,value', [('bad.exe', b'x'), ('empty.md', b''), ('fake.pdf', b'wrong'), ('fake.docx', b'wrong')])
def test_upload_validation_cleans_files(client, filename, value):
    r = client.post('/api/manuscripts', files={'manuscript': (filename, value)})
    assert r.status_code == 400
    assert not list(client.service.root.glob('*'))


def test_invalid_options_and_size_limit(client, monkeypatch):
    assert submit(client, data={'options': '{broken'}).status_code == 400
    assert submit(client, data={'options': json.dumps({'language': 'nonsense'})}).status_code == 400
    monkeypatch.setattr('app.manuscript_api.MAX_FILE', 10)
    assert submit(client).status_code == 413
    assert not list(client.service.root.glob('*'))


def test_existing_job_snapshot_only_accepts_done_jobs(client):
    r = submit(client, data={'options': json.dumps({'job_ids': ['running']})})
    assert r.status_code == 400
    r = submit(client, data={'options': json.dumps({'job_ids': ['completed']})})
    run = wait_run(client, r.json()['id'])
    value = json.loads(Path(run['files'][1]['path']).read_text())
    assert value['result']['accuracy'] == .75 and value['job_id'] == 'completed'


def test_bad_json_stops_before_paid_model(client):
    r = client.post('/api/manuscripts', files=[('manuscript', ('draft.md', TEXT)), ('results', ('bad.json', '{broken'))])
    run = wait_run(client, r.json()['id'])
    assert run['status'] == 'failed'
    assert client.service.worker.calls == 0


def test_cancel_queued_or_running_and_recover_interruption(client):
    class BlockingWriter:
        async def run(self, *a, **k):
            await asyncio.Event().wait()
    client.service.worker = BlockingWriter()
    first, second = submit(client).json(), submit(client).json()
    assert client.post(f'/api/manuscripts/{second["id"]}/cancel').json()['status'] == 'cancelled'
    assert client.post(f'/api/manuscripts/{first["id"]}/revise').status_code == 409
    restored = ManuscriptService(client.service.root, worker=FixtureWriter(), corpus=EmptyCorpus())
    assert restored.get(first['id'])['status'] == 'interrupted'
    assert client.post(f'/api/manuscripts/{first["id"]}/cancel').json()['status'] == 'cancelled'


def test_number_claim_and_source_role_guards():
    sources = [{'id': 'S1', 'text': TEXT, 'role': 'manuscript'}]
    value, findings = validate_manuscript(draft(), sources)
    assert not findings
    bad = copy.deepcopy(value)
    bad['sections'][3]['paragraphs'][0]['text'] = 'Accuracy was 0.99 in 999 records.'
    _, findings = validate_manuscript(bad, sources)
    assert any(f['code'] == 'untraced_numbers' for f in findings)
    bad['sections'][3]['paragraphs'][0]['evidence'][0]['quote'] = 'This did not occur in the input.'
    _, findings = validate_manuscript(bad, sources)
    assert any(f['code'] == 'invalid_quote' for f in findings)
    _, findings = validate_manuscript(value, [{**sources[0], 'role': 'literature'}])
    assert any(f['code'] == 'own_results_required' for f in findings)


def test_missing_source_and_unprovided_url_block_completion():
    d = draft()
    d['sections'][0]['paragraphs'][0]['text'] += ' https://example.org/fabricated-dataset'
    _, findings = validate_manuscript(d, [{'id': 'S1', 'text': TEXT, 'role': 'manuscript'}])
    assert any(f['code'] == 'untraced_url' for f in findings)
    d['sections'][0]['paragraphs'][0]['evidence'] = []
    _, findings = validate_manuscript(d, [])
    assert any(f['code'] == 'no_evidence' for f in findings)
    d['sections'][0]['key'] = 'methods'
    with pytest.raises(ValueError):
        validate_manuscript(d, [])


def test_reviewer_cannot_invent_manuscript_quotes():
    r = review()
    r['checks'][0]['manuscript_quote'] = 'an invented quote to pass the gate'
    checked = validate_review(r, draft())
    assert checked['checks'][0]['status'] == 'missing'
    r['checks'][-1]['id'] = r['checks'][0]['id']
    with pytest.raises(ValueError):
        validate_review(r, draft())


def test_real_docx_pdf_csv_extraction_and_bibliography(tmp_path):
    path = tmp_path / 'draft.docx'
    doc = Document(); doc.add_paragraph(TEXT); doc.add_table(rows=1, cols=2).cell(0, 0).text = 'Original table'
    doc.save(path)
    extracted = extract_source(path, 'S1', 'manuscript')
    assert TEXT in extracted['text'] and 'Original table' in extracted['text']
    p = tmp_path / 'draft.pdf'; p.write_bytes(pdf_bytes())
    assert '[Page 1]' in extract_source(p, 'S1', 'manuscript')['text']
    p = tmp_path / 'results.csv'; p.write_text('model,accuracy\nbaseline,0.75\n')
    source = extract_source(p, 'S2', 'results')
    assert source['tables'][0]['rows'][1][1] == '0.75'
    literature = {'id': 'L1', 'role': 'literature', 'text': 'Background research in a test fixture.',
                  'title': 'Fixture reference', 'journal_name': 'Fixture Journal', 'publication_year': 2024,
                  'authors': '["A. Example"]', 'doi': 'test-doi', 'url': 'https://example.org/reference'}
    d = draft(); d['sections'][1]['paragraphs'][0]['evidence'].append({'source_id': 'L1', 'quote': literature['text']})
    content = markdown(d, [source, literature])
    assert '[1]' in content and 'Fixture reference' in content
    assert 'title = {Fixture reference}' in bibtex(d, [literature])
    export_docx(tmp_path / 'output.docx', d, [source, literature])
    assert Document(tmp_path / 'output.docx').tables[0].cell(1, 1).text == '0.75'


def test_long_input_discloses_truncation(tmp_path):
    p = tmp_path / 'long.txt'; p.write_text('long text ' * 10000)
    assert extract_source(p, 'S1', 'manuscript')['truncated'] is True


def test_inventory_boundaries_symlink_and_result_import(client, tmp_path):
    root = client.inventory.roots[0]
    (root / 'reports').mkdir(parents=True)
    (root / 'src').mkdir(); (root / '.venv').mkdir()
    (root / 'src/worker.py').write_text('print(1)')
    (root / 'reports/results.csv').write_text('metric,value\naccuracy,0.75\n')
    (root / 'reports/secrets.json').write_text('NEVER INCLUDE THIS')
    (root / '.env').write_text('NEVER INCLUDE THIS')
    outside = tmp_path / 'outside.txt'; outside.write_text('private data')
    (root / 'reports/link.txt').symlink_to(outside)
    (root / '.venv/ignored.py').write_text('dependency')
    report = client.post('/api/research/inventory/scan').json()
    assert report['files'] == 2 and report['program_files'] == 1
    assert len(report['artifacts']) == 1
    assert 'NEVER INCLUDE' not in json.dumps(report)
    assert client.get('/api/research/inventory').json()['scanned_at'] == report['scanned_at']
    assert submit(client, data={'options': json.dumps({'resource_paths': [str(outside)]})}).status_code == 400
    artifact = report['artifacts'][0]['path']
    response = submit(client, data={'options': json.dumps({'resource_paths': [artifact]})})
    run = wait_run(client, response.json()['id'])
    assert Path(run['files'][1]['path']).read_text() == Path(artifact).read_text()
    Path(artifact).unlink(); Path(artifact).symlink_to(outside)
    with pytest.raises(ValueError):
        client.inventory.resolve_artifact(artifact)


def test_sqlite_search_excludes_retractions_and_journal_has_year_category(tmp_path):
    p = tmp_path / 'corpus.sqlite'
    with sqlite3.connect(p) as c:
        c.executescript('''CREATE TABLE works(work_id TEXT, title TEXT, abstract TEXT, doi TEXT, journal_name TEXT,
            publication_year INT, authors TEXT, is_q1 INT, q1_categories TEXT, license TEXT, selected INT, is_retracted INT);
            CREATE VIRTUAL TABLE works_fts USING fts5(title,abstract);
            CREATE TABLE journals_q1(title TEXT, sourceid INT, sjr REAL, categories TEXT, sjr_year INT);''')
        for i in range(2):
            c.execute('INSERT INTO works VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                      (f'PMC{i}', 'Synthetic validation', TEXT, f'10.test/{i}', 'Test journal', 2025, '[]', 1, 'Medicine (Q1)', 'CC-BY', 1, i))
            c.execute('INSERT INTO works_fts VALUES (?,?)', ('Synthetic validation', TEXT))
        c.execute('INSERT INTO journals_q1 VALUES (?,?,?,?,?)', ('Test journal', 42, 1.2, 'Medicine (Q1)', 2025))
    before = p.stat().st_mtime_ns
    corpus = ResearchCorpus(p, tmp_path)
    hits = corpus.search('synthetic validation', 3)
    assert len(hits) == 1 and hits[0]['work_id'] == 'PMC0'
    assert hits[0]['evidence_scope'] == 'abstract'
    assert corpus.journal('Test journal')['sjr_year'] == 2025
    assert corpus.journal('Test journal')['categories'] == 'Medicine (Q1)'
    assert corpus.journal('Unknown journal') is None
    assert corpus.search('"; DROP TABLE works; --', 3) == []
    assert p.stat().st_mtime_ns == before


def test_fulltext_excerpts_stay_within_corpus_boundary(tmp_path):
    corpus = ResearchCorpus(tmp_path / 'db/corpus.sqlite', tmp_path)
    path = tmp_path / 'raw/fulltext/txt/paper.txt'
    path.parent.mkdir(parents=True)
    path.write_text('Relevant segmentation research. ' * 30)
    outside = tmp_path / 'private.txt'
    outside.write_text('Private unrelated text. ' * 30)
    with sqlite3.connect(':memory:') as c:
        c.row_factory = sqlite3.Row
        c.execute('CREATE TABLE files(work_id TEXT, kind TEXT, status TEXT, path TEXT, sha256 TEXT)')
        c.execute('INSERT INTO files VALUES (?,?,?,?,?)', ('PMC1', 'txt', 'ok', 'raw/fulltext/txt/paper.txt', 'recorded-hash'))
        c.execute('INSERT INTO files VALUES (?,?,?,?,?)', ('PMC2', 'txt', 'ok', str(outside), 'private'))
        paper = {'work_id': 'PMC1', 'text': 'Abstract.', 'evidence_scope': 'abstract'}
        corpus._fulltext(c, paper, ['segmentation'])
        assert paper['evidence_scope'] == 'fulltext_excerpts'
        assert 'Relevant segmentation' in paper['text']
        assert paper['fulltext_sha256_record'] == 'recorded-hash'
        private = {'work_id': 'PMC2', 'text': 'Abstract.', 'evidence_scope': 'abstract'}
        corpus._fulltext(c, private, ['private'])
        assert private == {'work_id': 'PMC2', 'text': 'Abstract.', 'evidence_scope': 'abstract'}
