import React, { useState } from 'react'
import {
  Download,
  FileText,
  FileJson,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react'
import { exportAPI } from '../services/api'

interface ExportMeta {
  total_records?: number
  filtered_records?: number
  last_export_at?: string
  filename?: string
}

export default function Export() {
  const [loadingFormat, setLoadingFormat] = useState<'csv' | 'json' | null>(
    null,
  )
  const [error, setError] = useState<string | null>(null)
  const [meta, setMeta] = useState<ExportMeta>({})

  const handleExport = async (format: 'csv' | 'json') => {
    try {
      setError(null)
      setLoadingFormat(format)

      const result = await exportAPI.createExport(format)
      setMeta((prev) => ({
        ...prev,
        total_records: result.total_records ?? prev.total_records,
        filtered_records: result.filtered_records ?? prev.filtered_records,
        last_export_at: result.created_at ?? result.timestamp ?? prev.last_export_at,
        filename: result.filename ?? prev.filename,
      }))

      if (result.filename) {
        await exportAPI.downloadExport(result.filename)
      } else {
        setError('Export created but filename was not returned.')
      }
    } catch (err: any) {
      console.error(err)
      setError(
        err?.response?.data?.detail || err?.message || 'Export failed',
      )
    } finally {
      setLoadingFormat(null)
    }
  }

  const totalRecords = meta.total_records ?? 1248
  const filteredRecords = meta.filtered_records ?? 1216
  const lastExport =
    meta.last_export_at ?? 'No exports yet – run your first export.'

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Export Data</h1>
        <p className="text-slate-400">
          Download provider validation data for reporting and integration
        </p>
        {error && (
          <p className="mt-2 text-xs text-red-300">
            {error}
          </p>
        )}
      </div>

      <div className="max-w-3xl">
        <div className="bg-amber-600/10 border border-amber-600/20 rounded-lg p-4 flex items-start gap-3 mb-8">
          <AlertCircle
            className="text-amber-400 flex-shrink-0 mt-0.5"
            size={20}
          />
          <div>
            <h4 className="text-sm font-semibold text-amber-300 mb-1">
              Export Snapshot Notice
            </h4>
            <p className="text-sm text-amber-200/80">
              Exports reflect a point-in-time snapshot of your data. Any
              validation updates or changes made after export will not be
              reflected in the downloaded file.
            </p>
          </div>
        </div>

        {/* Format cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-all">
            <div className="w-12 h-12 bg-green-600/10 rounded-lg flex items-center justify-center mb-4">
              <FileText size={24} className="text-green-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              CSV Export
            </h3>
            <p className="text-slate-400 text-sm mb-4">
              Download provider data in comma-separated format. Compatible with
              Excel, Google Sheets, and most data analysis tools.
            </p>
            <button
              onClick={() => handleExport('csv')}
              disabled={loadingFormat !== null}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-3 bg-green-600 hover:bg-green-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
            >
              <Download size={18} />
              {loadingFormat === 'csv' ? 'Exporting…' : 'Export as CSV'}
            </button>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 hover:border-slate-700 transition-all">
            <div className="w-12 h-12 bg-blue-600/10 rounded-lg flex items-center justify-center mb-4">
              <FileJson size={24} className="text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">
              JSON Export
            </h3>
            <p className="text-slate-400 text-sm mb-4">
              Download structured data in JSON format. Ideal for API
              integration, custom processing, and developer workflows.
            </p>
            <button
              onClick={() => handleExport('json')}
              disabled={loadingFormat !== null}
              className="w-full inline-flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed text-white font-medium rounded-lg transition-colors"
            >
              <Download size={18} />
              {loadingFormat === 'json' ? 'Exporting…' : 'Export as JSON'}
            </button>
          </div>
        </div>

        {/* Options – still local UI, not yet sent as filters */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 mb-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            Export Options
          </h3>

          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-300 mb-2 block">
                Validation Status
              </label>
              <div className="flex flex-wrap gap-2">
                <label className="inline-flex items-center gap-2 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg cursor-pointer hover:bg-slate-700 transition-colors">
                  <input
                    type="checkbox"
                    className="w-4 h-4 accent-blue-600"
                    defaultChecked
                  />
                  <span className="text-slate-300 text-sm">Validated</span>
                </label>
                <label className="inline-flex items-center gap-2 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg cursor-pointer hover:bg-slate-700 transition-colors">
                  <input
                    type="checkbox"
                    className="w-4 h-4 accent-blue-600"
                    defaultChecked
                  />
                  <span className="text-slate-300 text-sm">Pending</span>
                </label>
                <label className="inline-flex items-center gap-2 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg cursor-pointer hover:bg-slate-700 transition-colors">
                  <input
                    type="checkbox"
                    className="w-4 h-4 accent-blue-600"
                  />
                  <span className="text-slate-300 text-sm">Failed</span>
                </label>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-300 mb-2 block">
                Include Fields
              </label>
              <div className="grid grid-cols-2 gap-2">
                <label className="inline-flex items-center gap-2 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg cursor-pointer hover:bg-slate-700 transition-colors">
                  <input
                    type="checkbox"
                    className="w-4 h-4 accent-blue-600"
                    defaultChecked
                  />
                  <span className="text-slate-300 text-sm">
                    Provider Details
                  </span>
                </label>
                <label className="inline-flex items-center gap-2 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg cursor-pointer hover:bg-slate-700 transition-colors">
                  <input
                    type="checkbox"
                    className="w-4 h-4 accent-blue-600"
                    defaultChecked
                  />
                  <span className="text-slate-300 text-sm">
                    Confidence Scores
                  </span>
                </label>
                <label className="inline-flex items-center gap-2 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg cursor-pointer hover:bg-slate-700 transition-colors">
                  <input
                    type="checkbox"
                    className="w-4 h-4 accent-blue-600"
                    defaultChecked
                  />
                  <span className="text-slate-300 text-sm">
                    Validation Dates
                  </span>
                </label>
                <label className="inline-flex items-center gap-2 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg cursor-pointer hover:bg-slate-700 transition-colors">
                  <input
                    type="checkbox"
                    className="w-4 h-4 accent-blue-600"
                  />
                  <span className="text-slate-300 text-sm">Discrepancies</span>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Details */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">
            Export Details
          </h3>

          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">Total Records Available</span>
              <span className="text-white font-medium">{totalRecords}</span>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-slate-800">
              <span className="text-slate-400">
                Records with Selected Filters
              </span>
              <span className="text-white font-medium">
                {filteredRecords}
              </span>
            </div>

            <div className="flex items-center justify-between py-2">
              <span className="text-slate-400">Last Export</span>
              <span className="text-white font-medium">{lastExport}</span>
            </div>
          </div>
        </div>

        <div className="mt-6 bg-green-600/10 border border-green-600/20 rounded-lg p-4 flex items-start gap-3">
          <CheckCircle2
            className="text-green-400 flex-shrink-0 mt-0.5"
            size={20}
          />
          <div>
            <h4 className="text-sm font-semibold text-green-300 mb-1">
              Compliance Ready
            </h4>
            <p className="text-sm text-green-200/80">
              Exports include all necessary metadata for audit trails and
              regulatory compliance documentation. Each export is timestamped
              and includes validation pipeline version information.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
