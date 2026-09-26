import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { Mic, MicOff } from 'lucide-react'
import { canListen, useListen } from '../hooks/useSpeech'
import { useToast } from '../context/ToastContext'

// Persistent mic (shown when Voice assistance is on). Simple commands:
// "scan" / "search <food>" / "history" / "trends" / "settings" / "is this safe for me" (reads the result aloud).
export default function VoiceButton({ compact }) {
  const navigate = useNavigate()
  const toast = useToast()
  const onResult = useCallback((text) => {
    const t = text.toLowerCase().trim()
    if (/\b(scan|camera|label)\b/.test(t)) return navigate('/check/scan')
    if (/\bhistory\b/.test(t)) return navigate('/history')
    if (/\b(trend|pattern)s?\b/.test(t)) return navigate('/trends')
    if (/\bsettings?\b/.test(t)) return navigate('/settings')
    if (/(safe for me|read (the )?result|is this safe)/.test(t)) return window.dispatchEvent(new Event('sb:read-result'))
    const q = t.replace(/^(search( for)?|check|find|look up)\s+/, '')
    toast(`Searching for “${q}”`)
    navigate(`/check/search?q=${encodeURIComponent(q)}`)
  }, [navigate, toast])
  const { start, stop, listening, error } = useListen(onResult)
  if (!canListen) return null
  if (error) setTimeout(() => toast(error, { tone: 'error' }), 0)
  return (
    <button
      type="button"
      onClick={listening ? stop : start}
      aria-pressed={listening}
      aria-label={listening ? 'Stop voice input' : 'Voice input: say “search dal” or “is this safe for me”'}
      className={`inline-flex h-11 w-11 items-center justify-center rounded-full border ${listening ? 'animate-pulse border-high bg-high text-white' : 'border-line bg-surface text-brand hover:border-brand'} ${compact ? '' : ''}`}
    >
      {listening ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5" />}
    </button>
  )
}
