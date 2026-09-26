import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import AuthShell from './AuthShell'
import { InlineError } from '../components/States'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login, demoLogin } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [busy, setBusy] = useState(false)
  const go = (u) => nav(u.onboarding_complete ? (loc.state?.from || '/') : '/onboarding', { replace: true })

  const submit = async (e) => {
    e.preventDefault()
    const errs = {}
    if (!/^\S+@\S+\.\S+$/.test(form.email)) errs.email = 'Enter a valid email address.'
    if (!form.password) errs.password = 'Enter your password.'
    setErrors(errs)
    if (Object.keys(errs).length) return
    setBusy(true)
    try { go(await login(form.email.trim(), form.password)) }
    catch (err) { setErrors({ form: err.message }) } finally { setBusy(false) }
  }
  const demo = async () => {
    setBusy(true)
    try { go(await demoLogin()) } catch (err) { setErrors({ form: err.message }) } finally { setBusy(false) }
  }
  useEffect(() => { if (loc.state?.demo) demo() }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <AuthShell title="Log in" subtitle="Welcome back. Your profile and history are waiting.">
      <form onSubmit={submit} noValidate className="space-y-4">
        <div>
          <label className="label" htmlFor="email">Email</label>
          <input id="email" type="email" autoComplete="email" className="field" value={form.email} aria-invalid={!!errors.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })} />
          <InlineError>{errors.email}</InlineError>
        </div>
        <div>
          <label className="label" htmlFor="password">Password</label>
          <input id="password" type="password" autoComplete="current-password" className="field" value={form.password} aria-invalid={!!errors.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })} />
          <InlineError>{errors.password}</InlineError>
        </div>
        {errors.form && <div className="rounded-xl bg-high-soft p-3 text-sm font-medium text-high" role="alert">{errors.form}</div>}
        <button type="submit" className="btn-primary w-full" disabled={busy}>{busy ? 'Logging in…' : 'Log in'}</button>
      </form>
      <div className="mt-6 rounded-panel border border-line bg-surface p-4">
        <p className="text-sm font-semibold">Trying SafeBite for a hackathon demo?</p>
        <p className="text-sm text-muted">Open Aryan's sample account with 30 days of meals already logged.</p>
        <button onClick={demo} className="btn-secondary mt-3 w-full" disabled={busy}>Use the demo account</button>
      </div>
      <p className="mt-6 text-sm text-muted">New to SafeBite? <Link to="/signup" className="link">Create an account</Link></p>
    </AuthShell>
  )
}
