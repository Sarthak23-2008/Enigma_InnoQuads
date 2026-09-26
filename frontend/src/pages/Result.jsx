import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { Volume2, Square, Check, Minus, Plus, Info, TriangleAlert, ArrowLeft } from 'lucide-react'
import RiskResultCard from '../components/RiskResultCard'
import IngredientList from '../components/IngredientList'
import NutritionCard from '../components/NutritionCard'
import AlternativeFoodCard from '../components/AlternativeFoodCard'
import MealPicker from '../components/MealPicker'
import { ErrorState, LoadingState } from '../components/States'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { canSpeak, useSpeak } from '../hooks/useSpeech'
import { usePrefs } from '../context/PrefsContext'
import { useToast } from '../context/ToastContext'
import { mealForNow, METHOD_LABEL } from '../utils/format'

function speechFor(r) {
  const word = { LOW: 'Low risk', CAUTION: 'Caution', HIGH: 'High risk' }[r.risk_level]
  return `${r.food_name}. ${word}. ${r.explanation}${r.alternatives?.length ? ` You could try ${r.alternatives.map((a) => a.name).join(', or ')} instead.` : ''}`
}

export default function Result() {
  const { id } = useParams()
  const loc = useLocation()
  const nav = useNavigate()
  const toast = useToast()
  const { prefs } = usePrefs()
  const { data: r, error, loading, reload, setData } = useAsync(() => api.result(id), [id])
  const [meal, setMeal] = useState(null)
  const [qty, setQty] = useState(1)
  const [logging, setLogging] = useState(false)
  const { speak, stop, speaking } = useSpeak()
  const autoDone = useRef(false)

  useEffect(() => { if (r && !meal) setMeal(r.suggested_meal_type || mealForNow()) }, [r, meal])

  const logIt = useCallback(async (mealType = meal, quantity = qty) => {
    setLogging(true)
    try {
      const l = await api.logFood({ scan_id: r.scan_id, meal_type: mealType, quantity })
      setData((s) => ({ ...s, logged_log_id: l.log_id }))
      toast(l.message, { action: { label: 'View history', onClick: () => nav('/history') } })
    } catch (e) { toast(e.message, { tone: 'error' }) } finally { setLogging(false) }
  }, [r, meal, qty, toast, nav, setData])

  // Optional behaviours from settings: auto-log, and read the result aloud when voice assistance is on.
  useEffect(() => {
    if (!r || !loc.state?.fresh || autoDone.current) return
    autoDone.current = true
    if (prefs.accessibility?.voice_assistance) speak(speechFor(r))
    if (prefs.input_prefs?.auto_log && !r.logged_log_id) logIt(r.suggested_meal_type || mealForNow(), 1)
  }, [r]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const h = () => r && speak(speechFor(r))
    window.addEventListener('sb:read-result', h)
    return () => window.removeEventListener('sb:read-result', h)
  }, [r, speak])

  if (error) return <ErrorState error={error.status === 404 ? 'This result was not found.' : error} onRetry={error.status === 404 ? undefined : reload} />
  if (loading || !r) return <LoadingState label="Loading result…" />
  const logged = !!r.logged_log_id

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Link to="/check" className="inline-flex items-center gap-1 text-sm font-semibold text-muted hover:text-ink"><ArrowLeft className="h-4 w-4" aria-hidden />Check another food</Link>
        <div className="flex items-center gap-2 text-sm text-muted">
          <span>{METHOD_LABEL[r.input_method]}</span>
          {r.estimate && <span className="rounded-md border border-caution bg-caution-soft px-2 py-0.5 text-xs font-bold text-caution">{r.estimate.label}</span>}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-6">
          <RiskResultCard result={r} />
          {canSpeak && (
            <button className="btn-secondary" onClick={() => (speaking ? stop() : speak(speechFor(r)))} aria-pressed={speaking}>
              {speaking ? <Square className="h-4 w-4" aria-hidden /> : <Volume2 className="h-4 w-4" aria-hidden />}{speaking ? 'Stop reading' : 'Read result aloud'}
            </button>
          )}

          {r.estimate && (
            <div className="flex gap-3 rounded-panel border border-caution/40 bg-caution-soft/60 p-4 text-sm">
              <Info className="mt-0.5 h-5 w-5 shrink-0 text-caution" aria-hidden />
              <p>{r.estimate.note}</p>
            </div>
          )}

          <section className="panel p-5" aria-labelledby="ings">
            <h2 id="ings" className="type-title text-lg">Ingredients checked</h2>
            <p className="mb-3 text-sm text-muted">Highlighted ingredients are the ones that matched your profile.</p>
            <IngredientList details={r.ingredient_details} conflicts={r.detected_conflicts} />
            {(r.allergen_statements?.contains?.length > 0 || r.allergen_statements?.may_contain?.length > 0) && (
              <dl className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
                {r.allergen_statements.contains?.length > 0 && <div><dt className="font-semibold">Label says contains</dt><dd className="text-muted">{r.allergen_statements.contains.join(', ')}</dd></div>}
                {r.allergen_statements.may_contain?.length > 0 && <div><dt className="font-semibold">Label says may contain</dt><dd className="text-muted">{r.allergen_statements.may_contain.join(', ')}</dd></div>}
              </dl>
            )}
          </section>

          {r.alternatives?.length > 0 && (
            <section aria-labelledby="alts">
              <h2 id="alts" className="type-title text-2xl">Try instead</h2>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">{r.alternatives.map((a) => <AlternativeFoodCard key={a.name} alt={a} />)}</div>
            </section>
          )}

          {(r.warnings?.length > 0 || r.notes?.length > 0) && (
            <section className="panel p-5 text-sm" aria-labelledby="notes">
              <h2 id="notes" className="type-title text-lg">Good to know</h2>
              <ul className="mt-2 space-y-2">
                {[...(r.notes || []), ...(r.warnings || [])].map((w, i) => (
                  <li key={i} className="flex gap-2"><TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-muted" aria-hidden />{w}</li>
                ))}
              </ul>
            </section>
          )}
        </div>

        <div className="space-y-6">
          <section className="panel p-5 lg:sticky lg:top-24" aria-labelledby="ate">
            <h2 id="ate" className="type-title text-xl">Did you eat it?</h2>
            {logged ? (
              <div className="mt-3">
                <p className="flex items-center gap-2 font-semibold text-low"><Check className="h-5 w-5" aria-hidden />Added to your diet history.</p>
                <Link to={`/history/${r.logged_log_id}`} className="link mt-2 inline-block text-sm">View in history</Link>
              </div>
            ) : (
              <div className="mt-3 space-y-4">
                <p className="text-sm text-muted">Logging only what you actually eat keeps your trends accurate.</p>
                <MealPicker value={meal} onChange={setMeal} />
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold" id="qty-label">Servings</span>
                  <div className="flex items-center gap-2" role="group" aria-labelledby="qty-label">
                    <button className="btn-secondary h-10 min-h-0 w-10 p-0" aria-label="Fewer servings" onClick={() => setQty((q) => Math.max(0.5, q - 0.5))}><Minus className="h-4 w-4" /></button>
                    <span className="w-10 text-center font-bold tabular" aria-live="polite">{qty}</span>
                    <button className="btn-secondary h-10 min-h-0 w-10 p-0" aria-label="More servings" onClick={() => setQty((q) => Math.min(10, q + 0.5))}><Plus className="h-4 w-4" /></button>
                  </div>
                </div>
                <button className="btn-primary w-full text-base" onClick={() => logIt()} disabled={logging}>{logging ? 'Adding…' : 'I Ate This'}</button>
              </div>
            )}
          </section>
          <NutritionCard nutrition={r.nutrition} ranges={r.estimate?.ranges} title="Nutrition per serving" />
          <p className="text-xs text-muted">{r.disclaimer}</p>
        </div>
      </div>
    </div>
  )
}
