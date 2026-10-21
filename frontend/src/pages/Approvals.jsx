import { useState } from 'react'
import { api } from '../api/client.js'

function Pending({ a, onDone }) {
  const [name, setName] = useState('')
  const [err, setErr] = useState('')
  const run = async (fn) => { try { setErr(''); await fn(); onDone() } catch (e) { setErr(e.message) } }
  return (
    <article className="pending">
      <h3>{a.action} {a.resource_name}</h3>
      <p>{a.impact}</p>
      <label>Type <b>{a.resource_name}</b> to confirm
        <input value={name} onChange={(e) => setName(e.target.value)} autoComplete="off" />
      </label>
      {err && <p className="err">{err}</p>}
      <div className="row">
        <button disabled={name !== a.resource_name} onClick={() => run(() => api.confirm(a.id, name))}>Confirm {a.action}</button>
        <button className="ghost" onClick={() => run(() => api.cancel(a.id))}>Cancel</button>
      </div>
    </article>
  )
}

export default function Approvals({ audit, onDone }) {
  const pending = audit.filter((a) => a.status === 'pending')
  return (
    <>
      <section className="panel">
        <h2>Waiting for approval</h2>
        {pending.length ? pending.map((a) => <Pending key={a.id} a={a} onDone={onDone} />)
          : <p className="muted">Nothing pending. Request an action from the inventory.</p>}
      </section>
      <section className="panel">
        <h2>Audit log</h2>
        <div className="scroll">
          <table>
            <thead><tr><th>Requested</th><th>Action</th><th>Resource</th><th>Provider</th><th>Result</th><th>Detail</th></tr></thead>
            <tbody>
              {audit.map((a) => (
                <tr key={a.id}>
                  <td className="muted">{new Date(a.requested_at).toLocaleString()}</td>
                  <td>{a.action}</td><td>{a.resource_name}</td><td>{a.provider}</td>
                  <td><span className={`badge ${a.status}`}>{a.status}</span></td>
                  <td className="muted">{a.detail}</td>
                </tr>
              ))}
              {!audit.length && <tr><td colSpan={6} className="muted">No actions recorded yet.</td></tr>}
            </tbody>
          </table>
        </div>
      </section>
    </>
  )
}
