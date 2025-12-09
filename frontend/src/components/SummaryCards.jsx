import React from 'react'
import './SummaryCards.css'

function SummaryCards({ summary }) {
  if (!summary) return null

  const cards = [
    {
      title: 'Total Providers',
      value: summary.total_providers,
      color: '#3498db',
      icon: '👥'
    },
    {
      title: 'Validated',
      value: summary.validated_providers,
      color: '#27ae60',
      icon: '✅'
    },
    {
      title: 'Pending',
      value: summary.pending_providers,
      color: '#f39c12',
      icon: '⏳'
    },
    {
      title: 'Discrepancies',
      value: summary.total_discrepancies,
      color: '#e74c3c',
      icon: '⚠️'
    },
    {
      title: 'Open Issues',
      value: summary.open_discrepancies,
      color: '#e67e22',
      icon: '🔴'
    },
    {
      title: 'Avg Confidence',
      value: `${summary.avg_confidence_score.toFixed(1)}%`,
      color: '#9b59b6',
      icon: '📊'
    },
    {
      title: 'High Risk',
      value: summary.high_risk_providers,
      color: '#c0392b',
      icon: '🚨'
    }
  ]

  return (
    <div className="summary-cards">
      {cards.map((card, index) => (
        <div key={index} className="summary-card" style={{ borderTopColor: card.color }}>
          <div className="card-icon">{card.icon}</div>
          <div className="card-content">
            <div className="card-value" style={{ color: card.color }}>
              {card.value}
            </div>
            <div className="card-title">{card.title}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default SummaryCards

