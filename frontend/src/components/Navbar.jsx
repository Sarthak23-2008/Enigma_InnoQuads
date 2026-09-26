import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { ChevronDown, LogOut, Settings, UserRound, Stethoscope, Shield } from 'lucide-react'
import Logo from './Logo'
import CheckFoodButton from './CheckFoodButton'
import VoiceButton from './VoiceButton'
import { useAuth } from '../context/AuthContext'
import { usePrefs } from '../context/PrefsContext'

const links = [{ to: '/', label: 'Home', end: true }, { to: '/history', label: 'History' }, { to: '/trends', label: 'Trends' }]

export default function Navbar() {
  const { user, logout } = useAuth()
  const { prefs } = usePrefs()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const menu = useRef(null)
  useEffect(() => {
    const close = (e) => { if (menu.current && !menu.current.contains(e.target)) setOpen(false) }
    const esc = (e) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', close); document.addEventListener('keydown', esc)
    return () => { document.removeEventListener('mousedown', close); document.removeEventListener('keydown', esc) }
  }, [])
  const initials = (user?.name || '?').split(' ').map((p) => p[0]).slice(0, 2).join('').toUpperCase()
  const doLogout = async () => { setOpen(false); await logout(); navigate('/login') }
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-paper/90 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-page items-center gap-4 px-4">
        <Logo />
        <nav className="ml-6 hidden items-center gap-1 md:flex" aria-label="Main">
          {links.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={({ isActive }) => `rounded-lg px-3 py-2 text-[0.95rem] font-semibold ${isActive ? 'bg-ink/5 text-ink' : 'text-muted hover:text-ink'}`}>{l.label}</NavLink>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2">
          {prefs.accessibility?.voice_assistance && <VoiceButton />}
          <CheckFoodButton className="hidden md:inline-flex" />
          <div className="relative" ref={menu}>
            <button onClick={() => setOpen((o) => !o)} aria-haspopup="menu" aria-expanded={open} aria-label="Account menu"
              className="flex items-center gap-1 rounded-full border border-line bg-surface p-1 pr-2 hover:border-ink/40">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-ink text-sm font-bold text-paper">{initials}</span>
              <ChevronDown className="h-4 w-4 text-muted" aria-hidden />
            </button>
            {open && (
              <div role="menu" className="t-scale absolute right-0 mt-2 w-60 origin-top-right rounded-xl border border-line bg-surface p-1.5 shadow-lift">
                <div className="px-3 py-2">
                  <p className="font-semibold">{user?.name}</p>
                  <p className="truncate text-sm text-muted">{user?.email}</p>
                </div>
                <div className="my-1 border-t border-line" />
                {[{ to: '/settings/profile', label: 'Dietary profile', Icon: UserRound }, { to: '/settings', label: 'Settings', Icon: Settings },
                  { to: '/consult', label: 'Consult a professional', Icon: Stethoscope }, { to: '/privacy', label: 'Privacy', Icon: Shield }].map(({ to, label, Icon }) => (
                  <Link key={to} role="menuitem" to={to} onClick={() => setOpen(false)} className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm font-medium hover:bg-paper">
                    <Icon className="h-4 w-4 text-muted" aria-hidden />{label}
                  </Link>
                ))}
                <div className="my-1 border-t border-line" />
                <button role="menuitem" onClick={doLogout} className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm font-medium hover:bg-paper">
                  <LogOut className="h-4 w-4 text-muted" aria-hidden />Log out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
