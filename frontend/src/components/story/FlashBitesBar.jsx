import React, { useRef, useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Zap,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import ImageWithFallback from '../common/ImageWithFallback';
import { getCategoryMeta } from '../../constants/taxonomy';
import FlashBiteModal from './FlashBiteModal';
import {
  generateSmartBrevityBullets,
  formatCleanHeadline,
  formatCleanTopicName,
} from '../../utils/flashBitesUtils';

export { generateSmartBrevityBullets, formatCleanHeadline, formatCleanTopicName };

/**
 * FlashBitesBar — Gen-Z oriented 60-Second Flash Story Rings with full-screen interactive micro-reader.
 */
export default function FlashBitesBar({ stories = [] }) {
  const navigate = useNavigate();
  const trackRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  // Active Story in Flash Modal
  const [activeStoryIndex, setActiveStoryIndex] = useState(null);

  // Pick top 8 diverse stories across categories for flash bites
  const flashStories = useMemo(() => {
    if (!stories || stories.length === 0) return [];

    const byCat = {};
    for (const s of stories) {
      const cat = s.category || 'Tech';
      if (!byCat[cat]) byCat[cat] = [];
      byCat[cat].push(s);
    }

    const result = [];
    const categories = Object.keys(byCat);
    for (let round = 0; round < 2; round++) {
      for (const cat of categories) {
        if (byCat[cat][round] && result.length < 8) {
          result.push(byCat[cat][round]);
        }
      }
    }
    return result.length > 0 ? result : stories.slice(0, 8);
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
  }, [flashStories]);

  const scroll = (direction) => {
    if (!trackRef.current) return;
    const amount = 360;
    trackRef.current.scrollBy({
      left: direction === 'left' ? -amount : amount,
      behavior: 'smooth',
    });
    setTimeout(checkScroll, 350);
  };

  if (!flashStories || flashStories.length === 0) return null;

  return (
    <section className="flash-bites-section" aria-label="60-Second Flash Bites">
      {/* Header Pill & Brevity Tagline */}
      <div className="flash-bites-header">
        <div className="flash-bites-title-group">
          <span className="flash-bites-pill">
            <Zap size={13} className="flash-bites-zap-icon" />
            <span>60s FLASH BITES</span>
          </span>
          <span className="flash-bites-tagline">
            Tap any ring for rapid 3-bullet smart brevity
          </span>
        </div>

        {flashStories.length > 5 && (
          <div className="flash-bites-arrows">
            <button
              type="button"
              className={`flash-bites-arrow-btn ${!canScrollLeft ? 'disabled' : ''}`}
              onClick={() => scroll('left')}
              disabled={!canScrollLeft}
              aria-label="Scroll flash bites left"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              type="button"
              className={`flash-bites-arrow-btn ${!canScrollRight ? 'disabled' : ''}`}
              onClick={() => scroll('right')}
              disabled={!canScrollRight}
              aria-label="Scroll flash bites right"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        )}
      </div>

      {/* Story Rings Horizontal Rail */}
      <div className="flash-bites-track" ref={trackRef} onScroll={checkScroll}>
        {flashStories.map((story, index) => {
          const meta = getCategoryMeta(story.category);
          const color = meta?.color || '#00E5FF';
          const cleanTopic = formatCleanTopicName(story);
          const cleanHeadline = formatCleanHeadline(story);

          return (
            <button
              key={story.id}
              type="button"
              className="flash-ring-item"
              onClick={() => setActiveStoryIndex(index)}
              style={{ '--ring-accent': color }}
              aria-label={`Open 60-second bite: ${cleanHeadline}`}
            >
              {/* Outer Glowing Story Ring */}
              <div className="flash-ring-wrapper">
                <div className="flash-ring-glow" />
                <div className="flash-ring-inner">
                  <ImageWithFallback
                    src={story.imageUrl}
                    alt={cleanHeadline}
                    category={story.category}
                    subcategory={story.subcategory}
                    className="flash-ring-avatar"
                    size="thumb"
                  />
                </div>
                <span className="flash-ring-pulse-badge">
                  <Zap size={10} />
                </span>
              </div>

              {/* Title & Clear Complete Category Badge */}
              <div className="flash-ring-text">
                <span
                  className="flash-ring-category-badge"
                  style={{
                    backgroundColor: 'rgba(12, 16, 26, 0.85)',
                    borderColor: `${color}66`,
                    color: color,
                    boxShadow: `0 2px 8px rgba(0, 0, 0, 0.5), inset 0 0 8px ${color}22`,
                  }}
                >
                  {cleanTopic}
                </span>
                <span className="flash-ring-headline" title={cleanHeadline}>
                  {cleanHeadline}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Full-Screen / Modal Story Viewer */}
      <FlashBiteModal
        isOpen={activeStoryIndex !== null}
        story={activeStoryIndex !== null ? flashStories[activeStoryIndex] : null}
        stories={flashStories}
        initialIndex={activeStoryIndex ?? 0}
        onClose={() => setActiveStoryIndex(null)}
      />
    </section>
  );
}
