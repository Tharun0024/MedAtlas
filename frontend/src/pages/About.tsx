import { CheckCircle2, Shield, Clock, FileCheck, ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function About() {
  const navigate = useNavigate()

  const goToDashboard = () => navigate('/dashboard')
  const goToProviders = () => navigate('/providers')

  return (
    <div className="bg-slate-950">
      {/* HERO */}
      <section className="px-12 py-16 border-b border-slate-800">
        <div className="max-w-4xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-600/10 border border-blue-600/20 rounded-full text-blue-400 text-sm font-medium mb-6">
            <Shield size={14} />
            <span>Healthcare Provider Validation</span>
          </div>
          <h1 className="text-5xl font-bold text-white mb-6 leading-tight">
            Validate provider data.<br />
            Ensure compliance.<br />
            Stay audit-ready.
          </h1>
          <p className="text-xl text-slate-400 mb-8 max-w-2xl">
            MedAtlas automates healthcare provider data validation, helping operations teams
            maintain accurate records and meet regulatory requirements without manual overhead.
          </p>
          <div className="flex gap-4">
            <button
              onClick={goToDashboard}
              className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
            >
              Go to Dashboard
              <ArrowRight size={18} />
            </button>
            <button
              onClick={goToProviders}
              className="inline-flex items-center gap-2 px-6 py-3 bg-slate-900 border border-slate-700 hover:bg-slate-800 text-slate-100 font-medium rounded-lg transition-colors"
            >
              View Providers
            </button>
          </div>
        </div>
      </section>

      {/* WHY MEDATLAS */}
      <section className="px-12 py-16 border-b border-slate-800">
        <div className="max-w-4xl">
          <h2 className="text-3xl font-bold text-white mb-4">Why MedAtlas?</h2>
          <p className="text-lg text-slate-400 mb-10">
            Healthcare organizations face constant pressure to maintain accurate provider data
            for compliance, credentialing, and operational efficiency. Manual validation is
            time-consuming, error-prone, and doesn't scale.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
              <div className="w-12 h-12 bg-blue-600/10 rounded-lg flex items-center justify-center mb-4">
                <Clock size={24} className="text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Save Time</h3>
              <p className="text-slate-400 text-sm">
                Automate hours of manual validation work. Get results in minutes, not days.
              </p>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
              <div className="w-12 h-12 bg-blue-600/10 rounded-lg flex items-center justify-center mb-4">
                <CheckCircle2 size={24} className="text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Increase Accuracy</h3>
              <p className="text-slate-400 text-sm">
                Reduce human error with systematic validation rules and confidence scoring.
              </p>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
              <div className="w-12 h-12 bg-blue-600/10 rounded-lg flex items-center justify-center mb-4">
                <Shield size={24} className="text-blue-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">Stay Compliant</h3>
              <p className="text-slate-400 text-sm">
                Maintain audit trails and documentation for regulatory requirements.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* WHAT YOU GET */}
      <section className="px-12 py-16 border-b border-slate-800">
        <div className="max-w-4xl">
          <h2 className="text-3xl font-bold text-white mb-4">What you get out-of-the-box</h2>
          <p className="text-lg text-slate-400 mb-10">
            MedAtlas includes everything you need to validate and manage provider data.
          </p>

          <div className="space-y-4">
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 flex items-start gap-4">
              <div className="w-8 h-8 bg-green-600/10 rounded flex items-center justify-center flex-shrink-0 mt-1">
                <CheckCircle2 size={18} className="text-green-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  Automated Validation Pipeline
                </h3>
                <p className="text-slate-400">
                  Multi-stage validation using specialized agents that check credentials, licenses,
                  and eligibility against authoritative sources.
                </p>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 flex items-start gap-4">
              <div className="w-8 h-8 bg-green-600/10 rounded flex items-center justify-center flex-shrink-0 mt-1">
                <CheckCircle2 size={18} className="text-green-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  Discrepancy Detection &amp; Tracking
                </h3>
                <p className="text-slate-400">
                  Automatically identify data issues, conflicts, and anomalies. Track resolution
                  status and maintain audit trails.
                </p>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 flex items-start gap-4">
              <div className="w-8 h-8 bg-green-600/10 rounded flex items-center justify-center flex-shrink-0 mt-1">
                <CheckCircle2 size={18} className="text-green-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Confidence Scoring</h3>
                <p className="text-slate-400">
                  Every validation includes a confidence score, helping you prioritize manual
                  review for edge cases.
                </p>
              </div>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 flex items-start gap-4">
              <div className="w-8 h-8 bg-green-600/10 rounded flex items-center justify-center flex-shrink-0 mt-1">
                <CheckCircle2 size={18} className="text-green-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">Export &amp; Reporting</h3>
                <p className="text-slate-400">
                  Export validation results in CSV or JSON format for downstream systems,
                  reporting, and compliance documentation.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FLOW */}
      <section className="px-12 py-16 border-b border-slate-800">
        <div className="max-w-4xl">
          <h2 className="text-3xl font-bold text-white mb-4">How MedAtlas fits into your day</h2>
          <p className="text-lg text-slate-400 mb-10">
            Designed for healthcare operations teams who need accurate data without disrupting workflows.
          </p>

          <div className="space-y-6">
            {[1, 2, 3, 4].map((step) => {
              const titles = [
                'Upload provider data',
                'Automated validation runs',
                'Review and resolve',
                'Export and document',
              ]
              const descriptions = [
                'Import provider records from your existing systems via CSV or API integration.',
                'The validation pipeline processes records in the background, checking credentials and identifying discrepancies.',
                'Check the dashboard for pending validations and open discrepancies. Address issues flagged for manual review.',
                'Generate reports for compliance audits, credentialing committees, or downstream systems integration.',
              ]
              return (
                <div key={step} className="flex items-start gap-4">
                  <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0 font-bold text-white">
                    {step}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-2">
                      {titles[step - 1]}
                    </h3>
                    <p className="text-slate-400">{descriptions[step - 1]}</p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* FINAL CTA */}
      <section className="px-12 py-16">
        <div className="max-w-4xl">
          <div className="bg-gradient-to-br from-blue-600/10 to-slate-900 border border-blue-600/20 rounded-xl p-10">
            <div className="flex items-center gap-3 mb-4">
              <FileCheck size={32} className="text-blue-400" />
              <h2 className="text-3xl font-bold text-white">Ready to get started?</h2>
            </div>
            <p className="text-lg text-slate-300 mb-6">
              View your provider validation dashboard and start managing your data with confidence.
            </p>
            <button
              onClick={goToDashboard}
              className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
            >
              Open Dashboard
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      </section>
    </div>
  )
}
