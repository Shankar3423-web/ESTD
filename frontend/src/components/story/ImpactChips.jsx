import React from 'react';
import {
  DollarSign,
  Percent,
  BarChart3,
  TrendingUp,
  Globe,
  ShieldCheck,
  Layers,
  Newspaper,
  Compass,
} from 'lucide-react';

/**
 * ImpactChips: Structured Key Intelligence Indicators Dock.
 *
 * Ensures all names (Domain, Reporter, Scope) are 100% completely visible
 * without ugly '...' truncation or clipping:
 * - Row 1 (Full Width): Domain with Layers icon
 * - Row 2 (Split 2 Columns): Reporter (50%) & Scope (50%)
 */
export default function ImpactChips({ chips = [], accentColor = '#00E5FF' }) {
  if (!chips || chips.length === 0) return null;

  function getChipIcon(type, label = '') {
    const lblLower = (label || '').toLowerCase();
    if (type === 'domain' || lblLower.includes('domain')) {
      return <Layers size={11} />;
    }
    if (type === 'reporter' || lblLower.includes('reporter')) {
      return <Newspaper size={11} />;
    }
    if (type === 'scope' || lblLower.includes('scope')) {
      return <Globe size={11} />;
    }
    switch (type) {
      case 'financial':
        return <DollarSign size={11} />;
      case 'percentage':
        return <Percent size={11} />;
      case 'volume':
        return <BarChart3 size={11} />;
      case 'status':
        return <ShieldCheck size={11} />;
      default:
        return <Compass size={11} />;
    }
  }

  function formatDisplayValue(value = '') {
    if (!value) return '';
    let clean = String(value);
    if (/regional\s+and\s+international/i.test(clean)) {
      clean = 'Regional & Global';
    }
    clean = clean.replace(/\(Sports\)/i, '').replace(/\(Tech\)/i, '').replace(/\(Entertainment\)/i, '').trim();
    return clean;
  }

  // Identify specific indicator roles
  const domainChip = chips.find(
    (c) => c.type === 'domain' || (c.label || '').toLowerCase().includes('domain')
  );
  const reporterChip = chips.find(
    (c) => c.type === 'reporter' || (c.label || '').toLowerCase().includes('reporter')
  );
  const scopeChip = chips.find(
    (c) => c.type === 'scope' || (c.label || '').toLowerCase().includes('scope')
  );
  const otherChips = chips.filter(
    (c) => c !== domainChip && c !== reporterChip && c !== scopeChip
  );

  // If structured indicators exist, render the clean 2-row completely visible layout
  if (domainChip || reporterChip || scopeChip) {
    return (
      <div
        className="card-intel-dock"
        style={{
          '--dock-accent': accentColor,
          borderColor: `${accentColor}28`,
          background: `linear-gradient(180deg, ${accentColor}08 0%, rgba(18, 20, 28, 0.45) 100%)`,
        }}
      >
        {/* Row 1: Full-width Domain (Never truncated) */}
        {domainChip && (
          <div className="intel-dock-domain-row" title={`Domain: ${domainChip.value}`}>
            <div className="intel-cell-header">
              <span className="intel-cell-icon" style={{ color: accentColor }}>
                <Layers size={11} />
              </span>
              <span className="intel-cell-label">DOMAIN</span>
            </div>
            <div className="intel-cell-value-full">
              {formatDisplayValue(domainChip.value)}
            </div>
          </div>
        )}

        {/* Subtle horizontal divider */}
        {domainChip && (reporterChip || scopeChip) && (
          <div className="intel-dock-divider" style={{ backgroundColor: `${accentColor}18` }} />
        )}

        {/* Row 2: Reporter & Scope (Balanced 2-column layout) */}
        {(reporterChip || scopeChip) && (
          <div className="intel-dock-sub-row">
            {reporterChip && (
              <div className="intel-sub-cell" title={`Reporter: ${reporterChip.value}`}>
                <div className="intel-cell-header">
                  <span className="intel-cell-icon" style={{ color: accentColor }}>
                    <Newspaper size={11} />
                  </span>
                  <span className="intel-cell-label">REPORTER</span>
                </div>
                <div className="intel-cell-value-full">
                  {formatDisplayValue(reporterChip.value)}
                </div>
              </div>
            )}

            {scopeChip && (
              <div className="intel-sub-cell" title={`Scope: ${scopeChip.value}`}>
                <div className="intel-cell-header">
                  <span className="intel-cell-icon" style={{ color: accentColor }}>
                    <Globe size={11} />
                  </span>
                  <span className="intel-cell-label">SCOPE</span>
                </div>
                <div className="intel-cell-value-full">
                  {formatDisplayValue(scopeChip.value)}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Extra metric chips if present */}
        {otherChips.length > 0 && (
          <div className="intel-dock-sub-row" style={{ marginTop: 4 }}>
            {otherChips.map((chip, idx) => (
              <div key={idx} className="intel-sub-cell" title={`${chip.label}: ${chip.value}`}>
                <div className="intel-cell-header">
                  <span className="intel-cell-icon" style={{ color: accentColor }}>
                    {getChipIcon(chip.type, chip.label)}
                  </span>
                  <span className="intel-cell-label">{chip.label}</span>
                </div>
                <div className="intel-cell-value-full">
                  {formatDisplayValue(chip.value)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  // Fallback for purely numerical chips
  return (
    <div
      className="card-intel-dock"
      style={{
        '--dock-accent': accentColor,
        borderColor: `${accentColor}28`,
        background: `linear-gradient(180deg, ${accentColor}08 0%, rgba(18, 20, 28, 0.45) 100%)`,
      }}
    >
      <div className="intel-dock-sub-row">
        {chips.map((chip, idx) => (
          <div key={idx} className="intel-sub-cell" title={`${chip.label}: ${chip.value}`}>
            <div className="intel-cell-header">
              <span className="intel-cell-icon" style={{ color: accentColor }}>
                {getChipIcon(chip.type, chip.label)}
              </span>
              <span className="intel-cell-label">{chip.label}</span>
            </div>
            <div className="intel-cell-value-full">
              {formatDisplayValue(chip.value)}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
