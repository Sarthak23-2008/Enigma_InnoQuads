import { useSearchParams, Link } from 'react-router-dom'
import { LineChart, Lightbulb, Info } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import AlertCard from '../components/AlertCard'
import GoalCard from '../components/GoalCard'
import RiskMeter from '../components/RiskMeter'
import TrendChart from '../charts/TrendChart'
import CategoryChart from '../charts/CategoryChart'
import { EmptyState, ErrorState, Skeleton } from '../components/States'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { fmtDate, fmtNum } from '../utils/format'

// "Try instead" ideas for pattern alerts. Each link opens a search, where the food is re-checked
// against the user's profile before anything is logged.
const TRY = {
  sodium: ['Roasted Makhana (Fox Nuts)', 'Vegetable Salad', 'Jowar Roti'],
  added_sugar: ['Apple (Medium)', 'Roasted Chana (Chickpea)'],
  fiber: ['Roasted Chana (Chickpea)', 'Moong Sprouts Salad', 'Brown Rice (Cooked)'],
  fruit_veg: ['Amla (Indian Gooseberry)', 'Apple (Medium)', 'Vegetable Salad'],
  processed: ['Roasted Chana Chaat', 'Moong Sprouts Salad'],
  protein: ['Roasted Chana (Chickpea)', 'Tofu', 'Moong Sprouts Salad'],
  diversity: ['Ragi Dosa', 'Jowar Roti'],
}
const CHARTS = [
  { key: 'sodium', title: 'Sodium', unit: 'mg', threshold: 2000, tl: '2,000 mg' },
  { key: 'added_sugar', title: 'Added sugar', unit: 'g', threshold: 30, tl: '30 g' },
  { key: 'fiber', title: 'Fiber', unit: 'g', threshold: 25, tl: '25 g target' },
  { key: 'protein', title: 'Protein', unit: 'g', threshold: 35, tl: '35 g' },
  { key: 'fruit_veg', title: 'Fruit & vegetables', unit: 'servings' },
  { key: 'processed', title: 'Processed foods', unit: 'items' },
]
const CLS = { HIGH: 'text-caution', LOW: 'text-caution' }

function Seg({ value, options, onChange, label }) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex rounded-xl border border-line bg-surface p-1">
      {options.map((o) => (
        <button key={o.v} role="radio" aria-checked={value === o.v} onClick={() => onChange(o.v)}
          className={`rounded-lg px-3.5 py-1.5 text-sm font-semibold ${value === o.v ? 'bg-ink text-paper' : 'text-muted hover:text-ink'}`}>{o.l}</button>
      ))}
    </div>
  )
}

