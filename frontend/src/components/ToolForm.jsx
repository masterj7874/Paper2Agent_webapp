// Renders a form from a tool's JSON Schema (as exposed by the MCP server) — string/number/bool/enum/array + file pickers.
import { Fragment, useEffect, useMemo, useState } from 'react'
import { api } from '../lib/api'

const isPathParam = (name, desc) => /(_path|_dir|_root|_file|_folder)$|^(path|file|folder|directory)$/.test(name) || /^(absolute |server )?(path|file path|directory|folder)\b/i.test((desc || '').trim())
const typeOf = (s) => {
  if (!s) return 'string'
  if (s.enum) return 'enum'
  if (s.type) return Array.isArray(s.type) ? s.type.find((t) => t !== 'null') || 'string' : s.type
  if (s.anyOf) { const t = s.anyOf.map((x) => x.enum ? 'enum' : x.type).filter((t) => t && t !== 'null'); return t[0] || 'string' }
  return 'string'
}
const enumOf = (s) => s?.enum || s?.anyOf?.find((x) => x.enum)?.enum || null
const defaultOf = (s) => (s && 'default' in s ? s.default : undefined)

export default function ToolForm({ agent, tool, samples, onSubmit, busy }) {
  const props = tool?.inputSchema?.properties || {}
  const required = new Set(tool?.inputSchema?.required || [])
  const [values, setValues] = useState({})
  const [uploading, setUploading] = useState(null)
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [converted, setConverted] = useState({})   // param -> [{kind, path, description}]
  const [notices, setNotices] = useState({})       // param -> text
  const [problems, setProblems] = useState({})     // param -> validation text

  useEffect(() => {
    const init = {}
    for (const [k, s] of Object.entries(props)) { const d = defaultOf(s); if (d !== undefined && d !== null) init[k] = d }
    setValues(init)
  }, [tool?.name])

  const order = useMemo(() => Object.keys(props).sort((a, b) => (required.has(b) - required.has(a))), [tool?.name])
  const set = (k, v) => setValues((o) => ({ ...o, [k]: v }))

  const onFile = async (k, file) => {
    if (!file) return
    setUploading(k)
    try {
      const r = await api.upload(file)
      const desc = props[k]?.description || ''
      const conv = r.converted || []
      const wantsDir = /(_dir|_root|_folder)$/.test(k) || (/folder|directory/i.test(desc) && !/\bfile\b/i.test(desc))
      const wantsVolume = /nii|nifti|volume|3d|ct|mr/i.test(desc) && !/png|jpg|2d image/i.test(desc)
      let pick = r.path
      if (conv.length) {
        const byKind = (kind) => conv.find((c) => c.kind === kind)?.path
        pick = (wantsDir && byKind('folder')) || (wantsVolume && byKind('volume')) || byKind('image') || byKind('volume') || byKind('folder') || r.path
      }
      set(k, pick)
      setConverted((o) => ({ ...o, [k]: conv }))
      setNotices((o) => ({ ...o, [k]: r.notice || '' }))
    } finally { setUploading(null) }
  }

  // accepted extensions inferred from the parameter description, e.g. "(.nii.gz)", "png/jpg/tif", "npz"
  const acceptedExts = (desc) => {
    const found = new Set()
    for (const m of (desc || '').matchAll(/\b(nii\.gz|nii|nrrd|mha|mhd|npz|npy|png|jpe?g|tiff?|csv|json|zip|bmp)\b/gi)) found.add(m[1].toLowerCase().replace('jpeg', 'jpg').replace('tiff', 'tif'))
    return [...found]
  }
  const checkPath = (k, v) => {
    const exts = acceptedExts(props[k]?.description)
    if (!v || !exts.length || /\/$/.test(v)) return ''
    const low = v.toLowerCase()
    if (/\.(avi|mp4|mov|mkv|wmv|mpg|mpeg|webm)$/.test(low)) return 'this is a video file; use the converted frames/NIfTI paths created at upload'
    if (/\.(dcm|dicom)$/.test(low) && !exts.includes('dcm')) return 'DICOM files are converted to NIfTI at upload; pick the converted path'
    const ok = exts.some((e) => low.endsWith('.' + e) || (e === 'nii' && low.endsWith('.nii.gz')))
    const hasExt = /\.[a-z0-9]{2,5}(\.gz)?$/.test(low)
    return ok || !hasExt ? '' : `expected ${exts.join('/')} (got .${low.split('.').pop()})`
  }

  const submit = (e) => {
    e.preventDefault()
    const probs = {}
    for (const k of Object.keys(props)) {
      const v = values[k]
      if (required.has(k) && (v === undefined || v === '' || v === null)) probs[k] = 'required'
      else if (isPathParam(k, props[k]?.description) && typeof v === 'string') { const w = checkPath(k, v); if (w) probs[k] = w }
    }
    setProblems(probs)
    if (Object.keys(probs).length) return
    const out = {}
    for (const [k, s] of Object.entries(props)) {
      let v = values[k]
      if (v === undefined || v === '' || v === null) continue
      const t = typeOf(s)
      if (t === 'integer') v = parseInt(v, 10)
      else if (t === 'number') v = parseFloat(v)
      else if (t === 'array' && typeof v === 'string') { try { v = JSON.parse(v) } catch { v = v.split(/[,\s]+/).filter(Boolean).map((x) => (isNaN(+x) ? x : +x)) } }
      if (t === 'integer' || t === 'number') { if (Number.isNaN(v)) continue }
      out[k] = v
    }
    onSubmit(out)
  }

  const basic = order.filter((k) => required.has(k) || isPathParam(k, props[k]?.description) || ['channels', 'boxes', 'prompts', 'points', 'flag', 'split', 'model_type', 'modality', 'device'].includes(k))
  const advanced = order.filter((k) => !basic.includes(k))

  // Render fields directly so typing does not remount a nested component and lose focus.
  const renderField = (k) => {
    const s = props[k] || {}
    const t = typeOf(s), en = enumOf(s), v = values[k]
    const desc = s.description || ''
    const label = <label className="fld-label"><span className="fld-name">{k}{required.has(k) && <b className="req">*</b>}</span><span className="fld-desc" title={desc}>{desc}</span></label>
    if (t === 'boolean') return <div className="fld"><label className="switch"><input type="checkbox" checked={!!v} onChange={(e) => set(k, e.target.checked)} /><span className="slider" /></label>{label}</div>
    if (en) return <div className="fld">{label}<select value={v ?? ''} onChange={(e) => set(k, e.target.value)}><option value="">— default —</option>{en.map((o) => <option key={o} value={o}>{String(o)}</option>)}</select></div>
    if (isPathParam(k, desc)) {
      // sample chips only make sense for *input* paths; a directory-typed param gets the sample's folder
      const isInput = !/output|out_dir|save|model|checkpoint|pretrained|weights|result/i.test(k)
      const wantsDir = /(_dir|_root|_folder)$/.test(k) || (/folder|directory/i.test(desc) && !/\bfile\b/i.test(desc))
      const dirOf = (pth) => pth.replace(/\/[^/]+$/, '')
      const seen = new Set()
      const wantsGT = /ground_truth|^gt|_gt|reference|label/i.test(k)
      const isGT = (x) => /ground truth|label/i.test(x.description || '')
      let mine = !isInput ? [] : (samples || []).filter((x) => (wantsGT ? isGT(x) : !isGT(x)))
      if (wantsGT && mine.length === 0) mine = samples || []
      mine = mine.filter((x) => wantsDir || !x.is_dir).map((x) => wantsDir ? (x.is_dir ? x : { ...x, path: dirOf(x.path), name: dirOf(x.path).split('/').slice(-2).join('/') }) : x).filter((x) => (seen.has(x.path) ? false : seen.add(x.path)))
      const counts = mine.reduce((m, x) => (m[x.name] = (m[x.name] || 0) + 1, m), {})
      mine = mine.map((x) => counts[x.name] > 1 ? { ...x, name: dirOf(x.path).split('/').pop() + '/' + x.name } : x)
      return <div className="fld">{label}
        <div className="pathrow">
          <input type="text" value={v ?? ''} placeholder="server path, upload, or pick a sample" onChange={(e) => set(k, e.target.value)} />
          <label className="btn ghost small">{uploading === k ? 'uploading…' : 'upload'}<input type="file" hidden onChange={(e) => onFile(k, e.target.files?.[0])} /></label>
        </div>
        {mine.length > 0 && <div className="chips">{mine.slice(0, 12).map((s) => <button type="button" key={s.path} className={'chip' + (v === s.path ? ' on' : '')} title={s.description + ' · ' + s.path} onClick={() => set(k, s.path)}>{s.name}</button>)}</div>}
        {(converted[k] || []).length > 0 && <div className="chips">{converted[k].map((c) => <button type="button" key={c.path} className={'chip conv' + (v === c.path ? ' on' : '')} title={c.description + ' · ' + c.path} onClick={() => set(k, c.path)}>⟳ {c.kind}: {c.path.split('/').pop()}</button>)}</div>}
        {notices[k] && <div className="hint notice">{notices[k]}</div>}
        {(problems[k] || (typeof v === 'string' && checkPath(k, v))) && <div className="hint problem">⚠ {problems[k] || checkPath(k, v)}</div>}
        {acceptedExts(desc).length > 0 && <div className="hint">accepted: {acceptedExts(desc).join(', ')}</div>}
      </div>
    }
    if (t === 'array') return <div className="fld">{label}<input type="text" value={typeof v === 'string' ? v : (v === undefined ? '' : JSON.stringify(v))} placeholder='JSON, e.g. [[95,255,190,350]] or 0,0' onChange={(e) => set(k, e.target.value)} /></div>
    if (t === 'integer' || t === 'number') return <div className="fld">{label}<input type="number" step={t === 'integer' ? 1 : 'any'} value={v ?? ''} onChange={(e) => set(k, e.target.value)} /></div>
    return <div className="fld">{label}<input type="text" value={v ?? ''} onChange={(e) => set(k, e.target.value)} /></div>
  }

  return (
    <form className="toolform" onSubmit={submit}>
      <div className="grid2">{basic.map((k) => <Fragment key={k}>{renderField(k)}</Fragment>)}</div>
      {advanced.length > 0 && <button type="button" className="linkbtn" onClick={() => setShowAdvanced((s) => !s)}>{showAdvanced ? '▾' : '▸'} advanced parameters ({advanced.length})</button>}
      {showAdvanced && <div className="grid2 adv">{advanced.map((k) => <Fragment key={k}>{renderField(k)}</Fragment>)}</div>}
      <div className="formfoot">
        <button className="btn primary" disabled={busy || !!uploading} type="submit">{busy ? 'running…' : `▶ run ${tool?.name}`}</button>
        <span className="hint">runs on the {agent} MCP server · outputs go to a fresh folder per call</span>
      </div>
    </form>
  )
}
