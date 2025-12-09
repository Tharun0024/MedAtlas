import React, { useState, useEffect } from 'react'
import { providerAPI, validationAPI } from '../services/api'
import SummaryCards from '../components/SummaryCards'
import './Dashboard.css'

function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [validating, setValidating] = useState(false)
  const [validationResult, setValidationResult] = useState(null)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    loadSummary()
  }, [])

  const loadSummary = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await providerAPI.getSummary()
      setSummary(data)
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to load dashboard data'
      setError(errorMsg)
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleRunValidation = async () => {
    try {
      setValidating(true)
      setValidationResult(null)
      setError(null)
      showToast('Starting validation pipeline...', 'info')
      
      const result = await validationAPI.runValidation()
      setValidationResult(result)
      
      // Reload summary and providers after validation
      await loadSummary()
      showToast(
        `Validation complete! Validated: ${result.validated}, Needs Review: ${result.needs_review}`,
        'success'
      )
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to run validation pipeline'
      setError(errorMsg)
      showToast(errorMsg, 'error')
      console.error(err)
    } finally {
      setValidating(false)
    }
  }

  const showToast = (message, type) => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }

  if (loading) {
    return <div className="loading">Loading dashboard...</div>
  }

  return (
    <div className="dashboard">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p>Overview of provider data validation and directory management</p>
      </div>

      {toast && (
        <div className={`toast toast-${toast.type}`}>
          {toast.message}
        </div>
      )}

      {error && <div className="error">{error}</div>}

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h2>Validation Pipeline</h2>
            <p>Process all providers through the validation pipeline for data quality assurance.</p>
          </div>
          <button
            className="button"
            onClick={handleRunValidation}
            disabled={validating}
            style={{ minWidth: '160px' }}
          >
            {validating ? 'Running...' : 'Run Validation'}
          </button>
        </div>
      </div>

      {summary && <SummaryCards summary={summary} />}

      <div className="card">
        <h2>Quick Stats</h2>
        <div className="quick-stats">
          <div className="stat-item">
            <div className="stat-label">Total Providers</div>
            <div className="stat-value">{summary?.total_providers || 0}</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">Validation Status</div>
            <div className="stat-value">{summary?.validation_status || 'N/A'}</div>
          </div>
          <div className="stat-item">
            <div className="stat-label">Recent Updates</div>
            <div className="stat-value">{summary?.recent_updates || 0}</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard

