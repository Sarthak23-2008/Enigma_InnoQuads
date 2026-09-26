import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Trash2 } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import MealPicker from '../components/MealPicker'
import { InlineError } from '../components/States'
import { api } from '../services/api'
import { mealForNow, NUTRIENTS } from '../utils/format'

export default function Manual() {
  const nav = useNavigate()
  const [name, setName] = useState('')
  const [items, setItems] = useState(['', ''])
  const [meal, setMeal] = useState(mealForNow())
  const [nut, setNut] = useState({})
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    const ings = items.map((x) => x.trim()).filter(Boolean)
    const errs = {}
    if (!name.trim()) errs.name = 'Enter the food or dish name.'
    if (!ings.length) errs.items = 'Add at least one ingredient.'
    const nutrition = {}
    for (const n of NUTRIENTS) {
      const v = nut[n.key]
      if (v === undefined || v === '') continue
      if (Number.isNaN(Number(v)) || Number(v) < 0) errs.nut = `${n.label} must be a positive number.`
      else nutrition[n.key] = Number(v)
    }
    setErrors(errs)
    if (Object.keys(errs).length) return
    setBusy(true)
    try {
      const r = await api.analyze({ input_method: 'manual', food_name: name.trim(), ingredients: ings, nutrition, meal_type: meal })
      nav(`/result/${r.scan_id}`, { state: { fresh: true } })
    } catch (err) { setErrors({ form: err.message }); setBusy(false) }
  }

  return (
    <form onSubmit={submit} noValidate className="max-w-3xl space-y-5">
      <PageHeader title="Enter manually" back={{ to: '/check', label: 'Check a food' }} subtitle="For home-cooked or unpackaged food. List what went into it." />
      <div className="panel space-y-4 p-5">
        <div>
          <label className="label" htmlFor="name">Food or dish</label>
          <input id="name" className="field" value={name} maxLength={200} onChange={(e) => setName(e.target.value)} placeholder="e.g. Aloo paratha with curd" />
          <InlineError>{errors.name}</InlineError>
        </div>
        <div>
          <span className="label">Meal</span>
          <MealPicker value={meal} onChange={setMeal} />
        </div>
      </div>
      <fieldset className="panel p-5">
        <legend className="type-title px-1 text-lg">Ingredients</legend>
        <ol className="mt-2 space-y-2">
          {items.map((x, i) => (
            <li key={i} className="flex gap-2">
              <label className="sr-only" htmlFor={`m-ing-${i}`}>Ingredient {i + 1}</label>
              <input id={`m-ing-${i}`} className="field" value={x} maxLength={200} placeholder={i === 0 ? 'e.g. wheat flour' : 'e.g. butter'} onChange={(e) => setItems((xs) => xs.map((y, j) => (j === i ? e.target.value : y)))} />
              <button type="button" className="btn-secondary px-3" aria-label="Remove ingredient" onClick={() => setItems((xs) => (xs.length > 1 ? xs.filter((_, j) => j !== i) : ['']))}><Trash2 className="h-4 w-4" /></button>
            </li>
          ))}
        </ol>
        <button type="button" className="btn-ghost mt-2" onClick={() => setItems((xs) => [...xs, ''])}><Plus className="h-4 w-4" aria-hidden />Add ingredient</button>
        <InlineError>{errors.items}</InlineError>
      </fieldset>
      <details className="panel p-5">
        <summary className="cursor-pointer font-semibold">Add nutrition (optional)</summary>
        <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
          {NUTRIENTS.map((n) => (
            <div key={n.key}>
              <label className="label text-xs" htmlFor={`mn-${n.key}`}>{n.label} ({n.unit})</label>
              <input id={`mn-${n.key}`} className="field" inputMode="decimal" value={nut[n.key] ?? ''} onChange={(e) => setNut((s) => ({ ...s, [n.key]: e.target.value }))} />
            </div>
          ))}
        </div>
        <InlineError>{errors.nut}</InlineError>
      </details>
      {errors.form && <div className="rounded-xl bg-high-soft p-3 text-sm font-medium text-high" role="alert">{errors.form}</div>}
      <button type="submit" className="btn-primary px-6" disabled={busy}>{busy ? 'Analyzing…' : 'Analyze Food'}</button>
    </form>
  )
}
