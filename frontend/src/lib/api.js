const J = async (r) => {
  const body = await r.json().catch(() => null)
  if (!r.ok) {
    const detail = body?.detail
    throw new Error(typeof detail === 'string' ? detail : Array.isArray(detail) ? detail.map((item) => item.msg).join(' · ') : '서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.')
  }
  if (body === null) throw new Error('서버 응답을 읽을 수 없습니다.')
  return body
}
export const api = {
  manuscriptCapabilities: () => fetch('/api/manuscripts/capabilities').then(J),
  manuscriptRuns: () => fetch('/api/manuscripts').then(J),
  manuscriptRun: (id) => fetch(`/api/manuscripts/${encodeURIComponent(id)}`).then(J),
  createManuscript: (manuscript, results, options) => {
    const data = new FormData()
    data.append('manuscript', manuscript)
    results.forEach(file => data.append('results', file))
    data.append('options', JSON.stringify(options))
    return fetch('/api/manuscripts', { method: 'POST', body: data }).then(J)
  },
  cancelManuscript: (id) => fetch(`/api/manuscripts/${encodeURIComponent(id)}/cancel`, { method: 'POST' }).then(J),
  reviseManuscript: (id, files, instructions, journal, journalRequirements) => {
    const data = new FormData()
    files.forEach(file => data.append('files', file)); data.append('instructions', instructions)
    data.append('journal', journal); data.append('journal_requirements', journalRequirements)
    return fetch(`/api/manuscripts/${encodeURIComponent(id)}/revise`, { method: 'POST', body: data }).then(J)
  },
  researchInventory: () => fetch('/api/research/inventory').then(J),
  scanResearch: () => fetch('/api/research/inventory/scan', { method: 'POST' }).then(J),
  researchJournals: (q = '') => fetch(`/api/research/journals?q=${encodeURIComponent(q)}`).then(J),
  agents: () => fetch('/api/agents').then(J),
  tools: (name) => fetch(`/api/agents/${encodeURIComponent(name)}/tools`).then(J),
  restart: (name) => fetch(`/api/agents/${encodeURIComponent(name)}/restart`, { method: 'POST' }).then(J),
  samples: () => fetch('/api/samples').then(J),
  stats: () => fetch('/api/stats').then(J),
  upload: (file) => { const fd = new FormData(); fd.append('file', file); return fetch('/api/upload', { method: 'POST', body: fd }).then(J) },
  submit: (agent, tool, args) => fetch('/api/jobs', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ agent, tool, arguments: args }) }).then(J),
  jobs: (limit = 40) => fetch(`/api/jobs?limit=${limit}`).then(J),
  job: (id) => fetch(`/api/jobs/${id}`).then(J),
  fileUrl: (path, download = false) => `/api/files?path=${encodeURIComponent(path)}${download ? '&download=true' : ''}`,
  preview: (path) => fetch(`/api/files/preview?path=${encodeURIComponent(path)}`).then(J),
  paper: (skill) => fetch(`/api/papers/${skill}`).then(J),
  section: (skill, file, heading) => fetch(`/api/papers/${skill}/section?file=${encodeURIComponent(file)}&heading=${encodeURIComponent(heading)}`).then(J),
  search: (skill, q) => fetch(`/api/papers/${skill}/search?q=${encodeURIComponent(q)}&limit=12`).then(J),
  assetUrl: (skill, cat, name) => `/api/papers/${skill}/asset/${cat}/${encodeURIComponent(name)}`,
  autoPlan: (path) => fetch('/api/auto/plan', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ path }) }).then(J),
  autoRun: (path, recipe_id, project) => fetch('/api/auto/run', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ path, recipe_id, project }) }).then(J),
  autoRuns: (limit = 20) => fetch(`/api/auto/runs?limit=${limit}`).then(J),
  autoRunGet: (id) => fetch(`/api/auto/runs/${id}`).then(J),
  paperCapabilities: () => fetch('/api/paper-runs/capabilities').then(J),
  paperRuns: () => fetch('/api/paper-runs').then(J),
  paperRun: (id) => fetch(`/api/paper-runs/${encodeURIComponent(id)}`).then(J),
  createPaperAgent: (file, repository = '', goal = '') => {
    const data = new FormData()
    data.append('file', file); data.append('repository', repository); data.append('goal', goal)
    return fetch('/api/paper-runs', { method: 'POST', body: data }).then(J)
  },
  cancelPaperRun: (id) => fetch(`/api/paper-runs/${encodeURIComponent(id)}/cancel`, { method: 'POST' }).then(J),
  retryPaperRun: (id, repository, goal) => fetch(`/api/paper-runs/${encodeURIComponent(id)}/retry`, {
    method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ repository, goal }),
  }).then(J),
}
