import React from 'react';
import { Play, RotateCw, Sparkles, Loader2 } from 'lucide-react';

export default function Header({
  isRunning,
  onRunPipeline,
  onRefreshResults,
  isRefreshing,
}) {
  return (
    <header className="dashboard-header">
      <div className="header-title-group">
        <h1>
          <Sparkles className="text-blue-400" size={28} />
          ESTD — News Intelligence Pipeline
        </h1>
        <p>End-to-End Backend Pipeline Verification Dashboard</p>
      </div>

      <div className="header-actions">
        <button
          className="btn btn-secondary"
          onClick={onRefreshResults}
          disabled={isRefreshing || isRunning}
          title="Query existing backend results without re-fetching news"
        >
          {isRefreshing ? (
            <Loader2 className="animate-spin" size={16} />
          ) : (
            <RotateCw size={16} />
          )}
          Refresh Results
        </button>

        <button
          className="btn btn-primary"
          onClick={onRunPipeline}
          disabled={isRunning}
          title="Execute the full end-to-end backend pipeline (Steps 1–8)"
        >
          {isRunning ? (
            <>
              <Loader2 className="animate-spin" size={16} />
              Pipeline already running...
            </>
          ) : (
            <>
              <Play size={16} fill="currentColor" />
              Fetch & Process Latest News
            </>
          )}
        </button>
      </div>
    </header>
  );
}
