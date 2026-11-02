import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Bookmark,
  Share2,
  FileText,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  Check,
  Video,
  Clock,
  Volume2,
  VolumeX,
  Database,
  Sparkles,
  Layers,
  Globe,
  Flame,
  Zap,
  CheckCircle2,
  Quote,
  TrendingUp,
  Radio,
  Type,
  ArrowUp,
  Hash,
} from 'lucide-react';
import ImageWithFallback from '../common/ImageWithFallback';
import ImpactChips from './ImpactChips';
import VideoRail from './VideoRail';
import VideoModalPlayer from './VideoModalPlayer';
import ListenPlayer from './ListenPlayer';
import ErrorState from '../common/ErrorState';
import FlashBiteModal from './FlashBiteModal';
import { formatCleanHeadline, formatCleanTopicName } from '../../utils/flashBitesUtils';
import {
  fetchStoryById,
  fetchStories,
  toggleStoryLike,
  fetchStoryLikes,
  parseStructuredArticleContent,
} from '../../api/estdApi';
import { getCategoryMeta, slugify } from '../../constants/taxonomy';
import { trackArticleRead } from '../../utils/readingHistory';

/**
 * StoryObject: The Ultimate Gen-Z News Reading Experience
 *
 * Implements a world-class, engaging, and unique editorial layout:
 * 1. Top Navigation Bar with Back-to-feed & Prev/Next Story Switcher
 * 2. High-Impact Category & Byline Header with Live Reading Time & Verification Pill
 * 3. 16:9 Cinematic Hero Media Frame with Ambient Glow & Floating Video Perspectives Pill
 * 4. "⚡ THE QUICK DROP" (Gen Z TL;DR Executive Brief with Integrated Impact Chips)
 * 5. Multi-Source Video Perspectives Rail (5 Perspectives: Official, Broadcast, Analysis, Creator, Fan)
 * 6. Story Arc: "Context in 4 Beats" (Clean Chronological Milestones)
 * 7. "The Deep Dive" (Structured Journalistic Intelligence Report):
 *    - 4-Card Key Fact Indicators Grid (Domain, Reporter, Pipeline Status, Scope)
 *    - Editorial Drop-cap Lead Paragraph
 *    - Neon Gen-Z Pull Quote Card
 *    - Crisp, Formatted Article Paragraphs (Zero ASCII garbage, zero raw URLs)
 *    - "The Bottom Line" Skimmable Key Takeaways Checklist
 * 8. Cultural Pulse & Community Reaction Card
 * 9. Interactive Live Reaction / Like Dock
 * 10. Sticky Sidebar with Story Actions, Subcategory Discovery & Provenance
 */
