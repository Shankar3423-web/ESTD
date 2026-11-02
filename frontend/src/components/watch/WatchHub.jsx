import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Sparkles,
  Zap,
  Film,
  Trophy,
  Cpu,
  TrendingUp,
  Compass,
  Radio,
  Flame,
  Play,
  RotateCcw,
  CheckCircle2,
  Tv,
  Layers,
} from 'lucide-react';
import WatchFilterBar from './WatchFilterBar';
import WatchVideoCard from './WatchVideoCard';
import ErrorState from '../common/ErrorState';
import { fetchStories } from '../../api/estdApi';
import { CATEGORIES, getCategoryMeta, SUBCATEGORIES_BY_CATEGORY } from '../../constants/taxonomy';
import { matchCategory, interleaveStoriesByCategory } from '../../utils/watchUtils';
export { matchCategory, interleaveStoriesByCategory } from '../../utils/watchUtils';

// Canonical category key map
const CANONICAL_CATEGORY_KEYS = {
  tech: 'Tech',
  entertainment: 'Entertainment',
  'business-finance': 'Business & Finance',
  'business & finance': 'Business & Finance',
  developments: 'Developments',
  sports: 'Sports',
};



/**
 * WatchHub: YouTube-Fidelity News Video Discovery Destination for ESTD.
 */
