import React from 'react';
import { AlertTriangle, RotateCcw } from 'lucide-react';

export default function ErrorState({
  title = 'Unable to Load Stories',
  error = 'A network or server error occurred while retrieving stories from the ESTD backend.',
  onRetry,
}) {
  return (
    <div
      className="state-container"
      style={{
        borderColor: 'rgba(239, 68, 68, 0.3)',
        background: 'rgba(239, 68, 68, 0.04)',
      }}
    >
      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: '50%',
          background: 'rgba(239, 68, 68, 0.12)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#f87171',
        }}
      >
        <AlertTriangle size={28} />
      </div>
      <h3 className="state-title" style={{ color: '#fca5a5' }}>
        {title}
      </h3>
      <p className="state-description" style={{ color: '#f87171' }}>
        {typeof error === 'string' ? error : error?.message || 'Unexpected backend error.'}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            marginTop: 8,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 20px',
            borderRadius: 9999,
            background: 'rgba(239, 68, 68, 0.2)',
            color: '#fca5a5',
            fontSize: 13,
            fontWeight: 600,
            border: '1px solid rgba(239, 68, 68, 0.4)',
            cursor: 'pointer',
          }}
        >
          <RotateCcw size={14} />
          Retry Connection
        </button>
      )}
    </div>
  );
}
