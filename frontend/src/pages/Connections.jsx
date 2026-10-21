import { useEffect, useState } from 'react'
import { api } from '../api/client.js'

function Card({ p, budget, onDone }) {
  const [vals, setVals] = useState({})
  const [msg, setMsg] = useState('')
  const save = async (clear) => {
    const body = clear ? Object.fromEntries(p.fields.map((f) => [f.name, ''])) : vals
    await api.saveConnection(p.key, body); setVals({}); setMsg(clear ? 'Credentials removed.' : 'Saved. Use Refresh to sync.'); onDone()
  }
  return (
    <article className="provider">
      <h2>{p.label}</h2>
      {p.fields.length === 0 && <p className="muted">Live connection is not built yet (roadmap Phase 3).</p>}
      {p.fields.map((f) => (
        <label key={f.name} className="field">{f.name} {f.set && <span className="badge live">saved</span>}
          <input type={f.secret ? 'password' : 'text'} autoComplete="off" placeholder={f.set ? 'Saved. Type to replace.' : ''}
            value={vals[f.name] || ''} onChange={(e) => setVals({ ...vals, [f.name]: e.target.value })} />
        </label>
      ))}
      {p.fields.length > 0 && <div className="row">
        <button disabled={!Object.values(vals).some(Boolean)} onClick={() => save(false)}>Save</button>
        <button className="ghost" onClick={() => save(true)}>Remove</button>
      </div>}
      {msg && <p className="muted">{msg}</p>}
    </article>
  )
}

export default function Connections({ overview, onChanged }) {
  const [c, setC] = useState(null)
  const [budgets, setBudgets] = useState({})
  const load = () => api.connections().then(setC)
  useEffect(() => { load() }, [])
  if (!c) return <p className="muted">Loading…</p>
  const refresh = () => { load(); onChanged() }
  return (
    <>
      <section className="panel">
        <h2>Data source</h2>
        <p className="muted">Sample data lets you try the dashboard with no accounts. Switching clears synced resources and notes on them, and keeps your manual entries.</p>
        <div className="row">
          <button className={c.use_mock ? '' : 'ghost'} onClick={async () => { await api.setMode(true); refresh() }}>Sample data</button>
          <button className={c.use_mock ? 'ghost' : ''} onClick={async () => { await api.setMode(false); refresh() }}>Live accounts</button>
        </div>
      </section>
      <section className="providers">{c.providers.map((p) => <Card key={p.key} p={p} onDone={refresh} />)}</section>
      <section className="panel">
        <h2>Monthly budgets</h2>
        <p className="muted">You get an alert at 80% and 100% of the total cost you entered per provider.</p>
        {(overview?.costs || []).map((r) => (
          <div key={r.provider} className="cost">
            <span>{r.label}</span>
            <input type="number" min="0" placeholder="No budget" value={budgets[r.provider] ?? r.budget ?? ''}
              onChange={(e) => setBudgets({ ...budgets, [r.provider]: e.target.value })} />
            <button className="ghost" onClick={async () => { await api.setBudget(r.provider, Number(budgets[r.provider] || 0) || null); onChanged() }}>Save</button>
          </div>
        ))}
      </section>
    </>
  )
}
