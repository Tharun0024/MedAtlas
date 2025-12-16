import React, { useEffect, useState } from 'react'
import {
  Users,
  CheckCircle2,
  Clock,
  AlertTriangle,
  TrendingUp,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { providerAPI } from '../services/api'

interface SummaryStats {
  total_providers: number
  validated_providers: number
  pending_providers: number
  total_discrepancies: number
  open_discrepancies: number
  avg_confidence_score: number
  high_risk_providers: number
}

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  trend?: string
  trendUp?: boolean
}

function StatCard({ title, value, icon, trend, trendUp }: StatCardProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-colors">
      <div className="flex items-start justify-between mb-4">
        <div className="w-12 h-12 bg-blue-600/10 rounded-lg flex items-center justify-center">
          {icon}
        </div>
        {trend && (
          <div
            className={`flex items-center gap-1 text-xs font-medium ${
              trendUp ? 'text-green-400' : 'text-red-400'
            }`}
          >
            <TrendingUp size={14} className={trendUp ? '' : 'rotate-180'} />
            {trend}
          </div>
        )}
      </div>
      <div className="text-3xl font-bold text-white mb-1">{value}</div>
      <div className="text-sm text-slate-400">{title}</div>
    </div>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [summary, setSummary] = useState<SummaryStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadSummary = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await providerAPI.getSummary()
      setSummary(data)
    } catch (err: any) {
      setError(
        err?.response?.data?.detail || err?.message || 'Failed to load summary',
      )
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadSummary()
  }, [])

  const total = summary?.total_providers ?? 0
  const validated = summary?.validated_providers ?? 0
  const pending = summary?.pending_providers ?? 0
  const openDisc = summary?.open_discrepancies ?? 0
  const avgConf = summary?.avg_confidence_score ?? 0

  const validatedPct = total ? Math.round((validated / total) * 100) : 0
  const pendingPct = total ? Math.round((pending / total) * 100) : 0
  const failedPct = total
    ? Math.max(0, 100 - validatedPct - pendingPct)
    : 0

  return (
    <div className="p-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2">Dashboard</h1>
          <p className="text-slate-400">
            Provider validation metrics and system overview
          </p>
        </div>
        {loading && (
          <span className="text-xs text-slate-400">Refreshing metrics…</span>
        )}
      </div>

      {error && (
        <div className="mb-4 rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-2 text-sm text-red-200">
          {error}
        </div>
      )}

      {/* Top stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">
        <StatCard
          title="Total Providers"
          value={total}
          icon={<Users size={24} className="text-blue-400" />}
        />

        <StatCard
          title="Validated"
          value={validated}
          icon={<CheckCircle2 size={24} className="text-green-400" />}
        />

        <StatCard
          title="Pending"
          value={pending}
          icon={<Clock size={24} className="text-amber-400" />}
        />

        <StatCard
          title="Open Discrepancies"
          value={openDisc}
          icon={<AlertTriangle size={24} className="text-red-400" />}
        />

        <StatCard
          title="Avg Confidence"
          value={`${avgConf.toFixed(1)}%`}
          icon={<TrendingUp size={24} className="text-blue-400" />}
        />
      </div>

      {/* Validation status + recent activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">
            Validation Status
          </h2>
          <div className="space-y-3">
            {/* Validated */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-green-500 rounded-full" />
                <span className="text-slate-300">Validated</span>
              </div>
              <span className="text-white font-medium">{validated}</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full"
                style={{ width: `${validatedPct}%` }}
              />
            </div>

            {/* Pending */}
            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-amber-500 rounded-full" />
                <span className="text-slate-300">Pending</span>
              </div>
              <span className="text-white font-medium">{pending}</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2">
              <div
                className="bg-amber-500 h-2 rounded-full"
                style={{ width: `${pendingPct}%` }}
              />
            </div>

            {/* Failed / issues */}
            <div className="flex items-center justify-between pt-2">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-red-500 rounded-full" />
                <span className="text-slate-300">Failed / Issues</span>
              </div>
              <span className="text-white font-medium">{openDisc}</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2">
              <div
                className="bg-red-500 h-2 rounded-full"
                style={{ width: `${failedPct}%` }}
              />
            </div>
          </div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">
            Recent Activity
          </h2>
          <div className="space-y-4 text-sm">
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 bg-green-500 rounded-full mt-2" />
              <div className="flex-1">
                <p className="text-slate-300">
                  Validation completed for {validated} providers in the latest run.
                </p>
                <p className="text-slate-500 text-xs mt-1">Most recent job</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-2 h-2 bg-amber-500 rounded-full mt-2" />
              <div className="flex-1">
                <p className="text-slate-300">
                  {pending} providers awaiting manual review or next run.
                </p>
                <p className="text-slate-500 text-xs mt-1">
                  Scheduled validation
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-2 h-2 bg-blue-500 rounded-full mt-2" />
              <div className="flex-1">
                <p className="text-slate-300">
                  Network now contains {total} providers in MedAtlas.
                </p>
                <p className="text-slate-500 text-xs mt-1">Directory snapshot</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="w-2 h-2 bg-red-500 rounded-full mt-2" />
              <div className="flex-1">
                <p className="text-slate-300">
                  {openDisc} discrepancies currently open.
                </p>
                <p className="text-slate-500 text-xs mt-1">
                  QA queue / discrepancy view
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick actions + system status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">
            Quick Actions
          </h2>
          <div className="space-y-2">
            <button
              onClick={() => navigate('/providers')}
              className="w-full text-left px-4 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
            >
              View All Providers
            </button>
            <button
              onClick={() => navigate('/discrepancies')}
              className="w-full text-left px-4 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
            >
              Review Discrepancies
            </button>
            <button
              onClick={() => navigate('/export')}
              className="w-full text-left px-4 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
            >
              Export Data
            </button>
          </div>
        </div>

        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h2 className="text-lg font-semibold text-white mb-4">
            System Status
          </h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            {[
              'Validation Pipeline',
              'Discrepancy Detection',
              'Export Service',
              'API Gateway',
            ].map((label) => (
              <div key={label} className="flex items-center gap-3">
                <div className="w-3 h-3 bg-green-500 rounded-full" />
                <div>
                  <p className="text-slate-400 text-xs">{label}</p>
                  <p className="text-white font-medium">Operational</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
