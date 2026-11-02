import React from 'react';
import {
  Sparkles,
  Zap,
  Cpu,
  Film,
  Trophy,
  TrendingUp,
  Compass,
} from 'lucide-react';

/**
 * WatchFilterBar: Precision YouTube-Style Category Chip Bar.
 * Clean, edge-aligned, zero clutter, high contrast active states.
 */
export default function WatchFilterBar({
  selectedCategory = 'all',
  onSelectCategory,
  totalVideosCount = 0,
}) {
  const categories = [
    { id: 'all', label: 'All', icon: Sparkles, color: '#00E5FF' },
    { id: 'Tech', label: 'Tech', icon: Cpu, color: '#00E5FF' },
    { id: 'Entertainment', label: 'Entertainment', icon: Film, color: '#FF20B8' },
    { id: 'Business & Finance', label: 'Business & Finance', icon: TrendingUp, color: '#A855F7' },
    { id: 'Sports', label: 'Sports', icon: Trophy, color: '#B8FF3B' },
    { id: 'Developments', label: 'Developments', icon: Compass, color: '#FFB020' },
  ];

  const isCatActive = (catId) => {
    const s = selectedCategory.toLowerCase().trim();
    const c = catId.toLowerCase().trim();
    if (s === c) return true;
    if ((s.includes('business') || s.includes('finance')) && (c.includes('business') || c.includes('finance'))) {
      return true;
    }
    return false;
  };

  return (
    <div className="watch-youtube-filter-bar">
      <div className="watch-filter-scroll-track" aria-label="Watch Categories">
        {categories.map((cat) => {
          const Icon = cat.icon;
          const isActive = isCatActive(cat.id);
          return (
            <button
              key={cat.id}
              type="button"
              className={`watch-yt-chip ${isActive ? 'active' : ''}`}
              onClick={() => onSelectCategory(cat.id)}
            >
              <Icon size={13} className="watch-yt-chip-icon" />
              <span>{cat.label}</span>
              {cat.badge && <span className="watch-yt-chip-badge">{cat.badge}</span>}
            </button>
          );
        })}
      </div>

      {totalVideosCount > 0 && (
        <div className="watch-yt-filter-stats">
          <span>{totalVideosCount} Videos</span>
        </div>
      )}
    </div>
  );
}
