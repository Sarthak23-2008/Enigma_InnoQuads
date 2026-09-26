// Shows how sure SafeBite is about the reading. Three segments + a word, so it never relies on colour.
export default function ConfidenceIndicator({ value, label = 'Reading confidence' }) {
  if (value === null || value === undefined) return null
  const level = value >= 0.8 ? 'High' : value >= 0.6 ? 'Medium' : 'Low'
  const filled = level === 'High' ? 3 : level === 'Medium' ? 2 : 1
  const color = level === 'High' ? 'bg-low' : level === 'Medium' ? 'bg-caution' : 'bg-high'
  return (
    <div className="flex items-center gap-2 text-sm" aria-label={`${label}: ${level} (${Math.round(value * 100)}%)`}>
      <span className="text-muted">{label}</span>
      <span className="flex gap-0.5" aria-hidden>
        {[0, 1, 2].map((i) => <span key={i} className={`h-2 w-5 rounded-sm ${i < filled ? color : 'bg-line'}`} />)}
      </span>
      <span className="font-semibold">{level}</span>
    </div>
  )
}
