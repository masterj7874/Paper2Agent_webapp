"""Read-only access to the Paper2Skill reading packages (SKILL.md + references/*.md + assets): navigation index, section
retrieval and a simple ranked full-text search so the UI can quote the paper next to the tools."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def paper_overview(skill_dir: Path) -> dict[str, Any]:
    refs = skill_dir / "references"
    idx = _read(refs / "index.md")
    sections = []
    for name in ("paper.md", "supplement.md"):
        text = _read(refs / name)
        heads = [(m.start(), m.group(1).count("#"), m.group(2).strip()) for m in re.finditer(r"^(#{1,4}) (.+)$", text, flags=re.M)]
        sections.append({"file": name, "chars": len(text), "headings": [{"level": lvl, "title": t} for _, lvl, t in heads][:200]})
    assets = {}
    for cat in ("figure", "supp_figs", "table", "supp_table"):
        d = skill_dir / "assets" / cat
        if d.is_dir():
            assets[cat] = sorted(p.name for p in d.iterdir() if p.is_file())
    return {"skill": skill_dir.name, "index_markdown": idx, "sections": sections, "assets": assets}


def paper_section(skill_dir: Path, file: str, heading: str, max_chars: int = 12000) -> dict[str, Any]:
    if file not in ("paper.md", "supplement.md", "index.md"):
        raise ValueError("file must be paper.md, supplement.md or index.md")
    text = _read(skill_dir / "references" / file)
    if not heading:
        return {"file": file, "heading": None, "markdown": text[:max_chars], "truncated": len(text) > max_chars}
    m = re.search(rf"^(#{{1,4}}) {re.escape(heading)}\s*$", text, flags=re.M)
    if not m:
        raise KeyError(heading)
    level = len(m.group(1))
    rest = text[m.end():]
    nxt = re.search(rf"^#{{1,{level}}} ", rest, flags=re.M)
    body = rest[: nxt.start()] if nxt else rest
    return {"file": file, "heading": heading, "markdown": body.strip()[:max_chars], "truncated": len(body) > max_chars}


def paper_search(skill_dir: Path, query: str, limit: int = 12) -> list[dict[str, Any]]:
    terms = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
    if not terms:
        return []
    hits: list[dict[str, Any]] = []
    for name in ("paper.md", "supplement.md"):
        text = _read(skill_dir / "references" / name)
        current = None
        for ln, line in enumerate(text.splitlines(), 1):
            hm = re.match(r"^(#{1,4}) (.+)$", line)
            if hm:
                current = hm.group(2).strip()
                continue
            low = line.lower()
            score = sum(low.count(t) for t in terms)
            if score and len(line.strip()) > 20:
                hits.append({"file": name, "line": ln, "heading": current, "score": score, "text": line.strip()[:400]})
    hits.sort(key=lambda h: (-h["score"], h["file"], h["line"]))
    return hits[:limit]
