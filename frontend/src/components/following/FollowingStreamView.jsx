import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  ArrowRight,
  Bookmark,
  Share2,
  Heart,
  Play,
  Clock,
  Check,
  Plus,
  Cpu,
  Film,
  TrendingUp,
  Compass,
  Trophy,
  SlidersHorizontal,
  Flame,
  Radio,
  Eye,
  CheckCircle2,
} from 'lucide-react';
import ImageWithFallback from '../common/ImageWithFallback';
import { CATEGORIES, CATEGORY_MAP } from '../../constants/taxonomy';
import { toggleStoryLike } from '../../api/estdApi';
import { trackArticleRead } from '../../utils/readingHistory';
import { useFollowedCategories } from '../../utils/followedCategories';

const CATEGORY_ICON_MAP = {
  Tech: Cpu,
  Entertainment: Film,
  'Business & Finance': TrendingUp,
  Developments: Compass,
  Sports: Trophy,
};

export default function FollowingStreamView({
  stories = [],
  savedStories = [],
  onToggleSave,
  watchLaterStories = [],
  onToggleWatchLater,
  onWatchVideo,
  onListen,
}) {
  const navigate = useNavigate();
  const { followedCategories, toggleCategory, isFollowing } = useFollowedCategories();

  // Active category filter tab: Defaults to the first followed category, or 'Tech'
  const [selectedCategory, setSelectedCategory] = useState(() => {
    return followedCategories[0] || 'Tech';
  });

  const [copiedId, setCopiedId] = useState(null);

  // Likes tracking
  const [likedMap, setLikedMap] = useState(() => {
    try {
      const stored = localStorage.getItem('estd_liked_stories');
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  });

  const [likeCounts, setLikeCounts] = useState({});

  const handleLike = async (e, story) => {
    e.stopPropagation();
    const storyId = story.id;
    const isLiked = !!likedMap[storyId];
    const nextState = !isLiked;

    setLikedMap((prev) => {
      const updated = { ...prev, [storyId]: nextState };
      try {
        localStorage.setItem('estd_liked_stories', JSON.stringify(updated));
      } catch (err) {}
      return updated;
    });

    const currentCount =
      typeof likeCounts[storyId] === 'number'
        ? likeCounts[storyId]
        : story.likesCount || 0;

    setLikeCounts((prev) => ({
      ...prev,
      [storyId]: nextState ? currentCount + 1 : Math.max(0, currentCount - 1),
    }));

    try {
      const res = await toggleStoryLike(storyId);
      if (res && typeof res.likes_count === 'number') {
        setLikeCounts((prev) => ({ ...prev, [storyId]: res.likes_count }));
      }
    } catch (err) {
      console.warn('Like failed:', err);
    }
  };

  const handleShare = async (e, story) => {
    e.stopPropagation();
    const shareUrl = `${window.location.origin}/story/${story.id}`;
    if (navigator.share) {
      try {
        await navigator.share({
          title: story.headline,
          text: story.brief,
          url: shareUrl,
        });
      } catch (err) {
        copyToClipboard(shareUrl, story.id);
      }
    } else {
      copyToClipboard(shareUrl, story.id);
    }
  };

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleOpenStory = (story) => {
    trackArticleRead(story);
    navigate(`/story/${story.id}`);
  };

  // Filter stories based on selected category (or 'All' followed)
  const filteredStories = useMemo(() => {
    if (selectedCategory === 'All') {
      if (followedCategories.length === 0) return stories;
      return stories.filter((s) => followedCategories.includes(s.category));
    }
    return stories.filter((s) => s.category === selectedCategory);
  }, [stories, selectedCategory, followedCategories]);

  // Lead Top Story & Subsequent Stream
  const leadStory = filteredStories[0] || null;
  const subsequentStories = filteredStories.slice(1);

  // Active Category Meta
  const activeCatMeta = CATEGORY_MAP[selectedCategory] || CATEGORIES[0];
  const accentColor = activeCatMeta.color || '#00E5FF';
  const isCurrentFollowed = isFollowing(selectedCategory);

  return (
    <div className="following-magazine-stream" style={{ maxWidth: 1200, margin: '0 auto', paddingBottom: 60 }}>
      {/* ============================================================== */}
      {/* 1. SECTOR NAVIGATION BAR (Explore Desks & Toggle Follow)        */}
      {/* ============================================================== */}
      <div
        style={{
          background: '#090C15',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: 16,
          padding: '12px 16px',
          marginBottom: 24,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          {/* Optional 'All Followed' pill if user follows more than 1 category */}
          {followedCategories.length > 1 && (
            <button
              type="button"
              onClick={() => setSelectedCategory('All')}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '7px 14px',
                borderRadius: 20,
                fontSize: 12.5,
                fontWeight: 800,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                background: selectedCategory === 'All' ? '#00E5FF' : 'rgba(255, 255, 255, 0.04)',
                color: selectedCategory === 'All' ? '#000000' : '#ffffff',
                border: selectedCategory === 'All' ? '1px solid #00E5FF' : '1px solid rgba(255, 255, 255, 0.1)',
                boxShadow: selectedCategory === 'All' ? '0 0 14px rgba(0, 229, 255, 0.4)' : 'none',
              }}
            >
              <Sparkles size={13} />
              <span>All Followed</span>
              <span
                style={{
                  fontSize: 11,
                  padding: '1px 5px',
                  borderRadius: 8,
                  background: selectedCategory === 'All' ? 'rgba(0,0,0,0.25)' : 'rgba(255,255,255,0.12)',
                  fontWeight: 800,
                }}
              >
                {stories.filter((s) => followedCategories.includes(s.category)).length}
              </span>
            </button>
          )}

          {/* Canonical 5 Category Tabs with Live Follow Status */}
          {CATEGORIES.map((cat) => {
            const isCatFollowed = isFollowing(cat.name);
            const isSelected = selectedCategory === cat.name;
            const CatIcon = CATEGORY_ICON_MAP[cat.name] || Compass;

            return (
              <div
                key={cat.id}
                onClick={() => setSelectedCategory(cat.name)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 8,
                  padding: '6px 12px',
                  borderRadius: 12,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  background: isSelected
                    ? `linear-gradient(135deg, ${cat.color}22, #0D101A)`
                    : 'rgba(255, 255, 255, 0.03)',
                  border: isSelected
                    ? `1.5px solid ${cat.color}`
                    : isCatFollowed
                    ? `1px solid ${cat.color}55`
                    : '1px solid rgba(255, 255, 255, 0.08)',
                  boxShadow: isSelected ? `0 0 16px ${cat.color}35` : 'none',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <CatIcon
                    size={14}
                    style={{ color: isSelected ? cat.color : isCatFollowed ? cat.color : '#94a3b8' }}
                  />
                  <span style={{ fontSize: 13, fontWeight: 800, color: isSelected ? '#ffffff' : '#cbd5e1' }}>
                    {cat.name}
                  </span>
                </div>

                {/* Follow Button on the Tab */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleCategory(cat.name);
                  }}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 3,
                    padding: '2px 7px',
                    borderRadius: 10,
                    fontSize: 10.5,
                    fontWeight: 800,
                    cursor: 'pointer',
                    background: isCatFollowed ? cat.color : 'rgba(255, 255, 255, 0.08)',
                    color: isCatFollowed ? '#000000' : '#94a3b8',
                    border: isCatFollowed ? `1px solid ${cat.color}` : '1px solid rgba(255, 255, 255, 0.15)',
                    transition: 'all 0.15s ease',
                  }}
                  title={isCatFollowed ? `Unfollow ${cat.name}` : `Follow ${cat.name}`}
                >
                  {isCatFollowed ? (
                    <>
                      <Check size={10} strokeWidth={3} />
                      <span>Following</span>
                    </>
                  ) : (
                    <>
                      <Plus size={10} strokeWidth={2} />
                      <span>Follow</span>
                    </>
                  )}
                </button>
              </div>
            );
          })}
        </div>

        {/* Current Following Counter */}
        <div style={{ fontSize: 12, color: '#94a3b8', fontWeight: 700 }}>
          <b style={{ color: '#00E5FF' }}>{followedCategories.length} of 5</b> Desks Followed
        </div>
      </div>

      {/* ============================================================== */}
      {/* 2. FEED HEADER STRIP                                           */}
      {/* ============================================================== */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
          marginBottom: 20,
          padding: '14px 20px',
          borderRadius: 14,
          background: `linear-gradient(90deg, ${accentColor}15, rgba(13, 16, 26, 0.6))`,
          border: `1px solid ${accentColor}44`,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: accentColor,
              boxShadow: `0 0 10px ${accentColor}`,
            }}
          />
          <h2 style={{ fontSize: 16, fontWeight: 900, color: '#ffffff', margin: 0 }}>
            {selectedCategory === 'All'
              ? 'All Followed Dispatches'
              : `${selectedCategory} Intelligence Wire`}
          </h2>
          <span
            style={{
              fontSize: 11,
              fontWeight: 800,
              padding: '2px 8px',
              borderRadius: 8,
              background: 'rgba(255, 255, 255, 0.08)',
              color: '#cbd5e1',
            }}
          >
            {filteredStories.length} Stories
          </span>
        </div>

        {selectedCategory !== 'All' && (
          <button
            type="button"
            onClick={() => toggleCategory(selectedCategory)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 5,
              padding: '6px 14px',
              borderRadius: 20,
              fontSize: 12,
              fontWeight: 800,
              cursor: 'pointer',
              background: isCurrentFollowed ? accentColor : 'rgba(255, 255, 255, 0.08)',
              color: isCurrentFollowed ? '#000000' : '#ffffff',
              border: isCurrentFollowed ? `1px solid ${accentColor}` : '1px solid rgba(255, 255, 255, 0.2)',
              boxShadow: isCurrentFollowed ? `0 0 14px ${accentColor}66` : 'none',
              transition: 'all 0.15s ease',
            }}
          >
            {isCurrentFollowed ? (
              <>
                <Check size={12} strokeWidth={3} />
                <span>{selectedCategory} Following</span>
              </>
            ) : (
              <>
                <Plus size={12} strokeWidth={2.5} />
                <span>+ Follow {selectedCategory}</span>
              </>
            )}
          </button>
        )}
      </div>

      {/* ============================================================== */}
      {/* 3. ASYMMETRICAL CINEMA LEAD STORY CARD (Top Featured Story)   */}
      {/* ============================================================== */}
      {leadStory && (
        <div
          onClick={() => handleOpenStory(leadStory)}
          style={{
            position: 'relative',
            borderRadius: 18,
            background: 'linear-gradient(145deg, #0f1320, #080a11)',
            border: `1.5px solid ${accentColor}55`,
            boxShadow: `0 12px 36px rgba(0, 0, 0, 0.6), 0 0 24px ${accentColor}18`,
            overflow: 'hidden',
            cursor: 'pointer',
            marginBottom: 28,
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            transition: 'all 0.25s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = accentColor;
            e.currentTarget.style.boxShadow = `0 16px 44px rgba(0, 0, 0, 0.7), 0 0 32px ${accentColor}30`;
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = `${accentColor}55`;
            e.currentTarget.style.boxShadow = `0 12px 36px rgba(0, 0, 0, 0.6), 0 0 24px ${accentColor}18`;
          }}
        >
          {/* Media Showcase */}
          <div style={{ position: 'relative', minHeight: 280, overflow: 'hidden' }}>
            <ImageWithFallback
              src={leadStory.imageUrl}
              alt={leadStory.headline}
              category={leadStory.category}
              subcategory={leadStory.subcategory}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
                display: 'block',
              }}
            />
            <div
              style={{
                position: 'absolute',
                inset: 0,
                background: 'linear-gradient(180deg, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0.7) 100%)',
              }}
            />

            {/* Badges on Media */}
            <div
              style={{
                position: 'absolute',
                top: 14,
                left: 14,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span
                style={{
                  padding: '4px 10px',
                  borderRadius: 6,
                  background: accentColor,
                  color: '#000000',
                  fontSize: 11,
                  fontWeight: 900,
                  textTransform: 'uppercase',
                }}
              >
                {leadStory.category}
              </span>
              {leadStory.sourceName && (
                <span
                  style={{
                    padding: '4px 10px',
                    borderRadius: 6,
                    background: 'rgba(0, 0, 0, 0.75)',
                    backdropFilter: 'blur(8px)',
                    color: '#ffffff',
                    fontSize: 11,
                    fontWeight: 700,
                    border: '1px solid rgba(255, 255, 255, 0.15)',
                  }}
                >
                  {leadStory.sourceName}
                </span>
              )}
            </div>

            {/* Reel overlay */}
            {onWatchVideo && (
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  onWatchVideo(leadStory, 0);
                }}
                style={{
                  position: 'absolute',
                  bottom: 14,
                  left: 14,
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '6px 12px',
                  borderRadius: 16,
                  background: 'rgba(0, 0, 0, 0.8)',
                  backdropFilter: 'blur(8px)',
                  border: '1px solid rgba(255, 255, 255, 0.25)',
                  color: '#ffffff',
                  fontSize: 11.5,
                  fontWeight: 800,
                  cursor: 'pointer',
                }}
              >
                <Play size={11} fill="#ffffff" />
                <span>Watch Reel</span>
              </button>
            )}
          </div>

          {/* Details Content */}
          <div
            style={{
              padding: '24px 28px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              gap: 16,
            }}
          >
            <div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginBottom: 8,
                  fontSize: 11.5,
                  color: accentColor,
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                }}
              >
                <span>⚡ Top Dispatch</span>
                {leadStory.subcategory && (
                  <>
                    <span style={{ color: '#475569' }}>•</span>
                    <span style={{ color: '#94a3b8' }}>{leadStory.subcategory}</span>
                  </>
                )}
              </div>

              <h3
                style={{
                  fontSize: 20,
                  fontWeight: 900,
                  color: '#ffffff',
                  lineHeight: 1.35,
                  margin: '0 0 12px 0',
                  letterSpacing: '-0.01em',
                }}
              >
                {leadStory.headline}
              </h3>

              <p
                style={{
                  fontSize: 13,
                  color: '#cbd5e1',
                  lineHeight: 1.6,
                  margin: 0,
                  display: '-webkit-box',
                  WebkitLineClamp: 3,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                }}
              >
                {leadStory.brief}
              </p>
            </div>

            {/* Actions */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingTop: 14,
                borderTop: '1px solid rgba(255, 255, 255, 0.08)',
                flexWrap: 'wrap',
                gap: 10,
              }}
            >
              <button
                type="button"
                onClick={() => handleOpenStory(leadStory)}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '8px 16px',
                  borderRadius: 10,
                  background: accentColor,
                  color: '#000000',
                  fontSize: 12.5,
                  fontWeight: 800,
                  border: 'none',
                  cursor: 'pointer',
                  boxShadow: `0 0 16px ${accentColor}55`,
                }}
              >
                <span>Read Full Briefing</span>
                <ArrowRight size={14} />
              </button>

              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                {/* Like */}
                <button
                  type="button"
                  onClick={(e) => handleLike(e, leadStory)}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 4,
                    padding: '6px 10px',
                    borderRadius: 8,
                    background: likedMap[leadStory.id] ? 'rgba(239, 68, 68, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                    border: likedMap[leadStory.id] ? '1px solid rgba(239, 68, 68, 0.4)' : '1px solid rgba(255, 255, 255, 0.1)',
                    color: likedMap[leadStory.id] ? '#ef4444' : '#cbd5e1',
                    fontSize: 11.5,
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  <Heart size={13} fill={likedMap[leadStory.id] ? '#ef4444' : 'none'} />
                  <span>{(likeCounts[leadStory.id] ?? leadStory.likesCount) || 0}</span>
                </button>

                {/* Save */}
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onToggleSave && onToggleSave(leadStory);
                  }}
                  style={{
                    padding: '6px 10px',
                    borderRadius: 8,
                    background: savedStories.some((s) => s.id === leadStory.id) ? 'rgba(0, 229, 255, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                    border: savedStories.some((s) => s.id === leadStory.id) ? '1px solid #00E5FF' : '1px solid rgba(255, 255, 255, 0.1)',
                    color: savedStories.some((s) => s.id === leadStory.id) ? '#00E5FF' : '#cbd5e1',
                    cursor: 'pointer',
                  }}
                  title="Save to Vault"
                >
                  <Bookmark size={13} fill={savedStories.some((s) => s.id === leadStory.id) ? '#00E5FF' : 'none'} />
                </button>

                {/* Share */}
                <button
                  type="button"
                  onClick={(e) => handleShare(e, leadStory)}
                  style={{
                    padding: '6px 9px',
                    borderRadius: 8,
                    background: 'rgba(255, 255, 255, 0.05)',
                    border: '1px solid rgba(255, 255, 255, 0.1)',
                    color: copiedId === leadStory.id ? '#10B981' : '#cbd5e1',
                    cursor: 'pointer',
                  }}
                  title="Share"
                >
                  {copiedId === leadStory.id ? <Check size={13} /> : <Share2 size={13} />}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* 4. CURATED HORIZONTAL MAGAZINE STREAM (Different News Cards)   */}
      {/* ============================================================== */}
      {subsequentStories.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {subsequentStories.map((story) => {
            const storyColor = CATEGORY_MAP[story.category]?.color || accentColor;
            const isSaved = savedStories.some((s) => s.id === story.id);
            const isLiked = !!likedMap[story.id];
            const storyLikes = (likeCounts[story.id] ?? story.likesCount) || 0;

            return (
              <div
                key={story.id}
                onClick={() => handleOpenStory(story)}
                style={{
                  display: 'flex',
                  alignItems: 'stretch',
                  background: '#0D101A',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: 14,
                  overflow: 'hidden',
                  cursor: 'pointer',
                  transition: 'all 0.18s ease',
                  flexWrap: 'wrap',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = storyColor;
                  e.currentTarget.style.transform = 'translateX(4px)';
                  e.currentTarget.style.boxShadow = `0 8px 24px rgba(0, 0, 0, 0.5), 0 0 16px ${storyColor}20`;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                  e.currentTarget.style.transform = 'none';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                {/* Left Thumbnail (Wide aspect) */}
                <div
                  style={{
                    position: 'relative',
                    width: 260,
                    minHeight: 160,
                    flexShrink: 0,
                    overflow: 'hidden',
                  }}
                >
                  <ImageWithFallback
                    src={story.imageUrl}
                    alt={story.headline}
                    category={story.category}
                    subcategory={story.subcategory}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'cover',
                      display: 'block',
                    }}
                  />
                  <div
                    style={{
                      position: 'absolute',
                      inset: 0,
                      background: 'linear-gradient(180deg, rgba(0,0,0,0.1) 0%, rgba(13,16,26,0.8) 100%)',
                    }}
                  />

                  {/* Subcategory chip */}
                  {story.subcategory && (
                    <span
                      style={{
                        position: 'absolute',
                        top: 10,
                        left: 10,
                        padding: '3px 8px',
                        borderRadius: 6,
                        background: 'rgba(0, 0, 0, 0.7)',
                        backdropFilter: 'blur(6px)',
                        color: storyColor,
                        fontSize: 10,
                        fontWeight: 800,
                        border: `1px solid ${storyColor}44`,
                      }}
                    >
                      {story.subcategory}
                    </span>
                  )}

                  {/* Video Reel trigger */}
                  {onWatchVideo && (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onWatchVideo(story, 0);
                      }}
                      style={{
                        position: 'absolute',
                        bottom: 8,
                        right: 8,
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '3px 8px',
                        borderRadius: 10,
                        background: 'rgba(0, 0, 0, 0.8)',
                        backdropFilter: 'blur(6px)',
                        border: '1px solid rgba(255, 255, 255, 0.2)',
                        color: '#ffffff',
                        fontSize: 10.5,
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      <Play size={10} fill="#ffffff" />
                      <span>Reel</span>
                    </button>
                  )}
                </div>

                {/* Right Content */}
                <div
                  style={{
                    padding: '16px 20px',
                    flex: 1,
                    minWidth: 280,
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    {/* Meta Info */}
                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 8,
                        marginBottom: 6,
                        fontSize: 11,
                        color: '#94a3b8',
                      }}
                    >
                      <span
                        style={{
                          fontWeight: 800,
                          color: storyColor,
                          textTransform: 'uppercase',
                        }}
                      >
                        {story.category}
                      </span>
                      {story.sourceName && (
                        <>
                          <span>•</span>
                          <span style={{ color: '#cbd5e1' }}>{story.sourceName}</span>
                        </>
                      )}
                    </div>

                    <h4
                      style={{
                        fontSize: 16,
                        fontWeight: 800,
                        color: '#ffffff',
                        lineHeight: 1.4,
                        margin: '0 0 8px 0',
                      }}
                    >
                      {story.headline}
                    </h4>

                    <p
                      style={{
                        fontSize: 12.5,
                        color: '#94a3b8',
                        lineHeight: 1.55,
                        margin: 0,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                      }}
                    >
                      {story.brief}
                    </p>
                  </div>

                  {/* Actions Footer */}
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      paddingTop: 10,
                      marginTop: 10,
                      borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => handleOpenStory(story)}
                      style={{
                        background: 'none',
                        border: 'none',
                        color: storyColor,
                        fontSize: 12,
                        fontWeight: 800,
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: 0,
                        cursor: 'pointer',
                      }}
                    >
                      <span>Read Full Story</span>
                      <ArrowRight size={13} />
                    </button>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {/* Like */}
                      <button
                        type="button"
                        onClick={(e) => handleLike(e, story)}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 4,
                          padding: '4px 7px',
                          borderRadius: 6,
                          background: isLiked ? 'rgba(239, 68, 68, 0.15)' : 'transparent',
                          border: isLiked ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid transparent',
                          color: isLiked ? '#ef4444' : '#64748b',
                          fontSize: 11,
                          fontWeight: 700,
                          cursor: 'pointer',
                        }}
                      >
                        <Heart size={12} fill={isLiked ? '#ef4444' : 'none'} />
                        <span>{storyLikes}</span>
                      </button>

                      {/* Save */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          onToggleSave && onToggleSave(story);
                        }}
                        style={{
                          padding: '4px 6px',
                          borderRadius: 6,
                          background: isSaved ? 'rgba(0, 229, 255, 0.15)' : 'transparent',
                          border: isSaved ? '1px solid #00E5FF' : '1px solid transparent',
                          color: isSaved ? '#00E5FF' : '#64748b',
                          cursor: 'pointer',
                        }}
                        title="Save to Vault"
                      >
                        <Bookmark size={12} fill={isSaved ? '#00E5FF' : 'none'} />
                      </button>

                      {/* Share */}
                      <button
                        type="button"
                        onClick={(e) => handleShare(e, story)}
                        style={{
                          padding: '4px 6px',
                          borderRadius: 6,
                          background: 'transparent',
                          border: 'none',
                          color: copiedId === story.id ? '#10B981' : '#64748b',
                          cursor: 'pointer',
                        }}
                        title="Share"
                      >
                        {copiedId === story.id ? <Check size={12} /> : <Share2 size={12} />}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {filteredStories.length === 0 && (
        <div style={{ padding: '60px 20px', textAlign: 'center', color: '#64748b' }}>
          <p style={{ fontSize: 15, margin: 0 }}>No dispatches available under this selection.</p>
        </div>
      )}
    </div>
  );
}
