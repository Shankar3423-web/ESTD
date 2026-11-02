import React, { useRef, useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Cpu,
  Film,
  TrendingUp,
  Compass,
  Trophy,
  GraduationCap,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  ThumbsUp,
  Bookmark,
  Share2,
  Check,
  Clock,
} from 'lucide-react';
import ImageWithFallback from '../common/ImageWithFallback';
import { getCategoryMeta, slugify } from '../../constants/taxonomy';
import { toggleStoryLike } from '../../api/estdApi';

const CATEGORY_ICON_MAP = {
  Tech: Cpu,
  Entertainment: Film,
  'Business & Finance': TrendingUp,
  Business: TrendingUp,
  Developments: Compass,
  Sports: Trophy,
  Education: GraduationCap,
};

function getSourceBadge(sourceName = '') {
  const clean = (sourceName || '').trim();
  if (/economic times/i.test(clean)) return { text: 'ET', bg: '#ED1C24', color: '#fff' };
  if (/times of india/i.test(clean)) return { text: 'TOI', bg: '#D32F2F', color: '#fff' };
  if (/news18/i.test(clean)) return { text: 'N18', bg: '#1A365D', color: '#fff' };
  if (/hindu/i.test(clean)) return { text: 'TH', bg: '#1E3A8A', color: '#fff' };
  if (/reuters/i.test(clean)) return { text: 'R', bg: '#FF8000', color: '#fff' };
  if (/bbc/i.test(clean)) return { text: 'BBC', bg: '#BB1919', color: '#fff' };
  if (/techcrunch/i.test(clean)) return { text: 'TC', bg: '#00A562', color: '#fff' };
  if (/ndtv/i.test(clean)) return { text: 'ND', bg: '#E11D48', color: '#fff' };
  if (/verge/i.test(clean)) return { text: 'V', bg: '#E01A4F', color: '#fff' };
  if (/espn/i.test(clean)) return { text: 'ESPN', bg: '#CC0000', color: '#fff' };
  const initial = clean.charAt(0).toUpperCase() || 'N';
  return { text: initial, bg: 'rgba(255, 255, 255, 0.16)', color: '#fff' };
}

/**
 * CategoryQuickRow — A horizontal scroll row dedicated to a specific category or thematic pulse (e.g. Education Pulse).
 * Styled to match modern news cards with image, category badge, source metadata, headline, and real database-backed like, save, and share actions.
 */
