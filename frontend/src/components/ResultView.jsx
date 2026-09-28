import { useEffect, useState } from 'react'
import { api } from '../lib/api'

const IMG = /\.(png|jpe?g|gif|webp)$/i
const TXT = /\.(json|txt|csv|md|log|tsv)$/i

export function Artifact({ a, accent }) {
  const [open, setOpen] = useState(false)
  const [prev, setPrev] = useState(null)
  const isImg = IMG.test(a.path)
  // label masks / 16-bit images are near-black when shown raw: ask the backend to colorise them
  const isLabel = /(mask|label|seg)[^/]*\.(png|tif|tiff)$/i.test(a.path) || /label|mask/i.test(a.description || '') && /\.(png|tif|tiff)$/i.test(a.path)
  const imgSrc = isLabel ? api.fileUrl(a.path) + '&render=labels' : api.fileUrl(a.path)
  useEffect(() => { if (open && !isImg && !prev) api.preview(a.path).then(setPrev).catch((e) => setPrev({ kind: 'error', text: String(e) })) }, [open])
  return (
    <div className="artifact" style={{ '--accent': accent }}>
      <div className="art-head" onClick={() => setOpen((o) => !o)}>
        <span className="art-name">{a.path.split('/').pop()}</span>
        <span className="art-desc">{a.description}</span>
        <a className="btn ghost small" href={api.fileUrl(a.path, true)} onClick={(e) => e.stopPropagation()}>⤓</a>
      </div>
      {isImg && <a href={imgSrc} target="_blank" rel="noreferrer"><img className="art-img" src={imgSrc} alt={a.description} loading="lazy" /></a>}
      {open && !isImg && prev && (prev.kind === 'text' ? <pre className="art-pre">{prev.text}</pre> : <pre className="art-pre">{JSON.stringify(prev, null, 1)}</pre>)}
    </div>
  )
}

function Summary({ result }) {
  if (!result || typeof result !== 'object') return <pre className="art-pre">{String(result)}</pre>
  const skip = new Set(['message', 'reference', 'artifacts'])
  const rows = Object.entries(result).filter(([k, v]) => !skip.has(k) && (typeof v !== 'object' || v === null || (Array.isArray(v) && v.length <= 12 && v.every((x) => typeof x !== 'object'))))
  const deep = Object.entries(result).filter(([k, v]) => !skip.has(k) && !rows.find(([rk]) => rk === k))
  return (
    <div>
      <div className="kv">{rows.map(([k, v]) => <div className="kvrow" key={k}><span className="k">{k}</span><span className="v">{Array.isArray(v) ? v.join(', ') : typeof v === 'number' ? (Number.isInteger(v) ? v : v.toFixed(6)) : String(v)}</span></div>)}</div>
      {deep.length > 0 && <details className="deep"><summary>full result JSON ({deep.length} nested fields)</summary><pre className="art-pre">{JSON.stringify(Object.fromEntries(deep), null, 1)}</pre></details>}
    </div>
  )
}

export default function ResultView({ job, accent }) {
  if (!job) return null
  const r = job.result
  return (
    <div className="result" style={{ '--accent': accent }}>
      <div className="res-head">
        <span className={'pill ' + job.status}>{job.status}</span>
        <span className="mono">{job.agent} · {job.tool}</span>
        {job.duration_s != null && <span className="mono dim">{job.duration_s}s</span>}
        {r?.reference && <a className="mono dim" href={r.reference} target="_blank" rel="noreferrer">source ↗</a>}
      </div>
      {job.status === 'error' && r?.hint && <div className="res-msg hint-box">💡 {r.hint}</div>}
      {job.status === 'error' && <pre className="art-pre err">{job.error}\n{r?.traceback}</pre>}
      {job.status === 'done' && r?.message && <p className="res-msg">{r.message}</p>}
      {job.status === 'done' && <Summary result={r} />}
      {job.status === 'done' && Array.isArray(r?.artifacts) && r.artifacts.length > 0 && (
        <div className="artifacts">{[...r.artifacts].sort((a, b) => IMG.test(b.path) - IMG.test(a.path)).map((a) => <Artifact key={a.path} a={a} accent={accent} />)}</div>
      )}
    </div>
  )
}
