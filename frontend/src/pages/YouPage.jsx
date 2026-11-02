import React, { useState, useEffect } from 'react';
import { useNavigate, useOutletContext } from 'react-router-dom';
import {
  Bookmark,
  Check,
  Edit3,
  Camera,
  Play,
  Trash2,
  Clock,
  CheckCircle2,
  BookOpen,
  ArrowRight,
  Rss,
  Plus,
  Cpu,
  Film,
  TrendingUp,
  Compass,
  Trophy,
  X,
  Sparkles,
} from 'lucide-react';
import { CATEGORIES } from '../constants/taxonomy';
import ImageWithFallback from '../components/common/ImageWithFallback';
import { useReadingHistory } from '../utils/readingHistory';
import { useFollowedCategories } from '../utils/followedCategories';

const CATEGORY_ICON_MAP = {
  Tech: Cpu,
  Entertainment: Film,
  'Business & Finance': TrendingUp,
  Developments: Compass,
  Sports: Trophy,
};

// Helper to generate crisp SVG data URLs for Snapchat/Bitmoji-style emoji avatars
const createEmojiAvatarSvg = (emoji, color1, color2) => {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
    <defs>
      <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="${color1}"/>
        <stop offset="100%" stop-color="${color2}"/>
      </linearGradient>
      <radialGradient id="h" cx="35%" cy="25%" r="60%">
        <stop offset="0%" stop-color="#ffffff" stop-opacity="0.32"/>
        <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
      </radialGradient>
    </defs>
    <circle cx="64" cy="64" r="64" fill="url(#g)"/>
    <circle cx="64" cy="64" r="64" fill="url(#h)"/>
    <text x="64" y="68" font-size="62" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI Emoji','Apple Color Emoji','Noto Color Emoji',sans-serif" text-anchor="middle" dominant-baseline="central">${emoji}</text>
  </svg>`;
  return `data:image/svg+xml;utf8,${encodeURIComponent(svg)}`;
};

export const SNAP_EMOJI_AVATARS = [
  {
    id: 'cyber-fox',
    label: 'Cyber Fox',
    emoji: '🦊',
    color1: '#FF5E3A',
    color2: '#FF2A68',
    gradient: 'linear-gradient(135deg, #FF5E3A 0%, #FF2A68 100%)',
    dataUrl: createEmojiAvatarSvg('🦊', '#FF5E3A', '#FF2A68'),
  },
  {
    id: 'ai-synth',
    label: 'AI Synth',
    emoji: '🤖',
    color1: '#00E5FF',
    color2: '#0070F3',
    gradient: 'linear-gradient(135deg, #00E5FF 0%, #0070F3 100%)',
    dataUrl: createEmojiAvatarSvg('🤖', '#00E5FF', '#0070F3'),
  },
  {
    id: 'stealth-agent',
    label: 'Stealth Agent',
    emoji: '🕶️',
    color1: '#475569',
    color2: '#0F172A',
    gradient: 'linear-gradient(135deg, #475569 0%, #0F172A 100%)',
    dataUrl: createEmojiAvatarSvg('🕶️', '#475569', '#0F172A'),
  },
  {
    id: 'volt-runner',
    label: 'Volt Runner',
    emoji: '⚡',
    color1: '#FDE047',
    color2: '#EAB308',
    gradient: 'linear-gradient(135deg, #FDE047 0%, #EAB308 100%)',
    dataUrl: createEmojiAvatarSvg('⚡', '#FDE047', '#EAB308'),
  },
  {
    id: 'pioneer',
    label: 'Pioneer',
    emoji: '🚀',
    color1: '#A855F7',
    color2: '#6366F1',
    gradient: 'linear-gradient(135deg, #A855F7 0%, #6366F1 100%)',
    dataUrl: createEmojiAvatarSvg('🚀', '#A855F7', '#6366F1'),
  },
  {
    id: 'glitch-pixel',
    label: 'Glitch Pixel',
    emoji: '👾',
    color1: '#FF20B8',
    color2: '#9333EA',
    gradient: 'linear-gradient(135deg, #FF20B8 0%, #9333EA 100%)',
    dataUrl: createEmojiAvatarSvg('👾', '#FF20B8', '#9333EA'),
  },
  {
    id: 'code-ninja',
    label: 'Code Ninja',
    emoji: '🧑‍💻',
    color1: '#10B981',
    color2: '#047857',
    gradient: 'linear-gradient(135deg, #10B981 0%, #047857 100%)',
    dataUrl: createEmojiAvatarSvg('🧑‍💻', '#10B981', '#047857'),
  },
  {
    id: 'fierce-tiger',
    label: 'Fierce Tiger',
    emoji: '🐯',
    color1: '#FB923C',
    color2: '#C2410C',
    gradient: 'linear-gradient(135deg, #FB923C 0%, #C2410C 100%)',
    dataUrl: createEmojiAvatarSvg('🐯', '#FB923C', '#C2410C'),
  },
  {
    id: 'apex-hawk',
    label: 'Apex Hawk',
    emoji: '🦅',
    color1: '#38BDF8',
    color2: '#0284C7',
    gradient: 'linear-gradient(135deg, #38BDF8 0%, #0284C7 100%)',
    dataUrl: createEmojiAvatarSvg('🦅', '#38BDF8', '#0284C7'),
  },
  {
    id: 'oracle-seer',
    label: 'Oracle Seer',
    emoji: '🔮',
    color1: '#E879F9',
    color2: '#7E22CE',
    gradient: 'linear-gradient(135deg, #E879F9 0%, #7E22CE 100%)',
    dataUrl: createEmojiAvatarSvg('🔮', '#E879F9', '#7E22CE'),
  },
  {
    id: 'quantum-brain',
    label: 'Quantum Brain',
    emoji: '🧠',
    color1: '#F43F5E',
    color2: '#BE123C',
    gradient: 'linear-gradient(135deg, #F43F5E 0%, #BE123C 100%)',
    dataUrl: createEmojiAvatarSvg('🧠', '#F43F5E', '#BE123C'),
  },
  {
    id: 'apex-sovereign',
    label: 'Apex Sovereign',
    emoji: '👑',
    color1: '#FBBF24',
    color2: '#D97706',
    gradient: 'linear-gradient(135deg, #FBBF24 0%, #D97706 100%)',
    dataUrl: createEmojiAvatarSvg('👑', '#FBBF24', '#D97706'),
  },
  {
    id: 'beats-maestro',
    label: 'Beats Maestro',
    emoji: '🎧',
    color1: '#2DD4BF',
    color2: '#0F766E',
    gradient: 'linear-gradient(135deg, #2DD4BF 0%, #0F766E 100%)',
    dataUrl: createEmojiAvatarSvg('🎧', '#2DD4BF', '#0F766E'),
  },
  {
    id: 'phoenix-prime',
    label: 'Phoenix Prime',
    emoji: '🔥',
    color1: '#F97316',
    color2: '#DC2626',
    gradient: 'linear-gradient(135deg, #F97316 0%, #DC2626 100%)',
    dataUrl: createEmojiAvatarSvg('🔥', '#F97316', '#DC2626'),
  },
  {
    id: 'cosmic-nomad',
    label: 'Cosmic Nomad',
    emoji: '🌌',
    color1: '#818CF8',
    color2: '#3730A3',
    gradient: 'linear-gradient(135deg, #818CF8 0%, #3730A3 100%)',
    dataUrl: createEmojiAvatarSvg('🌌', '#818CF8', '#3730A3'),
  },
  {
    id: 'apex-lion',
    label: 'Apex Lion',
    emoji: '🦁',
    color1: '#F59E0B',
    color2: '#9A3412',
    gradient: 'linear-gradient(135deg, #F59E0B 0%, #9A3412 100%)',
    dataUrl: createEmojiAvatarSvg('🦁', '#F59E0B', '#9A3412'),
  },
];

const DEFAULT_PROFILE = {
  name: 'News Analyst',
  handle: '@analyst',
  bio: 'Tracking global news, verified dispatches, and multi-angle video intelligence across ESTD.',
  avatarUrl: SNAP_EMOJI_AVATARS[0].dataUrl,
  avatarEmoji: SNAP_EMOJI_AVATARS[0].emoji,
  avatarName: SNAP_EMOJI_AVATARS[0].label,
};

export default function YouPage({
  savedStories = [],
  onToggleSave,
  watchLaterStories = [],
  onToggleWatchLater,
}) {
  const navigate = useNavigate();
  const outletCtx = useOutletContext() || {};
  const onOpenDiagnostics = outletCtx.onOpenDiagnostics;

  // Real reading history tracking
  const { readArticles, readCount, clearHistory } = useReadingHistory();

  // Followed categories from app-wide reactive hook
  const { followedCategories, toggleCategory, isFollowing } = useFollowedCategories();

  // Profile info in localStorage with auto-migration to Snap emoji avatars
  const [profile, setProfile] = useState(() => {
    try {
      const stored = localStorage.getItem('estd_user_profile');
      if (stored) {
        const parsed = JSON.parse(stored);
        // If old profile used real stock photo or lacks emoji, migrate to default Snap avatar
        if (!parsed.avatarUrl || parsed.avatarUrl.includes('unsplash.com') || !parsed.avatarEmoji) {
          parsed.avatarUrl = SNAP_EMOJI_AVATARS[0].dataUrl;
          parsed.avatarEmoji = SNAP_EMOJI_AVATARS[0].emoji;
          parsed.avatarName = SNAP_EMOJI_AVATARS[0].label;
          try {
            localStorage.setItem('estd_user_profile', JSON.stringify({ ...DEFAULT_PROFILE, ...parsed }));
          } catch {}
        }
        return { ...DEFAULT_PROFILE, ...parsed };
      }
      return DEFAULT_PROFILE;
    } catch {
      return DEFAULT_PROFILE;
    }
  });

  // Edit Identity state
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState(profile.name);
  const [editHandle, setEditHandle] = useState(profile.handle);
  const [editBio, setEditBio] = useState(profile.bio);
  const [showAvatarModal, setShowAvatarModal] = useState(false);

  // Close avatar popup on Escape key
  useEffect(() => {
    if (!showAvatarModal) return;
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setShowAvatarModal(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showAvatarModal]);

  // Active Profile Vault Tab ('saved', 'watchlater', 'history', 'interests')
  const [activeTab, setActiveTab] = useState('saved');

  // Save profile updates to localStorage
  const handleSaveProfile = (e) => {
    e.preventDefault();
    const updated = {
      ...profile,
      name: editName.trim() || 'News Analyst',
      handle: editHandle.trim()
        ? editHandle.trim().startsWith('@')
          ? editHandle.trim()
          : `@${editHandle.trim()}`
        : '@analyst',
      bio: editBio.trim() || DEFAULT_PROFILE.bio,
    };
    setProfile(updated);
    try {
      localStorage.setItem('estd_user_profile', JSON.stringify(updated));
    } catch (err) {}
    setIsEditing(false);
  };

  const handleSelectAvatar = (avatarItem) => {
    const updated = {
      ...profile,
      avatarUrl: avatarItem.dataUrl,
      avatarEmoji: avatarItem.emoji,
      avatarName: avatarItem.label,
    };
    setProfile(updated);
    try {
      localStorage.setItem('estd_user_profile', JSON.stringify(updated));
    } catch (err) {}
    setShowAvatarModal(false);
  };

  return (
    <div className="profile-hub-container">
      {/* ============================================================== */}
      {/* 1. CLEAN USER IDENTITY CARD (Customizable Name, Handle & Bio)   */}
      {/* ============================================================== */}
      <div className="profile-hero-card" style={{ padding: '26px 30px' }}>
        <div className="profile-hero-glow" />

        <div className="profile-hero-content">
          {/* Avatar with Interactive Change Badge */}
          <div className="profile-avatar-wrapper" onClick={() => setShowAvatarModal(true)}>
            <div className="profile-avatar-ring">
              <img
                src={profile.avatarUrl}
                alt={profile.name}
                className="profile-avatar-img"
              />
            </div>
            <button
              type="button"
              className="profile-avatar-edit-badge"
              title="Change Profile Picture"
            >
              <Camera size={13} />
            </button>
          </div>

          {/* User Details & Identity */}
          <div className="profile-identity-col" style={{ flex: 1 }}>
            <div className="profile-name-row">
              <h1 className="profile-name">{profile.name}</h1>
              <span className="profile-verified-badge" title="ESTD Verified Reader">
                <CheckCircle2 size={14} className="profile-verified-icon" />
                <span>Verified Reader</span>
              </span>
              <button
                type="button"
                className="profile-edit-toggle-btn"
                onClick={() => {
                  setEditName(profile.name);
                  setEditHandle(profile.handle);
                  setEditBio(profile.bio);
                  setIsEditing((prev) => !prev);
                }}
              >
                <Edit3 size={13} />
                <span>{isEditing ? 'Cancel Editing' : 'Edit Profile'}</span>
              </button>
            </div>

            <div className="profile-handle-row" style={{ marginBottom: 12 }}>
              <span className="profile-handle">{profile.handle}</span>
              <span className="profile-dot-separator">•</span>
              <span style={{ fontSize: 12, color: '#94a3b8' }}>
                ESTD Personal Intelligence Account
              </span>
            </div>

            {/* Editable Form or Static Bio */}
            {isEditing ? (
              <form onSubmit={handleSaveProfile} className="profile-inline-edit-form" style={{ marginTop: 8 }}>
                <div className="profile-form-row">
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    placeholder="Enter Your Name"
                    className="profile-input"
                    maxLength={40}
                    autoFocus
                  />
                  <input
                    type="text"
                    value={editHandle}
                    onChange={(e) => setEditHandle(e.target.value)}
                    placeholder="@username"
                    className="profile-input"
                    maxLength={30}
                  />
                </div>
                <textarea
                  value={editBio}
                  onChange={(e) => setEditBio(e.target.value)}
                  placeholder="Tell us about yourself and what topics you track..."
                  className="profile-textarea"
                  rows={2}
                  maxLength={180}
                />
                <div className="profile-form-actions">
                  <button type="submit" className="profile-save-btn">
                    Save Profile
                  </button>
                  <button
                    type="button"
                    className="profile-cancel-btn"
                    onClick={() => setIsEditing(false)}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            ) : (
              <p className="profile-bio" style={{ margin: 0, fontSize: 13.5, color: '#cbd5e1', lineHeight: 1.55 }}>
                {profile.bio}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* ============================================================== */}
      {/* 2. REAL STATS GRID (3 Real Cards)                             */}
      {/* ============================================================== */}
      <div
        className="profile-stats-grid"
        style={{
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: 16,
          marginBottom: 28,
        }}
      >
        {/* Card 1: ARTICLES READ (Real Live Tracking) */}
        <div className="profile-stat-card">
          <div className="profile-stat-top">
            <span className="profile-stat-label">ARTICLES READ</span>
            <span className="profile-stat-badge cyan">Real-Time Tracker</span>
          </div>
          <div className="profile-stat-value text-cyan" style={{ color: '#00E5FF' }}>
            {readCount}
          </div>
          <div className="profile-stat-sub">
            {readCount === 0
              ? 'No articles opened yet — start reading to track!'
              : `${readCount} verified stories opened & read`}
          </div>
        </div>

        {/* Card 2: SAVED IN VAULT (Personal Library) */}
        <div className="profile-stat-card">
          <div className="profile-stat-top">
            <span className="profile-stat-label">SAVED IN VAULT</span>
            <span className="profile-stat-badge gold">Deep Research</span>
          </div>
          <div className="profile-stat-value text-gold">{savedStories.length}</div>
          <div className="profile-stat-sub">Bookmarked in Personal Library</div>
        </div>

        {/* Card 3: WATCH LATER QUEUE (Video Playback) */}
        <div className="profile-stat-card">
          <div className="profile-stat-top">
            <span className="profile-stat-label">WATCH LATER QUEUE</span>
            <span className="profile-stat-badge amber">Saved Videos</span>
          </div>
          <div className="profile-stat-value text-amber">{watchLaterStories.length}</div>
          <div className="profile-stat-sub">Queued for Focused Playback</div>
        </div>
      </div>

      {/* ============================================================== */}
      {/* 3. VAULT TABS BAR                                              */}
      {/* ============================================================== */}
      <div className="profile-tabs-bar">
        <button
          type="button"
          className={`profile-tab-btn ${activeTab === 'saved' ? 'active' : ''}`}
          onClick={() => setActiveTab('saved')}
        >
          <Bookmark size={15} />
          <span>Saved Reads</span>
          <span className="profile-tab-count">{savedStories.length}</span>
        </button>

        <button
          type="button"
          className={`profile-tab-btn ${activeTab === 'watchlater' ? 'active' : ''}`}
          onClick={() => setActiveTab('watchlater')}
        >
          <Clock size={15} />
          <span>Watch Later</span>
          <span className="profile-tab-count">{watchLaterStories.length}</span>
        </button>

        <button
          type="button"
          className={`profile-tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          <BookOpen size={15} />
          <span>Reading History</span>
          <span className="profile-tab-count">{readCount}</span>
        </button>

        <button
          type="button"
          className={`profile-tab-btn ${activeTab === 'interests' ? 'active' : ''}`}
          onClick={() => setActiveTab('interests')}
        >
          <Rss size={15} />
          <span>Following Channels</span>
          <span className="profile-tab-count">{followedCategories.length}</span>
        </button>
      </div>

      {/* ============================================================== */}
      {/* TAB 1: SAVED READS (Compact Row Blocks matching Reading History)*/}
      {/* ============================================================== */}
      {activeTab === 'saved' && (
        <div className="profile-tab-panel">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 800, color: '#ffffff', margin: 0 }}>
                Saved Reads & Vault
              </h3>
              <p style={{ fontSize: 12.5, color: '#94a3b8', margin: '2px 0 0 0' }}>
                Your personal library of bookmarked dispatches for deep reference.
              </p>
            </div>
            <span style={{ fontSize: 11.5, padding: '3px 9px', borderRadius: 10, background: 'rgba(0, 229, 255, 0.1)', color: '#00E5FF', fontWeight: 800 }}>
              {savedStories.length} Saved
            </span>
          </div>

          {savedStories.length === 0 ? (
            <div className="profile-empty-vault">
              <div className="profile-empty-icon">
                <Bookmark size={32} />
              </div>
              <h3 className="profile-empty-title">Your Saved Vault is Empty</h3>
              <p className="profile-empty-desc">
                When browsing any news article across ESTD, click the <strong>Bookmark (Save)</strong> icon to archive it here for deep research and offline reference.
              </p>
              <button
                type="button"
                className="profile-empty-btn"
                onClick={() => navigate('/')}
              >
                Browse Wire to Save Articles
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {savedStories.map((story) => (
                <div
                  key={story.id}
                  onClick={() => navigate(`/story/${story.id}`)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 16px',
                    borderRadius: 12,
                    background: '#0D101A',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#00E5FF';
                    e.currentTarget.style.transform = 'translateX(3px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                    e.currentTarget.style.transform = 'none';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        padding: '3px 8px',
                        borderRadius: 6,
                        background: 'rgba(0, 229, 255, 0.15)',
                        color: '#00E5FF',
                        fontSize: 11,
                        fontWeight: 800,
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {story.category || 'News'}
                    </div>

                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div
                        style={{
                          fontSize: 14,
                          fontWeight: 700,
                          color: '#ffffff',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {story.headline || story.title}
                      </div>
                      <div style={{ fontSize: 11.5, color: '#64748b', marginTop: 2 }}>
                        {story.sourceName && `${story.sourceName} • `}
                        {story.subcategory && `${story.subcategory} • `}
                        Bookmarked in Vault
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0, marginLeft: 12 }}>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleSave && onToggleSave(story);
                      }}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '5px 10px',
                        borderRadius: 6,
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid rgba(239, 68, 68, 0.25)',
                        color: '#ef4444',
                        fontSize: 11.5,
                        fontWeight: 700,
                        cursor: 'pointer',
                        transition: 'all 0.15s ease',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
                      }}
                      title="Remove from Saved Reads"
                    >
                      <Trash2 size={12} />
                      <span>Remove</span>
                    </button>
                    <ArrowRight size={15} style={{ color: '#64748b' }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 2: WATCH LATER QUEUE (Compact Row Blocks)                  */}
      {/* ============================================================== */}
      {activeTab === 'watchlater' && (
        <div className="profile-tab-panel">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 800, color: '#ffffff', margin: 0 }}>
                Watch Later Queue
              </h3>
              <p style={{ fontSize: 12.5, color: '#94a3b8', margin: '2px 0 0 0' }}>
                Your saved video reels and dispatches queued for focused playback.
              </p>
            </div>
            <span style={{ fontSize: 11.5, padding: '3px 9px', borderRadius: 10, background: 'rgba(245, 158, 11, 0.1)', color: '#F59E0B', fontWeight: 800 }}>
              {watchLaterStories.length} Queued
            </span>
          </div>

          {watchLaterStories.length === 0 ? (
            <div className="profile-empty-vault">
              <div className="profile-empty-icon">
                <Clock size={32} />
              </div>
              <h3 className="profile-empty-title">Watch Later Queue is Empty</h3>
              <p className="profile-empty-desc">
                Add video stories from the wire to watch later when you have dedicated screen time.
              </p>
              <button
                type="button"
                className="profile-empty-btn"
                onClick={() => navigate('/watch')}
              >
                Explore Video Feed
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {watchLaterStories.map((story) => (
                <div
                  key={story.id}
                  onClick={() => navigate(`/watch/${story.id}`)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 16px',
                    borderRadius: 12,
                    background: '#0D101A',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#F59E0B';
                    e.currentTarget.style.transform = 'translateX(3px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                    e.currentTarget.style.transform = 'none';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        padding: '3px 8px',
                        borderRadius: 6,
                        background: 'rgba(245, 158, 11, 0.15)',
                        color: '#F59E0B',
                        fontSize: 11,
                        fontWeight: 800,
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {story.category || 'News'}
                    </div>

                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div
                        style={{
                          fontSize: 14,
                          fontWeight: 700,
                          color: '#ffffff',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {story.headline || story.title}
                      </div>
                      <div style={{ fontSize: 11.5, color: '#64748b', marginTop: 2 }}>
                        {story.sourceName && `${story.sourceName} • `}
                        {story.subcategory && `${story.subcategory} • `}
                        Video Reel Queued
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0, marginLeft: 12 }}>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/watch/${story.id}`);
                      }}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 5,
                        padding: '5px 10px',
                        borderRadius: 6,
                        background: 'rgba(0, 229, 255, 0.12)',
                        border: '1px solid rgba(0, 229, 255, 0.3)',
                        color: '#00E5FF',
                        fontSize: 11.5,
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      <Play size={11} fill="#00E5FF" />
                      <span>Watch</span>
                    </button>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onToggleWatchLater && onToggleWatchLater(story);
                      }}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4,
                        padding: '5px 10px',
                        borderRadius: 6,
                        background: 'rgba(239, 68, 68, 0.1)',
                        border: '1px solid rgba(239, 68, 68, 0.25)',
                        color: '#ef4444',
                        fontSize: 11.5,
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                      title="Remove from Watch Later"
                    >
                      <Trash2 size={12} />
                      <span>Remove</span>
                    </button>
                    <ArrowRight size={15} style={{ color: '#64748b' }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 3: REAL READING HISTORY (Opened & Read Articles)           */}
      {/* ============================================================== */}
      {activeTab === 'history' && (
        <div className="profile-tab-panel">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              <h3 style={{ fontSize: 16, fontWeight: 800, color: '#ffffff', margin: 0 }}>
                Recent Reading History
              </h3>
              <p style={{ fontSize: 12.5, color: '#94a3b8', margin: '2px 0 0 0' }}>
                Automatically logged whenever you open and read a story across the ESTD wire.
              </p>
            </div>

            {readCount > 0 && (
              <button
                type="button"
                onClick={clearHistory}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '6px 12px',
                  borderRadius: 8,
                  fontSize: 12,
                  fontWeight: 700,
                  color: '#ef4444',
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.25)',
                  cursor: 'pointer',
                }}
              >
                <Trash2 size={13} />
                <span>Clear History</span>
              </button>
            )}
          </div>

          {readCount === 0 ? (
            <div className="profile-empty-vault">
              <div className="profile-empty-icon">
                <BookOpen size={32} />
              </div>
              <h3 className="profile-empty-title">No Reading History Yet</h3>
              <p className="profile-empty-desc">
                Whenever you open a story to read on ESTD, it will automatically be tracked here so you can revisit past reads.
              </p>
              <button
                type="button"
                className="profile-empty-btn"
                onClick={() => navigate('/')}
              >
                Start Reading Stories
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {readArticles.map((article) => (
                <div
                  key={article.id}
                  onClick={() => navigate(`/story/${article.id}`)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 16px',
                    borderRadius: 12,
                    background: '#0D101A',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#00E5FF';
                    e.currentTarget.style.transform = 'translateX(3px)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                    e.currentTarget.style.transform = 'none';
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        padding: '3px 8px',
                        borderRadius: 6,
                        background: 'rgba(0, 229, 255, 0.15)',
                        color: '#00E5FF',
                        fontSize: 11,
                        fontWeight: 800,
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {article.category || 'News'}
                    </div>

                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div
                        style={{
                          fontSize: 14,
                          fontWeight: 700,
                          color: '#ffffff',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {article.title}
                      </div>
                      <div style={{ fontSize: 11.5, color: '#64748b', marginTop: 2 }}>
                        {article.sourceName && `${article.sourceName} • `}
                        {article.subcategory && `${article.subcategory} • `}
                        {article.readAt ? new Date(article.readAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recently read'}
                      </div>
                    </div>
                  </div>

                  <ArrowRight size={15} style={{ color: '#64748b', marginLeft: 12, flexShrink: 0 }} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 4: GEN-Z FOLLOWING CHANNELS & INTELLIGENCE RADAR           */}
      {/* ============================================================== */}
      {activeTab === 'interests' && (
        <div className="profile-tab-panel">
          <div className="profile-radar-card" style={{ padding: '24px 26px', background: '#080A11', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 18 }}>
              <div>
                <h3 className="profile-radar-title" style={{ display: 'flex', alignItems: 'center', gap: 8, margin: 0, fontSize: 18 }}>
                  <Rss size={20} style={{ color: '#00E5FF' }} />
                  <span>My Following Channels</span>
                </h3>
                <p className="profile-radar-sub" style={{ margin: '6px 0 0 0', color: '#94a3b8', fontSize: 13 }}>
                  Select the desks you want to follow. When you click <strong>Following</strong> in the top bar, your wire immediately highlights your followed channels.
                </p>
              </div>

              <button
                type="button"
                onClick={() => navigate('/?feed=following')}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '8px 14px',
                  background: 'rgba(0, 229, 255, 0.12)',
                  border: '1px solid rgba(0, 229, 255, 0.35)',
                  borderRadius: 8,
                  color: '#00E5FF',
                  fontSize: 12.5,
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                }}
              >
                <span>View Following Wire</span>
                <ArrowRight size={14} />
              </button>
            </div>

            {/* Gen-Z Category Channels Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(290px, 1fr))', gap: 14 }}>
              {CATEGORIES.map((cat) => {
                const followed = isFollowing(cat.name);
                const CatIcon = CATEGORY_ICON_MAP[cat.name] || Compass;

                return (
                  <div
                    key={cat.id}
                    style={{
                      padding: '18px 20px',
                      borderRadius: 14,
                      background: followed
                        ? `linear-gradient(145deg, ${cat.color}15, #0D101A 75%)`
                        : '#0D101A',
                      border: followed
                        ? `1px solid ${cat.color}88`
                        : '1px solid rgba(255, 255, 255, 0.08)',
                      boxShadow: followed ? `0 0 20px ${cat.color}20` : 'none',
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      gap: 14,
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 12 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                        <div
                          style={{
                            width: 40,
                            height: 40,
                            borderRadius: 10,
                            background: `${cat.color}20`,
                            border: `1px solid ${cat.color}55`,
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: cat.color,
                            flexShrink: 0,
                          }}
                        >
                          <CatIcon size={20} />
                        </div>
                        <div>
                          <h4 style={{ margin: 0, fontSize: 16, fontWeight: 800, color: '#ffffff' }}>
                            {cat.name}
                          </h4>
                          <span
                            style={{
                              fontSize: 11,
                              color: followed ? cat.color : '#64748b',
                              fontWeight: 700,
                              textTransform: 'uppercase',
                              letterSpacing: '0.04em',
                            }}
                          >
                            {followed ? `● ${cat.name} Following` : 'Not Followed'}
                          </span>
                        </div>
                      </div>

                      {/* Interactive Gen-Z Follow / Following Button */}
                      <button
                        type="button"
                        onClick={() => toggleCategory(cat.name)}
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 6,
                          padding: '7px 13px',
                          borderRadius: 22,
                          fontSize: 12,
                          fontWeight: 800,
                          cursor: 'pointer',
                          transition: 'all 0.15s ease',
                          background: followed ? cat.color : 'rgba(255, 255, 255, 0.06)',
                          color: followed ? '#000000' : '#ffffff',
                          border: followed ? `1px solid ${cat.color}` : '1px solid rgba(255, 255, 255, 0.18)',
                          boxShadow: followed ? `0 0 14px ${cat.color}66` : 'none',
                        }}
                      >
                        {followed ? (
                          <>
                            <Check size={13} strokeWidth={3} />
                            <span>{cat.name} Following</span>
                          </>
                        ) : (
                          <>
                            <Plus size={13} strokeWidth={2.5} />
                            <span>+ Follow {cat.name}</span>
                          </>
                        )}
                      </button>
                    </div>

                    <p style={{ margin: 0, fontSize: 12.5, color: '#94a3b8', lineHeight: 1.5 }}>
                      {cat.description}
                    </p>

                    <div
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        paddingTop: 10,
                        borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                      }}
                    >
                      <span style={{ fontSize: 11, color: '#64748b' }}>Canonical ESTD Desk</span>
                      <button
                        type="button"
                        onClick={() => navigate(`/category/${cat.slug}`)}
                        style={{
                          background: 'none',
                          border: 'none',
                          color: cat.color,
                          fontSize: 12,
                          fontWeight: 700,
                          cursor: 'pointer',
                          padding: 0,
                          display: 'flex',
                          alignItems: 'center',
                          gap: 4,
                        }}
                      >
                        <span>Open {cat.name} Desk</span>
                        <ArrowRight size={12} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* System Diagnostics Trigger */}
          {onOpenDiagnostics && (
            <div className="profile-diagnostics-card" style={{ marginTop: 20 }}>
              <div>
                <h4 className="profile-diag-title">ESTD System Diagnostics</h4>
                <p className="profile-diag-sub">
                  Inspect backend PostgreSQL events, multi-angle scraping status, and pipeline execution logs.
                </p>
              </div>
              <button
                type="button"
                className="profile-diag-btn"
                onClick={onOpenDiagnostics}
              >
                Open Diagnostics
              </button>
            </div>
          )}
        </div>
      )}

      {/* ============================================================== */}
      {/* SNAP & MEMOJI AVATAR SELECTOR MODAL POPUP                      */}
      {/* ============================================================== */}
      {showAvatarModal && (
        <div
          className="profile-modal-backdrop"
          onClick={() => setShowAvatarModal(false)}
        >
          <div
            className="profile-modal-card"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="profile-modal-heading"
          >
            <div className="profile-modal-header">
              <div className="profile-modal-title-wrap">
                <span className="profile-modal-badge">
                  <Sparkles size={11} /> Snap &amp; Memoji Personas
                </span>
                <h3 id="profile-modal-heading" className="profile-modal-title">
                  Choose Your Snap Avatar
                </h3>
                <p className="profile-modal-sub">
                  Pick a stylish 3D emoji persona for your ESTD intelligence profile:
                </p>
              </div>
              <button
                type="button"
                className="profile-modal-close-icon-btn"
                onClick={() => setShowAvatarModal(false)}
                aria-label="Close avatar modal"
              >
                <X size={18} />
              </button>
            </div>

            <div className="profile-modal-grid">
              {SNAP_EMOJI_AVATARS.map((av) => {
                const isSelected =
                  profile.avatarUrl === av.dataUrl ||
                  profile.avatarEmoji === av.emoji;
                return (
                  <button
                    key={av.id}
                    type="button"
                    className={`profile-modal-avatar-item ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleSelectAvatar(av)}
                    title={av.label}
                  >
                    <div
                      className="profile-modal-emoji-circle"
                      style={{ background: av.gradient }}
                    >
                      <span className="profile-modal-emoji-char">{av.emoji}</span>
                      {isSelected && (
                        <div className="profile-modal-selected-check">
                          <Check size={11} strokeWidth={3.5} />
                        </div>
                      )}
                    </div>
                    <span className="profile-modal-avatar-label">{av.label}</span>
                  </button>
                );
              })}
            </div>

            <div className="profile-modal-footer">
              <div className="profile-modal-footer-hint">
                <Sparkles size={13} style={{ color: '#00e5ff', flexShrink: 0 }} />
                <span>Selected persona syncs across your ESTD profile &amp; wire feed</span>
              </div>
              <button
                type="button"
                className="profile-modal-done-btn"
                onClick={() => setShowAvatarModal(false)}
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
