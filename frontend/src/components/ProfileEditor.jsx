import { useState } from 'react'
import { Plus, X, Check } from 'lucide-react'

// Multi-select chips with an "add your own" field (used for allergies, intolerances, preferences).
export function ChipSelect({ legend, hint, options, value, onChange, allowCustom = true, idPrefix }) {
  const [custom, setCustom] = useState('')
  const [err, setErr] = useState('')
  const toggle = (o) => onChange(value.includes(o) ? value.filter((v) => v !== o) : [...value, o])
  const add = () => {
    const v = custom.trim().replace(/\s+/g, ' ')
    if (!v) return
    if (!/^[\w\s\-/&().,']{1,40}$/.test(v)) { setErr('Use letters, numbers and spaces only (max 40 characters).'); return }
    if (!value.some((x) => x.toLowerCase() === v.toLowerCase())) onChange([...value, v])
    setCustom(''); setErr('')
  }
  const extras = value.filter((v) => !options.includes(v))
  return (
    <fieldset>
      <legend className="type-title text-lg">{legend}</legend>
      {hint && <p className="mt-0.5 text-sm text-muted">{hint}</p>}
      <div className="mt-3 flex flex-wrap gap-2">
        {[...options, ...extras].map((o) => {
          const on = value.includes(o)
          return (
            <button key={o} type="button" aria-pressed={on} onClick={() => toggle(o)}
              className={`chip ${on ? 'border-brand bg-brand text-white' : 'border-line bg-surface text-ink hover:border-ink/40'}`}>
              {on ? <Check className="h-3.5 w-3.5" aria-hidden /> : null}{o}
              {on && extras.includes(o) && <X className="h-3.5 w-3.5" aria-hidden />}
            </button>
          )
        })}
      </div>
      {allowCustom && (
        <div className="mt-3 flex max-w-sm gap-2">
          <label className="sr-only" htmlFor={`${idPrefix}-custom`}>Add another</label>
          <input id={`${idPrefix}-custom`} className="field" placeholder="Add another" value={custom} maxLength={40}
            onChange={(e) => setCustom(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); add() } }} />
          <button type="button" className="btn-secondary" onClick={add} aria-label="Add"><Plus className="h-4 w-4" /></button>
        </div>
      )}
      {err && <p className="mt-1 text-sm text-high">{err}</p>}
    </fieldset>
  )
}

// Keyed options (health considerations, goals)
export function KeyedSelect({ legend, hint, options, value, onChange }) {
  return (
    <fieldset>
      <legend className="type-title text-lg">{legend}</legend>
      {hint && <p className="mt-0.5 text-sm text-muted">{hint}</p>}
      <div className="mt-3 grid gap-2 sm:grid-cols-2">
        {options.map((o) => {
          const on = value.includes(o.key)
          return (
            <button key={o.key} type="button" aria-pressed={on} onClick={() => onChange(on ? value.filter((v) => v !== o.key) : [...value, o.key])}
              className={`flex items-center justify-between rounded-xl border px-4 py-3 text-left font-semibold ${on ? 'border-brand bg-brand-soft text-brand' : 'border-line bg-surface hover:border-ink/40'}`}>
              {o.label}{on && <Check className="h-4 w-4" aria-hidden />}
            </button>
          )
        })}
      </div>
    </fieldset>
  )
}
