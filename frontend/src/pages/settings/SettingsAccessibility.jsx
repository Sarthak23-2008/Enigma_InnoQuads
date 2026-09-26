import PageHeader from '../../components/PageHeader'
import SettingsSection, { Toggle } from '../../components/SettingsSection'
import { usePrefs } from '../../context/PrefsContext'
import { useToast } from '../../context/ToastContext'
import { canListen, canSpeak } from '../../hooks/useSpeech'

const SIZES = [{ v: 'normal', l: 'Default' }, { v: 'large', l: 'Large' }, { v: 'xlarge', l: 'Extra large' }]

export default function SettingsAccessibility() {
  const { prefs, save } = usePrefs()
  const toast = useToast()
  const a = prefs.accessibility || {}
  const set = async (v) => { try { await save('accessibility', v) } catch (e) { toast(e.message, { tone: 'error' }) } }
  return (
    <div className="max-w-3xl space-y-5">
      <PageHeader title="Accessibility" back={{ to: '/settings', label: 'Settings' }} />
      <SettingsSection title="Text size">
        <div role="radiogroup" aria-label="Text size" className="inline-flex rounded-xl border border-line bg-paper p-1">
          {SIZES.map((s) => (
            <button key={s.v} role="radio" aria-checked={a.text_size === s.v} onClick={() => set({ text_size: s.v })}
              className={`rounded-lg px-4 py-2 font-semibold ${a.text_size === s.v ? 'bg-surface shadow-sm ring-1 ring-line' : 'text-muted'}`}>{s.l}</button>
          ))}
        </div>
      </SettingsSection>
      <SettingsSection title="Display">
        <Toggle label="High contrast" description="Stronger text and borders." checked={!!a.high_contrast} onChange={(v) => set({ high_contrast: v })} />
      </SettingsSection>
      <SettingsSection title="Voice assistance" description={canListen || canSpeak ? 'Adds a microphone to the top bar. Say “search dal”, “scan”, or “is this safe for me” on a result. Results are also read aloud after each check.' : 'Your browser does not support voice input or speech. Try Chrome or Edge.'}>
        <Toggle label="Voice assistance" checked={!!a.voice_assistance} disabled={!canListen && !canSpeak} onChange={(v) => set({ voice_assistance: v })} />
      </SettingsSection>
    </div>
  )
}
