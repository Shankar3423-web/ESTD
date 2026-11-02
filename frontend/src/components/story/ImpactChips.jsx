import React from 'react';
import { DollarSign, Percent, BarChart3, TrendingUp, Globe, ShieldCheck } from 'lucide-react';

/**
 * Renders measurable, factual impact metrics extracted from verified source content.
 * Only displays numbers grounded in source; omits when empty.
 */
export default function ImpactChips({ chips = [], accentColor = '#00E5FF' }) {
  if (!chips || chips.length === 0) return null;

  function getChipIcon(type) {
    switch (type) {
      case 'financial':
        return <DollarSign size={13} />;
      case 'percentage':
        return <Percent size={13} />;
      case 'volume':
        return <BarChart3 size={13} />;
      case 'domain':
        return <Globe size={13} />;
      case 'status':
        return <ShieldCheck size={13} />;
      default:
        return <TrendingUp size={13} />;
    }
  }

  return (
    <div className="impact-chips-row">
      {chips.map((chip, idx) => (
        <div
          key={idx}
          className="impact-chip"
          style={{
            borderColor: `${accentColor}33`,
            background: `${accentColor}0D`,
          }}
        >
          <span style={{ color: accentColor, display: 'flex', alignItems: 'center' }}>
            {getChipIcon(chip.type)}
          </span>
          <span className="impact-chip-label">{chip.label}:</span>
          <span className="impact-chip-value" style={{ color: accentColor }}>
            {chip.value}
          </span>
        </div>
      ))}
    </div>
  );
}
