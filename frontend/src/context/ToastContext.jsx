import { createContext, useCallback, useContext, useRef, useState } from 'react'
import { CheckCircle2, AlertTriangle, X } from 'lucide-react'

const ToastCtx = createContext(null)

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])
  const id = useRef(0)
  const dismiss = useCallback((tid) => setToasts((t) => t.filter((x) => x.id !== tid)), [])
  const toast = useCallback((message, { tone = 'success', action, duration = 4000 } = {}) => {
    const tid = ++id.current
    setToasts((t) => [...t.slice(-2), { id: tid, message, tone, action }])
    setTimeout(() => dismiss(tid), duration)
  }, [dismiss])
  return (
    <ToastCtx.Provider value={toast}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 bottom-24 z-50 flex flex-col items-center gap-2 px-4 md:bottom-8" aria-live="polite" role="status">
        {toasts.map((t) => (
          <div key={t.id} className="t-toast pointer-events-auto flex w-full max-w-sm items-center gap-3 rounded-xl bg-ink px-4 py-3 text-paper shadow-lift">
            {t.tone === 'error' ? <AlertTriangle className="h-5 w-5 shrink-0 text-[#ffb4ae]" aria-hidden /> : <CheckCircle2 className="h-5 w-5 shrink-0 text-[#8fe0b4]" aria-hidden />}
            <p className="flex-1 text-sm font-medium">{t.message}</p>
            {t.action && <button className="text-sm font-semibold underline underline-offset-4" onClick={() => { t.action.onClick(); dismiss(t.id) }}>{t.action.label}</button>}
            <button onClick={() => dismiss(t.id)} aria-label="Dismiss notification" className="rounded p-1 opacity-70 hover:opacity-100"><X className="h-4 w-4" /></button>
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  )
}

export const useToast = () => useContext(ToastCtx)
