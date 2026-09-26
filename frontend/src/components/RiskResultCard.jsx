import { RISK } from './RiskBadge'
import ConfidenceIndicator from './ConfidenceIndicator'

// The signature element: the result reads like a food label panel — heavy rules, the verdict in
// condensed display type, then each finding as a labelled row.
export default function RiskResultCard({ result }) {
  const r = RISK[result.risk_level] || RISK.LOW
  return (
    <section className="panel overflow-hidden" aria-labelledby="verdict">
      <div className={`${r.solid} h-2`} aria-hidden />
      <div className="p-5 sm:p-6">
        <p className="text-sm font-semibold text-muted">Result for your profile</p>
        <h1 className="type-display mt-1 text-4xl sm:text-5xl">{result.food_name}</h1>
        <div className="rule-heavy mt-4" />
        <div id="verdict" className={`flex items-center gap-3 py-3 ${r.text}`}>
          <r.Icon className="h-10 w-10 shrink-0" aria-hidden />
          <div>
            <p className="type-display text-5xl sm:text-6xl">{r.word}</p>
            <p className="text-sm font-semibold text-ink">{result.risk_level === 'LOW' ? 'No conflicts found with your profile' : result.risk_level === 'HIGH' ? 'Conflicts with your profile' : 'Worth a closer look'}</p>
          </div>
        </div>
        <div className="rule-thin" />
        <p className="py-3 text-[1.05rem] leading-relaxed">{result.explanation}</p>
        {result.detected_conflicts?.length > 0 && (
          <>
            <div className="rule-mid" />
            <ul className="divide-y divide-ink/15" aria-label="What was flagged">
              {result.detected_conflicts.map((c, i) => {
                const cr = RISK[c.severity === 'high' ? 'HIGH' : 'CAUTION']
                return (
                  <li key={i} className="flex items-start gap-3 py-2.5">
                    <cr.Icon className={`mt-0.5 h-4 w-4 shrink-0 ${cr.text}`} aria-hidden />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm"><span className="font-semibold">{c.ingredient || 'Nutrition'}</span> <span className="text-muted">— matches your {c.profile_match}</span></p>
                      <p className="text-sm text-ink/80">{c.reason}</p>
                    </div>
                    <span className={`text-xs font-bold ${cr.text}`}>{cr.word}</span>
                  </li>
                )
              })}
            </ul>
          </>
        )}
        <div className="rule-heavy" />
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3">
          <ConfidenceIndicator value={result.confidence} label="Confidence" />
          <span className="text-xs text-muted">
            {result.data_certainty === 'known' ? 'Based on the listed ingredients' : result.data_certainty === 'estimated' ? 'Based on estimated ingredients' : 'Ingredients unknown'}
          </span>
        </div>
      </div>
    </section>
  )
}
