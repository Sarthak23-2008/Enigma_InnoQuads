import { Link } from 'react-router-dom'

// Phase 3 "Pattern Attention Level" — an educational indicator, not a medical risk score.
export default function RiskMeter({ attention }) {
  if (!attention) return null
  const pct = Math.min(100, attention.score)
  const color = attention.level === 'Elevated' ? 'bg-high' : attention.level === 'Moderate' ? 'bg-caution' : 'bg-low'
  return (
    <section className="panel p-5" aria-labelledby="attention-title">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="attention-title" className="type-title text-lg">Pattern attention level</h2>
        <span className="font-bold">{attention.level}</span>
      </div>
      <div className="mt-3 h-3 overflow-hidden rounded-full bg-line" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={pct} aria-label={`Pattern attention level ${attention.level}`}>
        <div className={`h-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <div className="mt-1 flex justify-between text-xs text-muted"><span>Low</span><span>Moderate</span><span>Elevated</span></div>
      <p className="mt-3 text-sm text-muted">Based on {attention.high_checks} high and {attention.caution_checks} caution checks and the patterns in your recent logs. It is not a medical risk score.</p>
      {attention.suggest_consult && (
        <div className="mt-3 rounded-xl bg-paper p-3 text-sm">
          <p className="font-semibold">{attention.message}</p>
          <Link to="/consult" className="link mt-1 inline-block">See consultation options</Link>
        </div>
      )}
    </section>
  )
}
