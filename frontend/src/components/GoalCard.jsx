import { TrendingDown, TrendingUp, Minus, Target } from 'lucide-react'
import { fmtNum, GOAL_LABEL } from '../utils/format'

export default function GoalCard({ g }) {
  const d = g.trend?.direction
  const Icon = d === 'down' ? TrendingDown : d === 'up' ? TrendingUp : d === 'stable' ? Minus : Target
  const tone = g.on_track === true ? 'text-low' : g.on_track === false ? 'text-caution' : 'text-muted'
  return (
    <div className="panel flex items-start gap-3 p-4">
      <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${tone}`} aria-hidden />
      <div>
        <p className="text-sm font-semibold text-muted">Goal: {GOAL_LABEL[g.goal] || g.label}</p>
        <p className="font-semibold">{g.statement}</p>
        <p className="mt-1 text-sm text-muted tabular">Now {fmtNum(g.current, 1)} {g.unit}{g.trend ? `, previously ${fmtNum(g.trend.previous_value, 1)}` : ''}{g.on_track === true ? ' — heading the right way' : g.on_track === false ? ' — not yet moving toward your goal' : ''}</p>
      </div>
    </div>
  )
}
