import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Sparkles, Check, Plus } from 'lucide-react';
import StoryCard from '../components/story/StoryCard';
import CategoryHeroCarousel from '../components/story/CategoryHeroCarousel';
import SubcategoryCommandDeck from '../components/story/SubcategoryCommandDeck';
import VideoModalPlayer from '../components/story/VideoModalPlayer';
import EmptyState from '../components/common/EmptyState';
import ErrorState from '../components/common/ErrorState';
import SkeletonCard from '../components/story/SkeletonCard';
import { fetchStories, fetchSubcategories, getCachedStories } from '../api/estdApi';
import {
  CATEGORIES,
  CATEGORY_SLUG_MAP,
  SUBCATEGORIES_BY_CATEGORY,
  slugify,
} from '../constants/taxonomy';
import { useFollowedCategories } from '../utils/followedCategories';

/**
 * High-performance, zero-latency subcategory in-memory filter
 */
function filterStoriesBySubcategory(list = [], subName = 'All') {
  if (!subName || subName === 'All') return list;
  const subNorm = subName.toLowerCase().trim();

  // 1. Exact canonical subcategory match
  const exact = list.filter(
    (s) => (s.subcategory || '').toLowerCase().trim() === subNorm
  );
  if (exact.length > 0) return exact;

  // 2. Keyword fallback across headline, brief, subcategory, content
  const subKeywords = subNorm
    .replace(/&/g, ' ')
    .split(/\s+/)
    .filter((w) => w.length > 2 && !['and', 'for', 'the', 'with'].includes(w));

  const keywordMatched = list.filter((s) => {
    const text = `${s.headline || ''} ${s.brief || ''} ${s.subcategory || ''} ${s.content || ''}`.toLowerCase();
    return subKeywords.some((kw) => text.includes(kw));
  });

  return keywordMatched.length > 0 ? keywordMatched : list;
}

