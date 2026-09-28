// ⚡ Auto: drop/upload a file or paste a path -> deterministic detection + recipe -> chained run with live progress + report.
import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../lib/api'
import { Artifact } from './ResultView'

const IMG = /\.(png|jpe?g|gif|webp)$/i
const KIND_LABEL = {
  mri_volume: 'MRI volume', ct_volume: 'CT volume', microscopy_2d: '2-D microscopy image', medical_2d: '2-D medical image', medsam_npz: 'MedSAM demo npz',
  video: 'video', frames_folder: 'video frames', image_folder: 'folder of 2-D images', msd_task: 'MSD task folder', nnunet_dataset: 'nnU-Net dataset',
  dicom_series: 'DICOM series', medmnist_flag: 'MedMNIST dataset', unknown: 'unknown input',
}
const AGENT_COLOR = { MedSAM: '#22d3ee', MedMNIST: '#a78bfa', Cellpose: '#34d399', HDBET: '#fb923c', nnUNet: '#f472b6', MedKG: '#facc15', auto: '#8b96ad' }
const fmt = (v) => (typeof v === 'number' ? (Number.isInteger(v) ? String(v) : v.toPrecision(4)) : String(v))
const short = (p) => (p || '').split('/').slice(-2).join('/')

function pickUploadPath(r) {
  const conv = r.converted || []
  const by = (k) => conv.find((c) => c.kind === k)?.path
  if (r.kind === 'dicom' || r.kind === 'dicom-zip') return by('volume') || r.path
  if (r.kind === 'zip') return by('folder') || r.path
  return r.path // videos are resolved to their frame folder by the planner
}

function StepRow({ s, accent, open, onToggle }) {
  const kn = Object.entries(s.key_numbers || {}).slice(0, 6)
  return (
    <div className={'astep ' + s.status} style={{ '--c': AGENT_COLOR[s.agent] || accent }}>
      <div className="astep-head" onClick={onToggle}>
        <span className="astep-idx mono">{s.index}</span>
        <span className={'pill ' + s.status}>{s.status}</span>
        <span className="astep-tool mono"><b>{s.agent}</b>.{s.tool}</span>
        <span className="astep-label">{s.label}</span>
        <span className="mono dim">{s.duration_s != null ? `${s.duration_s}s` : s.status === 'running' ? '…' : ''}</span>
      </div>
      {kn.length > 0 && <div className="astep-kn mono">{kn.map(([k, v]) => <span key={k}><i>{k}</i> {fmt(v)}</span>)}</div>}
      {s.error && <div className="hint problem">⚠ {s.error}{s.hint ? ` — ${s.hint}` : ''}</div>}
      {open && (
        <div className="astep-body">
          {s.message && <p className="res-msg">{s.message}</p>}
          <details><summary className="mono dim">arguments</summary><pre className="art-pre">{JSON.stringify(s.resolved_arguments || s.arguments, null, 1)}</pre></details>
          {(s.artifacts || []).length > 0 && <div className="artifacts">{[...s.artifacts].sort((a, b) => IMG.test(b.path) - IMG.test(a.path)).slice(0, 12).map((a) => <Artifact key={a.path} a={a} accent={AGENT_COLOR[s.agent] || accent} />)}</div>}
        </div>
      )}
    </div>
  )
}

