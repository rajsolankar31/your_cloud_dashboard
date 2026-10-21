import StatusChart from '../charts/StatusChart.jsx'

const MODE = { mock: 'Sample data', live: 'Live', unconfigured: 'Not connected', manual: 'Added by you' }
const fmt = (t) => (t ? new Date(t).toLocaleString() : 'never')

export default function Dashboard({ providers, resources, overview, onSync, busy }) {
  const alerts = overview?.alerts || []
  return (
    <>
      <section className="summary">
        <h1>{resources.length} resources across {providers.filter((p) => p.resources).length} providers</h1>
        <p>{alerts.length ? `${alerts.length} alert${alerts.length > 1 ? 's' : ''} need attention.` : 'No alerts. Everything reported is healthy.'}</p>
      </section>
      {alerts.length > 0 && (
        <section className="panel">
          <h2>Alerts</h2>
          <ul className="alerts">{alerts.map((a, i) => <li key={i} className={a.level}>{a.text}</li>)}</ul>
        </section>
      )}
      <section className="providers">
        {providers.map((p) => (
          <article key={p.key} className="provider">
            <header><h2>{p.label}</h2><span className={`badge ${p.mode}`}>{MODE[p.mode]}</span></header>
            <p className="big">{p.resources} <small>resources</small></p>
            {p.mode !== 'manual' && <p className="muted">Last sync: {fmt(p.last_sync)}</p>}
            {p.error && <p className="err">{p.error}</p>}
            {p.mode !== 'manual' && (
              <button disabled={busy || p.mode === 'unconfigured'} onClick={() => onSync(p.key)}>
                {p.mode === 'unconfigured' ? 'Connect in Connections' : 'Refresh'}
              </button>
            )}
          </article>
        ))}
      </section>
      <section className="panel">
        <h2>Monthly cost: {overview?.total_cost ?? 0}</h2>
        <p className="muted">{overview?.note}</p>
        {(overview?.costs || []).filter((c) => c.cost || c.budget).map((c) => {
          const pct = c.budget ? Math.min(100, (c.cost / c.budget) * 100) : 0
          return (
            <div key={c.provider} className="cost">
              <span>{c.label}</span>
              {c.budget ? <div className="meter"><i className={pct >= 100 ? 'bad' : pct >= 80 ? 'warn' : ''} style={{ width: pct + '%' }} /></div> : <span className="muted">no budget set</span>}
              <b>{c.cost}{c.budget ? ` / ${c.budget}` : ''}</b>
            </div>
          )
        })}
      </section>
      <section className="panel">
        <h2>Resources by status</h2>
        <StatusChart providers={providers} resources={resources} />
      </section>
    </>
  )
}
