import React from 'react'
import './DiscrepancyList.css'

function DiscrepancyList({ discrepancies, onResolve, providers = {} }) {
  const getRiskBadge = (riskLevel) => {
    const badges = {
      high: { class: 'badge-danger', text: 'High Risk' },
      medium: { class: 'badge-warning', text: 'Medium Risk' },
      low: { class: 'badge-info', text: 'Low Risk' }
    }
    const badge = badges[riskLevel] || badges.medium
    return <span className={`badge ${badge.class}`}>{badge.text}</span>
  }

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return '#27ae60'
    if (confidence >= 60) return '#f39c12'
    return '#e74c3c'
  }

  if (discrepancies.length === 0) {
    return <div className="empty-state">No discrepancies found</div>
  }

  return (
    <div className="discrepancy-list">
      {discrepancies.map((discrepancy) => (
        <div key={discrepancy.id} className="discrepancy-card">
          <div className="discrepancy-header">
            <div>
              <h3>{discrepancy.field_name.replace('_', ' ').toUpperCase()}</h3>
              <span className="provider-id">
                {providers[discrepancy.provider_id] || `Provider ID: ${discrepancy.provider_id}`}
              </span>
            </div>
            <div className="discrepancy-badges">
              {getRiskBadge(discrepancy.risk_level)}
              <span
                className="confidence-badge"
                style={{ color: getConfidenceColor(discrepancy.confidence || 0) }}
              >
                Confidence: {discrepancy.confidence || 0}%
              </span>
            </div>
          </div>

          <div className="discrepancy-values">
            <div className="value-group">
              <label>CSV Value:</label>
              <div className="value-box csv-value">
                {discrepancy.csv_value || 'N/A'}
              </div>
            </div>

            <div className="value-group">
              <label>API Value:</label>
              <div className="value-box api-value">
                {discrepancy.api_value || 'N/A'}
              </div>
            </div>

            <div className="value-group">
              <label>Scraped Value:</label>
              <div className="value-box scraped-value">
                {discrepancy.scraped_value || 'N/A'}
              </div>
            </div>

            <div className="value-group">
              <label>Final Value:</label>
              <div className="value-box final-value">
                {discrepancy.final_value || 'N/A'}
              </div>
            </div>
          </div>

          {discrepancy.notes && (
            <div className="discrepancy-notes">
              <strong>Notes:</strong> {discrepancy.notes}
            </div>
          )}

          <div className="discrepancy-actions">
            {discrepancy.status === 'open' && (
              <button
                className="button button-secondary"
                onClick={() => onResolve(discrepancy.id)}
              >
                Mark as Resolved
              </button>
            )}
            {discrepancy.status === 'resolved' && (
              <span className="resolved-badge">✓ Resolved</span>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export default DiscrepancyList

