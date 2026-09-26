import { fmtNum } from '../utils/format'

export default function FoodCard({ food, onSelect, busy }) {
  const n = food.nutrition || {}
  return (
    <button type="button" onClick={() => onSelect(food)} disabled={busy}
      className="flex w-full items-center gap-3 rounded-xl border border-line bg-surface px-4 py-3 text-left hover:border-brand disabled:opacity-60">
      <div className="min-w-0 flex-1">
        <p className="font-semibold">{food.name}</p>
        <p className="text-sm text-muted">{food.category}{food.is_packaged ? ', packaged' : ''}</p>
      </div>
      <div className="text-right text-sm tabular text-muted">
        <p>{fmtNum(n.calories)} kcal</p>
        <p>{fmtNum(n.sodium)} mg sodium</p>
      </div>
    </button>
  )
}
