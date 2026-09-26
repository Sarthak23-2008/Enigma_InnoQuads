// Web Speech API wrappers. Everything degrades gracefully when the browser lacks support.
import { useCallback, useEffect, useRef, useState } from 'react'

export const canSpeak = typeof window !== 'undefined' && 'speechSynthesis' in window
const Recognition = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)
export const canListen = Boolean(Recognition)

export function useSpeak() {
  const [speaking, setSpeaking] = useState(false)
  const speak = useCallback((text) => {
    if (!canSpeak || !text) return
    window.speechSynthesis.cancel()
    const u = new SpeechSynthesisUtterance(text)
    u.rate = 0.98
    u.onend = () => setSpeaking(false)
    u.onerror = () => setSpeaking(false)
    setSpeaking(true)
    window.speechSynthesis.speak(u)
  }, [])
  const stop = useCallback(() => { if (canSpeak) window.speechSynthesis.cancel(); setSpeaking(false) }, [])
  useEffect(() => () => { if (canSpeak) window.speechSynthesis.cancel() }, [])
  return { speak, stop, speaking }
}

export function useListen(onResult) {
  const [listening, setListening] = useState(false)
  const [error, setError] = useState(null)
  const rec = useRef(null)
  const start = useCallback(() => {
    if (!Recognition) { setError('Voice input is not supported in this browser.'); return }
    setError(null)
    const r = new Recognition()
    r.lang = 'en-IN'
    r.interimResults = false
    r.maxAlternatives = 1
    r.onresult = (e) => onResult(e.results[0][0].transcript)
    r.onerror = (e) => setError(e.error === 'not-allowed' ? 'Microphone permission was denied.' : 'Voice input stopped. Try again.')
    r.onend = () => setListening(false)
    rec.current = r
    setListening(true)
    r.start()
  }, [onResult])
  const stop = useCallback(() => { rec.current?.stop(); setListening(false) }, [])
  return { start, stop, listening, error }
}
