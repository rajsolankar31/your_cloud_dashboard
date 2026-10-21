import { Fragment, useState } from 'react'
import { api } from '../api/client.js'
import StatusDot from '../components/StatusDot.jsx'

const STATUS = ['running', 'stopped', 'deploying', 'error', 'unknown']

function Form({ init, custom, onSave, onDelete, onCancel }) {
  const [f, setF] = useState({ ...init, monthly_cost: init.monthly_cost ?? '' })
  const [err, setErr] = useState('')
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const save = async () => {
    try {
      setErr('')
      await onSave({ ...f, monthly_cost: f.monthly_cost === '' ? null : Number(f.monthly_cost) })
    } catch (e) { setErr(e.message) }
  }
  return (
    <div className="form">
      {custom && <>
        <label>Name<input value={f.name || ''} onChange={set('name')} /></label>
        <label>Type<input value={f.resource_type || ''} onChange={set('resource_type')} placeholder="server, domain, database" /></label>
        <label>Region<input value={f.region || ''} onChange={set('region')} /></label>
        <label>Status<select value={f.status} onChange={set('status')}>{STATUS.map((s) => <option key={s}>{s}</option>)}</select></label>
      </>}
      <label>Owner<input value={f.owner || ''} onChange={set('owner')} /></label>
      <label>Monthly cost<input type="number" min="0" value={f.monthly_cost} onChange={set('monthly_cost')} /></label>
      <label>Tags (comma separated)<input value={f.tags || ''} onChange={set('tags')} /></label>
      <label className="wide">Notes<textarea rows={3} value={f.notes || ''} onChange={set('notes')} /></label>
      {err && <p className="err wide">{err}</p>}
      <div className="row wide">
        <button onClick={save}>Save</button>
        <button className="ghost" onClick={onCancel}>Close</button>
        {onDelete && <button className="ghost danger" onClick={onDelete}>Delete</button>}
      </div>
    </div>
  )
}

export default function Inventory({ resources, providers, onRequested, onChanged }) {
  const [filter, setFilter] = useState('all')
  const [q, setQ] = useState('')
  const [open, setOpen] = useState(null)
  const [adding, setAdding] = useState(false)
  const [hist, setHist] = useState([])
  const [err, setErr] = useState('')
  const rows = resources.filter((r) => (filter === 'all' || r.provider === filter) &&
    `${r.name} ${r.tags || ''} ${r.owner || ''}`.toLowerCase().includes(q.toLowerCase()))

  const toggle = async (id) => {
    if (open === id) return setOpen(null)
    setOpen(id); setHist(await api.history(id))
  }
  const request = async (id, action) => {
    try { setErr(''); await api.requestAction(id, action); onRequested() } catch (e) { setErr(e.message) }
  }
  const remove = async (r) => {
    if (!window.confirm(`Delete "${r.name}"? This only removes it from this dashboard.`)) return
    await api.deleteResource(r.id); setOpen(null); onChanged()
  }

  return (
    <section className="panel">
      <div className="bar">
        <h2>Inventory</h2>
        <div className="row">
          <input placeholder="Search name, tag, owner" value={q} onChange={(e) => setQ(e.target.value)} />
          <select value={filter} onChange={(e) => setFilter(e.target.value)} aria-label="Filter by provider">
            <option value="all">All providers</option>
            {providers.map((p) => <option key={p.key} value={p.key}>{p.label}</option>)}
          </select>
          <button onClick={() => setAdding(!adding)}>{adding ? 'Close' : 'Add resource'}</button>
        </div>
      </div>
      {adding && (
        <Form custom init={{ name: '', resource_type: 'server', region: '', status: 'running' }}
          onCancel={() => setAdding(false)}
          onSave={async (b) => { await api.createResource(b); setAdding(false); onChanged() }} />
      )}
      {err && <p className="err">{err}</p>}
      <div className="scroll">
        <table>
          <thead><tr><th>Name</th><th>Provider</th><th>Type</th><th>Status</th><th>Owner</th><th>Cost</th><th /></tr></thead>
          <tbody>
            {rows.map((r) => (
              <Fragment key={r.id}>
                <tr>
                  <td><button className="link" onClick={() => toggle(r.id)}>{r.name}</button>
                    {r.tags && <div className="muted">{r.tags}</div>}</td>
                  <td>{r.provider}</td><td>{r.resource_type.replace('_', ' ')}</td>
                  <td><StatusDot status={r.status} />{r.stale && <span className="badge stale">stale</span>}</td>
                  <td>{r.owner}</td><td>{r.monthly_cost ?? ''}</td>
                  <td className="actions">
                    {r.actions.map((a) => <button key={a} className="ghost" onClick={() => request(r.id, a)}>{a}</button>)}
                  </td>
                </tr>
                {open === r.id && (
                  <tr className="hist"><td colSpan={7}>
                    <p>History ({hist.length}): {hist.slice(0, 40).map((h, i) => <span key={i} title={`${h.status} at ${h.checked_at}`}><StatusDot status={h.status} /> </span>)}</p>
                    <Form init={r} custom={r.provider === 'custom'} onCancel={() => setOpen(null)}
                      onDelete={r.provider === 'custom' ? () => remove(r) : null}
                      onSave={async (b) => { await api.updateResource(r.id, b); onChanged() }} />
                  </td></tr>
                )}
              </Fragment>
            ))}
            {!rows.length && <tr><td colSpan={7} className="muted">Nothing here yet. Use Add resource, or connect a provider.</td></tr>}
          </tbody>
        </table>
      </div>
    </section>
  )
}
