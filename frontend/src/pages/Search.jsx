import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams, Link } from 'react-router-dom'
import { Search as SearchIcon } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import FoodCard from '../components/FoodCard'
import { EmptyState, ErrorState, LoadingState } from '../components/States'
import { api } from '../services/api'

export default function Search() {
  const [params, setParams] = useSearchParams()
  const nav = useNavigate()
  const [q, setQ] = useState(params.get('q') || '')
  const [res, setRes] = useState({ loading: true, items: [], error: null })
  const [busyId, setBusyId] = useState(null)

  useEffect(() => {
    const ctl = new AbortController()
    const t = setTimeout(async () => {
      setRes((r) => ({ ...r, loading: true, error: null }))
      try { const d = await api.searchFoods(q.trim(), ctl.signal); setRes({ loading: false, items: d.results, error: null }) }
      catch (e) { if (e.name !== 'AbortError') setRes({ loading: false, items: [], error: e }) }
      setParams(q.trim() ? { q: q.trim() } : {}, { replace: true })
    }, 220)
    return () => { clearTimeout(t); ctl.abort() }
  }, [q]) // eslint-disable-line react-hooks/exhaustive-deps

  const pick = async (food) => {
    setBusyId(food.food_id)
    try {
      const r = await api.analyze({ input_method: 'search', food_name: food.name, food_id: food.food_id })
      nav(`/result/${r.scan_id}`, { state: { fresh: true } })
    } catch (e) { setRes((s) => ({ ...s, error: e })); setBusyId(null) }
  }

  return (
    <div className="max-w-3xl">
      <PageHeader title="Search food" back={{ to: '/check', label: 'Check a food' }} subtitle="Common Indian dishes and packaged foods. Ingredients are based on typical recipes." />
      <div className="relative">
        <SearchIcon className="pointer-events-none absolute left-3.5 top-3.5 h-5 w-5 text-muted" aria-hidden />
        <label htmlFor="q" className="sr-only">Search food</label>
        <input id="q" autoFocus className="field pl-11 text-lg" placeholder="Try “poha”, “paneer” or “noodles”" value={q} onChange={(e) => setQ(e.target.value)} maxLength={80} />
      </div>
      <div className="mt-5 space-y-2" aria-live="polite">
        {res.error && <ErrorState error={res.error} />}
        {res.loading && !res.items.length ? <LoadingState label="Searching…" /> : res.items.length === 0 && !res.error ? (
          <EmptyState icon={SearchIcon} title={`No foods match “${q}”`} body="Check the spelling, try a simpler name, or enter the food yourself." action={{ to: '/check/manual', label: 'Enter manually' }} />
        ) : res.items.map((f) => <FoodCard key={f.food_id} food={f} onSelect={pick} busy={busyId !== null} />)}
      </div>
      {busyId && <p className="mt-3 text-sm text-muted" role="status">Checking against your profile…</p>}
      <p className="mt-6 text-sm text-muted">Have the packet? <Link to="/check/scan" className="link">Scanning the label</Link> gives a more accurate result.</p>
    </div>
  )
}
