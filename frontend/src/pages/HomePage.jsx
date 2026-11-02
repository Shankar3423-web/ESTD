import React, { useState, useEffect, useMemo } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import StoryCard from '../components/story/StoryCard';
import VideoModalPlayer from '../components/story/VideoModalPlayer';
import FeaturedNewsCarousel from '../components/story/FeaturedNewsCarousel';
import FlashBitesBar from '../components/story/FlashBitesBar';
import WeeklyRadarDrop from '../components/story/WeeklyRadarDrop';
import CategoryQuickRow from '../components/story/CategoryQuickRow';
import FollowingStreamView from '../components/following/FollowingStreamView';
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
  const [stories, setStories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
      setLoading(true);
      setError(null);
      try {
        if (selectedCategory === 'All') {
          // Curate a balanced, interleaved mix of news across all 5 canonical categories
          const categories = [
            'Tech',
            'Entertainment',
            'Sports',
            'Developments',
            'Business & Finance',
          ];
          const categoryResults = await Promise.all(
            categories.map((cat) =>
              fetchStories({ category: cat, limit: 25 }).catch(() => [])
            )
          );

          // Interleave category stories 1-by-1 for a vibrant, diverse feed
          const mixed = [];
          const maxCount = Math.max(...categoryResults.map((r) => r.length), 0);
          for (let i = 0; i < maxCount; i++) {
            for (let c = 0; c < categoryResults.length; c++) {
              if (i < categoryResults[c].length) {
                mixed.push(categoryResults[c][i]);
              }
            }
          }

          if (isMounted) {
            setStories(mixed);
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
        if (isMounted) setError(err.message || 'Failed to load feed.');
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
