import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Sparkles, Check, Plus } from 'lucide-react';
import StoryCard from '../components/story/StoryCard';
import CategoryHeroCarousel from '../components/story/CategoryHeroCarousel';
import SubcategoryCommandDeck from '../components/story/SubcategoryCommandDeck';
import VideoModalPlayer from '../components/story/VideoModalPlayer';
import EmptyState from '../components/common/EmptyState';
import ErrorState from '../components/common/ErrorState';
import SkeletonCard from '../components/story/SkeletonCard';
import { fetchStories, fetchSubcategories } from '../api/estdApi';
import {
  CATEGORIES,
  CATEGORY_SLUG_MAP,
  SUBCATEGORIES_BY_CATEGORY,
  slugify,
} from '../constants/taxonomy';
import { useFollowedCategories } from '../utils/followedCategories';

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

  const [subcategories, setSubcategories] = useState(
    SUBCATEGORIES_BY_CATEGORY[canonicalName] || []
  );
  const [selectedSubcategory, setSelectedSubcategory] = useState('All');
  const [categoryStories, setCategoryStories] = useState([]);
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Video Lightbox Modal State
  const [modalStory, setModalStory] = useState(null);
  const [modalVideoIndex, setModalVideoIndex] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Load canonical subcategories dynamically from backend
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

  // Fetch all category stories
  useEffect(() => {
    let isMounted = true;
    async function loadCategoryFeed() {
      setLoading(true);
      setError(null);
      try {
        const allCategoryData = await fetchStories({
          category: canonicalName,
          limit: 100,
        });

        if (isMounted) {
          setCategoryStories(allCategoryData || []);

          if (selectedSubcategory === 'All') {
            setStories(allCategoryData || []);
          } else {
            const subNorm = selectedSubcategory.toLowerCase().trim();
            // 1. Exact subcategory match
            const exactFiltered = (allCategoryData || []).filter(
              (s) => (s.subcategory || '').toLowerCase().trim() === subNorm
            );

            if (exactFiltered.length > 0) {
              setStories(exactFiltered);
            } else {
              // 2. Semantic topic keywords fallback across category wire
              const subKeywords = subNorm
                .replace(/&/g, ' ')
                .split(/\s+/)
                .filter((w) => w.length > 2 && !['and', 'for', 'the', 'with'].includes(w));

              const topicFiltered = (allCategoryData || []).filter((s) => {
                const text = `${s.headline || ''} ${s.brief || ''} ${s.subcategory || ''} ${s.content || ''}`.toLowerCase();
                return subKeywords.some((kw) => text.includes(kw));
              });

              if (topicFiltered.length > 0) {
                setStories(topicFiltered);
              } else {
                const directSubData = await fetchStories({
                  category: canonicalName,
                  subcategory: selectedSubcategory,
                  limit: 50,
                });
                if (isMounted) {
                  setStories(directSubData && directSubData.length > 0 ? directSubData : (allCategoryData || []).slice(0, 6));
                }
              }
            }
          }
        }
      } catch (err) {
        if (isMounted) setError(err.message || 'Failed to load category feed.');
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadCategoryFeed();
    return () => {
      isMounted = false;
    };
  }, [canonicalName, selectedSubcategory]);

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
  // Subsequent news cards (follow hero)
  const subsequentStories = stories.length > 5 ? stories.slice(5) : stories;

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
              {subsequentStories.map((story) => (
                <StoryCard
                  key={story.id}
                  story={story}
                  isSaved={savedStories.some((s) => String(s.id) === String(story.id))}
                  onToggleSave={onToggleSave}
                  watchLaterStories={watchLaterStories}
                  isWatchLater={watchLaterStories.some((s) => String(s.id) === String(story.id))}
                  onToggleWatchLater={onToggleWatchLater}
                  onListen={onListen}
                  accentColor={accentColor}
                />
              ))}
            </div>
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
