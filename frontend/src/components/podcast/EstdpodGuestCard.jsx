import React from 'react';
import { Play, Clock, Sparkles, Youtube, ExternalLink } from 'lucide-react';

/**
 * EstdpodGuestCard
 * High-impact guest spotlight card modeled after premier podcast showcase designs.
 */
export default function EstdpodGuestCard({ episode, onSelect, index = 0 }) {
  if (!episode) return null;

  const episodeNumber = String(index + 1).padStart(2, '0');
  const durationText = episode.duration || 'Full Episode';
  const thumbnail = episode.thumbnail_url || `https://i.ytimg.com/vi/${episode.youtube_video_id}/maxresdefault.jpg`;

  return (
    <article
      className="estdpod-guest-card"
      onClick={() => onSelect && onSelect(episode)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect && onSelect(episode);
        }
      }}
      aria-label={`Watch ESTDPOD Episode: ${episode.title}`}
    >
      {/* Poster / Artwork Container */}
      <div className="estdpod-poster-wrapper">
        <img
          src={thumbnail}
          alt={episode.title}
          className="estdpod-poster-image"
          loading="lazy"
          onError={(e) => {
            e.currentTarget.src = `https://i.ytimg.com/vi/${episode.youtube_video_id}/hqdefault.jpg`;
          }}
        />

        {/* Gradient Overlay */}
        <div className="estdpod-poster-gradient" />

        {/* Top Badges */}
        <div className="estdpod-badges-row">
          <span className="estdpod-ep-pill">
            <span className="estdpod-live-dot" />
            PODCAST {episodeNumber}
          </span>
          <span className="estdpod-duration-pill">
            <Clock size={11} />
            {durationText}
          </span>
        </div>

        {/* Play Button Overlay */}
        <div className="estdpod-play-overlay">
          <div className="estdpod-play-btn" aria-hidden="true">
            <Play size={22} fill="white" className="estdpod-play-icon" />
          </div>
        </div>

        {/* Category Pill on bottom of image */}
        <div className="estdpod-cat-tag">
          <Sparkles size={11} className="text-amber-400" />
          {episode.category || 'Tech & AI'}
        </div>
      </div>

      {/* Guest & Episode Details */}
      <div className="estdpod-card-body">
        {/* Topic Headline */}
        <h3 className="estdpod-card-title" title={episode.title}>
          {episode.title}
        </h3>

        {/* Guest Name */}
        <div className="estdpod-guest-meta">
          <h4 className="estdpod-guest-name">
            {episode.guest_name || 'ESTD Special Guests'}
          </h4>
          <p className="estdpod-guest-role">
            {episode.guest_designation || episode.guest_organization || 'Industry Experts'}
          </p>
        </div>

        {/* Footer Action */}
        <div className="estdpod-card-footer">
          <span className="estdpod-listen-btn">
            <Play size={12} fill="currentColor" /> Watch Episode
          </span>
          <a
            href={episode.youtube_url || `https://www.youtube.com/watch?v=${episode.youtube_video_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="estdpod-yt-link"
            onClick={(e) => e.stopPropagation()}
            title="Open on YouTube"
          >
            <Youtube size={14} className="text-red-500" />
            <span>@ESTDPOD</span>
          </a>
        </div>
      </div>
    </article>
  );
}

