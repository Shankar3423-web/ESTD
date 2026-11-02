import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  Play,
  Share2,
  Bookmark,
  Clock,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  Video,
  ShieldCheck,
  Tv,
  Sparkles,
  Radio,
  Users,
  Check,
  CheckCircle2,
  Film,
  Youtube,
  Zap,
  ThumbsUp,
  ThumbsDown,
  Flame,
  Bell,
  Grid,
} from 'lucide-react';
import ImageWithFallback from '../common/ImageWithFallback';
import ImpactChips from '../story/ImpactChips';
import ErrorState from '../common/ErrorState';
import FlashBiteModal from '../story/FlashBiteModal';
import WatchSentimentPulse from './WatchSentimentPulse';
import { fetchStoryById, fetchStories, fetchStoryVideos } from '../../api/estdApi';
import { getCategoryMeta } from '../../constants/taxonomy';
import { matchCategory, interleaveStoriesByCategory } from '../../utils/watchUtils';

/**
 * WatchTheatreView: Full YouTube-Fidelity Focused Player for `/watch/:storyId`.
 */
export default function WatchTheatreView({
  storyId,
  savedStories = [],
  onToggleSave,
  watchLaterStories = [],
  onToggleWatchLater,
}) {
  const navigate = useNavigate();

  const [story, setStory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activePerspectiveIndex, setActivePerspectiveIndex] = useState(0);
  const [allStories, setAllStories] = useState([]);

  // Video player state
  const [isSubscribed, setIsSubscribed] = useState(false);
  const [subscribersCount, setSubscribersCount] = useState(1420000);
  const [likesCount, setLikesCount] = useState(1280);
  const [hasLiked, setHasLiked] = useState(false);
  const [hasDisliked, setHasDisliked] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isDescExpanded, setIsDescExpanded] = useState(false);
  const [selectedQueueCategory, setSelectedQueueCategory] = useState('All');
  const [autoplayNext, setAutoplayNext] = useState(true);
  const [toastMessage, setToastMessage] = useState(null);

  // Flash Bite Modal state
  const [isFlashBiteOpen, setIsFlashBiteOpen] = useState(false);

  // Fetch story data and queue
  useEffect(() => {
    let isMounted = true;
    async function loadWatchStory() {
      setLoading(true);
      setError(null);
      try {
        const list = await fetchStories({ limit: 150 });
        if (isMounted) setAllStories(list);

        let targetStory = null;
        if (storyId) {
          try {
            targetStory = await fetchStoryById(storyId);
          } catch (fetchErr) {
            console.warn('fetchStoryById error, resolving from stories list:', fetchErr);
            targetStory = list.find((s) => String(s.id) === String(storyId));
          }
        }
        if (!targetStory && list && list.length > 0) {
          targetStory = list[0];
        }

        if (targetStory) {
          try {
            const freshRail = await fetchStoryVideos(targetStory.id);
            if (freshRail && freshRail.length > 0) {
              targetStory = { ...targetStory, videoRail: freshRail };
            }
          } catch {
            // fallback gracefully
          }
        }

        if (isMounted) {
          setStory(targetStory);
          setActivePerspectiveIndex(0);
          const seed = typeof targetStory?.id === 'number' ? targetStory.id : 42;
          setLikesCount((targetStory?.likesCount || 340) + ((seed * 37) % 500) + 120);
          setSubscribersCount(840000 + ((seed * 12345) % 1500000));
          setHasLiked(false);
          setHasDisliked(false);
          setIsSubscribed(false);
        }
      } catch (err) {
        if (isMounted) setError(err.message || 'Story video could not be loaded.');
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadWatchStory();
    return () => {
      isMounted = false;
    };
  }, [storyId]);

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const catMeta = useMemo(() => {
    if (!story) return { color: '#00E5FF', label: 'News' };
    return story.categoryMeta || getCategoryMeta(story.category);
  }, [story]);

  const accentColor = catMeta.color || '#00E5FF';
  const isSaved = story ? savedStories.some((s) => String(s.id) === String(story.id)) : false;
  const isWatchLater = story ? watchLaterStories.some((s) => String(s.id) === String(story.id)) : false;

  const perspectives = story?.videoRail || [];
  const currentPerspective = perspectives[activePerspectiveIndex] || perspectives[0] || {};

  const currentIndex = allStories.findIndex((s) => String(s.id) === String(story?.id));
  const prevStory = currentIndex > 0 ? allStories[currentIndex - 1] : null;
  const nextStory = currentIndex >= 0 && currentIndex < allStories.length - 1 ? allStories[currentIndex + 1] : null;

  const QUEUE_CATEGORIES = [
    { id: 'All', label: 'All' },
    { id: 'Tech', label: 'Tech' },
    { id: 'Entertainment', label: 'Entertainment' },
    { id: 'Business & Finance', label: 'Business & Finance' },
    { id: 'Sports', label: 'Sports' },
    { id: 'Developments', label: 'Developments' },
  ];



  const filteredQueue = useMemo(() => {
    let list = allStories.filter((s) => String(s.id) !== String(story?.id));
    if (selectedQueueCategory !== 'All') {
      list = list.filter((s) => matchCategory(s.category, selectedQueueCategory));
    } else {
      list = interleaveStoriesByCategory(list);
    }
    return list;
  }, [allStories, story, selectedQueueCategory]);

  const queueCategoryCounts = useMemo(() => {
    const list = allStories.filter((s) => String(s.id) !== String(story?.id));
    const counts = { All: list.length };
    for (const item of list) {
      const cat = (item.category || '').toLowerCase().trim();
      if (cat.includes('tech')) counts['Tech'] = (counts['Tech'] || 0) + 1;
      else if (cat.includes('entertain')) counts['Entertainment'] = (counts['Entertainment'] || 0) + 1;
      else if (cat.includes('business') || cat.includes('finance') || cat.includes('biz')) counts['Business & Finance'] = (counts['Business & Finance'] || 0) + 1;
      else if (cat.includes('sport')) counts['Sports'] = (counts['Sports'] || 0) + 1;
      else if (cat.includes('develop')) counts['Developments'] = (counts['Developments'] || 0) + 1;
    }
    return counts;
  }, [allStories, story]);

  const getRoleIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'official':
        return <ShieldCheck size={14} />;
      case 'broadcast':
        return <Tv size={14} />;
      case 'analysis':
        return <Sparkles size={14} />;
      case 'creator':
        return <Radio size={14} />;
      case 'fan':
        return <Users size={14} />;
      default:
        return <Flame size={14} />;
    }
  };

  const handleLike = () => {
    if (hasLiked) {
      setHasLiked(false);
      setLikesCount((prev) => prev - 1);
    } else {
      setHasLiked(true);
      if (hasDisliked) setHasDisliked(false);
      setLikesCount((prev) => prev + 1);
      showToast('Added to Liked Videos');
    }
  };

  const handleDislike = () => {
    if (hasDisliked) {
      setHasDisliked(false);
    } else {
      setHasDisliked(true);
      if (hasLiked) {
        setHasLiked(false);
        setLikesCount((prev) => prev - 1);
      }
      showToast('Feedback noted');
    }
  };

  const handleSubscribe = () => {
    if (isSubscribed) {
      setIsSubscribed(false);
      setSubscribersCount((prev) => prev - 1);
      showToast('Unsubscribed from ' + (currentPerspective.source || 'Channel'));
    } else {
      setIsSubscribed(true);
      setSubscribersCount((prev) => prev + 1);
      showToast('Subscribed to ' + (currentPerspective.source || 'Channel'));
    }
  };

  const handleShare = () => {
    const url = window.location.href;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url);
      setCopied(true);
      showToast('Link copied to clipboard!');
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const formatNumber = (num) => {
    if (!num) return '0';
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return String(num);
  };

  const formattedDate = useMemo(() => {
    if (!story?.publishedAt) return 'Recently';
    try {
      const d = new Date(story.publishedAt);
      return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
      return 'Recently';
    }
  }, [story]);

  if (loading) {
    return (
      <div className="watch-page-container">
        <div className="watch-skeleton-grid">
          <div className="watch-skeleton-player" />
          <div className="watch-skeleton-sidebar" />
        </div>
      </div>
    );
  }

  if (error || !story) {
    return (
      <div className="watch-page-container">
        <button className="story-back-nav" onClick={() => navigate('/watch')}>
          <ArrowLeft size={16} />
          <span>Back to Watch Hub</span>
        </button>
        <ErrorState
          title="Watch Perspective Unavailable"
          error={error || 'No story available for video playback.'}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  // queue categories handled via QUEUE_CATEGORIES

  return (
    <div className="watch-page-container">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="watch-toast-notification">
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Top Header Navigation Row */}
      <div className="watch-top-nav-bar">
        <div className="watch-top-left-crumbs">
          {/* Back to Watch Feed */}
          <button className="watch-nav-btn watch-back-hub-btn" onClick={() => navigate('/watch')}>
            <Grid size={15} />
            <span>Watch Hub</span>
          </button>
          <span className="watch-nav-crumb-separator">•</span>
          <button className="watch-nav-btn" onClick={() => navigate(`/story/${story.id}`)}>
            <ArrowLeft size={14} />
            <span>Story Object</span>
          </button>
          <span className="watch-nav-crumb-separator">•</span>
          <span className="watch-nav-cat-pill" style={{ color: accentColor }}>
            {story.category}
          </span>
          {story.subcategory && (
            <span className="watch-nav-subcat-pill">• {story.subcategory}</span>
          )}
        </div>

        <div className="watch-top-right-controls">
          {prevStory && (
            <button
              className="watch-prev-next-btn"
              onClick={() => navigate(`/watch/${prevStory.id}`)}
              title={`Previous: ${prevStory.headline}`}
            >
              <ChevronLeft size={16} />
              <span>Prev Story</span>
            </button>
          )}
          {nextStory && (
            <button
              className="watch-prev-next-btn"
              onClick={() => navigate(`/watch/${nextStory.id}`)}
              title={`Next: ${nextStory.headline}`}
            >
              <span>Next Story</span>
              <ChevronRight size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Main YouTube 2-Column Theatre Grid */}
      <div className="watch-theatre-grid">
        {/* Left Column: Video Player, Channel Bar, 5 Angles, Sentiment, Description */}
        <div className="watch-primary-column">
          {/* Cinematic Video Player Frame */}
          <div className="watch-video-viewport-wrapper">
            {/* Top Player Status Bar */}
            <div className="watch-player-mode-bar">
              <div className="watch-player-brand-pill">
                <Youtube size={15} style={{ color: '#FF0000' }} />
                <span>YouTube Theatre Player</span>
              </div>

              <div className="watch-player-angle-indicator">
                <span className="watch-player-angle-dot" style={{ background: accentColor }} />
                <span>{currentPerspective.role || 'Official'} Angle • 5 Perspectives Available</span>
              </div>
            </div>

            {/* Video Canvas */}
            <div className="watch-video-canvas">
              {currentPerspective.embedUrl ? (
                <iframe
                  key={`yt-${currentPerspective.id}-${activePerspectiveIndex}-${currentPerspective.embedUrl}`}
                  src={`${currentPerspective.embedUrl}${currentPerspective.embedUrl.includes('?') ? '&' : '?'}autoplay=1&mute=0&rel=0&modestbranding=1`}
                  title={currentPerspective.title || story.headline}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                  className="watch-iframe-player"
                />
              ) : currentPerspective.videoId ? (
                <iframe
                  key={`yt-${currentPerspective.videoId}-${activePerspectiveIndex}`}
                  src={`https://www.youtube-nocookie.com/embed/${currentPerspective.videoId}?autoplay=1&mute=0&rel=0&modestbranding=1`}
                  title={currentPerspective.title || story.headline}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                  className="watch-iframe-player"
                />
              ) : (
                <div className="watch-player-placeholder">
                  <Play size={44} style={{ color: accentColor }} />
                  <span>Loading perspective stream...</span>
                </div>
              )}
            </div>
          </div>

          {/* YouTube Video Title */}
          <div className="watch-title-wrapper">
            <h1 className="watch-video-headline">{currentPerspective.title || story.headline}</h1>
          </div>

          {/* YouTube-Style Channel Bar & Action Buttons */}
          <div className="watch-channel-bar">
            {/* Left: Channel Info & Subscribe Button */}
            <div className="watch-channel-left">
              <div
                className="watch-channel-avatar"
                style={{
                  background: `linear-gradient(135deg, ${accentColor}33, #1e293b)`,
                  borderColor: accentColor,
                }}
              >
                <span>{(currentPerspective.source || 'ESTD').slice(0, 2).toUpperCase()}</span>
              </div>

              <div className="watch-channel-meta">
                <div className="watch-channel-title-row">
                  <span className="watch-channel-name">
                    {currentPerspective.source || story.sourceName || 'ESTD Verified Wire'}
                  </span>
                  <CheckCircle2 size={14} className="watch-verified-icon" />
                </div>
                <span className="watch-subscribers-count">
                  {formatNumber(subscribersCount)} subscribers • Verified Partner
                </span>
              </div>

              <button
                type="button"
                className={`watch-subscribe-btn ${isSubscribed ? 'subscribed' : ''}`}
                onClick={handleSubscribe}
              >
                {isSubscribed ? (
                  <>
                    <Bell size={14} />
                    <span>Subscribed</span>
                  </>
                ) : (
                  <span>Subscribe</span>
                )}
              </button>
            </div>

            {/* Right: Segmented Likes/Dislikes, Share, Save, 60s Flash Bite */}
            <div className="watch-actions-right">
              {/* YouTube Segmented Like / Dislike Pill */}
              <div className="watch-segmented-likes">
                <button
                  type="button"
                  className={`watch-like-btn ${hasLiked ? 'active' : ''}`}
                  onClick={handleLike}
                  title="I like this"
                >
                  <ThumbsUp size={15} fill={hasLiked ? accentColor : 'none'} color={hasLiked ? accentColor : 'currentColor'} />
                  <span>{formatNumber(likesCount)}</span>
                </button>
                <div className="watch-segmented-divider" />
                <button
                  type="button"
                  className={`watch-dislike-btn ${hasDisliked ? 'active' : ''}`}
                  onClick={handleDislike}
                  title="I dislike this"
                >
                  <ThumbsDown size={15} fill={hasDisliked ? '#ef4444' : 'none'} color={hasDisliked ? '#ef4444' : 'currentColor'} />
                </button>
              </div>

              {/* Share Button */}
              <button
                type="button"
                className="watch-action-pill"
                onClick={handleShare}
                title="Share video"
              >
                {copied ? <Check size={15} style={{ color: '#10b981' }} /> : <Share2 size={15} />}
                <span>{copied ? 'Copied' : 'Share'}</span>
              </button>

              {/* Watch Later Button */}
              <button
                type="button"
                className={`watch-action-pill ${isWatchLater ? 'active text-amber' : ''}`}
                onClick={() => onToggleWatchLater && onToggleWatchLater(story)}
                title={isWatchLater ? 'Remove from Watch Later' : 'Watch Later'}
              >
                <Clock
                  size={15}
                  className="watch-later-clock"
                  fill="none"
                  color={isWatchLater ? '#FFB020' : 'currentColor'}
                  strokeWidth={isWatchLater ? 2.3 : 2}
                />
                <span>{isWatchLater ? 'In Watch Later' : 'Watch Later'}</span>
              </button>

              {/* Save Button */}
              <button
                type="button"
                className="watch-action-pill"
                onClick={() => onToggleSave && onToggleSave(story)}
                title={isSaved ? 'Saved to Playlist' : 'Save to Playlist'}
              >
                <Bookmark
                  size={15}
                  fill={isSaved ? accentColor : 'none'}
                  color={isSaved ? accentColor : 'currentColor'}
                />
                <span>{isSaved ? 'Saved' : 'Save'}</span>
              </button>

              {/* ⚡ 60s Flash Bite Micro-Reader Button */}
              <button
                type="button"
                className="watch-flash-bite-btn"
                onClick={() => setIsFlashBiteOpen(true)}
                title="Read 3-bullet 60s Smart Brevity"
              >
                <Zap size={14} fill="#00E5FF" color="#00E5FF" />
                <span>60s Flash Bite</span>
              </button>

              {/* Full Article Link */}
              <button
                type="button"
                className="watch-action-pill watch-article-link"
                onClick={() => navigate(`/story/${story.id}`)}
                title="Read full article"
              >
                <span>Read Story</span>
                <ExternalLink size={13} />
              </button>
            </div>
          </div>

          {/* Gen-Z Fact vs Cap Community Pulse Meter */}
          <div className="watch-theatre-sentiment-wrapper">
            <WatchSentimentPulse storyId={story.id} accentColor={accentColor} />
          </div>

          {/* 5-Angles Coverage Switcher Dock */}
          <div className="watch-perspectives-dock">
            <div className="watch-perspectives-header">
              <div className="watch-perspectives-title-wrap">
                <Video size={16} style={{ color: accentColor }} />
                <h3 className="watch-perspectives-title">
                  Multi-Perspective News Coverage ({perspectives.length} Angles)
                </h3>
                <span className="watch-perspectives-badge">ESTD Verified</span>
              </div>
              <span className="watch-perspectives-sub">
                Official statements, news desks, financial analysis, creator breakdowns & fan pulse.
              </span>
            </div>

            <div className="watch-perspectives-grid">
              {perspectives.map((vid, idx) => {
                const isActive = idx === activePerspectiveIndex;
                const type = vid.type || vid.role;
                return (
                  <button
                    key={vid.id || idx}
                    type="button"
                    className={`watch-angle-card ${isActive ? 'active' : ''}`}
                    onClick={() => {
                      setActivePerspectiveIndex(idx);
                      showToast(`Switched to ${type} angle`);
                    }}
                    style={{
                      borderColor: isActive ? accentColor : 'rgba(255, 255, 255, 0.08)',
                      boxShadow: isActive ? `0 0 16px ${accentColor}25` : 'none',
                    }}
                  >
                    <div className="watch-angle-card-top">
                      <span
                        className="watch-angle-role-tag"
                        style={{ color: isActive ? accentColor : '#94a3b8' }}
                      >
                        {getRoleIcon(type)}
                        <span>{type}</span>
                      </span>
                      <span className="watch-angle-duration">{vid.duration || '2:30'}</span>
                    </div>

                    <h4 className="watch-angle-title">{vid.title}</h4>

                    <div className="watch-angle-footer">
                      <span className="watch-angle-source">{vid.source}</span>
                      {isActive && (
                        <span className="watch-angle-playing-pill" style={{ background: accentColor, color: '#07080B' }}>
                          PLAYING
                        </span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* YouTube Expandable Description Box */}
          <div
            className={`watch-description-box ${isDescExpanded ? 'expanded' : ''}`}
            onClick={() => !isDescExpanded && setIsDescExpanded(true)}
          >
            {/* Meta Row: Views, Upload Date, Hashtags */}
            <div className="watch-desc-meta-row">
              <span className="watch-desc-views">
                {currentPerspective.views || '180K views'}
              </span>
              <span className="watch-desc-dot">•</span>
              <span className="watch-desc-date">{formattedDate}</span>
              <span className="watch-desc-dot">•</span>
              <span className="watch-desc-tag" style={{ color: accentColor }}>
                #{story.category?.replace(/\s+/g, '')}
              </span>
              {story.subcategory && (
                <span className="watch-desc-tag">#{story.subcategory?.replace(/\s+/g, '')}</span>
              )}
              <span className="watch-desc-tag">#ESTDIntelligence</span>
            </div>

            {/* Brief / Summary */}
            <p className="watch-desc-brief">
              {currentPerspective.summary || story.brief}
            </p>

            {/* Expanded Detailed Intelligence */}
            {isDescExpanded && (
              <div className="watch-desc-extended">
                <div className="watch-desc-divider" />
                <h5 className="watch-desc-heading">Executive Story Context</h5>
                <p className="watch-desc-body">{story.brief}</p>

                {story.impactChips && story.impactChips.length > 0 && (
                  <div className="watch-desc-chips-wrap">
                    <span className="watch-desc-chip-label">Key Dimensions:</span>
                    <ImpactChips chips={story.impactChips} accentColor={accentColor} />
                  </div>
                )}

                <div className="watch-desc-provenance">
                  <div className="watch-desc-prov-item">
                    <span className="watch-prov-label">Primary Source:</span>
                    <span className="watch-prov-val">{story.sourceName}</span>
                  </div>
                  <div className="watch-desc-prov-item">
                    <span className="watch-prov-label">ESTD Pipeline:</span>
                    <span className="watch-prov-val">Verified Step 1–9 Multi-Angle Synthesis</span>
                  </div>
                  {story.sourceUrl && (
                    <div className="watch-desc-prov-item">
                      <span className="watch-prov-label">Original Disclosure:</span>
                      <a
                        href={story.sourceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="watch-prov-link"
                      >
                        Read Original Source <ExternalLink size={11} />
                      </a>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Show More / Show Less Toggle */}
            <button
              type="button"
              className="watch-desc-toggle-btn"
              onClick={(e) => {
                e.stopPropagation();
                setIsDescExpanded((prev) => !prev);
              }}
            >
              {isDescExpanded ? 'Show less' : '...more'}
            </button>
          </div>
        </div>

        {/* Right Column: YouTube "Up Next" Video Queue & Category Chips */}
        <aside className="watch-sidebar-column">
          {/* Category Filter Chips */}
          <div className="watch-queue-chips-bar" aria-label="Up Next Categories">
            {QUEUE_CATEGORIES.map((cat) => {
              const count = queueCategoryCounts[cat.id] ?? 0;
              const isActive = selectedQueueCategory === cat.id;
              return (
                <button
                  key={cat.id}
                  type="button"
                  className={`watch-queue-chip ${isActive ? 'active' : ''}`}
                  onClick={() => setSelectedQueueCategory(cat.id)}
                  title={`Filter queue by ${cat.label} (${count} videos)`}
                >
                  <span>{cat.label}</span>
                  <span className="watch-queue-chip-count">{count}</span>
                </button>
              );
            })}
          </div>

          {/* Autoplay & Header Control */}
          <div className="watch-queue-header">
            <span className="watch-queue-title">Up Next in Intelligence</span>
            <div className="watch-autoplay-toggle">
              <span className="watch-autoplay-label">Autoplay</span>
              <button
                type="button"
                className={`watch-autoplay-switch ${autoplayNext ? 'on' : ''}`}
                onClick={() => setAutoplayNext((prev) => !prev)}
                title={autoplayNext ? 'Autoplay is ON' : 'Autoplay is OFF'}
              >
                <span className="watch-autoplay-knob" />
              </button>
            </div>
          </div>

          {/* Playlist Queue Items or Empty State */}
          {filteredQueue.length === 0 ? (
            <div className="watch-queue-empty-state">
              <p>No other videos found in {selectedQueueCategory}.</p>
              <button
                type="button"
                className="watch-queue-reset-btn"
                onClick={() => setSelectedQueueCategory('All')}
              >
                Show All Videos ({allStories.length})
              </button>
            </div>
          ) : (
            <div className="watch-queue-list">
              {filteredQueue.map((item) => {
              const itemCatMeta = item.categoryMeta || getCategoryMeta(item.category);
              const itemColor = itemCatMeta.color || '#00E5FF';
              const isCurrent = String(item.id) === String(story.id);

              return (
                <div
                  key={item.id}
                  className={`watch-queue-card ${isCurrent ? 'current-playing' : ''}`}
                  onClick={() => navigate(`/watch/${item.id}`)}
                >
                  <div className="watch-queue-thumb-wrap">
                    <ImageWithFallback
                      src={item.imageUrl}
                      alt={item.headline}
                      category={item.category}
                      subcategory={item.subcategory}
                    />
                    <div className="watch-queue-thumb-overlay">
                      <Play size={16} fill="#ffffff" />
                    </div>
                    <span className="watch-queue-duration-badge">
                      {item.videoRail?.[0]?.duration || '4:15'}
                    </span>
                    <span
                      className="watch-queue-cat-badge"
                      style={{ background: `${itemColor}dd`, color: '#07080B' }}
                    >
                      {item.category}
                    </span>
                  </div>

                  <div className="watch-queue-info">
                    <h5 className="watch-queue-item-headline">{item.headline}</h5>
                    <div className="watch-queue-item-source-row">
                      <span className="watch-queue-item-source">{item.sourceName}</span>
                      <CheckCircle2 size={12} className="watch-verified-icon" />
                    </div>
                    <div className="watch-queue-item-meta">
                      <span>{item.videoRail?.[0]?.views || '160K views'}</span>
                      <span>•</span>
                      <span>5 Angles</span>
                    </div>
                    {isCurrent && (
                      <span className="watch-now-playing-pill" style={{ color: accentColor }}>
                        ▶ NOW PLAYING
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
            </div>
          )}
        </aside>
      </div>

      {/* Integrated 60s Flash Bite Modal */}
      <FlashBiteModal
        isOpen={isFlashBiteOpen}
        story={story}
        stories={[story]}
        onClose={() => setIsFlashBiteOpen(false)}
      />
    </div>
  );
}

