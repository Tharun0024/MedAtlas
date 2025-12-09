import React, { useState, useEffect } from 'react'
import { providerAPI, exportAPI } from '../services/api'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import './ReportsPage.css'

function ReportsPage() {
  const [summary, setSummary] = useState(null)
  const [providers, setProviders] = useState([])
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)
  const [error, setError] = useState(null)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [summaryData, providersData] = await Promise.all([
        providerAPI.getSummary(),
        providerAPI.getProviders()
      ])
      setSummary(summaryData)
      setProviders(providersData || [])
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to load reports data'
      setError(errorMsg)
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async (format) => {
    try {
      setExporting(true)
      showToast(`Exporting as ${format.toUpperCase()}...`, 'info')
      
      const result = await exportAPI.exportDirectory(format)
      
      // Download the file
      const blob = await exportAPI.downloadExport(result.filename)
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = result.filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
      
      showToast(`Successfully exported ${result.provider_count} providers`, 'success')
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to export directory'
      showToast(errorMsg, 'error')
      console.error(err)
    } finally {
      setExporting(false)
    }
  }

  const showToast = (message, type) => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }

  // Prepare chart data
  const statusData = providers.reduce((acc, provider) => {
    const status = provider.validation_status || provider.status || 'pending'
    acc[status] = (acc[status] || 0) + 1
    return acc
  }, {})

  const statusChartData = Object.entries(statusData).map(([name, value]) => ({
    name: name.replace('_', ' ').toUpperCase(),
    value
  }))

  const confidenceRanges = [
    { range: '0-20', count: 0 },
    { range: '21-40', count: 0 },
    { range: '41-60', count: 0 },
    { range: '61-80', count: 0 },
    { range: '81-100', count: 0 }
  ]

  providers.forEach(provider => {
    const score = provider.confidence_score || 0
    if (score <= 20) confidenceRanges[0].count++
    else if (score <= 40) confidenceRanges[1].count++
    else if (score <= 60) confidenceRanges[2].count++
    else if (score <= 80) confidenceRanges[3].count++
    else confidenceRanges[4].count++
  })

  // Confidence histogram data
  const confidenceHistogramData = confidenceRanges.map(range => ({
    range: range.range,
    count: range.count
  }))

  const COLORS = ['#e74c3c', '#f39c12', '#f1c40f', '#2ecc71', '#27ae60']

  if (loading) {
    return <div className="loading">Loading reports...</div>
  }

  return (
    <div className="reports-page">
      <div className="page-header">
        <h1>Reports & Analytics</h1>
        <p>Visualize provider data quality and export directories</p>
      </div>

      {toast && (
        <div className={`toast toast-${toast.type}`}>
          {toast.message}
        </div>
      )}

      {error && <div className="error">{error}</div>}

      <div className="card">
        <div className="export-controls">
          <h2>Export Directory</h2>
          <p>Export all validated provider data to CSV or JSON format.</p>
          <div className="export-buttons">
            <button
              className="button"
              onClick={() => handleExport('csv')}
              disabled={exporting}
            >
              {exporting ? 'Exporting...' : 'Export as CSV'}
            </button>
            <button
              className="button button-secondary"
              onClick={() => handleExport('json')}
              disabled={exporting}
            >
              {exporting ? 'Exporting...' : 'Export as JSON'}
            </button>
          </div>
        </div>
      </div>

      {statusChartData.length > 0 && (
        <div className="card">
          <h2>Provider Status Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusChartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {statusChartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      )}

      {confidenceHistogramData.length > 0 && (
        <div className="card">
          <h2>Confidence Score Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={confidenceHistogramData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="count" fill="#3498db" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {summary && (
        <div className="card">
          <h2>Summary Statistics</h2>
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-value">{summary.total_providers || 0}</div>
              <div className="stat-label">Total Providers</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{summary.validated_providers || 0}</div>
              <div className="stat-label">Validated</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{summary.pending_providers || 0}</div>
              <div className="stat-label">Pending</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{summary.total_discrepancies || 0}</div>
              <div className="stat-label">Total Discrepancies</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{summary.open_discrepancies || 0}</div>
              <div className="stat-label">Open Discrepancies</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{(summary.avg_confidence_score || 0).toFixed(1)}</div>
              <div className="stat-label">Avg Confidence</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{summary.high_risk_providers || 0}</div>
              <div className="stat-label">High Risk</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ReportsPage

