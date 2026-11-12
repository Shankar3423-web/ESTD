import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Zap,
  Radio,
  ChevronRight,
  TrendingUp,
  Clock,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { fetchStories } from '../../api/estdApi';
import { getCategoryMeta } from '../../constants/taxonomy';
import { formatCleanHeadline, formatCleanTopicName } from '../../utils/flashBitesUtils';
import FlashBiteModal from '../story/FlashBiteModal';

/**
 * BreakingTickerBar — Live Platform Breaking News Intelligence Ticker Bar.
 * 
 * Features:
 * - Real-time animated ticker marquee with live signal indicator.
 * - Displays latest verified wire developments across Tech, Finance, Policy & Sports.
 * - Pauses on hover for comfortable reading and clicking.
 * - Direct click to open full article or quick 60s Flash Bite micro-reader.
 * - Collapsible state remembered in localStorage.
 */
export default function BreakingTickerBar({ onSelectStory }) {
  const navigate = useNavigate();
  const [stories, setStories] = useState(() => {
    try {
      const cached = localStorage.getItem('estd_feed_cache');
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed.slice(0, 12);
      }
    } catch {}
    return [];
  });
  const [loading, setLoading] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(() => {
    try {
      return localStorage.getItem('estd_ticker_collapsed') === 'true';
    } catch {
      return false;
    }
  });

  // Optional quick Flash Bite modal preview from ticker
  const [modalStory, setModalStory] = useState(null);

  // Fetch latest breaking stories for ticker
  useEffect(() => {
    let isMounted = true;
    async function loadTickerItems() {
      try {
        const items = await fetchStories({ limit: 12 });
        if (isMounted && items && items.length > 0) {
          setStories(items);
        }
      } catch (err) {
        console.debug('Ticker wire update notice:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadTickerItems();
    // Refresh wire headlines every 90 seconds
    const interval = setInterval(loadTickerItems, 90000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleToggleCollapse = () => {
    setIsCollapsed((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('estd_ticker_collapsed', String(next));
      } catch {}
      return next;
    });
  };

  const handleItemClick = (story) => {
    if (!story) return;
    if (onSelectStory) {
      onSelectStory(story.id);
    } else {
      navigate(`/story/${story.id}`);
    }
  };

  const handleQuickBiteClick = (e, story) => {
    e.stopPropagation();
    setModalStory(story);
  };

  // Duplicate items for continuous seamless infinite loop
  const tickerItems = useMemo(() => {
    if (!stories || stories.length === 0) return [];
    // Duplicate 2x for smooth CSS continuous scroll
    return [...stories, ...stories];
  }, [stories]);

  if (loading && stories.length === 0) {
    return null;
  }

  if (stories.length === 0) {
    return null;
  }

  return (
    <>
      <div className={`breaking-ticker-bar ${isCollapsed ? 'collapsed' : ''}`}>
        {/* Left Live Badge Anchor */}
        <div className="ticker-live-badge-wrapper">
          <div className="ticker-live-dot-pulse" />
          <Radio size={12} className="ticker-live-icon" />
          <span className="ticker-live-text">LIVE WIRE</span>
        </div>

        {/* Marquee Scroller Area */}
        {!isCollapsed ? (
          <div className="ticker-track-container">
            <div className="ticker-marquee-track">
              {tickerItems.map((story, idx) => {
                const meta = getCategoryMeta(story.category);
                const accent = meta?.color || '#00E5FF';
                const topic = formatCleanTopicName(story);
                const headline = formatCleanHeadline(story);

                return (
                  <div
                    key={`${story.id}-${idx}`}
                    className="ticker-item"
                    onClick={() => handleItemClick(story)}
                    title={`Click to read: ${headline}`}
                  >
                    <span
                      className="ticker-item-cat-badge"
                      style={{
                        color: accent,
                        borderColor: `${accent}44`,
                        backgroundColor: `${accent}14`,
                      }}
                    >
                      {topic}
                    </span>

                    <span className="ticker-item-headline">
                      {headline}
                    </span>

                    <button
                      type="button"
                      className="ticker-item-bite-btn"
                      onClick={(e) => handleQuickBiteClick(e, story)}
                      title="Preview 60s Flash Deck"
                    >
                      <Zap size={10} />
                      <span>60s</span>
                    </button>

                    <span className="ticker-item-divider">•</span>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="ticker-collapsed-summary">
            <span className="ticker-collapsed-text">
              {stories.length} breaking intelligence developments active
            </span>
          </div>
        )}

        {/* Collapse / Expand Toggle Button */}
        <button
          type="button"
          className="ticker-toggle-btn"
          onClick={handleToggleCollapse}
          title={isCollapsed ? 'Expand Live Wire Ticker' : 'Minimize Live Wire Ticker'}
          aria-label={isCollapsed ? 'Expand Ticker' : 'Collapse Ticker'}
        >
          {isCollapsed ? <ChevronDown size={14} /> : <ChevronUp size={14} />}
        </button>
      </div>

      {/* Quick 60s Flash Bite preview when opened from ticker */}
      {modalStory && (
        <FlashBiteModal
          isOpen={true}
          story={modalStory}
          stories={stories}
          initialIndex={stories.findIndex((s) => String(s.id) === String(modalStory.id))}
          onClose={() => setModalStory(null)}
        />
      )}
    </>
  );
}

