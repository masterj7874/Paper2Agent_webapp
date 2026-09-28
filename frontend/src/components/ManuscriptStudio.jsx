import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import './manuscript.css'

const ACTIVE = ['queued', 'running']
const STATUS = { queued: '대기 중', running: '작성 중', needs_evidence: '자료 보완 필요', review_ready: '원고 완성 · 저자 검토', failed: '작성 중단', cancelled: '취소됨', interrupted: '중단됨' }
const CHECK = { satisfied: '충족', missing: '보완 필요', not_applicable: '비대상' }
const ACCEPT = '.pdf,.docx,.md,.txt,.csv,.tsv,.json'
const number = value => Number(value || 0).toLocaleString('ko-KR')

export default function ManuscriptStudio() {
  const [cap, setCap] = useState(null), [inventory, setInventory] = useState(null)
  const [runs, setRuns] = useState([]), [selected, setSelected] = useState(null), [run, setRun] = useState(null)
  const [error, setError] = useState(''), [busy, setBusy] = useState(false), [scanning, setScanning] = useState(false)
  const [draft, setDraft] = useState(null), [results, setResults] = useState([]), [jobs, setJobs] = useState([])
  const [jobIds, setJobIds] = useState([]), [resourcePaths, setResourcePaths] = useState([])
  const [resourceQuery, setResourceQuery] = useState(''), [journals, setJournals] = useState([])
  const [options, setOptions] = useState({ study_type: 'medical_ai', journal: '', journal_requirements: '', language: 'English', target_words: 2500, instructions: '' })
  const [extraFiles, setExtraFiles] = useState([]), [revision, setRevision] = useState('')
  const [watch, setWatch] = useState(0)
  const [revisionJournal, setRevisionJournal] = useState(''), [revisionRequirements, setRevisionRequirements] = useState('')
  const resultRef = useRef(null), selectedRef = useRef(null)
  selectedRef.current = selected
  const update = (key, value) => setOptions(previous => ({ ...previous, [key]: value }))

  useEffect(() => {
    let alive = true
    Promise.all([api.manuscriptCapabilities(), api.researchInventory(), api.jobs(100)]).then(([c, i, j]) => {
      if (alive) { setCap(c); setInventory(i); setJobs(j.filter(x => x.status === 'done')) }
    }).catch(e => alive && setError(e.message))
    const load = () => api.manuscriptRuns().then(values => {
      if (!alive) return
      setRuns(values)
      if (!selectedRef.current && values.length) setSelected(values[0].id)
    }).catch(e => alive && setError(e.message))
    load(); const timer = setInterval(load, 3500)
    return () => { alive = false; clearInterval(timer) }
  }, [])
  useEffect(() => {
    if (!selected) return
    let alive = true, timer
    setRun(null); setExtraFiles([]); setRevision('')
    const poll = async () => {
      try {
        const next = await api.manuscriptRun(selected)
        if (!alive) return
        setRun(next)
        setRevisionJournal(next.options.journal || ''); setRevisionRequirements(next.options.journal_requirements || '')
        if (ACTIVE.includes(next.status)) timer = setTimeout(poll, 2200)
      } catch (e) { if (alive) { setError(e.message); timer = setTimeout(poll, 5000) } }
    }
    poll()
    return () => { alive = false; clearTimeout(timer) }
  }, [selected, watch])
  useEffect(() => {
    let alive = true
    const timer = setTimeout(() => api.researchJournals(options.journal).then(j => alive && setJournals(j)).catch(() => alive && setJournals([])), 300)
    return () => { alive = false; clearTimeout(timer) }
  }, [options.journal])

  const selectFiles = (files, setter) => {
    const values = Array.from(files || [])
    if (values.some(f => f.size > 30 * 1024 * 1024 || !/\.(pdf|docx|md|txt|csv|tsv|json)$/i.test(f.name))) {
      setError('지원 형식의 파일을 선택해 주세요. 파일당 최대 30 MB입니다.'); return
    }
    setError(''); setter(values)
  }
  const start = async event => {
    event.preventDefault()
    if (!draft) { setError('내 논문 초안을 먼저 선택해 주세요.'); return }
    setBusy(true); setError('')
    try {
      const created = await api.createManuscript(draft, results, { ...options, job_ids: jobIds, resource_paths: resourcePaths })
      setSelected(created.id); setRun(created)
      setRuns(await api.manuscriptRuns())
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100)
    } catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  const scan = async () => {
    setScanning(true); setError('')
    try { setInventory(await api.scanResearch()) } catch (e) { setError(e.message) } finally { setScanning(false) }
  }
  const revise = async () => {
    setBusy(true); setError('')
    try { setRun(await api.reviseManuscript(run.id, extraFiles, revision, revisionJournal, revisionRequirements)); setWatch(v => v + 1); setExtraFiles([]); setRevision('') }
    catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  const toggle = (value, setter) => setter(previous => previous.includes(value) ? previous.filter(x => x !== value) : [...previous, value])
  const selectedJournal = journals.find(j => j.title.toLowerCase() === options.journal.toLowerCase())
  const resourceCandidates = (inventory?.artifacts || []).filter(a => `${a.name} ${a.project}`.toLowerCase().includes(resourceQuery.toLowerCase())).slice(0, 35)

  return <div className="manuscript-studio">
    <section className="paper-hero manuscript-hero">
      <div className="eyebrow">FROM EVIDENCE TO MANUSCRIPT <span>Q1 WORKSPACE</span></div>
      <h1>연구 결과를,<br />투고할 수 있는 원고로.</h1>
      <p>내 논문 초안과 기존 실험 결과를 올리세요.<br />문헌을 찾고, 원고를 보완하고, 검토 의견을 반영한 파일까지 만듭니다.</p>
      <div className="manuscript-promise"><span>실제 결과 기반 집필</span><span>주장별 출처 추적</span><span>독립 검토 후 수정</span></div>
    </section>
    {error && <div className="notice-error" role="alert">{error}</div>}
    <div className="manuscript-compose">
      <form className="manuscript-form" onSubmit={start}>
        <div className="section-title"><div><div className="eyebrow">01 / YOUR RESEARCH</div><h2>원고와 근거 준비</h2></div><span className="soft-label">기존 결과 사용</span></div>
        <label className="manuscript-file main-file"><span className="file-symbol">▤</span><strong>{draft ? draft.name : '내 논문 초안 선택'}</strong><small>PDF, Word, Markdown, TXT · 최대 30 MB</small><input aria-label="내 논문 초안" type="file" accept=".pdf,.docx,.md,.txt" onChange={e => selectFiles(e.target.files, v => setDraft(v[0] || null))} /></label>
        <label className="manuscript-file result-files"><strong>＋ 실험 결과 · 방법 · 저자 정보 추가</strong><small>{results.length ? results.map(f => f.name).join(' · ') : 'CSV, JSON, PDF, Word, TXT 등 · 초안 포함 최대 10개'}</small><input aria-label="기존 연구 결과" type="file" accept={ACCEPT} multiple onChange={e => selectFiles(e.target.files, setResults)} /></label>
        <p className="input-help">본인이 작성 중인 초안과 실제 결과를 사용합니다. 다른 연구의 출판 논문은 본 연구의 실험 결과로 간주하지 않습니다.</p>
        <div className="manuscript-fields">
          <label>연구 유형<select value={options.study_type} onChange={e => update('study_type', e.target.value)}>{Object.entries(cap?.study_types || { medical_ai: { label: '의료 AI 연구' } }).map(([key, value]) => <option value={key} key={key}>{value.label}</option>)}</select></label>
          <label>원고 언어<select value={options.language} onChange={e => update('language', e.target.value)}><option value="English">영어</option><option value="Korean">한국어</option></select></label>
        </div>
        <label className="manuscript-label">목표 저널 <span>선택</span><input value={options.journal} list="research-journals" placeholder="저널명을 입력하거나 수집본에서 선택" maxLength={250} onChange={e => update('journal', e.target.value)} /><datalist id="research-journals">{journals.map(j => <option key={j.title} value={j.title}>{j.sjr_year} SJR Q1 수집본</option>)}</datalist></label>
        {selectedJournal && <p className="journal-snapshot"><a href={selectedJournal.url} target="_blank" rel="noreferrer">{selectedJournal.sjr_year} SJR · Q1 (Best Quartile) ↗</a><small>{selectedJournal.categories}</small></p>}
        <details className="manuscript-options"><summary>투고 규정 · 작성 요청 · 기존 도구 결과 연결</summary><div>
          <label className="manuscript-label">최신 투고 규정<textarea value={options.journal_requirements} rows={4} maxLength={14000} placeholder="저널의 공식 규정과 출처 URL을 붙여 넣으세요. 원고 유형, 초록·본문 분량, 필수 선언문 등" onChange={e => update('journal_requirements', e.target.value)} /></label>
          <label className="manuscript-label">작성 요청<textarea value={options.instructions} maxLength={4000} rows={3} placeholder="강조할 연구 기여, 유지할 표현, 저자 정보 등" onChange={e => update('instructions', e.target.value)} /></label>
          <label className="manuscript-label">목표 분량 <span>영어 단어 수 기준 · 자료가 뒷받침하는 범위</span><input type="number" min={1000} max={6000} step={100} value={options.target_words} onChange={e => update('target_words', Number(e.target.value))} /></label>
          <div className="source-picker"><b>완료된 에이전트 실행 결과</b><button type="button" className="text-button" onClick={() => api.jobs(100).then(j => setJobs(j.filter(x => x.status === 'done'))).catch(e => setError(e.message))}>새로고침</button>{jobs.length ? jobs.map(j => <label key={j.id}><input type="checkbox" checked={jobIds.includes(j.id)} onChange={() => toggle(j.id, setJobIds)} /><span>{j.agent} / {j.tool}<small>{j.id}</small></span></label>) : <p>완료된 실행 결과가 없습니다. 결과 파일을 직접 추가할 수 있습니다.</p>}</div>
          <div className="source-picker"><b>스캔에서 찾은 보고서·결과</b><input aria-label="연구 결과 파일 검색" placeholder="파일명 또는 프로젝트명 검색" value={resourceQuery} onChange={e => setResourceQuery(e.target.value)} />{resourceCandidates.map(a => <label key={a.path}><input type="checkbox" checked={resourcePaths.includes(a.path)} onChange={() => toggle(a.path, setResourcePaths)} /><span>{a.name}<small>{a.project}</small></span></label>)}{!resourceCandidates.length && <p>아래 연구 자원 목록에서 폴더를 조사하면 파일을 선택할 수 있습니다.</p>}</div>
        </div></details>
        <button className="btn primary manuscript-start" disabled={busy || !draft || cap?.worker_available === false} type="submit">{busy ? '자료를 저장하는 중…' : '기존 결과로 원고 완성'} <span>↗</span></button>
        <p className="input-help">선택한 자료만 기존 Claude 작업기로 전달합니다. 생성은 수 분 이상 걸릴 수 있으며 로그인·사용량 한도를 사용합니다.</p>
      </form>
      <aside className="manuscript-guide">
        <div className="eyebrow">02 / EDITORIAL WORKFLOW</div><h2>집필에서 검토까지,<br />하나의 작업으로.</h2>
        <ol>{[['자료 읽기', '초안·실험 결과·표의 원본을 보존합니다.'], ['근거 수집', '로컬 논문 DB에서 관련 문헌을 찾습니다.'], ['원고 작성', '초록, 방법, 결과, 논의와 선언문을 작성합니다.'], ['검토 및 수정', '주장과 숫자를 점검하고 원고를 다시 다듬습니다.'], ['패키지 완성', 'Word 원고, 인용 근거, 수정 내역을 내려받습니다.']].map(([title, text], i) => <li key={title}><span>{String(i + 1).padStart(2, '0')}</span><div><b>{title}</b><p>{text}</p></div></li>)}</ol>
        <div className="manuscript-context"><b>Q1을 준비하는 방식</b><p>저널 등급은 출처·연도·분야와 함께 표시합니다. 원고는 연구 설계와 근거에 맞춰 보완하며, 확인되지 않은 결과는 보완 항목으로 남깁니다.</p><small>보고 지침 안내: {cap?.study_types?.[options.study_type]?.guideline || '연구 설계별 보고 지침'}</small></div>
        <div className="resource-availability"><span className={cap?.corpus_available ? 'available' : ''} />{cap?.corpus_available ? '로컬 문헌 DB 연결됨' : '로컬 문헌 DB 연결 확인 필요'}<br /><small>등급 수집본·편집 점검은 게재 보장이 아닙니다.</small></div>
      </aside>
    </div>

    <section className="research-inventory"><div className="section-title"><div><div className="eyebrow">CONNECTED RESEARCH RESOURCES</div><h2>연결된 연구 자원</h2></div><button className="btn ghost small" disabled={scanning} onClick={scan}>{scanning ? '폴더 조사 중…' : inventory?.scanned_at ? '다시 스캔' : '연구 폴더 스캔'}</button></div>
      {inventory?.scanned_at ? <><div className="inventory-stats"><span><b>{inventory.projects.length}</b> 연구 프로젝트</span><span><b>{number(inventory.directories)}</b> 폴더</span><span><b>{number(inventory.program_files)}</b> 프로그램 파일</span><span><b>{number(inventory.files)}</b> 조사한 파일</span></div>{inventory.report_path && <a className="inventory-download" href={api.fileUrl(inventory.report_path, true)}>조사 보고서 내려받기 ↓</a>}<details><summary>프로젝트별 조사 결과 · {new Date(inventory.scanned_at * 1000).toLocaleString('ko-KR')}{!inventory.complete && ' · 일부 조사 제한'}</summary><div className="inventory-projects">{inventory.projects.map(p => <div key={p.path}><b>{p.name}</b><span>{number(p.program_files)} 프로그램 · {number(p.files)} 파일</span><small>{p.path}</small><small>{p.complete ? '제외 항목 외 목록 조사 완료' : '시간 한도 또는 접근 오류로 부분 조사'} · 의존성/숨김 폴더 {p.excluded_directories}개 제외</small>{p.environments?.length > 0 && <small>가상환경 {p.environments.length}개 · 패키지 {number(p.environments.reduce((n, e) => n + e.package_count, 0))}개 식별</small>}</div>)}</div><p className="input-help">{inventory.exclusions}</p><p className="input-help">{inventory.artifact_list_capped ? '결과 파일 목록은 프로젝트별 45개, 전체 500개까지 표시합니다. 다른 파일은 직접 업로드하세요.' : '파일 본문은 자동으로 집필 자료에 포함되지 않습니다. 위에서 필요한 결과를 선택하세요.'}</p></details></> : <p className="input-help">연결된 연구 폴더와 프로그램, 기존 분석 결과의 위치를 조사합니다. 인증 파일과 파일 본문은 수집하지 않습니다.</p>}
    </section>

    <section className="manuscript-runs" ref={resultRef}>
      <div className="section-title"><div><div className="eyebrow">YOUR MANUSCRIPTS</div><h2>원고 작업</h2></div><span className="soft-label">{runs.length}개</span></div>
      {runs.length > 0 && <div className="manuscript-run-tabs">{runs.map(r => <button key={r.id} className={selected === r.id ? 'selected' : ''} onClick={() => setSelected(r.id)}><b>{r.title}</b><small>{STATUS[r.status] || r.status} · {r.attempt}차</small></button>)}</div>}
      {!runs.length && <div className="paper-empty"><span>▤</span><div><b>첫 원고를 준비해 보세요.</b><p>작성 과정과 파일, 보완할 사항이 이곳에 저장됩니다.</p></div></div>}
      {selected && !run && <p className="input-help" role="status">원고 작업을 불러오는 중…</p>}
      {run && <article className="run-detail manuscript-detail">
        <div className="run-heading"><div><div className="eyebrow">MANUSCRIPT / {run.attempt}차 원고</div><h2>{run.title}</h2><p>{run.options.journal || '목표 저널 미지정'} · {run.options.language === 'English' ? '영문' : '국문'} 원고</p></div><span className={'run-status ' + run.status}>{STATUS[run.status] || run.status}</span></div>
        <ol className="pipeline manuscript-pipeline">{run.stages.map((s, i) => <li key={s.id} className={s.status}><span className="stage-number">{s.status === 'done' ? '✓' : i + 1}</span><span>{s.label}</span><small>{s.status === 'done' ? '완료' : s.status === 'running' ? '진행 중' : s.status === 'pending' ? '대기' : '중단'}</small></li>)}</ol>
        {ACTIVE.includes(run.status) && <div className="run-live" role="status"><span className="pulse-dot" />{run.events.at(-1)?.message || '작업 순서를 기다리고 있습니다.'}<button className="text-button" onClick={async () => { try { setRun(await api.cancelManuscript(run.id)) } catch (e) { setError(e.message) } }}>작업 취소</button></div>}
        {run.error && <div className="notice-error" role="alert">{run.error}</div>}
        {run.readiness && <div className="manuscript-result">
          <div className="manuscript-verdict"><div className="eyebrow">EDITORIAL REVIEW</div><h3>{run.readiness.label}</h3><p>{run.review.summary}</p><div className="readiness-count"><b>{run.readiness.satisfied}<span> / {run.readiness.total}</span></b><span>내부 편집 항목 충족 판정</span></div><small>{run.readiness.scope}</small>{run.journal && <p className="journal-snapshot"><a href={run.journal.url} target="_blank" rel="noreferrer">{run.journal.title} · SJR {run.journal.sjr_year} 수집본 ↗</a><small>{run.journal.categories}</small></p>}
            <div className="download-list">{run.artifacts.map(a => <a key={a.path} href={api.fileUrl(a.path, true)}>{a.label}<span>↓</span></a>)}</div>
          </div>
          <div className="manuscript-review"><h3>원고 점검과 보완 항목</h3>{run.review.checks.map(c => <details key={c.id} className={'editorial-check ' + c.status}><summary><span>{CHECK[c.status]}</span>{cap?.checklist?.[c.id] || c.id}</summary><p>{c.explanation}</p>{c.action && <p className="check-action">{c.action}</p>}{c.manuscript_quote && <blockquote>{c.manuscript_quote}</blockquote>}</details>)}
            {(run.readiness.notes.length > 0 || run.readiness.findings.length > 0) && <details className="additional-findings" open><summary>추가 확인 {run.readiness.notes.length + run.readiness.findings.length}건</summary><ul>{run.readiness.notes.map((n, i) => <li key={'n' + i}>{n}</li>)}{run.readiness.findings.map((f, i) => <li key={'f' + i}>{f.location} · {f.message}</li>)}</ul></details>}
          </div>
        </div>}
        {run.manuscript && <details className="manuscript-preview"><summary>완성된 원고 미리보기</summary><div><h2>{run.manuscript.title}</h2>{run.manuscript.sections.map(s => <section key={s.key}><h3>{s.heading}</h3>{s.paragraphs.map((p, i) => <p key={i} className={p.kind === 'missing' ? 'missing-paragraph' : ''}>{p.kind === 'missing' && <b>저자 자료 필요 · </b>}{p.text}</p>)}</section>)}</div></details>}
        {run.literature?.length > 0 && <details className="activity-log"><summary>검색한 문헌과 출처 · {run.literature.length}건</summary><div className="literature-list">{run.literature.map(l => <div key={l.id}><b>{l.id} · {l.title}</b><p>{l.journal_name} · {l.publication_year} · {l.evidence_scope === 'fulltext_excerpts' ? '초록·원문 발췌' : l.evidence_scope === 'abstract' ? '초록 근거' : '제목만 확보'}</p>{l.url && <a href={l.url} target="_blank" rel="noreferrer">DOI 확인 ↗</a>}</div>)}</div></details>}
        {!ACTIVE.includes(run.status) && <div className="manuscript-revise"><h3>자료를 보완해 다시 작성</h3><p>현재 원고와 검토 기록은 남겨두고 다음 차수로 작성합니다.</p><label className="manuscript-label">추가 근거 파일<input type="file" aria-label="보완 자료" accept={ACCEPT} multiple onChange={e => selectFiles(e.target.files, setExtraFiles)} /></label><label className="manuscript-label">목표 저널<input value={revisionJournal} maxLength={250} onChange={e => setRevisionJournal(e.target.value)} /></label><label className="manuscript-label">최신 투고 규정<textarea rows={3} value={revisionRequirements} maxLength={14000} onChange={e => setRevisionRequirements(e.target.value)} /></label><label className="manuscript-label">추가 작성 요청<textarea rows={2} value={revision} maxLength={4000} placeholder="보완한 내용이나 유지할 사항을 적어 주세요." onChange={e => setRevision(e.target.value)} /></label><button className="btn primary" disabled={busy} onClick={revise}>{busy ? '저장 중…' : '보완 자료로 다시 작성'}</button></div>}
        {run.history.length > 0 && <details className="activity-log"><summary>이전 원고 · {run.history.length}개 차수 보존</summary>{run.history.map(h => <div className="download-list" key={h.attempt}><b>{h.attempt}차 · {STATUS[h.status]}</b>{(h.artifacts || []).map(a => <a key={a.path} href={api.fileUrl(a.path, true)}>{a.label}<span>↓</span></a>)}</div>)}</details>}
        <details className="activity-log"><summary>작업 기록</summary><ol>{run.events.map((e, i) => <li key={i}><time>{new Date(e.at * 1000).toLocaleTimeString('ko-KR')}</time><span>{e.message}</span></li>)}</ol></details>
      </article>}
    </section>
  </div>
}
