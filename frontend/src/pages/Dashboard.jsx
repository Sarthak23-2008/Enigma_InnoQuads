import { Link } from 'react-router-dom'
import { Coffee, Sun, Cookie, Moon, ArrowUpRight, ScanLine, Search, PencilLine } from 'lucide-react'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { ErrorState, Skeleton } from '../components/States'
import RiskBadge from '../components/RiskBadge'
import AlertCard from '../components/AlertCard'
import SymptomPrompt from '../components/SymptomPrompt'
import { fmtNum, fmtTime, METHOD_LABEL } from '../utils/format'

const MEAL_ICON = { breakfast: Coffee, lunch: Sun, snack: Cookie, dinner: Moon }
const CLS_TONE = { HIGH: 'text-caution', LOW: 'text-caution', MODERATE: 'text-ink' }

export default function Dashboard() {
  const { data, error, loading, reload, setData } = useAsync(() => api.dashboard(), [])
  if (error) return <ErrorState error={error} onRetry={reload} />
  if (loading && !data) return (
    <div className="space-y-4"><Skeleton className="h-14 w-2/3" /><div className="grid gap-4 md:grid-cols-2"><Skeleton className="h-56" /><Skeleton className="h-56" /></div></div>
  )
  const d = data
  const first = d.name.split(' ')[0]
  const todayCount = Object.values(d.today).reduce((a, b) => a + b.length, 0)
  return (
    <div className="space-y-8">
      <section className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="type-display text-5xl sm:text-6xl">{d.greeting}, {first}</h1>
          <p className="mt-2 text-muted">{todayCount ? `${todayCount} item${todayCount > 1 ? 's' : ''} logged today, ${fmtNum(d.today_totals.sodium)} mg sodium so far.` : 'Nothing logged yet today.'}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link to="/check/scan" className="btn-primary"><ScanLine className="h-5 w-5" aria-hidden />Scan Food Label</Link>
          <Link to="/check/search" className="btn-secondary"><Search className="h-4 w-4" aria-hidden />Search</Link>
          <Link to="/check/manual" className="btn-secondary"><PencilLine className="h-4 w-4" aria-hidden />Enter manually</Link>
        </div>
      </section>

      {d.pending_symptoms?.length > 0 && (
        <section aria-label="Check-ins" className="space-y-3">
          {d.pending_symptoms.map((l) => (
            <SymptomPrompt key={l.log_id} log={l} question={d.symptom_question}
              onDone={() => setData((s) => ({ ...s, pending_symptoms: s.pending_symptoms.filter((x) => x.log_id !== l.log_id) }))} />
          ))}
        </section>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.35fr_1fr]">
        <section className="panel p-5" aria-labelledby="today">
          <div className="flex items-baseline justify-between">
            <h2 id="today" className="type-title text-2xl">Today's diet</h2>
            <Link to="/history" className="link text-sm">All history</Link>
          </div>
          <div className="rule-heavy mt-3" />
          <ul>
            {['breakfast', 'lunch', 'snack', 'dinner'].map((m) => {
              const Icon = MEAL_ICON[m]
              const items = d.today[m] || []
              return (
                <li key={m} className="flex gap-4 border-b border-ink/15 py-3 last:border-0">
                  <div className="flex w-28 shrink-0 items-center gap-2 font-semibold capitalize"><Icon className="h-4 w-4 text-muted" aria-hidden />{m}</div>
                  <div className="min-w-0 flex-1">
                    {items.length === 0 ? <Link to="/check" className="text-sm text-muted hover:text-brand">Not logged. Check a food</Link> : (
                      <ul className="space-y-1.5">
                        {items.map((l) => (
                          <li key={l.log_id}>
                            <Link to={`/history/${l.log_id}`} className="flex items-center justify-between gap-2 hover:text-brand">
                              <span className="truncate">{l.food_name}</span><RiskBadge level={l.risk_level} size="sm" />
                            </Link>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </li>
              )
            })}
          </ul>
        </section>

        <div className="space-y-6">
          <section className="panel p-5" aria-labelledby="recent">
            <h2 id="recent" className="type-title text-2xl">Recent risk check</h2>
            {d.recent_check ? (
              <Link to={`/result/${d.recent_check.scan_id}`} className="group mt-3 block">
                <div className="flex items-start justify-between gap-3">
                  <p className="font-semibold group-hover:text-brand">{d.recent_check.food_name}</p>
                  <RiskBadge level={d.recent_check.risk_level} />
                </div>
                <p className="mt-2 line-clamp-3 text-sm text-ink/80">{d.recent_check.explanation}</p>
                <p className="mt-2 text-xs text-muted">{METHOD_LABEL[d.recent_check.input_method]}, {fmtTime(d.recent_check.created_at)}</p>
              </Link>
            ) : <p className="mt-2 text-sm text-muted">Your latest food check will show here.</p>}
          </section>

          <section className="panel p-5" aria-labelledby="snapshot">
            <div className="flex items-baseline justify-between">
              <h2 id="snapshot" className="type-title text-2xl">Diet pattern snapshot</h2>
              <Link to="/trends" className="inline-flex items-center gap-1 text-sm font-semibold text-brand">Trends<ArrowUpRight className="h-4 w-4" aria-hidden /></Link>
            </div>
            <p className="text-xs text-muted">Last 15 days</p>
            {d.snapshot.status === 'insufficient' ? (
              <p className="mt-3 text-sm text-muted">Keep logging your meals. More data will help SafeBite identify meaningful dietary patterns.</p>
            ) : (
              <dl className="mt-3 grid grid-cols-2 gap-x-4">
                {d.snapshot.metrics.map((m) => (
                  <div key={m.key} className="flex items-baseline justify-between border-t border-ink/15 py-2">
                    <dt className="text-sm">{m.label}</dt>
                    <dd className={`text-sm font-bold ${m.attention ? CLS_TONE[m.classification] : 'text-ink'}`}>{m.classification}</dd>
                  </div>
                ))}
              </dl>
            )}
          </section>
        </div>
      </div>
      {d.snapshot.top_alert && <AlertCard alert={d.snapshot.top_alert} />}
    </div>
  )
}
