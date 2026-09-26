import { useEffect, useRef } from 'react'
import { Outlet, useLocation, useNavigationType } from 'react-router-dom'
import Navbar from '../components/Navbar'
import MobileBottomNav from '../components/MobileBottomNav'
import DemoBanner from '../components/DemoBanner'
import { useAuth } from '../context/AuthContext'

// Transition per navigation type (subtle, 160–240 ms; disabled under reduced motion):
//  tab peers -> fade, forward into the check flow / detail -> slide forward, back -> slide back,
//  result -> rise up, settings subpages -> push.
function transitionFor(path, navType) {
  if (navType === 'POP') return 't-back'
  if (path.startsWith('/result')) return 't-up'
  if (path.startsWith('/check') || /^\/history\/\d+/.test(path) || /^\/settings\/.+/.test(path)) return 't-forward'
  return 't-fade'
}

export default function AppLayout() {
  const { user } = useAuth()
  const loc = useLocation()
  const navType = useNavigationType()
  const main = useRef(null)
  useEffect(() => { window.scrollTo(0, 0) }, [loc.pathname])
  return (
    <div className="min-h-screen">
      <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:left-3 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-surface focus:px-3 focus:py-2">Skip to content</a>
      {user?.is_demo && <DemoBanner />}
      <Navbar />
      <main id="main" ref={main} key={loc.pathname} className={`${transitionFor(loc.pathname, navType)} mx-auto max-w-page px-4 pb-safe pt-6 sm:pt-8`}>
        <Outlet />
      </main>
      <MobileBottomNav />
    </div>
  )
}
