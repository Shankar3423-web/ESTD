import React, { useRef, useState, useEffect } from 'react';
import { Play, Video, ShieldCheck, Tv, Sparkles, Radio, Users, Compass, ChevronLeft, ChevronRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

/**
 * VideoRail: Horizontal scroll of related videos from multiple sources
 * Roles: Official, Broadcast, Analysis, Creator, Fan
 * Each card shows thumbnail, source name badge, duration, and type tag.
 */
export default function VideoRail({
  videos = [],
  storyId,
  title = 'Video Rail',
  subtitle = 'Multiple angles: Official, Broadcast, Analysis, Creator, and Fan perspectives',
  accentColor = '#00E5FF',
  onSelectVideo,
}) {
  const navigate = useNavigate();
  const scrollRef = useRef(null);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(true);

  const checkScroll = () => {
    if (scrollRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollRef.current;
      setCanScrollLeft(scrollLeft > 10);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 10);
    }
  };

  useEffect(() => {
    checkScroll();
    const handleResize = () => checkScroll();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [videos]);

  const handleScroll = (direction) => {
    if (scrollRef.current) {
      const scrollAmount = 270;
      scrollRef.current.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth',
      });
      setTimeout(checkScroll, 350);
    }
  };

  if (!videos || videos.length === 0) return null;

  const handleCardClick = (vid, idx) => {
    if (onSelectVideo) {
      onSelectVideo(vid, idx);
    } else if (storyId) {
      navigate(`/watch/${storyId}`);
    } else if (vid.url) {
      window.open(vid.url, '_blank', 'noopener,noreferrer');
    }
  };

  const getSourceIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'official':
        return <ShieldCheck size={12} />;
      case 'broadcast':
        return <Tv size={12} />;
      case 'analysis':
        return <Sparkles size={12} />;
      case 'creator':
        return <Radio size={12} />;
      case 'fan':
        return <Users size={12} />;
      default:
        return <Compass size={12} />;
    }
  };

  const ROLE_THEMES = {
    official: { color: '#00E5FF', glow: 'rgba(0, 229, 255, 0.3)', label: 'OFFICIAL' },
    broadcast: { color: '#38BDF8', glow: 'rgba(56, 189, 248, 0.3)', label: 'BROADCAST' },
    analysis: { color: '#FBBF24', glow: 'rgba(251, 191, 36, 0.3)', label: 'ANALYSIS' },
    creator: { color: '#C084FC', glow: 'rgba(192, 132, 252, 0.3)', label: 'CREATOR' },
    fan: { color: '#F472B6', glow: 'rgba(244, 114, 182, 0.3)', label: 'FAN PULSE' },
  };

  return (
    <section className="video-rail-section">
      <div className="section-header video-rail-header">
        <div className="video-rail-titles">
          <div className="section-title-wrap">
            <h3 className="section-title">
              <Video size={18} style={{ color: accentColor }} />
              <span>{title}</span>
            </h3>
            <span
              className="perspectives-count-pill"
              style={{
                borderColor: `${accentColor}44`,
                color: accentColor,
              }}
            >
              <span className="live-dot-pulse" style={{ background: accentColor }} />
              {videos.length} Perspectives Available
            </span>
          </div>
          {subtitle && <span className="section-subtitle">{subtitle}</span>}
        </div>

        <div className="rail-nav-controls">
          <button
            type="button"
            className="rail-scroll-btn"
            onClick={() => handleScroll('left')}
            disabled={!canScrollLeft}
            aria-label="Scroll left"
            title="Previous perspective"
            style={{
              opacity: canScrollLeft ? 1 : 0.35,
              cursor: canScrollLeft ? 'pointer' : 'default',
            }}
          >
            <ChevronLeft size={16} />
          </button>
          <button
            type="button"
            className="rail-scroll-btn"
            onClick={() => handleScroll('right')}
            disabled={!canScrollRight}
            aria-label="Scroll right"
            title="Next perspective"
            style={{
              opacity: canScrollRight ? 1 : 0.35,
              cursor: canScrollRight ? 'pointer' : 'default',
            }}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      <div
        className="video-rail-scroll"
        ref={scrollRef}
        onScroll={checkScroll}
      >
        {videos.map((vid, idx) => {
          const rawType = vid.type || vid.role || 'Perspective';
          const roleKey = rawType.toLowerCase();
          const theme = ROLE_THEMES[roleKey] || {
            color: accentColor,
            glow: `${accentColor}33`,
            label: rawType.toUpperCase(),
          };

          return (
            <div
              key={vid.id || idx}
              className="video-perspective-card"
              onClick={() => handleCardClick(vid, idx)}
              role="button"
              tabIndex={0}
              style={{
                '--card-accent': theme.color,
                '--card-glow': theme.glow,
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  handleCardClick(vid, idx);
                }
              }}
            >
              {/* Media Thumbnail Container with Video Overlay */}
              <div className="video-card-thumb-container">
                <div
                  className="video-card-thumb-bg"
                  style={{
                    backgroundImage: vid.thumbnail
                      ? `linear-gradient(180deg, rgba(7,8,11,0.15) 0%, rgba(7,8,11,0.88) 100%), url(${vid.thumbnail})`
                      : `linear-gradient(135deg, ${theme.color}22 0%, #12141c 100%)`,
                  }}
                />

                {/* Top Badges: Type and Duration */}
                <div className="video-thumb-top-badges">
                  <span
                    className="video-type-badge"
                    style={{
                      color: theme.color,
                      borderColor: `${theme.color}55`,
                      background: 'rgba(7, 8, 12, 0.88)',
                    }}
                  >
                    {getSourceIcon(rawType)}
                    <span>{theme.label}</span>
                  </span>

                  <span className="video-duration-tag">
                    {vid.duration || '2:30'}
                  </span>
                </div>

                {/* Hover Play Halo */}
                <div className="video-thumb-play-halo" style={{ background: theme.color }}>
                  <Play size={16} fill="#07080B" color="#07080B" />
                </div>
              </div>

              {/* Title & Summary */}
              <div className="video-card-body">
                <h4 className="perspective-title">{vid.title}</h4>

                {vid.summary && (
                  <p className="perspective-summary">
                    {vid.summary}
                  </p>
                )}

                {/* Meta: Source name & views */}
                <div className="perspective-meta">
                  <span className="perspective-source-name">{vid.source}</span>
                  <span className="perspective-watch-link" style={{ color: theme.color }}>
                    <Play size={10} fill={theme.color} />
                    Watch Angle
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
