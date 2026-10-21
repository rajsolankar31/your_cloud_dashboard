import { useCallback, useEffect, useState } from 'react'
import { api } from './api/client.js'
import Dashboard from './pages/Dashboard.jsx'
import Inventory from './pages/Inventory.jsx'
import Connections from './pages/Connections.jsx'
import Approvals from './pages/Approvals.jsx'

export default function App() {
  const [tab, setTab] = useState('dashboard')
  const [providers, setProviders] = useState([])
  const [resources, setResources] = useState([])
  const [audit, setAudit] = useState([])
  const [overview, setOverview] = useState(null)
  const [auto, setAuto] = useState(0)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const load = useCallback(async () => {
    try {
      const [p, r, a, o] = await Promise.all([api.providers(), api.resources(), api.audit(), api.overview()])
      setProviders(p); setResources(r); setAudit(a); setOverview(o); setError('')
    } catch (e) { setError('Cannot reach the backend. Start it with: uvicorn app.main:app --reload') }
  }, [])
  useEffect(() => { load() }, [load])

  const sync = async (key) => {
    setBusy(true)
    try { await api.sync(key); await load() } finally { setBusy(false) }
  }
  useEffect(() => {
    if (!auto) return
    const t = setInterval(() => api.sync().then(load).catch(() => {}), auto * 1000)
    return () => clearInterval(t)
  }, [auto, load])
  const pendingCount = audit.filter((a) => a.status === 'pending').length

  return (
    <div className="app">
      <header className="top">
        <strong className="brand">Unified Cloud Dashboard</strong>
        <nav>
          {[['dashboard', 'Dashboard'], ['inventory', 'Inventory'], ['approvals', `Approvals${pendingCount ? ` (${pendingCount})` : ''}`], ['connections', 'Connections']].map(([k, l]) => (
            <button key={k} className={tab === k ? 'on' : ''} onClick={() => setTab(k)}>{l}</button>
          ))}
        </nav>
        <select className="auto" value={auto} onChange={(e) => setAuto(Number(e.target.value))} aria-label="Auto refresh">
          <option value={0}>Auto refresh: off</option><option value={30}>Every 30s</option><option value={60}>Every 60s</option>
        </select>
        <button className="ghost" disabled={busy} onClick={() => sync()}>{busy ? 'Refreshing…' : 'Refresh all'}</button>
      </header>
      <main>
        {error && <p className="err banner">{error}</p>}
        {tab === 'dashboard' && <Dashboard providers={providers} resources={resources} overview={overview} onSync={sync} busy={busy} />}
        {tab === 'inventory' && <Inventory resources={resources} providers={providers} onRequested={() => { load(); setTab('approvals') }} onChanged={load} />}
        {tab === 'connections' && <Connections overview={overview} onChanged={load} />}
        {tab === 'approvals' && <Approvals audit={audit} onDone={load} />}
      </main>
    </div>
  )
}
