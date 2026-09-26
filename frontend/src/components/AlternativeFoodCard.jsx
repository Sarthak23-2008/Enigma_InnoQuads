import { Link } from 'react-router-dom'
import RiskBadge from './RiskBadge'

export default function AlternativeFoodCard({ alt }) {
  return (
    <Link to={`/check/search?q=${encodeURIComponent(alt.name)}`} className="group flex flex-col gap-1.5 rounded-xl border border-line bg-surface p-3.5 hover:border-brand">
      <div className="flex items-start justify-between gap-2">
        <span className="font-semibold text-ink group-hover:text-brand">{alt.name}</span>
        <RiskBadge level={alt.risk_level} size="sm" />
      </div>
      <p className="text-sm text-muted">{alt.reason}</p>
      <p className="text-xs text-muted">Checked against your profile. Check it yourself before you eat it.</p>
    </Link>
  )
}
