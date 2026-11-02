import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Share2,
  Bookmark,
  Heart,
  ChevronLeft,
  ChevronRight,
  Clock,
  Check,
  Play,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import ImageWithFallback from '../common/ImageWithFallback';
import { toggleStoryLike } from '../../api/estdApi';

/**
 * Format timestamp into short relative or human-readable format.
 */
function formatTimeAgoShort(date) {
  if (!date || isNaN(date.getTime())) return 'Recent';
  const now = new Date();
  const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);
  if (diffSec < 60) return 'Just now';
  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDays = Math.floor(diffHr / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

/**
 * CategoryHeroCarousel — Large cinematic hero showcase featuring the top 4-5
 * recent verified stories of an individual category with smooth normal auto-advance,
 * swipe support, and direct actions.
 */
export default function CategoryHeroCarousel({
  stories = [],
  categoryMeta,
  savedStories = [],
  onToggleSave,
  onWatchVideo,
}) {
  const navigate = useNavigate();
  // Limit to top 4 to 5 most recent stories
  const heroStories = stories.slice(0, 5);
  const total = heroStories.length;

  const [activeIndex, setActiveIndex] = useState(0);
  const [liked, setLiked] = useState(() => {
    try {
      const stored = localStorage.getItem('estd_liked_stories');
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  });
  const [copiedId, setCopiedId] = useState(null);
  const [touchStartX, setTouchStartX] = useState(null);
  const [isPaused, setIsPaused] = useState(false);

  const carouselRef = useRef(null);

  const accentColor = categoryMeta?.color || '#00E5FF';
  const glowColor = categoryMeta?.glow || 'rgba(0, 229, 255, 0.28)';

  // Sync like state to localStorage and PostgreSQL database
  const toggleLike = async (e, storyId) => {
    e.stopPropagation();
    const nextState = !liked[storyId];
    setLiked((prev) => ({ ...prev, [storyId]: nextState }));
    try {
      const stored = localStorage.getItem('estd_liked_stories');
      const map = stored ? JSON.parse(stored) : {};
      map[storyId] = nextState;
      localStorage.setItem('estd_liked_stories', JSON.stringify(map));
      await toggleStoryLike(storyId);
    } catch (err) {
      console.warn('Could not persist like:', err);
    }
  };

  const handleShare = async (e, story) => {
    e.stopPropagation();
    const shareUrl = `${window.location.origin}/story/${story.id}`;
    if (navigator.share) {
      try {
        await navigator.share({
          title: story.headline,
          text: story.brief || story.headline,
          url: shareUrl,
        });
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
    setTimeout(() => setCopiedId(null), 2200);
  };

  const goTo = (idx) => {
    setActiveIndex(idx);
  };

  const goPrev = () => goTo((activeIndex - 1 + total) % total);
  const goNext = () => goTo((activeIndex + 1) % total);

  // Normal smooth auto-advance every 5s without any progress line
  useEffect(() => {
    if (total <= 1 || isPaused) return;

    const interval = setInterval(() => {
      setActiveIndex((current) => (current + 1) % total);
    }, 5000);

    return () => clearInterval(interval);
  }, [total, isPaused]);

  // Touch / Swipe
  const handleTouchStart = (e) => setTouchStartX(e.touches[0].clientX);
  const handleTouchEnd = (e) => {
    if (touchStartX === null) return;
    const diff = touchStartX - e.changedTouches[0].clientX;
    if (Math.abs(diff) > 45) {
      diff > 0 ? goNext() : goPrev();
    }
    setTouchStartX(null);
  };

  if (total === 0) return null;

  const current = heroStories[activeIndex] || heroStories[0];
  const isSaved = savedStories.some((s) => s.id === current.id);
  const isLiked = !!liked[current.id];
  const isCopied = copiedId === current.id;
  const currentSubcategory = current.subcategory || categoryMeta?.name || 'Top Story';

  const formattedDate = current.publishedAt
    ? formatTimeAgoShort(new Date(current.publishedAt))
    : 'Recent';

  return (
    <div
      className="category-hero-carousel"
      ref={carouselRef}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      style={{
        '--cat-accent': accentColor,
        '--cat-glow': glowColor,
      }}
    >
      {/* Dynamic Ambient Glow Behind Hero */}
      <div className="chc-ambient-aura" />

      {/* Slide Visual & Overlay */}
      <div
        className="chc-slide"
        onClick={() => navigate(`/story/${current.id}`)}
      >
        {/* Background Image Container */}
        <div className="chc-image-wrapper">
          <ImageWithFallback
            src={current.imageUrl}
            alt={current.headline}
            category={categoryMeta?.name || current.category}
            subcategory={current.subcategory}
            className="chc-image"
            size="hero"
            priority={true}
          />
          {/* Multi-layered cinematic gradient */}
          <div className="chc-gradient-scrim" />
        </div>

        {/* Content Overlay */}
        <div className="chc-overlay-content">
          {/* Metadata Badges Row */}
          <div className="chc-meta-row">
            <span
              className="chc-live-badge"
              style={{
                background: 'rgba(10, 13, 20, 0.88)',
                color: accentColor,
                borderColor: `${accentColor}88`,
                boxShadow: `0 2px 10px rgba(0, 0, 0, 0.55), inset 0 0 12px ${accentColor}25`,
              }}
            >
              <Sparkles size={12} />
              <span>{categoryMeta?.name || current.category} Spotlight</span>
            </span>

            <span className="chc-subcategory-pill">
              {currentSubcategory}
            </span>

            <span className="chc-time-pill">
              <Clock size={12} />
              <span>{formattedDate}</span>
            </span>

            {/* Slide Index Counter (e.g. 02 / 05) */}
            {total > 1 && (
              <span className="chc-index-pill">
                <strong>{String(activeIndex + 1).padStart(2, '0')}</strong>
                <span>/</span>
                <span>{String(total).padStart(2, '0')}</span>
              </span>
            )}
          </div>

          {/* Impact Headline */}
          <h2 className="chc-headline" title={current.headline}>
            {current.headline}
          </h2>

          {/* Quick 2-line Brief / Synthesis */}
          <p className="chc-brief">
            {current.brief || current.contentSnippet || 'Comprehensive verified report and context from official reporting sources.'}
          </p>

          {/* Bottom Actions Row */}
          <div className="chc-actions-bar">
            {/* Left: Primary Read CTA, Video Angle, Share, Save, Like */}
            <div className="chc-left-ctas">
              <button
                type="button"
                className="chc-read-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  navigate(`/story/${current.id}`);
                }}
                style={{
                  background: accentColor,
                  color: '#07080B',
                  boxShadow: `0 4px 20px ${accentColor}55`,
                }}
              >
                <span>Read Full Story</span>
                <ArrowRight size={15} />
              </button>

              {current.videoRail && current.videoRail.length > 0 && (
                <button
                  type="button"
                  className="chc-video-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    if (onWatchVideo) onWatchVideo(current);
                    else navigate(`/watch/${current.id}`);
                  }}
                >
                  <Play size={13} fill="#FFFFFF" />
                  <span>Watch Video Angles ({current.videoRail.length})</span>
                </button>
              )}

              {/* Social Actions (Share, Save, Like) beside Watch Video Angles */}
              <button
                type="button"
                className={`chc-icon-action-btn ${isCopied ? 'copied' : ''}`}
                onClick={(e) => handleShare(e, current)}
                title={isCopied ? 'Link Copied!' : 'Share Story'}
              >
                {isCopied ? <Check size={15} /> : <Share2 size={15} />}
                <span className="chc-btn-label">{isCopied ? 'Copied' : 'Share'}</span>
              </button>

              <button
                type="button"
                className={`chc-icon-action-btn ${isSaved ? 'active' : ''}`}
                onClick={(e) => {
                  e.stopPropagation();
                  if (onToggleSave) onToggleSave(current);
                }}
                title={isSaved ? 'Saved to bookmarks' : 'Save for later'}
              >
                <Bookmark
                  size={15}
                  fill={isSaved ? '#FFB020' : 'none'}
                  color={isSaved ? '#FFB020' : 'currentColor'}
                />
                <span className="chc-btn-label">{isSaved ? 'Saved' : 'Save'}</span>
              </button>

              <button
                type="button"
                className={`chc-icon-action-btn ${isLiked ? 'liked' : ''}`}
                onClick={(e) => toggleLike(e, current.id)}
                title={isLiked ? 'Liked' : 'Like'}
              >
                <Heart
                  size={15}
                  fill={isLiked ? '#FF4757' : 'none'}
                  color={isLiked ? '#FF4757' : 'currentColor'}
                />
                <span className="chc-btn-label">{isLiked ? 'Liked' : 'Like'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Manual Navigation Controls (Prev / Next Arrows) */}
      {total > 1 && (
        <div className="chc-nav-controls">
          <button
            type="button"
            className="chc-arrow-btn prev"
            onClick={(e) => {
              e.stopPropagation();
              goPrev();
            }}
            aria-label="Previous story"
          >
            <ChevronLeft size={18} />
          </button>
          <button
            type="button"
            className="chc-arrow-btn next"
            onClick={(e) => {
              e.stopPropagation();
              goNext();
            }}
            aria-label="Next story"
          >
            <ChevronRight size={18} />
          </button>
        </div>
      )}

      {/* Bottom Dot / Segment Indicators */}
      {total > 1 && (
        <div className="chc-indicator-pills">
          {heroStories.map((s, idx) => (
            <button
              key={s.id || idx}
              type="button"
              className={`chc-pill-dot ${idx === activeIndex ? 'active' : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                goTo(idx);
              }}
              aria-label={`Jump to slide ${idx + 1}`}
              style={{
                '--pill-accent': accentColor,
              }}
            >
              <span className="chc-pill-dot-inner" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
