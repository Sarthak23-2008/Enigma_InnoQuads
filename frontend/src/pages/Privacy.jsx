import { Link } from 'react-router-dom'
import Logo from '../components/Logo'

const SECTIONS = [
  ['What SafeBite stores', 'Your name, email and a hashed password; the food profile you enter (allergies, intolerances, diet, optional health considerations and goals); the foods you check; the foods you log with “I Ate This”; symptom check-ins you choose to answer; and your settings.'],
  ['Label photos', 'Photos are read to extract text and then discarded. SafeBite keeps only a fingerprint (hash) of the image, not the image itself, unless the server operator explicitly turns image storage on.'],
  ['Health information', 'Health considerations are optional and only used to flag sugar, sodium or potassium. SafeBite never infers or diagnoses a condition. Pattern insights describe your logs and are not medical advice.'],
  ['Your control', 'In Settings you can edit your profile, export all your data as JSON or your diet history as CSV, clear your diet history, and permanently delete your account and everything linked to it.'],
  ['Sharing', 'SafeBite does not sell or share your data. Scheduled reports go only to your own email address. The consultation directory contains sample listings; nothing is sent to them.'],
  ['Security', 'Passwords are hashed with bcrypt, sessions use signed tokens that are revoked when you log out, and each account can only read its own data.'],
]

export default function Privacy() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex h-16 max-w-3xl items-center px-4"><Logo /></header>
      <main id="main" className="mx-auto max-w-3xl px-4 pb-16 pt-4">
        <h1 className="type-display text-5xl">Privacy</h1>
        <p className="mt-3 text-muted">Plain-language summary of how SafeBite handles your data.</p>
        <div className="mt-8 space-y-6">
          {SECTIONS.map(([h, b]) => <section key={h} className="border-t-2 border-ink pt-3"><h2 className="type-title text-xl">{h}</h2><p className="mt-1 text-ink/85">{b}</p></section>)}
        </div>
        <p className="mt-10 text-sm text-muted">SafeBite gives dietary information, not medical advice. If you have a severe allergy, always read the physical label and follow your doctor's guidance.</p>
        <Link to="/" className="link mt-4 inline-block">Back to SafeBite</Link>
      </main>
    </div>
  )
}
