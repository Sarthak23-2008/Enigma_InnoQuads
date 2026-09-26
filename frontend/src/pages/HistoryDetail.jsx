import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Trash2, Repeat } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import RiskResultCard from '../components/RiskResultCard'
import IngredientList from '../components/IngredientList'
import NutritionCard from '../components/NutritionCard'
import MealPicker from '../components/MealPicker'
import Modal from '../components/Modal'
import SymptomPrompt from '../components/SymptomPrompt'
import { ErrorState, LoadingState } from '../components/States'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'
import { useToast } from '../context/ToastContext'
import { fmtDateTime, mealLabel, METHOD_LABEL } from '../utils/format'

export default function HistoryDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const toast = useToast()
  const { data: l, error, loading, reload, setData } = useAsync(() => api.historyItem(id), [id])
  const [confirm, setConfirm] = useState(false)
  const [editing, setEditing] = useState(false)
  const [busy, setBusy] = useState(false)

  if (error) return <ErrorState error={error.status === 404 ? 'This log entry was not found.' : error} onRetry={reload} />
  if (loading || !l) return <LoadingState />

  const saveMeal = async (meal) => {
    try { const u = await api.updateLog(l.log_id, { meal_type: meal }); setData((s) => ({ ...s, ...u, analysis: s.analysis })); setEditing(false); toast('Meal updated.') }
    catch (e) { toast(e.message, { tone: 'error' }) }
  }
  const del = async () => {
    setBusy(true)
    try { await api.deleteLog(l.log_id); toast('Removed from your history.'); nav('/history', { replace: true }) }
    catch (e) { toast(e.message, { tone: 'error' }); setBusy(false) }
  }
  const a = l.analysis

  return (
    <div className="space-y-6">
      <PageHeader title={l.food_name} back={{ to: '/history', label: 'History' }}
        subtitle={`${mealLabel(l.meal_type)}, ${fmtDateTime(l.consumed_at)}. ${l.quantity} serving${l.quantity === 1 ? '' : 's'}. ${METHOD_LABEL[l.input_method]}.`}
        actions={<>
          <button className="btn-secondary" onClick={() => setEditing((e) => !e)}>Change meal</button>
          <button className="btn-secondary text-high" onClick={() => setConfirm(true)}><Trash2 className="h-4 w-4" aria-hidden />Delete</button>
        </>} />
      {editing && <div className="panel max-w-md p-4"><MealPicker value={l.meal_type} onChange={saveMeal} /></div>}
      {l.is_demo && <p className="text-sm text-muted">This entry is part of the demo data.</p>}

      {l.symptom_prompt_due && <SymptomPrompt log={l} question="Any discomfort or reaction since eating this?" onDone={() => reload()} />}
      {l.symptom && (
        <div className="panel p-4 text-sm">
          <p className="font-semibold">Your check-in: {l.symptom.severity === 'none' ? 'no symptoms' : `${l.symptom.severity}${l.symptom.symptom ? `, ${l.symptom.symptom}` : ''}`}</p>
        </div>
      )}
      {l.symptom_association && (
        <div className="flex gap-3 rounded-panel border-l-4 border-caution bg-caution-soft/70 p-4">
          <Repeat className="mt-0.5 h-5 w-5 shrink-0 text-caution" aria-hidden />
          <div><p className="font-semibold">{l.symptom_association.message}</p><p className="text-sm text-ink/80">{l.symptom_association.note}</p></div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-6">
          {a ? (
            <>
              <RiskResultCard result={a} />
              <section className="panel p-5"><h2 className="type-title mb-3 text-lg">Ingredients checked</h2><IngredientList details={a.ingredient_details} conflicts={a.detected_conflicts} /></section>
            </>
          ) : <p className="text-sm text-muted">The original analysis isn't available for this entry.</p>}
        </div>
        <NutritionCard nutrition={l.nutrition} title={`Nutrition logged (${l.quantity} serving${l.quantity === 1 ? '' : 's'})`} />
      </div>

      <Modal open={confirm} title="Delete this entry?" onClose={() => setConfirm(false)}
        footer={<><button className="btn-secondary" onClick={() => setConfirm(false)}>Keep it</button><button className="btn-danger" onClick={del} disabled={busy}>Delete entry</button></>}>
        <p>{l.food_name} will be removed from your history and trends.</p>
      </Modal>
    </div>
  )
}
