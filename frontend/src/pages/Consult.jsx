import { Mail, Stethoscope } from 'lucide-react'
import PageHeader from '../components/PageHeader'
import RiskMeter from '../components/RiskMeter'
import { ErrorState, LoadingState } from '../components/States'
import { api } from '../services/api'
import { useAsync } from '../hooks/useAsync'

export default function Consult() {
  const providers = useAsync(() => api.consultProviders(), [])
  const att = useAsync(() => api.attention(), [])
  return (
    <div className="space-y-6">
      <PageHeader title="Consult a professional" subtitle="A dietitian or doctor can interpret your patterns with your full health history. SafeBite doesn't diagnose." />
      {att.data && att.data.status !== 'insufficient' && <div className="max-w-xl"><RiskMeter attention={{ ...att.data, suggest_consult: false }} /></div>}
      <section>
        <h2 className="type-title text-xl">Directory</h2>
        <p className="mt-1 text-sm text-muted">These are sample listings for the demo. Contact details are placeholders and no bookings are made.</p>
        {providers.error ? <ErrorState error={providers.error} onRetry={providers.reload} /> : providers.loading ? <LoadingState /> : (
          <ul className="mt-4 grid gap-3 md:grid-cols-2">
            {providers.data.map((p) => (
              <li key={p.provider_id} className="panel p-4">
                <div className="flex items-start gap-3">
                  <Stethoscope className="mt-0.5 h-5 w-5 shrink-0 text-brand" aria-hidden />
                  <div className="min-w-0">
                    <p className="font-semibold">{p.name}</p>
                    <p className="text-sm text-muted">{p.specialty}</p>
                    <p className="mt-1 text-sm">{p.rate}{p.available ? '' : ', currently unavailable'}</p>
                    <p className="mt-2 inline-flex items-center gap-1.5 text-sm text-muted"><Mail className="h-4 w-4" aria-hidden />{p.contact}</p>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
