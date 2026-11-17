import React, { useEffect } from 'react';
import { X, Youtube, ExternalLink, Sparkles, Clock, User, Share2, Check } from 'lucide-react';

/**
 * EstdpodModalPlayer
 * High-fidelity YouTube modal player with guest profile and chapter takeaways.
 */
export default function EstdpodModalPlayer({ episode, onClose }) {
  const [copied, setCopied] = React.useState(false);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  if (!episode) return null;

  const handleCopyLink = () => {
    navigator.clipboard.writeText(episode.youtube_url || window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const takeaways = episode.key_takeaways || [];

  return (
    <div className="estdpod-modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div
        className="estdpod-modal-dialog"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          type="button"
          className="estdpod-modal-close"
          onClick={onClose}
          aria-label="Close modal"
        >
          <X size={20} />
        </button>

        {/* Modal Grid Layout */}
        <div className="estdpod-modal-grid">
          {/* Main 16:9 YouTube Player */}
          <div className="estdpod-player-frame-wrapper">
            <iframe
              src={episode.youtube_embed_url}
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
                <p className="estdpod-guest-sub">{episode.guest_designation}</p>
                {episode.guest_organization && (
                  <p className="estdpod-guest-org">{episode.guest_organization}</p>
                )}
              </div>
            </div>

            {/* Key Takeaways */}
            {takeaways.length > 0 && (
              <div className="estdpod-takeaways-section">
                <h4 className="estdpod-section-label">KEY CONVERSATION CHAPTERS</h4>
                <ul className="estdpod-takeaways-list">
                  {takeaways.map((item, idx) => (
                    <li key={idx} className="estdpod-takeaway-item">
                      <span className="estdpod-time-marker">{item.time || `0${idx + 1}:00`}</span>
                      <span className="estdpod-takeaway-text">{item.point || item}</span>
                    </li>
                  ))}
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
}

