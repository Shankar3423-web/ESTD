import React, { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Flame, ChevronLeft, ChevronRight, Clock } from 'lucide-react';
import ImageWithFallback from '../common/ImageWithFallback';
import { getCategoryMeta } from '../../constants/taxonomy';

/**
 * TrendingStrip — Horizontal scrolling strip of fast-scanning trending news cards.
 * Designed for Gen-Z instant scanning with rank indices, category accents, and smooth scroll controls.
 */
export default function TrendingStrip({ stories = [] }) {
  const navigate = useNavigate();
  const trackRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  // Curate 8-10 diverse, high-freshness stories across categories
  const trendingStories = React.useMemo(() => {
    if (!stories || stories.length === 0) return [];

    // Interleave across categories to guarantee variety
    const byCategory = {};
    for (const story of stories) {
      const cat = story.category || 'General';
      if (!byCategory[cat]) byCategory[cat] = [];
      byCategory[cat].push(story);
    }

    const categories = Object.keys(byCategory);
    const selected = [];
    const maxPerCat = 3;

    for (let i = 0; i < maxPerCat; i++) {
      for (const cat of categories) {
        if (byCategory[cat][i] && selected.length < 10) {
          selected.push(byCategory[cat][i]);
        }
      }
    }

    return selected.length > 0 ? selected : stories.slice(0, 10);
  }, [stories]);

  const checkScroll = () => {
    if (!trackRef.current) return;
    const { scrollLeft, scrollWidth, clientWidth } = trackRef.current;
    setCanScrollLeft(scrollLeft > 10);
    setCanScrollRight(scrollLeft + clientWidth < scrollWidth - 10);
  };

  useEffect(() => {
    checkScroll();
    window.addEventListener('resize', checkScroll);
    return () => window.removeEventListener('resize', checkScroll);
  }, [trendingStories]);

  const scroll = (direction) => {
    if (!trackRef.current) return;
    const scrollAmount = 380;
    trackRef.current.scrollBy({
      left: direction === 'left' ? -scrollAmount : scrollAmount,
      behavior: 'smooth',
    });
    setTimeout(checkScroll, 350);
  };

  if (trendingStories.length === 0) return null;

  return (
    <section className="trending-strip-section" aria-label="Trending Stories">
      <div className="trending-strip-header">
        <div className="trending-strip-title-group">
          <div className="trending-badge">
            <Flame size={15} className="trending-flame-icon" />
            <span>TRENDING NOW</span>
          </div>
          <span className="trending-live-indicator">
            <span className="trending-live-dot" />
            Live Updates
          </span>
        </div>

        {trendingStories.length > 3 && (
          <div className="trending-scroll-controls">
            <button
              type="button"
              className={`trending-scroll-btn ${!canScrollLeft ? 'disabled' : ''}`}
              onClick={() => scroll('left')}
              disabled={!canScrollLeft}
              aria-label="Scroll trending stories left"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              type="button"
              className={`trending-scroll-btn ${!canScrollRight ? 'disabled' : ''}`}
              onClick={() => scroll('right')}
              disabled={!canScrollRight}
              aria-label="Scroll trending stories right"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>

      <div
        className="trending-strip-track"
        ref={trackRef}
        onScroll={checkScroll}
      >
        {trendingStories.map((story, index) => {
          const catMeta = story.categoryMeta || getCategoryMeta(story.category);
          const accentColor = catMeta?.color || '#00E5FF';
          const timeAgo = formatTimeAgo(story.publishedAt);
          const rank = String(index + 1).padStart(2, '0');

          return (
            <article
              key={story.id || index}
              className="trending-card"
              onClick={() => navigate(`/story/${story.id}`)}
              style={{ '--story-accent': accentColor }}
            >
              <span className="trending-rank">{rank}</span>

              <div className="trending-thumb-wrapper">
                <ImageWithFallback
                  src={story.imageUrl}
                  alt={story.headline}
                  category={story.category}
                  subcategory={story.subcategory}
                  className="trending-thumb-img"
                  size="thumb"
                  priority={index < 4}
                />
              </div>

              <div className="trending-info">
                <div className="trending-meta-row">
                  <span
                    className="trending-cat-dot"
                    style={{ background: accentColor, boxShadow: `0 0 8px ${accentColor}` }}
                  />
                  <span className="trending-cat-name" style={{ color: accentColor }}>
                    {story.category}
                  </span>
                  <span className="trending-meta-sep">·</span>
                  <span className="trending-source-name">
                    {story.sourceName || 'Verified'}
                  </span>
                  <span className="trending-meta-sep">·</span>
                  <span className="trending-time">
                    <Clock size={10} />
                    {timeAgo}
                  </span>
                </div>

                <h3 className="trending-headline" title={story.headline}>
                  {story.headline}
                </h3>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return 'Recent';
  const seconds = Math.floor((new Date() - new Date(dateStr)) / 1000);
  if (isNaN(seconds) || seconds < 0) return 'Just now';
  if (seconds < 60) return 'Just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d`;
  return new Date(dateStr).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}
