import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Search, X, Activity, User, SlidersHorizontal, ArrowLeft } from 'lucide-react';
import { useFollowedCategories } from '../../utils/followedCategories';

export default function TopBar({
  feedMode = 'latest',
  onFeedModeChange,
  onOpenDiagnostics,
  systemOverview,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const navigate = useNavigate();
  const location = useLocation();
  const { count: followedCount } = useFollowedCategories();

  // Active user avatar from profile
  const userAvatarUrl = (() => {
    try {
      const stored = localStorage.getItem('estd_user_profile');
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed.avatarUrl && !parsed.avatarUrl.includes('unsplash.com')) {
          return parsed.avatarUrl;
        }
      }
    } catch {}
    return null;
  })();

  const isStoryPage = location.pathname.startsWith('/story/');

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  const handleClear = () => {
    setSearchTerm('');
  };

  const handleFeedToggle = (mode) => {
    if (onFeedModeChange) {
      onFeedModeChange(mode);
    }
    if (location.pathname !== '/') {
      navigate(`/?feed=${mode}`);
    } else {
      // Update query param without full reload
      navigate(`/?feed=${mode}`, { replace: true });
    }
  };

  return (
    <header className="top-bar">
      {/* Search Console & Inline Back to Feed Button */}
      <div className="topbar-left-group">
        {isStoryPage && (
          <button
            type="button"
            className="topbar-back-btn"
            onClick={() => navigate('/')}
            title="Return to news feed"
          >
            <ArrowLeft size={14} />
            <span>Back to Feed</span>
          </button>
        )}

        {/* Compact Ask ESTD Search Input */}
        <form className="search-container compact-search" onSubmit={handleSearchSubmit}>
          <div className="search-input-wrapper">
            <Search size={15} className="search-icon" />
            <input
              type="text"
              className="search-input"
              placeholder="Ask ESTD or search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            {searchTerm && (
              <button
                type="button"
                className="search-clear-btn"
                onClick={handleClear}
                aria-label="Clear search input"
              >
                <X size={13} />
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Actions and Feed controls */}
      <div className="top-bar-actions">
        {/* Latest / Following Feed Selector */}
        <div className="feed-toggle" role="tablist">
          <button
            className={`feed-toggle-btn ${feedMode === 'latest' ? 'active' : ''}`}
            onClick={() => handleFeedToggle('latest')}
            role="tab"
            aria-selected={feedMode === 'latest'}
          >
            Latest
          </button>
          <button
            className={`feed-toggle-btn ${feedMode === 'following' ? 'active' : ''}`}
            onClick={() => handleFeedToggle('following')}
            role="tab"
            aria-selected={feedMode === 'following'}
            title="View news from your followed intelligence desks"
          >
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <span>Following</span>
              {followedCount > 0 && (
                <span
                  style={{
                    fontSize: 10,
                    padding: '1px 6px',
                    borderRadius: 10,
                    background: feedMode === 'following' ? '#00E5FF' : 'rgba(255, 255, 255, 0.16)',
                    color: feedMode === 'following' ? '#000000' : '#ffffff',
                    fontWeight: 800,
                  }}
                >
                  {followedCount}
                </span>
              )}
            </span>
          </button>
        </div>

        {/* User profile avatar */}
        <button
          className="btn-icon"
          onClick={() => navigate('/you')}
          title="User Preferences & Profile"
          aria-label="Profile and preferences"
          style={{
            padding: userAvatarUrl ? '2px' : undefined,
            overflow: 'hidden',
          }}
        >
          {userAvatarUrl ? (
            <img
              src={userAvatarUrl}
              alt="Profile avatar"
              style={{
                width: 26,
                height: 26,
                borderRadius: '50%',
                display: 'block',
              }}
            />
          ) : (
            <User size={18} />
          )}
        </button>
      </div>
    </header>
  );
}
