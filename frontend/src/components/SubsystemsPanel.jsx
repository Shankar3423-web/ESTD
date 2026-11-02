import React from 'react';
import {
  Database,
  Cpu,
  Bot,
  Cloud,
  Clock,
  ExternalLink,
  ShieldCheck,
} from 'lucide-react';

export default function SubsystemsPanel({ overview = {}, onOpenDriveModal }) {
  const pg = overview.postgres || {};
  const mcp = overview.mcp || {};
  const gemini = overview.gemini || {};
  const drive = overview.google_drive || {};
  const lastRun = overview.last_run || {};

  return (
    <div className="dashboard-section">
      <div className="section-header">
        <div className="section-title">
          <ShieldCheck size={18} />
          ESTD Subsystems & Backend Integrations
        </div>
      </div>

      <div className="subsystems-grid">
        {/* 1. PostgreSQL Knowledge Source (Section 17) */}
        <div className="subsystem-card">
          <div className="subsystem-header">
            <div className="subsystem-title">
              <Database size={16} color="#34d399" />
              PostgreSQL Knowledge Source
            </div>
            <span className="subsystem-status-badge">✓ {pg.status || 'CONNECTED'}</span>
          </div>
          <div className="subsystem-meta">
            <div>Status: <strong style={{ color: '#34d399' }}>✓ Connected / Available</strong></div>
            <div>Articles Stored: <strong style={{ color: '#fff' }}>{pg.articles_stored ?? 0}</strong></div>
            <div>Database: <strong>{pg.database_name || 'estd_knowledge'}</strong> (Port: {pg.port || 5433})</div>
          </div>
        </div>

        {/* 2. MCP Access Layer (Section 18) */}
        <div className="subsystem-card">
          <div className="subsystem-header">
            <div className="subsystem-title">
              <Cpu size={16} color="#60a5fa" />
              MCP Access Layer
            </div>
            <span className="subsystem-status-badge">✓ {mcp.status || 'OPERATIONAL'}</span>
          </div>
          <div className="subsystem-meta">
            <div>Status: <strong style={{ color: '#34d399' }}>✓ Operational</strong></div>
            <div>Knowledge Source: <strong>{mcp.knowledge_source || 'PostgreSQL'}</strong></div>
            <div style={{ color: 'var(--text-secondary)', fontSize: 11, marginTop: 4 }}>
              <strong>Purpose:</strong> MCP provides controlled access to the ESTD knowledge source for AI processing.
            </div>
          </div>
        </div>

        {/* 3. AI Processing / Gemini (Section 19) */}
        <div className="subsystem-card">
          <div className="subsystem-header">
            <div className="subsystem-title">
              <Bot size={16} color="#c084fc" />
              AI Processing (Gemini)
            </div>
            <span className="subsystem-status-badge">✓ {gemini.status || 'CONNECTED'}</span>
          </div>
          <div className="subsystem-meta">
            <div>Gemini: <strong style={{ color: '#34d399' }}>✓ Connected</strong></div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6, marginTop: 4, background: 'rgba(0,0,0,0.2)', padding: '6px 8px', borderRadius: 6 }}>
              <div>Generated: <strong style={{ color: '#c084fc' }}>{gemini.generated ?? 0}</strong></div>
              <div>Validated: <strong style={{ color: '#34d399' }}>{gemini.validated ?? 0}</strong></div>
              <div>Failed: <strong style={{ color: gemini.failed ? '#f87171' : '#94a3b8' }}>{gemini.failed ?? 0}</strong></div>
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
              Model: {gemini.model || 'gemini-2.5-flash'} (Temp: {gemini.temperature || '0.2'})
            </div>
          </div>
        </div>

        {/* 4. Google Drive Output (Section 16) */}
        <div className="subsystem-card">
          <div className="subsystem-header">
            <div className="subsystem-title">
              <Cloud size={16} color="#38bdf8" />
              Google Drive Output
            </div>
            <span className="subsystem-status-badge">✓ {drive.status || 'CONNECTED'}</span>
          </div>
          <div className="subsystem-meta">
            <div className="tree-view" style={{ fontSize: 11, padding: 8, margin: '2px 0' }}>
              <strong>ESTD CONTENT</strong><br />
              ├── Artificial Intelligence<br />
              ├── Technology<br />
              ├── Business<br />
              ├── Education<br />
              └── Science
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
              <span>Documents Created: <strong style={{ color: '#34d399' }}>{drive.documents_created ?? 0}</strong></span>
              <span>Documents Failed: <strong style={{ color: drive.documents_failed ? '#f87171' : '#94a3b8' }}>{drive.documents_failed ?? 0}</strong></span>
            </div>
          </div>
        </div>

        {/* 5. Last Pipeline Run (Section 20) */}
        <div className="subsystem-card">
          <div className="subsystem-header">
            <div className="subsystem-title">
              <Clock size={16} color="#f59e0b" />
              Last Pipeline Run
            </div>
            <span
              className="subsystem-status-badge"
              style={{
                background:
                  lastRun.status === 'COMPLETED'
                    ? 'rgba(16, 185, 129, 0.15)'
                    : lastRun.status === 'RUNNING'
                    ? 'rgba(59, 130, 246, 0.15)'
                    : 'rgba(245, 158, 11, 0.15)',
                color:
                  lastRun.status === 'COMPLETED'
                    ? '#34d399'
                    : lastRun.status === 'RUNNING'
                    ? '#60a5fa'
                    : '#fcd34d',
              }}
            >
              {lastRun.status || 'IDLE'}
            </span>
          </div>
          <div className="subsystem-meta">
            {lastRun.status === 'RUNNING' && (
              <div>Current Step: <strong style={{ color: '#60a5fa' }}>{lastRun.current_step}</strong></div>
            )}
            <div>Job ID: <strong className="mono">{lastRun.job_id || 'None yet'}</strong></div>
            <div>
              Started: <strong>{lastRun.started_at ? new Date(lastRun.started_at).toLocaleTimeString() : 'N/A'}</strong>
            </div>
            <div>
              Completed: <strong>{lastRun.completed_at ? new Date(lastRun.completed_at).toLocaleTimeString() : 'N/A'}</strong>
            </div>
            <div>
              Duration: <strong>{lastRun.duration_seconds ? `${lastRun.duration_seconds}s` : 'N/A'}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 2 }}>
              <span>Articles Processed: <strong style={{ color: '#fff' }}>{lastRun.metrics?.fetched ?? 0}</strong></span>
              <span>Documents Created: <strong style={{ color: '#34d399' }}>{lastRun.metrics?.docs_created ?? 0}</strong></span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
