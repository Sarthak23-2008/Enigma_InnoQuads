import { Loader2, AlertCircle, RotateCcw } from 'lucide-react'
import { Link } from 'react-router-dom'

export function LoadingState({ label = 'Loading…', block = true }) {
  return (
    <div className={`flex items-center gap-3 text-muted ${block ? 'justify-center py-16' : ''}`} role="status" aria-live="polite">
      <Loader2 className="h-5 w-5 animate-spin text-brand" aria-hidden />
      <span className="text-sm font-medium">{label}</span>
    </div>
  )
}

export function Skeleton({ className = '' }) {
  return <div className={`animate-pulse rounded-lg bg-line/70 ${className}`} aria-hidden />
}

export function ErrorState({ error, onRetry, title = "This didn't load" }) {
  const msg = typeof error === 'string' ? error : error?.message || 'Something went wrong. Please try again.'
  return (
    <div className="panel flex flex-col items-start gap-3 p-5" role="alert">
      <div className="flex items-center gap-2 font-semibold text-high"><AlertCircle className="h-5 w-5" aria-hidden />{title}</div>
      <p className="text-sm text-muted">{msg}</p>
      {onRetry && <button className="btn-secondary" onClick={onRetry}><RotateCcw className="h-4 w-4" aria-hidden />Try again</button>}
    </div>
  )
}

export function EmptyState({ icon: Icon, title, body, action }) {
  return (
    <div className="flex flex-col items-start gap-3 rounded-panel border border-dashed border-line bg-surface/60 p-6">
      {Icon && <Icon className="h-7 w-7 text-brand" aria-hidden />}
      <h3 className="type-title text-xl">{title}</h3>
      {body && <p className="max-w-prose text-sm text-muted">{body}</p>}
      {action && (action.to ? <Link to={action.to} className="btn-primary">{action.label}</Link>
        : <button className="btn-primary" onClick={action.onClick}>{action.label}</button>)}
    </div>
  )
}

export function InlineError({ children }) {
  if (!children) return null
  return <p className="mt-1.5 text-sm font-medium text-high" role="alert">{children}</p>
}
