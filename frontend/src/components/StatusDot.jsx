export const STATUS_COLORS = {
  running: '#1F7A5A', stopped: '#7B8794', deploying: '#C58A12', error: '#B3412F', unknown: '#A9B2BA',
}

export default function StatusDot({ status }) {
  return (
    <span className="status">
      <i style={{ background: STATUS_COLORS[status] || STATUS_COLORS.unknown }} />
      {status}
    </span>
  )
}
