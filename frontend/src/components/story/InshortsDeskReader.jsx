import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Volume2,
  VolumeX,
  Bookmark,
  Share2,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  Check,
  Video,
  Clock,
  Sparkles,
  Heart,
  ChevronUp,
  ChevronDown,
  RotateCcw,
  LayoutGrid,
  ShieldCheck,
  Tv,
  Radio,
  Users,
  Layers,
  Globe,
} from 'lucide-react';
import ImageWithFallback from '../common/ImageWithFallback';
import VideoModalPlayer from './VideoModalPlayer';
import { getCategoryMeta, slugify } from '../../constants/taxonomy';
import { toggleStoryLike } from '../../api/estdApi';
import { trackArticleRead } from '../../utils/readingHistory';

/**
 * InshortsDeskReader: The High-Octane Desktop Inshorts-Style News Experience.
 *
 * Implements the sacred ESTD Story Contract for desktop:
 * - Headline (<= 12 words, spoken language)
 * - 50-70 word one-paragraph summary (What, Why, What changes)
 * - Unified single-source intelligence meta row (Category, Subcategory, Reporter, Scope, Time)
 * - 4-Beat Context preview (Background Origin, Trigger Catalyst, Key Development, Forward Horizon)
 * - 5 Multi-Angle Video Perspectives dock
 * - Integrated 60s AI Voiceover brief
 * - Native desktop controls: Keyboard (J/K, Arrows, S, Space, Enter) + Mouse Wheel Snap
 * - Seamless end-of-pack category continuation gateway (zero blank screen crashes)
 */
