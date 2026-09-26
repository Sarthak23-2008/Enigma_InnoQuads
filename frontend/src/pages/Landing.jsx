import { Link } from 'react-router-dom'
import { ScanLine, ListChecks, LineChart, OctagonAlert, TriangleAlert } from 'lucide-react'
import Logo from '../components/Logo'

// The hero shows the product doing its one job: a real-looking ingredients panel with the
// words that matter to one person flagged, and the verdict beside it.
function LabelSpecimen() {
  const hi = 'rounded bg-high-soft px-1 font-semibold text-high ring-1 ring-high/40'
  const ca = 'rounded bg-caution-soft px-1 font-semibold text-caution ring-1 ring-caution/40'
  return (
    <div className="relative mx-auto w-full max-w-md">
      <div className="panel rotate-[-1.2deg] p-5 shadow-lift">
        <p className="type-title text-lg">ChocoCrunch Biscuits</p>
        <div className="rule-heavy mt-2" />
        <p className="pt-2 text-[0.95rem] leading-7">
          <strong>Ingredients:</strong> Wheat flour, <span className={ca}>Milk solids</span>, Sugar, Cocoa, <span className={hi}>Peanut traces</span>, Soy lecithin.
        </p>
        <div className="rule-thin mt-2" />
        <dl className="tabular text-sm">
          {[['Energy', '144 kcal'], ['Total sugars', '9 g'], ['Sodium', '120 mg']].map(([k, v]) => (
            <div key={k} className="flex justify-between border-b border-ink/15 py-1"><dt>{k}</dt><dd className="font-semibold">{v}</dd></div>
          ))}
        </dl>
        <div className="rule-mid" />
      </div>
      <div className="panel relative -mt-6 ml-auto w-[85%] rotate-[1deg] border-2 border-high bg-surface p-4 shadow-lift">
        <p className="text-xs font-semibold text-muted">For Aryan: peanut allergy, lactose intolerant</p>
        <p className="type-display mt-1 flex items-center gap-2 text-4xl text-high"><OctagonAlert className="h-8 w-8" aria-hidden />HIGH</p>
        <p className="mt-2 text-sm">Peanut traces were detected and match your peanut allergy profile.</p>
        <p className="mt-1 flex items-start gap-1.5 text-sm"><TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-caution" aria-hidden />Milk solids may conflict with your lactose intolerance.</p>
      </div>
    </div>
  )
}

const STEPS = [
  { Icon: ScanLine, title: 'Scan', body: 'Photograph the ingredients panel, search a dish, or type what you ate.' },
  { Icon: ListChecks, title: 'Understand', body: 'SafeBite matches every ingredient, including hidden names like arachis or casein, against your allergies, intolerances and diet.' },
  { Icon: LineChart, title: 'Track', body: 'Log what you actually eat and see 15- and 30-day patterns in sodium, sugar, fiber and more.' },
]

export default function Landing() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex h-16 max-w-page items-center justify-between px-4">
        <Logo />
        <nav className="flex items-center gap-2" aria-label="Account">
          <Link to="/login" className="btn-ghost">Log in</Link>
          <Link to="/signup" className="btn-secondary hidden sm:inline-flex">Sign up</Link>
        </nav>
      </header>

      <main id="main">
        <section className="mx-auto grid max-w-page items-center gap-12 px-4 pb-16 pt-8 lg:grid-cols-[1.1fr_1fr] lg:pt-16">
          <div>
            <h1 className="type-display text-[3.2rem] sm:text-7xl">Know What's In Your Food. Know What It Means For You.</h1>
            <p className="mt-6 max-w-xl text-lg text-ink/80">
              “Sugar-free” biscuits with maltitol and maida. Peanut traces in a spice mix. Sodium in a salad.
              SafeBite reads the label and tells you what it means for your allergies, intolerances and diet.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link to="/signup" className="btn-primary px-6 text-base"><ScanLine className="h-5 w-5" aria-hidden />Check Your Food</Link>
              <a href="#how" className="btn-secondary px-6 text-base">How It Works</a>
            </div>
            <p className="mt-4 text-sm text-muted">Want to look around first? <Link to="/login" state={{ demo: true }} className="link">Open the demo account</Link></p>
          </div>
          <LabelSpecimen />
        </section>

        <section id="how" className="border-y border-line bg-surface">
          <div className="mx-auto max-w-page px-4 py-16">
            <h2 className="type-display text-4xl">How it works</h2>
            <ol className="mt-8 grid gap-8 md:grid-cols-3">
              {STEPS.map(({ Icon, title, body }, i) => (
                <li key={title} className="border-t-4 border-ink pt-4">
                  <p className="flex items-center gap-2 text-sm font-bold text-muted"><span className="tabular">{i + 1}</span><Icon className="h-4 w-4" aria-hidden /></p>
                  <h3 className="type-title mt-2 text-2xl">{title}</h3>
                  <p className="mt-2 text-ink/80">{body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="mx-auto grid max-w-page gap-10 px-4 py-16 md:grid-cols-2">
          <div>
            <h2 className="type-title text-3xl">Built for everyday food decisions</h2>
            <p className="mt-3 text-ink/80">A packet in a shop, a thali at home, a dish at a restaurant. Each result shows what was flagged, why, and how sure SafeBite is.</p>
          </div>
          <ul className="space-y-3 text-ink/90">
            {['Three clear levels: Low, Caution, High, always with a reason', 'Recognises Indian ingredient names, INS codes and hidden sugars',
              'You review what the camera read before anything is analysed', 'Suggests alternatives that are re-checked against your profile',
              'Pattern alerts, never diagnoses'].map((t) => (
              <li key={t} className="flex gap-3 border-b border-line pb-3"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-brand" aria-hidden />{t}</li>
            ))}
          </ul>
        </section>
      </main>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-page flex-wrap items-center justify-between gap-3 px-4 py-6 text-sm text-muted">
          <p>SafeBite gives dietary information, not medical advice.</p>
          <Link to="/privacy" className="link">Privacy</Link>
        </div>
      </footer>
    </div>
  )
}
