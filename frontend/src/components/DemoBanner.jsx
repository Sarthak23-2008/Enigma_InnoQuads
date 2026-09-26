import { useState } from 'react'
import { Info, RotateCcw } from 'lucide-react'
import { api } from '../services/api'
import { useToast } from '../context/ToastContext'

export default function DemoBanner() {
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const reset = async () => {
    setBusy(true)
    try { await api.resetDemo(); toast('Demo data was reset.'); setTimeout(() => window.location.reload(), 600) }
    catch (e) { toast(e.message, { tone: 'error' }) } finally { setBusy(false) }
  }
  return (
    <div className="border-b border-brand/20 bg-brand-soft text-sm text-ink">
      <div className="mx-auto flex max-w-page flex-wrap items-center gap-x-3 gap-y-1 px-4 py-2">
        <Info className="h-4 w-4 text-brand" aria-hidden />
        <span><strong>Demo account.</strong> Aryan's profile and 30 days of meals are sample data.</span>
        <button onClick={reset} disabled={busy} className="ml-auto inline-flex items-center gap-1 font-semibold text-brand underline-offset-4 hover:underline">
          <RotateCcw className="h-3.5 w-3.5" aria-hidden />{busy ? 'Resetting…' : 'Reset demo data'}
        </button>
      </div>
    </div>
  )
}
