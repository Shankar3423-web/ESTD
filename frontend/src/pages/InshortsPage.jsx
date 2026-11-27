import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import InshortsDeskReader from '../components/story/InshortsDeskReader';
import ErrorState from '../components/common/ErrorState';
import { fetchStories, getCachedStories } from '../api/estdApi';
import { CATEGORIES } from '../constants/taxonomy';
import { Zap, LayoutGrid, Sparkles, ArrowRight } from 'lucide-react';

/**
 * InshortsPage: Dedicated Desktop & Mobile Route for the Swipable Inshorts News Experience.
 * Accessible via `/inshorts` and `/swipe`.
 *
 * Implements:
 * - Category filter tabs (All, Tech, Entertainment, Business & Finance, Developments, Sports)
 * - Full-screen desktop card reader with keyboard & mouse-wheel navigation
 * - Continuous reading loop with automatic next-vertical progression (zero blank screens)
 * - Spoken headline (<= 12 words) + 50-70 word brief + unified meta row + 4 beats
 * - Integrated 60s AI audio voiceover
 * - Multi-angle video perspectives modal
 */
export default function InshortsPage({
  savedStories = [],
  onToggleSave,
  watchLaterStories = [],
  onToggleWatchLater,
}) {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const initialCategory = searchParams.get('category') || 'All';

  const [selectedCategory, setSelectedCategory] = useState(initialCategory);
  const [stories, setStories] = useState(() =>
    getCachedStories({ category: initialCategory === 'All' ? undefined : initialCategory, limit: 60 })
  );
  const [loading, setLoading] = useState(() => stories.length === 0);
  const [error, setError] = useState(null);

  // Canonical sequence of verticals for seamless auto-advance
  const categoryOrder = ['All', 'Tech', 'Entertainment', 'Business & Finance', 'Developments', 'Sports'];
  const currentCatIdx = categoryOrder.indexOf(selectedCategory);
  const nextCategory =
    currentCatIdx !== -1 && currentCatIdx < categoryOrder.length - 1
      ? categoryOrder[currentCatIdx + 1]
      : categoryOrder[0];

  useEffect(() => {
    let isMounted = true;
    const cached = getCachedStories({
      category: selectedCategory === 'All' ? undefined : selectedCategory,
      limit: 60,
    });
    if (cached.length > 0) {
      setStories(cached);
      setLoading(false);
    } else {
      setLoading(true);
    }

    async function loadStories() {
      setError(null);
      try {
        if (selectedCategory === 'All') {
          const allStories = await fetchStories({ limit: 150 });
          const byCat = {};
          for (const s of allStories) {
            const cat = s.category || 'General';
            if (!byCat[cat]) byCat[cat] = [];
            byCat[cat].push(s);
          }
          const categories = Object.keys(byCat);
          const mixed = [];
          const maxCount = Math.max(...categories.map((c) => byCat[c].length), 0);
          for (let i = 0; i < maxCount; i++) {
            for (const cat of categories) {
              if (i < byCat[cat].length) {
                mixed.push(byCat[cat][i]);
              }
            }
          }
          if (isMounted) setStories(mixed.length > 0 ? mixed.slice(0, 60) : allStories.slice(0, 60));
        } else {
          const data = await fetchStories({ category: selectedCategory, limit: 30 });
          if (isMounted) setStories(data);
        }
      } catch (err) {
        if (isMounted && cached.length === 0) setError(err.message || 'Failed to load Inshorts stories.');
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadStories();

    return () => {
      isMounted = false;
    };
  }, [selectedCategory]);

  const handleCategoryChange = (catName) => {
    setSelectedCategory(catName);
    if (catName === 'All') {
      searchParams.delete('category');
    } else {
      searchParams.set('category', catName);
    }
    setSearchParams(searchParams);
  };

  const handleNextCategory = () => {
    handleCategoryChange(nextCategory);
  };

  return (
    <div className="inshorts-page-wrapper">
      {/* Top Controls Header */}
      <div className="inshorts-page-header">
        <div className="inshorts-page-title-row">
          <div className="inshorts-badge-group">
            <span className="inshorts-badge-pill">
              <Zap size={14} />
              <span>INSHORTS QUICK-READ</span>
            </span>
            <span className="inshorts-keyboard-hint">
              Use <strong>↓ / ↑</strong> or <strong>J / K</strong> to swipe stories • <strong>Space</strong> for audio • <strong>Enter</strong> for full story
            </span>
          </div>

          <button
            type="button"
            className="inshorts-switch-bento-btn"
            onClick={() => navigate('/')}
            title="Switch to Bento Magazine Wire"
          >
            <LayoutGrid size={14} />
            <span>Switch to Bento Magazine</span>
          </button>
        </div>

        {/* Category Pills Bar */}
        <div className="inshorts-cat-filters">
          <button
            type="button"
            className={`inshorts-cat-filter-btn ${selectedCategory === 'All' ? 'active' : ''}`}
            onClick={() => handleCategoryChange('All')}
          >
            All Verticals
          </button>
          {CATEGORIES.map((cat) => (
            <button
              key={cat.code}
              type="button"
              className={`inshorts-cat-filter-btn ${selectedCategory === cat.name ? 'active' : ''}`}
              style={{
                '--filter-accent': cat.color,
              }}
              onClick={() => handleCategoryChange(cat.name)}
            >
              <span className="cat-filter-dot" style={{ backgroundColor: cat.color }} />
              <span>{cat.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Loading Shimmer Skeleton (Never Blank) */}
      {loading && (
        <div className="inshorts-skeleton-wrap">
          <div className="inshorts-desk-tracker skeleton-shimmer" style={{ height: 46, borderRadius: 14, marginBottom: 16 }} />
          <div className="inshorts-skeleton-card skeleton-shimmer" style={{ height: 480, borderRadius: 22 }} />
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <ErrorState
          title="Could Not Load Inshorts Stories"
          error={error}
          onRetry={() => setSelectedCategory((c) => c)}
        />
      )}

      {/* Empty State Fallback (Never Blank) */}
      {!loading && !error && stories.length === 0 && (
        <div className="inshorts-desk-container inshorts-end-container">
          <div className="inshorts-end-card">
            <div className="inshorts-end-badge">
              <Sparkles size={28} />
            </div>
            <span className="inshorts-end-subtitle">NO STORIES QUEUED</span>
            <h2 className="inshorts-end-title">No Dispatches in {selectedCategory}</h2>
            <p className="inshorts-end-description">
              All live reporting for {selectedCategory} has been updated. Switch to All Verticals to browse all real-time dispatches.
            </p>
            <div className="inshorts-end-actions">
              <button
                type="button"
                className="inshorts-btn inshorts-btn-primary"
                onClick={() => handleCategoryChange('All')}
              >
                <span>Switch to All Verticals</span>
                <ArrowRight size={15} />
              </button>
              <button
                type="button"
                className="inshorts-btn inshorts-btn-secondary"
                onClick={() => navigate('/')}
              >
                <LayoutGrid size={15} />
                <span>Go to Bento Home</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* The Inshorts Desktop Reader */}
      {!loading && !error && stories.length > 0 && (
        <InshortsDeskReader
          stories={stories}
          savedStories={savedStories}
          onToggleSave={onToggleSave}
          watchLaterStories={watchLaterStories}
          onToggleWatchLater={onToggleWatchLater}
          onExitToBento={() => navigate('/')}
          currentCategory={selectedCategory}
          nextCategory={nextCategory}
          onNextCategory={handleNextCategory}
        />
      )}
    </div>
  );
}
