import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Download } from 'lucide-react'
import PageHeader from '../../components/PageHeader'
import SettingsSection from '../../components/SettingsSection'
import Modal from '../../components/Modal'
import { api } from '../../services/api'
import { useToast } from '../../context/ToastContext'

async function save(res, name) {
  const url = URL.createObjectURL(await res.blob())
  const a = Object.assign(document.createElement('a'), { href: url, download: name })
  a.click(); URL.revokeObjectURL(url)
}

export default function SettingsDietHistory() {
  const toast = useToast()
  const [open, setOpen] = useState(false)
  const [typed, setTyped] = useState('')
  const [busy, setBusy] = useState(false)
  const exp = async (fmt) => {
    try { await save(await api.exportLogs(fmt), `safebite-diet-history.${fmt}`) } catch (e) { toast(e.message, { tone: 'error' }) }
  }
  const clear = async () => {
    setBusy(true)
    try { const r = await api.clearLogs(); toast(`${r.message} ${r.deleted} entries removed.`); setOpen(false); setTyped('') }
    catch (e) { toast(e.message, { tone: 'error' }) } finally { setBusy(false) }
  }
  return (
    <div className="max-w-3xl space-y-5">
      <PageHeader title="Diet history" back={{ to: '/settings', label: 'Settings' }} />
      <SettingsSection title="View" description="Browse, filter and search everything you've logged."><Link to="/history" className="btn-secondary">Open history</Link></SettingsSection>
      <SettingsSection title="Export" description="Download your logs to keep or share with a dietitian.">
        <div className="flex flex-wrap gap-2">
          <button className="btn-secondary" onClick={() => exp('csv')}><Download className="h-4 w-4" aria-hidden />CSV (spreadsheet)</button>
          <button className="btn-secondary" onClick={() => exp('json')}><Download className="h-4 w-4" aria-hidden />JSON</button>
        </div>
      </SettingsSection>
      <SettingsSection title="Clear history" description="Removes every logged food and resets your trends. Your profile and account stay.">
        <button className="btn-danger" onClick={() => setOpen(true)}>Clear diet history</button>
      </SettingsSection>
      <Modal open={open} title="Clear all diet history?" onClose={() => setOpen(false)}
        footer={<><button className="btn-secondary" onClick={() => setOpen(false)}>Cancel</button><button className="btn-danger" disabled={typed !== 'CLEAR' || busy} onClick={clear}>Clear history</button></>}>
        <p>This can't be undone. Type <strong>CLEAR</strong> to confirm.</p>
        <label className="sr-only" htmlFor="clear-confirm">Type CLEAR</label>
        <input id="clear-confirm" className="field mt-3" value={typed} onChange={(e) => setTyped(e.target.value)} autoComplete="off" />
      </Modal>
    </div>
  )
}
