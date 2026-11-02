import React from 'react';
import { BarChart3 } from 'lucide-react';

export default function MetricsGrid({ metrics = {} }) {
  const items = [
    { label: 'Fetched', value: metrics.fetched ?? 0, color: '#60a5fa' },
    { label: 'Scraped', value: metrics.scraped ?? 0, color: '#38bdf8' },
    { label: 'Cleaned', value: metrics.cleaned ?? 0, color: '#818cf8' },
    { label: 'Duplicates Removed', value: metrics.duplicates_removed ?? 0, color: '#f59e0b' },
    { label: 'Stored in PostgreSQL', value: metrics.stored_in_postgres ?? 0, color: '#34d399' },
    { label: 'AI Generated', value: metrics.ai_generated ?? 0, color: '#c084fc' },
    { label: 'Google Docs Created', value: metrics.docs_created ?? 0, color: '#10b981' },
    { label: 'Failed', value: metrics.failed ?? 0, color: metrics.failed > 0 ? '#ef4444' : '#64748b' },
  ];

  return (
    <div className="dashboard-section">
      <div className="section-header">
        <div className="section-title">
          <BarChart3 size={18} />
          Pipeline Execution Metrics
        </div>
      </div>

      <div className="metrics-row">
        {items.map((m) => (
          <div key={m.label} className="metric-card">
            <div className="metric-val" style={{ color: m.color }}>
              {m.value}
            </div>
            <div className="metric-label">{m.label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
