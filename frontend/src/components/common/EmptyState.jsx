import React from 'react';
import { Newspaper, RotateCcw } from 'lucide-react';

export default function EmptyState({
  title = 'No Stories Found',
  description = 'There are no stories matching the current filter. Try selecting another category or resetting filters.',
  actionLabel = 'Reset Filters',
  onAction,
}) {
  return (
    <div className="state-container">
      <div
        style={{
          width: 56,
          height: 56,
          borderRadius: '50%',
          background: 'rgba(255, 255, 255, 0.05)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#94a3b8',
        }}
      >
        <Newspaper size={28} />
      </div>
      <h3 className="state-title">{title}</h3>
      <p className="state-description">{description}</p>
      {onAction && (
        <button
          onClick={onAction}
          style={{
            marginTop: 8,
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            padding: '8px 18px',
            borderRadius: 9999,
            background: '#1e2436',
            color: '#ffffff',
            fontSize: 13,
            fontWeight: 600,
            border: '1px solid rgba(255, 255, 255, 0.1)',
            cursor: 'pointer',
          }}
        >
          <RotateCcw size={14} />
          {actionLabel}
        </button>
      )}
    </div>
  );
}
