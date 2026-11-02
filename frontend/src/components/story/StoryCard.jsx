import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bookmark,
  Share2,
  ArrowRight,
  Check,
  Clock,
  Video,
  Heart,
} from 'lucide-react';
import ImageWithFallback from '../common/ImageWithFallback';
import { getCategoryMeta, slugify } from '../../constants/taxonomy';
import { toggleStoryLike } from '../../api/estdApi';
import { trackArticleRead } from '../../utils/readingHistory';

/**
 * Editorial News Card Component with Organic Squircle Geometry
 * Spec:
 * - Curved, non-sharp squircle edges (24px radius with glassmorphic border)
 * - 2-row structured top bar:
 *     Row 1: Category Badge & "X Videos" Badge
 *     Row 2: High-contrast Subcategory Capsule & Freshness Timestamp
 * - News image with "Watch Video Brief" overlay
 * - Headline of the news (2 lines fixed)
 * - Information of that news (One simple, complete 5-line paragraph)
 * - Action footer: Read More button (redirects to article) + Share, Save, Like (persists to DB, no default fake likes)
 */
export default function StoryCard({
  story,
  isSaved = false,
  onToggleSave,
  watchLaterStories = [],
  onToggleWatchLater,
  isWatchLater = false,
  onWatchVideo,
}) {
  const navigate = useNavigate();
  const [copied, setCopied] = useState(false);
  const [liked, setLiked] = useState(() => {
    try {
      const stored = localStorage.getItem('estd_liked_stories');
      const map = stored ? JSON.parse(stored) : {};
      return !!map[story?.id];
    } catch {
      return false;
    }
  });

  // Real like count from PostgreSQL database (no fake/deterministic defaults)
  const [likeCount, setLikeCount] = useState(() => {
    return typeof story?.likesCount === 'number' ? story.likesCount : 0;
  });
  const [bursting, setBursting] = useState(false);

  if (!story) return null;

  const categoryName = story.category || story.categoryMeta?.name || 'General';
  const subcategoryName = story.subcategory || 'Latest Analysis';
  const catMeta = story.categoryMeta || getCategoryMeta(categoryName);
  const accentColor = catMeta.color || '#00E5FF';
  const videoCount = story.videoRail?.length || 5;

  const handleOpenStory = (e) => {
    if (e.target.closest('button') && !e.target.closest('.story-read-more-btn')) return;
    trackArticleRead(story);
    navigate(`/story/${story.id}`);
  };

  const handleShare = async (e) => {
    e.stopPropagation();
    const shareUrl = `${window.location.origin}/story/${story.id}`;
    if (navigator.share) {
      try {
        await navigator.share({
          title: story.headline,
          text: story.brief,
          url: shareUrl,
        });
      } catch (err) {
        copyToClipboard(shareUrl);
      }
    } else {
      copyToClipboard(shareUrl);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Toggle like and persist directly to PostgreSQL database
  const handleLike = async (e) => {
    e.stopPropagation();
    const nextState = !liked;
    setLiked(nextState);
    setLikeCount((prev) => (nextState ? prev + 1 : Math.max(0, prev - 1)));
    if (nextState) {
      setBursting(true);
      setTimeout(() => setBursting(false), 700);
    }
    try {
      const stored = localStorage.getItem('estd_liked_stories');
      const map = stored ? JSON.parse(stored) : {};
      map[story.id] = nextState;
      localStorage.setItem('estd_liked_stories', JSON.stringify(map));

      // Call database API
      const res = await toggleStoryLike(story.id);
      if (res && typeof res.likes_count === 'number') {
        setLikeCount(res.likes_count);
      }
    } catch (err) {
      console.warn('Could not persist like to database:', err);
    }
  };

  const handleWatch = (e) => {
    e.stopPropagation();
    if (onWatchVideo) {
      onWatchVideo(story);
    } else {
      navigate(`/watch/${story.id}`);
    }
  };

  const formattedPubDate = story.publishedAt
    ? formatTimeAgo(new Date(story.publishedAt))
    : 'Recent';

  const fullPubDateStr = story.publishedAt
    ? new Date(story.publishedAt).toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : 'Date Verified';

  // Format exactly one clean, cohesive 5-line paragraph
  const singleParagraph = getSingleCompleteParagraph(
    story.brief || story.contentSnippet || story.content,
    story.headline || story.originalTitle,
    categoryName,
    subcategoryName
  );

  return (
    <article
      className="story-card squircle-card"
      style={{
        '--card-accent': accentColor,
        cursor: 'pointer',
      }}
      onClick={handleOpenStory}
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter') handleOpenStory(e);
      }}
    >
      {/* 1. TOP BAR: Category, Subcategory, Videos Badge & Freshness (Structured 2-row layout) */}
      <div className="story-card-top">
        {/* Row 1: Category Badge (left) & Videos Badge (right) */}
        <div className="story-card-top-row1">
          <span
            className="category-badge"
            style={{
              borderColor: `${accentColor}66`,
              color: accentColor,
            }}
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/category/${catMeta.slug || slugify(categoryName)}`);
            }}
          >
            {categoryName}
          </span>

          {/* "X Videos" Badge */}
          <span
            className="story-videos-badge"
            style={{
              borderColor: `${accentColor}55`,
              color: accentColor,
              background: `${accentColor}18`,
            }}
            onClick={handleWatch}
            title="Explore multi-source video angles"
          >
            <Video size={11} />
            <span>{videoCount} Videos</span>
          </span>
        </div>

        {/* Row 2: Subcategory Capsule (left) & Publication Freshness (right) */}
        <div className="story-card-top-row2">
          <span
            className="story-subcategory-capsule"
            title={subcategoryName}
          >
            {subcategoryName}
          </span>

          <div
            className="story-timestamp"
            title={`Original Publication: ${fullPubDateStr}`}
          >
            <Clock size={11} style={{ marginRight: 3, display: 'inline' }} />
            <span>{formattedPubDate}</span>
          </div>
        </div>
      </div>

      {/* 2. NEWS IMAGE (Opens article on click) */}
      <div
        className="story-media-preview"
        onClick={(e) => {
          e.stopPropagation();
          handleOpenStory(e);
        }}
        title={`Read: ${story.headline}`}
      >
        <ImageWithFallback
          src={story.imageUrl}
          alt={story.headline}
          category={categoryName}
          subcategory={subcategoryName}
          className="story-media-img"
          size="card"
        />
      </div>

      {/* 3. TITLE OF THE NEWS */}
      <h3 className="story-headline">{story.headline}</h3>

      {/* 4. INFORMATION RELATED TO THAT NEWS (One simple, complete 5-line paragraph) */}
      <div className="story-brief">
        <p className="story-brief-text">
          {singleParagraph}
        </p>
      </div>

      {/* 5. FOOTER: READ MORE BUTTON + SHARE, SAVE, LIKE */}
      <div className="story-footer">
        {/* Read More Button to open news story */}
        <button
          type="button"
          className="story-read-more-btn"
          onClick={(e) => {
            e.stopPropagation();
            handleOpenStory(e);
          }}
          title="Read complete story"
          aria-label="Read more"
        >
          <span>Read More</span>
          <ArrowRight size={13} />
        </button>

        {/* Action Controls: Like, Save, Share (Speaker symbol removed as requested) */}
        <div className="story-actions-group">
          {/* Like Button: Active only on user click, persists to PostgreSQL */}
          <button
            type="button"
            className={`action-icon-btn like-btn ${liked ? 'active' : ''} ${bursting ? 'bursting' : ''} ${likeCount === 0 ? 'symbol-only' : ''}`}
            title={liked ? `Liked (${likeCount})` : 'Like this story'}
            aria-label="Like story"
            onClick={handleLike}
          >
            <Heart
              size={15}
              fill={liked ? '#FF4757' : 'none'}
              color={liked ? '#FF4757' : 'currentColor'}
            />
            {likeCount > 0 && <span className="like-count-num">{likeCount}</span>}
          </button>

          {/* Watch Later */}
          <button
            type="button"
            className={`action-icon-btn watch-later-btn ${isWatchLater ? 'active' : ''}`}
            title={isWatchLater ? 'Remove from Watch Later' : 'Watch Later'}
            aria-label="Watch Later"
            onClick={(e) => {
              e.stopPropagation();
              if (onToggleWatchLater) onToggleWatchLater(story);
            }}
          >
            <Clock
              size={15}
              className="watch-later-clock"
              fill="none"
              color={isWatchLater ? '#FFB020' : 'currentColor'}
              strokeWidth={isWatchLater ? 2.3 : 2}
            />
          </button>

          {/* Save Story */}
          <button
            type="button"
            className={`action-icon-btn ${isSaved ? 'active' : ''}`}
            title={isSaved ? 'Remove from saved' : 'Save story'}
            aria-label="Save story"
            onClick={(e) => {
              e.stopPropagation();
              if (onToggleSave) onToggleSave(story);
            }}
          >
            <Bookmark size={15} fill={isSaved ? accentColor : 'none'} color={isSaved ? accentColor : 'currentColor'} />
          </button>

          {/* Share */}
          <button
            type="button"
            className={`action-icon-btn ${copied ? 'copied' : ''}`}
            title={copied ? 'Link Copied!' : 'Share story'}
            aria-label="Share story"
            onClick={handleShare}
          >
            {copied ? <Check size={15} style={{ color: '#10b981' }} /> : <Share2 size={15} />}
          </button>
        </div>
      </div>
    </article>
  );
}

/**
 * Returns exactly ONE simple, complete, cohesive paragraph formatted to 5 lines.
 * Ensures the paragraph finishes with proper sentence-ending punctuation.
 */
function getSingleCompleteParagraph(text, title = '', category = '', subcategory = '') {
  const fallbackDomain = subcategory || category || 'intelligence';
  const cleanTitle = (title || '').replace(/\.{3,}$/, '').trim();
  const titleSentence = cleanTitle ? (cleanTitle.endsWith('.') ? cleanTitle : cleanTitle + '.') : '';

  if (!text || !text.trim()) {
    return `${titleSentence} In latest developments reported across ${fallbackDomain} monitoring channels, key stakeholders reviewed operational milestones and verified disclosures. Official updates confirm continued momentum across primary initiatives.`;
  }

  // Normalize line breaks and spaces into a continuous clean string
  let cleaned = text.replace(/\r\n/g, ' ').replace(/[\r\n]+/g, ' ').replace(/\s+/g, ' ').trim();

  // Extract complete sentences
  const sentences = (cleaned.match(/[^.!?]+[.!?]+(\s|$)/g) || [])
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

  let result = '';

  if (sentences.length >= 2) {
    // Accumulate complete sentences up to ~320-370 characters (ideal 5-line block)
    let candidate = '';
    for (const s of sentences) {
      if ((candidate + ' ' + s).trim().length <= 360) {
        candidate = candidate ? `${candidate} ${s}` : s;
      } else {
        break;
      }
    }
    result = candidate || sentences.slice(0, 2).join(' ');
  } else if (sentences.length === 1) {
    result = `${sentences[0]} Verified disclosures confirm ongoing developments and operational updates across the ${fallbackDomain} ecosystem.`;
  } else {
    // If no standard sentence punctuation, trim cleanly and add terminal punctuation
    result = cleaned.length > 320 ? cleaned.slice(0, 320).trim() : cleaned;
    if (!/[.!?]$/.test(result)) {
      result += '.';
    }
  }

  // Strictly ensure paragraph ends with complete terminal punctuation
  if (!/[.!?]$/.test(result)) {
    const lastPunc = Math.max(result.lastIndexOf('.'), result.lastIndexOf('!'), result.lastIndexOf('?'));
    if (lastPunc > 60) {
      result = result.slice(0, lastPunc + 1);
    } else {
      result += '.';
    }
  }

  return result;
}

function formatTimeAgo(date) {
  const seconds = Math.floor((new Date() - date) / 1000);
  if (isNaN(seconds) || seconds < 0) return 'Just now';
  if (seconds < 60) return 'Just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days === 1) return 'Yesterday';
  if (days < 7) return `${days}d ago`;
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}