export default function CategoryPage({
  savedStories = [],
  onToggleSave,
  watchLaterStories = [],
  onToggleWatchLater,
  onListen,
}) {
  const { categorySlug, subcategorySlug } = useParams();
  const navigate = useNavigate();
  const { toggleCategory, isFollowing } = useFollowedCategories();

  // Resolve canonical category from slug
  const normalizedCatSlug = categorySlug?.toLowerCase();
  const categoryMeta =
    CATEGORY_SLUG_MAP[normalizedCatSlug] ||
    CATEGORIES.find((c) => slugify(c.name) === normalizedCatSlug) ||
    CATEGORIES.find((c) => c.slug === normalizedCatSlug) ||
    CATEGORIES[0];

  const canonicalName = categoryMeta.name;
  const accentColor = categoryMeta.color;
  const glowColor = categoryMeta.glow || `${accentColor}33`;

  // Instant synchronous cache resolution: 0ms initial render without blank screen
  const initialCategoryStories = getCachedStories({ category: canonicalName });
  const [subcategories, setSubcategories] = useState(
    SUBCATEGORIES_BY_CATEGORY[canonicalName] || []
  );
  const [selectedSubcategory, setSelectedSubcategory] = useState('All');
  const [categoryStories, setCategoryStories] = useState(initialCategoryStories);
  const [stories, setStories] = useState(() =>
    filterStoriesBySubcategory(initialCategoryStories, 'All')
  );
  const [loading, setLoading] = useState(initialCategoryStories.length === 0);
  const [error, setError] = useState(null);

  // Video Lightbox Modal State
  const [modalStory, setModalStory] = useState(null);
  const [modalVideoIndex, setModalVideoIndex] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Incremental rendering batch size so large categories don't dump 90+ cards into DOM at once
  const [visibleCount, setVisibleCount] = useState(15);
  useEffect(() => {
    setVisibleCount(15);
  }, [canonicalName, selectedSubcategory]);

  const savedIdSet = useMemo(
    () => new Set(savedStories.map((s) => String(s.id))),
    [savedStories]
  );
  const watchLaterIdSet = useMemo(
    () => new Set(watchLaterStories.map((s) => String(s.id))),
    [watchLaterStories]
  );

  // Load canonical subcategories dynamically (with in-memory memoization)
  useEffect(() => {
    let isMounted = true;
    async function loadSubs() {
      try {
        const subs = await fetchSubcategories(canonicalName);
        if (isMounted && subs.length > 0) {
          setSubcategories(subs.map((s) => s.name));
        }
      } catch (err) {
        console.warn('Using local fallback for subcategories:', err);
      }
    }
    loadSubs();
    return () => {
      isMounted = false;
    };
  }, [canonicalName]);

  // Sync subcategorySlug param to state
  useEffect(() => {
    if (subcategorySlug) {
      const match = subcategories.find(
        (s) => slugify(s) === subcategorySlug.toLowerCase()
      );
      if (match) {
        setSelectedSubcategory(match);
      } else {
        setSelectedSubcategory('All');
      }
    } else {
      setSelectedSubcategory('All');
    }
  }, [subcategorySlug, subcategories]);

  // Zero-latency in-memory subcategory filtering (0ms, no network delay)
  useEffect(() => {
    setStories(filterStoriesBySubcategory(categoryStories, selectedSubcategory));
  }, [selectedSubcategory, categoryStories]);

  // Fetch category stories with Stale-While-Revalidate: render cached instantly, revalidate silently
  useEffect(() => {
    let isMounted = true;

    // Instantly show cached category stories if available (no blank screen, no skeleton flash)
    const cached = getCachedStories({ category: canonicalName });
    if (cached.length > 0) {
      setCategoryStories(cached);
      setStories(filterStoriesBySubcategory(cached, selectedSubcategory));
      setLoading(false);
    } else {
      setLoading(true);
    }

    async function loadCategoryFeed() {
      setError(null);
      try {
        const allCategoryData = await fetchStories({
          category: canonicalName,
          limit: 100,
        });

        if (isMounted && allCategoryData && allCategoryData.length > 0) {
          setCategoryStories(allCategoryData);
          setStories(filterStoriesBySubcategory(allCategoryData, selectedSubcategory));
        }
      } catch (err) {
        if (isMounted && (!cached || cached.length === 0)) {
          setError(err.message || 'Failed to load category feed.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadCategoryFeed();
    return () => {
      isMounted = false;
    };
  }, [canonicalName]);

  const handleSelectSubcategory = (sub) => {
    setSelectedSubcategory(sub);
    const basePath = `/category/${categoryMeta.slug}`;
    if (sub === 'All') {
      navigate(basePath);
    } else {
      navigate(`${basePath}/${slugify(sub)}`);
    }
  };

  const handleOpenVideoModal = (story, videoIndex = 0) => {
    setModalStory(story);
    setModalVideoIndex(videoIndex);
    setIsModalOpen(true);
  };

  // Top 4 to 5 stories for Hero Showcase
  const heroStories = stories.slice(0, 5);
  // Subsequent news cards (follow hero), sliced progressively for fast mount & smooth scrolling
  const subsequentStories = stories.length > 5 ? stories.slice(5) : stories;
  const visibleSubsequentStories = subsequentStories.slice(0, visibleCount);
  const hasMoreStories = subsequentStories.length > visibleCount;

  return (
    <div
      className="category-page-container"
      style={{
        paddingBottom: 80,
        '--cat-accent': accentColor,
        '--cat-glow': glowColor,
      }}
    >
      {/* CATEGORY HEADER WITH ACCENT GLOW, METADATA & QUICK FOLLOW */}
      <header className="category-header-wrap">
        <div className="category-title-row" style={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span
              className="category-glow-dot"
              style={{
                background: accentColor,
                boxShadow: `0 0 20px ${accentColor}`,
              }}
            />
            <h1 className="category-main-title" style={{ margin: 0 }}>
              {canonicalName}
            </h1>
            <span
              className="category-count-badge"
              style={{
                background: `${accentColor}18`,
                color: accentColor,
                border: `1px solid ${accentColor}44`,
              }}
            >
              {categoryStories.length} Verified Stories
            </span>
          </div>

          {/* Interactive Category Follow / Following Button */}
          <button
            type="button"
            onClick={() => toggleCategory(canonicalName)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '7px 15px',
              borderRadius: 22,
              fontSize: 12.5,
              fontWeight: 800,
              cursor: 'pointer',
              marginLeft: 'auto',
              transition: 'all 0.15s ease',
              background: isFollowing(canonicalName) ? accentColor : 'rgba(255, 255, 255, 0.08)',
              color: isFollowing(canonicalName) ? '#000000' : '#ffffff',
              border: isFollowing(canonicalName) ? `1px solid ${accentColor}` : '1px solid rgba(255, 255, 255, 0.2)',
              boxShadow: isFollowing(canonicalName) ? `0 0 16px ${accentColor}66` : 'none',
            }}
          >
            {isFollowing(canonicalName) ? (
              <>
                <Check size={14} strokeWidth={3} />
                <span>{canonicalName} Following</span>
              </>
            ) : (
              <>
                <Plus size={14} strokeWidth={2.5} />
                <span>+ Follow {canonicalName}</span>
              </>
            )}
          </button>
        </div>

        <p className="category-description">
          {categoryMeta.description}
        </p>
      </header>

      {/* Loading Skeleton State */}
      {loading && (
        <div className="category-loading-grid">
          <div className="skeleton-hero-box" />
          <div className="category-stories-grid category-squircle-grid">
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <ErrorState
          title={`Error Loading ${canonicalName}`}
          error={error}
          onRetry={() => setSelectedSubcategory((s) => s)}
        />
      )}

      {/* Empty State */}
      {!loading && !error && stories.length === 0 && (
        <EmptyState
          title={`No Stories in ${selectedSubcategory === 'All' ? canonicalName : selectedSubcategory}`}
          description={`No dispatches available under this filter. Try selecting 'All' or a different subcategory.`}
          actionLabel="Show All"
          onAction={() => handleSelectSubcategory('All')}
        />
      )}

      {/* Main Content Area */}
      {!loading && !error && stories.length > 0 && (
        <>
          {/* Top 5 Hero Story Carousel Showcase */}
          {selectedSubcategory === 'All' && heroStories.length > 0 && (
            <CategoryHeroCarousel
              stories={heroStories}
              accentColor={accentColor}
              categoryName={canonicalName}
              onOpenVideoModal={handleOpenVideoModal}
              savedStories={savedStories}
              onToggleSave={onToggleSave}
            />
          )}

          {/* Subcategory Command Deck (Grid layout with Active States) */}
          <SubcategoryCommandDeck
            subcategories={subcategories}
            selectedSubcategory={selectedSubcategory}
            onSelectSubcategory={handleSelectSubcategory}
            stories={categoryStories}
            categoryName={canonicalName}
            accentColor={accentColor}
            glowColor={glowColor}
          />

          {/* Subsequent News Stories Grid */}
          <section className="category-subsequent-section">
            <div className="category-section-label-row">
              <span className="section-label-title">
                {selectedSubcategory === 'All'
                  ? `More in ${canonicalName}`
                  : `Dispatches in ${selectedSubcategory}`}
              </span>
              <span className="section-label-count">
                {subsequentStories.length} Articles
              </span>
            </div>

            <div className="category-stories-grid category-squircle-grid">
              {visibleSubsequentStories.map((story) => (
                <StoryCard
                  key={story.id}
                  story={story}
                  isSaved={savedIdSet.has(String(story.id))}
                  onToggleSave={onToggleSave}
                  watchLaterStories={watchLaterStories}
                  isWatchLater={watchLaterIdSet.has(String(story.id))}
                  onToggleWatchLater={onToggleWatchLater}
                  onListen={onListen}
                  accentColor={accentColor}
                />
              ))}
            </div>

            {hasMoreStories && (
              <div style={{ display: 'flex', justifyContent: 'center', marginTop: 28 }}>
                <button
                  type="button"
                  onClick={() => setVisibleCount((c) => c + 15)}
                  style={{
                    padding: '10px 24px',
                    borderRadius: 999,
                    background: `${accentColor}18`,
                    border: `1px solid ${accentColor}55`,
                    color: accentColor,
                    fontSize: 13,
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  Load More Stories ({subsequentStories.length - visibleCount} remaining)
                </button>
              </div>
            )}
          </section>
        </>
      )}

      {/* Video Lightbox Player Modal */}
      <VideoModalPlayer
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        story={modalStory}
        initialVideoIndex={modalVideoIndex}
      />
    </div>
  );
}
