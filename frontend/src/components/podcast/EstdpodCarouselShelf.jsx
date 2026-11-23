import React, { useState, useEffect, useRef } from 'react';
import { ChevronLeft, ChevronRight, Mic, Youtube, Sparkles, Play, Headphones } from 'lucide-react';
import EstdpodGuestCard from './EstdpodGuestCard';
import EstdpodModalPlayer from './EstdpodModalPlayer';
import { fetchEstdpodEpisodes, DEFAULT_ESTDPOD_EPISODES } from '../../api/estdApi';

/**
 * EstdpodCarouselShelf
 * Compact, engaging podcast showcase section.
 * When only 1 episode: horizontal banner layout (info left, card right).
 * When multiple episodes: carousel grid.
 */
export default function EstdpodCarouselShelf({ category = null }) {
  const [episodes, setEpisodes] = useState(DEFAULT_ESTDPOD_EPISODES);
  const [loading, setLoading] = useState(false);
  const [selectedEpisode, setSelectedEpisode] = useState(null);
  const scrollContainerRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    async function loadEpisodes() {
      try {
        const data = await fetchEstdpodEpisodes(category, 20);
        if (mounted && data && data.length > 0) {
          setEpisodes(data);
        }
      } catch (err) {
        console.warn('Failed to load ESTDPOD episodes:', err);
      }
    }
    // Defer network call so main feed loads first; component already has DEFAULT_ESTDPOD_EPISODES
    const timer = setTimeout(loadEpisodes, 1500);
    return () => {
      mounted = false;
      clearTimeout(timer);
    };
  }, [category]);

  const handleScroll = (direction) => {
    if (!scrollContainerRef.current) return;
    const scrollAmount = 360;
    scrollContainerRef.current.scrollBy({
      left: direction === 'left' ? -scrollAmount : scrollAmount,
      behavior: 'smooth',
    });
  };

  const displayList = episodes && episodes.length > 0 ? episodes : DEFAULT_ESTDPOD_EPISODES;
  const isSingleEpisode = displayList.length === 1;

  return (
    <section
      className={`estdpod-shelf-section ${isSingleEpisode ? 'estdpod-shelf-compact' : ''}`}
      id="estdpod"
      aria-label="ESTDPOD Originals"
    >
      <div className="estdpod-shelf-container">
        {isSingleEpisode ? (
          /* ── COMPACT BANNER LAYOUT (1 episode) ── */
          <div className="estdpod-banner-layout">
            <div className="estdpod-banner-info">
              <div className="estdpod-header-eyebrow">
                <span className="estdpod-mic-badge">
                  <Mic size={13} className="text-red-500 animate-pulse" />
                  ESTDPOD ORIGINALS
                </span>
              </div>
              <h2 className="estdpod-banner-title">
                <span className="estdpod-heading-highlight">Latest</span> Episode
              </h2>
              <p className="estdpod-banner-desc">
                {displayList[0].title || 'Conversations That Inspire. Ideas That Innovate.'}
              </p>
              {displayList[0].guest_name && (
                <div className="estdpod-banner-guest">
                  <Headphones size={14} />
                  <span>
                    <strong>{displayList[0].guest_name}</strong>
                    {displayList[0].guest_title ? ` — ${displayList[0].guest_title}` : ''}
                  </span>
                </div>
              )}
              <div className="estdpod-banner-actions">
                <button
                  type="button"
                  className="estdpod-banner-play-btn"
                  onClick={() => setSelectedEpisode(displayList[0])}
                >
                  <Play size={16} fill="#fff" />
                  <span>Watch Now</span>
                </button>
                <a
                  href="https://www.youtube.com/@ESTDPOD?sub_confirmation=1"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="estdpod-yt-subscribe-btn"
                  title="Subscribe to @ESTDPOD on YouTube"
                >
                  <Youtube size={15} fill="#FF0000" color="#FF0000" />
                  <span>Subscribe</span>
                </a>
              </div>
            </div>
            <div className="estdpod-banner-card-wrap">
              <EstdpodGuestCard
                episode={displayList[0]}
                index={0}
                onSelect={(selected) => setSelectedEpisode(selected)}
              />
            </div>
          </div>
        ) : (
          /* ── MULTI-EPISODE CAROUSEL LAYOUT ── */
          <>
            <div className="estdpod-header-block">
              <div className="estdpod-header-eyebrow">
                <span className="estdpod-mic-badge">
                  <Mic size={13} className="text-red-500 animate-pulse" />
                  ESTDPOD ORIGINALS
                </span>
                <a
                  href="https://www.youtube.com/@ESTDPOD?sub_confirmation=1"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="estdpod-yt-subscribe-btn"
                  title="Subscribe to @ESTDPOD on YouTube"
                >
                  <Youtube size={15} fill="#FF0000" color="#FF0000" />
                  <span>Subscribe on YouTube</span>
                </a>
              </div>
              <h2 className="estdpod-main-heading">
                <span className="estdpod-heading-highlight">Guests</span> we have had on our channel
              </h2>
              <p className="estdpod-sub-heading">
                Conversations That Inspire. Ideas That Innovate. — Episodes That Have Captured Hearts and Minds
              </p>
            </div>

            <div className="estdpod-carousel-wrapper">
              <button
                type="button"
                className="estdpod-nav-arrow estdpod-nav-left"
                onClick={() => handleScroll('left')}
                aria-label="Scroll left"
              >
                <ChevronLeft size={22} />
              </button>

              <div className="estdpod-cards-track" ref={scrollContainerRef}>
                {loading ? (
                  [...Array(3)].map((_, idx) => (
                    <div key={idx} className="estdpod-guest-card-skeleton animate-pulse" />
                  ))
                ) : (
                  displayList.map((ep, idx) => (
                    <EstdpodGuestCard
                      key={ep.id || ep.youtube_video_id || idx}
                      episode={ep}
                      index={idx}
                      onSelect={(selected) => setSelectedEpisode(selected)}
                    />
                  ))
                )}
              </div>

              <button
                type="button"
                className="estdpod-nav-arrow estdpod-nav-right"
                onClick={() => handleScroll('right')}
                aria-label="Scroll right"
              >
                <ChevronRight size={22} />
              </button>
            </div>
          </>
        )}
      </div>

      {/* Interactive Modal Player */}
      {selectedEpisode && (
        <EstdpodModalPlayer
          episode={selectedEpisode}
          onClose={() => setSelectedEpisode(null)}
        />
      )}
    </section>
  );
}

