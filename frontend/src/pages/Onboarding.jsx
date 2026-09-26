import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Logo from '../components/Logo'
import { ChipSelect, KeyedSelect } from '../components/ProfileEditor'
import { ErrorState, LoadingState } from '../components/States'
import { api } from '../services/api'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'

const STEPS = ['Allergies', 'Intolerances', 'Diet', 'Health', 'Goals']

export default function Onboarding() {
  const { user, setUser } = useAuth()
  const toast = useToast()
  const nav = useNavigate()
  const [opts, setOpts] = useState(null)
  const [err, setErr] = useState(null)
  const [step, setStep] = useState(0)
  const [busy, setBusy] = useState(false)
  const [p, setP] = useState({ allergies: [], intolerances: [], dietary_preferences: [], health_conditions: [], goals: [] })

  useEffect(() => {
    Promise.all([api.profileOptions(), api.profile()]).then(([o, prof]) => {
      setOpts(o)
      setP({ allergies: prof.allergies, intolerances: prof.intolerances, dietary_preferences: prof.dietary_preferences, health_conditions: prof.health_conditions, goals: prof.goals })
    }).catch(setErr)
  }, [])

  const finish = async () => {
    setBusy(true)
    try {
      await api.saveProfile({ ...p, complete_onboarding: true })
      setUser({ ...user, onboarding_complete: true })
      toast('Your food profile is set up.')
      nav('/', { replace: true })
    } catch (e) { toast(e.message, { tone: 'error' }) } finally { setBusy(false) }
  }
  const set = (k) => (v) => setP((s) => ({ ...s, [k]: v }))

  if (err) return <div className="mx-auto max-w-md p-6"><ErrorState error={err} /></div>
  if (!opts) return <LoadingState label="Loading profile options…" />
  const body = [
    <ChipSelect key="a" idPrefix="allergy" legend="Do you have any food allergies?" hint="SafeBite marks foods containing these as High risk, including trace amounts." options={opts.allergies} value={p.allergies} onChange={set('allergies')} />,
    <ChipSelect key="i" idPrefix="intol" legend="Any food intolerances?" hint="Foods with these ingredients are marked Caution." options={opts.intolerances} value={p.intolerances} onChange={set('intolerances')} />,
    <ChipSelect key="d" idPrefix="pref" legend="How do you eat?" hint="Foods that don't fit your diet are marked Caution." options={opts.preferences} value={p.dietary_preferences} onChange={set('dietary_preferences')} />,
    <KeyedSelect key="h" legend="Anything SafeBite should keep in mind?" hint="Optional. Only what you choose here is used, to flag sugar, sodium or potassium. SafeBite never diagnoses anything." options={opts.health_conditions} value={p.health_conditions} onChange={set('health_conditions')} />,
    <KeyedSelect key="g" legend="What would you like to work on?" hint="Your trends will put these first and track your progress." options={opts.goals} value={p.goals} onChange={set('goals')} />,
  ][step]
  const last = step === STEPS.length - 1
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex h-16 max-w-2xl items-center px-4"><Logo to="/onboarding" /></header>
      <main id="main" className="mx-auto max-w-2xl px-4 pb-16 pt-4">
        <h1 className="type-display text-5xl">Set up your food profile</h1>
        <ol className="mt-6 flex gap-1.5" aria-label="Progress">
          {STEPS.map((s, i) => (
            <li key={s} className="flex-1">
              <span className={`block h-1.5 rounded-full ${i <= step ? 'bg-brand' : 'bg-line'}`} aria-hidden />
              <span className={`mt-1.5 block text-xs font-semibold ${i === step ? 'text-ink' : 'text-muted'}`} aria-current={i === step ? 'step' : undefined}>{s}</span>
            </li>
          ))}
        </ol>
        <div key={step} className="t-forward panel mt-6 p-5 sm:p-6">{body}</div>
        <div className="mt-6 flex flex-wrap items-center gap-2">
          {step > 0 && <button className="btn-secondary" onClick={() => setStep(step - 1)} disabled={busy}>Back</button>}
          <button className="btn-primary px-6" onClick={() => (last ? finish() : setStep(step + 1))} disabled={busy}>{last ? (busy ? 'Saving…' : 'Finish setup') : 'Continue'}</button>
          {!last && <button className="btn-ghost ml-auto" onClick={() => setStep(step + 1)}>Skip for now</button>}
        </div>
        <p className="mt-6 text-sm text-muted">You can change any of this later in Settings.</p>
      </main>
    </div>
  )
}
