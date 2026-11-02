import React from 'react';
import { Activity, Clock, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function PipelineStatusBar({ activeJob, isRunning, lastError }) {
  const getStatusBadge = () => {
    if (isRunning) {
      return (
        <span className="step-badge badge-running">
          ● RUNNING ({activeJob?.current_step || 'INITIALIZING'})
        </span>
      );
    }
    if (activeJob?.status === 'COMPLETED') {
      return (
        <span className="step-badge badge-completed">
          ✓ COMPLETED ({activeJob.duration_seconds}s)
        </span>
      );
    }
    if (activeJob?.status === 'FAILED') {
      return <span className="step-badge badge-failed">✕ FAILED</span>;
    }
    return <span className="step-badge badge-pending">○ IDLE</span>;
  };

  return (
    <div className="status-bar">
      <div className="status-indicator">
        <div
          className={`pulse-dot ${
            isRunning ? 'running' : activeJob?.status === 'FAILED' ? 'failed' : ''
          }`}
        />
        <span>
          <strong>Pipeline Status:</strong> {getStatusBadge()}
        </span>
        {activeJob?.job_id && (
          <span className="mono" style={{ color: 'var(--text-muted)', marginLeft: 8 }}>
            [{activeJob.job_id}]
          </span>
        )}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        {activeJob?.started_at && (
          <span style={{ color: 'var(--text-secondary)' }}>
            Started: {new Date(activeJob.started_at).toLocaleTimeString()}
          </span>
        )}
        {activeJob?.completed_at && (
          <span style={{ color: 'var(--text-secondary)' }}>
            Completed: {new Date(activeJob.completed_at).toLocaleTimeString()}
          </span>
        )}
      </div>
    </div>
  );
}
