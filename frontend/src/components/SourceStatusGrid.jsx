import React from 'react';
import { Globe, Radio, Rss, CheckCircle2, AlertTriangle, Clock } from 'lucide-react';

export default function SourceStatusGrid({ sources = {} }) {
  const renderProviderCard = (key, title, icon, defaultDesc) => {
    const data = sources[key] || { status: 'PENDING', count: 0 };
    const status = data.status || 'PENDING';
    const isConnected = status === 'CONNECTED';
    const isWarning = status === 'WARNING';

    return (
      <div className="source-card">
        <div className="source-icon">
          {icon}
        </div>
        <div className="source-info">
          <div className="source-name">{title}</div>
          <div className="source-status">
            {isConnected ? (
              <span style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: 4 }}>
                <CheckCircle2 size={13} /> Connected
              </span>
            ) : isWarning ? (
              <span style={{ color: '#f59e0b', display: 'flex', alignItems: 'center', gap: 4 }}>
                <AlertTriangle size={13} /> Notice / Rate-Limited
              </span>
            ) : (
              <span style={{ color: '#94a3b8', display: 'flex', alignItems: 'center', gap: 4 }}>
                <Clock size={13} /> Standby
              </span>
            )}
          </div>
          <div className="source-count">
            Articles Ingested: <strong style={{ color: '#fff' }}>{data.count || 0}</strong>
          </div>
          {data.error && (
            <div style={{ fontSize: 10, color: '#f87171', marginTop: 4 }}>
              {data.error}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="dashboard-section">
      <div className="section-header">
        <div className="section-title">
          <Globe size={18} />
          Step 1 Source Collection Providers
        </div>
      </div>

      <div className="sources-grid">
        {renderProviderCard('gnews', 'GNews API', <Globe size={22} />, 'Real-time REST collection')}
        {renderProviderCard('newsdata', 'NewsData.io API', <Radio size={22} />, 'Global news REST API')}
        {renderProviderCard('rss', 'Curated RSS Feeds', <Rss size={22} />, 'Verified XML/Atom feeds')}
      </div>
    </div>
  );
}
