import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'

const STATUS = { queued: '대기 중', running: '생성 중', ready: '등록 완료', failed: '생성 실패', needs_input: '확인 필요', cancelled: '중단됨', interrupted: '중단됨' }
const STAGES = ['논문 읽기', '내용 분석', '에이전트 생성', '실행 검증', '자동 등록']
const isActive = (run) => ['queued', 'running'].includes(run?.status)
const date = (value) => new Date(value * 1000).toLocaleString('ko-KR', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })

function RunDetail({ run, onOpenAgent, onUpdate }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [repository, setRepository] = useState(run.repository_url || run.resolved_repository || '')
  const [goal, setGoal] = useState(run.goal || '')
  const action = async (callback) => {
    setBusy(true); setError('')
    try { onUpdate(await callback()) } catch (e) { setError(e.message) } finally { setBusy(false) }
  }
  const canRetry = ['failed', 'needs_input', 'cancelled', 'interrupted'].includes(run.status)
  return <section className="run-detail" aria-label="선택한 논문 생성 작업">
    <div className="run-heading">
      <div><div className="eyebrow">PAPER TO AGENT <span> / {run.id}</span></div><h2>{run.title}</h2><p>{run.filename}{run.page_count ? ` · ${run.page_count}쪽` : ''} · {date(run.created_at)}</p></div>
      <span className={'run-status ' + run.status}>{isActive(run) && <i className="spinner" />}{STATUS[run.status]}</span>
    </div>
    <ol className="pipeline" aria-label="생성 단계">
      {run.stages.map((stage, index) => <li key={stage.id} className={stage.status} aria-current={stage.status === 'running' ? 'step' : undefined}>
        <span className="stage-number">{stage.status === 'done' ? '✓' : stage.status === 'running' ? <i className="spinner" /> : String(index + 1).padStart(2, '0')}</span>
        <span>{stage.label}</span><small>{stage.status === 'done' ? '완료' : stage.status === 'running' ? '진행 중' : stage.status === 'failed' ? '확인 필요' : stage.status === 'pending' ? '대기' : '중단'}</small>
      </li>)}
    </ol>
    {isActive(run) && <div className="run-live" role="status"><span className="pulse-dot" /><span>{run.status === 'queued' ? '앞선 논문의 생성이 끝나면 자동으로 시작합니다.' : run.stages.find((s) => s.status === 'running')?.detail || '자동 생성을 진행하고 있습니다.'}</span><button className="text-button" disabled={busy} onClick={() => action(() => api.cancelPaperRun(run.id))}>작업 중단</button></div>}
    {run.error && <div className="notice-error" role="alert">{run.error}</div>}
    {error && <div className="notice-error" role="alert">{error}</div>}
    {canRetry && <div className="retry-box"><p>입력이나 서버 상태를 확인한 뒤, 같은 논문으로 다시 생성할 수 있습니다.</p><div className="option-fields"><label>코드 저장소 <span>선택</span><input type="url" value={repository} maxLength={500} placeholder="https://github.com/owner/repository" onChange={(e) => setRepository(e.target.value)} /></label><label>생성할 도구에 대한 요청 <span>선택</span><input value={goal} maxLength={2000} placeholder="예: 데이터 전처리와 추론 도구에 집중해 주세요" onChange={(e) => setGoal(e.target.value)} /></label></div><button className="btn primary" disabled={busy} onClick={() => action(() => api.retryPaperRun(run.id, repository, goal))}>{busy ? '처리 중…' : '다시 생성하기 ↗'}</button></div>}
    {run.analysis && <div className="paper-insights">
      <div className="insight-main"><div className="eyebrow">논문 분석</div><h3>이 논문으로 만드는 에이전트</h3><p className="paper-summary">{run.analysis.summary}</p><div className="method-tags">{run.analysis.methods.map((method, index) => <span key={index}>{method}</span>)}</div>
        <details className="source-evidence"><summary>원문 근거 {run.analysis.evidence.length}개 확인하기</summary>{run.analysis.evidence.map((item, i) => <div key={i}><b>p. {item.page} · {item.claim}</b><blockquote>{item.quote}</blockquote></div>)}</details>
      </div>
      <aside className="agent-output"><span className="eyebrow">생성 결과</span><h3>{run.agent_kind === 'research_code' ? '연구 코드 에이전트' : run.agent_kind === 'paper_knowledge' ? '논문 지식 에이전트' : '에이전트 설계 중'}</h3>
        {run.resolved_repository ? <a className="repo-link" href={run.resolved_repository} target="_blank" rel="noreferrer">{run.resolved_repository.replace('https://', '')} ↗</a> : <p>연결된 코드 저장소가 없는 경우 본문 검색, 페이지 읽기, 근거가 포함된 요약 도구를 생성합니다.</p>}
        {run.agent_kind === 'paper_knowledge' && <p className="muted">논문의 실험이나 모델을 재현하는 도구는 포함되지 않습니다.</p>}
        {run.verification && <div className="verification"><strong>{run.verification.tool_count}</strong><span>연결된 도구</span><ul>{run.verification.calls.map((call, i) => <li key={i}>✓ {call.tool}</li>)}</ul><small>표시된 도구의 지정 입력 호출을 검증했습니다.</small></div>}
        {run.status === 'ready' && <button className="btn primary open-agent" onClick={() => onOpenAgent(run.agent_name)}>에이전트 열기 ↗</button>}
        <div className="download-list">{run.artifacts?.map((artifact) => <a key={artifact.path} href={api.fileUrl(artifact.path, true)} download>{artifact.label} <span>↓</span></a>)}</div>
      </aside>
    </div>}
    {(run.analysis?.limitations?.length > 0 || run.build_limitations?.length > 0) && <details className="run-limits"><summary>논문 및 생성 범위의 한계</summary><ul>{[...run.analysis.limitations, ...(run.build_limitations || [])].map((item, i) => <li key={i}>{item}</li>)}</ul></details>}
    <details className="activity-log"><summary>활동 기록 <span>{run.events.length}</span></summary><ol>{run.events.slice().reverse().map((event, i) => <li key={i}><time>{new Date(event.at * 1000).toLocaleTimeString('ko-KR')}</time><span>{event.message}</span></li>)}</ol></details>
  </section>
}

