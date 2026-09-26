export const MEALS = [
  { key: 'breakfast', label: 'Breakfast' }, { key: 'lunch', label: 'Lunch' },
  { key: 'snack', label: 'Snack' }, { key: 'dinner', label: 'Dinner' },
]
export const mealLabel = (k) => MEALS.find((m) => m.key === k)?.label || k

export function mealForNow(d = new Date()) {
  const h = d.getHours()
  if (h < 11) return 'breakfast'
  if (h < 16) return 'lunch'
  if (h < 19) return 'snack'
  return 'dinner'
}

export const fmtDate = (iso, opts = { day: 'numeric', month: 'short' }) =>
  iso ? new Date(iso).toLocaleDateString(undefined, opts) : ''
export const fmtTime = (iso) => (iso ? new Date(iso).toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' }) : '')
export const fmtDateTime = (iso) => (iso ? `${fmtDate(iso, { day: 'numeric', month: 'short', year: 'numeric' })}, ${fmtTime(iso)}` : '')

export function fmtNum(v, digits = 0) {
  if (v === null || v === undefined || Number.isNaN(v)) return '—'
  return Number(v).toLocaleString(undefined, { maximumFractionDigits: digits })
}

export const NUTRIENTS = [
  { key: 'calories', label: 'Calories', unit: 'kcal' },
  { key: 'protein', label: 'Protein', unit: 'g' },
  { key: 'carbohydrates', label: 'Carbohydrates', unit: 'g' },
  { key: 'sugar', label: 'Sugar', unit: 'g' },
  { key: 'fiber', label: 'Fiber', unit: 'g' },
  { key: 'fat', label: 'Fat', unit: 'g' },
  { key: 'sodium', label: 'Sodium', unit: 'mg' },
  { key: 'potassium', label: 'Potassium', unit: 'mg' },
]

export const METHOD_LABEL = { scan: 'Scanned label', search: 'Searched', manual: 'Entered manually', eating_out: 'Eating out' }
export const GOAL_LABEL = {
  reduce_sodium: 'Reduce sodium', reduce_sugar: 'Reduce sugar', increase_fiber: 'Increase fiber',
  increase_protein: 'Increase protein', improve_diversity: 'Improve food diversity',
}
export const CONDITION_LABEL = { diabetes: 'Blood-sugar management', hypertension: 'Blood pressure', ckd: 'Kidney health (CKD)', pcos: 'PCOS' }
