import React, { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Filter, ChevronDown, Search } from 'lucide-react'
import { discrepancyAPI } from "../services/api";



type Severity = 'high' | 'medium' | 'low'
type Status = 'open' | 'under_review' | 'resolved'

interface Discrepancy {
  id: string
  providerId: string
  providerName: string
  type: string
  severity: Severity
  description: string
  detectedDate: string
  status: Status
}

function SeverityBadge({ severity }: { severity: Severity }) {
  const styles: Record<Severity, string> = {
    high: 'bg-red-600/10 text-red-400 border-red-600/20',
    medium: 'bg-amber-600/10 text-amber-400 border-amber-600/20',
    low: 'bg-blue-600/10 text-blue-400 border-blue-600/20',
  }

  const labels: Record<Severity, string> = {
    high: 'High',
    medium: 'Medium',
    low: 'Low',
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border ${styles[severity]}`}
    >
      {labels[severity]}
    </span>
  )
}

function StatusBadge({ status }: { status: Status }) {
  const styles: Record<Status, string> = {
    open: 'bg-red-600/10 text-red-400 border-red-600/20',
    under_review: 'bg-amber-600/10 text-amber-400 border-amber-600/20',
    resolved: 'bg-green-600/10 text-green-400 border-green-600/20',
  }

  const labels: Record<Status, string> = {
    open: 'Open',
    under_review: 'Under Review',
    resolved: 'Resolved',
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium border ${styles[status]}`}
    >
      {labels[status]}
    </span>
  )
}

