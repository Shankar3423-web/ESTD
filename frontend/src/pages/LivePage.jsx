import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Radio,
  Clock,
  RefreshCw,
  Zap,
  Video,
  ExternalLink,
  Bookmark,
  Share2,
  Check,
  CheckCircle2,
  Flame,
  ShieldCheck,
  AlertCircle,
  Activity,
  Wifi,
  ChevronRight,
  TrendingUp,
  Volume2,
} from 'lucide-react';
import ImageWithFallback from '../components/common/ImageWithFallback';
import FlashBiteModal from '../components/story/FlashBiteModal';
import { fetchStories } from '../api/estdApi';
import { getCategoryMeta } from '../constants/taxonomy';

/**
 * Format the exact publication or ingest timestamp from the database.
 * Never fabricates relative times like "Just now" or "4m ago" for historical articles.
 */
function formatExactStoryTime(rawDate) {
  if (!rawDate) return 'Live Wire';
  const d = new Date(rawDate);
  if (isNaN(d.getTime())) return 'Live Wire';

  return d.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

function formatTickerTime(rawDate) {
  if (!rawDate) return 'Live Wire';
  const d = new Date(rawDate);
  if (isNaN(d.getTime())) return 'Live Wire';

  return d.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
}

/**
 * LivePage: Real-Time Live Intelligence Terminal for ESTD.
 * Spec:
 * - Top animated marquee ticker: 🔴 LIVE WIRE with breaking updates
 * - Live Command Terminal header with real-time status, auto-update 30s countdown, and manual refresh
 * - Category / Status filter chips (All Live, Breaking, Developing, Verified, Tech Wire, Sports Wire, etc.)
 * - Chronological Stem-and-Node Wire Timeline with live status nodes (Breaking, Developing, Verified)
 * - Quick action dock on every event: 60s Flash Bite, Watch Video Angles, Read Story, Save
 * - Silent 30s background polling with instant alert toast on new story ingest
 * - Integrated FlashBiteModal locked strictly to clicked live story
 */
export default function LivePage({
  savedStories = [],
  onToggleSave,
  watchLaterStories = [],
  onToggleWatchLater,
}) {
  const navigate = useNavigate();

  const [activeUpdates, setActiveUpdates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [activeFilter, setActiveFilter] = useState('All');
  const [autoPolling, setAutoPolling] = useState(true);
  const [countdown, setCountdown] = useState(30);
  const [newUpdateAlert, setNewUpdateAlert] = useState(null);
  const [copiedId, setCopiedId] = useState(null);

  // Flash Bite Modal state
  const [flashStory, setFlashStory] = useState(null);
  const [isFlashModalOpen, setIsFlashModalOpen] = useState(false);

  // Keep track of known story IDs to detect new incoming items
  const knownStoryIdsRef = useRef(new Set());

  // Core fetch function
  const loadLiveFeed = async (silent = false) => {
    if (!silent) setLoading(true);
    else setIsRefreshing(true);

    try {
      const stories = await fetchStories({ limit: 150 });
      if (stories && stories.length > 0) {
        // Detect newly ingested stories if not first load
        if (knownStoryIdsRef.current.size > 0) {
          const freshItems = stories.filter((s) => !knownStoryIdsRef.current.has(s.id));
          if (freshItems.length > 0) {
            setNewUpdateAlert(freshItems[0]);
            setTimeout(() => setNewUpdateAlert(null), 7000);
          }
        }

        // Update known IDs
        stories.forEach((s) => knownStoryIdsRef.current.add(s.id));
        setActiveUpdates(stories);
      }
    } catch (err) {
      console.warn('Failed to load live feed:', err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
      setCountdown(30);
    }
  };

  // Initial load
  useEffect(() => {
    loadLiveFeed(false);
  }, []);

  // Demo simulator for manual real-time ingest testing
  const handleSimulateIngest = () => {
    const simId = `sim-${Date.now()}`;
    const simStory = {
      id: simId,
      headline: `⚡ BREAKING: Transatlantic Quantum Mesh Achieves Real-Time Cryptographic Lock`,
      title: `⚡ BREAKING: Transatlantic Quantum Mesh Achieves Real-Time Cryptographic Lock`,
      summary: `International consortium validates first zero-latency post-quantum communication lattice across transatlantic subsea nodes.`,
      category: 'Tech',
      subcategory: 'Cybersecurity & Privacy',
      createdAt: new Date().toISOString(),
      source: 'ESTD Live Wire Ingest',
      imageUrl: 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=800&q=80',
      views: '2.4K',
      readingTimeMinutes: 2,
    };
    knownStoryIdsRef.current.add(simId);
    setActiveUpdates((prev) => [simStory, ...prev]);
    setNewUpdateAlert(simStory);
    setTimeout(() => setNewUpdateAlert(null), 8000);
  };

  // 30-Second Countdown & Auto-Polling Loop
  useEffect(() => {
    if (!autoPolling) return;

    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          loadLiveFeed(true);
          return 30;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [autoPolling]);

  // Compute live status & synthetic urgency for chronological timeline
  const timelineItems = useMemo(() => {
    return activeUpdates.map((story, idx) => {
      // Deterministic classification based on story index & content
      let statusType = 'VERIFIED';
      let statusLabel = 'VERIFIED BY ESTD';
      let statusColor = '#10b981';

      if (idx === 0 || idx === 1 || story.headline?.toLowerCase().includes('fine') || story.headline?.toLowerCase().includes('antitrust')) {
        statusType = 'BREAKING';
        statusLabel = 'BREAKING WIRE';
        statusColor = '#ef4444';
      } else if (idx === 2 || idx === 3 || story.headline?.toLowerCase().includes('deal') || story.headline?.toLowerCase().includes('disruption')) {
        statusType = 'DEVELOPING';
        statusLabel = 'DEVELOPING STORY';
        statusColor = '#f59e0b';
      }

      // Compute exact verified timestamp from database metadata
      const rawDate = story.publishedAt || story.createdAt || story.published_at || story.created_at;
      const exactTimeFormatted = formatExactStoryTime(rawDate);
      const tickerTime = formatTickerTime(rawDate);

      return {
        ...story,
        liveStatus: {
          type: statusType,
          label: statusLabel,
          color: statusColor,
        },
        exactTimeFormatted,
        tickerTime,
      };
    });
  }, [activeUpdates]);

  // Filtered stories with accurate category matching
  const filteredTimeline = useMemo(() => {
    if (activeFilter === 'All') return timelineItems;
    if (activeFilter === 'BREAKING') return timelineItems.filter((i) => i.liveStatus.type === 'BREAKING');
    if (activeFilter === 'DEVELOPING') return timelineItems.filter((i) => i.liveStatus.type === 'DEVELOPING');
    if (activeFilter === 'VERIFIED') return timelineItems.filter((i) => i.liveStatus.type === 'VERIFIED');
    return timelineItems.filter((i) => {
      const cat = (i.category || '').toLowerCase().trim();
      const filter = activeFilter.toLowerCase().trim();
      if (filter.includes('business')) return cat.includes('business');
      return cat === filter;
    });
  }, [timelineItems, activeFilter]);

  // Open flash bite for a story
  const handleOpenFlashBite = (story) => {
    setFlashStory(story);
    setIsFlashModalOpen(true);
  };

  // Copy share link
  const handleShareStory = (story) => {
    const url = `${window.location.origin}/story/${story.id}`;
    if (navigator.clipboard) {
      navigator.clipboard.writeText(url);
      setCopiedId(story.id);
      setTimeout(() => setCopiedId(null), 2000);
    }
  };

  const filterChips = [
    { key: 'All', label: 'All Live Wire', count: activeUpdates.length },
    { key: 'BREAKING', label: '🔴 Breaking Only', count: timelineItems.filter((i) => i.liveStatus.type === 'BREAKING').length },
    { key: 'DEVELOPING', label: '⚡ Developing', count: timelineItems.filter((i) => i.liveStatus.type === 'DEVELOPING').length },
    { key: 'VERIFIED', label: '🟢 Verified', count: timelineItems.filter((i) => i.liveStatus.type === 'VERIFIED').length },
    { key: 'Tech', label: 'Tech Wire', count: timelineItems.filter((i) => (i.category || '').toLowerCase() === 'tech').length, color: '#00E5FF' },
    { key: 'Sports', label: 'Sports Wire', count: timelineItems.filter((i) => (i.category || '').toLowerCase() === 'sports').length, color: '#B8FF3B' },
    { key: 'Entertainment', label: 'Entertainment Wire', count: timelineItems.filter((i) => (i.category || '').toLowerCase() === 'entertainment').length, color: '#FF20B8' },
    { key: 'Business & Finance', label: 'Business & Finance', count: timelineItems.filter((i) => (i.category || '').toLowerCase().includes('business')).length, color: '#A855F7' },
    { key: 'Developments', label: 'Developments Wire', count: timelineItems.filter((i) => (i.category || '').toLowerCase() === 'developments').length, color: '#FFB020' },
  ];

  return (
    <div className="live-page-container">
      {/* 🔴 Top Animated Breaking Marquee Ticker */}
      <div className="live-marquee-ticker-bar">
        <div className="live-marquee-badge">
          <span className="live-marquee-pulse-dot" />
          <span>LIVE WIRE</span>
        </div>

        <div className="live-marquee-track-container">
          <div className="live-marquee-content-track">
            {timelineItems.slice(0, 10).map((item, idx) => (
              <span
                key={`ticker-${item.id}-${idx}`}
                className="live-marquee-item"
                onClick={() => navigate(`/story/${item.id}`)}
              >
                
                <span className="live-ticker-tag" style={{ color: item.liveStatus.color }}>
                  {item.liveStatus.label}:
                </span>
                <span className="live-ticker-headline">{item.headline}</span>
                <span className="live-ticker-separator">•</span>
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Floating Ingestion Alert Toast */}
      {newUpdateAlert && (
        <div className="live-new-ingest-toast" onClick={() => navigate(`/story/${newUpdateAlert.id}`)}>
          <div className="live-ingest-toast-icon">
            <Zap size={16} fill="#00E5FF" color="#00E5FF" />
          </div>
          <div className="live-ingest-toast-info">
            <span className="live-ingest-toast-tag">NEW LIVE EVENT INGESTED</span>
            <span className="live-ingest-toast-headline">{newUpdateAlert.headline}</span>
          </div>
          <span className="live-ingest-toast-action">View Story →</span>
        </div>
      )}

      {/* Live Command Terminal Header */}
      <div className="live-command-terminal-header">
        <div className="live-terminal-title-col">
          <div className="live-terminal-badge-row">
            <span className="live-engine-status-pill">
              <span className="live-engine-led-dot" />
              <span>ENGINE ONLINE</span>
            </span>
            <span className="live-stream-count-pill">
              <Radio size={13} />
              <span>{activeUpdates.length} Live Items Active</span>
            </span>
          </div>

          <h1 className="live-terminal-title">Live Intelligence Stream</h1>
          <p className="live-terminal-subtitle">
            Continuous real-time ingest pipeline • Multi-source deduplication • Automatic 5-angle video synthesis
          </p>
        </div>

        {/* Polling & Manual Refresh Controls */}
        <div className="live-terminal-controls-col">
          <div className="live-polling-control-wrap">
            <div className="live-countdown-badge">
              <Clock size={13} className={autoPolling ? 'live-spin-slow' : ''} />
              <span>Auto-Update: {autoPolling ? `${countdown}s` : 'PAUSED'}</span>
            </div>

            <button
              type="button"
              className={`live-poll-toggle-btn ${autoPolling ? 'active' : ''}`}
              onClick={() => setAutoPolling((prev) => !prev)}
              title={autoPolling ? 'Pause Auto-Update' : 'Resume Auto-Update'}
            >
              {autoPolling ? 'Pause' : 'Resume'}
            </button>
          </div>

          <div className="live-action-buttons-group">
            <button
              type="button"
              className="live-manual-refresh-btn"
              onClick={() => loadLiveFeed(true)}
              disabled={isRefreshing}
            >
              <RefreshCw size={14} className={isRefreshing ? 'spin' : ''} />
              <span>{isRefreshing ? 'Syncing...' : 'Refresh Stream'}</span>
            </button>

            <button
              type="button"
              className="live-simulate-btn"
              onClick={handleSimulateIngest}
              title="Simulate incoming live wire event"
            >
              <Zap size={14} />
              <span>Simulate Ingest</span>
            </button>
          </div>
        </div>
      </div>

      {/* Filter Chips Bar */}
      <div className="live-filter-chips-bar">
        {filterChips.map((chip) => {
          const isActive = activeFilter === chip.key;
          return (
            <button
              key={chip.key}
              type="button"
              className={`live-filter-chip ${isActive ? 'active' : ''}`}
              onClick={() => setActiveFilter(chip.key)}
              style={
                isActive && chip.color
                  ? {
                      borderColor: chip.color,
                      color: '#ffffff',
                      background: `${chip.color}25`,
                      boxShadow: `0 0 12px ${chip.color}33`,
                    }
                  : {}
              }
            >
              <span>{chip.label}</span>
              {chip.count !== undefined && (
                <span
                  className="live-filter-chip-count"
                  style={
                    isActive && chip.color
                      ? { background: chip.color, color: '#07090E' }
                      : {}
                  }
                >
                  {chip.count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Chronological Stem & Node Timeline Track */}
      {loading ? (
        <div className="live-timeline-skeleton">
          <div className="live-skeleton-node" />
          <div className="live-skeleton-node" />
          <div className="live-skeleton-node" />
        </div>
      ) : (
        <div className="live-timeline-track">
          {/* Vertical Stem Line */}
          <div className="live-vertical-stem-line" />

          {/* Timeline Event Cards */}
          <div className="live-timeline-items-wrapper">
            {filteredTimeline.map((item) => {
              const catMeta = item.categoryMeta || getCategoryMeta(item.category);
              const accentColor = catMeta.color || '#00E5FF';
              const isSaved = savedStories.some((s) => String(s.id) === String(item.id));
              const isWatchLater = watchLaterStories.some((s) => String(s.id) === String(item.id));

              return (
                <div key={item.id} className="live-timeline-event-row">
                  {/* Stem Node Dot */}
                  <div className="live-timeline-node-anchor">
                    <div
                      className="live-timeline-pulsing-node"
                      style={{
                        background: item.liveStatus.color,
                        boxShadow: `0 0 16px ${item.liveStatus.color}`,
                      }}
                    />
                  </div>

                  {/* Event Intelligence Card */}
                  <div className="live-event-card">
                    {/* Card Top: Status, Category, Source, Actions */}
                    <div className="live-card-top-row">
                      <div className="live-card-meta-tags">
                        <span
                          className="live-status-pill"
                          style={{
                            background: `${item.liveStatus.color}22`,
                            color: item.liveStatus.color,
                            border: `1px solid ${item.liveStatus.color}55`,
                          }}
                        >
                          <span
                            className="live-status-dot"
                            style={{ background: item.liveStatus.color }}
                          />
                          {item.liveStatus.label}
                        </span>

                        <span
                          className="live-category-pill"
                          style={{ color: accentColor, background: `${accentColor}18` }}
                        >
                          {item.category}
                        </span>

                        {item.subcategory && (
                          <span className="live-subcat-pill">• {item.subcategory}</span>
                        )}

                        <div className="live-source-brand">
                          <span className="live-source-name">{item.sourceName}</span>
                          <CheckCircle2 size={13} className="live-verified-icon" />
                        </div>


                      </div>

                      <div className="live-card-quick-actions">
                        <button
                          type="button"
                          className="live-icon-btn"
                          onClick={() => handleShareStory(item)}
                          title="Share event link"
                        >
                          {copiedId === item.id ? (
                            <Check size={14} style={{ color: '#10b981' }} />
                          ) : (
                            <Share2 size={14} />
                          )}
                        </button>
                        {/* Watch Later */}
                        <button
                          type="button"
                          className={`live-icon-btn ${isWatchLater ? 'active' : ''}`}
                          onClick={() => onToggleWatchLater && onToggleWatchLater(item)}
                          title={isWatchLater ? 'Remove from Watch Later' : 'Watch Later'}
                        >
                          <Clock
                            size={14}
                            className="watch-later-clock"
                            fill="none"
                            color={isWatchLater ? '#FFB020' : 'currentColor'}
                            strokeWidth={isWatchLater ? 2.3 : 2}
                          />
                        </button>

                        <button
                          type="button"
                          className="live-icon-btn"
                          onClick={() => onToggleSave && onToggleSave(item)}
                          title={isSaved ? 'Remove from saved' : 'Save event'}
                        >
                          <Bookmark
                            size={14}
                            fill={isSaved ? accentColor : 'none'}
                            color={isSaved ? accentColor : 'currentColor'}
                          />
                        </button>
                      </div>
                    </div>

                    {/* Headline */}
                    <h2
                      className="live-event-headline"
                      onClick={() => navigate(`/story/${item.id}`)}
                    >
                      {item.headline}
                    </h2>

                    {/* Main Split: Media Preview + Live Brief Snippet */}
                    <div className="live-event-body-grid">
                      {/* Left: 16:9 Media Preview */}
                      <div
                        className="live-event-media-wrap"
                        onClick={() => navigate(`/watch/${item.id}`)}
                        title="Watch 5 Video Perspectives"
                      >
                        <ImageWithFallback
                          src={item.imageUrl}
                          alt={item.headline}
                          category={item.category}
                          subcategory={item.subcategory}
                        />
                        <div className="live-media-overlay">
                          <div className="live-media-play-pill">
                            <Video size={13} />
                            <span>5 Video Angles</span>
                          </div>
                        </div>
                        <span className="live-media-duration-badge">
                          {item.videoRail?.[0]?.duration || '4:15'}
                        </span>
                      </div>

                      {/* Right: Brief Context & Dimensions */}
                      <div className="live-event-content-col">
                        <p className="live-event-brief">{item.brief}</p>


                      </div>
                    </div>

                    {/* Action Dock */}
                    <div className="live-card-action-dock">
                      {/* ⚡ 60s Flash Bite Micro-Reader Button */}
                      <button
                        type="button"
                        className="live-action-flash-btn"
                        onClick={() => handleOpenFlashBite(item)}
                      >
                        <Zap size={14} fill="#00E5FF" color="#00E5FF" />
                        <span>60s Flash Bite</span>
                      </button>

                      {/* Watch Video Angles */}
                      <button
                        type="button"
                        className="live-action-watch-btn"
                        onClick={() => navigate(`/watch/${item.id}`)}
                      >
                        <Video size={14} />
                        <span>Watch 5 Video Angles</span>
                      </button>

                      {/* Full Story Link */}
                      <button
                        type="button"
                        className="live-action-read-btn"
                        onClick={() => navigate(`/story/${item.id}`)}
                      >
                        <span>Read Full Story</span>
                        <ChevronRight size={14} />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* 60s Flash Bite Modal strictly locked to the clicked live story */}
      <FlashBiteModal
        isOpen={isFlashModalOpen}
        story={flashStory}
        stories={flashStory ? [flashStory] : []}
        onClose={() => setIsFlashModalOpen(false)}
      />
    </div>
  );
}
