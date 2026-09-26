import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { UtensilsCrossed } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import { ErrorState, LoadingState } from '../components/States'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { fmtNum } from '../utils/format'

export default function EatingOut() {
  const nav = useNavigate()
  const { data, error, loading, reload } = useAsync(() => api.dishes(), [])
  const [q, setQ] = useState('')
  const [busy, setBusy] = useState(null)
  const [err, setErr] = useState(null)
  const list = useMemo(() => (data || []).filter((d) => d.name.toLowerCase().includes(q.toLowerCase())), [data, q])
  const pick = async (d) => {
    setBusy(d.name); setErr(null)
    try { const r = await api.analyze({ input_method: 'eating_out', food_name: d.name, dish_name: d.name }); nav(`/result/${r.scan_id}`, { state: { fresh: true } }) }
    catch (e) { setErr(e); setBusy(null) }
  }
  return (
    <div className="max-w-3xl">
      <PageHeader title="Eating out" back={{ to: '/check', label: 'Check a food' }}
        subtitle="Restaurant recipes vary, so results use estimated ingredients and are marked ESTIMATE. Ask how a dish is prepared if you have an allergy." />
      <label className="sr-only" htmlFor="dish-q">Find a dish</label>
      <input id="dish-q" className="field" placeholder="Find a dish" value={q} onChange={(e) => setQ(e.target.value)} />
      {err && <div className="mt-3"><ErrorState error={err} /></div>}
      {error ? <div className="mt-4"><ErrorState error={error} onRetry={reload} /></div> : loading ? <LoadingState /> : (
        <ul className="mt-4 grid gap-2 sm:grid-cols-2">
          {list.map((d) => (
            <li key={d.name}>
              <button onClick={() => pick(d)} disabled={!!busy} className="flex w-full items-start gap-3 rounded-xl border border-line bg-surface p-4 text-left hover:border-brand disabled:opacity-60">
                <UtensilsCrossed className="mt-0.5 h-5 w-5 shrink-0 text-brand" aria-hidden />
                <div>
                  <p className="font-semibold">{d.name}</p>
                  <p className="text-sm text-muted tabular">~{fmtNum(d.nutrition.calories)} kcal, ~{fmtNum(d.nutrition.sodium)} mg sodium</p>
                  {busy === d.name && <p className="text-sm text-brand">Checking…</p>}
                </div>
              </button>
            </li>
          ))}
          {list.length === 0 && <p className="text-sm text-muted">No dish matches. Use Enter Manually for anything else.</p>}
        </ul>
      )}
    </div>
  )
}
