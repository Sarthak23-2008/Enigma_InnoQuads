import { useState } from 'react'
import PageHeader from '../../components/PageHeader'
import SettingsSection, { Toggle } from '../../components/SettingsSection'
import { api } from '../../services/api'
import { usePrefs } from '../../context/PrefsContext'
import { useToast } from '../../context/ToastContext'
import { useAsync } from '../../hooks/useAsync'
import { fmtDateTime } from '../../utils/format'

export default function SettingsNotifications() {
  const { prefs, save } = usePrefs()
  const toast = useToast()
  const n = prefs.notifications || {}
  const outbox = useAsync(() => api.outbox(), [])
  const [sending, setSending] = useState(false)
  const flip = (k) => async (v) => {
    try { await save('notifications', { [k]: v }); toast('Notification settings saved.') } catch (e) { toast(e.message, { tone: 'error' }) }
  }
  const test = async () => {
    setSending(true)
    try { await api.sendTestReport('weekly'); toast('Report generated. See it below.'); outbox.reload() }
    catch (e) { toast(e.message, { tone: 'error' }) } finally { setSending(false) }
  }
  return (
    <div className="max-w-3xl space-y-5">
      <PageHeader title="Notifications" back={{ to: '/settings', label: 'Settings' }} subtitle="Reports summarise the same patterns you see in Trends." />
      <SettingsSection title="Diet reports">
        <div className="divide-y divide-line">
          <Toggle label="Weekly report" description="Every 7 days, covering the last 15 days" checked={!!n.weekly_reports} onChange={flip('weekly_reports')} />
          <Toggle label="Bi-weekly report" description="Every 14 days" checked={!!n.biweekly_reports} onChange={flip('biweekly_reports')} />
          <Toggle label="Monthly report" description="Every 30 days, covering the last 30 days" checked={!!n.monthly_reports} onChange={flip('monthly_reports')} />
        </div>
      </SettingsSection>
      <SettingsSection title="Delivery">
        <div className="divide-y divide-line">
          <Toggle label="Email" description="Sent to your account email" checked={!!n.email_enabled} onChange={flip('email_enabled')} />
          <Toggle label="Push notifications" description="Coming with the mobile app" checked={!!n.push_enabled} onChange={flip('push_enabled')} />
        </div>
      </SettingsSection>
      <SettingsSection title="Recent reports" description="In this demo, reports are generated and stored here instead of being emailed.">
        <button className="btn-secondary" onClick={test} disabled={sending}>{sending ? 'Generating…' : 'Generate a report now'}</button>
        <ul className="mt-4 space-y-3">
          {(outbox.data || []).map((r) => (
            <li key={r.outbox_id} className="rounded-xl border border-line p-3">
              <details>
                <summary className="cursor-pointer text-sm"><span className="font-semibold">{r.subject}</span> <span className="text-muted">{fmtDateTime(r.created_at)}, {r.status.replace('_', ' ')}</span></summary>
                <pre className="mt-2 whitespace-pre-wrap font-sans text-sm text-ink/85">{r.body}</pre>
              </details>
            </li>
          ))}
          {outbox.data?.length === 0 && <li className="text-sm text-muted">No reports yet.</li>}
        </ul>
      </SettingsSection>
    </div>
  )
}
