// Accessibility + input preferences, applied app-wide (text size, high contrast, voice assistance).
import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api } from '../services/api'
import { useAuth } from './AuthContext'

const PrefsCtx = createContext(null)
const LOCAL = 'sb_a11y'
const DEFAULTS = {
  accessibility: { text_size: 'normal', high_contrast: false, voice_assistance: false },
  input_prefs: { default_input_method: 'scan', ocr_language: 'eng', auto_log: false },
  notifications: {},
}

function readLocal() { try { return JSON.parse(localStorage.getItem(LOCAL)) || null } catch { return null } }

export function PrefsProvider({ children }) {
  const { status } = useAuth()
  const [prefs, setPrefs] = useState(() => ({ ...DEFAULTS, accessibility: { ...DEFAULTS.accessibility, ...(readLocal() || {}) } }))

  useEffect(() => {
    if (status !== 'authed') return
    api.settings().then((s) => setPrefs(s)).catch(() => {})
  }, [status])

  useEffect(() => {
    const a = prefs.accessibility || DEFAULTS.accessibility
    const html = document.documentElement
    html.dataset.text = a.text_size
    html.dataset.contrast = a.high_contrast ? 'high' : 'normal'
    try { localStorage.setItem(LOCAL, JSON.stringify(a)) } catch { /* ignore */ }
  }, [prefs.accessibility])

  const save = useCallback(async (section, values) => {
    setPrefs((p) => ({ ...p, [section]: { ...p[section], ...values } }))
    const next = await api.saveSettings({ [section]: values })
    setPrefs(next)
    return next
  }, [])

  return <PrefsCtx.Provider value={{ prefs, save, setPrefs }}>{children}</PrefsCtx.Provider>
}

export const usePrefs = () => useContext(PrefsCtx)