export default function WatchHub({
  savedStories = [],
  onToggleSave,
  watchLaterStories = [],
  onToggleWatchLater,
}) {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [allStories, setAllStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Active top navigation category (initialized from URL query ?category=...)
  const urlCategory = searchParams.get('category') || 'all';
  const [selectedCategory, setSelectedCategory] = useState(urlCategory);

  // Active subcategory filter (for when inside a specific category view)
  const [selectedSubcategory, setSelectedSubcategory] = useState('all');

  // Keep state in sync with URL searchParams (e.g. back/forward button navigation)
  useEffect(() => {
    const cat = searchParams.get('category') || 'all';
    setSelectedCategory(cat);
  }, [searchParams]);

  // Load all stories across all categories (limit=150 returns all 117 articles)
  useEffect(() => {
    let isMounted = true;
    async function loadHubStories() {
      setLoading(true);
      setError(null);
      try {
        const list = await fetchStories({ limit: 150 });
        if (isMounted) {
          setAllStories(list || []);
        }
      } catch (err) {
        if (isMounted) setError(err.message || 'Failed to load video catalog.');
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    loadHubStories();
    return () => {
      isMounted = false;
    };
  }, []);

  // When switching top category, reset active subcategory, update URL, and scroll to top
  const handleSelectCategory = (catId) => {
    setSelectedCategory(catId);
    setSelectedSubcategory('all');
    if (catId === 'all') {
      setSearchParams({});
    } else {
      setSearchParams({ category: catId });
    }
    window.scrollTo({ top: 0, behavior: 'instant' });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
    const mainEl = document.getElementById('main-content');
    if (mainEl) mainEl.scrollTop = 0;
  };

  // Reset scroll to top whenever selected category changes
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
    const mainEl = document.getElementById('main-content');
    if (mainEl) mainEl.scrollTop = 0;
  }, [selectedCategory]);

  // Canonical name for current category
  const canonicalCategoryName = useMemo(() => {
    if (selectedCategory === 'all' || selectedCategory === 'reels') return null;
    return CANONICAL_CATEGORY_KEYS[selectedCategory.toLowerCase()] || selectedCategory;
  }, [selectedCategory]);

  // Active category meta for header
  const activeCategoryMeta = useMemo(() => {
    if (!canonicalCategoryName) return null;
    return (
      getCategoryMeta(canonicalCategoryName) || {
        name: canonicalCategoryName,
        color: '#00E5FF',
        description: 'Verified video journalism and multi-angle analysis.',
        icon: 'Cpu',
      }
    );
  }, [canonicalCategoryName]);

  const accentColor = activeCategoryMeta?.color || '#00E5FF';

  // Balanced round-robin interleaving for the 'All' feed
  const mixedAllStories = useMemo(() => {
    return interleaveStoriesByCategory(allStories);
  }, [allStories]);

  // All stories belonging to the active category
  const categoryAllStories = useMemo(() => {
    if (!allStories || allStories.length === 0) return [];
    if (selectedCategory === 'all' || selectedCategory === 'reels') return mixedAllStories;

    return allStories.filter((s) => matchCategory(s.category, selectedCategory));
  }, [allStories, mixedAllStories, selectedCategory]);

  // Subcategories list for the active category
  const availableSubcategories = useMemo(() => {
    if (!canonicalCategoryName) return [];

    // Official canonical list from taxonomy
    const officialList = SUBCATEGORIES_BY_CATEGORY[canonicalCategoryName] || [];

    // Group actual story counts per subcategory
    const counts = {};
    for (const s of categoryAllStories) {
      const sub = s.subcategory || 'General';
      counts[sub] = (counts[sub] || 0) + 1;
    }

    return officialList.map((subName) => ({
      name: subName,
      count: counts[subName] || 0,
    }));
  }, [canonicalCategoryName, categoryAllStories]);

  // Stories filtered by both category AND subcategory
  const displayedCategoryStories = useMemo(() => {
    if (selectedSubcategory === 'all') return categoryAllStories;
    return categoryAllStories.filter(
      (s) => (s.subcategory || '').toLowerCase().trim() === selectedSubcategory.toLowerCase().trim()
    );
  }, [categoryAllStories, selectedSubcategory]);

  const handlePlayStory = (story) => {
    if (story?.id) {
      navigate(`/watch/${story.id}`);
    }
  };

  const getCategoryIconComponent = (code) => {
    switch (code) {
      case 'TECH':
        return Cpu;
      case 'ENT':
        return Film;
      case 'SPORTS':
        return Trophy;
      case 'BIZ_FIN':
        return TrendingUp;
      case 'DEV':
        return Compass;
      default:
        return Sparkles;
    }
  };

  const CategoryIcon = getCategoryIconComponent(activeCategoryMeta?.code);

  if (loading) {
    return (
      <div className="watch-hub-page-container">
        <div className="watch-hub-skeleton">
          <div className="watch-skeleton-filter-bar" />
          <div className="watch-skeleton-hero" />
          <div className="watch-skeleton-cards-grid" />
        </div>
      </div>
    );
  }

  if (error || allStories.length === 0) {
    return (
      <div className="watch-hub-page-container">
        <ErrorState
          title="Watch Feed Unavailable"
          error={error || 'No news videos could be loaded.'}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }

  return (
    <div className="watch-hub-page-container">
      {/* 1. YouTube-Style Sticky Category Navigation Chips */}
      <WatchFilterBar
        selectedCategory={selectedCategory}
        onSelectCategory={handleSelectCategory}
        totalVideosCount={allStories.length}
      />

      {/* 2. CASE: User clicked a Category (Tech, Developments, Sports, Entertainment, Business & Finance) */}
      {selectedCategory !== 'all' && (
        <section className="watch-category-channel-view">
          {/* Refined Category Channel Header Banner */}
          <div
            className="watch-category-channel-banner"
            style={{
              borderColor: `${accentColor}35`,
              background: `linear-gradient(135deg, ${accentColor}15 0%, rgba(15, 20, 30, 0.95) 100%)`,
            }}
          >
            <div className="watch-channel-banner-left">
              <div className="watch-channel-banner-top-row">
                <span
                  className="watch-channel-banner-pill"
                  style={{
                    background: `${accentColor}25`,
                    borderColor: accentColor,
                    color: accentColor,
                  }}
                >
                  <CategoryIcon size={12} />
                  <span>{canonicalCategoryName.toUpperCase()} DESK</span>
                </span>
                <span className="watch-channel-verified-pill">
                  <CheckCircle2 size={12} style={{ color: accentColor }} />
                  <span>Verified Video Wire</span>
                </span>
              </div>

              <h2 className="watch-channel-banner-title">
                {canonicalCategoryName} Video Intelligence
              </h2>
              <p className="watch-channel-banner-desc">
                {activeCategoryMeta?.description ||
                  'Curated video coverage with multi-angle verification.'}
              </p>
            </div>

            <div className="watch-channel-banner-stats">
              <span className="watch-channel-stats-count">{categoryAllStories.length}</span>
              <span className="watch-channel-stats-label">Videos in Category</span>
            </div>
          </div>

          {/* Subcategory Filter Pills Sub-Bar */}
          {availableSubcategories.length > 0 && (
            <div className="watch-subcat-filter-track" aria-label="Subcategories">
              {/* All in Category Chip */}
              <button
                type="button"
                className={`watch-subcat-chip ${selectedSubcategory === 'all' ? 'active' : ''}`}
                onClick={() => setSelectedSubcategory('all')}
                style={{ '--subcat-accent': accentColor }}
              >
                <span>All {canonicalCategoryName}</span>
                <span className="watch-subcat-chip-count">{categoryAllStories.length}</span>
              </button>

              {/* Subcategories */}
              {availableSubcategories.map((sub) => {
                const isActive = selectedSubcategory.toLowerCase() === sub.name.toLowerCase();
                return (
                  <button
                    key={sub.name}
                    type="button"
                    className={`watch-subcat-chip ${isActive ? 'active' : ''}`}
                    onClick={() => setSelectedSubcategory(sub.name)}
                    style={{ '--subcat-accent': accentColor }}
                  >
                    <span>{sub.name}</span>
                    <span className="watch-subcat-chip-count">{sub.count}</span>
                  </button>
                );
              })}
            </div>
          )}

          {/* Active Subcategory Heading & Count */}
          <div className="watch-category-results-header">
            <span className="watch-results-label">
              Showing {displayedCategoryStories.length} video{displayedCategoryStories.length === 1 ? '' : 's'}
              {selectedSubcategory !== 'all' ? ` in ${selectedSubcategory}` : ` across all ${canonicalCategoryName} subcategories`}
            </span>
            {selectedSubcategory !== 'all' && (
              <button
                type="button"
                className="watch-reset-subcat-btn"
                onClick={() => setSelectedSubcategory('all')}
              >
                <RotateCcw size={12} />
                <span>Show All {canonicalCategoryName}</span>
              </button>
            )}
          </div>

          {/* Clean YouTube Video Grid for this Category / Subcategory */}
          {displayedCategoryStories.length > 0 ? (
            <div className="watch-youtube-videos-grid">
              {displayedCategoryStories.map((story) => {
                const video = story.videoRail?.[0] || {};
                const isSaved = savedStories.some((s) => String(s.id) === String(story.id));
                const isWatchLater = watchLaterStories.some((s) => String(s.id) === String(story.id));
                return (
                  <WatchVideoCard
                    key={story.id}
                    video={video}
                    story={story}
                    onPlay={() => handlePlayStory(story)}
                    onToggleSave={onToggleSave}
                    isSaved={isSaved}
                    isWatchLater={isWatchLater}
                    onToggleWatchLater={onToggleWatchLater}
                  />
                );
              })}
            </div>
          ) : (
            <div className="watch-empty-subcat-state">
              <p>No video reports found under {selectedSubcategory}.</p>
              <button
                type="button"
                className="watch-hero-secondary-btn"
                onClick={() => setSelectedSubcategory('all')}
              >
                View all {canonicalCategoryName} videos ({categoryAllStories.length})
              </button>
            </div>
          )}
        </section>
      )}

      {/* 3. CASE: User is on 'All' -> Continuous Clean YouTube Video Grid */}
      {selectedCategory === 'all' && (
        <div className="watch-main-youtube-feed">
          {/* Section Header */}
          <div className="watch-feed-section-header">
            <div className="watch-feed-title-wrap">
              <Tv size={18} style={{ color: '#00E5FF' }} />
              <h3 className="watch-feed-heading">Latest News Videos</h3>
              <span className="watch-feed-badge">TOP PICKS</span>
            </div>
            <span className="watch-feed-subtitle">
              Verified news broadcasts, press releases, and investigative reports
            </span>
          </div>

          <div className="watch-youtube-videos-grid">
            {mixedAllStories.map((story) => {
              const video = story.videoRail?.[0] || {};
              const isSaved = savedStories.some((s) => String(s.id) === String(story.id));
              const isWatchLater = watchLaterStories.some((s) => String(s.id) === String(story.id));
              return (
                <WatchVideoCard
                  key={story.id}
                  video={video}
                  story={story}
                  onPlay={() => handlePlayStory(story)}
                  onToggleSave={onToggleSave}
                  isSaved={isSaved}
                  isWatchLater={isWatchLater}
                  onToggleWatchLater={onToggleWatchLater}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
