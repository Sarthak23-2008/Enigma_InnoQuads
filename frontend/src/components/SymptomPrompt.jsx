import { useState } from 'react'
import { MessageCircleQuestion } from 'lucide-react'
import { api } from '../services/api'
import { useToast } from '../context/ToastContext'
import { fmtDate, mealLabel } from '../utils/format'

const OPTIONS = [{ k: 'none', l: 'No, all fine' }, { k: 'mild', l: 'Mild' }, { k: 'moderate', l: 'Moderate' }, { k: 'severe', l: 'Severe' }]

// Check-in 2–3 days after an unpackaged food. Observational only; never a diagnosis.
export default function SymptomPrompt({ log, question, onDone }) {
  const toast = useToast()
  const [sev, setSev] = useState(null)
  const [symptom, setSymptom] = useState('')
  const [busy, setBusy] = useState(false)
  const submit = async (severity) => {
    setBusy(true)
    try {
      const r = await api.submitSymptom({ food_log_id: log.log_id, severity, symptom: symptom.trim() })
      toast(r.message)
      if (r.association) toast(r.association.message, { duration: 7000 })
      onDone?.(r)
    } catch (e) { toast(e.message, { tone: 'error' }) } finally { setBusy(false) }
  }
  return (
    <div className="panel p-4">
      <div className="flex items-start gap-3">
        <MessageCircleQuestion className="mt-0.5 h-5 w-5 shrink-0 text-brand" aria-hidden />
        <div className="min-w-0 flex-1">
          <p className="font-semibold">{question}</p>
          <p className="text-sm text-muted">{log.food_name}, {mealLabel(log.meal_type).toLowerCase()} on {fmtDate(log.consumed_at, { weekday: 'short', day: 'numeric', month: 'short' })}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {OPTIONS.map((o) => (
              <button key={o.k} disabled={busy} onClick={() => (o.k === 'none' ? submit('none') : setSev(o.k))}
                className={`chip ${sev === o.k ? 'border-brand bg-brand-soft text-brand' : 'border-line bg-surface hover:border-ink/40'}`}>{o.l}</button>
            ))}
          </div>
          {sev && (
            <div className="t-fade mt-3 flex flex-col gap-2 sm:flex-row">
              <label className="sr-only" htmlFor={`sym-${log.log_id}`}>What did you notice?</label>
              <input id={`sym-${log.log_id}`} className="field" maxLength={200} placeholder="What did you notice? (optional)" value={symptom} onChange={(e) => setSymptom(e.target.value)} />
              <button className="btn-primary" disabled={busy} onClick={() => submit(sev)}>Save check-in</button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
