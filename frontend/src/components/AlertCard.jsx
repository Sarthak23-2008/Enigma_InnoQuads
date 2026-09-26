import { Link } from 'react-router-dom'
import { TrendingUp } from 'lucide-react'

// Pattern alert (Engine 2). Uses caution styling — patterns are observations, never diagnoses.
export default function AlertCard({ alert, tryInstead }) {
  return (
    <div className="rounded-panel border-l-4 border-caution bg-caution-soft/70 p-4">
      <div className="flex items-start gap-3">
        <TrendingUp className="mt-0.5 h-5 w-5 shrink-0 text-caution" aria-hidden />
        <div className="min-w-0">
          <p className="font-semibold text-ink">{alert.message}</p>
          <p className="mt-1 text-sm text-ink/80">{alert.action}</p>
          {alert.contributors?.length > 0 && (
            <p className="mt-2 text-sm text-muted">Biggest contributors: {alert.contributors.join(', ')}</p>
          )}
          {tryInstead?.length > 0 && (
            <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
              <span className="font-semibold">Try instead:</span>
              {tryInstead.map((f) => (
                <Link key={f} to={`/check/search?q=${encodeURIComponent(f)}`} className="chip border-brand/30 bg-surface text-brand hover:border-brand">{f}</Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
