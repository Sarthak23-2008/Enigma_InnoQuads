import { Link } from 'react-router-dom'
import RiskBadge from './RiskBadge'
import { fmtNum, fmtTime, mealLabel, METHOD_LABEL } from '../utils/format'

export default function HistoryItem({ log }) {
  return (
    <Link to={`/history/${log.log_id}`} className="flex items-center gap-3 px-4 py-3 hover:bg-paper">
      <div className="min-w-0 flex-1">
        <p className="truncate font-semibold">{log.food_name}</p>
        <p className="text-sm text-muted">{mealLabel(log.meal_type)}, {fmtTime(log.consumed_at)}{log.quantity !== 1 ? `, ${log.quantity} servings` : ''} <span className="hidden sm:inline">· {METHOD_LABEL[log.input_method]}</span></p>
      </div>
      <span className="hidden text-sm tabular text-muted sm:block">{log.calories != null ? `${fmtNum(log.calories)} kcal` : ''}</span>
      {log.risk_level && <RiskBadge level={log.risk_level} size="sm" />}
    </Link>
  )
}
