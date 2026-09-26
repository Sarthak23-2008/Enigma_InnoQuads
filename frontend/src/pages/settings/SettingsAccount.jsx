import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Download } from 'lucide-react'
import PageHeader from '../../components/PageHeader'
import SettingsSection from '../../components/SettingsSection'
import Modal from '../../components/Modal'
import { InlineError } from '../../components/States'
import { api, tokenStore } from '../../services/api'
import { useAuth } from '../../context/AuthContext'
import { useToast } from '../../context/ToastContext'

export default function SettingsAccount() {
  const { user, setUser, refresh } = useAuth()
  const toast = useToast()
  const nav = useNavigate()
  const [name, setName] = useState(user.name)
  const [email, setEmail] = useState(user.email)
  const [pw, setPw] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const [del, setDel] = useState({ open: false, password: '', text: '', err: '' })
  const emailChanged = email.trim().toLowerCase() !== user.email

  const saveAccount = async (e) => {
    e.preventDefault()
    if (!name.trim()) return setErr('Enter your name.')
    setBusy(true); setErr('')
    try {
      const u = await api.updateAccount({ name: name.trim(), ...(emailChanged ? { email: email.trim(), current_password: pw } : {}) })
      setUser(u); setPw(''); toast('Account details saved.')
    } catch (x) { setErr(x.message) } finally { setBusy(false) }
  }
  const exportAll = async () => {
    try {
      const data = await api.exportAccount()
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' }))
      Object.assign(document.createElement('a'), { href: url, download: 'safebite-account-export.json' }).click()
      URL.revokeObjectURL(url)
    } catch (x) { toast(x.message, { tone: 'error' }) }
  }
  const deleteAccount = async () => {
    setBusy(true)
    try { await api.deleteAccount({ password: del.password, confirm_text: del.text }); tokenStore.clear(); await refresh(); toast('Your account was deleted.'); nav('/', { replace: true }) }
    catch (x) { setDel((d) => ({ ...d, err: x.message })) } finally { setBusy(false) }
  }
  return (
    <div className="max-w-3xl space-y-5">
      <PageHeader title="Account" back={{ to: '/settings', label: 'Settings' }} />
      <SettingsSection title="Details">
        <form onSubmit={saveAccount} className="max-w-md space-y-3" noValidate>
          <div><label className="label" htmlFor="a-name">Name</label><input id="a-name" className="field" value={name} maxLength={120} onChange={(e) => setName(e.target.value)} /></div>
          <div><label className="label" htmlFor="a-email">Email</label><input id="a-email" type="email" className="field" value={email} disabled={user.is_demo} onChange={(e) => setEmail(e.target.value)} /></div>
          {emailChanged && <div><label className="label" htmlFor="a-pw">Current password</label><input id="a-pw" type="password" className="field" value={pw} onChange={(e) => setPw(e.target.value)} autoComplete="current-password" /></div>}
          <InlineError>{err}</InlineError>
          <button className="btn-primary" disabled={busy}>Save details</button>
        </form>
      </SettingsSection>
      <SettingsSection title="Your data" description="Download everything SafeBite stores about you as a JSON file.">
        <button className="btn-secondary" onClick={exportAll}><Download className="h-4 w-4" aria-hidden />Export all data</button>
      </SettingsSection>
      <SettingsSection title="Delete account" description="Permanently deletes your account, profile, history, trends and check-ins.">
        {user.is_demo ? <p className="text-sm text-muted">The shared demo account can't be deleted.</p>
          : <button className="btn-danger" onClick={() => setDel({ open: true, password: '', text: '', err: '' })}>Delete account</button>}
      </SettingsSection>
      <Modal open={del.open} title="Delete your account?" onClose={() => setDel((d) => ({ ...d, open: false }))}
        footer={<><button className="btn-secondary" onClick={() => setDel((d) => ({ ...d, open: false }))}>Cancel</button>
          <button className="btn-danger" disabled={busy || del.text !== 'DELETE' || !del.password} onClick={deleteAccount}>Delete permanently</button></>}>
        <p>This can't be undone. Enter your password and type <strong>DELETE</strong>.</p>
        <label className="label mt-3" htmlFor="d-pw">Password</label>
        <input id="d-pw" type="password" className="field" value={del.password} onChange={(e) => setDel((d) => ({ ...d, password: e.target.value }))} />
        <label className="label mt-3" htmlFor="d-text">Type DELETE</label>
        <input id="d-text" className="field" value={del.text} autoComplete="off" onChange={(e) => setDel((d) => ({ ...d, text: e.target.value }))} />
        <InlineError>{del.err}</InlineError>
      </Modal>
    </div>
  )
}
