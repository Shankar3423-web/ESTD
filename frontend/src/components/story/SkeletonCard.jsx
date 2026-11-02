import React from 'react';

/**
 * SkeletonCard - Clean dark theme skeleton loader matching the news card layout
 */
export default function SkeletonCard() {
  return (
    <div
      className="skeleton-card"
      style={{
        padding: '16px 18px',
        display: 'flex',
        flexDirection: 'column',
        gap: 12,
        borderRadius: 14,
        background: '#12141c',
        border: '1px solid rgba(255, 255, 255, 0.06)',
      }}
    >
      {/* Top Bar Shimmer */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 6 }}>
          <div className="skeleton-shimmer" style={{ width: 68, height: 18, borderRadius: 12 }} />
          <div className="skeleton-shimmer" style={{ width: 60, height: 18, borderRadius: 12 }} />
        </div>
        <div className="skeleton-shimmer" style={{ width: 50, height: 14 }} />
      </div>

      {/* Image Shimmer */}
      <div className="skeleton-shimmer" style={{ width: '100%', height: 185, borderRadius: 10 }} />

      {/* Headline Shimmer (2 lines) */}
      <div className="skeleton-shimmer" style={{ width: '92%', height: 18, marginBottom: 4 }} />
      <div className="skeleton-shimmer" style={{ width: '65%', height: 18, marginBottom: 6 }} />

      {/* Brief Shimmer (3 lines) */}
      <div className="skeleton-shimmer" style={{ width: '100%', height: 13, marginBottom: 3 }} />
      <div className="skeleton-shimmer" style={{ width: '96%', height: 13, marginBottom: 3 }} />
      <div className="skeleton-shimmer" style={{ width: '70%', height: 13 }} />

      {/* Footer Read More + 4 Actions Shimmer */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: 10,
          marginTop: 'auto',
          paddingTop: 12,
          borderTop: '1px solid rgba(255, 255, 255, 0.05)',
        }}
      >
        <div className="skeleton-shimmer" style={{ width: 95, height: 28, borderRadius: 14 }} />
        <div style={{ display: 'flex', gap: 8 }}>
          <div className="skeleton-shimmer" style={{ width: 32, height: 32, borderRadius: 6 }} />
          <div className="skeleton-shimmer" style={{ width: 32, height: 32, borderRadius: 6 }} />
          <div className="skeleton-shimmer" style={{ width: 32, height: 32, borderRadius: 6 }} />
          <div className="skeleton-shimmer" style={{ width: 32, height: 32, borderRadius: 6 }} />
        </div>
      </div>
    </div>
  );
}
