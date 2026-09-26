import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import AuthShell from './AuthShell'
import { InlineError } from '../components/States'
import { useAuth } from '../context/AuthContext'

export default function Signup() {
  const { register } = useAuth()
  const nav = useNavigate()
  const [f, setF] = useState({ name: '', email: '', password: '', confirm_password: '' })
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!f.name.trim()) errs.name = 'Enter your name.'
    if (!/^\S+@\S+\.\S+$/.test(f.email)) errs.email = 'Enter a valid email address.'
    if (f.password.length < 8 || !/[A-Za-z]/.test(f.password) || !/\d/.test(f.password)) errs.password = 'Use at least 8 characters with a letter and a number.'
    if (f.confirm_password !== f.password) errs.confirm_password = "Passwords don't match."
    setErrors(errs)
    if (Object.keys(errs).length) return
    setBusy(true)
    try { await register({ ...f, name: f.name.trim(), email: f.email.trim() }); nav('/onboarding', { replace: true }) }
    catch (err) { setErrors({ form: err.message }) } finally { setBusy(false) }
  }
  const field = (k, label, type, auto) => (
    <div>
      <label className="label" htmlFor={k}>{label}</label>
      <input id={k} type={type} autoComplete={auto} className="field" value={f[k]} onChange={set(k)} aria-invalid={!!errors[k]} aria-describedby={k === 'password' ? 'pw-hint' : undefined} />
      {k === 'password' && !errors.password && <p id="pw-hint" className="mt-1 text-xs text-muted">At least 8 characters, with a letter and a number.</p>}
      <InlineError>{errors[k]}</InlineError>
    </div>
  )
  return (
    <AuthShell title="Create your account" subtitle="Next, you'll set up the food profile SafeBite checks against.">
      <form onSubmit={submit} noValidate className="space-y-4">
        {field('name', 'Name', 'text', 'name')}
        {field('email', 'Email', 'email', 'email')}
        {field('password', 'Password', 'password', 'new-password')}
        {field('confirm_password', 'Confirm password', 'password', 'new-password')}
        {errors.form && <div className="rounded-xl bg-high-soft p-3 text-sm font-medium text-high" role="alert">{errors.form}</div>}
        <button type="submit" className="btn-primary w-full" disabled={busy}>{busy ? 'Creating account…' : 'Create account'}</button>
      </form>
      <p className="mt-6 text-sm text-muted">Already have an account? <Link to="/login" className="link">Log in</Link></p>
    </AuthShell>
  )
}
