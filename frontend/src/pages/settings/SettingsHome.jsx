import { Link, useNavigate } from 'react-router-dom'
import { UserRound, Bell, History, SlidersHorizontal, KeyRound, Accessibility, ChevronRight, LogOut, Stethoscope, Home as HomeIcon, Shield } from 'lucide-react'
import PageHeader from '../../components/PageHeader'
import { useAuth } from '../../context/AuthContext'

const ITEMS = [
  { to: '/settings/profile', Icon: UserRound, title: 'Dietary profile', body: 'Allergies, intolerances, diet, health considerations, goals' },
  { to: '/settings/notifications', Icon: Bell, title: 'Notifications', body: 'Weekly, bi-weekly and monthly diet reports' },
  { to: '/settings/diet-history', Icon: History, title: 'Diet history', body: 'View, export or clear your logs' },
  { to: '/settings/input-preferences', Icon: SlidersHorizontal, title: 'Input preferences', body: 'Default check method, label language, auto-log' },
  { to: '/settings/accessibility', Icon: Accessibility, title: 'Accessibility', body: 'Text size, high contrast, voice assistance' },
  { to: '/settings/account', Icon: KeyRound, title: 'Account', body: 'Name, email, export data, delete account' },
]
const MORE = [
  { to: '/consult', Icon: Stethoscope, title: 'Consult a professional' },
  { to: '/household', Icon: HomeIcon, title: 'Household labels (preview)' },
  { to: '/privacy', Icon: Shield, title: 'Privacy' },
]

export default function SettingsHome() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  return (
    <div className="max-w-3xl">
      <PageHeader title="Settings" subtitle={`Signed in as ${user?.email}`} />
      <ul className="panel divide-y divide-line overflow-hidden">
        {ITEMS.map(({ to, Icon, title, body }) => (
          <li key={to}>
            <Link to={to} className="flex items-center gap-4 px-5 py-4 hover:bg-paper">
              <Icon className="h-5 w-5 shrink-0 text-brand" aria-hidden />
              <div className="min-w-0 flex-1"><p className="font-semibold">{title}</p><p className="truncate text-sm text-muted">{body}</p></div>
              <ChevronRight className="h-5 w-5 text-muted" aria-hidden />
            </Link>
          </li>
        ))}
      </ul>
      <ul className="panel mt-4 divide-y divide-line overflow-hidden">
        {MORE.map(({ to, Icon, title }) => (
          <li key={to}><Link to={to} className="flex items-center gap-4 px-5 py-3.5 hover:bg-paper"><Icon className="h-5 w-5 text-muted" aria-hidden /><span className="flex-1 font-medium">{title}</span><ChevronRight className="h-5 w-5 text-muted" aria-hidden /></Link></li>
        ))}
      </ul>
      <button className="btn-secondary mt-6" onClick={async () => { await logout(); nav('/login') }}><LogOut className="h-4 w-4" aria-hidden />Log out</button>
    </div>
  )
}
