import { MEALS } from '../utils/format'

export default function MealPicker({ value, onChange, name = 'meal' }) {
  return (
    <div role="radiogroup" aria-label="Meal" className="grid grid-cols-4 gap-1 rounded-xl border border-line bg-paper p-1">
      {MEALS.map((m) => (
        <label key={m.key} className={`cursor-pointer rounded-lg px-2 py-2 text-center text-sm font-semibold ${value === m.key ? 'bg-surface text-ink shadow-sm ring-1 ring-line' : 'text-muted hover:text-ink'}`}>
          <input type="radio" name={name} value={m.key} checked={value === m.key} onChange={() => onChange(m.key)} className="sr-only" />
          {m.label}
        </label>
      ))}
    </div>
  )
}
