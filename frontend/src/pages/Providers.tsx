import React, { useEffect, useMemo, useState } from 'react'
import { Search, Filter, ChevronDown } from 'lucide-react'
import { providerAPI } from '../services/api'

type ProviderStatus = 'validated' | 'pending' | 'failed'

interface Provider {
  id: string
  name: string
  npi: string
  specialty: string
  status: ProviderStatus
  confidence: number
  lastValidated: string
}

function StatusBadge({ status }: { status: ProviderStatus }) {
  const styles: Record<ProviderStatus, string> = {
    validated: 'bg-green-600/10 text-green-400 border-green-600/20',
    pending: 'bg-amber-600/10 text-amber-400 border-amber-600/20',
    failed: 'bg-red-600/10 text-red-400 border-red-600/20',
  }

  const labels: Record<ProviderStatus, string> = {
    validated: 'Validated',
    pending: 'Pending',
    failed: 'Failed',
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border ${styles[status]}`}
    >
      {labels[status]}
    </span>
  )
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const color =
    confidence >= 90
      ? 'bg-green-500'
      : confidence >= 75
      ? 'bg-amber-500'
      : 'bg-red-500'

  const safeWidth = Math.max(0, Math.min(100, confidence))

  return (
    <div className="flex items-center gap-2">
      <div className="w-24 bg-slate-800 rounded-full h-2">
        <div
          className={`${color} h-2 rounded-full`}
          style={{ width: `${safeWidth}%` }}
        />
      </div>
      <span className="text-sm text-slate-400 w-10">
        {safeWidth.toFixed(0)}%
      </span>
    </div>
  )
}

export default function Providers() {
  const [providers, setProviders] = useState<Provider[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<ProviderStatus | 'all'>(
    'all',
  )

  const [validatingId, setValidatingId] = useState<string | null>(null)

  const loadProviders = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await providerAPI.getProviders()
      const mapped: Provider[] = data.map((p: any) => ({
        id: String(p.id),
        name:
          p.full_name ??
          [p.first_name, p.last_name].filter(Boolean).join(' ') ??
          'Unknown provider',
        npi: p.npi ?? '',
        specialty: p.specialty ?? 'Not specified',
        status: (p.validation_status ?? 'pending') as ProviderStatus,
        confidence:
          typeof p.confidence_score === 'number'
            ? p.confidence_score
            : p.confidence_score
            ? Number(p.confidence_score)
            : 0,
        lastValidated:
          p.last_validated_at?.slice(0, 10) ??
          p.updated_at?.slice(0, 10) ??
          '—',
      }))
      setProviders(mapped)
    } catch (err: any) {
      console.error(err)
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'Failed to load providers',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadProviders()
  }, [])

  const handleValidate = async (id: string) => {
    try {
      setValidatingId(id)
      setError(null)
      const result = await providerAPI.validateProvider(Number(id))
      const final = result?.final_results ?? {}
      const newStatus = (final.validation_status ?? 'validated') as ProviderStatus
      const newConfidence =
        typeof final.confidence_score === 'number'
          ? final.confidence_score
          : final.confidence_score
          ? Number(final.confidence_score)
          : 0

      setProviders((prev) =>
        prev.map((p) =>
          p.id === id
            ? {
                ...p,
                status: newStatus,
                confidence: newConfidence || p.confidence,
                lastValidated: new Date().toISOString().slice(0, 10),
              }
            : p,
        ),
      )
    } catch (err: any) {
      console.error(err)
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'Failed to validate provider',
      )
    } finally {
      setValidatingId(null)
    }
  }

  const filteredProviders = useMemo(() => {
    return providers.filter((p) => {
      const matchesSearch =
        !search ||
        p.name.toLowerCase().includes(search.toLowerCase()) ||
        p.npi.toLowerCase().includes(search.toLowerCase()) ||
        p.specialty.toLowerCase().includes(search.toLowerCase())

      const matchesStatus =
        statusFilter === 'all' || p.status === statusFilter

      return matchesSearch && matchesStatus
    })
  }, [providers, search, statusFilter])

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Providers</h1>
        <p className="text-slate-400">
          Manage and review provider validation status
        </p>
        {loading && (
          <p className="mt-2 text-xs text-slate-500">
            Loading providers…
          </p>
        )}
        {error && (
          <p className="mt-2 text-xs text-red-300">
            {error}
          </p>
        )}
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        {/* Search + filters */}
        <div className="p-6 border-b border-slate-800">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
                size={20}
              />
              <input
                type="text"
                placeholder="Search by name, NPI, or specialty..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
              />
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() =>
                  setStatusFilter((prev) =>
                    prev === 'all' ? 'validated' : 'all',
                  )
                }
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg transition-colors"
              >
                <Filter size={18} />
                <span>
                  Status:{' '}
                  {statusFilter === 'all'
                    ? 'All'
                    : statusFilter.charAt(0).toUpperCase() +
                      statusFilter.slice(1)}
                </span>
                <ChevronDown size={16} />
              </button>

              <button
                type="button"
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-800 border border-slate-700 text-slate-500 rounded-lg cursor-default"
              >
                <span>Specialty</span>
                <ChevronDown size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-800/50 border-b border-slate-800">
              <tr>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Provider Name
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  NPI
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Specialty
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Confidence
                </th>
                <th className="px-6 py-4 text-left text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Last Validated
                </th>
                <th className="px-6 py-4" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filteredProviders.map((provider) => (
                <tr
                  key={provider.id}
                  className="hover:bg-slate-800/30 transition-colors"
                >
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-white">
                      {provider.name}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-slate-400 font-mono">
                      {provider.npi}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-slate-300">
                      {provider.specialty}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={provider.status} />
                  </td>
                  <td className="px-6 py-4">
                    <ConfidenceBar confidence={provider.confidence} />
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-slate-400">
                      {provider.lastValidated}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-xs font-medium text-white disabled:opacity-60 disabled:cursor-not-allowed"
                      onClick={() => handleValidate(provider.id)}
                      disabled={validatingId === provider.id}
                    >
                      {validatingId === provider.id ? 'Validating…' : 'Validate'}
                    </button>
                  </td>
                </tr>
              ))}

              {!loading && filteredProviders.length === 0 && (
                <tr>
                  <td
                    colSpan={7}
                    className="px-6 py-6 text-sm text-slate-400 text-center"
                  >
                    No providers match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between">
          <div className="text-sm text-slate-400">
            Showing{' '}
            <span className="text-white font-medium">
              {filteredProviders.length}
            </span>{' '}
            of{' '}
            <span className="text-white font-medium">
              {providers.length}
            </span>{' '}
            providers
          </div>
          <div className="flex gap-2">
            <button
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled
            >
              Previous
            </button>
            <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg transition-colors">
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
