import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

// Daily values per logged day. Days without logs stay empty (never interpolated).
export default function TrendChart({ data, dataKey, unit, threshold, thresholdLabel, color = 'rgb(var(--brand))', title, height = 200 }) {
  const rows = data.map((d) => ({ ...d, label: new Date(d.date + 'T00:00:00').toLocaleDateString(undefined, { day: 'numeric', month: 'short' }) }))
  const logged = rows.filter((r) => r[dataKey] !== null && r[dataKey] !== undefined)
  return (
    <figure className="panel p-4">
      <figcaption className="mb-2 flex items-baseline justify-between gap-2">
        <span className="font-semibold">{title}</span>
        <span className="text-xs text-muted">{unit}, per logged day</span>
      </figcaption>
      {logged.length === 0 ? <p className="py-8 text-center text-sm text-muted">No logged days in this period.</p> : (
        <div style={{ height }} role="img" aria-label={`${title}: ${logged.length} logged days`}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={rows} margin={{ top: 6, right: 4, left: -18, bottom: 0 }}>
              <CartesianGrid stroke="rgb(var(--line))" vertical={false} />
              <XAxis dataKey="label" tick={{ fontSize: 11, fill: 'rgb(var(--muted))' }} tickLine={false} axisLine={false} interval="preserveStartEnd" minTickGap={18} />
              <YAxis tick={{ fontSize: 11, fill: 'rgb(var(--muted))' }} tickLine={false} axisLine={false} width={48} />
              <Tooltip cursor={{ fill: 'rgb(var(--ink) / 0.05)' }} contentStyle={{ borderRadius: 10, border: '1px solid rgb(var(--line))', fontSize: 13 }}
                formatter={(v) => (v === null ? ['Not logged', ''] : [`${Math.round(v * 10) / 10} ${unit}`, title])} />
              {threshold && <ReferenceLine y={threshold} stroke="rgb(var(--caution))" strokeDasharray="4 4" label={{ value: thresholdLabel, position: 'insideTopRight', fontSize: 11, fill: 'rgb(var(--caution))' }} />}
              <Bar dataKey={dataKey} fill={color} radius={[3, 3, 0, 0]} maxBarSize={22} isAnimationActive={false} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </figure>
  )
}
