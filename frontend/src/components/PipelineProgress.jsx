import React from 'react';
import {
  CheckCircle,
  Loader2,
  Circle,
  AlertCircle,
  Layers,
} from 'lucide-react';

const STEP_DEFINITIONS = [
  { key: 'step1', number: 1, name: 'Source Collection', desc: 'GNews, NewsData, RSS' },
  { key: 'step2', number: 2, name: 'Scraping', desc: 'Article extraction' },
  { key: 'step3', number: 3, name: 'Content Cleaning', desc: 'HTML & boilerplate removal' },
  { key: 'step4', number: 4, name: 'Duplicate Detection', desc: 'URL, Hash, Cosine Sim' },
  { key: 'step5', number: 5, name: 'PostgreSQL', desc: 'Knowledge Base' },
  { key: 'step6', number: 6, name: 'MCP Access Layer', desc: 'DB Query Tool' },
  { key: 'step7', number: 7, name: 'Gemini AI', desc: 'Fact-grounded synthesis' },
  { key: 'step8', number: 8, name: 'Google Docs', desc: 'Drive category folders' },
];

export default function PipelineProgress({ steps = {}, progress = 0, currentStep = '' }) {
  const getStatusIcon = (status) => {
    switch (status) {
      case 'COMPLETED':
        return <CheckCircle size={16} className="text-emerald-400" color="#34d399" />;
      case 'RUNNING':
        return <Loader2 size={16} className="animate-spin" color="#60a5fa" />;
      case 'FAILED':
        return <AlertCircle size={16} color="#f87171" />;
      default:
        return <Circle size={16} color="#64748b" />;
    }
  };

  const getBadgeClass = (status) => {
    switch (status) {
      case 'COMPLETED':
        return 'badge-completed';
      case 'RUNNING':
        return 'badge-running';
      case 'FAILED':
        return 'badge-failed';
      default:
        return 'badge-pending';
    }
  };

  return (
    <div className="dashboard-section">
      <div className="section-header">
        <div className="section-title">
          <Layers size={18} />
          ESTD Continuous Pipeline Flow (Steps 1–8)
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
          Progress: <strong style={{ color: '#fff' }}>{progress}%</strong>
          {currentStep && currentStep !== 'QUEUED' && (
            <span style={{ marginLeft: 10, color: '#60a5fa' }}>
              Current: <strong>{currentStep}</strong>
            </span>
          )}
        </div>
      </div>

      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${progress}%` }} />
      </div>

      <div className="pipeline-steps-grid">
        {STEP_DEFINITIONS.map((def) => {
          const stepData = steps[def.key] || {};
          const status = stepData.status || 'PENDING';
          const isActive = status === 'RUNNING';
          const isDone = status === 'COMPLETED';
          const isErr = status === 'FAILED';

          return (
            <div
              key={def.key}
              className={`step-card ${isActive ? 'active' : ''} ${
                isDone ? 'completed' : ''
              } ${isErr ? 'failed' : ''}`}
            >
              <div className="step-top">
                <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)' }}>
                  STEP {def.number}
                </span>
                <span className={`step-badge ${getBadgeClass(status)}`}>
                  {status}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 4 }}>
                {getStatusIcon(status)}
                <span className="step-name">{def.name}</span>
              </div>

              <span className="step-desc">
                {stepData.details || def.desc}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
