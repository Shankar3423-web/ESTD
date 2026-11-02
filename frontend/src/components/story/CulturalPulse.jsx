import React from 'react';
import { Sparkles, MessageCircle, Flame } from 'lucide-react';

/**
 * Cultural Pulse & Community Vibe
 * Highlights real-time audience resonance, sentiment, and viral talking points.
 */
export default function CulturalPulse({ pulse, accentColor = '#FF20B8' }) {
  if (!pulse) return null;

  return (
    <section className="cultural-pulse-section" style={{ margin: '32px 0' }}>
      <div
        className="cultural-pulse-card"
        style={{
          borderColor: `${accentColor}44`,
          background: `linear-gradient(135deg, ${accentColor}12 0%, #10131d 55%, #0d0f17 100%)`,
          boxShadow: `0 8px 32px rgba(0, 0, 0, 0.4), inset 0 0 20px ${accentColor}08`,
        }}
      >
        <div className="cultural-pulse-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              className="cultural-pulse-icon"
              style={{
                background: `${accentColor}22`,
                color: accentColor,
              }}
            >
              <Flame size={16} />
            </div>
            <div>
              <div className="cultural-pulse-kicker" style={{ color: accentColor }}>
                AUDIENCE SENTIMENT & SOCIAL RADAR
              </div>
              <h4 className="cultural-pulse-title">
                {pulse.title || 'Community & Fan Pulse'}
              </h4>
            </div>
          </div>

          {pulse.tag && (
            <span
              className="cultural-pulse-tag"
              style={{
                borderColor: `${accentColor}55`,
                background: `${accentColor}18`,
                color: accentColor,
              }}
            >
              {pulse.tag}
            </span>
          )}
        </div>

        <div className="cultural-pulse-quote-container">
          <span className="quote-mark-icon" style={{ color: `${accentColor}44` }}>“</span>
          <p className="cultural-pulse-quote-text">
            {pulse.quote?.replace(/^["']|["']$/g, '')}
          </p>
        </div>

        <div className="cultural-pulse-footer">
          <span className="pulse-indicator-dot" style={{ background: accentColor }} />
          <span className="pulse-vibe-label">
            Consensus Sentiment: <strong style={{ color: '#ffffff' }}>{pulse.reactionType || 'Viral Consensus'}</strong>
          </span>
        </div>
      </div>
    </section>
  );
}
