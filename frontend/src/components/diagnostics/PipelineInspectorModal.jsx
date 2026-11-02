import React, { useState } from 'react';
import { X, Play, RefreshCw, Database, Cpu, HardDrive } from 'lucide-react';
import PipelineStatusBar from '../PipelineStatusBar';
import PipelineProgress from '../PipelineProgress';
import SourceStatusGrid from '../SourceStatusGrid';
import MetricsGrid from '../MetricsGrid';
import SubsystemsPanel from '../SubsystemsPanel';
import DriveHierarchyModal from '../DriveHierarchyModal';

export default function PipelineInspectorModal({
  isOpen,
  onClose,
  activeJob,
  isRunning,
  overview,
  onRunPipeline,
  onRefresh,
}) {
  const [isDriveModalOpen, setIsDriveModalOpen] = useState(false);

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 700, letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: 10 }}>
              <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#10b981' }} />
              ESTD Backend Pipeline & Subsystem Inspector
            </h2>
            <p style={{ fontSize: 12.5, color: '#94a3b8', marginTop: 4 }}>
              Real-time audit of Steps 1–8: Source Collection → Cleaning → Dedup → PostgreSQL → MCP → Gemini → Google Docs
            </p>
          </div>
          <button
            onClick={onClose}
            className="btn-icon"
            style={{ width: 32, height: 32 }}
            aria-label="Close modal"
          >
            <X size={16} />
          </button>
        </div>

        {/* Modal Controls */}
        <div style={{ padding: '16px 24px', background: '#0a0d15', borderBottom: '1px solid rgba(255,255,255,0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', gap: 10 }}>
            <button
              className="btn btn-primary"
              onClick={onRunPipeline}
              disabled={isRunning}
              style={{ fontSize: 13, padding: '7px 16px', background: '#2563eb' }}
            >
              <Play size={14} fill="#ffffff" />
              {isRunning ? 'Pipeline Executing...' : 'Trigger Pipeline (Steps 1–8)'}
            </button>
            <button
              className="btn btn-secondary"
              onClick={onRefresh}
              style={{ fontSize: 13, padding: '7px 16px' }}
            >
              <RefreshCw size={14} />
              Read-Only Refresh
            </button>
          </div>

          <button
            onClick={() => setIsDriveModalOpen(true)}
            style={{ fontSize: 12.5, color: '#60a5fa', fontWeight: 600, background: 'none', border: 'none', cursor: 'pointer' }}
          >
            View Google Drive Hierarchy →
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          {/* Runner Status Bar */}
          <PipelineStatusBar activeJob={activeJob} isRunning={isRunning} />

          {/* Visual 8-Step Pipeline */}
          <PipelineProgress
            steps={activeJob?.steps || {}}
            progress={activeJob?.progress || 0}
            currentStep={activeJob?.current_step || ''}
          />

          {/* Step 1 Source Grid */}
          <SourceStatusGrid sources={activeJob?.sources || {}} />

          {/* Pipeline Metrics */}
          <MetricsGrid metrics={activeJob?.metrics || {}} />

          {/* Subsystems Overview Panel */}
          <SubsystemsPanel
            overview={overview}
            onOpenDriveModal={() => setIsDriveModalOpen(true)}
          />
        </div>
      </div>

      {/* Embedded Google Drive Hierarchy Modal */}
      <DriveHierarchyModal
        isOpen={isDriveModalOpen}
        onClose={() => setIsDriveModalOpen(false)}
        driveData={overview.google_drive || {}}
      />
    </div>
  );
}
