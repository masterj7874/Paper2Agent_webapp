"""Manuscript input, evidence contracts, deterministic checks and Word export."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .paper_documents import extract_pdf

ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.md', '.txt', '.csv', '.tsv', '.json'}
MAX_FILE = 30 * 1024 * 1024
SECTIONS = ['abstract', 'introduction', 'methods', 'results', 'discussion', 'conclusion', 'declarations']
GUIDELINE_LIBRARY = 'https://www.equator-network.org/reporting-guidelines-study-design/artificial-intelligence-machine-learning-studies/'
STUDY_TYPES = {
    'medical_ai': {'label': '의료 AI 연구', 'guideline': '연구 설계에 맞는 EQUATOR 지침 선택', 'url': GUIDELINE_LIBRARY},
    'prediction': {'label': '임상 예측 모델', 'guideline': 'TRIPOD+AI', 'url': 'https://www.tripod-statement.org/'},
    'imaging': {'label': '의료 영상 AI', 'guideline': 'CLAIM 2024', 'url': 'https://pubs.rsna.org/doi/10.1148/ryai.240300'},
    'diagnostic': {'label': '진단 정확도 연구', 'guideline': 'STARD-AI', 'url': 'https://www.nature.com/articles/s41591-025-03953-8'},
    'trial': {'label': 'AI 임상시험', 'guideline': 'CONSORT 및 CONSORT-AI', 'url': GUIDELINE_LIBRARY},
    'review': {'label': '체계적 문헌고찰', 'guideline': 'PRISMA 2020', 'url': 'https://www.prisma-statement.org/'},
    'other': {'label': '기타 연구', 'guideline': '연구 분야별 보고 지침 확인', 'url': 'https://www.equator-network.org/'},
}
CHECKS = {
    'question': '연구 질문·기여와 기존 연구의 구분',
    'design': '연구 설계·자료 출처·포함/제외 기준',
    'methods': '재현 가능한 방법·설정·자료 분할과 누수 방지',
    'results': '제공된 실제 결과와 표·본문의 일치',
    'statistics': '평가 지표·불확실성·통계 방법과 적용 근거',
    'validation': '연구 설계에 적합한 비교·검증과 한계',
    'claims': '결론의 범위가 연구 설계와 근거를 넘지 않음',
    'limitations': '편향·일반화·제한점과 후속 검증',
    'ethics': '윤리·동의·개인정보 처리 또는 비대상 근거',
    'availability': '데이터·코드 접근 방법과 재현성',
    'disclosures': '기여·이해상충·지원·AI 사용 공개',
    'references': '실재 문헌과 주장 간 인용 근거',
    'reporting': '선택한 보고 지침에 필요한 항목과 적용 범위',
    'journal': '목표 저널 범위·원고 유형·최신 투고 규정',
}


class SourceQuote(BaseModel):
    source_id: str = Field(max_length=30)
    quote: str = Field(min_length=5, max_length=1800)


class ResearchBrief(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    search_query: str = Field(min_length=3, max_length=300)
    research_question: str = Field(max_length=1500)
    contribution: str = Field(max_length=2000)
    observed_facts: list[SourceQuote] = Field(max_length=20)
    missing_evidence: list[str] = Field(max_length=20)


class Paragraph(BaseModel):
    text: str = Field(min_length=1, max_length=7000)
    kind: Literal['observed', 'background', 'interpretation', 'missing']
    evidence: list[SourceQuote] = Field(max_length=8)


class Section(BaseModel):
    key: Literal['abstract', 'introduction', 'methods', 'results', 'discussion', 'conclusion', 'declarations']
    heading: str = Field(min_length=1, max_length=160)
    paragraphs: list[Paragraph] = Field(min_length=1, max_length=12)


class Manuscript(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    sections: list[Section] = Field(min_length=7, max_length=7)
    changes: list[str] = Field(max_length=30)


class CheckFinding(BaseModel):
    id: str = Field(max_length=40)
    status: Literal['satisfied', 'missing', 'not_applicable']
    explanation: str = Field(min_length=1, max_length=1600)
    manuscript_quote: str = Field(max_length=1500)
    action: str = Field(max_length=1800)


class Review(BaseModel):
    summary: str = Field(max_length=3500)
    checks: list[CheckFinding] = Field(min_length=14, max_length=14)
    revision_instructions: list[str] = Field(max_length=20)


def normalize(text):
    return re.sub(r'\s+', ' ', text).strip().casefold()


def extract_source(path, source_id, role, name=None):
    path = Path(path)
    if path.suffix.lower() not in ALLOWED_EXTENSIONS or not 0 < path.stat().st_size <= MAX_FILE:
        raise ValueError('PDF·DOCX·MD·TXT·CSV·TSV·JSON 파일만 지원하며 파일당 최대 30 MB입니다.')
    suffix = path.suffix.lower()
    tables = []
    if suffix == '.pdf':
        document = extract_pdf(path, path.with_suffix('.extracted.txt'))
        text = '\n\n'.join(f'[Page {i + 1}]\n{p}' for i, p in enumerate(document['pages']))
    elif suffix == '.docx':
        with zipfile.ZipFile(path) as z:
            if len(z.infolist()) > 2000 or sum(i.file_size for i in z.infolist()) > 50_000_000:
                raise ValueError('압축 해제 크기가 너무 큰 DOCX입니다.')
            if any('encrypted' in i.filename.lower() for i in z.infolist()):
                raise ValueError('암호화된 DOCX는 지원하지 않습니다.')
        from docx import Document
        from docx.table import Table
        from docx.text.paragraph import Paragraph as WordParagraph
        doc = Document(path)
        content = []
        for block in doc.iter_inner_content():
            if isinstance(block, WordParagraph):
                content.append(block.text)
            elif isinstance(block, Table):
                content.extend('\t'.join(c.text for c in row.cells) for row in block.rows)
        text = '\n'.join(content)
    else:
        if path.stat().st_size > 2_000_000:
            raise ValueError('텍스트·표 자료는 2 MB 이하의 결과 요약으로 업로드해 주세요.')
        text = path.read_text(encoding='utf-8-sig')
        if '\x00' in text:
            raise ValueError('UTF-8 텍스트 파일을 업로드해 주세요.')
        if suffix == '.json':
            text = json.dumps(json.loads(text), ensure_ascii=False, indent=2)
        if suffix in {'.csv', '.tsv'}:
            rows = list(csv.reader(io.StringIO(text), delimiter='\t' if suffix == '.tsv' else ','))
            if rows and 1 < len(rows[0]) <= 6 and len(rows) <= 41 and all(len(r) == len(rows[0]) for r in rows):
                tables.append({'heading': name or path.name, 'rows': rows})
    if len(text.strip()) < 10:
        raise ValueError(f'{name or path.name}: 읽을 수 있는 본문이 부족합니다.')
    limit = 65000 if role == 'manuscript' else 22000
    return {'id': source_id, 'role': role, 'name': name or path.name,
            'text': text[:limit], 'characters': len(text), 'truncated': len(text) > limit,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'tables': tables}


def quote_valid(quote, sources):
    source = sources.get(quote['source_id'])
    return bool(source and normalize(quote['quote']) in normalize(source['text']))


def number_tokens(text):
    return set(re.findall(r'(?<![\w])\d+(?:[.,]\d+)*(?:%|e[+-]?\d+)?', text.lower()))


def validate_manuscript(value, sources):
    manuscript = Manuscript.model_validate(value).model_dump()
    if [s['key'] for s in manuscript['sections']] != SECTIONS:
        raise ValueError('원고의 필수 절 구조가 올바르지 않습니다. 다시 시도해 주세요.')
    source_map = {s['id']: s for s in sources}
    findings = []
    for section in manuscript['sections']:
        for i, paragraph in enumerate(section['paragraphs']):
            loc = f"{section['key']}:{i + 1}"
            def add(code, message):
                findings.append({'code': code, 'location': loc, 'message': message})
            evidence = paragraph['evidence']
            if paragraph['kind'] == 'missing':
                add('missing_evidence', '저자가 보완할 자료가 원고에 남아 있습니다.')
                continue
            if not evidence:
                add('no_evidence', '문단의 근거가 연결되지 않았습니다.')
            for quote in evidence:
                if not quote_valid(quote, source_map):
                    add('invalid_quote', f"{quote['source_id']}: 인용문을 해당 원문에서 확인하지 못했습니다.")
            valid = [q for q in evidence if quote_valid(q, source_map)]
            if paragraph['kind'] == 'observed' or section['key'] in {'results', 'methods', 'declarations'}:
                if not any(source_map[q['source_id']]['role'] != 'literature' for q in valid):
                    add('own_results_required', '본 연구의 방법·결과·선언은 제공된 연구 자료로 확인해야 합니다.')
            numbers = number_tokens(paragraph['text'])
            supported = number_tokens(' '.join(q['quote'] for q in valid))
            missing_numbers = numbers - supported
            if missing_numbers:
                add('untraced_numbers', '근거 발췌에서 확인되지 않은 숫자: ' + ', '.join(sorted(missing_numbers)[:15]))
            known_urls = ' '.join(s['text'] for s in sources) + ' '.join(s.get('url', '') for s in sources)
            for url in re.findall(r'https?://[^\s<>\])]+', paragraph['text']):
                if url.rstrip('.,;') not in known_urls:
                    add('untraced_url', '제공 자료에 없는 URL이 원고에 포함되어 있습니다.')
            if re.search(r'\[(?:CIT|TODO|TBD|MISSING|AUTHOR)[^\]]*\]|\b(?:TBD|TODO)\b', paragraph['text'], re.I):
                add('placeholder', '미완성 표기가 원고에 남아 있습니다.')
    return manuscript, findings


def validate_review(value, manuscript):
    review = Review.model_validate(value).model_dump()
    ids = [c['id'] for c in review['checks']]
    if len(set(ids)) != len(CHECKS) or set(ids) != set(CHECKS):
        raise ValueError('검토 결과에 필수 점검 항목이 누락되었습니다.')
    text = normalize(' '.join(p['text'] for s in manuscript['sections'] for p in s['paragraphs']))
    for check in review['checks']:
        quote = normalize(check['manuscript_quote'])
        if check['status'] == 'satisfied' and (len(quote) < 8 or quote not in text):
            check.update(status='missing', action='충족 판단의 원고 인용문을 확인할 수 없어 저자 확인이 필요합니다.')
    return review


def reference_map(manuscript, sources):
    used = list(dict.fromkeys(q['source_id'] for s in manuscript['sections'] for p in s['paragraphs'] for q in p['evidence']))
    rows = [s for source_id in used for s in sources if s['id'] == source_id and s['role'] == 'literature']
    return {s['id']: i + 1 for i, s in enumerate(rows)}, rows


def paragraph_text(paragraph, refs):
    ids = sorted(set(refs[q['source_id']] for q in paragraph['evidence'] if q['source_id'] in refs))
    text = paragraph['text']
    if paragraph['kind'] == 'missing' and not text.startswith('[AUTHOR INPUT REQUIRED]'):
        text = '[AUTHOR INPUT REQUIRED] ' + text
    return text + (' [' + ', '.join(map(str, ids)) + ']' if ids else '')


def reference_text(source):
    authors = source.get('authors') or []
    if isinstance(authors, str):
        try:
            authors = json.loads(authors)
        except ValueError:
            authors = []
    names = [a.get('name', '') if isinstance(a, dict) else str(a) for a in authors[:6]]
    return '. '.join(str(x).rstrip('. ') for x in [', '.join(names), source.get('title'), source.get('journal_name'),
                                    source.get('publication_year'), source.get('url')] if x)


def markdown(manuscript, sources):
    refs, references = reference_map(manuscript, sources)
    parts = ['# ' + manuscript['title']]
    for section in manuscript['sections']:
        parts += ['## ' + section['heading']] + [paragraph_text(p, refs) for p in section['paragraphs']]
    if references:
        parts.append('## References')
        parts += [f'[{i + 1}] {reference_text(s)}' for i, s in enumerate(references)]
    for source in sources:
        for table in source.get('tables', []):
            rows = table['rows']
            escaped = lambda r: '| ' + ' | '.join(c.replace('|', '\\|').replace('\n', ' ') for c in r) + ' |'
            parts.append('## Supplied results: ' + table['heading'])
            parts.append('\n'.join([escaped(rows[0]), '| ' + ' | '.join('---' for _ in rows[0]) + ' |'] + [escaped(r) for r in rows[1:]]))
    return '\n\n'.join(parts) + '\n'


def export_docx(path, manuscript, sources):
    """Narrative preset, with a named submission override: black serif headings.

    All tables are unchanged uploaded values; no model-generated numerical table.
    """
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor, Twips
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    doc = Document()
    doc.settings.odd_and_even_pages_header_footer = False
    section = doc.sections[0]
    section.different_first_page_header_footer = False
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Inches(1)
    section.header_distance = section.footer_distance = Inches(.492)
    for name, size, before, after in [('Normal', 11, 0, 8), ('Title', 20, 0, 14),
                                     ('Heading 1', 16, 18, 10), ('Heading 2', 13, 12, 6), ('Heading 3', 12, 8, 4)]:
        style = doc.styles[name]
        style.font.name, style.font.size = 'Times New Roman', Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
        fonts = style.element.get_or_add_rPr().rFonts
        for attribute in ('asciiTheme', 'hAnsiTheme', 'eastAsiaTheme', 'cstheme'):
            fonts.attrib.pop(qn('w:' + attribute), None)
        fonts.set(qn('w:eastAsia'), 'Noto Sans CJK KR')
        for border in list(style.element.get_or_add_pPr().findall(qn('w:pBdr'))):
            style.element.pPr.remove(border)
        style.paragraph_format.space_before, style.paragraph_format.space_after = Pt(before), Pt(after)
        style.paragraph_format.line_spacing = 1.333
        style.paragraph_format.widow_control = True
        if name.startswith('Heading'):
            style.paragraph_format.keep_with_next = True
            style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if name == 'Title':
            style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    doc.styles['Normal'].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    section.header.paragraphs[0].text = 'Research manuscript · Author review required'
    section.header.paragraphs[0].style = doc.styles['Normal']
    for r in section.header.paragraphs[0].runs:
        r.font.size = Pt(8)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); footer._p.append(field)
    doc.add_paragraph(manuscript['title'], 'Title')
    refs, references = reference_map(manuscript, sources)
    for part in manuscript['sections']:
        doc.add_heading(part['heading'], 1)
        for p in part['paragraphs']:
            doc.add_paragraph(paragraph_text(p, refs))
    if references:
        doc.add_heading('References', 1)
        for i, ref in enumerate(references):
            p = doc.add_paragraph(f'[{i + 1}] {reference_text(ref)}')
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    for source in sources:
        for item in source.get('tables', []):
            doc.add_heading('Supplied results: ' + item['heading'], 1)
            rows = item['rows']
            table = doc.add_table(rows=0, cols=len(rows[0]))
            table.autofit = False
            table.style = 'Table Grid'
            widths = [9360 // len(rows[0])] * len(rows[0]); widths[-1] += 9360 - sum(widths)
            pr = table._tbl.tblPr
            pr.find(qn('w:tblW')).set(qn('w:w'), '9360'); pr.find(qn('w:tblW')).set(qn('w:type'), 'dxa')
            ind = OxmlElement('w:tblInd'); ind.set(qn('w:w'), '120'); ind.set(qn('w:type'), 'dxa'); pr.append(ind)
            margins = OxmlElement('w:tblCellMar')
            for key, value in [('top', 80), ('bottom', 80), ('start', 120), ('end', 120)]:
                node = OxmlElement('w:' + key); node.set(qn('w:w'), str(value)); node.set(qn('w:type'), 'dxa'); margins.append(node)
            pr.append(margins)
            for grid, width in zip(table._tbl.tblGrid.gridCol_lst, widths):
                grid.set(qn('w:w'), str(width))
            for index, values in enumerate(rows):
                row = table.add_row()
                for cell, value, width in zip(row.cells, values, widths):
                    cell.width = Twips(width); cell.text = value
                    for p in cell.paragraphs:
                        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
                        p.paragraph_format.space_after = Pt(4)
                        for r in p.runs:
                            r.font.size = Pt(9); r.bold = index == 0
                if index == 0:
                    header = OxmlElement('w:tblHeader'); row._tr.get_or_add_trPr().append(header)
    doc.core_properties.author = ''
    doc.core_properties.title = manuscript['title']
    doc.save(path)


def bibtex(manuscript, sources):
    _, references = reference_map(manuscript, sources)
    clean = lambda x: str(x or '').replace('\\', '').replace('{', '').replace('}', '').replace('\n', ' ')
    return '\n\n'.join('@article{ref' + str(i + 1) + ',\n' + ',\n'.join(
        f'  {key} = {{{clean(ref.get(field))}}}' for key, field in [('title', 'title'), ('journal', 'journal_name'),
        ('year', 'publication_year'), ('doi', 'doi'), ('url', 'url')]) + '\n}' for i, ref in enumerate(references))
