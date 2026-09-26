import Logo from '../components/Logo'

export default function AuthShell({ title, subtitle, children }) {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex h-16 max-w-page items-center px-4"><Logo /></header>
      <main id="main" className="t-fade mx-auto max-w-md px-4 pb-16 pt-6">
        <h1 className="type-display text-5xl">{title}</h1>
        {subtitle && <p className="mt-2 text-muted">{subtitle}</p>}
        <div className="mt-8">{children}</div>
      </main>
    </div>
  )
}
