// Ingredients as recognised by SafeBite. Flagged items are marked with the matching risk word.
export default function IngredientList({ details = [], conflicts = [] }) {
  const flag = {}
  for (const c of conflicts) {
    const key = (c.standard_name || c.ingredient || '').toLowerCase()
    if (!flag[key] || c.severity === 'high') flag[key] = c.severity
  }
  if (!details.length) return <p className="text-sm text-muted">No ingredient information is available.</p>
  return (
    <ul className="flex flex-wrap gap-2" aria-label="Ingredients">
      {details.map((d, i) => {
        const sev = flag[(d.name || '').toLowerCase()]
        const cls = sev === 'high' ? 'border-high bg-high-soft text-high' : sev === 'caution' ? 'border-caution bg-caution-soft text-caution' : d.name ? 'border-line bg-surface text-ink' : 'border-dashed border-muted/60 bg-surface text-muted'
        return (
          <li key={i} className={`chip ${cls}`} title={d.name ? `Recognised as ${d.name}` : 'Not recognised — could not be checked'}>
            {d.raw}
            {d.name && d.name.toLowerCase() !== d.raw.toLowerCase().replace(/[^a-z ]/g, '').trim() && <span className="text-xs opacity-70">= {d.name}</span>}
            {sev === 'high' && <span className="text-xs font-bold">HIGH</span>}
            {sev === 'caution' && <span className="text-xs font-bold">CAUTION</span>}
            {!d.name && <span className="text-xs">unrecognised</span>}
          </li>
        )
      })}
    </ul>
  )
}
