import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import {
  X,
  ArrowLeft,
  Youtube,
  Sparkles,
  Clock,
  User,
  Share2,
  Check,
  Mic,
} from 'lucide-react';

function parseTimestampToSeconds(timeStr) {
  if (!timeStr || typeof timeStr !== 'string') return 0;
  const parts = timeStr
    .trim()
    .split(':')
    .map((p) => parseInt(p, 10))
    .filter((n) => !Number.isNaN(n));
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  if (parts.length === 1) return parts[0];
  return 0;
}

function buildEmbedUrl(episode, startSeconds = 0) {
  const base =
    episode.youtube_embed_url ||
    `https://www.youtube-nocookie.com/embed/${episode.youtube_video_id}?autoplay=1&rel=0`;
  try {
    const url = new URL(base);
    url.searchParams.set('autoplay', '1');
    url.searchParams.set('rel', '0');
    url.searchParams.set('modestbranding', '1');
    if (startSeconds > 0) {
      url.searchParams.set('start', String(startSeconds));
    } else {
      url.searchParams.delete('start');
    }
    return url.toString();
  } catch {
    return startSeconds > 0 ? `${base}&start=${startSeconds}` : base;
  }
}

/**
 * EstdpodModalPlayer
 * Full-viewport portal YouTube modal player with explicit Back/Stop bar,
 * unclipped player controls & timeline, and interactive chapter markers.
 */
export default function EstdpodModalPlayer({ episode, onClose }) {
  const [copied, setCopied] = useState(false);
  const [activeChapterIdx, setActiveChapterIdx] = useState(0);
  const [startSeconds, setStartSeconds] = useState(0);

  useEffect(() => {
    setActiveChapterIdx(0);
    setStartSeconds(0);
  }, [episode?.youtube_video_id, episode?.id]);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = prevOverflow;
    };
  }, [onClose]);

  if (!episode) return null;

  const handleCopyLink = () => {
    navigator.clipboard.writeText(episode.youtube_url || window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleJumpToChapter = (item, idx) => {
    const sec = parseTimestampToSeconds(item?.time);
    setActiveChapterIdx(idx);
    setStartSeconds(sec);
  };

  const takeaways = episode.key_takeaways || [];
  const embedSrc = buildEmbedUrl(episode, startSeconds);

  const modalContent = (
    <div className="estdpod-modal-backdrop" onClick={onClose} role="dialog" aria-modal="true" aria-label={episode.title}>
      <div
        className="estdpod-modal-dialog"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Dedicated Modal Header Bar (Always Visible Back/Stop + Close) */}
        <div className="estdpod-modal-topbar">
          <button
            type="button"
            className="estdpod-modal-back-btn"
            onClick={onClose}
            aria-label="Back and stop playback"
          >
            <ArrowLeft size={16} />
            <span>Back</span>
          </button>

          <div className="estdpod-modal-topbar-title">
            <Mic size={13} className="text-red-500" />
            <span>ESTDPOD ORIGINALS</span>
          </div>

          <button
            type="button"
            className="estdpod-modal-close"
            onClick={onClose}
            aria-label="Close modal"
            title="Stop & Close (Esc)"
          >
            <X size={18} />
          </button>
        </div>

        {/* Modal Grid Layout */}
        <div className="estdpod-modal-grid">
          {/* Main 16:9 YouTube Player (Unclipped timeline & controls) */}
          <div className="estdpod-player-frame-wrapper">
            <iframe
              key={`${episode.youtube_video_id}-${startSeconds}`}
              src={embedSrc}
              title={episode.title}
              className="estdpod-iframe"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              allowFullScreen
            />
          </div>

          {/* Right Information & Takeaways Drawer */}
          <div className="estdpod-modal-details">
            <div className="estdpod-modal-badge-row">
              <span className="estdpod-tag-pill">
                <Sparkles size={12} className="text-amber-400" />
                {episode.category || 'Tech & AI'}
              </span>
              <span className="estdpod-duration-pill">
                <Clock size={12} />
                {episode.duration || 'Full Episode'}
              </span>
            </div>

            <h2 className="estdpod-modal-title">{episode.title}</h2>

            {/* Featured Guest Highlight Box */}
            <div className="estdpod-guest-box">
              <div className="estdpod-guest-avatar">
                {episode.guest_avatar_url ? (
                  <img
                    src={episode.guest_avatar_url}
                    alt={episode.guest_name}
                    className="w-full h-full object-cover rounded-full"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                ) : (
                  <User size={20} className="text-zinc-400" />
                )}
              </div>
              <div className="estdpod-guest-text">
                <p className="estdpod-guest-label">FEATURED GUEST / PANEL</p>
                <h4 className="estdpod-guest-title">{episode.guest_name || 'Industry Leaders'}</h4>
                {episode.guest_designation && (
                  <p className="estdpod-guest-sub">{episode.guest_designation}</p>
                )}
                {episode.guest_organization && (
                  <p className="estdpod-guest-org">{episode.guest_organization}</p>
                )}
              </div>
            </div>

            {/* Interactive Chapter Timeline */}
            {takeaways.length > 0 && (
              <div className="estdpod-takeaways-section">
                <h4 className="estdpod-section-label">KEY CONVERSATION CHAPTERS</h4>
                <ul className="estdpod-takeaways-list">
                  {takeaways.map((item, idx) => {
                    const isActive = activeChapterIdx === idx;
                    const timeLabel = item.time || `0${idx + 1}:00`;
                    const pointText = item.point || item;
                    return (
                      <li key={idx}>
                        <button
                          type="button"
                          onClick={() => handleJumpToChapter(item, idx)}
                          className={`estdpod-takeaway-item estdpod-chapter-btn ${isActive ? 'active' : ''}`}
                          title={`Jump to ${timeLabel}`}
                        >
                          <span className="estdpod-time-marker">{timeLabel}</span>
                          <span className="estdpod-takeaway-text">{pointText}</span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}

            {/* Description Snippet */}
            {episode.description && (
              <div className="estdpod-desc-section">
                <h4 className="estdpod-section-label">ABOUT THIS EPISODE</h4>
                <p className="estdpod-desc-text">{episode.description}</p>
              </div>
            )}

            {/* Action Bar */}
            <div className="estdpod-modal-actions">
              <a
                href={episode.youtube_url || `https://www.youtube.com/watch?v=${episode.youtube_video_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="estdpod-btn-youtube"
              >
                <Youtube size={16} fill="white" />
                Watch on YouTube @ESTDPOD
              </a>
              <button
                type="button"
                className="estdpod-btn-share"
                onClick={handleCopyLink}
                title="Copy Episode Link"
              >
                {copied ? <Check size={16} className="text-emerald-400" /> : <Share2 size={16} />}
                <span>{copied ? 'Copied!' : 'Share'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return typeof document !== 'undefined' ? createPortal(modalContent, document.body) : modalContent;
}
