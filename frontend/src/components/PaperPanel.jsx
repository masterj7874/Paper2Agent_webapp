import { useEffect, useState } from 'react'
import { api } from '../lib/api'

export default function PaperPanel({ skill, accent }) {
  const [ov, setOv] = useState(null)
  const [q, setQ] = useState('')
  const [hits, setHits] = useState([])
  const [sec, setSec] = useState(null)
  const [tab, setTab] = useState('sections')
  useEffect(() => { setOv(null); setSec(null); setHits([]); if (skill) api.paper(skill).then(setOv).catch(() => setOv(null)) }, [skill])
  if (!skill) return <div className="paper empty">No paper skill for this agent.</div>
  if (!ov) return <div className="paper empty">loading paper…</div>
  const search = async (e) => { e.preventDefault(); if (!q.trim()) return; const r = await api.search(skill, q); setHits(r.hits) }
  const openSec = async (file, heading) => { const s = await api.section(skill, file, heading); setSec(s) }
  const figs = [...(ov.assets.figure || []).map((n) => ['figure', n]), ...(ov.assets.supp_figs || []).map((n) => ['supp_figs', n])]
  return (
    <div className="paper" style={{ '--accent': accent }}>
      <form className="searchrow" onSubmit={search}><input value={q} onChange={(e) => setQ(e.target.value)} placeholder="search the paper (e.g. 'learning rate', 'NSD tolerance')" /><button className="btn ghost small" type="submit">search</button></form>
      {hits.length > 0 && <div className="hits">{hits.map((h, i) => <div className="hit" key={i} onClick={() => h.heading && openSec(h.file, h.heading)}><span className="mono dim">{h.file}:{h.line}{h.heading ? ' · ' + h.heading : ''}</span><p>{h.text}</p></div>)}</div>}
      <div className="tabs">{['sections', 'figures', 'tables'].map((t) => <button key={t} className={'tab' + (tab === t ? ' on' : '')} onClick={() => setTab(t)}>{t}</button>)}</div>
      {tab === 'sections' && <div className="sections">{ov.sections.map((s) => <div key={s.file}><div className="mono dim">{s.file} · {Math.round(s.chars / 1000)}k chars</div>{s.headings.filter((h) => h.level <= 3).map((h, i) => <button key={i} className={'seclink l' + h.level} onClick={() => openSec(s.file, h.title)}>{h.title}</button>)}</div>)}</div>}
      {tab === 'figures' && <div className="figs">{figs.map(([cat, n]) => <a key={n} href={api.assetUrl(skill, cat, n)} target="_blank" rel="noreferrer"><img src={api.assetUrl(skill, cat, n)} alt={n} loading="lazy" /><span className="mono dim">{n}</span></a>)}</div>}
      {tab === 'tables' && <div className="sections">{[...(ov.assets.table || []).map((n) => ['table', n]), ...(ov.assets.supp_table || []).map((n) => ['supp_table', n])].map(([cat, n]) => <a key={n} className="seclink l3" href={api.assetUrl(skill, cat, n)} target="_blank" rel="noreferrer">{n} ⤓</a>)}</div>}
      {sec && <div className="section"><div className="sec-head"><b>{sec.heading}</b><span className="mono dim">{sec.file}</span><button className="linkbtn" onClick={() => setSec(null)}>close</button></div><pre className="sec-body">{sec.markdown}</pre></div>}
    </div>
  )
}
