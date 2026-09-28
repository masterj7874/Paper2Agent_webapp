"""Copied into each paper's package. All responses come from its source document."""
import json
import re
from pathlib import Path

from fastmcp import FastMCP

DOCUMENT = json.loads((Path(__file__).parent / 'document.json').read_text(encoding='utf-8'))
mcp = FastMCP(DOCUMENT['analysis']['title'])


@mcp.tool()
def paper_overview() -> dict:
    """논문의 요약, 방법, 한계와 페이지별 근거를 반환합니다. 실험을 실행하는 도구는 아닙니다."""
    return {**DOCUMENT['analysis'], 'page_count': len(DOCUMENT['pages']),
            'capability': 'paper_knowledge', 'source_sha256': DOCUMENT['sha256']}


@mcp.tool()
def paper_search(query: str, limit: int = 5) -> dict:
    """논문 본문에서 검색어를 찾아 원문 문맥과 페이지 번호를 반환합니다."""
    terms = {term.casefold() for term in re.findall(r'\w+', query) if len(term) > 1}
    if not terms:
        raise ValueError('두 글자 이상의 검색어를 입력해 주세요.')
    if not 1 <= limit <= 20:
        raise ValueError('limit은 1~20이어야 합니다.')
    hits = []
    for index, page in enumerate(DOCUMENT['pages']):
        lowered = page.casefold()
        score = sum(lowered.count(term) for term in terms)
        if score:
            start = min(lowered.find(term) for term in terms if term in lowered)
            hits.append({'page': index + 1, 'score': score,
                         'text': page[max(0, start - 200):start + 1400]})
    hits.sort(key=lambda item: (-item['score'], item['page']))
    return {'query': query, 'hits': hits[:limit], 'total_pages_matched': len(hits)}


@mcp.tool()
def paper_page(page: int) -> dict:
    """지정한 페이지의 추출된 본문을 읽습니다. 페이지 번호는 1부터 시작합니다."""
    if not 1 <= page <= len(DOCUMENT['pages']):
        raise ValueError(f'페이지 번호는 1~{len(DOCUMENT["pages"])}이어야 합니다.')
    text = DOCUMENT['pages'][page - 1]
    return {'page': page, 'text': text[:25000], 'truncated': len(text) > 25000}


if __name__ == '__main__':
    mcp.run(transport='stdio', show_banner=False)