export default function AutoPanel({ accent, samples, onJobs }) {
  const [path, setPath] = useState('')
  const [uploading, setUploading] = useState(false)
  const [notice, setNotice] = useState('')
  const [plan, setPlan] = useState(null)
  const [planning, setPlanning] = useState(false)
  const [recipeId, setRecipeId] = useState(null)
  const [run, setRun] = useState(null)
  const [runs, setRuns] = useState([])
  const [open, setOpen] = useState({})
  const [report, setReport] = useState(null)
  const [error, setError] = useState('')
  const [drag, setDrag] = useState(false)
  const pollRef = useRef(null)

  const loadRuns = () => api.autoRuns().then(setRuns).catch(() => {})
  useEffect(() => { loadRuns() }, [])
  useEffect(() => () => clearTimeout(pollRef.current), [])

  // quick-start chips: one representative sample per agent
  const chips = useMemo(() => {
    const out = []
    const add = (agent, pat, label) => { const s = (samples?.[agent] || []).find((x) => pat.test(x.name)); if (s) out.push({ label: label || s.name, path: s.path }) }
    add('HDBET', /res-02_T1w/, 'MRI T1w (HD-BET)')
    add('Cellpose', /img02/, 'cells img02 (Cellpose)')
    add('MedSAM', /FLARE22.*nii/, 'abdominal CT (MedSAM)')
    add('MedSAM', /2DBox_CXR/, 'CXR demo npz')
    add('nnUNet', /Task04/, 'MSD Task04 (nnU-Net)')
    out.push({ label: 'pathmnist (MedMNIST)', path: 'pathmnist' })
    return out
  }, [samples])

  const upload = async (file) => {
    if (!file) return
    setUploading(true); setError(''); setPlan(null); setRun(null); setReport(null)
    try { const r = await api.upload(file); setPath(pickUploadPath(r)); setNotice(r.notice || ''); await detect(pickUploadPath(r)) } catch (e) { setError(String(e.message || e)) } finally { setUploading(false) }
  }

  const detect = async (p = path) => {
    if (!p) return
    setPlanning(true); setError(''); setRun(null); setReport(null)
    try { const r = await api.autoPlan(p); setPlan(r); setRecipeId(r.recipes?.[0]?.id || null) } catch (e) { setPlan(null); setError(String(e.message || e)) } finally { setPlanning(false) }
  }

  const poll = (id) => {
    clearTimeout(pollRef.current)
    pollRef.current = setTimeout(async () => {
      try {
        const r = await api.autoRunGet(id); setRun(r); onJobs?.()
        if (r.status === 'queued' || r.status === 'running') poll(id)
        else { loadRuns(); if (r.report_path) api.preview(r.report_path).then(setReport).catch(() => {}) }
      } catch (e) { setError(String(e.message || e)) }
    }, 1500)
  }

  const start = async () => {
    setError(''); setReport(null)
    try { const r = await api.autoRun(path, recipeId); setRun(r); setOpen({}); poll(r.run_id) } catch (e) { setError(String(e.message || e)) }
  }

  const show = async (id) => {
    try { const r = await api.autoRunGet(id); setRun(r); setPath(r.path); setPlan(null); setReport(null); if (r.status === 'running' || r.status === 'queued') poll(id); else if (r.report_path) api.preview(r.report_path).then(setReport).catch(() => {}) } catch (e) { setError(String(e.message || e)) }
  }

  const recipe = plan?.recipes?.find((r) => r.id === recipeId) || plan?.recipes?.[0]
  const busy = run && (run.status === 'running' || run.status === 'queued')
  const done = run ? run.steps.filter((s) => s.status === 'done').length : 0
  const runArts = run?.artifacts || []

  return (
    <section className="autopanel" style={{ '--accent': accent }}>
      <div className="auto-head">
        <div>
          <div className="wb-title">⚡ Auto <span className="dim">· drop a file, we pick the tools</span></div>
          <div className="dim auto-sub">Deterministic detection (NIfTI header, image texture, folder layout) → a recipe of chained tool calls across the agents → one report with every artifact. Manual forms below stay available.</div>
        </div>
        <div className="mono dim">{runs.length} auto runs</div>
      </div>
      <div className="auto-body">
        <div className={'dropzone' + (drag ? ' on' : '')} onDragOver={(e) => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)}
             onDrop={(e) => { e.preventDefault(); setDrag(false); upload(e.dataTransfer.files?.[0]) }}>
          <div className="pathrow">
            <input type="text" value={path} placeholder="drop a file here, upload, paste a server path (file / folder), or type a MedMNIST flag" onChange={(e) => setPath(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && detect()} />
            <label className="btn ghost small">{uploading ? 'uploading…' : 'upload'}<input type="file" hidden onChange={(e) => upload(e.target.files?.[0])} /></label>
            <button className="btn small" disabled={!path || planning || uploading} onClick={() => detect()}>{planning ? 'detecting…' : 'detect'}</button>
          </div>
          {chips.length > 0 && <div className="chips">{chips.map((c) => <button type="button" key={c.path} className={'chip' + (path === c.path ? ' on' : '')} title={c.path} onClick={() => { setPath(c.path); detect(c.path) }}>{c.label}</button>)}</div>}
          {notice && <div className="hint notice">{notice}</div>}
          {error && <div className="hint problem">⚠ {error}</div>}
        </div>

        {plan && !run && (
          <div className="auto-plan">
            <div className="auto-detect">
              <span className="kind">{KIND_LABEL[plan.kind] || plan.kind}</span>
              {plan.modality_guess && <span className="pill">{plan.modality_guess}</span>}
              <span className="mono dim">{short(plan.input_path)}</span>
            </div>
            <ul className="auto-notes">{(plan.notes || []).map((n, i) => <li key={i}>{n}</li>)}</ul>
            {plan.recipes.length === 0 && <div className="empty">No recipe for this input. Use the manual tool forms below.</div>}
            {plan.recipes.length > 1 && <div className="chips">{plan.recipes.map((r) => <button type="button" key={r.id} className={'chip' + (recipeId === r.id ? ' on' : '')} onClick={() => setRecipeId(r.id)}>{r.title}</button>)}</div>}
            {recipe && (
              <div className="auto-steps">
                {recipe.steps.map((s, i) => (
                  <div className="astep planned" key={i} style={{ '--c': AGENT_COLOR[s.agent] || accent }}>
                    <div className="astep-head" onClick={() => setOpen((o) => ({ ...o, ['p' + i]: !o['p' + i] }))}>
                      <span className="astep-idx mono">{i}</span>
                      <span className="astep-tool mono"><b>{s.agent}</b>.{s.tool}</span>
                      <span className="astep-label">{s.label}{s.optional ? ' (optional)' : ''}</span>
                    </div>
                    {open['p' + i] && <pre className="art-pre">{JSON.stringify(s.arguments, null, 1)}</pre>}
                  </div>
                ))}
                {(recipe.notes || []).map((n, i) => <div className="hint" key={i}>{n}</div>)}
                <div className="formfoot">
                  <button className="btn primary" onClick={start} disabled={busy}>⚡ Run automatically</button>
                  <span className="hint">{recipe.steps.length} steps · references like <code>{'${step[0].artifacts[mask]}'}</code> are resolved at run time</span>
                </div>
              </div>
            )}
          </div>
        )}

        {run && (
          <div className="auto-run">
            <div className="auto-detect">
              <span className={'pill ' + run.status}>{run.status}</span>
              <span className="kind">{KIND_LABEL[run.kind] || run.kind}</span>
              {run.modality_guess && <span className="pill">{run.modality_guess}</span>}
              <span className="mono dim">{run.recipe?.id} · run {run.run_id || run.id}{run.duration_s != null ? ` · ${run.duration_s}s` : ''}</span>
              <button className="btn ghost small" onClick={() => { setRun(null); setReport(null); if (path) detect() }}>new plan</button>
            </div>
            <div className="progress"><div className="bar" style={{ width: `${Math.round(100 * done / Math.max(1, run.steps.length))}%` }} /></div>
            <div className="auto-steps">{run.steps.map((s) => <StepRow key={s.index} s={s} accent={accent} open={!!open[s.index]} onToggle={() => setOpen((o) => ({ ...o, [s.index]: !o[s.index] }))} />)}</div>
            {(run.warnings || []).length > 0 && <div className="hint notice">{run.warnings.map((w, i) => <div key={i}>⚠ {w}</div>)}</div>}
            {!busy && (
              <div className="auto-report">
                <div className="sec-head"><b>Final report</b>{runArts.map((a) => <a key={a.path} className="btn ghost small" href={api.fileUrl(a.path, true)}>⤓ {a.path.split('/').pop()}</a>)}</div>
                {report?.text && <pre className="art-pre report">{report.text}</pre>}
                <div className="artifacts">
                  {run.steps.flatMap((s) => (s.artifacts || []).filter((a) => IMG.test(a.path)).slice(0, 4).map((a) => <Artifact key={a.path} a={a} accent={AGENT_COLOR[s.agent] || accent} />))}
                </div>
              </div>
            )}
          </div>
        )}

        {runs.length > 0 && (
          <details className="auto-history">
            <summary className="mono dim">previous auto runs ({runs.length})</summary>
            <div className="history">{runs.map((r) => <div key={r.id} className={'hrow' + (run?.id === r.id ? ' on' : '')} onClick={() => show(r.id)}><span className={'pill ' + r.status}>{r.status}</span><span className="mono">{KIND_LABEL[r.kind] || r.kind} · {r.recipe} · {short(r.path)}</span><span className="mono dim">{new Date(r.created_at * 1000).toLocaleString()}</span><span className="mono dim">{r.n_done}/{r.n_steps}{r.duration_s != null ? ` · ${r.duration_s}s` : ''}</span></div>)}</div>
          </details>
        )}
      </div>
    </section>
  )
}
