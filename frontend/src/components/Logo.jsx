import { Link } from 'react-router-dom'

// Wordmark: a tiny "label" glyph (rules of a nutrition panel) + condensed name.
export default function Logo({ to = '/', className = '' }) {
  return (
    <Link to={to} className={`inline-flex items-center gap-2 ${className}`} aria-label="SafeBite home">
      <svg viewBox="0 0 32 32" className="h-8 w-8" aria-hidden>
        <rect width="32" height="32" rx="8" fill="rgb(var(--brand))" />
        <path d="M9 8h14v3H9zM9 13h14v2H9zM9 17h9v2H9zM9 21h11v3H9z" fill="#F5F7F6" />
      </svg>
      <span className="type-title text-[1.35rem]">SafeBite</span>
    </Link>
  )
}
