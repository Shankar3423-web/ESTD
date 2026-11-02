import React from 'react';
import { Clock, CheckCircle2, ChevronRight, Sparkles } from 'lucide-react';

/**
 * Context in Four Beats (Story Arc)
 * Visualizes the 4 essential narrative beats (Origin, Catalyst, Development, Horizon)
 * Clean, structured, and skimmable for modern readers.
 */
export default function ContextTimeline({ beats = [], accentColor = '#00E5FF' }) {
  if (!beats || beats.length === 0) return null;

  // Defensive cleaning for beat details to ensure zero ASCII banners or URLs
  const cleanDetail = (text) => {
    if (!text) return '';
    return text
      .replace(/ESTD NEWS INTELLIGENCE[^\n]*\n[=]+\n.*?Canonical Reference:[^\n]*\n/gis, '')
      .replace(/https?:\/\/[^\s]+/g, '')
      .replace(/[=]{3,}/g, '')
      .replace(/[-]{3,}/g, '')
      .replace(/\b\d+\.\s+[A-Z\s&]+\b/g, '')
      .replace(/•[^\n]+/g, '')
      .replace(/ESTD News Intelligence Platform[^\n]*/gi, '')
      .replace(/\s+/g, ' ')
      .trim();
  };

  return (
    <section className="timeline-beats-section" style={{ margin: '36px 0' }}>
      <div className="timeline-header-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            className="timeline-header-icon"
            style={{
              background: `${accentColor}18`,
              borderColor: `${accentColor}44`,
              color: accentColor,
            }}
          >
            <Clock size={16} />
          </div>
          <div>
            <div className="timeline-section-kicker" style={{ color: accentColor }}>
              STORY ARC & VERIFIED TIMELINE
            </div>
            <h3 className="timeline-section-title">
              Context in Four Beats
            </h3>
          </div>
        </div>
        <div className="timeline-beats-badge" style={{ borderColor: `${accentColor}33`, color: accentColor }}>
          <Sparkles size={12} />
          <span>4 Critical Milestones</span>
        </div>
      </div>

      <div className="timeline-beats-container">
        {beats.map((beat, idx) => {
          const phaseStr = beat.phase || `0${idx + 1}`;
          const detail = cleanDetail(beat.detail);

          return (
            <div key={beat.beat || idx} className="timeline-beat-card">
              <div className="beat-indicator-col">
                <div
                  className="beat-number"
                  style={{
                    color: accentColor,
                    borderColor: `${accentColor}55`,
                    background: `${accentColor}14`,
                    boxShadow: `0 0 16px ${accentColor}22`,
                  }}
                >
                  {phaseStr}
                </div>
                {idx < beats.length - 1 && (
                  <div
                    className="beat-connecting-line"
                    style={{
                      background: `linear-gradient(to bottom, ${accentColor}66, rgba(255,255,255,0.06))`,
                    }}
                  />
                )}
              </div>

              <div className="beat-content-card">
                <div className="beat-card-header">
                  <h4 className="beat-card-title">{beat.title}</h4>
                  <span className="beat-phase-tag" style={{ color: accentColor }}>
                    Phase {idx + 1}
                  </span>
                </div>
                <p className="beat-card-detail">{detail}</p>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
