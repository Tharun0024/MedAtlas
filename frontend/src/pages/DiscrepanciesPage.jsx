import React, { useState, useEffect } from 'react'
import { discrepancyAPI, providerAPI } from '../services/api'
import DiscrepancyList from '../components/DiscrepancyList'
import './DiscrepanciesPage.css'

function DiscrepanciesPage() {
  const [discrepancies, setDiscrepancies] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [statusFilter, setStatusFilter] = useState('open')
  const [toast, setToast] = useState(null)
  const [providers, setProviders] = useState({})

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    // Filter discrepancies when filter changes
    if (!loading) {
      loadDiscrepancies()
    }
  }, [statusFilter])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Load both discrepancies and providers in parallel
      const [discData, provData] = await Promise.all([
        discrepancyAPI.getDiscrepancies(),
        providerAPI.getProviders()
      ])
      
      setDiscrepancies(discData || [])
      
      // Create provider lookup map
      const providerMap = {}
      provData?.forEach(p => {
        const name = (p.first_name && p.last_name) 
          ? `${p.first_name} ${p.last_name}` 
          : (p.organization_name || 'Unknown')
        providerMap[p.id] = name
      })
      setProviders(providerMap)
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to load discrepancies'
      setError(errorMsg)
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const loadDiscrepancies = async () => {
    try {
      setError(null)
      const data = await discrepancyAPI.getDiscrepancies(
        null,
        statusFilter === 'all' ? null : statusFilter
      )
      setDiscrepancies(data || [])
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to load discrepancies'
      setError(errorMsg)
      console.error(err)
    }
  }

  const handleResolve = async (discrepancyId) => {
    try {
      await discrepancyAPI.updateDiscrepancy(discrepancyId, 'resolved', 'Resolved manually')
      showToast('Discrepancy marked as resolved', 'success')
      await loadData()
    } catch (err) {
      const errorMsg = err.response?.data?.detail || 'Failed to resolve discrepancy'
      showToast(errorMsg, 'error')
      console.error(err)
    }
  }

  const showToast = (message, type) => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 3000)
  }

  const getFilteredDiscrepancies = () => {
    if (statusFilter === 'all') {
      return discrepancies
    }
    return discrepancies.filter(d => d.status === statusFilter)
  }

  if (loading) {
    return <div className="loading">Loading discrepancies...</div>
  }

  const filtered = getFilteredDiscrepancies()

  return (
    <div className="discrepancies-page">
      <div className="page-header">
        <h1>Discrepancies</h1>
        <p>Review and resolve data inconsistencies across providers</p>
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
            <option value="all">All ({discrepancies.length})</option>
            <option value="open">Open ({discrepancies.filter(d => d.status === 'open').length})</option>
            <option value="resolved">Resolved ({discrepancies.filter(d => d.status === 'resolved').length})</option>
          </select>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <DiscrepancyList
        discrepancies={filtered}
        onResolve={handleResolve}
        providers={providers}
      />
    </div>
  )
}

export default DiscrepanciesPage

