import React, { useState } from 'react'
import { UploadCloud, FileText, FileScan, CheckCircle2, AlertCircle } from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL

export default function Upload() {
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [pdfFiles, setPdfFiles] = useState<File[]>([])
  const [runValidation, setRunValidation] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!csvFile) {
      setError('Select a provider CSV file first.')
      return
    }

    try {
      setLoading(true)
      setError(null)
      setMessage(null)

      const formData = new FormData()
      // MUST match FastAPI param names:
      formData.append('file', csvFile) // CSV -> file: UploadFile
      pdfFiles.forEach((f) => formData.append('pdf_files', f)) // List[UploadFile]
      formData.append('run_validation', String(runValidation)) // bool Form field

      const res = await fetch(`${API_BASE}/providers/upload`, {
        method: 'POST',
        body: formData, // do NOT set Content-Type header
      })

      if (!res.ok) {
        const payload = await res.json().catch(() => null)
        throw new Error(payload?.detail || 'Upload failed')
      }

      const data = await res.json()
      setMessage(
        `Uploaded and processed ${data.processed ?? data.uploaded ?? 'N'} providers.`,
      )
    } catch (err: any) {
      setError(err?.message || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Upload Providers</h1>
        <p className="text-slate-400">
          Upload a CSV of providers and optional supporting PDFs for validation.
        </p>
      </div>

      <div className="max-w-3xl space-y-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
          <div className="flex gap-4">
            <div className="w-10 h-10 rounded-lg bg-blue-600/20 flex items-center justify-center">
              <FileText size={22} className="text-blue-400" />
            </div>
            <div className="text-sm text-slate-300">
              <p className="font-medium mb-1">Provider CSV</p>
              <p className="text-slate-400">
                Required. Columns like NPI, name, specialty, address, phone, license, etc.
              </p>
            </div>
          </div>

          <div className="flex gap-4">
            <div className="w-10 h-10 rounded-lg bg-emerald-600/20 flex items-center justify-center">
              <FileScan size={22} className="text-emerald-400" />
            </div>
            <div className="text-sm text-slate-300">
              <p className="font-medium mb-1">Supporting PDFs</p>
              <p className="text-slate-400">
                Optional. Upload license certificates or other documents for OCR and
                document checks.
              </p>
            </div>
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-5"
        >
          {/* CSV input */}
          <div>
            <label className="block text-sm font-medium text-slate-200 mb-2">
              Provider CSV (required)
            </label>
            <label className="flex flex-col items-center justify-center gap-2 border border-dashed border-slate-700 rounded-xl px-6 py-10 cursor-pointer hover:border-slate-500 hover:bg-slate-800/40 transition-colors">
              <UploadCloud size={28} className="text-slate-300" />
              <span className="text-sm text-slate-200">
                {csvFile ? csvFile.name : 'Click to choose a CSV file'}
              </span>
              <span className="text-xs text-slate-500">Only .csv files are accepted</span>
              <input
                type="file"
                accept=".csv"
                className="hidden"
                onChange={(e) => setCsvFile(e.target.files?.[0] ?? null)}
              />
            </label>
          </div>

          {/* PDFs input */}
          <div>
            <label className="block text-sm font-medium text-slate-200 mb-2">
              Supporting PDFs (optional, multiple)
            </label>
            <label className="flex flex-col items-center justify-center gap-2 border border-dashed border-slate-700 rounded-xl px-6 py-6 cursor-pointer hover:border-slate-500 hover:bg-slate-800/40 transition-colors">
              <FileScan size={24} className="text-slate-300" />
              <span className="text-sm text-slate-200">
                {pdfFiles.length
                  ? `${pdfFiles.length} PDF file(s) selected`
                  : 'Click to choose one or more PDF files'}
              </span>
              <span className="text-xs text-slate-500">.pdf only · multiple selection allowed</span>
              <input
                type="file"
                accept="application/pdf"
                multiple
                className="hidden"
                onChange={(e) => setPdfFiles(Array.from(e.target.files ?? []))}
              />
            </label>
          </div>

          <label className="inline-flex items-center gap-2 text-sm text-slate-200">
            <input
              type="checkbox"
              className="h-4 w-4 accent-blue-600"
              checked={runValidation}
              onChange={(e) => setRunValidation(e.target.checked)}
            />
            <span>Run validation immediately after upload</span>
          </label>

          {error && (
            <div className="flex items-start gap-2 rounded-lg border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-200">
              <AlertCircle size={16} className="mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {message && (
            <div className="flex items-start gap-2 rounded-lg border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-200">
              <CheckCircle2 size={16} className="mt-0.5" />
              <span>{message}</span>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center justify-center rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed px-4 py-2 text-sm font-medium text-white"
          >
            {loading ? 'Uploading…' : 'Upload files'}
          </button>
        </form>
      </div>
    </div>
  )
}
