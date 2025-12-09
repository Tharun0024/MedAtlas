import React from 'react'
import './ProviderTable.css'

function ProviderTable({ providers, onValidate, validatingId }) {
  const getStatusBadge = (status) => {
    const badges = {
      validated: { class: 'badge-success', text: 'Validated' },
      pending: { class: 'badge-warning', text: 'Pending' },
      needs_review: { class: 'badge-info', text: 'Needs Review' },
      review_recommended: { class: 'badge-warning', text: 'Review Recommended' },
      high_risk: { class: 'badge-danger', text: 'High Risk' }
    }
    const badge = badges[status] || badges.pending
    return <span className={`badge ${badge.class}`}>{badge.text}</span>
  }

  const getConfidenceColor = (score) => {
    if (score >= 80) return '#27ae60'
    if (score >= 60) return '#f39c12'
    return '#e74c3c'
  }

  const getProviderName = (provider) => {
    if (provider.first_name || provider.last_name) {
      return `${provider.first_name || ''} ${provider.last_name || ''}`.trim()
    }
    return provider.organization_name || provider.name || 'N/A'
  }

  if (providers.length === 0) {
    return <div className="empty-state">No providers found.</div>
  }

  return (
    <div className="provider-table-container">
      <table className="provider-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Specialty</th>
            <th>Phone</th>
            <th>Confidence</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {providers.map((provider) => (
            <tr key={provider.id}>
              <td>{provider.id}</td>
              <td>{getProviderName(provider)}</td>
              <td>{provider.specialty || 'N/A'}</td>
              <td>{provider.phone || 'N/A'}</td>
              <td>
                <span
                  className="score-badge"
                  style={{ color: getConfidenceColor(provider.confidence_score || 0) }}
                >
                  {provider.confidence_score || 0}%
                </span>
              </td>
              <td>{getStatusBadge(provider.validation_status || provider.status || 'pending')}</td>
              <td>
                <button
                  className="button-small"
                  onClick={() => onValidate(provider.id)}
                  disabled={validatingId === provider.id}
                >
                  {validatingId === provider.id ? 'Validating...' : 'Validate'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default ProviderTable

