import { useRef, useState } from 'react'
import { Camera, ImageUp, FileImage } from 'lucide-react'

const OK_TYPES = ['image/jpeg', 'image/png', 'image/webp']
export const SAMPLES = [
  { file: 'chococrunch_biscuits.jpg', label: 'ChocoCrunch biscuits' },
  { file: 'masala_noodles.jpg', label: 'Masala noodles' },
  { file: 'roasted_makhana.jpg', label: 'Roasted makhana' },
]

export default function OCRUploader({ onFile, maxMb = 8, disabled }) {
  const input = useRef(null)
  const camera = useRef(null)
  const [drag, setDrag] = useState(false)
  const [err, setErr] = useState('')

  const accept = (f) => {
    if (!f) return
    if (!OK_TYPES.includes(f.type)) { setErr('Use a JPEG, PNG or WEBP photo of the label.'); return }
    if (f.size > maxMb * 1024 * 1024) { setErr(`That image is over ${maxMb} MB. Try a smaller photo.`); return }
    setErr(''); onFile(f)
  }
  const useSample = async (s) => {
    const res = await fetch(`/samples/${s.file}`)
    const blob = await res.blob()
    accept(new File([blob], s.file, { type: 'image/jpeg' }))
  }

  return (
    <div>
      <div
        onDragOver={(e) => { e.preventDefault(); setDrag(true) }} onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); accept(e.dataTransfer.files?.[0]) }}
        className={`flex flex-col items-center gap-4 rounded-panel border-2 border-dashed px-6 py-10 text-center ${drag ? 'border-brand bg-brand-soft' : 'border-line bg-surface'}`}>
        <FileImage className="h-10 w-10 text-brand" aria-hidden />
        <div>
          <p className="type-title text-xl">Photograph the ingredients and nutrition panel</p>
          <p className="mt-1 text-sm text-muted">Flat, well lit and in focus works best. JPEG, PNG or WEBP up to {maxMb} MB.</p>
        </div>
        <div className="flex flex-wrap justify-center gap-2">
          <button type="button" className="btn-primary" disabled={disabled} onClick={() => camera.current?.click()}><Camera className="h-5 w-5" aria-hidden />Take photo</button>
          <button type="button" className="btn-secondary" disabled={disabled} onClick={() => input.current?.click()}><ImageUp className="h-5 w-5" aria-hidden />Upload image</button>
        </div>
        <input ref={camera} type="file" accept="image/*" capture="environment" className="sr-only" tabIndex={-1} aria-hidden onChange={(e) => { accept(e.target.files?.[0]); e.target.value = '' }} />
        <input ref={input} type="file" accept="image/jpeg,image/png,image/webp" className="sr-only" tabIndex={-1} aria-hidden onChange={(e) => { accept(e.target.files?.[0]); e.target.value = '' }} />
      </div>
      {err && <p className="mt-2 text-sm font-medium text-high" role="alert">{err}</p>}
      <div className="mt-4">
        <p className="text-sm font-semibold">No label handy? Use a sample label</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {SAMPLES.map((s) => (
            <button key={s.file} type="button" disabled={disabled} onClick={() => useSample(s)} className="chip border-line bg-surface hover:border-brand hover:text-brand">
              {s.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
