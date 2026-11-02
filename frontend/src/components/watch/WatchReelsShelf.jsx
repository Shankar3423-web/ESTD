import React, { useRef, useState, useEffect } from 'react';
import { Zap, Play, ChevronLeft, ChevronRight, ArrowRight, Flame } from 'lucide-react';
import ImageWithFallback from '../common/ImageWithFallback';
import { getCategoryMeta } from '../../constants/taxonomy';
import WatchReelPlayerModal from './WatchReelPlayerModal';

/**
 * WatchReelsShelf: YouTube Shorts / Hot News Reels Experience.
 * Supports both:
 * 1. Horizontal Shelf (inserted inside the "All" video feed)
 * 2. Full-Page Multi-Column Grid (when "Shorts / Reels" tab is selected)
 */
export default function WatchReelsShelf({
  reels = [],
  savedStories = [],
  onToggleSave,
  onViewAll,
  isFullGrid = false,
}) {
  const trackRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  // Active Reel Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [activeReelIndex, setActiveReelIndex] = useState(0);

  const checkScroll = () => {
    if (trackRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = trackRef.current;
      setCanScrollLeft(scrollLeft > 10);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
    }
  };

  useEffect(() => {
    if (!isFullGrid) {
      checkScroll();
      window.addEventListener('resize', checkScroll);
      return () => window.removeEventListener('resize', checkScroll);
    }
  }, [reels, isFullGrid]);

  const scroll = (direction) => {
    if (trackRef.current) {
      const amount = 380;
      trackRef.current.scrollBy({
        left: direction === 'left' ? -amount : amount,
        behavior: 'smooth',
      });
      setTimeout(checkScroll, 350);
    }
  };

  if (!reels || reels.length === 0) return null;

  const handleOpenReel = (idx) => {
    setActiveReelIndex(idx);
    setModalOpen(true);
  };

  const renderReelCard = (item, idx) => {
    const catMeta = item.categoryMeta || getCategoryMeta(item.category);
    const accentColor = catMeta?.color || '#FF20B8';
    const duration = item.videoRail?.[0]?.duration || '0:55';
    const views = item.videoRail?.[0]?.views || '210K';

    return (
      <div
        key={item.id || idx}
        className="watch-reel-card-9-16"
        onClick={() => handleOpenReel(idx)}
        style={{ '--reel-color': accentColor }}
      >
        {/* Poster Image */}
        <div className="watch-reel-poster-wrap">
          <ImageWithFallback
            src={item.imageUrl}
            alt={item.headline}
            category={item.category}
            subcategory={item.subcategory}
          />

          {/* Dark Gradient Overlay */}
          <div className="watch-reel-gradient-overlay" />

          {/* Top Duration & Audio Pulse */}
          <div className="watch-reel-top-row">
            <span className="watch-reel-duration-badge">{duration}</span>
            <div className="watch-reel-audio-wave">
              <span className="wave-bar bar-1" />
              <span className="wave-bar bar-2" />
              <span className="wave-bar bar-3" />
            </div>
          </div>

          {/* Center Hover Play Icon */}
          <div className="watch-reel-center-play">
            <Play size={22} fill="#ffffff" color="#ffffff" className="play-icon-offset" />
          </div>

          {/* Bottom Content Info */}
          <div className="watch-reel-bottom-info">
            <span className="watch-reel-category-pill" style={{ color: accentColor }}>
              {item.category}
            </span>
            <h4 className="watch-reel-card-title">{item.headline}</h4>
            <div className="watch-reel-stats-row">
              <span className="watch-reel-views-label">{views} views</span>
              <span className="watch-reel-dot">•</span>
              <span className="watch-reel-source-label">{item.sourceName}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <section
      className={`watch-reels-shelf-section ${isFullGrid ? 'full-grid-mode' : ''}`}
      aria-label="News Reels and Shorts"
    >
      {/* Header */}
      <div className="watch-shelf-header">
        <div className="watch-shelf-title-group">
          <div className="watch-shelf-title-row">
            <span className="watch-reels-icon-pill">
              <Flame size={14} className="watch-zap-anim" />
              <span>SHORTS & HOT REELS</span>
            </span>
            <span className="watch-shorts-count-badge">{reels.length} Reels</span>
          </div>
          <span className="watch-shelf-tagline">
            Vertical 60s micro-video bites with rapid 3-bullet Smart Brevity takeaways
          </span>
        </div>

        {/* Right Controls: View All Link or Scroll Arrows */}
        <div className="watch-shelf-actions-group">
          {!isFullGrid && onViewAll && (
            <button
              type="button"
              className="watch-shelf-explore-link"
              onClick={onViewAll}
            >
              <span>View All Shorts</span>
              <ArrowRight size={14} />
            </button>
          )}

          {!isFullGrid && (
            <div className="watch-shelf-nav-arrows">
              <button
                type="button"
                className={`watch-shelf-arrow-btn ${!canScrollLeft ? 'disabled' : ''}`}
                onClick={() => scroll('left')}
                disabled={!canScrollLeft}
                aria-label="Scroll reels left"
              >
                <ChevronLeft size={16} />
              </button>
              <button
                type="button"
                className={`watch-shelf-arrow-btn ${!canScrollRight ? 'disabled' : ''}`}
                onClick={() => scroll('right')}
                disabled={!canScrollRight}
                aria-label="Scroll reels right"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Render either Horizontal Scroll Track or Full-Page Grid */}
      {isFullGrid ? (
        <div className="watch-reels-full-grid">
          {reels.map((item, idx) => renderReelCard(item, idx))}
        </div>
      ) : (
        <div
          ref={trackRef}
          className="watch-reels-track"
          onScroll={checkScroll}
        >
          {reels.map((item, idx) => renderReelCard(item, idx))}
        </div>
      )}

      {/* Full-Screen Swipeable Reels Player Modal */}
      <WatchReelPlayerModal
        isOpen={modalOpen}
        reels={reels}
        initialIndex={activeReelIndex}
        onClose={() => setModalOpen(false)}
        savedStories={savedStories}
        onToggleSave={onToggleSave}
      />
    </section>
  );
}