export default function CategoryQuickRow({
  categoryName = 'Tech',
  subcategoryName = null,
  excludeSubcategory = null,
  stories = [],
  savedStories = [],
  onToggleSave = null,
  watchLaterStories = [],
  onToggleWatchLater = null,
  titleOverride,
  subtitle,
  icon: IconOverride = null,
  accentColor: accentColorOverride = null,
  seeAllLink: seeAllLinkOverride = null,
}) {
  const navigate = useNavigate();
  const trackRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  // Live like counts synced with backend database
  const [likesOverrideMap, setLikesOverrideMap] = useState({});

  // Share clipboard copy state tracker
  const [copiedId, setCopiedId] = useState(null);

  // Fallback local saved state when onToggleSave is not provided
  const [localSavedMap, setLocalSavedMap] = useState({});

  // Persistent set of story IDs that this user/browser has liked
  const [myLikedSet, setMyLikedSet] = useState(() => {
    try {
      const saved = localStorage.getItem('estd_my_liked_stories');
      return new Set(saved ? JSON.parse(saved) : []);
    } catch {
      return new Set();
    }
  });

  const handleToggleLike = async (e, storyId) => {
    e.stopPropagation();

    const wasLiked = myLikedSet.has(storyId);
    const nextLiked = !wasLiked;

    // 1. Optimistic UI update
    setMyLikedSet((prev) => {
      const next = new Set(prev);
      if (nextLiked) next.add(storyId);
      else next.delete(storyId);
      try {
        localStorage.setItem('estd_my_liked_stories', JSON.stringify([...next]));
      } catch {}
      return next;
    });

    setLikesOverrideMap((prev) => {
      const curCount =
        prev[storyId] !== undefined
          ? prev[storyId]
          : (stories.find((s) => s.id === storyId)?.likesCount || 0);
      const nextCount = nextLiked ? curCount + 1 : Math.max(0, curCount - 1);
      return { ...prev, [storyId]: nextCount };
    });

    // 2. Persist to PostgreSQL backend database
    try {
      const res = await toggleStoryLike(storyId);
      if (res && typeof res.likes_count === 'number') {
        setLikesOverrideMap((prev) => ({
          ...prev,
          [storyId]: res.likes_count,
        }));
        if (typeof res.liked === 'boolean') {
          setMyLikedSet((prev) => {
            const next = new Set(prev);
            if (res.liked) next.add(storyId);
            else next.delete(storyId);
            try {
              localStorage.setItem('estd_my_liked_stories', JSON.stringify([...next]));
            } catch {}
            return next;
          });
        }
      }
    } catch (err) {
      console.warn(`Failed to persist like for story #${storyId}:`, err);
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
        return;
      } catch (err) {
        // Fallback to clipboard
      }
    }
    if (navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(shareUrl);
        setCopiedId(story.id);
        setTimeout(() => setCopiedId(null), 2000);
      } catch (err) {
        console.warn('Could not copy link:', err);
      }
    }
  };

  const handleToggleSave = (e, story) => {
    e.stopPropagation();
    if (onToggleSave) {
      onToggleSave(story);
    } else {
      try {
        const saved = JSON.parse(localStorage.getItem('estd_saved_stories') || '[]');
        const exists = saved.some((s) => s.id === story.id);
        const updated = exists ? saved.filter((s) => s.id !== story.id) : [...saved, story];
        localStorage.setItem('estd_saved_stories', JSON.stringify(updated));
        setLocalSavedMap((prev) => ({ ...prev, [story.id]: !exists }));
      } catch (err) {
        console.warn('Could not save story:', err);
      }
    }
  };

  const [localWatchLaterMap, setLocalWatchLaterMap] = useState({});

  const handleToggleWatchLater = (e, story) => {
    e.stopPropagation();
    if (onToggleWatchLater) {
      onToggleWatchLater(story);
    } else {
      try {
        const stored = JSON.parse(localStorage.getItem('estd_watch_later') || '[]');
        const exists = stored.some((s) => String(s.id) === String(story.id));
        const updated = exists
          ? stored.filter((s) => String(s.id) !== String(story.id))
          : [story, ...stored];
        localStorage.setItem('estd_watch_later', JSON.stringify(updated));
        setLocalWatchLaterMap((prev) => ({ ...prev, [story.id]: !exists }));
      } catch (err) {
        console.warn('Could not save to watch later:', err);
      }
    }
  };

  // Filter stories matching this category or subcategory
  const categoryStories = React.useMemo(() => {
    if (!stories || stories.length === 0) return [];

    // Subcategory-specific pulse (e.g. Education Pulse)
    if (subcategoryName) {
      const subLower = subcategoryName.toLowerCase();
      return stories.filter(
        (s) =>
          s.subcategory?.toLowerCase().includes(subLower) ||
          s.title?.toLowerCase().includes(subLower)
      );
    }

    // Category pulse with optional subcategory exclusion
    return stories.filter((s) => {
      const matchCat =
        s.category?.toLowerCase() === categoryName.toLowerCase() ||
        (categoryName === 'Business & Finance' &&
          (s.category === 'Business' || s.category === 'Business & Finance'));

      if (!matchCat) return false;

      if (excludeSubcategory) {
        const exLower = excludeSubcategory.toLowerCase();
        if (s.subcategory?.toLowerCase().includes(exLower)) return false;
      }

      return true;
    });
  }, [stories, categoryName, subcategoryName, excludeSubcategory]);

  const catMeta = getCategoryMeta(categoryName);
  const accentColor = accentColorOverride || catMeta?.color || '#00E5FF';
  const categorySlug = catMeta?.slug || slugify(categoryName);
  const IconComponent =
    IconOverride ||
    (subcategoryName && subcategoryName.toLowerCase().includes('education')
      ? GraduationCap
      : CATEGORY_ICON_MAP[categoryName] || Sparkles);

  const finalSeeAllLink = seeAllLinkOverride || `/category/${categorySlug}`;

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
  }, [categoryStories]);

  const scroll = (direction) => {
    if (!trackRef.current) return;
    const scrollAmount = 450;
    trackRef.current.scrollBy({
      left: direction === 'left' ? -scrollAmount : scrollAmount,
      behavior: 'smooth',
    });
    setTimeout(checkScroll, 350);
  };

  if (categoryStories.length === 0) return null;

  const displayTitle = titleOverride || `${categoryName} Pulse`;

  return (
    <section
      className="category-quick-section"
      aria-label={`${displayTitle} stories`}
      style={{ '--cat-accent': accentColor }}
    >
      {/* Section Header */}
      <div className="category-quick-header">
        <div className="category-quick-title-group">
          <div
            className="category-quick-icon-badge"
            style={{
              background: `linear-gradient(135deg, ${accentColor}25, ${accentColor}0a)`,
              borderColor: `${accentColor}44`,
              color: accentColor,
            }}
          >
            <IconComponent size={18} />
          </div>

          <div className="category-quick-titles">
            <div className="category-quick-name-row">
              <h2 className="category-quick-heading">{displayTitle}</h2>
              <span
                className="category-quick-count-pill"
                style={{ color: accentColor, borderColor: `${accentColor}33` }}
              >
                {categoryStories.length} stories
              </span>
            </div>
            {subtitle && <p className="category-quick-sub">{subtitle}</p>}
          </div>
        </div>

        <div className="category-quick-actions">
          <Link
            to={finalSeeAllLink}
            className="category-quick-see-all"
            style={{ color: accentColor }}
          >
            <span>See all</span>
            <ArrowRight size={14} />
          </Link>

          {categoryStories.length > 2 && (
            <div className="category-quick-arrows">
              <button
                type="button"
                className={`category-quick-arrow-btn ${!canScrollLeft ? 'disabled' : ''}`}
                onClick={() => scroll('left')}
                disabled={!canScrollLeft}
                aria-label={`Scroll ${displayTitle} left`}
              >
                <ChevronLeft size={16} />
              </button>
              <button
                type="button"
                className={`category-quick-arrow-btn ${!canScrollRight ? 'disabled' : ''}`}
                onClick={() => scroll('right')}
                disabled={!canScrollRight}
                aria-label={`Scroll ${displayTitle} right`}
              >
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Horizontal Cards Track */}
      <div
        className="category-quick-track"
        ref={trackRef}
        onScroll={checkScroll}
      >
        {categoryStories.map((story) => {
          const timeAgo = formatTimeAgo(story.publishedAt);
          const editorialType = story.editorialType;
          const displaySubcategory =
            story.subcategory && story.subcategory !== 'General'
              ? story.subcategory
              : story.category;
          const sourceBadge = getSourceBadge(story.sourceName);
          const isLiked = myLikedSet.has(story.id);
          const likeCount =
            likesOverrideMap[story.id] !== undefined
              ? likesOverrideMap[story.id]
              : (story.likesCount || 0);

          const isSaved = onToggleSave
            ? savedStories.some((s) => String(s.id) === String(story.id))
            : (localSavedMap[story.id] !== undefined
                ? localSavedMap[story.id]
                : (() => {
                    try {
                      const saved = JSON.parse(localStorage.getItem('estd_saved_stories') || '[]');
                      return saved.some((s) => String(s.id) === String(story.id));
                    } catch {
                      return false;
                    }
                  })());

          const isWatchLater = onToggleWatchLater
            ? watchLaterStories.some((s) => String(s.id) === String(story.id))
            : (localWatchLaterMap[story.id] !== undefined
                ? localWatchLaterMap[story.id]
                : (() => {
                    try {
                      const list = JSON.parse(localStorage.getItem('estd_watch_later') || '[]');
                      return list.some((s) => String(s.id) === String(story.id));
                    } catch {
                      return false;
                    }
                  })());
          const isCopied = copiedId === story.id;

          return (
            <article
              key={story.id}
              className="cqr-card"
              onClick={() => navigate(`/story/${story.id}`)}
            >
              {/* Image with crisp high-contrast subcategory badge on top */}
              <div className="cqr-image-container">
                <ImageWithFallback
                  src={story.imageUrl}
                  alt={story.headline}
                  category={story.category}
                  subcategory={story.subcategory}
                  className="cqr-image"
                  size="row"
                />
                <div className="cqr-image-overlay" />

                <span className="cqr-image-subcat-badge" title={displaySubcategory}>
                  {displaySubcategory}
                </span>
              </div>

              {/* Card Body */}
              <div className="cqr-body">
                {/* Source & Relative Time Row */}
                <div className="cqr-source-row">
                  <span
                    className="cqr-source-avatar"
                    style={{
                      backgroundColor: sourceBadge.bg,
                      color: sourceBadge.color,
                    }}
                  >
                    {sourceBadge.text}
                  </span>
                  <span className="cqr-source-name" title={story.sourceName || 'Verified Source'}>
                    {story.sourceName || 'Verified Source'}
                  </span>
                  <span className="cqr-source-dot">·</span>
                  <span className="cqr-time-ago">{timeAgo}</span>

                  {editorialType && editorialType !== 'REPORT' && (
                    <span
                      className="cqr-special-badge"
                      style={{
                        borderColor: 'rgba(255, 176, 32, 0.4)',
                        color: '#FFB020',
                        background: 'rgba(255, 176, 32, 0.12)',
                      }}
                    >
                      {editorialType}
                    </span>
                  )}
                </div>

                {/* Headline Title */}
                <h3 className="cqr-headline" title={story.headline}>
                  {story.headline}
                </h3>

                {/* Bottom Row with Thumbs Up Like, Save, and Share Action Buttons */}
                <div className="cqr-bottom-row">
                  {/* Like Button */}
                  <button
                    type="button"
                    className={`cqr-action-btn cqr-like-btn ${isLiked ? 'liked' : ''} ${likeCount === 0 ? 'symbol-only' : ''}`}
                    onClick={(e) => handleToggleLike(e, story.id)}
                    aria-label={isLiked ? `Unlike story (${likeCount} likes)` : `Like story (${likeCount} likes)`}
                    title={isLiked ? 'Unlike' : 'Like'}
                  >
                    <ThumbsUp
                      size={14}
                      className={`cqr-action-icon ${isLiked ? 'filled' : ''}`}
                    />
                    {likeCount > 0 && (
                      <span className="cqr-like-count">{likeCount}</span>
                    )}
                  </button>

                  {/* Watch Later Button */}
                  <button
                    type="button"
                    className={`cqr-action-btn cqr-watch-later-btn ${isWatchLater ? 'active' : ''}`}
                    onClick={(e) => handleToggleWatchLater(e, story)}
                    aria-label={isWatchLater ? 'Remove from Watch Later' : 'Watch Later'}
                    title={isWatchLater ? 'In Watch Later' : 'Watch Later'}
                  >
                    <Clock
                      size={14}
                      className="cqr-action-icon watch-later-clock"
                      fill="none"
                      color={isWatchLater ? '#FFB020' : 'currentColor'}
                      strokeWidth={isWatchLater ? 2.3 : 2}
                    />
                  </button>

                  {/* Save Button */}
                  <button
                    type="button"
                    className={`cqr-action-btn cqr-save-btn ${isSaved ? 'saved' : ''}`}
                    onClick={(e) => handleToggleSave(e, story)}
                    aria-label={isSaved ? 'Remove from Saved' : 'Save story'}
                    title={isSaved ? 'Saved' : 'Save'}
                  >
                    <Bookmark
                      size={14}
                      className={`cqr-action-icon ${isSaved ? 'filled' : ''}`}
                    />
                  </button>

                  {/* Share Button */}
                  <button
                    type="button"
                    className={`cqr-action-btn cqr-share-btn ${isCopied ? 'copied' : ''}`}
                    onClick={(e) => handleShare(e, story)}
                    aria-label="Share story"
                    title={isCopied ? 'Link Copied!' : 'Share'}
                  >
                    {isCopied ? (
                      <Check size={14} className="cqr-action-icon" color="#10B981" />
                    ) : (
                      <Share2 size={14} className="cqr-action-icon" />
                    )}
                  </button>
                </div>
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
  if (days === 1) return '1d';
  if (days < 7) return `${days}d`;
  return new Date(dateStr).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}
