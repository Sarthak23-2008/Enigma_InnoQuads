import { useState } from 'react'
import { Plus, Trash2, TriangleAlert } from 'lucide-react'
import ConfidenceIndicator from './ConfidenceIndicator'
import { NUTRIENTS } from '../utils/format'

// Review screen: the user corrects what OCR read BEFORE anything is analysed.
export default function OCRReview({ ocr, imageUrl, onAnalyze, onRetake, busy }) {
  const [name, setName] = useState(ocr.food_name || '')
  const [items, setItems] = useState(ocr.ingredients.length ? ocr.ingredients : [''])
  const [contains, setContains] = useState((ocr.allergen_statements?.contains || []).join(', '))
  const [may, setMay] = useState((ocr.allergen_statements?.may_contain || []).join(', '))
  const [nut, setNut] = useState(() => Object.fromEntries(NUTRIENTS.map((n) => [n.key, ocr.nutrition?.[n.key] ?? ''])))
  const [err, setErr] = useState('')

  const set = (i, v) => setItems((xs) => xs.map((x, j) => (j === i ? v : x)))
  const split = (s) => s.split(',').map((x) => x.trim()).filter(Boolean)
  const submit = (e) => {
    e.preventDefault()
    const ings = items.map((x) => x.trim()).filter(Boolean)
    if (!name.trim()) return setErr('Give this food a name.')
    if (!ings.length) return setErr('Add at least one ingredient.')
    const nutrition = {}
    for (const n of NUTRIENTS) {
      const v = nut[n.key]
      if (v === '' || v === null) continue
      const num = Number(v)
      if (Number.isNaN(num) || num < 0) return setErr(`${n.label} must be a positive number.`)
      nutrition[n.key] = num
    }
    if (ocr.nutrition?.basis) nutrition.basis = ocr.nutrition.basis
    if (ocr.nutrition?.serving_size) nutrition.serving_size = ocr.nutrition.serving_size
    setErr('')
    onAnalyze({ food_name: name.trim(), ingredients: ings, nutrition,
      allergen_statements: { contains: split(contains), may_contain: split(may) } })
  }

  return (
    <form onSubmit={submit} className="grid gap-6 lg:grid-cols-[1fr_20rem]" noValidate>
      <div className="space-y-5">
        <div className="panel p-5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="type-title text-2xl">Check what we read</h2>
            <ConfidenceIndicator value={ocr.confidence} />
          </div>
          {(ocr.incomplete || ocr.warnings?.length > 0) && (
            <div className="mt-3 rounded-xl bg-caution-soft p-3 text-sm" role="status">
              <p className="flex items-center gap-2 font-semibold text-caution"><TriangleAlert className="h-4 w-4" aria-hidden />{ocr.incomplete_message || 'Please review the extracted ingredients.'}</p>
              {ocr.warnings?.length > 0 && <ul className="mt-1 list-disc pl-6 text-ink/80">{ocr.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>}
            </div>
          )}
          <label className="label mt-4" htmlFor="food-name">Food name</label>
          <input id="food-name" className="field" value={name} maxLength={200} onChange={(e) => setName(e.target.value)} />
        </div>

        <fieldset className="panel p-5">
          <legend className="sr-only">Ingredients</legend>
          <div className="flex items-baseline justify-between">
            <h3 className="type-title text-lg">Ingredients</h3>
            <span className="text-sm text-muted">{items.filter((x) => x.trim()).length} found</span>
          </div>
          <p className="text-sm text-muted">Fix any misread words. Order doesn't matter.</p>
          <ol className="mt-3 space-y-2">
            {items.map((x, i) => (
              <li key={i} className="flex gap-2">
                <label className="sr-only" htmlFor={`ing-${i}`}>Ingredient {i + 1}</label>
                <input id={`ing-${i}`} className="field" value={x} maxLength={200} onChange={(e) => set(i, e.target.value)} />
                <button type="button" className="btn-secondary px-3" aria-label={`Remove ${x || 'ingredient'}`} onClick={() => setItems((xs) => xs.filter((_, j) => j !== i))}><Trash2 className="h-4 w-4" /></button>
              </li>
            ))}
          </ol>
          <button type="button" className="btn-ghost mt-2" onClick={() => setItems((xs) => [...xs, ''])}><Plus className="h-4 w-4" aria-hidden />Add ingredient</button>

          <div className="mt-4 grid gap-4 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="contains">Label says “Contains”</label>
              <input id="contains" className="field" value={contains} onChange={(e) => setContains(e.target.value)} placeholder="e.g. wheat, milk" />
            </div>
            <div>
              <label className="label" htmlFor="may">Label says “May contain”</label>
              <input id="may" className="field" value={may} onChange={(e) => setMay(e.target.value)} placeholder="e.g. tree nuts" />
            </div>
          </div>
        </fieldset>

        <fieldset className="panel p-5">
          <legend className="sr-only">Nutrition</legend>
          <h3 className="type-title text-lg">Nutrition {ocr.nutrition?.basis ? <span className="text-sm font-normal text-muted">({ocr.nutrition.basis}{ocr.nutrition.serving_size ? `, ${ocr.nutrition.serving_size}` : ''})</span> : null}</h3>
          <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {NUTRIENTS.map((n) => (
              <div key={n.key}>
                <label className="label text-xs" htmlFor={`n-${n.key}`}>{n.label} ({n.unit})</label>
                <input id={`n-${n.key}`} className="field tabular" inputMode="decimal" value={nut[n.key]} onChange={(e) => setNut((s) => ({ ...s, [n.key]: e.target.value }))} />
              </div>
            ))}
          </div>
        </fieldset>
        {err && <p className="text-sm font-semibold text-high" role="alert">{err}</p>}
        <div className="flex flex-wrap gap-2">
          <button type="submit" className="btn-primary px-6" disabled={busy}>{busy ? 'Analyzing…' : 'Analyze Food'}</button>
          <button type="button" className="btn-secondary" onClick={onRetake} disabled={busy}>Retake photo</button>
        </div>
      </div>
      <aside className="space-y-3">
        {imageUrl && <img src={imageUrl} alt="The label you uploaded" className="w-full rounded-panel border border-line bg-surface object-contain" />}
        <details className="panel p-4 text-sm">
          <summary className="cursor-pointer font-semibold">Raw text read from the label</summary>
          <pre className="mt-2 max-h-72 overflow-auto whitespace-pre-wrap font-sans text-xs text-muted">{ocr.raw_text}</pre>
        </details>
      </aside>
    </form>
  )
}
