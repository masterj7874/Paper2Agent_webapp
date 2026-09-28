"""Read-only inventory and literature access for the connected research workspace.

Inventory never executes discovered programs or reads credentials. The corpus is
queried in SQLite read-only mode; a running MedKG service is not required.
"""
from __future__ import annotations

import asyncio
import collections
import json
import os
import re
import shutil
import sqlite3
import time
from pathlib import Path

from .config import WEBAPP_ROOT, relocate
from .paper_automation import write_json

RESEARCH_DIR = Path(os.getenv('PAPER2AGENT_RESEARCH_DIR', WEBAPP_ROOT / 'data/research'))
CORPUS_DB = Path(os.getenv('PAPER2AGENT_CORPUS_DB', WEBAPP_ROOT.parent / 'MedicalAI_Papers/db/medical_ai_papers.sqlite'))
PAPER_PLATFORM = Path(os.getenv('PAPER2AGENT_PAPER_PLATFORM', '/media/jerisuh/HardDisk01/Paper_Generation'))
SKIP_DIRS = {'.git', 'node_modules', '.venv', 'venv', 'env', '__pycache__', '.cache',
             '.mypy_cache', '.pytest_cache', 'site-packages', 'medkg-env', '.Trash-1000',
             '.ssh', '.aws', '.codex', '.claude', 'lost+found'}
CODE_TYPES = {'.py', '.js', '.jsx', '.ts', '.tsx', '.sh', '.r', '.ipynb', '.m', '.cpp', '.rs'}
RESULT_TYPES = {'.md', '.txt', '.csv', '.tsv', '.json', '.docx', '.pdf'}
MANIFEST_NAMES = {'package.json', 'pyproject.toml', 'requirements.txt', 'environment.yml',
                  'Dockerfile', 'docker-compose.yml', 'Cargo.toml'}


def private_name(name):
    name = name.lower()
    return name.startswith('.') or any(s in name for s in ('credential', 'secret', 'token', 'password')) or name.endswith(('.env', '.pem', '.key'))


def connected_roots(agents=None):
    override = os.getenv('PAPER2AGENT_RESEARCH_ROOTS')
    if override is not None:
        return [Path(p).resolve() for p in override.split(os.pathsep) if p]
    roots = [WEBAPP_ROOT.parent / n for n in ('Paper2Agent_webapp', 'Paper2Agent', 'Paper2Agent_out',
             'MedicalAI_Papers', 'MedKG', 'NeuralNode_Research', 'cole-medin-knowledge-base')]
    roots += [PAPER_PLATFORM, PAPER_PLATFORM.parent / 'Q1_Paper_Generation',
              Path('/media/jerisuh/SSD1/scihub-db'), Path('/media/jerisuh/SSD1/sci-hub.kr')]
    for spec in (agents or {}).values():
        if not any(spec.package_dir.is_relative_to(r) for r in roots):
            roots.append(spec.package_dir)
    return list(dict.fromkeys(r.resolve() for r in roots if r.is_dir()))


