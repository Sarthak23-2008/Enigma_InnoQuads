import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import ProtectedRoute from './components/ProtectedRoute'
import { LoadingState } from './components/States'
import { useAuth } from './context/AuthContext'
import Landing from './pages/Landing'

const Login = lazy(() => import('./pages/Login'))
const Signup = lazy(() => import('./pages/Signup'))
const Onboarding = lazy(() => import('./pages/Onboarding'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const CheckHub = lazy(() => import('./pages/CheckHub'))
const Scan = lazy(() => import('./pages/Scan'))
const Search = lazy(() => import('./pages/Search'))
const Manual = lazy(() => import('./pages/Manual'))
const EatingOut = lazy(() => import('./pages/EatingOut'))
const Result = lazy(() => import('./pages/Result'))
const History = lazy(() => import('./pages/History'))
const HistoryDetail = lazy(() => import('./pages/HistoryDetail'))
const Trends = lazy(() => import('./pages/Trends'))
const Consult = lazy(() => import('./pages/Consult'))
const Household = lazy(() => import('./pages/Household'))
const Privacy = lazy(() => import('./pages/Privacy'))
const NotFound = lazy(() => import('./pages/NotFound'))
const SettingsHome = lazy(() => import('./pages/settings/SettingsHome'))
const SettingsProfile = lazy(() => import('./pages/settings/SettingsProfile'))
const SettingsNotifications = lazy(() => import('./pages/settings/SettingsNotifications'))
const SettingsDietHistory = lazy(() => import('./pages/settings/SettingsDietHistory'))
const SettingsInputPrefs = lazy(() => import('./pages/settings/SettingsInputPrefs'))
const SettingsAccount = lazy(() => import('./pages/settings/SettingsAccount'))
const SettingsAccessibility = lazy(() => import('./pages/settings/SettingsAccessibility'))

function Home() {
  const { status, user } = useAuth()
  if (status === 'loading') return <LoadingState />
  if (status !== 'authed') return <Landing />
  if (!user.onboarding_complete) return <Navigate to="/onboarding" replace />
  return null // handled by the nested dashboard route
}

function PublicOnly({ children }) {
  const { status } = useAuth()
  if (status === 'loading') return <LoadingState />
  return status === 'authed' ? <Navigate to="/" replace /> : children
}

export default function App() {
  const { status } = useAuth()
  const authed = status === 'authed'
  return (
    <Suspense fallback={<LoadingState />}>
      <Routes>
        {!authed && <Route path="/" element={<Home />} />}
        <Route path="/login" element={<PublicOnly><Login /></PublicOnly>} />
        <Route path="/signup" element={<PublicOnly><Signup /></PublicOnly>} />
        <Route path="/onboarding" element={<ProtectedRoute allowIncompleteOnboarding><Onboarding /></ProtectedRoute>} />
        <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
          {authed && <Route path="/" element={<Dashboard />} />}
          <Route path="/check" element={<CheckHub />} />
          <Route path="/check/scan" element={<Scan />} />
          <Route path="/check/search" element={<Search />} />
          <Route path="/check/manual" element={<Manual />} />
          <Route path="/check/eating-out" element={<EatingOut />} />
          <Route path="/result/:id" element={<Result />} />
          <Route path="/history" element={<History />} />
          <Route path="/history/:id" element={<HistoryDetail />} />
          <Route path="/trends" element={<Trends />} />
          <Route path="/settings" element={<SettingsHome />} />
          <Route path="/settings/profile" element={<SettingsProfile />} />
          <Route path="/settings/notifications" element={<SettingsNotifications />} />
          <Route path="/settings/diet-history" element={<SettingsDietHistory />} />
          <Route path="/settings/input-preferences" element={<SettingsInputPrefs />} />
          <Route path="/settings/account" element={<SettingsAccount />} />
          <Route path="/settings/accessibility" element={<SettingsAccessibility />} />
          <Route path="/consult" element={<Consult />} />
          <Route path="/household" element={<Household />} />
        </Route>
        <Route path="/privacy" element={<Privacy />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Suspense>
  )
}
