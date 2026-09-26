import { Link } from 'react-router-dom'
import { ScanLine, Search, PencilLine, UtensilsCrossed, ChevronRight } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import { usePrefs } from '../context/PrefsContext'

const SECONDARY = [
  { to: '/check/search', Icon: Search, title: 'Search Food', body: 'Look up a common dish or packaged food.' },
  { to: '/check/manual', Icon: PencilLine, title: 'Enter Manually', body: 'Type a home-cooked meal and its ingredients.' },
  { to: '/check/eating-out', Icon: UtensilsCrossed, title: 'Eating out', body: 'Check a restaurant dish with estimated ingredients.' },
]

export default function CheckHub() {
  const { prefs } = usePrefs()
  const def = prefs.input_prefs?.default_input_method
  return (
    <div>
      <PageHeader title="Check a food" subtitle="SafeBite compares the ingredients with your allergies, intolerances and diet." />
      <Link to="/check/scan" className="group flex items-center gap-5 rounded-panel bg-brand p-6 text-white shadow-lift sm:p-8">
        <ScanLine className="h-12 w-12 shrink-0" aria-hidden />
        <div className="flex-1">
          <p className="type-display text-4xl">Scan Food Label</p>
          <p className="mt-1 text-white/85">Fastest for packaged food. Photograph the ingredients and nutrition panel.</p>
        </div>
        <ChevronRight className="h-7 w-7 transition-transform group-hover:translate-x-1" aria-hidden />
      </Link>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {SECONDARY.map(({ to, Icon, title, body }) => (
          <Link key={to} to={to} className={`flex items-start gap-3 rounded-panel border bg-surface p-5 hover:border-brand ${to === `/check/${def}` ? 'border-brand ring-2 ring-brand/20' : 'border-line'}`}>
            <Icon className="mt-0.5 h-6 w-6 shrink-0 text-brand" aria-hidden />
            <div><p className="type-title text-xl">{title}{to === `/check/${def}` && <span className="ml-2 align-middle text-xs font-semibold text-brand">Your default</span>}</p><p className="mt-1 text-sm text-muted">{body}</p></div>
          </Link>
        ))}
      </div>
      <p className="mt-6 text-sm text-muted">Checking soap or shampoo instead? <Link to="/household" className="link">Try household labels (preview)</Link></p>
    </div>
  )
}
