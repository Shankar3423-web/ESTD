import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Share2,
  Bookmark,
  Heart,
  ChevronLeft,
  ChevronRight,
  Clock,
  Check,
} from 'lucide-react';
import ImageWithFallback from '../common/ImageWithFallback';
import { getCategoryMeta } from '../../constants/taxonomy';

/**
 * FeaturedNewsCarousel — A horizontally scrollable hero carousel that displays
 * one recent news story per category with a large image, title overlay,
 * source badge, and share / save / like action buttons.
 *
 * Inspired by Google News "For You" top carousel.
 */
export default function FeaturedNewsCarousel({
  stories = [],
  savedStories = [],
  onToggleSave,
}) {
  const navigate = useNavigate();
  const [activeIndex, setActiveIndex] = useState(0);
  const [liked, setLiked] = useState({});
  const [copiedId, setCopiedId] = useState(null);
  const [touchStartX, setTouchStartX] = useState(null);
  const autoPlayRef = useRef(null);
  const carouselRef = useRef(null);

  // Pick the most recent story from each category
  const featuredStories = useMemo_pickOnePerCategory(stories);

  const total = featuredStories.length;

  // Auto-play every 5s
  const resetAutoPlay = useCallback(() => {
    if (autoPlayRef.current) clearInterval(autoPlayRef.current);
    if (total <= 1) return;
    autoPlayRef.current = setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % total);
    }, 5000);
  }, [total]);

  useEffect(() => {
    resetAutoPlay();
    return () => clearInterval(autoPlayRef.current);
  }, [resetAutoPlay]);

  const goTo = (idx) => {
    setActiveIndex(idx);
    resetAutoPlay();
  };

  const goPrev = () => goTo((activeIndex - 1 + total) % total);
  const goNext = () => goTo((activeIndex + 1) % total);

  // Touch / swipe support
  const handleTouchStart = (e) => setTouchStartX(e.touches[0].clientX);
  const handleTouchEnd = (e) => {
    if (touchStartX === null) return;
    const diff = touchStartX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 50) {
      diff > 0 ? goNext() : goPrev();
    }
    setTouchStartX(null);
  };

  const handleShare = async (e, story) => {
    e.stopPropagation();
    const shareUrl = `${window.location.origin}/story/${story.id}`;
    if (navigator.share) {
      try {
        await navigator.share({ title: story.headline, url: shareUrl });
      } catch {
        copyLink(story.id, shareUrl);
      }
    } else {
      copyLink(story.id, shareUrl);
    }
  };

  const copyLink = (id, url) => {
    navigator.clipboard.writeText(url);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleLike = (e, storyId) => {
    e.stopPropagation();
    setLiked((prev) => ({ ...prev, [storyId]: !prev[storyId] }));
  };

  if (total === 0) return null;

  const current = featuredStories[activeIndex];
  const catMeta = current.categoryMeta || getCategoryMeta(current.category);
  const accentColor = catMeta?.color || '#00E5FF';
  const isSaved = savedStories.some((s) => s.id === current.id);
  const isLiked = !!liked[current.id];
  const isCopied = copiedId === current.id;

  const formattedDate = current.publishedAt
    ? formatTimeAgoShort(new Date(current.publishedAt))
    : 'Recent';

  return (
    <div
      className="featured-news-carousel"
      ref={carouselRef}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
    >
      {/* ── Slide ── */}
      <div
        className="fnc-slide"
        onClick={() => navigate(`/story/${current.id}`)}
        style={{ cursor: 'pointer' }}
      >
        {/* Background Image */}
        <div className="fnc-image-wrapper">
          <ImageWithFallback
            src={current.imageUrl}
            alt={current.headline}
            category={current.category}
            subcategory={current.subcategory}
            className="fnc-image"
            size="hero"
            priority={true}
          />
          <div className="fnc-image-gradient" />
        </div>

        {/* Content Overlay */}
        <div className="fnc-content-overlay">
          {/* Source & Timestamp Row */}
          <div className="fnc-source-row">
            <span
              className="fnc-category-badge"
              style={{
                background: accentColor,
                color: '#07080B',
                boxShadow: `0 2px 10px rgba(0, 0, 0, 0.5), 0 0 16px ${accentColor}44`,
              }}
            >
              {current.category}
            </span>
            <span className="fnc-source-name">
              {current.sourceName || 'Verified Source'}
            </span>
            <span className="fnc-timestamp">
              <Clock size={11} style={{ color: accentColor }} />
              <span>{formattedDate}</span>
            </span>
          </div>

          {/* Headline */}
          <h2 className="fnc-headline">{current.headline}</h2>

          {/* Actions Row */}
          <div className="fnc-actions-row">
            {/* Action Buttons */}
            <div className="fnc-action-buttons">
              <button
                type="button"
                className={`fnc-action-btn ${isCopied ? 'copied' : ''}`}
                onClick={(e) => handleShare(e, current)}
                title="Share"
                aria-label="Share story"
              >
                {isCopied ? <Check size={16} /> : <Share2 size={16} />}
                <span>{isCopied ? 'Copied' : 'Share'}</span>
              </button>

              <button
                type="button"
                className={`fnc-action-btn ${isSaved ? 'active' : ''}`}
                onClick={(e) => {
                  e.stopPropagation();
                  if (onToggleSave) onToggleSave(current);
                }}
                title={isSaved ? 'Unsave' : 'Save'}
                aria-label="Save story"
              >
                <Bookmark
                  size={16}
                  fill={isSaved ? '#FFB020' : 'none'}
                  color={isSaved ? '#FFB020' : 'currentColor'}
                />
                <span>{isSaved ? 'Saved' : 'Save'}</span>
              </button>

              <button
                type="button"
                className={`fnc-action-btn ${isLiked ? 'liked' : ''}`}
                onClick={(e) => handleLike(e, current.id)}
                title={isLiked ? 'Unlike' : 'Like'}
                aria-label="Like story"
              >
                <Heart
                  size={16}
                  fill={isLiked ? '#FF4757' : 'none'}
                  color={isLiked ? '#FF4757' : 'currentColor'}
                />
                <span>{isLiked ? 'Liked' : 'Like'}</span>
              </button>
            </div>

            {/* Nav Arrows */}
            {total > 1 && (
              <div className="fnc-nav-arrows">
                <button
                  type="button"
                  className="fnc-arrow-btn"
                  onClick={(e) => { e.stopPropagation(); goPrev(); }}
                  aria-label="Previous story"
                >
                  <ChevronLeft size={18} />
                </button>
                <button
                  type="button"
                  className="fnc-arrow-btn"
                  onClick={(e) => { e.stopPropagation(); goNext(); }}
                  aria-label="Next story"
                >
                  <ChevronRight size={18} />
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Dot Indicators ── */}
      {total > 1 && (
        <div className="fnc-dots">
          {featuredStories.map((s, i) => {
            const dotMeta = getCategoryMeta(s.category);
            const dotColor = dotMeta?.color || '#00E5FF';
            return (
              <button
                key={s.id}
                type="button"
                className={`fnc-dot-btn ${i === activeIndex ? 'active' : ''}`}
                onClick={(e) => { e.stopPropagation(); goTo(i); }}
                aria-label={`Go to ${s.category} story`}
                style={{
                  '--dot-color': dotColor,
                }}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}

/**
 * Picks the most recent story from each unique category.
 */
function useMemo_pickOnePerCategory(stories) {
  return React.useMemo(() => {
    if (!stories || stories.length === 0) return [];
    const seen = new Map();
    for (const story of stories) {
      const cat = story.category || 'General';
      if (!seen.has(cat)) {
        seen.set(cat, story);
      }
    }
    return Array.from(seen.values());
  }, [stories]);
}

function formatTimeAgoShort(date) {
  const seconds = Math.floor((new Date() - date) / 1000);
  if (isNaN(seconds) || seconds < 0) return 'Just now';
  if (seconds < 60) return 'Just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  if (days === 1) return '1d';
  if (days < 7) return `${days}d`;
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}
