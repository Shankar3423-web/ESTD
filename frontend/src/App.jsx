import React, { useState, useEffect, lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import { prefetchAllCategories } from './api/estdApi';

// Route-level code splitting: pages load on-demand instead of bloating initial JS bundle
const HomePage = lazy(() => import('./pages/HomePage'));
const InshortsPage = lazy(() => import('./pages/InshortsPage'));
const CategoryPage = lazy(() => import('./pages/CategoryPage'));
// Pre-warm StoryObject chunk immediately so opening any article has 0 network bundle download delay
const storyObjectPromise = import('./components/story/StoryObject');
const StoryObject = lazy(() => storyObjectPromise);
const WatchPage = lazy(() => import('./pages/WatchPage'));
const LivePage = lazy(() => import('./pages/LivePage'));
const SavedPage = lazy(() => import('./pages/SavedPage'));
const YouPage = lazy(() => import('./pages/YouPage'));
const SearchPage = lazy(() => import('./pages/SearchPage'));
const EmptyState = lazy(() => import('./components/common/EmptyState'));

function PageLoaderFallback() {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '45vh',
        color: '#64748B',
        fontSize: '12px',
        fontWeight: 600,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        gap: '12px',
      }}
    >
      <div
        style={{
          width: 20,
          height: 20,
          border: '2px solid rgba(0, 229, 255, 0.2)',
          borderTopColor: '#00E5FF',
          borderRadius: '50%',
          animation: 'spin 0.6s linear infinite',
        }}
      />
      <span>Loading ESTD Desk...</span>
    </div>
  );
}

