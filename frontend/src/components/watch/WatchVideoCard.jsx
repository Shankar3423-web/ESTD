import React from 'react';
import { Play, CheckCircle2, Bookmark, Share2, ShieldCheck, Tv, Sparkles, Radio, Users, Clock } from 'lucide-react';
import ImageWithFallback from '../common/ImageWithFallback';
import { getCategoryMeta } from '../../constants/taxonomy';

/**
 * WatchVideoCard: High-polish 16:9 Video Card for ESTD Watch Hub Shelves.
 */
export default function WatchVideoCard({
  video,
  story,
  onPlay,
  onToggleSave,
  isSaved = false,
  watchLaterStories = [],
  onToggleWatchLater,
  isWatchLater = false,
  layout = 'standard', // 'standard' or 'compact'
}) {
  const targetStory = story || video?.story || {};
  const catMeta = targetStory.categoryMeta || getCategoryMeta(targetStory.category);
  const accentColor = catMeta?.color || '#00E5FF';

  const duration = video?.duration || '3:45';
  const views = video?.views || '140K views';
  const sourceName = video?.source || targetStory.sourceName || 'ESTD Verified Wire';
  const role = video?.role || video?.type || 'Official';
  const title = video?.title || targetStory.headline || 'Breaking Intelligence Video';
  const thumbnail = targetStory.imageUrl || video?.thumbnail;

  const getRoleIcon = (r) => {
    switch (r?.toLowerCase()) {
      case 'official':
        return <ShieldCheck size={11} />;
      case 'broadcast':
        return <Tv size={11} />;
      case 'analysis':
        return <Sparkles size={11} />;
      case 'creator':
        return <Radio size={11} />;
      case 'fan':
        return <Users size={11} />;
      default:
        return <Play size={11} />;
    }
  };

  const handleCardClick = () => {
    if (onPlay) {
      onPlay(targetStory, video);
    }
  };

  return (
    <div
      className={`watch-video-card ${layout === 'compact' ? 'compact-card' : ''}`}
      onClick={handleCardClick}
      style={{ '--card-accent': accentColor }}
    >
      {/* 16:9 Thumbnail Frame */}
      <div className="watch-card-thumb-wrap">
        <ImageWithFallback
          src={thumbnail}
          alt={title}
          category={targetStory.category}
          subcategory={targetStory.subcategory}
        />

        {/* Hover Dark Vignette & Play Icon */}
        <div className="watch-card-play-overlay">
          <div className="watch-card-play-circle" style={{ background: accentColor }}>
            <Play size={18} fill="#07080B" color="#07080B" className="play-icon-offset" />
          </div>
        </div>

        {/* Duration Pill */}
        <span className="watch-card-duration-badge">{duration}</span>

        {/* Perspective Role Tag */}
        <span className="watch-card-perspective-badge" style={{ borderColor: accentColor }}>
          {getRoleIcon(role)}
          <span>{role}</span>
        </span>
      </div>

      {/* Card Body */}
      <div className="watch-card-body">
        {/* Channel Row: Avatar + Headline */}
        <div className="watch-card-headline-row">
          <div
            className="watch-card-channel-avatar"
            style={{
              background: `linear-gradient(135deg, ${accentColor}40, #1e293b)`,
              borderColor: accentColor,
            }}
          >
            <span>{sourceName.slice(0, 2).toUpperCase()}</span>
          </div>

          <div className="watch-card-text-col">
            <h4 className="watch-card-title" title={title}>
              {title}
            </h4>

            {/* Source & Verified Checkmark */}
            <div className="watch-card-source-row">
              <span className="watch-card-channel-name">{sourceName}</span>
              <CheckCircle2 size={12} className="watch-verified-icon" />
            </div>

            {/* Meta Row: Views + Category Pill + Action Dock */}
            <div className="watch-card-meta-row">
              <span className="watch-card-views">{views}</span>
              <span className="watch-card-dot">•</span>
              <span className="watch-card-cat-pill" style={{ color: accentColor }}>
                {targetStory.category || 'News'}
              </span>

              {/* Action Buttons: Watch Later, Bookmark */}
              <div className="watch-card-actions-dock" onClick={(e) => e.stopPropagation()}>
                <button
                  type="button"
                  className={`watch-action-icon-btn ${isWatchLater ? 'active' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (onToggleWatchLater) onToggleWatchLater(targetStory);
                  }}
                  title={isWatchLater ? 'Remove from Watch Later' : 'Watch Later'}
                  aria-label="Watch Later"
                >
                  <Clock
                    size={13}
                    className="watch-later-clock"
                    fill="none"
                    color={isWatchLater ? '#FFB020' : 'currentColor'}
                    strokeWidth={isWatchLater ? 2.3 : 2}
                  />
                </button>

                <button
                  type="button"
                  className={`watch-action-icon-btn ${isSaved ? 'active' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (onToggleSave) onToggleSave(targetStory);
                  }}
                  title={isSaved ? 'Remove from Saved' : 'Save Story'}
                  aria-label="Save story"
                >
                  <Bookmark size={13} fill={isSaved ? accentColor : 'none'} color={isSaved ? accentColor : 'currentColor'} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

