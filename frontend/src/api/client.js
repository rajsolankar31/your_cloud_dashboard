async function j(path, opts = {}) {
  const r = await fetch('/api' + path, { headers: { 'Content-Type': 'application/json' }, ...opts })
  if (!r.ok) {
    const e = await r.json().catch(() => ({}))
    throw new Error(e.detail || r.statusText)
  }
  return r.json()
}
const send = (method) => (path, body) => j(path, { method, body: body ? JSON.stringify(body) : undefined })
const post = (path, body) => j(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined })

export const api = {
  providers: () => j('/providers'),
  resources: () => j('/resources'),
  history: (id) => j(`/resources/${encodeURIComponent(id)}/history`),
  sync: (provider) => post(provider ? `/sync/${provider}` : '/sync'),
  requestAction: (resource_id, action) => post('/actions', { resource_id, action }),
  confirm: (id, confirm_name) => post(`/actions/${id}/confirm`, { confirm_name }),
  cancel: (id) => post(`/actions/${id}/cancel`),
  audit: () => j('/audit'),
  overview: () => j('/overview'),
  createResource: (b) => post('/resources', b),
  updateResource: (id, b) => send('PATCH')(`/resources/${encodeURIComponent(id)}`, b),
  deleteResource: (id) => send('DELETE')(`/resources/${encodeURIComponent(id)}`),
  setBudget: (p, monthly_limit) => send('PUT')(`/budgets/${p}`, { monthly_limit }),
  connections: () => j('/connections'),
  saveConnection: (p, b) => send('PUT')(`/connections/${p}`, b),
  setMode: (use_mock) => send('PUT')('/settings', { use_mock }),
}
