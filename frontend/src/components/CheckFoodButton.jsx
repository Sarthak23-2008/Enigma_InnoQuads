import { Link } from 'react-router-dom'
import { ScanLine } from 'lucide-react'

export default function CheckFoodButton({ className = '', label = 'Check Food' }) {
  return (
    <Link to="/check" className={`btn-primary ${className}`}>
      <ScanLine className="h-5 w-5" aria-hidden />{label}
    </Link>
  )
}