export default function Trends() {
  const [sp, setSp] = useSearchParams()
  const win = sp.get('window') === '30' ? 30 : 15
  const view = sp.get('view') === 'detailed' ? 'detailed' : 'general'
  const { data: t, error, loading, reload } = useAsync(() => api.trends(win), [win])
  const set = (k, v) => { const n = new URLSearchParams(sp); n.set(k, v); setSp(n, { replace: true }) }

  return (
    <div>
      <PageHeader title="Trends" subtitle="Patterns in what you've logged. Observations only, not a diagnosis."
        actions={<>
          <Seg label="Period" value={win} onChange={(v) => set('window', v)} options={[{ v: 15, l: '15 days' }, { v: 30, l: '30 days' }]} />
          <Seg label="View" value={view} onChange={(v) => set('view', v)} options={[{ v: 'general', l: 'Generalized' }, { v: 'detailed', l: 'Detailed' }]} />
        </>} />
      {error ? <ErrorState error={error} onRetry={reload} /> : loading && !t ? (
        <div className="space-y-4"><Skeleton className="h-24" /><div className="grid gap-4 md:grid-cols-2"><Skeleton className="h-64" /><Skeleton className="h-64" /></div></div>
      ) : t.status === 'insufficient' ? (
        <EmptyState icon={LineChart} title="Not enough logs yet" body="Keep logging your meals. More data will help SafeBite identify meaningful dietary patterns." action={{ to: '/check', label: 'Check a food' }} />
      ) : (
        <div className={`space-y-8 ${loading ? 'opacity-60' : ''}`}>
          <section>
            <p className="text-sm text-muted">{fmtDate(t.start_date + 'T00:00:00')} to {fmtDate(t.end_date + 'T00:00:00')}: {t.log_count} foods on {t.logged_days} of {t.window} days{t.is_demo_data ? ' (includes demo data)' : ''}</p>
            <p className="type-title mt-2 max-w-3xl text-2xl sm:text-3xl">{t.summary}</p>
            {t.status === 'early_snapshot' && (
              <p className="mt-3 flex max-w-3xl gap-2 rounded-xl bg-brand-soft p-3 text-sm"><Info className="mt-0.5 h-4 w-4 shrink-0 text-brand" aria-hidden />You've logged {t.logged_days} of {t.window} days, so this is an early snapshot. Pattern alerts appear once you've logged at least half the days.</p>
            )}
          </section>

          {t.goal_progress?.length > 0 && (
            <section aria-labelledby="goals"><h2 id="goals" className="type-title mb-3 text-xl">Your goals</h2>
              <div className="grid gap-3 md:grid-cols-2">{t.goal_progress.map((g) => <GoalCard key={g.goal} g={g} />)}</div>
            </section>
          )}

          {t.alerts?.length > 0 && (
            <section aria-labelledby="alerts" className="space-y-3"><h2 id="alerts" className="type-title text-xl">Pattern alerts</h2>
              {t.alerts.map((a) => <AlertCard key={a.metric} alert={a} tryInstead={TRY[a.metric]} />)}
            </section>
          )}

          {t.health_insight && (
            <section className="panel border-l-4 border-l-brand p-5">
              <h2 className="type-title text-lg">Health insight</h2>
              <p className="mt-1">{t.health_insight.message}</p>
              <p className="mt-1 text-sm text-ink/80">{t.health_insight.action}</p>
              <p className="mt-2 text-xs text-muted">{t.health_insight.disclaimer} <Link to="/consult" className="link">Find a professional</Link></p>
            </section>
          )}

          <div className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
            <section className="panel p-5" aria-labelledby="summary-t">
              <h2 id="summary-t" className="type-title text-xl">{win}-day summary</h2>
              <p className="text-xs text-muted">Averages per logged day</p>
              <div className="rule-heavy mt-2" />
              <table className="w-full text-sm tabular">
                <caption className="sr-only">Nutrient pattern classification</caption>
                <tbody>
                  {t.metrics.map((m) => (
                    <tr key={m.key} className="border-b border-ink/15 last:border-0">
                      <th scope="row" className="py-2.5 text-left font-semibold">{m.label}</th>
                      <td className="py-2.5 text-right text-muted">{fmtNum(m.value, 1)} {m.unit}</td>
                      <td className={`w-28 py-2.5 text-right font-bold ${m.attention ? CLS[m.classification] : ''}`}>{m.classification}{m.attention ? ' •' : ''}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="rule-mid" />
              <p className="mt-2 text-xs text-muted">• needs attention. Classifications use general guidance for adults; your needs may differ.</p>
            </section>
            <RiskMeter attention={t.attention} />
          </div>

          {t.suggestions?.length > 0 && (
            <section aria-labelledby="sugg"><h2 id="sugg" className="type-title mb-3 text-xl">Ideas for your next meals</h2>
              <div className="grid gap-3 md:grid-cols-2">
                {t.suggestions.map((s) => (
                  <div key={s.metric} className="panel p-4">
                    <p className="flex items-center gap-2 font-semibold"><Lightbulb className="h-4 w-4 text-brand" aria-hidden />{s.title}</p>
                    <p className="mt-1 text-sm text-muted">{s.tip}</p>
                    <ul className="mt-2 list-disc pl-5 text-sm">{s.foods.map((f) => <li key={f}>{f}</li>)}</ul>
                  </div>
                ))}
              </div>
            </section>
          )}

          {view === 'detailed' && (
            <section aria-labelledby="detail" className="space-y-4">
              <h2 id="detail" className="type-title text-xl">Day by day</h2>
              <div className="grid gap-4 md:grid-cols-2">
                {CHARTS.map((c) => <TrendChart key={c.key} data={t.daily} dataKey={c.key} unit={c.unit} title={c.title} threshold={c.threshold} thresholdLabel={c.tl} />)}
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <CategoryChart data={t.category_breakdown} />
                <div className="panel p-4">
                  <p className="mb-2 font-semibold">What's behind each number</p>
                  <ul className="space-y-2 text-sm">
                    {t.metrics.map((m) => (
                      <li key={m.key} className="border-b border-ink/10 pb-2 last:border-0">
                        <span className="font-semibold">{m.label}:</span> {m.explanation}
                        {m.days_over_threshold > 0 && ['sodium', 'added_sugar'].includes(m.key) && <span className="text-muted"> Over the daily guide on {m.days_over_threshold} logged days.</span>}
                        {m.top_contributors?.length > 0 && <span className="text-muted"> Mostly from {m.top_contributors.join(', ')}.</span>}
                        {m.trend && <span className="text-muted"> {m.trend.direction === 'stable' ? 'About the same as' : `${m.trend.direction === 'up' ? 'Up' : 'Down'} ${Math.abs(m.trend.change_pct)}% from`} the previous {win} days.</span>}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </section>
          )}
          {view === 'general' && <button className="btn-secondary" onClick={() => set('view', 'detailed')}>Show day-by-day charts</button>}
        </div>
      )}
    </div>
  )
}
