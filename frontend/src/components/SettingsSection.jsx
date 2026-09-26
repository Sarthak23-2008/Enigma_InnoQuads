export default function SettingsSection({ title, description, children }) {
  return (
    <section className="panel p-5">
      <h2 className="type-title text-lg">{title}</h2>
      {description && <p className="mt-1 max-w-prose text-sm text-muted">{description}</p>}
      <div className="mt-4">{children}</div>
    </section>
  )
}

export function Toggle({ label, description, checked, onChange, disabled }) {
  const id = `t-${label.replace(/\W+/g, '-').toLowerCase()}`
  return (
    <div className="flex items-start justify-between gap-4 py-3">
      <div>
        <label htmlFor={id} className="font-semibold">{label}</label>
        {description && <p className="text-sm text-muted">{description}</p>}
      </div>
      <button id={id} role="switch" aria-checked={checked} disabled={disabled} onClick={() => onChange(!checked)}
        className={`relative mt-0.5 inline-flex h-7 w-12 shrink-0 items-center rounded-full border transition-colors ${checked ? 'border-brand bg-brand' : 'border-line bg-line'}`}>
        <span className={`inline-block h-5 w-5 rounded-full bg-white shadow transition-transform ${checked ? 'translate-x-6' : 'translate-x-1'}`} />
      </button>
    </div>
  )
}