export default function PaperAutomation({ onOpenAgent, onRegistered }) {
  const [runs, setRuns] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [run, setRun] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [drag, setDrag] = useState(false)
  const [error, setError] = useState('')
  const [connectionError, setConnectionError] = useState('')
  const [repository, setRepository] = useState('')
  const [goal, setGoal] = useState('')
  const [capabilities, setCapabilities] = useState(null)
  const fileInput = useRef(null)
  const uploadLock = useRef(false)
  const seenReady = useRef(new Set())
  const registeredRef = useRef(onRegistered)
  registeredRef.current = onRegistered

  useEffect(() => {
    let alive = true
    let timer
    const poll = async () => {
      try {
        const [list, caps] = await Promise.all([api.paperRuns(), api.paperCapabilities()])
        if (!alive) return
        setRuns(list); setCapabilities(caps); setConnectionError('')
        for (const item of list) if (item.status === 'ready' && !seenReady.current.has(item.id)) {
          seenReady.current.add(item.id); registeredRef.current?.()
        }
        setSelectedId((id) => id || list.find(isActive)?.id || list[0]?.id || null)
      } catch (e) { if (alive) setConnectionError(e.message) }
      if (alive) timer = setTimeout(poll, 3000)
    }
    poll()
    return () => { alive = false; clearTimeout(timer) }
  }, [])

  useEffect(() => {
    if (!selectedId) return
    let alive = true
    let timer
    const poll = async () => {
      try {
        const value = await api.paperRun(selectedId)
        if (!alive) return
        setRun(value); setConnectionError('')
        if (isActive(value)) timer = setTimeout(poll, 1800)
      } catch (e) { if (alive) { setConnectionError(e.message); timer = setTimeout(poll, 4000) } }
    }
    poll()
    return () => { alive = false; clearTimeout(timer) }
  }, [selectedId, run?.attempt, run?.status === 'queued'])

  const update = (value) => { setRun(value); setSelectedId(value.id); setRuns((all) => [value, ...all.filter((item) => item.id !== value.id)]) }
  const upload = async (file) => {
    if (!file || uploadLock.current) return
    setError('')
    if (!file.name.toLowerCase().endsWith('.pdf')) { setError('논문 PDF 파일을 선택해 주세요.'); return }
    if (!file.size || file.size > 30 * 1024 * 1024) { setError('비어 있지 않은 30 MB 이하의 PDF를 선택해 주세요.'); return }
    uploadLock.current = true; setUploading(true)
    try { update(await api.createPaperAgent(file, repository.trim(), goal.trim())) } catch (e) { setError(e.message) }
    finally { uploadLock.current = false; setUploading(false); if (fileInput.current) fileInput.current.value = '' }
  }
  const unavailable = capabilities && (!capabilities.pdf_available || !capabilities.worker_available)

  return <div className="paper-automation">
    <section className="paper-hero"><div className="eyebrow"><span className="tiny-spark">✦</span> FROM RESEARCH TO ACTION</div><h1>논문 한 편에서,<br /><span>작동하는 에이전트까지.</span></h1><p>논문을 올리면 분석부터 생성, 실행 검증과 등록까지.<br className="desktop-break" /> 새 에이전트가 준비되는 과정을 한곳에서 확인하세요.</p></section>
    {connectionError && <div className="notice-error" role="alert">{connectionError} 연결을 다시 확인하고 있습니다.</div>}
    <section className="upload-layout">
      <div className="paper-upload-card"><div className="section-label"><span>01 / 시작하기</span><span className="auto-label">자동 생성</span></div>
        <div className={'paper-drop ' + (drag ? 'dragging ' : '') + (uploading ? 'uploading' : '')} onDragOver={(e) => { e.preventDefault(); if (!uploading) setDrag(true) }} onDragLeave={(e) => { if (!e.currentTarget.contains(e.relatedTarget)) setDrag(false) }} onDrop={(e) => { e.preventDefault(); setDrag(false); if (e.dataTransfer.files.length > 1) { setError('한 번에 논문 한 편씩 업로드해 주세요.'); return }; upload(e.dataTransfer.files[0]) }}>
          <div className="paper-file-icon" aria-hidden="true"><span>PDF</span><i /><i /><i /></div><h2>{uploading ? '논문을 업로드하고 있습니다' : drag ? '여기에 놓으면 생성이 시작됩니다' : '논문 PDF를 여기에 놓아주세요'}</h2><p>파일을 선택하면 에이전트 생성이 바로 시작됩니다.</p>
          <button className="btn primary upload-button" disabled={uploading || unavailable} onClick={() => fileInput.current?.click()}>{uploading ? <><i className="spinner" /> 업로드 중…</> : <>↑ &nbsp; 논문 선택하고 시작</>}</button>
          <input ref={fileInput} type="file" accept=".pdf,application/pdf" hidden aria-label="논문 PDF 업로드" onChange={(e) => upload(e.target.files?.[0])} /><small>PDF · 최대 30 MB · 300쪽 이내</small>
        </div>
        {error && <div className="notice-error" role="alert">{error}</div>}
        {unavailable && <div className="notice-error" role="alert">{!capabilities.pdf_available ? '서버의 PDF 추출 도구(poppler-utils)를 설치해 주세요.' : '서버에 Claude Code를 설치하고 로그인해 주세요.'}</div>}
        <details className="upload-options"><summary>코드 저장소나 생성할 도구를 직접 지정하고 싶다면 <span>선택 사항 ＋</span></summary><div className="option-fields"><label>코드 저장소 주소<input type="url" value={repository} maxLength={500} placeholder="https://github.com/owner/repository" onChange={(e) => setRepository(e.target.value)} disabled={uploading} /></label><label>어떤 도구가 필요한가요?<textarea value={goal} maxLength={2000} rows={2} placeholder="예: 논문의 추론 파이프라인을 새 데이터에 적용할 수 있게 해주세요." onChange={(e) => setGoal(e.target.value)} disabled={uploading} /></label></div></details>
        <p className="processing-note">논문 내용은 연결된 Claude 계정으로 분석하며, 생성 결과는 이 서버에 보관합니다.</p>
      </div>
      <aside className="workflow-preview"><div className="eyebrow">업로드 다음은, 자동으로.</div><h2>논문이 도구가 되는 과정</h2><ol>{STAGES.map((name, i) => <li key={name}><span>{String(i + 1).padStart(2, '0')}</span><div><b>{name}</b><p>{['본문과 코드 저장소 링크 추출', '연구 방법과 원문 근거 파악', '논문 전용 실행 도구 구성', '서버 연결과 실제 도구 호출 확인', '에이전트 목록에 추가'][i]}</p></div>{i === 4 && <span className="last-check">↗</span>}</li>)}</ol><div className="workflow-note">코드가 있는 논문은 연구 코드 에이전트로,<br />코드가 없는 논문은 검색·요약 에이전트로.</div></aside>
    </section>
    <section className="paper-run-history"><div className="section-title"><div><span className="eyebrow">YOUR RESEARCH, IN MOTION</span><h2>최근 생성 작업 <span>{runs.length}</span></h2></div><span className="live-label"><i /> 실시간 업데이트</span></div>
      {runs.length ? <div className="run-list">{runs.map((item) => <button key={item.id} className={'run-list-item ' + (selectedId === item.id ? 'selected' : '')} onClick={() => { if (selectedId !== item.id) setRun(null); setSelectedId(item.id) }}><span className="mini-doc" aria-hidden="true">↳</span><span className="run-list-title"><b>{item.title}</b><small>{item.filename} · {date(item.created_at)}</small></span><span className={'run-status ' + item.status}>{STATUS[item.status]}</span><span aria-hidden="true">↗</span></button>)}</div> : <div className="paper-empty"><span aria-hidden="true">↳</span><div><b>첫 번째 논문을 기다리고 있어요.</b><p>업로드한 논문과 생성된 에이전트가 이곳에 차곡차곡 쌓입니다.</p></div></div>}
    </section>
    {run && <RunDetail key={run.id + ':' + run.attempt} run={run} onOpenAgent={onOpenAgent} onUpdate={update} />}
    {selectedId && !run && <div className="paper-empty" role="status">작업 기록을 불러오고 있습니다…</div>}
  </div>
}
