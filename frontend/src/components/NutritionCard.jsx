import { NUTRIENTS, fmtNum } from '../utils/format'

// Nutrition rendered as a label panel: heavy rules, tabular numbers.
export default function NutritionCard({ nutrition = {}, title = 'Nutrition', note, ranges }) {
  const rows = NUTRIENTS.filter((n) => nutrition[n.key] !== undefined && nutrition[n.key] !== null)
  return (
    <section className="panel p-4" aria-label={title}>
      <h3 className="type-title text-lg">{title}</h3>
      <p className="text-xs text-muted">{nutrition.basis ? `Values ${nutrition.basis}${nutrition.serving_size ? ` (${nutrition.serving_size})` : ''}` : 'Per serving'}</p>
      <div className="rule-heavy mt-2" />
      {rows.length === 0 ? (
        <p className="py-3 text-sm text-muted">Nutrition information isn't available for this food.</p>
      ) : (
        <dl className="tabular">
          {rows.map((n, i) => (
            <div key={n.key} className={`flex items-baseline justify-between py-1.5 ${i === 0 ? '' : 'border-t border-ink/15'} ${n.key === 'calories' ? 'text-base font-bold' : 'text-sm'}`}>
              <dt>{n.label}</dt>
              <dd className="font-semibold">
                {fmtNum(nutrition[n.key], 1)} {n.unit}
                {ranges?.[n.key] && <span className="ml-1 font-normal text-muted">(est. {ranges[n.key][0]}–{ranges[n.key][1]})</span>}
              </dd>
            </div>
          ))}
        </dl>
      )}
      <div className="rule-mid" />
      {note && <p className="mt-2 text-xs text-muted">{note}</p>}
    </section>
  )
}
