import PageHeader from '../../components/PageHeader'
import SettingsSection, { Toggle } from '../../components/SettingsSection'
import { usePrefs } from '../../context/PrefsContext'
import { useToast } from '../../context/ToastContext'

export default function SettingsInputPrefs() {
  const { prefs, save } = usePrefs()
  const toast = useToast()
  const ip = prefs.input_prefs || {}
  const set = async (v) => { try { await save('input_prefs', v); toast('Input preferences saved.') } catch (e) { toast(e.message, { tone: 'error' }) } }
  return (
    <div className="max-w-3xl space-y-5">
      <PageHeader title="Input preferences" back={{ to: '/settings', label: 'Settings' }} />
      <SettingsSection title="Default check method" description="Which option the Check button highlights first.">
        <label className="sr-only" htmlFor="dim">Default method</label>
        <select id="dim" className="field max-w-xs" value={ip.default_input_method || 'scan'} onChange={(e) => set({ default_input_method: e.target.value })}>
          <option value="scan">Scan food label</option><option value="search">Search food</option><option value="manual">Enter manually</option>
        </select>
      </SettingsSection>
      <SettingsSection title="Label language" description="Language used when reading label photos.">
        <label className="sr-only" htmlFor="ocrl">Label language</label>
        <select id="ocrl" className="field max-w-xs" value={ip.ocr_language || 'eng'} onChange={(e) => set({ ocr_language: e.target.value })}>
          <option value="eng">English</option><option value="hin">Hindi</option><option value="eng+hin">English + Hindi</option>
        </select>
      </SettingsSection>
      <SettingsSection title="Logging">
        <Toggle label="Log automatically after a check" description="Adds the food to your history as soon as it's analysed. Leave off if you often check foods you don't eat." checked={!!ip.auto_log} onChange={(v) => set({ auto_log: v })} />
      </SettingsSection>
    </div>
  )
}
