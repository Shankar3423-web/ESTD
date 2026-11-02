import React, { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronLeft, ChevronRight, ArrowRight } from 'lucide-react';
import WatchVideoCard from './WatchVideoCard';

/**
 * WatchCategoryRail: Horizontal scrolling video shelf for ESTD categories & perspective channels.
 */
export default function WatchCategoryRail({
  title,
  subtitle,
  categorySlug,
  accentColor = '#00E5FF',
  icon: Icon,
  badgeText,
  stories = [],
  savedStories = [],
  onToggleSave,
}) {
  const navigate = useNavigate();
  const trackRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  const checkScroll = () => {
    if (trackRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = trackRef.current;
      setCanScrollLeft(scrollLeft > 10);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
    }
  };

  useEffect(() => {
    checkScroll();
    window.addEventListener('resize', checkScroll);
    return () => window.removeEventListener('resize', checkScroll);
  }, [stories]);

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

  if (!stories || stories.length === 0) return null;

  const handlePlayStory = (story) => {
    if (story?.id) {
      navigate(`/watch/${story.id}`);
    }
  };

  return (
    <section className="watch-category-shelf-section" aria-label={title}>
      {/* Shelf Header */}
      <div className="watch-shelf-header">
        <div className="watch-shelf-title-group">
          <div className="watch-shelf-title-row">
            {Icon && <Icon size={18} style={{ color: accentColor }} />}
            <h3 className="watch-shelf-main-title">{title}</h3>
            {badgeText && (
              <span className="watch-shelf-badge" style={{ borderColor: accentColor, color: accentColor }}>
                {badgeText}
              </span>
            )}
          </div>
          {subtitle && <p className="watch-shelf-subtitle">{subtitle}</p>}
        </div>

        {/* Right Controls: See All Link + Scroll Arrows */}
        <div className="watch-shelf-actions-group">
          {categorySlug && (
            <button
              type="button"
              className="watch-shelf-explore-link"
              onClick={() => navigate(`/category/${categorySlug}`)}
            >
              <span>Explore</span>
              <ArrowRight size={13} />
            </button>
          )}

          <div className="watch-shelf-nav-arrows">
            <button
              type="button"
              className={`watch-shelf-arrow-btn ${!canScrollLeft ? 'disabled' : ''}`}
              onClick={() => scroll('left')}
              disabled={!canScrollLeft}
              aria-label="Scroll left"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              type="button"
              className={`watch-shelf-arrow-btn ${!canScrollRight ? 'disabled' : ''}`}
              onClick={() => scroll('right')}
              disabled={!canScrollRight}
              aria-label="Scroll right"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* Horizontal Track of 16:9 Cards */}
      <div
        ref={trackRef}
        className="watch-category-track"
        onScroll={checkScroll}
      >
        {stories.map((story) => {
          const video = story.videoRail?.[0] || {};
          const isSaved = savedStories.some((s) => String(s.id) === String(story.id));
          return (
            <div key={story.id} className="watch-category-card-slide">
              <WatchVideoCard
                video={video}
                story={story}
                onPlay={() => handlePlayStory(story)}
                onToggleSave={onToggleSave}
                isSaved={isSaved}
              />
            </div>
          );
        })}
      </div>
    </section>
  );
}