export default function InshortsDeskReader({
  stories = [],
  savedStories = [],
  onToggleSave,
  watchLaterStories = [],
  onToggleWatchLater,
  onExitToBento,
  initialIndex = 0,
  currentCategory = 'All',
  nextCategory = null,
  onNextCategory,
}) {
  const navigate = useNavigate();

  // Retain all loaded stories for continuous reading (never artificially cut off at 10)
  const dailyPack = useMemo(() => {
    if (!stories || !Array.isArray(stories)) return [];
    return stories;
  }, [stories]);

  const totalStories = dailyPack.length;
  const [currentIndex, setCurrentIndex] = useState(initialIndex);
  const [copied, setCopied] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [audioSpeechInstance, setAudioSpeechInstance] = useState(null);

  // Video Lightbox Modal State
  const [isVideoModalOpen, setIsVideoModalOpen] = useState(false);
  const [modalVideoIndex, setModalVideoIndex] = useState(0);

  // Persistent Likes State
  const [likedMap, setLikedMap] = useState(() => {
    try {
      const stored = localStorage.getItem('estd_liked_stories');
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  });

  // End of pack condition
  const isEndOfPack = totalStories > 0 && currentIndex >= totalStories;

  // Safe active story: fallback to last/first story when on completion card so hooks can compute safely
  const activeStory = !isEndOfPack
    ? dailyPack[currentIndex] || dailyPack[0] || null
    : dailyPack[totalStories - 1] || dailyPack[0] || null;

  // Stop audio voiceover
  const stopAudio = useCallback(() => {
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsPlayingAudio(false);
    setAudioSpeechInstance(null);
  }, []);

  // Track article read when card changes
  useEffect(() => {
    if (activeStory && !isEndOfPack) {
      trackArticleRead(activeStory);
    }
  }, [currentIndex, activeStory, isEndOfPack]);

  // Stop audio on index change
  useEffect(() => {
    stopAudio();
  }, [currentIndex, stopAudio]);

  // Clean up speech synthesis on unmount
  useEffect(() => {
    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  // Reset index to 0 when incoming stories collection changes (e.g. category change)
  useEffect(() => {
    setCurrentIndex(0);
    stopAudio();
  }, [stories, stopAudio]);

  // Audio Voiceover synthesis (60s AI Brief)
  const handleToggleAudio = useCallback(() => {
    if (!activeStory) return;

    if (isPlayingAudio) {
      stopAudio();
      return;
    }

    if (!('speechSynthesis' in window)) {
      alert('Speech synthesis is not supported on this browser.');
      return;
    }

    window.speechSynthesis.cancel();

    const textToRead = `${activeStory.headline}. ${cleanBrief || ''}`;
    const utterance = new SpeechSynthesisUtterance(textToRead);
    utterance.rate = 1.05;
    utterance.pitch = 1.0;

    const voices = window.speechSynthesis.getVoices();
    const englishVoice = voices.find((v) => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Premium')));
    if (englishVoice) {
      utterance.voice = englishVoice;
    }

    utterance.onend = () => {
      setIsPlayingAudio(false);
    };

    utterance.onerror = () => {
      setIsPlayingAudio(false);
    };

    setAudioSpeechInstance(utterance);
    setIsPlayingAudio(true);
    window.speechSynthesis.speak(utterance);
  }, [activeStory, isPlayingAudio, stopAudio]);

  // Navigation handlers
  const handleNext = useCallback(() => {
    stopAudio();
    if (currentIndex < totalStories - 1) {
      setCurrentIndex((prev) => prev + 1);
    } else if (currentIndex === totalStories - 1) {
      // Step into the end/continuation gateway card
      setCurrentIndex(totalStories);
    } else {
      // Already on end card: auto-advance to next category or loop back
      if (onNextCategory) {
        onNextCategory();
      } else {
        setCurrentIndex(0);
      }
    }
  }, [currentIndex, totalStories, stopAudio, onNextCategory]);

  const handlePrev = useCallback(() => {
    stopAudio();
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  }, [currentIndex, stopAudio]);

  const handleRestart = useCallback(() => {
    stopAudio();
    setCurrentIndex(0);
  }, [stopAudio]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;

      if (e.key === 'ArrowDown' || e.key === 'j' || e.key === 'J') {
        e.preventDefault();
        handleNext();
      } else if (e.key === 'ArrowUp' || e.key === 'k' || e.key === 'K') {
        e.preventDefault();
        handlePrev();
      } else if (e.key === 'r' || e.key === 'R') {
        if (isEndOfPack) {
          e.preventDefault();
          handleRestart();
        }
      } else if (e.key === 's' || e.key === 'S') {
        e.preventDefault();
        if (activeStory && onToggleSave) {
          onToggleSave(activeStory);
        }
      } else if (e.key === ' ' || e.key === 'a' || e.key === 'A') {
        e.preventDefault();
        if (!isEndOfPack) {
          handleToggleAudio();
        }
      } else if (e.key === 'v' || e.key === 'V') {
        e.preventDefault();
        if (activeStory && !isEndOfPack) {
          setIsVideoModalOpen(true);
        }
      } else if (e.key === 'Enter') {
        if (isEndOfPack) {
          e.preventDefault();
          if (onNextCategory) {
            onNextCategory();
          } else {
            handleRestart();
          }
        } else if (activeStory) {
          navigate(`/story/${activeStory.id}`);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleNext, handlePrev, handleRestart, isEndOfPack, activeStory, onToggleSave, handleToggleAudio, onNextCategory, navigate]);

  // Wheel scroll snapping with debounce
  const wheelLockRef = useRef(false);
  const handleWheel = (e) => {
    if (wheelLockRef.current) return;
    if (Math.abs(e.deltaY) < 30) return;

    if (e.deltaY > 0) {
      wheelLockRef.current = true;
      handleNext();
      setTimeout(() => {
        wheelLockRef.current = false;
      }, 350);
    } else if (e.deltaY < 0 && currentIndex > 0) {
      wheelLockRef.current = true;
      handlePrev();
      setTimeout(() => {
        wheelLockRef.current = false;
      }, 350);
    }
  };

  // Touch swipe support for touchscreens & swipeable trackpads
  const touchStartY = useRef(0);
  const handleTouchStart = (e) => {
    if (e.touches && e.touches[0]) {
      touchStartY.current = e.touches[0].clientY;
    }
  };
  const handleTouchEnd = (e) => {
    if (e.changedTouches && e.changedTouches[0]) {
      const deltaY = touchStartY.current - e.changedTouches[0].clientY;
      if (deltaY > 40) {
        handleNext();
      } else if (deltaY < -40 && currentIndex > 0) {
        handlePrev();
      }
    }
  };

  // Like action with PostgreSQL persistence
  const handleLike = async (story) => {
    if (!story) return;
    const currentLiked = !!likedMap[story.id];
    const nextLiked = !currentLiked;

    const nextMap = { ...likedMap, [story.id]: nextLiked };
    setLikedMap(nextMap);
    try {
      localStorage.setItem('estd_liked_stories', JSON.stringify(nextMap));
      await toggleStoryLike(story.id);
    } catch (err) {
      console.warn('Could not persist like:', err);
    }
  };

  const handleShare = async (story) => {
    if (!story) return;
    const shareUrl = `${window.location.origin}/story/${story.id}`;
    if (navigator.share) {
      try {
        await navigator.share({
          title: story.headline,
          text: story.brief,
          url: shareUrl,
        });
      } catch {
        navigator.clipboard.writeText(shareUrl);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    } else {
      navigator.clipboard.writeText(shareUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Safe category meta & color
  const catMeta = activeStory ? (activeStory.categoryMeta || getCategoryMeta(activeStory.category)) : {};
  const accentColor = catMeta.color || '#00E5FF';
  const isSaved = activeStory ? savedStories.some((s) => String(s.id) === String(activeStory.id)) : false;
  const isLiked = activeStory ? !!likedMap[activeStory.id] : false;

  // 4 Beats extraction: Guaranteed 4 chronological milestones with titles and details
  const rawBeats = activeStory?.contextBeats || [];
  const defaultBeatFallbacks = [
    { title: 'Background Origin', detail: 'Prior structural backdrop and context established by verified reporting sources.' },
    { title: 'Trigger Catalyst', detail: 'Primary disclosure, key milestone, or event announced by key stakeholders.' },
    { title: 'Key Development', detail: 'Verified report and operational updates documented across field channels.' },
    { title: 'Forward Horizon', detail: 'Upcoming regulatory, market, or community milestones to monitor moving forward.' },
  ];

  const beats = useMemo(() => {
    return [0, 1, 2, 3].map((idx) => {
      const b = rawBeats[idx] || {};
      const fallback = defaultBeatFallbacks[idx];
      const title = b.title || b.label || b.heading || fallback.title;
      const detail = b.detail || b.text || b.summary || b.description || (typeof b === 'string' ? b : '') || fallback.detail;
      return {
        title,
        detail,
      };
    });
  }, [rawBeats]);

  // 5 Multi-angle video perspectives for complete interactive coverage
  const defaultPerspectives = [
    { role: 'Official', label: 'Official Wire', suffix: 'Press Briefing & Primary Statements', duration: '2:15', icon: ShieldCheck, color: '#00E5FF' },
    { role: 'Broadcast', label: 'Broadcast Desk', suffix: 'Prime Time News Desk Coverage', duration: '4:40', icon: Tv, color: '#38BDF8' },
    { role: 'Analysis', label: 'Analysis Desk', suffix: 'Strategic, Financial & Data Breakdown', duration: '5:18', icon: Sparkles, color: '#FBBF24' },
    { role: 'Creator', label: 'Creator Pulse', suffix: 'Independent Review & Key Nuances', duration: '6:02', icon: Radio, color: '#C084FC' },
    { role: 'Fan', label: 'Community Pulse', suffix: 'Audience Debates & Viral Sentiment', duration: '1:45', icon: Users, color: '#F472B6' },
  ];

  const perspectives = useMemo(() => {
    const rail = activeStory?.videoRail || [];
    return defaultPerspectives.map((def, idx) => {
      const r = rail[idx] || {};
      return {
        ...def,
        ...r,
        role: r.role || def.role,
        label: def.label,
        suffix: r.suffix || def.suffix,
        duration: r.duration || def.duration,
        color: def.color,
        icon: def.icon,
      };
    });
  }, [activeStory]);

  // Extract scope for single-instance metadata display (no duplicate block)
  const scopeValue = useMemo(() => {
    const chips = activeStory?.impactChips || [];
    const scopeChip = chips.find(
      (c) => c.type === 'scope' || (c.label || '').toLowerCase().includes('scope')
    );
    return scopeChip ? scopeChip.value : null;
  }, [activeStory]);

  // Next category color meta
  const nextCatMeta = nextCategory ? getCategoryMeta(nextCategory) : null;
  const nextAccent = nextCatMeta?.color || '#00E5FF';

  // Clean brief: strip redundant headline prefix if duplicated in raw text
  const cleanBrief = useMemo(() => {
    const raw = activeStory?.brief || activeStory?.contentSnippet || activeStory?.content || '';
    const headline = (activeStory?.headline || '').trim();
    if (!raw) return '';
    let text = raw.trim();
    if (headline && text.toLowerCase().startsWith(headline.toLowerCase())) {
      text = text.slice(headline.length).replace(/^[:.\s-]+/, '').trim();
    }
    return text || raw;
  }, [activeStory]);

  // 1. IF NO STORIES AT ALL
  if (totalStories === 0) {
    return (
      <div className="inshorts-desk-empty">
        <Sparkles size={36} color="#00E5FF" />
        <h3>Loading Verified Stories...</h3>
        <p>Curating real-time dispatches across Tech, Entertainment, Sports, and Developments.</p>
      </div>
    );
  }

  // 2. END OF PACK / NEXT CATEGORY TRANSITION GATEWAY (NO CRASH, NO BLANK SCREEN)
  if (isEndOfPack) {
    return (
      <div
        className="inshorts-desk-container inshorts-end-container"
        onWheel={handleWheel}
        onTouchStart={handleTouchStart}
        onTouchEnd={handleTouchEnd}
        tabIndex={0}
        aria-label="Daily Pack Complete"
      >
        {/* Top Tracker: Kept visible for flawless alignment */}
        <div className="inshorts-desk-tracker" style={{ width: '100%' }}>
          <div className="inshorts-tracker-left">
            <span className="inshorts-tracker-pill" style={{ borderColor: '#10B981', color: '#10B981' }}>
              PACK COMPLETE
            </span>
            <span className="inshorts-tracker-count">
              All <strong>{totalStories}</strong> of <strong>{totalStories}</strong> Dispatches Read
            </span>
          </div>

          <div className="inshorts-progress-bar-wrap continuous">
            <div className="inshorts-progress-fill" style={{ width: '100%', backgroundColor: '#10B981' }} />
          </div>

          <div className="inshorts-tracker-right">
            <button
              type="button"
              className="inshorts-nav-arrow-btn"
              onClick={handlePrev}
              title="Previous Story (↑ or K)"
            >
              <ChevronUp size={16} />
            </button>
            <button
              type="button"
              className="inshorts-nav-arrow-btn"
              disabled
              title="End of Pack"
            >
              <ChevronDown size={16} />
            </button>
          </div>
        </div>

        {/* Cinematic Achievement & Continuation Card */}
        <div className="inshorts-end-card">
          <div className="inshorts-end-badge">
            <Check size={32} />
          </div>

          <span className="inshorts-end-subtitle">
            {currentCategory === 'All' ? 'ALL VERTICALS COMPLETE' : `${currentCategory.toUpperCase()} VERTICAL COMPLETE`}
          </span>

          <h2 className="inshorts-end-title">You're All Caught Up!</h2>

          <p className="inshorts-end-description">
            You've completed all {totalStories} verified dispatches in{' '}
            <strong>{currentCategory === 'All' ? 'the Daily Wire' : currentCategory}</strong>. Ready to continue into the next vertical?
          </p>

          {/* Forward Category Portal */}
          {nextCategory && onNextCategory && (
            <div className="inshorts-next-cat-preview">
              <span className="inshorts-next-cat-label">NEXT STREAM IN QUEUE:</span>
              <button
                type="button"
                className="inshorts-next-cat-btn"
                onClick={onNextCategory}
                style={{
                  '--next-accent': nextAccent,
                }}
              >
                <Sparkles size={16} color={nextAccent} />
                <span>Continue to {nextCategory}</span>
                <ArrowRight size={16} />
              </button>
            </div>
          )}

          {/* Action Buttons */}
          <div className="inshorts-end-actions">
            {nextCategory && onNextCategory ? (
              <button
                type="button"
                className="inshorts-btn inshorts-btn-primary"
                onClick={onNextCategory}
                style={{
                  background: `linear-gradient(135deg, ${nextAccent} 0%, #0070F3 100%)`,
                }}
              >
                <span>Read {nextCategory}</span>
                <ArrowRight size={15} />
              </button>
            ) : null}

            <button
              type="button"
              className="inshorts-btn inshorts-btn-secondary"
              onClick={handleRestart}
            >
              <RotateCcw size={15} />
              <span>Read Again (Story 1)</span>
            </button>

            {onExitToBento && (
              <button
                type="button"
                className="inshorts-btn inshorts-btn-secondary"
                onClick={onExitToBento}
              >
                <LayoutGrid size={15} />
                <span>Switch to Bento Magazine</span>
              </button>
            )}
          </div>

          {/* Key shortcut footer hint */}
          <div className="inshorts-end-shortcut-hint">
            <span>Press <kbd>↓</kbd> or <kbd>Enter</kbd> to start next vertical • <kbd>↑</kbd> to review last story</span>
          </div>
        </div>
      </div>
    );
  }

  // 3. ACTIVE STORY RENDER
  return (
    <div
      className="inshorts-desk-container"
      onWheel={handleWheel}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      tabIndex={0}
      aria-label="Inshorts Desktop Reader"
    >
      {/* 1. TOP PROGRESS TRACKER ROW */}
      <div className="inshorts-desk-tracker">
        <div className="inshorts-tracker-left">
          <span className="inshorts-tracker-pill" style={{ borderColor: `${accentColor}44`, color: accentColor }}>
            {currentCategory === 'All' ? 'DAILY PACK' : currentCategory.toUpperCase()}
          </span>
          <span className="inshorts-tracker-count">
            Story <strong>{currentIndex + 1}</strong> of <strong>{totalStories}</strong>
          </span>
        </div>

        {/* Progress Bar: segments if <= 15, smooth continuous bar if > 15 */}
        {totalStories <= 15 ? (
          <div className="inshorts-progress-bar-wrap">
            {dailyPack.map((_, i) => (
              <div
                key={i}
                className={`inshorts-progress-segment ${i <= currentIndex ? 'filled' : ''}`}
                style={{
                  backgroundColor: i <= currentIndex ? accentColor : 'rgba(255, 255, 255, 0.12)',
                }}
                onClick={() => {
                  stopAudio();
                  setCurrentIndex(i);
                }}
                title={`Jump to Story ${i + 1}`}
              />
            ))}
          </div>
        ) : (
          <div className="inshorts-progress-bar-wrap continuous" title={`Story ${currentIndex + 1} of ${totalStories}`}>
            <div
              className="inshorts-progress-fill"
              style={{
                width: `${Math.min(100, ((currentIndex + 1) / totalStories) * 100)}%`,
                backgroundColor: accentColor,
              }}
            />
          </div>
        )}

        {/* Audio Brief & Navigation Chevrons */}
        <div className="inshorts-tracker-right">
          <button
            type="button"
            className={`inshorts-audio-btn ${isPlayingAudio ? 'playing' : ''}`}
            onClick={handleToggleAudio}
            style={{
              borderColor: isPlayingAudio ? accentColor : 'rgba(255, 255, 255, 0.14)',
              color: isPlayingAudio ? accentColor : '#F5F5F5',
            }}
            title={isPlayingAudio ? 'Stop voiceover' : 'Listen to 60-second AI Voiceover'}
          >
            {isPlayingAudio ? <VolumeX size={15} /> : <Volume2 size={15} />}
            <span>{isPlayingAudio ? 'Stop Audio' : 'Listen Brief (60s)'}</span>
            {isPlayingAudio && <span className="audio-wave-pulse" style={{ backgroundColor: accentColor }} />}
          </button>

          <div className="inshorts-nav-arrows">
            <button
              type="button"
              className="inshorts-nav-arrow-btn"
              onClick={handlePrev}
              disabled={currentIndex === 0}
              title="Previous Story (↑ or K)"
            >
              <ChevronUp size={16} />
            </button>
            <button
              type="button"
              className="inshorts-nav-arrow-btn"
              onClick={handleNext}
              title="Next Story (↓ or J)"
            >
              <ChevronDown size={16} />
            </button>
          </div>
        </div>
      </div>

      {/* 2. THE MAIN INSHORTS DESKTOP CARD (Split Media + Editorial Contract) */}
      <article
        className="inshorts-desk-card"
        style={{
          '--card-accent': accentColor,
        }}
      >
        {/* LEFT COLUMN: Cinematic Hero Media with Floating Multi-Angle Quick-Dock */}
        <div className="inshorts-desk-media-col">
          <div
            className="inshorts-media-frame"
            onClick={() => {
              setModalVideoIndex(0);
              setIsVideoModalOpen(true);
            }}
            title="Click to watch 5-angle video perspectives"
          >
            <ImageWithFallback
              src={activeStory.imageUrl}
              alt={activeStory.headline}
              category={activeStory.category}
              subcategory={activeStory.subcategory}
              className="inshorts-media-img"
              size="hero"
            />

            {/* Ambient Edge Glow */}
            <div className="inshorts-media-glow" style={{ '--glow-color': accentColor }} />

            {/* Top-Left Perspective Beacon */}
            <div className="inshorts-media-top-badge">
              <div
                className="inshorts-video-pill"
                style={{
                  backgroundColor: 'rgba(7, 8, 12, 0.82)',
                  borderColor: `${accentColor}88`,
                }}
              >
                <span className="inshorts-pulse-dot" style={{ backgroundColor: accentColor }} />
                <Video size={13} color={accentColor} />
                <span style={{ color: '#FFFFFF', fontWeight: 700 }}>5 Multi-Angle Perspectives</span>
              </div>
            </div>

            {/* Center Play Button Overlay */}
            <div className="inshorts-media-center-action">
              <div className="inshorts-play-btn" style={{ borderColor: accentColor }}>
                <div className="inshorts-play-triangle" />
              </div>
              <span className="inshorts-play-hint">Watch Multi-Source Footage</span>
            </div>

            {/* Floating Glassmorphism Perspective Chips (Bottom of Media Frame) */}
            <div
              className="inshorts-media-perspectives-dock"
              onClick={(e) => e.stopPropagation()}
            >
              {perspectives.map((p, pIdx) => {
                const IconComponent = p.icon;
                return (
                  <button
                    key={pIdx}
                    type="button"
                    className="inshorts-media-persp-chip"
                    onClick={() => {
                      setModalVideoIndex(pIdx);
                      setIsVideoModalOpen(true);
                    }}
                    style={{
                      '--chip-accent': p.color,
                    }}
                    title={`Watch ${p.label}: ${p.suffix}`}
                  >
                    <IconComponent size={12} color={p.color} style={{ flexShrink: 0 }} />
                    <span className="inshorts-persp-chip-label">{p.role}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: The Sacred Story Contract (Zero Duplicated Metadata) */}
        <div className="inshorts-desk-content-col">
          {/* Unified Single-Source Intelligence Meta Row */}
          <div className="inshorts-meta-row">
            <span
              className="inshorts-cat-pill"
              style={{
                borderColor: `${accentColor}66`,
                color: accentColor,
                backgroundColor: `${accentColor}18`,
              }}
              onClick={() => navigate(`/category/${catMeta.slug || slugify(activeStory.category)}`)}
            >
              {activeStory.category}
            </span>

            {activeStory.subcategory && (
              <span className="inshorts-meta-chip inshorts-subcat-chip">
                <Layers size={11} color={accentColor} />
                <span>{activeStory.subcategory}</span>
              </span>
            )}

            <span className="inshorts-meta-chip inshorts-source-chip">
              <ShieldCheck size={11} color="#00E5FF" />
              <span>{activeStory.sourceName || 'Verified Wire'}</span>
            </span>

            {scopeValue && (
              <span className="inshorts-meta-chip inshorts-scope-chip">
                <Globe size={11} color="#94A3B8" />
                <span>{scopeValue}</span>
              </span>
            )}

            <span className="inshorts-meta-chip inshorts-time-chip">
              <Clock size={11} />
              <span>
                {activeStory.publishedAt
                  ? new Date(activeStory.publishedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                  : 'Just Now'}
              </span>
            </span>
          </div>

          {/* Spoken Headline (<= 12 words) */}
          <h2
            className="inshorts-headline"
            onClick={() => navigate(`/story/${activeStory.id}`)}
            title="Read complete story deep dive"
          >
            {activeStory.headline}
          </h2>

          {/* The One-Paragraph Summary (50-70 words) */}
          <div className="inshorts-summary-box">
            <p className="inshorts-summary-text" title={cleanBrief}>
              {cleanBrief}
            </p>
          </div>

          {/* Context in 4 Beats (Chronological Timeline Arc) */}
          <div className="inshorts-beats-preview">
            <div className="inshorts-beats-header">
              <span className="inshorts-beats-title">CONTEXT IN 4 BEATS</span>
            </div>
            <div className="inshorts-beats-grid">
              {beats.map((beat, bIdx) => (
                <div key={bIdx} className="inshorts-beat-item">
                  <span className="inshorts-beat-num" style={{ color: accentColor }}>
                    0{bIdx + 1}
                  </span>
                  <div className="inshorts-beat-content">
                    <strong className="inshorts-beat-label">{beat.title}:</strong>
                    <span className="inshorts-beat-text">{beat.detail}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* FOOTER ACTIONS & KEYBOARD SHORTCUTS */}
          <div className="inshorts-footer-dock">
            <div className="inshorts-primary-actions">
              <button
                type="button"
                className="inshorts-read-full-btn"
                onClick={() => navigate(`/story/${activeStory.id}`)}
                style={{
                  background: `linear-gradient(135deg, ${accentColor} 0%, #0070F3 100%)`,
                }}
              >
                <span>Read Full Story</span>
                <ArrowRight size={14} />
              </button>

              <button
                type="button"
                className={`inshorts-icon-btn ${isSaved ? 'active' : ''}`}
                onClick={() => onToggleSave && onToggleSave(activeStory)}
                title={isSaved ? 'Remove from Saved' : 'Save Story (S)'}
              >
                <Bookmark size={15} fill={isSaved ? accentColor : 'none'} color={isSaved ? accentColor : 'currentColor'} />
                <span>{isSaved ? 'Saved' : 'Save'}</span>
              </button>

              <button
                type="button"
                className={`inshorts-icon-btn ${isLiked ? 'active' : ''}`}
                onClick={() => handleLike(activeStory)}
                title={isLiked ? 'Liked' : 'Like Story'}
              >
                <Heart size={15} fill={isLiked ? '#FF4757' : 'none'} color={isLiked ? '#FF4757' : 'currentColor'} />
                <span>Like</span>
              </button>

              <button
                type="button"
                className="inshorts-icon-btn"
                onClick={() => handleShare(activeStory)}
                title="Share Story"
              >
                {copied ? <Check size={15} color="#10B981" /> : <Share2 size={15} />}
                <span>{copied ? 'Copied' : 'Share'}</span>
              </button>

              <button
                type="button"
                className="inshorts-icon-btn inshorts-watch-btn"
                onClick={() => setIsVideoModalOpen(true)}
                title="Watch Video Rail (V)"
              >
                <Video size={15} color={accentColor} />
                <span>Watch</span>
              </button>
            </div>

            {/* Dedicated Keyboard Shortcuts Status Bar */}
            <div className="inshorts-shortcuts-hint" aria-label="Keyboard Navigation Shortcuts">
              <span className="inshorts-shortcuts-label">Keys:</span>
              <span className="inshorts-shortcut-item">
                <kbd>↓</kbd> / <kbd>J</kbd> Next
              </span>
              <span className="inshorts-shortcut-item">
                <kbd>↑</kbd> / <kbd>K</kbd> Prev
              </span>
              <span className="inshorts-shortcut-item">
                <kbd>S</kbd> Save
              </span>
              <span className="inshorts-shortcut-item">
                <kbd>Space</kbd> Audio
              </span>
              <span className="inshorts-shortcut-item">
                <kbd>Enter</kbd> Full Story
              </span>
            </div>
          </div>
        </div>
      </article>

      {/* VIDEO MODAL FOR 5-ANGLE PERSPECTIVES */}
      {isVideoModalOpen && (
        <VideoModalPlayer
          isOpen={isVideoModalOpen}
          onClose={() => setIsVideoModalOpen(false)}
          story={activeStory}
          initialVideoIndex={modalVideoIndex}
          accentColor={accentColor}
          isSaved={isSaved}
          onToggleSave={onToggleSave}
        />
      )}
    </div>
  );
}
