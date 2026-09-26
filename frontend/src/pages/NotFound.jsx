import { Link } from 'react-router-dom'
import Logo from '../components/Logo'

export default function NotFound() {
  return (
    <div className="mx-auto max-w-md px-4 py-10">
      <Logo />
      <h1 className="type-display mt-10 text-6xl">Page not found</h1>
      <p className="mt-3 text-muted">The link may be old or mistyped.</p>
      <Link to="/" className="btn-primary mt-6">Go to SafeBite home</Link>
    </div>
  )
}
