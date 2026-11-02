import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppShell from './components/layout/AppShell';
import HomePage from './pages/HomePage';
import CategoryPage from './pages/CategoryPage';
import StoryObject from './components/story/StoryObject';
import WatchPage from './pages/WatchPage';
import LivePage from './pages/LivePage';
import SavedPage from './pages/SavedPage';
import YouPage from './pages/YouPage';
import SearchPage from './pages/SearchPage';
import EmptyState from './components/common/EmptyState';

export default function App() {
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