export default function App() {
  // Pre-warm category feeds in the background during idle time so all tabs open instantaneously
  useEffect(() => {
    const timer = setTimeout(() => {
      prefetchAllCategories();
    }, 1200);
    return () => clearTimeout(timer);
  }, []);

  // Locally persisted saved stories
  const [savedStories, setSavedStories] = useState(() => {
    try {
      const stored = localStorage.getItem('estd_saved_stories');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('estd_saved_stories', JSON.stringify(savedStories));
    } catch (e) {
      console.warn('Could not persist saved stories:', e);
    }
  }, [savedStories]);

  // Locally persisted Watch Later stories
  const [watchLaterStories, setWatchLaterStories] = useState(() => {
    try {
      const stored = localStorage.getItem('estd_watch_later');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem('estd_watch_later', JSON.stringify(watchLaterStories));
    } catch (e) {
      console.warn('Could not persist watch later stories:', e);
    }
  }, [watchLaterStories]);

  const handleToggleWatchLater = (story) => {
    if (!story) return;
    setWatchLaterStories((prev) => {
      const exists = prev.some((s) => String(s.id) === String(story.id));
      const next = exists
        ? prev.filter((s) => String(s.id) !== String(story.id))
        : [story, ...prev];
      try {
        localStorage.setItem('estd_watch_later', JSON.stringify(next));
      } catch (e) {
        console.warn('Could not persist watch later stories:', e);
      }
      return next;
    });
  };

  const handleToggleSave = (story) => {
    if (!story) return;
    setSavedStories((prev) => {
      const exists = prev.some((s) => String(s.id) === String(story.id));
      const next = exists
        ? prev.filter((s) => String(s.id) !== String(story.id))
        : [story, ...prev];
      try {
        localStorage.setItem('estd_saved_stories', JSON.stringify(next));
      } catch (e) {
        console.warn('Could not persist saved stories:', e);
      }
      return next;
    });
  };

  const handleClearAllSaved = () => {
    setSavedStories([]);
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route
          element={
            <AppShell
              savedStories={savedStories}
              onToggleSave={handleToggleSave}
              watchLaterStories={watchLaterStories}
              onToggleWatchLater={handleToggleWatchLater}
            />
          }
        >
          {/* Home */}
          <Route
            path="/"
            element={
              <HomePage
                savedStories={savedStories}
                onToggleSave={handleToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={handleToggleWatchLater}
              />
            }
          />

          {/* Inshorts / Swipe Cards Dedicated Routes */}
          <Route
            path="/inshorts"
            element={
              <InshortsPage
                savedStories={savedStories}
                onToggleSave={handleToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={handleToggleWatchLater}
              />
            }
          />
          <Route path="/swipe" element={<Navigate to="/inshorts" replace />} />
          <Route path="/cards" element={<Navigate to="/inshorts" replace />} />

          {/* Canonical Category & Subcategory Pages */}
          <Route
            path="/category/:categorySlug"
            element={
              <CategoryPage
                savedStories={savedStories}
                onToggleSave={handleToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={handleToggleWatchLater}
              />
            }
          />
          <Route
            path="/category/:categorySlug/:subcategorySlug"
            element={
              <CategoryPage
                savedStories={savedStories}
                onToggleSave={handleToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={handleToggleWatchLater}
              />
            }
          />

          {/* Direct Category & Subcategory Route Aliases (e.g. /sports, /sports/cricket) */}
          <Route
            path="/sports"
            element={<Navigate to="/category/sports" replace />}
          />
          <Route
            path="/sports/:subcategorySlug"
            element={<CategoryPage savedStories={savedStories} onToggleSave={handleToggleSave} watchLaterStories={watchLaterStories} onToggleWatchLater={handleToggleWatchLater} />}
          />
          <Route
            path="/entertainment"
            element={<Navigate to="/category/entertainment" replace />}
          />
          <Route
            path="/entertainment/:subcategorySlug"
            element={<CategoryPage savedStories={savedStories} onToggleSave={handleToggleSave} watchLaterStories={watchLaterStories} onToggleWatchLater={handleToggleWatchLater} />}
          />
          <Route
            path="/tech"
            element={<Navigate to="/category/tech" replace />}
          />
          <Route
            path="/tech/:subcategorySlug"
            element={<CategoryPage savedStories={savedStories} onToggleSave={handleToggleSave} watchLaterStories={watchLaterStories} onToggleWatchLater={handleToggleWatchLater} />}
          />
          <Route
            path="/developments"
            element={<Navigate to="/category/developments" replace />}
          />
          <Route
            path="/developments/:subcategorySlug"
            element={<CategoryPage savedStories={savedStories} onToggleSave={handleToggleSave} watchLaterStories={watchLaterStories} onToggleWatchLater={handleToggleWatchLater} />}
          />
          <Route
            path="/business-finance"
            element={<Navigate to="/category/business-finance" replace />}
          />
          <Route
            path="/business-finance/:subcategorySlug"
            element={<CategoryPage savedStories={savedStories} onToggleSave={handleToggleSave} watchLaterStories={watchLaterStories} onToggleWatchLater={handleToggleWatchLater} />}
          />

          {/* The Story Object Route */}
          <Route
            path="/story/:storyId"
            element={
              <StoryObject
                savedStories={savedStories}
                onToggleSave={handleToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={handleToggleWatchLater}
              />
            }
          />

          {/* Watch: Video-first story explorer (Supports root /watch and /watch/:storyId) */}
          <Route
            path="/watch"
            element={
              <WatchPage
                savedStories={savedStories}
                onToggleSave={handleToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={handleToggleWatchLater}
              />
            }
          />
          <Route
            path="/watch/:storyId"
            element={
              <WatchPage
                savedStories={savedStories}
                onToggleSave={handleToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={handleToggleWatchLater}
              />
            }
          />

          {/* Podcasts and ESTDPOD direct routes */}
          <Route path="/podcasts" element={<Navigate to="/watch?category=podcasts#estdpod" replace />} />
          <Route path="/estdpod" element={<Navigate to="/watch?category=podcasts#estdpod" replace />} />

          {/* Hubs Redirect */}
          <Route path="/hub" element={<Navigate to="/" replace />} />
          <Route path="/hubs" element={<Navigate to="/" replace />} />
          <Route path="/explore" element={<Navigate to="/" replace />} />
          <Route path="/hub/*" element={<Navigate to="/" replace />} />

          {/* Live Section */}
          <Route
            path="/live"
            element={
              <LivePage
                savedStories={savedStories}
                onToggleSave={handleToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={handleToggleWatchLater}
              />
            }
          />

          {/* Saved Section */}
          <Route
            path="/saved"
            element={
              <SavedPage
                savedStories={savedStories}
                onToggleSave={handleToggleSave}
                onClearAll={handleClearAllSaved}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={handleToggleWatchLater}
              />
            }
          />

          {/* You / Profile Section */}
          <Route
            path="/you"
            element={
              <YouPage
                savedStories={savedStories}
                onToggleSave={handleToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={handleToggleWatchLater}
              />
            }
          />
          <Route
            path="/profile"
            element={<Navigate to="/you" replace />}
          />

          {/* Search / Ask ESTD */}
          <Route
            path="/search"
            element={
              <SearchPage
                savedStories={savedStories}
                onToggleSave={handleToggleSave}
                watchLaterStories={watchLaterStories}
                onToggleWatchLater={handleToggleWatchLater}
              />
            }
          />

          {/* 404 Fallback */}
          <Route
            path="*"
            element={
              <div style={{ padding: '60px 0' }}>
                <EmptyState
                  title="Page Not Found"
                  description="The destination you requested does not exist in the ESTD navigation structure."
                  actionLabel="Back to Home"
                  onAction={() => window.location.href = '/'}
                />
              </div>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