class ResearchInventory:
    def __init__(self, root=RESEARCH_DIR, roots=None, agents=None):
        self.root = Path(root)
        self.roots = roots if roots is not None else connected_roots(agents)
        self.agents = agents or {}
        self.lock = asyncio.Lock()

    def get(self):
        p = self.root / 'inventory.json'
        try:
            return json.loads(p.read_text()) if p.exists() else None
        except (ValueError, OSError):
            return None

    async def refresh(self):
        async with self.lock:
            result = await asyncio.to_thread(self.scan)
            self.root.mkdir(parents=True, exist_ok=True)
            result['report_path'] = str((self.root / 'inventory.md').resolve())
            lines = ['# 연결된 연구 자원 조사', result['scope'], result['exclusions'],
                     f"조사: {len(result['projects'])}개 프로젝트, {result['directories']:,}개 폴더, "
                     f"{result['files']:,}개 파일, 프로그램 파일 {result['program_files']:,}개."]
            table = ['| 프로젝트 | 폴더 | 파일 | 프로그램 파일 | 조사 상태 |', '|---|---:|---:|---:|---|']
            for p in result['projects']:
                table.append(f"| {p['name']} | {p['directories']:,} | {p['files']:,} | {p['program_files']:,} | "
                             + ('제외 항목 외 조사 완료' if p['complete'] else '부분 조사') + ' |')
            lines.append('\n'.join(table))
            lines += ['\n## 원고 기능에 연결한 자원',
                      '- MedicalAI_Papers: 읽기 전용 문헌 검색과 연도·분야별 저널 등급 수집 기록.',
                      '- Paper_Generation: 기존 코퍼스 기반 편집 규칙. 공식 저널 규정과 구분하여 사용.',
                      '- Paper2Agent: 완료된 실행 결과를 선택하여 원고 근거로 복사.',
                      '- 나머지 프로젝트: 폴더·프로그램·보고서 위치 조사. 프로그램을 실행하거나 파일 본문을 일괄 전송하지 않음.',
                      '\n## 프로그램 위치']
            lines += [f'- {key}: {value or "찾지 못함"}' for key, value in result['programs'].items()]
            lines += ['\n## 프로젝트 경로'] + [f'- {p["name"]}: `{p["path"]}`' for p in result['projects']]
            (self.root / 'inventory.md').write_text('\n\n'.join(lines) + '\n', encoding='utf-8')
            write_json(self.root / 'inventory.json', result)
            return result

    def scan(self):
        started = time.time()
        projects, artifacts = [], []
        artifact_count = 0
        # Count every non-excluded directory/file; only manifest and result names
        # are retained, so a million-paper corpus does not become a million-row API.
        for root in self.roots:
            item = {'name': root.name, 'path': str(root), 'directories': 0, 'files': 0,
                    'program_files': 0, 'manifests': [], 'excluded_directories': 0,
                    'environments': [], 'errors': 0, 'complete': True}
            types = collections.Counter()
            project_artifacts = 0
            deadline = time.monotonic() + 45
            def on_error(_):
                item['errors'] += 1
            for folder, dirs, names in os.walk(root, followlinks=False, onerror=on_error):
                here = Path(folder)
                if time.monotonic() > deadline:
                    item['complete'] = False
                    break
                item['directories'] += 1
                keep = []
                for name in dirs:
                    child = here / name
                    if name in SKIP_DIRS or name.startswith('.') or child.is_symlink():
                        item['excluded_directories'] += 1
                        if name in {'.venv', 'venv', 'medkg-env'}:
                            packages = [p.name for p in child.glob('lib/python*/site-packages/*.dist-info')]
                            item['environments'].append({'path': str(child.relative_to(root)),
                                                         'packages': sorted(packages)[:250], 'package_count': len(packages)})
                    else:
                        keep.append(name)
                dirs[:] = keep
                for name in names:
                    if private_name(name):
                        continue
                    path = here / name
                    if path.is_symlink():
                        continue
                    item['files'] += 1
                    suffix = path.suffix.lower()
                    types[suffix or '(none)'] += 1
                    if suffix in CODE_TYPES:
                        item['program_files'] += 1
                    if name in MANIFEST_NAMES and len(item['manifests']) < 300:
                        item['manifests'].append(str(path.relative_to(root)))
                    relative = path.relative_to(root)
                    result_folder = any(re.search(r'(^|[_-])(reports?|results?|outputs?)([_-]|$)', part, re.I) for part in relative.parts[:-1])
                    if (suffix in RESULT_TYPES and result_folder
                            and not any(p in {'raw', 'fulltext', 'node_modules'} for p in relative.parts)):
                        try:
                            size = path.stat().st_size
                        except OSError:
                            item['errors'] += 1
                            continue
                        if size <= 30 * 1024 * 1024:
                            artifact_count += 1
                            if project_artifacts < 45 and len(artifacts) < 500:
                                artifacts.append({'path': str(path), 'name': name, 'project': root.name, 'bytes': size})
                                project_artifacts += 1
            item['file_types'] = dict(types.most_common(16))
            item['complete'] = item['complete'] and not item['errors']
            projects.append(item)
        return {'scanned_at': time.time(), 'duration_s': round(time.time() - started, 2),
                'scope': '연결된 연구 프로젝트의 폴더·프로그램 목록 (파일 본문은 수집하지 않음)',
                'exclusions': '가상환경은 패키지 목록으로 요약. 의존성·캐시·숨김/인증 파일·심볼릭 링크 제외. 프로젝트별 최대 45초.',
                'projects': projects, 'files': sum(p['files'] for p in projects),
                'directories': sum(p['directories'] for p in projects),
                'program_files': sum(p['program_files'] for p in projects),
                'complete': all(p['complete'] for p in projects), 'artifacts': artifacts,
                'artifact_list_capped': artifact_count > len(artifacts), 'artifact_count': artifact_count,
                'programs': {name: shutil.which(name) for name in ('claude', 'codex', 'python3', 'node', 'git', 'pdftotext', 'pdfinfo', 'libreoffice', 'pandoc', 'nvidia-smi')},
                'agents': [{'name': s.name, 'package_dir': str(s.package_dir)} for s in self.agents.values()]}

    def resolve_artifact(self, value):
        path = Path(value).resolve()
        if path != Path(value).absolute():
            raise ValueError('심볼릭 링크를 통해 연구 자료를 가져올 수 없습니다.')
        inventory = self.get() or {}
        if not any(value == a['path'] for a in inventory.get('artifacts', [])):
            raise ValueError('스캔된 연구 결과 목록에서 파일을 선택해 주세요.')
        if not any(path.is_relative_to(Path(r).resolve()) for r in self.roots) or not path.is_file():
            raise ValueError('선택한 연구 결과에 접근할 수 없습니다.')
        if path.suffix.lower() not in RESULT_TYPES or path.stat().st_size > 30 * 1024 * 1024:
            raise ValueError('지원되지 않거나 너무 큰 연구 결과 파일입니다.')
        return path


