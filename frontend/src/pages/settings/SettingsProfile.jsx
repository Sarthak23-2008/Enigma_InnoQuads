import { useEffect, useState } from 'react'
import PageHeader from '../../components/PageHeader'
import { ChipSelect, KeyedSelect } from '../../components/ProfileEditor'
import { ErrorState, LoadingState } from '../../components/States'
import { api } from '../../services/api'
import { useToast } from '../../context/ToastContext'

export default function SettingsProfile() {
  const toast = useToast()
  const [opts, setOpts] = useState(null)
  const [p, setP] = useState(null)
  const [orig, setOrig] = useState('')
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  const load = () => Promise.all([api.profileOptions(), api.profile()]).then(([o, prof]) => {
    const v = { allergies: prof.allergies, intolerances: prof.intolerances, dietary_preferences: prof.dietary_preferences, health_conditions: prof.health_conditions, goals: prof.goals }
    setOpts(o); setP(v); setOrig(JSON.stringify(v)); setErr(null)
  }).catch(setErr)
  useEffect(() => { load() }, [])
  if (err) return <ErrorState error={err} onRetry={load} />
  if (!p) return <LoadingState />
  const set = (k) => (v) => setP((s) => ({ ...s, [k]: v }))
  const dirty = JSON.stringify(p) !== orig
  const save = async () => {
    setBusy(true)
    try { const r = await api.saveProfile(p); setOrig(JSON.stringify({ allergies: r.allergies, intolerances: r.intolerances, dietary_preferences: r.dietary_preferences, health_conditions: r.health_conditions, goals: r.goals })); toast('Profile saved. New checks will use it.') }
    catch (e) { toast(e.message, { tone: 'error' }) } finally { setBusy(false) }
  }
  return (
    <div className="max-w-3xl space-y-5">
      <PageHeader title="Dietary profile" back={{ to: '/settings', label: 'Settings' }} subtitle="Every food check compares ingredients against this profile. Earlier results keep the profile they were checked with." />
      <div className="panel p-5"><ChipSelect idPrefix="s-all" legend="Allergies" hint="Marked High risk, including traces." options={opts.allergies} value={p.allergies} onChange={set('allergies')} /></div>
      <div className="panel p-5"><ChipSelect idPrefix="s-int" legend="Intolerances" hint="Marked Caution." options={opts.intolerances} value={p.intolerances} onChange={set('intolerances')} /></div>
      <div className="panel p-5"><ChipSelect idPrefix="s-pref" legend="Diet" options={opts.preferences} value={p.dietary_preferences} onChange={set('dietary_preferences')} /></div>
      <div className="panel p-5"><KeyedSelect legend="Health considerations" hint="Optional. Used only to flag sugar, sodium or potassium. Never a diagnosis." options={opts.health_conditions} value={p.health_conditions} onChange={set('health_conditions')} /></div>
      <div className="panel p-5"><KeyedSelect legend="Goals" options={opts.goals} value={p.goals} onChange={set('goals')} /></div>
      <div className="sticky bottom-20 z-10 flex items-center gap-3 rounded-panel border border-line bg-surface/95 p-3 backdrop-blur md:bottom-4">
        <button className="btn-primary" onClick={save} disabled={!dirty || busy}>{busy ? 'Saving…' : 'Save profile'}</button>
        <span className="text-sm text-muted">{dirty ? 'You have unsaved changes.' : 'All changes saved.'}</span>
      </div>
    </div>
  )
}
