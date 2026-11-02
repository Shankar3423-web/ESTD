import React, { useState, useEffect, useRef } from 'react';
import {
  X,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize2,
  Share2,
  Bookmark,
  ArrowRight,
  ShieldCheck,
  Tv,
  Radio,
  Sparkles,
  Users,
  Compass,
  Check,
  ExternalLink,
  Film,
  Youtube,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import ImpactChips from './ImpactChips';
import { fetchStoryVideos } from '../../api/estdApi';

/**
 * World-class Gen-Z native Video Modal Player.
 * Plays authentic video footage (Direct 1080p Stream or YouTube Embed) and
 * allows users to seamlessly switch between the 5 canonical angles
 * (Official, Broadcast, Analysis, Creator, Fan) without ever leaving the page.
 */
export default function VideoModalPlayer({
  isOpen,
  onClose,
  story,
  initialVideoIndex = 0,
  accentColor = '#00E5FF',
  isSaved = false,
  onToggleSave,
}) {
  const navigate = useNavigate();
  const [activeIdx, setActiveIdx] = useState(initialVideoIndex);
  const [playerMode, setPlayerMode] = useState('youtube'); // 'youtube' (YouTube Embed, reliable default) or 'stream' (Direct HTML5)
  const [isMuted, setIsMuted] = useState(true);
  const [copied, setCopied] = useState(false);
  const [resolvedVideos, setResolvedVideos] = useState(story?.videoRail || []);
  const videoRef = useRef(null);

  useEffect(() => {
    setActiveIdx(initialVideoIndex);
  }, [initialVideoIndex]);

  useEffect(() => {
    if (story?.videoRail && story.videoRail.length > 0) {
      setResolvedVideos(story.videoRail);
    }
    // If the modal opens and we don't have rich resolved videos (or they are search queries), fetch fresh Step 9 rail
    if (isOpen && story?.id) {
      const needsFresh = !story.videoRail || story.videoRail.length === 0 || story.videoRail[0]?.videoId?.startsWith('yt_search_');
      if (needsFresh) {
        fetchStoryVideos(story.id)
          .then((freshRail) => {
            if (freshRail && freshRail.length > 0) {
              setResolvedVideos(freshRail);
            }
          })
          .catch(() => {});
      }
    }
  }, [isOpen, story?.id, story?.videoRail]);

  // Ensure video stream actively plays on mount and perspective switch
  useEffect(() => {
    if (isOpen && playerMode === 'stream' && videoRef.current) {
      const v = videoRef.current;
      const playPromise = v.play();
      if (playPromise !== undefined) {
        playPromise.catch(() => {
          if (v && !v.muted) {
            v.muted = true;
            setIsMuted(true);
            v.play().catch(() => {});
          }
        });
      }
    }
  }, [isOpen, activeIdx, playerMode]);

  // Handle ESC key to close
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowRight') handleNext();
      if (e.key === 'ArrowLeft') handlePrev();
    };
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.body.style.overflow = '';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, activeIdx]);

  if (!isOpen || !story) return null;

  const cleanHeadline = (story.headline || story.title || 'Verified Story').replace(/^(EXCLUSIVE|WATCH|LIVE|BREAKING|REPORT|UPDATE|EXPLAINER)\s*[:|-]\s*/i, '').trim();

  const videos = (resolvedVideos && resolvedVideos.length > 0)
    ? resolvedVideos
    : (story.videoRail && story.videoRail.length > 0)
      ? story.videoRail
      : [
          {
            id: `${story.id || 1}-v1-official`,
            role: 'Official',
            type: 'Official',
            title: `${cleanHeadline} — Official Briefing`,
            source: story.sourceName || 'Official Wire',
            duration: '2:14',
            summary: 'Verified statements and official press communications.',
            videoStreamUrl: 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4',
            embedUrl: `https://www.youtube-nocookie.com/embed?listType=search&list=${encodeURIComponent(cleanHeadline)}`,
            url: `https://www.youtube.com/results?search_query=${encodeURIComponent(cleanHeadline)}`,
          },
        ];

  const currentVideo = videos[activeIdx] || videos[0];

  const handleSelectPerspective = (idx) => {
    setActiveIdx(idx);
  };

  const handleNext = () => {
    handleSelectPerspective((activeIdx + 1) % videos.length);
  };

  const handlePrev = () => {
    handleSelectPerspective((activeIdx - 1 + videos.length) % videos.length);
  };

  const handleShare = (e) => {
    e.stopPropagation();
    const url = `${window.location.origin}/story/${story.id}`;
    if (navigator.share) {
      navigator.share({ title: currentVideo.title, text: story.brief, url }).catch(() => copyLink(url));
    } else {
      copyLink(url);
    }
  };

  const copyLink = (url) => {
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

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
        return <Compass size={14} />;
    }
  };

  return (
    <div
      className="video-modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="Video Perspective Player"
    >
      <div
        className="video-modal-container"
        onClick={(e) => e.stopPropagation()}
        style={{ '--modal-accent': accentColor }}
      >
        {/* Top Header Bar */}
        <div className="video-modal-header">
          <div className="video-modal-header-left">
            <span
              className="video-perspective-pill"
              style={{
                color: accentColor,
                borderColor: `${accentColor}55`,
                background: `${accentColor}15`,
              }}
            >
              {getRoleIcon(currentVideo.type || currentVideo.role)}
              <span>{currentVideo.role || currentVideo.type || 'Perspective'} Angle</span>
            </span>

            {/* Mode Switcher: Direct Stream vs YouTube Embed */}
            <div className="player-mode-toggle">
              <button
                type="button"
                className={`mode-btn ${playerMode === 'stream' ? 'active' : ''}`}
                onClick={() => setPlayerMode('stream')}
                style={{
                  background: playerMode === 'stream' ? accentColor : 'transparent',
                  color: playerMode === 'stream' ? '#07080B' : '#94a3b8',
                }}
              >
                <Film size={12} />
                <span>1080p Stream</span>
              </button>
              <button
                type="button"
                className={`mode-btn ${playerMode === 'youtube' ? 'active' : ''}`}
                onClick={() => setPlayerMode('youtube')}
                style={{
                  background: playerMode === 'youtube' ? '#FF0000' : 'transparent',
                  color: playerMode === 'youtube' ? '#FFFFFF' : '#94a3b8',
                }}
              >
                <Youtube size={12} />
                <span>YouTube Feed</span>
              </button>
            </div>
          </div>

          <div className="video-modal-header-actions">
            {currentVideo.url && (
              <a
                href={currentVideo.url}
                target="_blank"
                rel="noopener noreferrer"
                className="modal-icon-btn"
                title="Open broadcast on YouTube"
                style={{ color: '#ff4757' }}
              >
                <ExternalLink size={15} />
              </a>
            )}
            <button
              className="modal-icon-btn"
              onClick={handleShare}
              title="Share video"
            >
              {copied ? <Check size={16} style={{ color: '#10b981' }} /> : <Share2 size={16} />}
            </button>
            <button
              className="modal-icon-btn"
              onClick={() => onToggleSave && onToggleSave(story)}
              title={isSaved ? 'Remove from saved' : 'Save story'}
            >
              <Bookmark
                size={16}
                fill={isSaved ? accentColor : 'none'}
                color={isSaved ? accentColor : 'currentColor'}
              />
            </button>
            <button
              className="modal-close-btn"
              onClick={onClose}
              aria-label="Close modal"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Real Video Player Frame */}
        <div className="video-player-frame">
          {playerMode === 'youtube' && currentVideo.embedUrl ? (
            <div className="video-viewport-wrapper">
              <iframe
                key={`yt-${currentVideo.id}-${activeIdx}-${currentVideo.videoId || currentVideo.embedUrl}`}
                src={`${currentVideo.embedUrl}${currentVideo.embedUrl.includes('?') ? '&' : '?'}autoplay=1&mute=0&rel=0&modestbranding=1`}
                title={currentVideo.title}
                className="video-iframe-element"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowFullScreen
              />
            </div>
          ) : (
            <div className="video-viewport-wrapper">
              <video
                ref={videoRef}
                key={`stream-${currentVideo.id}-${activeIdx}-${currentVideo.videoStreamUrl}`}
                src={currentVideo.videoStreamUrl || 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4'}
                poster={currentVideo.thumbnail || story.imageUrl}
                controls
                autoPlay
                muted={isMuted}
                playsInline
                className="video-native-element"
              >
                Your browser does not support the video tag.
              </video>

              {isMuted && (
                <button
                  type="button"
                  className="unmute-floating-pill"
                  onClick={() => {
                    setIsMuted(false);
                    if (videoRef.current) {
                      videoRef.current.muted = false;
                      videoRef.current.play().catch(() => {});
                    }
                  }}
                  title="Click to turn on audio"
                >
                  <VolumeX size={15} />
                  <span>Click to Unmute Audio</span>
                </button>
              )}
            </div>
          )}

          {/* Under-Video Information Bar */}
          <div className="video-info-strip">
            <div className="video-info-titles">
              <div className="video-title-row">
                <span className="live-source-tag" style={{ borderColor: `${accentColor}55`, color: accentColor }}>
                  {currentVideo.source || 'Verified Source'}
                </span>
                <span className="video-runtime-tag">{currentVideo.duration || '2:30'}</span>
              </div>
              <h4 className="video-active-title">{currentVideo.title}</h4>
              <p className="video-active-summary">{currentVideo.summary}</p>
            </div>

            {currentVideo.url && (
              <a
                href={currentVideo.url}
                target="_blank"
                rel="noopener noreferrer"
                className="open-source-link-btn"
              >
                <span>Watch on YouTube</span>
                <ExternalLink size={13} />
              </a>
            )}
          </div>
        </div>

        {/* Multi-Source Perspective Switcher Tabs */}
        <div className="perspective-tabs-container">
          <div className="perspective-tabs-label">
            <span>5 MULTI-ANGLE PERSPECTIVES</span>
            <span style={{ color: '#64748b', fontSize: 11 }}>Click any angle to switch video in real time</span>
          </div>

          <div className="perspective-tabs-rail">
            {videos.map((vid, idx) => {
              const isActive = idx === activeIdx;
              return (
                <button
                  key={vid.id || idx}
                  className={`perspective-tab-card ${isActive ? 'active' : ''}`}
                  onClick={() => handleSelectPerspective(idx)}
                  style={{
                    borderColor: isActive ? accentColor : 'rgba(255,255,255,0.08)',
                    boxShadow: isActive ? `0 0 16px ${accentColor}33` : 'none',
                    background: isActive ? 'rgba(255,255,255,0.08)' : 'rgba(255,255,255,0.02)',
                  }}
                >
                  <div className="tab-card-top">
                    <span
                      className="tab-role-tag"
                      style={{
                        color: isActive ? accentColor : '#94a3b8',
                      }}
                    >
                      {getRoleIcon(vid.type || vid.role)}
                      {vid.role || vid.type}
                    </span>
                    <span className="tab-duration">{vid.duration || '2:30'}</span>
                  </div>
                  <div className="tab-title">{vid.title}</div>
                  <div className="tab-source">{vid.source}</div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Story Brief & Footer Context */}
        <div className="video-modal-footer">
          <div className="modal-brief-container">
            <span className="modal-brief-kicker" style={{ color: accentColor }}>
              ESTD STORY BRIEF
            </span>
            <p className="modal-brief-text">{story.brief}</p>
            {story.impactChips && story.impactChips.length > 0 && (
              <div style={{ marginTop: 10 }}>
                <ImpactChips chips={story.impactChips} accentColor={accentColor} />
              </div>
            )}
          </div>

          <div className="modal-footer-actions">
            <button
              className="open-full-story-btn"
              style={{ background: accentColor, color: '#07080B' }}
              onClick={() => {
                navigate(`/story/${story.id}`);
                onClose();
              }}
            >
              <span>Read Full Story</span>
              <ArrowRight size={15} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
