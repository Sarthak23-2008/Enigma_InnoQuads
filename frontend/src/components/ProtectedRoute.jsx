import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { LoadingState, ErrorState } from './States'

export default function ProtectedRoute({ children, allowIncompleteOnboarding = false }) {
  const { status, user, refresh } = useAuth()
  const loc = useLocation()
  if (status === 'loading') return <LoadingState label="Loading your account…" />
  if (status === 'error') return <div className="mx-auto max-w-md p-6"><ErrorState error="Unable to connect. Please try again." onRetry={refresh} /></div>
  if (status !== 'authed') return <Navigate to="/login" replace state={{ from: loc.pathname + loc.search }} />
  if (!allowIncompleteOnboarding && user && !user.onboarding_complete) return <Navigate to="/onboarding" replace />
  return children
}
