import { NavLink, Link } from 'react-router-dom'
import { Home, History, Plus, LineChart, Settings } from 'lucide-react'

const item = 'flex flex-1 flex-col items-center gap-0.5 py-2 text-[0.7rem] font-semibold'
export default function MobileBottomNav() {
  const cls = ({ isActive }) => `${item} ${isActive ? 'text-brand' : 'text-muted'}`
  return (
    <nav aria-label="Main" className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-surface/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden">
      <div className="mx-auto flex max-w-md items-end">
        <NavLink to="/" end className={cls}><Home className="h-5 w-5" aria-hidden />Home</NavLink>
        <NavLink to="/history" className={cls}><History className="h-5 w-5" aria-hidden />History</NavLink>
        <div className="flex flex-1 justify-center">
          <Link to="/check" aria-label="Check food" className="-mt-5 flex h-14 w-14 items-center justify-center rounded-full bg-brand text-white shadow-lift ring-4 ring-paper">
            <Plus className="h-7 w-7" aria-hidden />
          </Link>
        </div>
        <NavLink to="/trends" className={cls}><LineChart className="h-5 w-5" aria-hidden />Trends</NavLink>
        <NavLink to="/settings" className={cls}><Settings className="h-5 w-5" aria-hidden />Settings</NavLink>
      </div>
    </nav>
  )
}
