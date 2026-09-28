import { useCallback, useEffect, useRef, useState } from 'react'
import ToolForm from './components/ToolForm'
import ResultView from './components/ResultView'
import PaperPanel from './components/PaperPanel'
import AutoPanel from './components/AutoPanel'
import PaperAutomation from './components/PaperAutomation'
import ManuscriptStudio from './components/ManuscriptStudio'
import { api } from './lib/api'
import './studio.css'

const ICON = { scan: '◎', grid: '▦', cell: '❂', brain: '⌬', net: '⬡', kg: '✦', paper: '▤', dot: '●' }

export default function App() {
  const [page, setPage] = useState('papers')
  const [agents, setAgents] = useState([])
  const [samples, setSamples] = useState({})
  const [stats, setStats] = useState(null)
  const [sel, setSel] = useState(null)
  const [tools, setTools] = useState([])
  const [tool, setTool] = useState(null)
  const [jobs, setJobs] = useState([])
  const [active, setActive] = useState(null)
  const [side, setSide] = useState('result')
  const [error, setError] = useState('')
  const [loadingTools, setLoadingTools] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const selection = useRef(0)
  const wb = useRef(null)

  const load = useCallback(async () => {
    try {
      const [a, s, st] = await Promise.all([api.agents(), api.samples().catch(() => ({})), api.stats().catch(() => null)])
      setAgents(a); setSamples(s); setStats(st); setError('')
    } catch (e) { setError(e.message) }
  }, [])
  useEffect(() => { load(); const timer = setInterval(load, 8000); return () => clearInterval(timer) }, [load])
  useEffect(() => { api.jobs().then(setJobs).catch(() => {}) }, [active?.status, side])
  useEffect(() => {
    if (!active?.id || !['queued', 'running'].includes(active.status)) return
    let alive = true, timer
    const poll = async () => {
      try {
        const value = await api.job(active.id)
        if (!alive) return
        setActive(value)
        if (['queued', 'running'].includes(value.status)) timer = setTimeout(poll, 1200)
      } catch (e) { if (alive) { setError(e.message); timer = setTimeout(poll, 3000) } }
    }
    timer = setTimeout(poll, 800)
    return () => { alive = false; clearTimeout(timer) }
  }, [active?.id, active?.status])

  const pick = async (name) => {
    const request = ++selection.current
    setPage('agents'); setSel(name); setTool(null); setActive(null); setSide('result'); setTools([]); setError(''); setLoadingTools(true)
    try {
      const result = await api.tools(name)
      if (request === selection.current) { setTools(result.tools); setTool(result.tools[0] || null) }
    } catch (e) { if (request === selection.current) setError(e.message) }
    finally { if (request === selection.current) setLoadingTools(false) }
  }
  useEffect(() => { if (page === 'agents' && sel) wb.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }) }, [page, sel])
  const openGenerated = async (name) => { await load(); await pick(name) }
  const run = async (args) => {
    setSubmitting(true); setError('')
    try { setActive(await api.submit(sel, tool.name, args)); setSide('result') } catch (e) { setError(e.message) }
    finally { setSubmitting(false) }
  }
  const cur = agents.find((agent) => agent.name === sel)
  const accent = cur?.display?.accent || '#aaa6ff'
  const readyCount = agents.filter((agent) => agent.status === 'running').length

  return <div className="app studio" style={{ '--accent': accent }}>
    <header className="studio-header"><button className="studio-brand" onClick={() => setPage('papers')} aria-label="Paper2Agent 홈"><span className="brand-mark">P<span>↗</span></span><span>Paper2Agent<small>RESEARCH WORKSPACE</small></span></button>
      <nav aria-label="주 메뉴">{[['papers', '논문으로 에이전트 만들기'], ['manuscript', 'Q1 원고 완성'], ['agents', '에이전트 보관함'], ['data', '데이터 분석']].map(([key, label]) => <button key={key} className={page === key ? 'active' : ''} aria-current={page === key ? 'page' : undefined} onClick={() => setPage(key)}>{label}{key === 'agents' && <span>{agents.length}</span>}</button>)}</nav>
      <div className="system-status"><span className={error ? 'offline' : ''} />{error ? '연결 확인 중' : `${readyCount} agents online`}</div>
    </header>
    <main className="studio-main">
      <div hidden={page !== 'papers'}><PaperAutomation onOpenAgent={openGenerated} onRegistered={load} /></div>
      <div hidden={page !== 'manuscript'}><ManuscriptStudio /></div>
      {page === 'agents' && <>
        <section className="library-heading"><div><div className="eyebrow">YOUR AGENT LIBRARY</div><h1>준비된 에이전트들.</h1><p>업로드한 논문에서 만든 도구와 기존 연구 에이전트를 실행하세요.</p></div><button className="btn primary" onClick={() => setPage('papers')}>＋ 새 에이전트 만들기</button></section>
        {error && <div className="notice-error" role="alert">{error}</div>}
        <section className="cards" aria-label="등록된 에이전트">
          {agents.map((a) => <button type="button" key={a.name} className={'card' + (sel === a.name ? ' on' : '')} style={{ '--c': a.display.accent || '#aaa6ff' }} onClick={() => pick(a.name)}>
            <div className="card-top"><span className="card-icon">{ICON[a.display.icon] || '●'}</span><span className={'run-status ' + (a.status === 'running' ? 'ready' : 'failed')}>{a.status === 'running' ? '사용 가능' : '연결 필요'}</span></div>
            <div className="card-title">{a.display.title}</div><div className="card-tag">{a.display.tagline}</div><div className="card-paper">{a.display.paper}</div>
            <div className="card-foot"><span>{a.display.kind === 'paper_knowledge' ? '논문 지식' : a.display.origin === 'upload' ? '연구 코드' : '기존 에이전트'}</span><span>{a.n_tools} tools ↗</span></div>
          </button>)}
          {!agents.length && <div className="empty">아직 등록된 에이전트가 없습니다. 논문을 업로드하면 첫 에이전트를 만들 수 있습니다.</div>}
        </section>
        {sel && cur && <section className="workbench" ref={wb}>
          <div className="wb-head"><div><div className="eyebrow">AGENT WORKBENCH</div><div className="wb-title">{cur.display.title}</div><div className="mono dim">{cur.display.venue}{cur.display.repo && <> · <a href={cur.display.repo} target="_blank" rel="noreferrer">코드 저장소 ↗</a></>}{cur.display.doi && <> · <a href={'https://doi.org/' + cur.display.doi} target="_blank" rel="noreferrer">논문 ↗</a></>}</div></div><button className="btn ghost small" onClick={async () => { try { await api.restart(sel); await load(); await pick(sel) } catch (e) { setError(e.message) } }}>서버 재연결</button></div>
          <div className="wb-body"><aside className="tools" aria-label="에이전트 도구">{loadingTools ? <div role="status" className="empty">도구를 불러오는 중…</div> : tools.map((t) => <button key={t.name} className={'toolbtn' + (tool?.name === t.name ? ' on' : '')} onClick={() => { setTool(t); setActive(null) }}><span className="tn">{t.name.replace(/^(medsam|medmnist|cellpose|hdbet|hd_bet|nnunet|medkg)_/, '')}</span><span className="td">{(t.description || '').split('\n')[0]}</span></button>)}</aside>
            <div className="stage">{tool && <><div className="tool-desc"><b className="mono">{tool.name}</b><p>{tool.description}</p></div><ToolForm key={sel + ':' + tool.name} agent={sel} tool={tool} samples={samples[sel]} onSubmit={run} busy={submitting || ['running', 'queued'].includes(active?.status)} /></>}
              <div className="sidetabs">{[['result', '실행 결과'], ['paper', '논문 읽기'], ['history', '실행 기록']].map(([key, label]) => <button key={key} className={'tab' + (side === key ? ' on' : '')} onClick={() => setSide(key)}>{label}</button>)}</div>
              <div className="result-slot">{side === 'result' && (active ? <ResultView job={active} accent={accent} /> : <div className="empty">도구를 실행하면 결과와 내려받을 수 있는 파일이 표시됩니다.</div>)}{side === 'paper' && <PaperPanel skill={cur.skill} accent={accent} />}{side === 'history' && <div className="history">{jobs.filter((j) => j.agent === sel).map((j) => <button className="hrow" key={j.id} onClick={() => { setActive(j); setSide('result') }}><span className={'pill ' + j.status}>{j.status}</span><span className="mono">{j.tool}</span><span className="mono dim">{new Date(j.created_at * 1000).toLocaleTimeString()}</span></button>)}{!jobs.some((j) => j.agent === sel) && <div className="empty">아직 실행 기록이 없습니다.</div>}</div>}</div>
            </div>
          </div>
        </section>}
      </>}
      {page === 'data' && <><section className="library-heading"><div><div className="eyebrow">PUT YOUR AGENTS TO WORK</div><h1>데이터에서 결과까지.</h1><p>준비된 연구 에이전트로 이미지와 의료 데이터를 분석합니다.</p></div></section><AutoPanel accent={accent} samples={samples} onJobs={() => api.jobs().then(setJobs).catch(() => {})} /></>}
    </main>
    <footer className="studio-footer"><span>Paper2Agent <span className="dim">/ Research becomes actionable.</span></span><span>{agents.length} 에이전트 · {agents.reduce((n, a) => n + a.n_tools, 0)} 도구{stats?.jobs_done ? ` · ${stats.jobs_done}회 실행 완료` : ''}</span></footer>
  </div>
}