export default function Discrepancies() {
  const [discrepancies, setDiscrepancies] = useState<Discrepancy[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState('')
  const [severityFilter, setSeverityFilter] = useState<Severity | 'all'>('all')
  const [statusFilter, setStatusFilter] = useState<Status | 'all'>('all')
  const [updatingId, setUpdatingId] = useState<string | null>(null)

  const loadDiscrepancies = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await discrepancyAPI.getDiscrepancies()

      const mapped: Discrepancy[] = data.map((d: any) => {
        const rawStatus = (d.status ?? 'open') as string
        const normalizedStatus = rawStatus.toLowerCase().replace(' ', '_') as Status

        return {
          id: String(d.id),
          providerId: String(d.provider_id ?? ''),
          providerName: d.provider_name ?? 'Unknown provider',
          type: d.type ?? d.field ?? 'Data discrepancy',
          severity: (d.severity ?? 'medium') as Severity,
          description: d.description ?? d.message ?? '',
          detectedDate:
            d.detected_at?.slice(0, 10) ??
            d.created_at?.slice(0, 10) ??
            '',
          status: normalizedStatus,
        }
      })

      setDiscrepancies(mapped)
    } catch (err: any) {
      console.error(err)
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'Failed to load discrepancies',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDiscrepancies()
  }, [])

  const handleReview = async (disc: Discrepancy) => {
    try {
      setUpdatingId(disc.id)
      setError(null)

      const nextStatus: Status =
        disc.status === 'open'
          ? 'under_review'
          : disc.status === 'under_review'
          ? 'resolved'
          : 'resolved'

      const notes =
        nextStatus === 'under_review'
          ? 'Marked as under review from UI'
          : nextStatus === 'resolved'
          ? 'Marked as resolved from UI'
          : ''

      const updated = await discrepancyAPI.updateDiscrepancy(
        Number(disc.id),
        nextStatus,
        notes,
      )

      const rawStatus = (updated.status ?? nextStatus) as string
      const normalizedStatus = rawStatus.toLowerCase().replace(' ', '_') as Status

      setDiscrepancies((prev) =>
        prev.map((d) =>
          d.id === disc.id ? { ...d, status: normalizedStatus } : d,
        ),
      )
    } catch (err: any) {
      console.error(err)
      setError(
        err?.response?.data?.detail ||
          err?.message ||
          'Failed to update discrepancy',
      )
    } finally {
      setUpdatingId(null)
    }
  }

  const filtered = useMemo(() => {
    return discrepancies.filter((d) => {
      const matchesSearch =
        !search ||
        d.id.toLowerCase().includes(search.toLowerCase()) ||
        d.providerId.toLowerCase().includes(search.toLowerCase()) ||
        d.providerName.toLowerCase().includes(search.toLowerCase()) ||
        d.type.toLowerCase().includes(search.toLowerCase())

      const matchesSeverity =
        severityFilter === 'all' || d.severity === severityFilter
      const matchesStatus =
        statusFilter === 'all' || d.status === statusFilter

      return matchesSearch && matchesSeverity && matchesStatus
    })
  }, [discrepancies, search, severityFilter, statusFilter])

  const totalOpen = discrepancies.filter((d) => d.status === 'open').length
  const totalUnderReview = discrepancies.filter(
    (d) => d.status === 'under_review',
  ).length
  const totalResolved = discrepancies.filter(
    (d) => d.status === 'resolved',
  ).length

  return (
    <div className="p-8">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <AlertTriangle className="text-red-400" size={32} />
          <h1 className="text-3xl font-bold text-white">Discrepancies</h1>
        </div>
        <p className="text-slate-400">
          Review and resolve data validation issues
        </p>
        {loading && (
          <p className="mt-2 text-xs text-slate-500">Loading discrepancies…</p>
        )}
        {error && (
          <p className="mt-2 text-xs text-red-300">
            {error}
          </p>
        )}
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-2xl font-bold text-red-400 mb-1">
            {totalOpen}
          </div>
          <div className="text-sm text-slate-400">Open Issues</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-2xl font-bold text-amber-400 mb-1">
            {totalUnderReview}
          </div>
          <div className="text-sm text-slate-400">Under Review</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <div className="text-2xl font-bold text-green-400 mb-1">
            {totalResolved}
          </div>
          <div className="text-sm text-slate-400">Resolved</div>
        </div>
      </div>

      {/* Filters + list */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-6 border-b border-slate-800">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search
                className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500"
                size={20}
              />
              <input
                type="text"
                placeholder="Search by provider, type, or ID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent"
              />
            </div>

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() =>
                  setSeverityFilter((prev) =>
                    prev === 'all' ? 'high' : 'all',
                  )
                }
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg transition-colors"
              >
                <Filter size={18} />
                <span>
                  Severity:{' '}
                  {severityFilter === 'all'
                    ? 'All'
                    : severityFilter.charAt(0).toUpperCase() +
                      severityFilter.slice(1)}
                </span>
                <ChevronDown size={16} />
              </button>

              <button
                type="button"
                onClick={() =>
                  setStatusFilter((prev) =>
                    prev === 'all' ? 'open' : 'all',
                  )
                }
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg transition-colors"
              >
                <span>
                  Status:{' '}
                  {statusFilter === 'all'
                    ? 'All'
                    : statusFilter === 'under_review'
                    ? 'Under Review'
                    : 'Open'}
                </span>
                <ChevronDown size={16} />
              </button>
            </div>
          </div>
        </div>

        <div className="divide-y divide-slate-800">
          {filtered.map((discrepancy) => (
            <div
              key={discrepancy.id}
              className="p-6 hover:bg-slate-800/30 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-sm font-mono text-slate-500">
                      {discrepancy.id}
                    </span>
                    <SeverityBadge severity={discrepancy.severity} />
                    <StatusBadge status={discrepancy.status} />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-1">
                    {discrepancy.type}
                  </h3>
                  <p className="text-slate-400 text-sm mb-2">
                    {discrepancy.description}
                  </p>
                  <div className="flex flex-wrap items-center gap-4 text-sm">
                    <span className="text-slate-500">
                      Provider:{' '}
                      <span className="text-slate-300">
                        {discrepancy.providerName}
                      </span>
                    </span>
                    <span className="text-slate-500">
                      Detected:{' '}
                      <span className="text-slate-300">
                        {discrepancy.detectedDate}
                      </span>
                    </span>
                  </div>
                </div>
                <button
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                  onClick={() => handleReview(discrepancy)}
                  disabled={updatingId === discrepancy.id}
                >
                  {updatingId === discrepancy.id ? 'Updating…' : 'Review'}
                </button>
              </div>
            </div>
          ))}

          {!loading && filtered.length === 0 && (
            <div className="p-6 text-sm text-slate-400">
              No discrepancies match the current filters.
            </div>
          )}
        </div>

        <div className="p-4 border-t border-slate-800 flex items-center justify-between">
          <div className="text-sm text-slate-400">
            Showing{' '}
            <span className="text-white font-medium">
              {filtered.length}
            </span>{' '}
            of{' '}
            <span className="text-white font-medium">
              {discrepancies.length}
            </span>{' '}
            discrepancies
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

      <div className="mt-6 bg-blue-600/10 border border-blue-600/20 rounded-lg p-4 flex items-start gap-3">
        <AlertTriangle
          className="text-blue-400 flex-shrink-0 mt-0.5"
          size={20}
        />
        <div>
          <h4 className="text-sm font-semibold text-blue-300 mb-1">
            Audit Trail
          </h4>
          <p className="text-sm text-blue-200/80">
            All discrepancies are automatically logged with timestamps,
            detection details, and resolution status for compliance
            documentation.
          </p>
        </div>
      </div>
    </div>
  )
}
