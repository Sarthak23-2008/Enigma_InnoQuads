import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { History as HistoryIcon, Download } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import HistoryItem from '../components/HistoryItem'
import { EmptyState, ErrorState, Skeleton } from '../components/States'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { fmtDate, MEALS } from '../utils/format'

export default function History() {
  const [sp, setSp] = useSearchParams()
  const [q, setQ] = useState(sp.get('q') || '')
  const f = { page: Number(sp.get('page') || 1), meal: sp.get('meal') || '', risk: sp.get('risk') || '', date_from: sp.get('from') || '', date_to: sp.get('to') || '', q: sp.get('q') || '' }
  const params = useMemo(() => {
    const p = { page: f.page, page_size: 20 }
    if (f.meal) p.meal = f.meal
    if (f.risk) p.risk = f.risk
    if (f.date_from) p.date_from = f.date_from
    if (f.date_to) p.date_to = f.date_to
    if (f.q) p.q = f.q
    return p
  }, [sp]) // eslint-disable-line react-hooks/exhaustive-deps
  const { data, error, loading, reload } = useAsync(() => api.history(params), [params])

  useEffect(() => {
    const t = setTimeout(() => { if (q !== f.q) update({ q }) }, 300)
    return () => clearTimeout(t)
  }, [q]) // eslint-disable-line react-hooks/exhaustive-deps

  function update(changes) {
    const next = new URLSearchParams(sp)
    for (const [k, v] of Object.entries(changes)) { if (v) next.set(k, v); else next.delete(k) }
    if (!('page' in changes)) next.delete('page')
    setSp(next, { replace: true })
  }
  const groups = useMemo(() => {
    const g = []
    for (const l of data?.items || []) {
      const day = fmtDate(l.consumed_at, { weekday: 'long', day: 'numeric', month: 'long' })
      if (!g.length || g[g.length - 1].day !== day) g.push({ day, items: [] })
      g[g.length - 1].items.push(l)
    }
    return g
  }, [data])
  const filtered = f.meal || f.risk || f.date_from || f.date_to || f.q

  const download = async () => {
    const res = await api.exportLogs('csv')
    const url = URL.createObjectURL(await res.blob())
    const a = Object.assign(document.createElement('a'), { href: url, download: 'safebite-diet-history.csv' })
    a.click(); URL.revokeObjectURL(url)
  }

  return (
    <div>
      <PageHeader title="History" subtitle="Everything you logged with “I Ate This”." actions={<button className="btn-secondary" onClick={download}><Download className="h-4 w-4" aria-hidden />Export CSV</button>} />
      <div className="panel mb-5 grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <label className="label" htmlFor="h-q">Search</label>
          <input id="h-q" className="field" placeholder="Food name" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <div>
          <label className="label" htmlFor="h-meal">Meal</label>
          <select id="h-meal" className="field" value={f.meal} onChange={(e) => update({ meal: e.target.value })}>
            <option value="">All meals</option>{MEALS.map((m) => <option key={m.key} value={m.key}>{m.label}</option>)}
          </select>
        </div>
        <div>
          <label className="label" htmlFor="h-risk">Risk</label>
          <select id="h-risk" className="field" value={f.risk} onChange={(e) => update({ risk: e.target.value })}>
            <option value="">All levels</option><option value="HIGH">High</option><option value="CAUTION">Caution</option><option value="LOW">Low</option>
          </select>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div><label className="label" htmlFor="h-from">From</label><input id="h-from" type="date" className="field px-2" value={f.date_from} onChange={(e) => update({ from: e.target.value })} /></div>
          <div><label className="label" htmlFor="h-to">To</label><input id="h-to" type="date" className="field px-2" value={f.date_to} onChange={(e) => update({ to: e.target.value })} /></div>
        </div>
      </div>

      {error ? <ErrorState error={error} onRetry={reload} /> : loading && !data ? (
        <div className="space-y-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-16" />)}</div>
      ) : data.total === 0 ? (
        filtered ? <EmptyState icon={HistoryIcon} title="Nothing matches these filters" body="Try a wider date range or clear the filters." action={{ onClick: () => { setQ(''); setSp({}, { replace: true }) }, label: 'Clear filters' }} />
          : <EmptyState icon={HistoryIcon} title="No meals logged yet" body="Check a food and tap “I Ate This” to start your history." action={{ to: '/check', label: 'Check a food' }} />
      ) : (
        <>
          <p className="mb-3 text-sm text-muted" aria-live="polite">{data.total} entr{data.total === 1 ? 'y' : 'ies'}</p>
          <div className={`space-y-5 ${loading ? 'opacity-60' : ''}`}>
            {groups.map((g) => (
              <section key={g.day}>
                <h2 className="mb-2 text-sm font-bold text-muted">{g.day}</h2>
                <div className="panel divide-y divide-line overflow-hidden">{g.items.map((l) => <HistoryItem key={l.log_id} log={l} />)}</div>
              </section>
            ))}
          </div>
          {data.pages > 1 && (
            <nav className="mt-6 flex items-center justify-between" aria-label="Pages">
              <button className="btn-secondary" disabled={f.page <= 1} onClick={() => update({ page: String(f.page - 1) })}>Newer</button>
              <span className="text-sm text-muted">Page {data.page} of {data.pages}</span>
              <button className="btn-secondary" disabled={f.page >= data.pages} onClick={() => update({ page: String(f.page + 1) })}>Older</button>
            </nav>
          )}
        </>
      )}
    </div>
  )
}
