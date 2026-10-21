import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { STATUS_COLORS } from '../components/StatusDot.jsx'

export default function StatusChart({ providers, resources }) {
  const data = providers.map((p) => {
    const row = { name: p.label.replace(/ \(.*\)/, '') }
    resources.filter((r) => r.provider === p.key).forEach((r) => { row[r.status] = (row[r.status] || 0) + 1 })
    return row
  })
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 16 }}>
        <CartesianGrid horizontal={false} stroke="#D5DDDB" />
        <XAxis type="number" allowDecimals={false} stroke="#5B6B73" />
        <YAxis type="category" dataKey="name" width={90} stroke="#5B6B73" />
        <Tooltip />
        <Legend />
        {Object.keys(STATUS_COLORS).map((s) => (
          <Bar key={s} dataKey={s} stackId="a" fill={STATUS_COLORS[s]} />
        ))}
      </BarChart>
    </ResponsiveContainer>
  )
}