class ResearchCorpus:
    def __init__(self, db=CORPUS_DB, platform=PAPER_PLATFORM):
        self.db, self.platform = Path(db), Path(platform)

    def connect(self):
        c = sqlite3.connect(self.db.resolve().as_uri() + '?mode=ro', uri=True, timeout=5)
        c.row_factory = sqlite3.Row
        c.execute('PRAGMA query_only=ON')
        deadline = time.monotonic() + 15
        c.set_progress_handler(lambda: int(time.monotonic() > deadline), 10000)
        return c

    def search(self, query, limit=12):
        terms = list(dict.fromkeys(re.findall(r'[\w-]{3,}', query.lower())))[:12]
        terms = [t for t in terms if t not in {'the', 'and', 'with', 'for', 'study', 'using', 'based', 'results'}]
        if not terms or not self.db.is_file():
            return []
        hits = []
        with self.connect() as c:
            for join in (' AND ', ' OR '):
                expr = join.join('"' + t + '"' for t in terms)
                rows = c.execute('''SELECT w.work_id, w.title, w.abstract, w.doi, w.journal_name,
                    w.publication_year, w.authors, w.is_q1, w.q1_categories, w.license
                    FROM works_fts JOIN works w ON w.rowid=works_fts.rowid
                    WHERE works_fts MATCH ? AND w.selected=1 AND coalesce(w.is_retracted,0)=0
                    ORDER BY bm25(works_fts) LIMIT ?''', (expr, limit)).fetchall()
                for row in rows:
                    if any(h['work_id'] == row['work_id'] for h in hits):
                        continue
                    d = dict(row)
                    d['id'] = f'L{len(hits) + 1}'
                    d['role'] = 'literature'
                    d['name'] = d['title']
                    d['text'] = (d['abstract'] or d['title'])[:7000]
                    d['evidence_scope'] = 'abstract' if d['abstract'] else 'title_only'
                    d['url'] = 'https://doi.org/' + d['doi'] if d.get('doi') else ''
                    if len(hits) < 4:
                        self._fulltext(c, d, terms)
                    hits.append(d)
                    if len(hits) == limit:
                        return hits
                if len(hits) >= limit:
                    break
        return hits

    def _fulltext(self, connection, paper, terms):
        """Relevant excerpts of existing corpus TXT, with a narrow filesystem boundary."""
        try:
            row = connection.execute("SELECT path, sha256 FROM files WHERE work_id=? AND kind='txt' AND status='ok' LIMIT 1",
                                     (paper['work_id'],)).fetchone()
            if not row:
                return
            corpus_root = self.db.parent.parent.resolve()
            path = Path(relocate(row['path']))
            path = (path if path.is_absolute() else corpus_root / path).resolve()
            if not path.is_relative_to(corpus_root / 'raw/fulltext') or not path.is_file():
                return
            with path.open(encoding='utf-8', errors='replace') as stream:
                text = stream.read(500_000)
            blocks = [p.strip() for p in re.split(r'\n\s*\n', text) if len(p.strip()) > 80]
            if not blocks:
                blocks = [text[i:i + 2200] for i in range(0, len(text), 2200)]
            ranked = sorted(enumerate(blocks), key=lambda pair: -sum(pair[1].lower().count(t) for t in terms))[:6]
            excerpts = '\n\n'.join(p[:2000] for _, p in sorted(ranked))[:10000]
            if len(excerpts) < 100:
                return
            paper['text'] += '\n\n[Retrieved full-text excerpts]\n' + excerpts
            paper['evidence_scope'] = 'fulltext_excerpts'
            paper['fulltext_path'] = str(path)
            paper['fulltext_sha256_record'] = row['sha256']
        except (OSError, sqlite3.Error):
            # A corpus without TXT files is still useful; the scope stays explicit.
            return

    def journals(self, query='', limit=60):
        if not self.db.is_file():
            return []
        with self.connect() as c:
            rows = c.execute('''SELECT title, sourceid, max(sjr) AS sjr, categories, sjr_year
                FROM journals_q1 WHERE title LIKE ? GROUP BY title ORDER BY sjr DESC LIMIT ?''',
                             ('%' + query + '%', limit)).fetchall()
        return [{**dict(r), 'ranking_source': 'SCImago SJR · 로컬 수집본',
                 'url': f'https://www.scimagojr.com/journalsearch.php?q={r["sourceid"]}&tip=sid',
                 'verification': 'local_snapshot', 'quartile': 'Q1 (Best Quartile)',
                 'note': '수집본의 등급이며 현재 JCR 등급 또는 게재 보장을 의미하지 않습니다.'} for r in rows]

    def journal(self, title):
        return next((x for x in self.journals(title, 100) if x['title'].casefold() == title.casefold()), None) if title else None

    def guideline(self):
        p = self.platform / 'backend/storage/q1/guideline.json'
        if not p.is_file() or p.stat().st_size > 3_000_000:
            return None
        d = json.loads(p.read_text())
        return {'source_path': str(p), 'version': d.get('version'), 'built_at': d.get('built_at'),
                'origin': '기존 Paper_Generation 코퍼스 분석 규칙 · 공식 저널 투고 규정과 구분',
                'hard_gates': d.get('hard_gates', [])[:20], 'claim_rules': d.get('claim_rules', [])[:15],
                'section_blueprint': d.get('section_blueprint', {})}
