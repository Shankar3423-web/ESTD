import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import BreakingTickerBar from '../common/BreakingTickerBar';
import PipelineInspectorModal from '../diagnostics/PipelineInspectorModal';
import {
  runPipeline,
  getJobStatus,
  getLatestJob,
  getPipelineStatus,
  getSystemOverview,
} from '../../api/pipelineApi';

export default function AppShell({ savedStories, onToggleSave, onListen }) {
  const location = useLocation();
  const [isDiagnosticsOpen, setIsDiagnosticsOpen] = useState(false);
  const [activeJob, setActiveJob] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [overview, setOverview] = useState({});
  const [feedMode, setFeedMode] = useState(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const f = params.get('feed');
      return f === 'following' ? 'following' : 'latest';
    } catch {
      return 'latest';
    }
  });
  const pollIntervalRef = useRef(null);

  // Sync feed mode if search param changes
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const feed = params.get('feed');
    if (feed === 'following' || feed === 'latest') {
      setFeedMode(feed);
    }
  }, [location.search]);

  // Load system overview
  const loadOverview = useCallback(async () => {
    try {
      const data = await getSystemOverview();
      setOverview(data || {});
    } catch (err) {
      console.warn('System overview check notice:', err);
    }
  }, []);

  // Poll pipeline job if running
  const startPollingJob = useCallback(
    (jobId) => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = setInterval(async () => {
        try {
          const job = await getJobStatus(jobId);
          setActiveJob(job);
          if (job.status === 'COMPLETED' || job.status === 'FAILED') {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
            setIsRunning(false);
            loadOverview();
          }
        } catch (err) {
          console.error('Job polling error:', err);
        }
      }, 1500);
    },
    [loadOverview]
  );

  // Initial startup: check pipeline runner state & system overview (deferred to avoid competing with initial feed load)
  useEffect(() => {
    const timer = setTimeout(() => {
      loadOverview();
      async function checkStatus() {
        try {
          const res = await getPipelineStatus();
          if (res.is_running && res.active_job_id) {
            setIsRunning(true);
            startPollingJob(res.active_job_id);
          } else if (res.last_job) {
            setActiveJob(res.last_job);
          }
        } catch (err) {
          console.debug('Initial status notice:', err);
        }
      }
      checkStatus();
    }, 2500);

    return () => {
      clearTimeout(timer);
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, [loadOverview, startPollingJob]);

  // Handler for triggering real pipeline execution
  const handleRunPipeline = async () => {
    if (isRunning) return;
    setIsRunning(true);
    try {
      const resp = await runPipeline({ target_per_category: 1 });
      if (resp.job_id) {
        startPollingJob(resp.job_id);
      }
    } catch (err) {
      setIsRunning(false);
      alert(`Pipeline execution error: ${err.message}`);
    }
  };

  // Handler for read-only refresh
  const handleRefresh = async () => {
    await loadOverview();
    try {
      const latest = await getLatestJob();
      if (latest) setActiveJob(latest);
    } catch (e) {
      // ignore
    }
  };

  return (
    <div className="app-shell">
      {/* Persistent Left Sidebar */}
      <Sidebar
        onOpenDiagnostics={() => setIsDiagnosticsOpen(true)}
        systemStatus={overview}
      />

      {/* Main Container */}
      <div className="app-main">
        {/* Top Navigation Bar */}
        <TopBar
          feedMode={feedMode}
          onFeedModeChange={setFeedMode}
          onOpenDiagnostics={() => setIsDiagnosticsOpen(true)}
          systemOverview={overview}
        />

        {/* The Live page has its own ticker, so show the shared wire elsewhere only. */}
        {location.pathname.replace(/\/+$/, '') !== '/live' && <BreakingTickerBar />}

        {/* Content Viewport */}
        <main className="content-viewport" id="main-content">
          <React.Suspense
            fallback={
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  minHeight: '45vh',
                  color: '#64748B',
                  fontSize: '12px',
                  fontWeight: 600,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  gap: '12px',
                }}
              >
                <div
                  style={{
                    width: 20,
                    height: 20,
                    border: '2px solid rgba(0, 229, 255, 0.2)',
                    borderTopColor: '#00E5FF',
                    borderRadius: '50%',
                    animation: 'spin 0.6s linear infinite',
                  }}
                />
                <span>Loading ESTD Desk...</span>
              </div>
            }
          >
            <Outlet context={{ feedMode, onOpenDiagnostics: () => setIsDiagnosticsOpen(true) }} />
          </React.Suspense>
        </main>
      </div>

      {/* Pipeline Verification Inspector Modal */}
      {isDiagnosticsOpen && (
        <PipelineInspectorModal
          isOpen={isDiagnosticsOpen}
          onClose={() => setIsDiagnosticsOpen(false)}
          activeJob={activeJob}
          isRunning={isRunning}
          overview={overview}
          onRunPipeline={handleRunPipeline}
          onRefresh={handleRefresh}
        />
      )}
    </div>
  );
}
