import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Play,
  Film,
  Zap,
  Bookmark,
  Share2,
  Check,
  Maximize2,
  ExternalLink,
  ShieldCheck,
  Tv,
  Sparkles,
  Radio,
  Users,
  Flame,
} from 'lucide-react';
import { getCategoryMeta } from '../../constants/taxonomy';
import WatchSentimentPulse from './WatchSentimentPulse';

/**
 * WatchHeroSpotlight: Cinematic Premier Spotlight Video Banner for ESTD Watch Hub.
 * Features live 16:9 player preview with real-time 5-Angle perspective flipping.
 */
export default function WatchHeroSpotlight({
  story,
  onOpenFlashBite,
  onToggleSave,
  isSaved = false,
}) {
  const navigate = useNavigate();
  const [activePerspectiveIndex, setActivePerspectiveIndex] = useState(0);
  const [copied, setCopied] = useState(false);

  const catMeta = useMemo(() => {
    if (!story) return { color: '#00E5FF', label: 'Tech' };
    return story.categoryMeta || getCategoryMeta(story.category);
  }, [story]);

  const accentColor = catMeta?.color || '#00E5FF';

  const perspectives = story?.videoRail || [];
  const currentPerspective = perspectives[activePerspectiveIndex] || perspectives[0] || {};

  const getRoleIcon = (role) => {
    switch (role?.toLowerCase()) {
      case 'official':
        return <ShieldCheck size={13} />;
      case 'broadcast':
        return <Tv size={13} />;
      case 'analysis':
        return <Sparkles size={13} />;
      case 'creator':
        return <Radio size={13} />;
      case 'fan':
        return <Users size={13} />;
      default:
        return <Flame size={13} />;
    }
  };

  const handleShare = () => {
    if (!story) return;
    const url = `${window.location.origin}/watch/${story.id}`;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!story) return null;

  return (
    <section className="watch-hero-spotlight-section" aria-label="Featured News Video Spotlight">
      {/* Background Ambient Glow */}
      <div
        className="watch-hero-ambient-glow"
        style={{
          background: `radial-gradient(circle at 30% 30%, ${accentColor}18 0%, transparent 70%)`,
        }}
      />

      <div className="watch-hero-content-grid">
        {/* Left Column: 16:9 Cinema Player Canvas */}
        <div className="watch-hero-player-column">
          <div className="watch-hero-canvas-frame">
            {currentPerspective.embedUrl ? (
              <iframe
                key={`hero-embed-${activePerspectiveIndex}-${currentPerspective.embedUrl}`}
                src={`${currentPerspective.embedUrl}${currentPerspective.embedUrl.includes('?') ? '&' : '?'}autoplay=0&mute=1&controls=1&modestbranding=1`}
                title={currentPerspective.title || story.headline}
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowFullScreen
                className="watch-hero-iframe"
              />
            ) : (
              <video
                key={`hero-vid-${activePerspectiveIndex}`}
                src={
                  currentPerspective.videoStreamUrl ||
                  'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4'
                }
                poster={currentPerspective.thumbnail || story.imageUrl}
                controls
                playsInline
                className="watch-hero-native-video"
              />
            )}

            {/* Top Badge: Spotlight + Angle indicator */}
            <div className="watch-hero-video-top-bar">
              <span className="watch-hero-live-pill">
                <span className="watch-pulse-dot" />
                <span>PREMIER SPOTLIGHT</span>
              </span>
              <span className="watch-hero-active-angle-badge" style={{ borderColor: accentColor }}>
                {getRoleIcon(currentPerspective.role)}
                <span>{currentPerspective.role || 'Official'} Angle</span>
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Intelligence & Interactive Angle Dock */}
        <div className="watch-hero-info-column">
          {/* Category & Kicker */}
          <div className="watch-hero-meta-kicker">
            <span className="watch-hero-cat-tag" style={{ color: accentColor }}>
              {story.category}
            </span>
            {story.subcategory && (
              <span className="watch-hero-subcat-tag">• {story.subcategory}</span>
            )}
            <span className="watch-hero-views-tag">
              {currentPerspective.views || '310K views'}
            </span>
          </div>

          {/* Headline */}
          <h2
            className="watch-hero-headline"
            onClick={() => navigate(`/watch/${story.id}`)}
            title="Open in Theatre Mode"
          >
            {story.headline}
          </h2>

          {/* Perspective Angle Summary / Lead */}
          <p className="watch-hero-summary">
            {currentPerspective.summary || story.brief}
          </p>

          {/* 5-Angle Interactive Switcher Bar */}
          <div className="watch-hero-angles-bar">
            <span className="watch-hero-angles-label">Flip Camera / Perspective:</span>
            <div className="watch-hero-angle-buttons">
              {perspectives.map((p, idx) => {
                const isActive = idx === activePerspectiveIndex;
                const role = p.role || p.type || 'Official';
                return (
                  <button
                    key={p.id || idx}
                    type="button"
                    className={`watch-hero-angle-btn ${isActive ? 'active' : ''}`}
                    onClick={() => setActivePerspectiveIndex(idx)}
                    style={{
                      '--angle-accent': accentColor,
                    }}
                  >
                    {getRoleIcon(role)}
                    <span>{role}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* CTA Action Row */}
          <div className="watch-hero-action-buttons">
            <button
              type="button"
              className="watch-hero-primary-btn"
              onClick={() => navigate(`/watch/${story.id}`)}
              style={{ background: accentColor }}
            >
              <Play size={16} fill="#07080B" color="#07080B" />
              <span>Watch in Full Theatre</span>
            </button>

            <button
              type="button"
              className="watch-hero-secondary-btn"
              onClick={() => onOpenFlashBite && onOpenFlashBite(story)}
            >
              <Zap size={15} fill="#00E5FF" color="#00E5FF" />
              <span>60s Smart Brevity</span>
            </button>

            <button
              type="button"
              className="watch-hero-icon-btn"
              onClick={() => onToggleSave && onToggleSave(story)}
              title={isSaved ? 'Saved to Playlist' : 'Save Video'}
            >
              <Bookmark
                size={16}
                fill={isSaved ? accentColor : 'none'}
                color={isSaved ? accentColor : 'currentColor'}
              />
            </button>

            <button
              type="button"
              className="watch-hero-icon-btn"
              onClick={handleShare}
              title="Share Video"
            >
              {copied ? <Check size={16} style={{ color: '#10b981' }} /> : <Share2 size={16} />}
            </button>
          </div>

          {/* Gen-Z Community Consensus Bar */}
          <div className="watch-hero-sentiment-wrap">
            <WatchSentimentPulse
              storyId={story.id}
              accentColor={accentColor}
            />
          </div>
        </div>
      </div>
    </section>
  );
}

