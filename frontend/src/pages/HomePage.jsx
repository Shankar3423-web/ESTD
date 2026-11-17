import React, { useState, useEffect, useMemo } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import StoryCard from '../components/story/StoryCard';
import VideoModalPlayer from '../components/story/VideoModalPlayer';
import FeaturedNewsCarousel from '../components/story/FeaturedNewsCarousel';
import FlashBitesBar from '../components/story/FlashBitesBar';
import EstdpodCarouselShelf from '../components/podcast/EstdpodCarouselShelf';
import WeeklyRadarDrop from '../components/story/WeeklyRadarDrop';
import CategoryQuickRow from '../components/story/CategoryQuickRow';
import FollowingStreamView from '../components/following/FollowingStreamView';
import InshortsDeskReader from '../components/story/InshortsDeskReader';
import { LayoutGrid, Zap, FileText } from 'lucide-react';
import EmptyState from '../components/common/EmptyState';
import ErrorState from '../components/common/ErrorState';
import SkeletonCard from '../components/story/SkeletonCard';
import { fetchStories } from '../api/estdApi';
import { CATEGORIES } from '../constants/taxonomy';
import { useFollowedCategories } from '../utils/followedCategories';

export default function HomePage({
  savedStories = [],
  onToggleSave,
  watchLaterStories = [],
  onToggleWatchLater,
  onListen,
}) {
  const navigate = useNavigate();
  const outletCtx = useOutletContext() || {};
  const feedMode = outletCtx.feedMode || 'latest';

  // Real-time app-wide followed categories
  const { followedCategories } = useFollowedCategories();

  // Active filter inside the Following mode ('All' or specific followed desk like 'Tech')
  const [activeFollowingCategory, setActiveFollowingCategory] = useState('All');

  const [selectedCategory, setSelectedCategory] = useState('All');
  
  // Instant load: initialize from localStorage cache if available so first paint is 0ms
  const [stories, setStories] = useState(() => {
    try {
      const cached = localStorage.getItem('estd_feed_cache');
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length > 0) {
          // Verify cached stories has at least 4 unique categories so old 3-category cache is refreshed
          const uniqueCats = new Set(parsed.map((s) => s.category));
          if (uniqueCats.size >= 4) return parsed;
        }
      }
    } catch {}
    return [];
  });
  
  const [loading, setLoading] = useState(() => {
    try {
      const cached = localStorage.getItem('estd_feed_cache');
      if (cached) {
        const parsed = JSON.parse(cached);
        if (Array.isArray(parsed) && parsed.length > 0) {
          const uniqueCats = new Set(parsed.map((s) => s.category));
          if (uniqueCats.size >= 4) return false;
        }
      }
    } catch {}
    return true;
  });
  const [error, setError] = useState(null);

  // View Mode State: 'bento' (default magazine) vs 'inshorts' (card-by-card quick read)
  const [viewMode, setViewMode] = useState(() => {
    try {
      return localStorage.getItem('estd_preferred_view_mode') || 'bento';
    } catch {
      return 'bento';
    }
  });

  const handleSetViewMode = (mode) => {
    setViewMode(mode);
    try {
      localStorage.setItem('estd_preferred_view_mode', mode);
    } catch (e) {
      console.warn('Could not persist view mode:', e);
    }
  };

  // Video Lightbox Modal State
  const [modalStory, setModalStory] = useState(null);
  const [modalVideoIndex, setModalVideoIndex] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // If activeFollowingCategory is no longer followed, reset to 'All'
  useEffect(() => {
    if (
      activeFollowingCategory !== 'All' &&
      !followedCategories.includes(activeFollowingCategory)
    ) {
      setActiveFollowingCategory('All');
    }
  }, [followedCategories, activeFollowingCategory]);

  useEffect(() => {
    let isMounted = true;
    async function loadFeed() {
      // Only set loading true if we don't already have cached stories (prevents blank screen flashes)
      if (stories.length === 0) {
        setLoading(true);
      }
      setError(null);
      try {
        if (selectedCategory === 'All') {
          // Ultra-fast single query with in-memory caching across all 5 categories
          const allStories = await fetchStories({ limit: 150 });

          // Interleave category stories 1-by-1 in pure memory (0.01ms) for balanced diversity
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

          const finalStories = mixed.length > 0 ? mixed : allStories;
          if (isMounted) {
            setStories(finalStories);
            try {
              localStorage.setItem('estd_feed_cache', JSON.stringify(finalStories.slice(0, 100)));
            } catch {}
          }
        } else {
          // Specific category filtered feed
          const data = await fetchStories({
            category: selectedCategory,
            limit: 50,
          });
          if (isMounted) {
            setStories(data);
          }
        }
      } catch (err) {
        if (isMounted && stories.length === 0) setError(err.message || 'Failed to load feed.');
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadFeed();

    return () => {
      isMounted = false;
    };
  }, [selectedCategory]);

  const handleOpenVideoModal = (story, videoIndex = 0) => {
    setModalStory(story);
    setModalVideoIndex(videoIndex);
    setIsModalOpen(true);
  };

  return (
    <div className="home-page-container">
      {/* Loading Skeleton Grid */}
      {loading && (
        <div className="home-stories-grid">
          {Array.from({ length: 9 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <ErrorState
          title="Could Not Connect to ESTD Backend"
          error={error}
          onRetry={() => setSelectedCategory((c) => c)}
        />
      )}

      {/* ============================================================== */}
      {/* MODE 1: EXCLUSIVE FOLLOWING STREAM VIEW                        */}
      {/* Renders a completely unique, high-engagement layout & cards     */}
      {/* ============================================================== */}
      {!loading && !error && feedMode === 'following' && (
        <FollowingStreamView
          stories={stories}
          followedCategories={followedCategories}
          activeCategory={activeFollowingCategory}
          onSelectCategory={setActiveFollowingCategory}
          savedStories={savedStories}
          onToggleSave={onToggleSave}
          watchLaterStories={watchLaterStories}
          onToggleWatchLater={onToggleWatchLater}
          onWatchVideo={handleOpenVideoModal}
          onListen={onListen}
        />
      )}

      {/* ============================================================== */}
      {/* MODE 2: LATEST HOME WIRE FEED                                   */}
      {/* ============================================================== */}
      {!loading && !error && feedMode === 'latest' && stories.length > 0 && (
        <>
          {/* View Mode Switcher: Bento Magazine vs Inshorts Card Reader */}
          <div className="home-view-toggle-bar">
            <div className="home-view-toggle-group">
              <button
                type="button"
                className={`home-view-toggle-btn ${viewMode === 'bento' ? 'active' : ''}`}
                onClick={() => handleSetViewMode('bento')}
                title="Bento Magazine Wire Layout"
              >
                <LayoutGrid size={14} />
                <span>Bento Magazine</span>
              </button>
              <button
                type="button"
                className={`home-view-toggle-btn ${viewMode === 'inshorts' ? 'active' : ''}`}
                onClick={() => handleSetViewMode('inshorts')}
                title="Inshorts-style Card-by-Card Quick Read"
              >
                <Zap size={14} />
                <span>Inshorts Quick-Read</span>
                <span className="home-view-new-badge">NEW</span>
              </button>
            </div>

            <div className="home-view-caption">
              {viewMode === 'inshorts' ? (
                <span>⚡ Card-by-card story contract with keyboard navigation (↓/↑, J/K, S)</span>
              ) : (
                <span>📰 Multi-category news desks, 60s flash bites & radar calendar</span>
              )}
            </div>
          </div>

          {viewMode === 'inshorts' ? (
            <InshortsDeskReader
              stories={stories}
              savedStories={savedStories}
              onToggleSave={onToggleSave}
              watchLaterStories={watchLaterStories}
              onToggleWatchLater={onToggleWatchLater}
              onExitToBento={() => handleSetViewMode('bento')}
            />
          ) : (
            <>
          {/* Section 1 & 2: Hero Landing Viewport (Featured Carousel + 60s Flash Bites) */}
          <div className="home-hero-landing">
            {/* Section 1: Hero Spotlight Carousel (one latest story per category) */}
            <FeaturedNewsCarousel
              stories={stories}
              savedStories={savedStories}
              onToggleSave={onToggleSave}
            />

            {/* Section 2: 60-Second Flash Bites (Gen-Z Story Rings & Smart Brevity) */}
            <FlashBitesBar stories={stories} />
          </div>

          {/* Section 2.3: ESTDPOD Originals — Guest Showcase Carousel */}
          <EstdpodCarouselShelf />

          {/* Section 2.5: The Daily Pack — Text Intelligence (The Sacred Story Contract) */}
          <section className="home-daily-pack-section">
            <div className="daily-pack-header">
              <div className="daily-pack-title-group">
                <span className="daily-pack-badge">
                  <FileText size={14} />
                  <span>ESTD • TOP STORIES</span>
                </span>
                <h3 className="daily-pack-title">Today's Top Stories</h3>
                <p className="daily-pack-subtitle">
                  Curated headlines and briefings from verified sources worldwide.
                </p>
              </div>

              <button
                type="button"
                className="daily-pack-switch-inshorts"
                onClick={() => navigate('/inshorts')}
                title="Switch to full-screen Inshorts card swiper"
              >
                <Zap size={14} color="#B8FF3B" />
                <span>Swipe Cards Mode (Inshorts) →</span>
              </button>
            </div>

            <div className="daily-pack-cards-grid">
              {stories.slice(0, 6).map((story) => (
                <StoryCard
                  key={story.id}
                  story={story}
                  isSaved={savedStories.some((s) => s.id === story.id)}
                  onToggleSave={onToggleSave}
                  watchLaterStories={watchLaterStories}
                  onToggleWatchLater={onToggleWatchLater}
                  isWatchLater={watchLaterStories.some((s) => String(s.id) === String(story.id))}
                  onWatchVideo={() => handleOpenVideoModal(story)}
                />
              ))}
            </div>
          </section>

          {/* Section 3: Category Pulse Rows */}
          {selectedCategory === 'All' ? (
            <div className="home-pulse-hubs-container">
              {/* Tech Pulse */}
              <CategoryQuickRow
                categoryName="Tech"
                titleOverride="Tech Pulse"
                subtitle="AI breakthroughs, enterprise cloud, consumer hardware & semiconductors"
                stories={stories}
                savedStories={savedStories}
                onToggleSave={onToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={onToggleWatchLater}
              />

              {/* Entertainment Pulse */}
              <CategoryQuickRow
                categoryName="Entertainment"
                titleOverride="Entertainment Pulse"
                subtitle="Cinema, streaming, digital storytelling & creator culture"
                stories={stories}
                savedStories={savedStories}
                onToggleSave={onToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={onToggleWatchLater}
              />

              {/* Sports Pulse */}
              <CategoryQuickRow
                categoryName="Sports"
                titleOverride="Sports Pulse"
                subtitle="Cricket, football, badminton, motorsport & Olympic athletics"
                stories={stories}
                savedStories={savedStories}
                onToggleSave={onToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={onToggleWatchLater}
              />

              {/* Education Pulse */}
              <CategoryQuickRow
                categoryName="Developments"
                subcategoryName="Education"
                titleOverride="Education Pulse"
                subtitle="Curriculum reforms, university admissions, exam scrutiny & NEP policy updates"
                accentColor="#38BDF8"
                seeAllLink="/category/developments/education-and-learning-policy"
                stories={stories}
                savedStories={savedStories}
                onToggleSave={onToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={onToggleWatchLater}
              />

              {/* Business & Markets Pulse */}
              <CategoryQuickRow
                categoryName="Business & Finance"
                titleOverride="Business & Markets Pulse"
                subtitle="Financial markets, venture capital, earnings & corporate strategy"
                stories={stories}
                savedStories={savedStories}
                onToggleSave={onToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={onToggleWatchLater}
              />

              {/* Developments & Science Pulse */}
              <CategoryQuickRow
                categoryName="Developments"
                excludeSubcategory="Education"
                titleOverride="Developments & Science Pulse"
                subtitle="Public policy, health sciences, clean energy transitions & geopolitics"
                stories={stories}
                savedStories={savedStories}
                onToggleSave={onToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={onToggleWatchLater}
              />
            </div>
          ) : (
            <CategoryQuickRow
              categoryName={selectedCategory}
              titleOverride={`${selectedCategory === 'Business & Finance' ? 'Business' : selectedCategory} Pulse`}
              stories={stories}
              savedStories={savedStories}
              onToggleSave={onToggleSave}
              watchLaterStories={watchLaterStories}
              onToggleWatchLater={onToggleWatchLater}
            />
          )}

          {/* Section 4: The Radar — What's Dropping This Week (Gen-Z Forward Calendar) */}
          {selectedCategory === 'All' && <WeeklyRadarDrop />}
            </>
          )}
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
