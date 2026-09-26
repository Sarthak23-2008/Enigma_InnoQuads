import { useState } from 'react'
import { SprayCan } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import RiskBadge from '../components/RiskBadge'
import { InlineError } from '../components/States'
import { api } from '../services/api'

// FUTURE SCOPE preview: household / personal-care labels, using a separate dictionary from food.
export default function Household() {
  const [text, setText] = useState('')
  const [res, setRes] = useState(null)
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const run = async (e) => {
    e.preventDefault()
    if (!text.trim()) return setErr('Paste the ingredient list from the product.')
    setBusy(true); setErr('')
    try { setRes(await api.household(text)) } catch (x) { setErr(x.message) } finally { setBusy(false) }
  }
  return (
    <div className="max-w-3xl space-y-5">
      <PageHeader title="Household labels" back={{ to: '/check', label: 'Check a food' }}
        subtitle="Preview: check soaps, shampoos and cleaners for ingredient groups some people prefer to avoid. This uses a separate list from food and is not a safety rating." />
      <form onSubmit={run} className="panel space-y-3 p-5">
        <label className="label" htmlFor="hh">Ingredient list</label>
        <textarea id="hh" rows={5} className="field" placeholder="Aqua, Sodium Laureth Sulfate, Cocamidopropyl Betaine, Parfum, Methylparaben" value={text} onChange={(e) => setText(e.target.value)} maxLength={5000} />
        <InlineError>{err}</InlineError>
        <button className="btn-primary" disabled={busy}><SprayCan className="h-4 w-4" aria-hidden />{busy ? 'Checking…' : 'Check ingredients'}</button>
      </form>
      {res && (
        <section className="panel p-5" aria-live="polite">
          <div className="flex items-center justify-between gap-2"><h2 className="type-title text-lg">What we found</h2><RiskBadge level={res.level} /></div>
          <p className="mt-1 text-sm">{res.summary}</p>
          <ul className="mt-3 divide-y divide-line">
            {res.flags.map((f) => <li key={f.name} className="py-2 text-sm"><span className="font-semibold">{f.name}</span> ({f.matched.join(', ')}): {f.reason}</li>)}
          </ul>
          <p className="mt-3 text-xs text-muted">{res.disclaimer}</p>
        </section>
      )}
    </div>
  )
}