export default function StoryObject({
  savedStories = [],
  onToggleSave,
  watchLaterStories = [],
  onToggleWatchLater,
}) {
  const { storyId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();

  const [story, setStory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);
  const [quoteCopied, setQuoteCopied] = useState(false);
  const [allStories, setAllStories] = useState([]);

  // Video Modal State
  const [modalVideoIndex, setModalVideoIndex] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // 60-Second Flash Bite Modal State
  const [isFlashModalOpen, setIsFlashModalOpen] = useState(false);

  // Audio speech player active state
  const shouldListen = new URLSearchParams(location.search).get('listen') === 'true';
  const [showAudioPlayer, setShowAudioPlayer] = useState(shouldListen);

  // Interactive Likes State
  const [likesCount, setLikesCount] = useState(0);
  const [hasLiked, setHasLiked] = useState(false);
  const [isLiking, setIsLiking] = useState(false);

  // Reader Customization & Audio Briefing State
  const [fontSize, setFontSize] = useState('md'); // 'sm' | 'md' | 'lg'
  const [isSpeaking, setIsSpeaking] = useState(false);

  useEffect(() => {
    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, [storyId]);

  useEffect(() => {
    let isMounted = true;
    async function loadStory() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchStoryById(storyId);
        if (isMounted) {
          setStory(data);
trackArticleRead(data);
          setLikesCount(data.likesCount || 0);
        }

        // Fetch feed stories for adjacent, related, and subcategory navigation
        const list = await fetchStories({ limit: 60 });
        if (isMounted) setAllStories(list);

        // Fetch live likes status from PostgreSQL
        try {
          const likesRes = await fetchStoryLikes(storyId);
          if (isMounted && likesRes) {
            setLikesCount(likesRes.likes_count || data.likesCount || 0);
            setHasLiked(Boolean(likesRes.has_liked));
          }
        } catch {
          // Non-critical if like check fails
        }
      } catch (err) {
        if (isMounted) setError(err.message || 'Story could not be loaded.');
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    if (storyId) {
      loadStory();
    }

    window.scrollTo({ top: 0, behavior: 'smooth' });

    return () => {
      isMounted = false;
    };
  }, [storyId]);

  const handleToggleLike = async () => {
    if (isLiking || !story) return;
    setIsLiking(true);
    try {
      const res = await toggleStoryLike(story.id);
      if (res) {
        setLikesCount(res.likes_count ?? (hasLiked ? likesCount - 1 : likesCount + 1));
        setHasLiked(res.liked);
      }
    } catch {
      // Optimistic fallback
      setHasLiked(!hasLiked);
      setLikesCount(hasLiked ? Math.max(0, likesCount - 1) : likesCount + 1);
    } finally {
      setIsLiking(false);
    }
  };

  const handleShare = () => {
    const url = window.location.href;
    if (navigator.share) {
      navigator.share({ title: story.headline, text: story.brief, url }).catch(() => copyToClipboard(url));
    } else {
      copyToClipboard(url);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopyQuote = (quoteText, author) => {
    navigator.clipboard.writeText(`"${quoteText}" — ${author}`);
    setQuoteCopied(true);
    setTimeout(() => setQuoteCopied(false), 2000);
  };

  if (loading) {
    return (
      <div className="story-object-view story-loading-skeleton" style={{ maxWidth: 1360, margin: '0 auto', paddingTop: 24 }}>
        <div className="skeleton-bar" style={{ height: 28, width: 220, marginBottom: 20 }} />
        <div className="skeleton-bar" style={{ height: 56, width: '85%', marginBottom: 16 }} />
        <div className="skeleton-bar" style={{ height: 24, width: '45%', marginBottom: 28 }} />
        <div className="skeleton-media-box" style={{ height: 420, width: '100%', borderRadius: 20, marginBottom: 32 }} />
      </div>
    );
  }

  if (error || !story) {
    return (
      <div className="story-object-view" style={{ maxWidth: 1360, margin: '0 auto', paddingTop: 30 }}>
        <button className="story-back-nav" onClick={() => navigate(-1)}>
          <ArrowLeft size={16} />
          <span>Go Back</span>
        </button>
        <ErrorState
          title="Story Not Found in Knowledge Base"
          error={error || `Story #${storyId} does not exist in the PostgreSQL knowledge base.`}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  const catMeta = story.categoryMeta || getCategoryMeta(story.category);
  const accentColor = catMeta.color || '#00E5FF';
  const isSaved = savedStories.some((s) => s.id === story.id);
  const isWatchLater = watchLaterStories.some((s) => String(s.id) === String(story.id));
  const editorialType = story.editorialType || 'REPORT';

  // Parse high-engagement structured journalism for this story
  const structured = parseStructuredArticleContent(
    story.content,
    story.headline,
    story.category,
    story.subcategory,
    story.publishedAt,
    story.sourceName,
    story.videoRail
  );

  const toggleSpeech = () => {
    if (!('speechSynthesis' in window)) {
      alert('Text-to-speech audio briefing is not supported in this browser.');
      return;
    }
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }
    const textToRead = [
      story?.headline,
      structured?.leadParagraph,
      structured?.tldr?.map((t) => `${t.title}: ${t.text}`).join('. '),
    ].filter(Boolean).join('. ');

    const utterance = new SpeechSynthesisUtterance(textToRead);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    window.speechSynthesis.speak(utterance);
    setIsSpeaking(true);
  };

  // Adjacent story navigation
  const currentIndex = allStories.findIndex((s) => s.id === Number(storyId));
  const prevStory = currentIndex > 0 ? allStories[currentIndex - 1] : null;
  const nextStory =
    currentIndex >= 0 && currentIndex < allStories.length - 1
      ? allStories[currentIndex + 1]
      : null;

  // Subcategory and Related Stories for Right Sidebar
  const subcategoryStories = allStories
    .filter((s) => s.id !== story.id && s.subcategory === story.subcategory)
    .slice(0, 3);

  const relatedCategoryStories = allStories
    .filter((s) => s.id !== story.id && s.category === story.category && s.subcategory !== story.subcategory)
    .slice(0, 3);

  const hasSidebar = subcategoryStories.length > 0 || relatedCategoryStories.length > 0;

  const originalPubDate = story.publishedAt
    ? new Date(story.publishedAt).toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : 'Recent';

  const ingestionDate = story.ingestedAt
    ? new Date(story.ingestedAt).toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : null;

  // Key fact indicators for the 4-card grid
  const keyIndicators = structured.keyIndicators && structured.keyIndicators.length > 0
    ? structured.keyIndicators
    : [
        { label: 'Domain', value: story.subcategory || story.category },
        { label: 'Primary Reporter', value: story.sourceName },
        { label: 'Verification Status', value: 'ESTD Authenticated' },
        { label: 'Distribution Scope', value: 'Global Intelligence' },
      ];

  const reportParagraphs = structured.paragraphs && structured.paragraphs.length > 0
    ? structured.paragraphs
    : [story.brief];

  const leadParagraph = reportParagraphs[0];
  const remainingParagraphs = reportParagraphs.slice(1);

  return (
    <div className="story-object-view" style={{ maxWidth: 1380, margin: '0 auto', paddingBottom: 100 }}>
      {/* 1. TOP HERO SECTION: TWO EQUAL-LENGTH COLUMNS (Image on left, Actions & Provenance on right) */}
      <div className="story-hero-two-column">
        {/* LEFT COLUMN: Breadcrumb, Headline, Byline, Hero Image */}
        <div className="story-hero-left-column">
          {/* Breadcrumb Tags & Verification Strip */}
          <div className="story-breadcrumb-strip">
            <span
              className="category-badge"
              style={{
                borderColor: `${accentColor}55`,
                background: `${accentColor}18`,
                color: accentColor,
              }}
              onClick={() => navigate(`/category/${catMeta.slug || slugify(story.category)}`)}
            >
              <span className="category-badge-dot" style={{ background: accentColor }} />
              {story.category}
            </span>

            {story.subcategory && (
              <span
                className="story-subcategory-label"
                onClick={() =>
                  navigate(
                    `/category/${catMeta.slug || slugify(story.category)}/${slugify(story.subcategory)}`
                  )
                }
              >
                {story.subcategory}
              </span>
            )}

            <span className="editorial-kicker" style={{ borderColor: 'rgba(255,255,255,0.12)' }}>
              ESTD {editorialType}
            </span>

            <span
              className="story-videos-badge"
              style={{
                borderColor: `${accentColor}55`,
                color: accentColor,
                background: `${accentColor}14`,
              }}
              onClick={() => {
                setModalVideoIndex(0);
                setIsModalOpen(true);
              }}
            >
              <Video size={13} />
              <span>{story.videoRail?.length || 5} Perspectives</span>
            </span>

            {/* Reading Time Pill and Adjacent Prev/Next Controls */}
            <div className="story-nav-right-cluster" style={{ marginLeft: 'auto' }}>
              <button
                type="button"
                className="reading-time-pill flash-breadcrumb-pill"
                onClick={() => setIsFlashModalOpen(true)}
                style={{
                  cursor: 'pointer',
                  borderColor: `${accentColor}55`,
                  background: `${accentColor}16`,
                  color: accentColor,
                  border: '1px solid',
                }}
                title="Tap for 60-second Smart Brevity Flash Bite"
              >
                <Zap size={13} style={{ color: accentColor }} />
                <span>⚡ 60s Flash Bite</span>
              </button>

              <div className="reading-time-pill">
                <Clock size={13} style={{ color: accentColor }} />
                <span>{structured.readTime || '⚡ 2 min read'}</span>
              </div>

              {(prevStory || nextStory) && (
                <div className="story-adjacent-nav">
                  {prevStory && (
                    <button
                      className="action-icon-btn adjacent-btn"
                      onClick={() => navigate(`/story/${prevStory.id}`)}
                      title={`Previous: ${prevStory.headline}`}
                    >
                      <ChevronLeft size={14} />
                      <span className="adjacent-label">Prev</span>
                    </button>
                  )}
                  {nextStory && (
                    <button
                      className="action-icon-btn adjacent-btn"
                      onClick={() => navigate(`/story/${nextStory.id}`)}
                      title={`Next: ${nextStory.headline}`}
                    >
                      <span className="adjacent-label">Next</span>
                      <ChevronRight size={14} />
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* COMPLETE SPOKEN-STYLE HEADLINE (No truncation) */}
          <h1 className="story-object-headline">
            {story.originalTitle || story.headline}
          </h1>

          {/* 16:9 CINEMATIC HERO MEDIA FRAME (Length perfectly fills column to match right cards) */}
          <div className="story-hero-media-wrapper">
            <div
              className="story-hero-ambient-glow"
              style={{ background: `radial-gradient(circle at center, ${accentColor}25 0%, transparent 70%)` }}
            />
            <div className="story-object-media-frame">
              <ImageWithFallback
                src={story.imageUrl}
                alt={story.headline}
                category={story.category}
                subcategory={story.subcategory}
                aspectRatio="16/9"
              />

              {/* Floating Round 60-Second Flash Bite Launcher (Top-Left) */}
              <div
                className="floating-flash-bite-launcher"
                onClick={() => setIsFlashModalOpen(true)}
                role="button"
                tabIndex={0}
                style={{ '--ring-accent': accentColor }}
                title="Tap for 60-second Smart Brevity Flash Bite"
              >
                <div className="flash-ring-wrapper">
                  <div className="flash-ring-glow" />
                  <div className="flash-ring-inner">
                    <ImageWithFallback
                      src={story.imageUrl}
                      alt={story.headline}
                      category={story.category}
                      subcategory={story.subcategory}
                      className="flash-ring-avatar"
                      size="thumb"
                    />
                  </div>
                  <span className="flash-ring-pulse-badge">
                    <Zap size={10} />
                  </span>
                </div>
                <div className="flash-launcher-text">
                  <div className="flash-launcher-header-row">
                    <span className="flash-launcher-badge" style={{ color: accentColor }}>
                      60s FLASH BITE
                    </span>
                  </div>
                  <span className="flash-launcher-title">
                    3-Bullet Smart Brevity
                  </span>
                </div>
              </div>

              {/* Floating Perspective Rail Video Launcher Badge */}
              <div
                className="floating-video-launcher-badge"
                style={{
                  background: 'rgba(10, 12, 18, 0.88)',
                  borderColor: `${accentColor}77`,
                  boxShadow: `0 8px 24px rgba(0,0,0,0.6), 0 0 16px ${accentColor}33`,
                }}
                onClick={() => {
                  setModalVideoIndex(0);
                  setIsModalOpen(true);
                }}
              >
                <div className="launcher-play-pulse" style={{ background: accentColor }}>
                  <Video size={14} color="#000000" />
                </div>
                <div className="launcher-text-block">
                  <span className="launcher-title" style={{ color: '#ffffff' }}>
                    Watch 5 Perspectives
                  </span>
                  <span className="launcher-subtitle" style={{ color: accentColor }}>
                    Official • Broadcast • Fan
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Story Actions & Source Provenance & Legal */}
        <aside className="story-hero-right-column">
          {/* Round 60-Second Flash Bite Pod Card */}
          <div
            className="sidebar-section-card flash-bite-sidebar-card"
            onClick={() => setIsFlashModalOpen(true)}
            role="button"
            tabIndex={0}
            style={{ '--ring-accent': accentColor }}
            title="Tap for 60-second Smart Brevity brief"
          >
            <div className="flash-sidebar-card-content">
              <div className="flash-ring-wrapper">
                <div className="flash-ring-glow" />
                <div className="flash-ring-inner">
                  <ImageWithFallback
                    src={story.imageUrl}
                    alt={story.headline}
                    category={story.category}
                    subcategory={story.subcategory}
                    className="flash-ring-avatar"
                    size="thumb"
                  />
                </div>
                <span className="flash-ring-pulse-badge">
                  <Zap size={10} />
                </span>
              </div>

              <div className="flash-sidebar-card-text">
                <div className="flash-sidebar-badge-row">
                  <span
                    className="flash-sidebar-pill"
                    style={{
                      color: accentColor,
                      borderColor: `${accentColor}55`,
                      background: `${accentColor}18`,
                    }}
                  >
                    ⚡ 60s FLASH BITE
                  </span>
                  <span className="flash-sidebar-count">Smart Brevity</span>
                </div>
                <h4 className="flash-sidebar-headline">
                  {formatCleanHeadline(story)}
                </h4>
                <span className="flash-sidebar-cta" style={{ color: accentColor }}>
                  Tap to read 3-bullet summary →
                </span>
              </div>
            </div>
          </div>

          {/* Story Actions Card (Compact Vertical List) */}
          <div className="sidebar-section-card sidebar-actions-card">
            <h4 className="sidebar-section-title">
              <Sparkles size={13} style={{ color: accentColor }} />
              <span>Story Actions</span>
            </h4>

            <div className="story-actions-vertical-list">
              {/* 1. Save Story */}
              <button
                className="compact-action-btn vertical-action-btn"
                style={{
                  background: isSaved ? 'rgba(255, 176, 32, 0.15)' : 'rgba(255,255,255,0.04)',
                  borderColor: isSaved ? '#FFB020' : 'rgba(255,255,255,0.08)',
                  color: isSaved ? '#FFB020' : '#ffffff',
                }}
                onClick={() => onToggleSave && onToggleSave(story)}
                title={isSaved ? 'Story is saved' : 'Save Story'}
              >
                <Bookmark size={13} fill={isSaved ? '#FFB020' : 'none'} />
                <span>{isSaved ? 'Saved Story ✓' : 'Save Story'}</span>
              </button>

              {/* 2. Watch Later */}
              <button
                className="compact-action-btn vertical-action-btn"
                style={{
                  background: isWatchLater ? 'rgba(255, 176, 32, 0.15)' : 'rgba(255,255,255,0.04)',
                  borderColor: isWatchLater ? '#FFB020' : 'rgba(255,255,255,0.08)',
                  color: isWatchLater ? '#FFB020' : '#ffffff',
                }}
                onClick={() => onToggleWatchLater && onToggleWatchLater(story)}
                title={isWatchLater ? 'In Watch Later' : 'Watch Later'}
              >
                <Clock
                  size={13}
                  className="watch-later-clock"
                  fill="none"
                  color={isWatchLater ? '#FFB020' : 'currentColor'}
                  strokeWidth={isWatchLater ? 2.3 : 2}
                />
                <span>{isWatchLater ? 'In Watch Later ✓' : 'Watch Later'}</span>
              </button>

              {/* 3. Share Story */}
              <button
                className="compact-action-btn vertical-action-btn"
                onClick={handleShare}
                title="Share Story"
              >
                {copied ? <Check size={13} style={{ color: '#10b981' }} /> : <Share2 size={13} />}
                <span>{copied ? 'Copied Link!' : 'Share Story'}</span>
              </button>

              {/* 3. 5 Perspectives */}
              <button
                className="compact-action-btn vertical-action-btn"
                style={{
                  background: `${accentColor}14`,
                  borderColor: `${accentColor}44`,
                  color: accentColor,
                }}
                onClick={() => {
                  setModalVideoIndex(0);
                  setIsModalOpen(true);
                }}
                title="Watch 5 Video Perspectives"
              >
                <Video size={13} />
                <span>5 Perspectives</span>
              </button>

              {/* 4. Google Doc in Drive (if present) */}
              {story.googleDoc?.document_url && (
                <a
                  href={story.googleDoc.document_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="compact-action-btn vertical-action-btn compact-doc-btn"
                  title="Open Google Doc in Google Drive"
                >
                  <FileText size={13} />
                  <span>Open Google Doc</span>
                  <ExternalLink size={10.5} />
                </a>
              )}
            </div>
          </div>

          {/* Verified Publisher & Legal Source List */}
          <div className="sidebar-section-card provenance-card">
            <h4 className="sidebar-section-title">
              <ShieldCheck size={13.5} style={{ color: '#10b981' }} />
              <span>Source Provenance & Legal</span>
            </h4>

            <div className="sources-list-grid">
              <div className="source-item-row">
                <span>Primary Publisher:</span>
                <strong style={{ color: '#ffffff' }}>{story.sourceName}</strong>
              </div>

              <div className="source-item-row">
                <span>Published On:</span>
                <strong style={{ color: '#ffffff' }}>{originalPubDate}</strong>
              </div>

              <div className="source-item-row">
                <span>ESTD Intelligence:</span>
                <span style={{ color: '#10b981', fontWeight: 600 }}>ESTD Verified Synthesis Engine</span>
              </div>

              <div className="source-item-row">
                <span>Ingested On:</span>
                <strong style={{ color: '#ffffff' }}>{ingestionDate || 'Real-Time Ingestion'}</strong>
              </div>

              {story.sourceUrl && (
                <div className="source-item-row">
                  <span>Original Source:</span>
                  <a
                    href={story.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    title="Read original source"
                  >
                    <span>Read Article</span>
                    <ExternalLink size={11} />
                  </a>
                </div>
              )}
            </div>

            <p className="provenance-disclaimer">
              Synthesized by ESTD under news intelligence principles. Original reporting remains copyright of {story.sourceName}.
            </p>
          </div>
        </aside>
      </div>

      {/* 2. FULL-WIDTH MULTI-SOURCE VIDEO PERSPECTIVES RAIL (All 5 videos clearly visible side-by-side as a rail without scrolling!) */}
      <section className="story-full-video-rail-section">
        <VideoRail
          videos={story.videoRail}
          storyId={story.id}
          accentColor={accentColor}
          title="Multi-Source Video Perspectives"
          subtitle="Explore authentic perspectives: Official Briefing, News Broadcast, Strategic Analysis, Creator Review, and Fan Pulse"
          onSelectVideo={(vid, idx) => {
            setModalVideoIndex(idx);
            setIsModalOpen(true);
          }}
        />
      </section>

      {/* 3. FULL-WIDTH GEN-Z EXECUTIVE INTELLIGENCE BENTO DECK (Key Quote on left + 30-Second Briefing on right) */}
      {(structured.pullQuote?.quote || (structured.tldr && structured.tldr.length > 0)) && (
        <section className="story-executive-bento-deck">
          <div
            className="bento-deck-ambient-glow"
            style={{ background: `radial-gradient(circle at 25% 40%, ${accentColor}18 0%, transparent 70%)` }}
          />

          <div className="bento-deck-header">
            <div className="bento-header-left">
              <span
                className="bento-badge"
                style={{
                  color: accentColor,
                  background: `${accentColor}15`,
                  borderColor: `${accentColor}35`,
                }}
              >
                <Zap size={13} />
                <span>30-SECOND EXECUTIVE BRIEFING</span>
              </span>
              <span className="bento-kicker-meta">High-Impact Key Takeaways & Soundbite</span>
            </div>

            <div className="bento-header-right">
              <span className="bento-verified-tag">
                <ShieldCheck size={13} style={{ color: '#10b981' }} />
                <span>Verified Intelligence • {story.sourceName}</span>
              </span>
            </div>
          </div>

          <div className="bento-deck-grid">
            {/* LEFT SIDE: KEY QUOTE COMMAND CARD (Fills the left side space with dramatic Gen-Z aesthetic) */}
            {structured.pullQuote?.quote && (
              <div
                className="bento-key-quote-card"
                style={{
                  borderColor: `${accentColor}40`,
                  background: `linear-gradient(145deg, ${accentColor}12 0%, #10131d 55%, #0b0d14 100%)`,
                  boxShadow: `0 12px 36px rgba(0,0,0,0.45), inset 0 0 24px ${accentColor}08`,
                }}
              >
                <div className="bento-quote-top-row">
                  <div className="quote-badge-group">
                    <Quote size={24} style={{ color: accentColor, opacity: 0.95 }} />
                    <span
                      className="quote-badge"
                      style={{
                        color: accentColor,
                        borderColor: `${accentColor}35`,
                        background: `${accentColor}16`,
                      }}
                    >
                      KEY QUOTE
                    </span>
                  </div>
                  <button
                    type="button"
                    className="quote-copy-btn"
                    onClick={() =>
                      handleCopyQuote(
                        structured.pullQuote.quote,
                        structured.pullQuote.author || story.sourceName
                      )
                    }
                    title="Copy Quote"
                    style={{ borderColor: `${accentColor}33`, color: accentColor }}
                  >
                    {quoteCopied ? <Check size={12} style={{ color: '#10b981' }} /> : <Share2 size={12} />}
                    <span>{quoteCopied ? 'Copied!' : 'Copy Quote'}</span>
                  </button>
                </div>

                <blockquote className="bento-quote-text">
                  "{structured.pullQuote.quote}"
                </blockquote>

                <div className="bento-quote-attribution">
                  <span className="bento-attribution-dash" style={{ background: accentColor }} />
                  <span className="bento-attribution-author" style={{ color: accentColor }}>
                    {structured.pullQuote.author || story.sourceName}
                  </span>
                </div>
              </div>
            )}

            {/* RIGHT SIDE: 30-SECOND BRIEFING / THE BIG PICTURE AT A GLANCE */}
            {structured.tldr && structured.tldr.length > 0 && (
              <div className="bento-briefing-column">
                <div className="bento-briefing-header">
                  <h3 className="bento-briefing-title">The Big Picture at a Glance</h3>
                  <span className="bento-briefing-sub">High-Impact Key Takeaways</span>
                </div>

                <div className="bento-capsules-grid">
                  {structured.tldr.map((item, idx) => (
                    <div
                      key={idx}
                      className="bento-capsule-item"
                      style={{
                        borderColor: idx === 0 ? `${accentColor}35` : 'rgba(255, 255, 255, 0.08)',
                        background:
                          idx === 0
                            ? `linear-gradient(145deg, ${accentColor}0e 0%, rgba(18, 22, 32, 0.75) 100%)`
                            : 'rgba(255, 255, 255, 0.035)',
                      }}
                    >
                      <div className="bento-capsule-top">
                        <span className="bento-capsule-icon">{item.icon}</span>
                        <span
                          className="bento-capsule-title"
                          style={{ color: idx === 0 ? accentColor : '#ffffff' }}
                        >
                          {item.title}
                        </span>
                      </div>
                      <p className="bento-capsule-text">{item.text}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      )}

      {/* 4. THE COMPLETE GEN-Z EDITORIAL NEWS EXPERIENCE & SIDEBAR */}
      <div className={`story-editorial-split-layout ${hasSidebar ? 'has-sidebar' : 'full-width-editorial'}`}>
        <div className="story-editorial-main-content">
          {/* READER UTILITY & EXPERIENCE TOOLBAR */}
          <div className="story-reader-toolbar">
            <div className="reader-toolbar-left">
              <span className="reader-stat-pill">
                <Clock size={13} style={{ color: accentColor }} />
                <span>{structured.readTime || '⚡ 3 min read'}</span>
              </span>
              <span className="reader-stat-pill">
                <FileText size={13} style={{ color: '#94a3b8' }} />
                <span>{structured.wordCount || 420} words</span>
              </span>
              <span className="reader-stat-pill verified-coverage-pill">
                <ShieldCheck size={13} style={{ color: '#10b981' }} />
                <span>Verified by {story.sourceName}</span>
              </span>
            </div>

            <div className="reader-toolbar-right">
              {/* Interactive Font Size Scaler */}
              <div className="reader-font-scaler" title="Adjust Article Text Size">
                <Type size={13} style={{ color: '#94a3b8' }} />
                <button
                  type="button"
                  className={`font-size-btn ${fontSize === 'sm' ? 'active' : ''}`}
                  onClick={() => setFontSize('sm')}
                  title="Compact Font (15px)"
                >
                  S
                </button>
                <button
                  type="button"
                  className={`font-size-btn ${fontSize === 'md' ? 'active' : ''}`}
                  onClick={() => setFontSize('md')}
                  title="Standard Font (17px)"
                >
                  M
                </button>
                <button
                  type="button"
                  className={`font-size-btn ${fontSize === 'lg' ? 'active' : ''}`}
                  onClick={() => setFontSize('lg')}
                  title="Comfort Font (19px)"
                >
                  L
                </button>
              </div>

              {/* Text-to-Speech Audio Briefing */}
              <button
                type="button"
                className={`audio-briefing-toggle-btn ${isSpeaking ? 'speaking' : ''}`}
                onClick={toggleSpeech}
                title={isSpeaking ? 'Stop Audio Briefing' : 'Listen to Audio Briefing'}
                style={{
                  borderColor: isSpeaking ? accentColor : 'var(--border-subtle)',
                  background: isSpeaking ? `${accentColor}25` : 'rgba(255,255,255,0.04)',
                  color: isSpeaking ? accentColor : '#e2e8f0',
                }}
              >
                {isSpeaking ? (
                  <>
                    <VolumeX size={14} />
                    <span className="audio-equalizer-bars">
                      <span className="eq-bar bar-1" style={{ background: accentColor }} />
                      <span className="eq-bar bar-2" style={{ background: accentColor }} />
                      <span className="eq-bar bar-3" style={{ background: accentColor }} />
                    </span>
                    <span>Stop Audio</span>
                  </>
                ) : (
                  <>
                    <Volume2 size={14} />
                    <span>Listen Story</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* MAIN ARTICLE JOURNALISTIC BODY */}
          <article className={`story-article-narrative-flow text-size-${fontSize}`}>
            {/* Editorial Lead Paragraph with Drop-Cap */}
            {structured.leadParagraph && (
              <div className="article-lead-wrapper">
                <div className="article-lead-kicker" style={{ color: accentColor }}>
                  <TrendingUp size={14} />
                  <span>SPECIAL REPORT & ANALYSIS</span>
                </div>
                <div className="article-lead-paragraph">
                  {/^[A-Za-z0-9]/.test(structured.leadParagraph) ? (
                    <>
                      <span className="lead-drop-cap" style={{ color: accentColor, textShadow: `0 0 20px ${accentColor}44` }}>
                        {structured.leadParagraph.charAt(0)}
                      </span>
                      <p className="lead-text">{structured.leadParagraph.slice(1)}</p>
                    </>
                  ) : (
                    <p className="lead-text">{structured.leadParagraph}</p>
                  )}
                </div>
              </div>
            )}

            {/* Editorial Subsections with Headings & Narrative */}
            {structured.sections && structured.sections.length > 0 ? (
              structured.sections.map((sec, sIdx) => (
                <div key={sIdx} className="article-narrative-section">
                  <h3 className="article-section-heading">
                    <span className="heading-accent-bar" style={{ background: accentColor }} />
                    <span>{sec.heading}</span>
                  </h3>
                  {sec.paragraphs.map((p, pIdx) => (
                    <p key={pIdx} className="narrative-paragraph">
                      {p}
                    </p>
                  ))}
                </div>
              ))
            ) : (
              remainingParagraphs.map((paragraph, pIdx) => (
                <p key={pIdx} className="narrative-paragraph">
                  {paragraph}
                </p>
              ))
            )}

            {/* KEY TOPICS & ENTITY HASHTAG CLOUD */}
            {structured.entities && structured.entities.length > 0 && (
              <div className="article-entities-cloud">
                <div className="entities-cloud-label">
                  <Hash size={14} style={{ color: accentColor }} />
                  <span>Related Topics & Entities</span>
                </div>
                <div className="entities-tag-list">
                  {structured.entities.map((tag, tIdx) => (
                    <button
                      key={tIdx}
                      type="button"
                      className="entity-tag-pill"
                      onClick={() => navigate(`/search?q=${encodeURIComponent(tag)}`)}
                      style={{
                        '--accent': accentColor,
                      }}
                    >
                      #{tag}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* THE BOTTOM LINE (KEY ACTIONABLE TAKEAWAYS) */}
            {structured.takeaways && structured.takeaways.length > 0 && (
              <div className="bottom-line-actionable-card">
                <div className="bottom-line-actionable-header">
                  <div className="bottom-line-icon-badge">
                    <CheckCircle2 size={18} style={{ color: '#10b981' }} />
                  </div>
                  <div>
                    <h4 className="bottom-line-card-title">The Bottom Line</h4>
                    <span className="bottom-line-card-sub">Verified Takeaways & Strategic Summary</span>
                  </div>
                </div>
                <div className="bottom-line-actionable-list">
                  {structured.takeaways.map((takeaway, tIdx) => (
                    <div key={tIdx} className="bottom-line-actionable-item">
                      <span className="actionable-bullet" style={{ background: accentColor }} />
                      <span className="actionable-text">{takeaway}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </article>

          {/* INTERACTIVE ENGAGEMENT DOCK */}
          <div className="story-engagement-dock">
            <div className="engagement-prompt">
              <span className="prompt-label">Did you find this report informative?</span>
              <span className="prompt-sub">Calibrate the ESTD intelligence recommendation engine</span>
            </div>

            <div className="engagement-actions-row">
              <button
                type="button"
                className={`dock-btn ${hasLiked ? 'liked' : ''}`}
                onClick={handleToggleLike}
                disabled={isLiking}
                style={{
                  borderColor: hasLiked ? accentColor : 'var(--border-subtle)',
                  background: hasLiked ? `${accentColor}20` : 'rgba(255,255,255,0.05)',
                  color: hasLiked ? accentColor : '#ffffff',
                }}
              >
                <Flame size={16} fill={hasLiked ? accentColor : 'none'} />
                <span>{hasLiked ? 'Verified & Helpful' : 'Helpful Story'} ({likesCount})</span>
              </button>

              <button type="button" className="dock-btn" onClick={handleShare}>
                {copied ? <Check size={16} style={{ color: '#10b981' }} /> : <Share2 size={16} />}
                <span>{copied ? 'Copied Link!' : 'Share Story'}</span>
              </button>

              <button
                type="button"
                className="dock-btn"
                onClick={() => onToggleSave && onToggleSave(story)}
                style={{
                  color: isSaved ? '#FFB020' : '#ffffff',
                  borderColor: isSaved ? '#FFB020' : 'var(--border-subtle)',
                  background: isSaved ? 'rgba(255, 176, 32, 0.15)' : 'rgba(255,255,255,0.05)',
                }}
              >
                <Bookmark size={16} fill={isSaved ? '#FFB020' : 'none'} />
                <span>{isSaved ? 'Saved in Library' : 'Save Story'}</span>
              </button>

              <button
                type="button"
                className="dock-btn back-to-top-btn"
                onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                title="Scroll back to top"
              >
                <ArrowUp size={15} />
                <span>Top</span>
              </button>
            </div>
          </div>
        </div>

        {/* SIDEBAR FOR RELATED & SUBCATEGORY STORIES */}
        {(subcategoryStories.length > 0 || relatedCategoryStories.length > 0) && (
          <aside className="story-editorial-sidebar">
            {subcategoryStories.length > 0 && (
              <div className="sidebar-section-card">
                <h4 className="sidebar-section-title">
                  <Layers size={15} style={{ color: accentColor }} />
                  <span>More in {story.subcategory}</span>
                </h4>

                <div className="related-stories-container">
                  {subcategoryStories.map((item) => (
                    <div
                      key={item.id}
                      className="related-story-card"
                      onClick={() => navigate(`/story/${item.id}`)}
                    >
                      <h5>{item.headline}</h5>
                      <div className="related-story-meta">
                        <span>{item.sourceName}</span>
                        <span className="related-video-pill">
                          <Video size={11} />
                          {item.videoRail?.length || 5} videos
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {relatedCategoryStories.length > 0 && (
              <div className="sidebar-section-card">
                <h4 className="sidebar-section-title">
                  <Sparkles size={15} style={{ color: accentColor }} />
                  <span>Related {story.category} Stories</span>
                </h4>

                <div className="related-stories-container">
                  {relatedCategoryStories.map((item) => (
                    <div
                      key={item.id}
                      className="related-story-card"
                      onClick={() => navigate(`/story/${item.id}`)}
                    >
                      <h5>{item.headline}</h5>
                      <div className="related-story-meta">
                        <span>{item.subcategory}</span>
                        <span>{item.sourceName}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </aside>
        )}
      </div>

      {/* Interactive In-Story Video Modal Player */}
      {isModalOpen && (
        <VideoModalPlayer
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          story={story}
          initialVideoIndex={modalVideoIndex}
          accentColor={accentColor}
          isSaved={isSaved}
          onToggleSave={onToggleSave}
        />
      )}

      {/* Interactive 60-Second Flash Bite Modal Viewer (Locked strictly to current article) */}
      <FlashBiteModal
        isOpen={isFlashModalOpen}
        story={story}
        stories={[story]}
        onClose={() => setIsFlashModalOpen(false)}
      />
    </div>
  );
}
