import { useEffect, useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import OCRUploader from '../components/OCRUploader'
import OCRReview from '../components/OCRReview'
import { ErrorState } from '../components/States'
import { api } from '../services/api'
import { usePrefs } from '../context/PrefsContext'

// Steps: upload -> reading (OCR) -> review (editable) -> analyze -> /result/:id
export default function Scan() {
  const nav = useNavigate()
  const { prefs } = usePrefs()
  const [step, setStep] = useState('upload')
  const [img, setImg] = useState(null)
  const [ocr, setOcr] = useState(null)
  const [err, setErr] = useState(null)
  const [busy, setBusy] = useState(false)
  useEffect(() => () => img && URL.revokeObjectURL(img), [img])

  const read = async (file) => {
    setErr(null); setImg(URL.createObjectURL(file)); setStep('reading')
    try { setOcr(await api.ocr(file, prefs.input_prefs?.ocr_language || 'eng')); setStep('review') }
    catch (e) { setErr(e); setStep('upload') }
  }
  const analyze = async (reviewed) => {
    setBusy(true)
    try {
      const r = await api.analyze({ input_method: 'scan', ...reviewed, ocr_scan_token: ocr.scan_token, raw_ocr_text: ocr.raw_text, ocr_confidence: ocr.confidence })
      nav(`/result/${r.scan_id}`, { state: { fresh: true } })
    } catch (e) { setErr(e); setBusy(false) }
  }

  return (
    <div>
      <PageHeader title={step === 'review' ? 'Review the label' : 'Scan food label'} back={{ to: '/check', label: 'Check a food' }}
        subtitle={step === 'review' ? 'Correct anything the camera misread, then analyze.' : undefined} />
      {err && (
        <div className="mb-4">
          <ErrorState title="We couldn't read this label clearly" error={err.message} />
          <p className="mt-2 text-sm">Try another photo, or <Link to="/check/manual" className="link">enter the ingredients manually</Link>.</p>
        </div>
      )}
      {step === 'upload' && <OCRUploader onFile={read} />}
      {step === 'reading' && (
        <div className="grid items-center gap-6 md:grid-cols-2" role="status" aria-live="polite">
          <div className="relative overflow-hidden rounded-panel border border-line bg-surface">
            {img && <img src={img} alt="Label being read" className="max-h-96 w-full object-contain opacity-80" />}
            <div className="pointer-events-none absolute inset-0 motion-safe:animate-[sb-scanline_1.6s_linear_infinite] bg-gradient-to-b from-transparent via-brand/25 to-transparent" aria-hidden />
          </div>
          <div>
            <p className="type-title text-2xl">Reading the label…</p>
            <p className="mt-2 text-muted">Finding the ingredient list, allergen statement and nutrition values. This usually takes a few seconds.</p>
          </div>
        </div>
      )}
      {step === 'review' && ocr && <OCRReview ocr={ocr} imageUrl={img} busy={busy} onAnalyze={analyze} onRetake={() => { setOcr(null); setStep('upload') }} />}
    </div>
  )
}
