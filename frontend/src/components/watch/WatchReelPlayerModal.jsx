import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  X,
  Play,
  Pause,
  Volume2,
  VolumeX,
  Heart,
  Share2,
  Bookmark,
  ChevronUp,
  ChevronDown,
  Sparkles,
  ExternalLink,
  Zap,
  Check,
  CheckCircle2,
} from 'lucide-react';
import { getCategoryMeta } from '../../constants/taxonomy';
import { generateSmartBrevityBullets } from '../../utils/flashBitesUtils';

/**
 * WatchReelPlayerModal: Gen-Z Vertical 9:16 Swipeable Video Reels Experience.
 * Features:
 * - Vertical snap scrolling between reels (ArrowUp/ArrowDown, Touch Swipe)
 * - Double-tap / click to like with floating heart burst animation
 * - Smart Brevity HUD drawer (3-bullet rapid takeaway overlay)
 * - Sound toggle (Muted by default with clear un-mute CTA)
 * - Direct deep-link to full Story Object or 16:9 Theatre mode
 */
export default function WatchReelPlayerModal({
  isOpen = false,
  reels = [],
  initialIndex = 0,
  onClose,
  savedStories = [],
  onToggleSave,
}) {
  const navigate = useNavigate();
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
  const [showHUD, setShowHUD] = useState(false);
  const [likedReels, setLikedReels] = useState(() => {
    try {
      const stored = localStorage.getItem('estd_liked_reels');
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  });
  const [floatingHeart, setFloatingHeart] = useState(false);
  const [copied, setCopied] = useState(false);

  const videoRef = useRef(null);

  // Sync index when opened
  useEffect(() => {
    if (isOpen) {
      setCurrentIndex(initialIndex);
      setIsPlaying(true);
      setShowHUD(false);
    }
  }, [isOpen, initialIndex]);

  const currentReel = reels[currentIndex] || reels[0];

  const catMeta = useMemo(() => {
    if (!currentReel) return { color: '#00E5FF', label: 'News' };
    return currentReel.categoryMeta || getCategoryMeta(currentReel.category);
  }, [currentReel]);

  const accentColor = catMeta?.color || '#00E5FF';

  const bullets = useMemo(() => {
    if (!currentReel) return [];
    return generateSmartBrevityBullets(currentReel);
  }, [currentReel]);

  const isSaved = currentReel
    ? savedStories.some((s) => String(s.id) === String(currentReel.id))
    : false;

  const isLiked = currentReel ? !!likedReels[currentReel.id] : false;

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowDown') {
        goToNext();
      } else if (e.key === 'ArrowUp') {
        goToPrev();
      } else if (e.key === ' ') {
        e.preventDefault();
        setIsPlaying((prev) => !prev);
      } else if (e.key === 'm' || e.key === 'M') {
        setIsMuted((prev) => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentIndex, reels.length, onClose]);

  // Video play/pause effect
  useEffect(() => {
    if (videoRef.current) {
      if (isPlaying) {
        videoRef.current.play().catch(() => {});
      } else {
        videoRef.current.pause();
      }
    }
  }, [isPlaying, currentIndex]);

  const goToNext = () => {
    if (currentIndex < reels.length - 1) {
      setCurrentIndex((prev) => prev + 1);
      setIsPlaying(true);
      setShowHUD(false);
    }
  };

  const goToPrev = () => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
      setIsPlaying(true);
      setShowHUD(false);
    }
  };

  const handleLike = () => {
    if (!currentReel) return;
    setLikedReels((prev) => {
      const isCurrentlyLiked = !!prev[currentReel.id];
      const next = { ...prev };
      if (isCurrentlyLiked) {
        delete next[currentReel.id];
      } else {
        next[currentReel.id] = {
          id: currentReel.id,
          headline: currentReel.headline || currentReel.title,
          category: currentReel.category,
          imageUrl: currentReel.imageUrl,
          duration: currentReel.videoRail?.[0]?.duration || '0:45',
          views: currentReel.videoRail?.[0]?.views || '180K',
          videoStreamUrl: currentReel.videoRail?.[0]?.videoStreamUrl || currentReel.videoStreamUrl,
        };
      }
      try {
        localStorage.setItem('estd_liked_reels', JSON.stringify(next));
      } catch (e) {}
      return next;
    });
    setFloatingHeart(true);
    setTimeout(() => setFloatingHeart(false), 900);
  };

  const handleDoubleTap = (e) => {
    e.stopPropagation();
    handleLike();
  };

  const handleShare = () => {
    if (!currentReel) return;
    const url = `${window.location.origin}/watch/${currentReel.id}`;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!isOpen || !currentReel) return null;

  const videoSrc =
    currentReel.videoRail?.[0]?.videoStreamUrl ||
    currentReel.videoStreamUrl ||
    'https://vjs.zencdn.net/v/oceans.mp4';

  return (
    <div className="watch-reels-modal-overlay" onClick={onClose}>
      {/* Floating Heart Reaction Animation */}
      {floatingHeart && (
        <div className="watch-reels-floating-heart">
          <Heart size={64} fill="#FF20B8" color="#FF20B8" />
        </div>
      )}

      {/* Close Button Top Right */}
      <button
        type="button"
        className="watch-reels-close-btn"
        onClick={onClose}
        aria-label="Close Reels"
      >
        <X size={22} />
      </button>

      {/* Counter Tag Top Left */}
      <div className="watch-reels-counter-badge">
        <Zap size={14} fill="#FF20B8" color="#FF20B8" />
        <span>REEL {currentIndex + 1} OF {reels.length}</span>
      </div>

      {/* Main 9:16 Video Canvas Card */}
      <div
        className="watch-reels-canvas-card"
        onClick={(e) => e.stopPropagation()}
        onDoubleClick={handleDoubleTap}
        style={{ '--reel-accent': accentColor }}
      >
        {/* Video element */}
        <video
          ref={videoRef}
          key={`reel-vid-${currentReel.id}`}
          src={videoSrc}
          poster={currentReel.imageUrl}
          playsInline
          autoPlay
          muted={isMuted}
          loop
          className="watch-reels-native-video"
          onClick={() => setIsPlaying((prev) => !prev)}
          onError={(e) => {
            if (e.target.src !== 'https://vjs.zencdn.net/v/oceans.mp4') {
              e.target.src = 'https://vjs.zencdn.net/v/oceans.mp4';
              e.target.play().catch(() => {});
            }
          }}
        />

        {/* Center Play/Pause indicator when paused */}
        {!isPlaying && (
          <div className="watch-reels-paused-overlay" onClick={() => setIsPlaying(true)}>
            <div className="watch-reels-play-bubble">
              <Play size={28} fill="#ffffff" color="#ffffff" className="play-icon-offset" />
            </div>
          </div>
        )}

        {/* Top Sound Control */}
        <button
          type="button"
          className="watch-reels-sound-btn"
          onClick={() => setIsMuted((prev) => !prev)}
          title={isMuted ? 'Unmute (M)' : 'Mute (M)'}
        >
          {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
        </button>

        {/* Right Floating Vertical Action Bar */}
        <div className="watch-reels-action-bar">
          {/* Like */}
          <button
            type="button"
            className={`watch-reels-action-btn ${isLiked ? 'liked' : ''}`}
            onClick={handleLike}
            title="Like Reel"
          >
            <Heart size={20} fill={isLiked ? '#FF20B8' : 'none'} color={isLiked ? '#FF20B8' : 'currentColor'} />
            <span className="watch-reels-action-text">{isLiked ? '1.2K' : '1.1K'}</span>
          </button>

          {/* Smart Brevity HUD toggle */}
          <button
            type="button"
            className={`watch-reels-action-btn ${showHUD ? 'hud-active' : ''}`}
            onClick={() => setShowHUD((prev) => !prev)}
            title="Toggle Smart Brevity HUD"
          >
            <Sparkles size={20} color={showHUD ? accentColor : 'currentColor'} />
            <span className="watch-reels-action-text">HUD</span>
          </button>

          {/* Save */}
          <button
            type="button"
            className="watch-reels-action-btn"
            onClick={() => onToggleSave && onToggleSave(currentReel)}
            title="Save Reel"
          >
            <Bookmark
              size={20}
              fill={isSaved ? accentColor : 'none'}
              color={isSaved ? accentColor : 'currentColor'}
            />
            <span className="watch-reels-action-text">{isSaved ? 'Saved' : 'Save'}</span>
          </button>

          {/* Share */}
          <button
            type="button"
            className="watch-reels-action-btn"
            onClick={handleShare}
            title="Share Reel"
          >
            {copied ? <Check size={20} style={{ color: '#10b981' }} /> : <Share2 size={20} />}
            <span className="watch-reels-action-text">{copied ? 'Copied' : 'Share'}</span>
          </button>

          {/* Full Article Link */}
          <button
            type="button"
            className="watch-reels-action-btn"
            onClick={() => {
              onClose();
              navigate(`/story/${currentReel.id}`);
            }}
            title="Read Full Story"
          >
            <ExternalLink size={19} />
            <span className="watch-reels-action-text">Story</span>
          </button>
        </div>

        {/* Bottom Headline & Metadata Overlay */}
        <div className="watch-reels-bottom-overlay">
          {/* Category & Publisher Row */}
          <div className="watch-reels-meta-row">
            <span className="watch-reels-category-tag" style={{ color: accentColor }}>
              {currentReel.category}
            </span>
            <span className="watch-reels-dot">•</span>
            <span className="watch-reels-source-name">{currentReel.sourceName}</span>
            <CheckCircle2 size={12} className="watch-verified-icon" />
          </div>

          {/* Headline */}
          <h3 className="watch-reels-headline">{currentReel.headline}</h3>

          {/* Smart Brevity HUD Bottom Sheet */}
          {showHUD && bullets.length > 0 && (
            <div className="watch-reels-hud-drawer">
              <div className="watch-reels-hud-header">
                <span className="watch-hud-title">⚡ 3-Bullet Smart Brevity</span>
                <button
                  type="button"
                  className="watch-hud-close"
                  onClick={() => setShowHUD(false)}
                >
                  <X size={14} />
                </button>
              </div>
              <div className="watch-reels-hud-bullets">
                {bullets.slice(0, 3).map((b, idx) => (
                  <div key={idx} className="watch-reels-hud-bullet">
                    <span className="watch-hud-bullet-icon">{b.icon || '•'}</span>
                    <span className="watch-hud-bullet-text">
                      <strong>{b.label}:</strong> {b.text || b.bullets?.[0] || ''}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Quick HUD Toggle Pill (if not already open) */}
          {!showHUD && (
            <button
              type="button"
              className="watch-reels-hud-prompt-btn"
              onClick={() => setShowHUD(true)}
            >
              <Sparkles size={12} style={{ color: accentColor }} />
              <span>Tap for 3-Bullet Key Takeaway</span>
            </button>
          )}
        </div>
      </div>

      {/* Up / Down Navigation Controls (Desktop Floating) */}
      <div className="watch-reels-nav-column" onClick={(e) => e.stopPropagation()}>
        <button
          type="button"
          className={`watch-reels-nav-btn ${currentIndex === 0 ? 'disabled' : ''}`}
          onClick={goToPrev}
          disabled={currentIndex === 0}
          title="Previous Reel (Arrow Up)"
        >
          <ChevronUp size={24} />
        </button>

        <button
          type="button"
          className={`watch-reels-nav-btn ${currentIndex === reels.length - 1 ? 'disabled' : ''}`}
          onClick={goToNext}
          disabled={currentIndex === reels.length - 1}
          title="Next Reel (Arrow Down)"
        >
          <ChevronDown size={24} />
        </button>
      </div>
    </div>
  );
}

