import { useState, useEffect } from 'react';

const STORAGE_KEY = 'estd_read_articles';

/**
 * Retrieves the list of read article records from localStorage.
 */
export function getReadArticles() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (e) {
    return [];
  }
}

/**
 * Tracks an article as read by the user.
 */
export function trackArticleRead(story) {
  if (!story || !story.id) return;

  const id = String(story.id);
  const current = getReadArticles();

  // Remove existing entry if present so we can move it to the top
  const filtered = current.filter((item) => String(item.id) !== id);

  const newEntry = {
    id: story.id,
    title: story.headline || story.title || 'Verified Dispatch',
    category: story.category || 'News',
    subcategory: story.subcategory || '',
    sourceName: story.sourceName || story.source_name || '',
    imageUrl: story.imageUrl || story.image_url || '',
    readAt: Date.now(),
  };

  const updated = [newEntry, ...filtered].slice(0, 200); // Keep last 200

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  } catch (e) {}

  window.dispatchEvent(new Event('estd_read_articles_changed'));
  return updated;
}

/**
 * Clears the reading history.
 */
export function clearReadingHistory() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (e) {}
  window.dispatchEvent(new Event('estd_read_articles_changed'));
}

/**
 * React hook to access and track reading history in real time.
 */
export function useReadingHistory() {
  const [readArticles, setReadArticles] = useState(getReadArticles);

  useEffect(() => {
    function handleUpdate() {
      setReadArticles(getReadArticles());
    }

    window.addEventListener('estd_read_articles_changed', handleUpdate);
    window.addEventListener('storage', handleUpdate);

    return () => {
      window.removeEventListener('estd_read_articles_changed', handleUpdate);
      window.removeEventListener('storage', handleUpdate);
    };
  }, []);

  return {
    readArticles,
    readCount: readArticles.length,
    trackRead: trackArticleRead,
    clearHistory: clearReadingHistory,
  };
}

