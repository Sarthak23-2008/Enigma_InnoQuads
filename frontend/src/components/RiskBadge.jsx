import { ShieldCheck, TriangleAlert, OctagonAlert } from 'lucide-react'

export const RISK = {
  LOW: { label: 'Low risk', word: 'LOW', Icon: ShieldCheck, text: 'text-low', bg: 'bg-low-soft', border: 'border-low', soft: 'border-low/40', solid: 'bg-low' },
  CAUTION: { label: 'Caution', word: 'CAUTION', Icon: TriangleAlert, text: 'text-caution', bg: 'bg-caution-soft', border: 'border-caution', soft: 'border-caution/40', solid: 'bg-caution' },
  HIGH: { label: 'High risk', word: 'HIGH', Icon: OctagonAlert, text: 'text-high', bg: 'bg-high-soft', border: 'border-high', soft: 'border-high/40', solid: 'bg-high' },
}

export default function RiskBadge({ level, size = 'md' }) {
  const r = RISK[level] || RISK.LOW
  const cls = size === 'sm' ? 'px-2 py-0.5 text-xs gap-1' : 'px-2.5 py-1 text-sm gap-1.5'
  return (
    <span className={`inline-flex shrink-0 items-center rounded-full border font-semibold ${cls} ${r.bg} ${r.text} ${r.soft}`}>
      <r.Icon className={size === 'sm' ? 'h-3.5 w-3.5' : 'h-4 w-4'} aria-hidden />
      {r.label}
    </span>
  )
}
