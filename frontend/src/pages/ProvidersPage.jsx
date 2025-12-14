import React, { useState, useEffect } from 'react'
import { providerAPI, validationAPI } from '../services/api'
import ProviderTable from '../components/ProviderTable'
import './ProvidersPage.css'

function ProvidersPage() {
  const [providers, setProviders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const [validatingId, setValidatingId] = useState(null)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    loadProviders()
  }, [])

  useEffect(() => {
    // Filter providers when filter changes
    if (!loading) {
      applyFilter()
    }
  }, [statusFilter])

  const applyFilter = () => {
    if (statusFilter === 'all') {
      return
    }
    // Filtering handled in rendering
  }

  const loadProviders = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await providerAPI.getProviders()
      setProviders(data || [])
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to load providers'
      setError(errorMsg)
      console.error(err)
      setProviders([])
    } finally {
      setLoading(false)
    }
  }

  const handleValidate = async (providerId) => {
    try {
      setValidatingId(providerId)
      await validationAPI.validateProvider(providerId, null, true)
      showToast('Provider validated successfully', 'success')
      // Reload to get updated data
      await loadProviders()
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to validate provider'
      showToast(errorMsg, 'error')
      console.error(err)
    } finally {
      setValidatingId(null)
    }
  }

  const showToast = (message, type) => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }

  const getFilteredProviders = () => {
  if (statusFilter === 'all') {
    return providers
  }
  return providers.filter(p => p.status === statusFilter)
}


  const filteredProviders = getFilteredProviders()

  if (loading) {
    return <div className="loading">Loading providers...</div>
  }

  return (
    <div className="providers-page">
      <div className="page-header">
        <h1>Providers</h1>
        <p>View and manage provider data</p>
      </div>

      {toast && (
        <div className={`toast toast-${toast.type}`}>
          {toast.message}
        </div>
      )}

      <div className="card">
        <div className="filters">
          <label className="label">Filter by Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input"
            style={{ width: 'auto', display: 'inline-block', marginLeft: '1rem' }}
          >
            <option value="all">All</option>
            <option value="pending">Pending</option>
            <option value="validated">Validated</option>
            <option value="needs_review">Needs Review</option>
            <option value="review_recommended">Review Recommended</option>
          </select>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <ProviderTable
        providers={filteredProviders}
        onValidate={handleValidate}
        validatingId={validatingId}
      />
    </div>
  )
}

export default ProvidersPage

