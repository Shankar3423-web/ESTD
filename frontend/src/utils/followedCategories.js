import { useState, useEffect, useCallback } from 'react';

const STORAGE_KEY = 'estd_user_followed_desks';
export const DEFAULT_FOLLOWED_CATEGORIES = [];

/**
 * Returns the currently followed category names from localStorage.
 * By default, NO categories are followed until the user explicitly clicks follow.
 */
export function getFollowedCategories() {
  try {
    // Clear any legacy mock defaults from previous versions
    if (typeof window !== 'undefined' && localStorage.getItem('estd_preferred_categories')) {
      localStorage.removeItem('estd_preferred_categories');
    }
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch (e) {
    return [];
  }
}

/**
 * Toggles a category in the followed list and broadcasts the change across the app.
 * Only adds or removes when explicitly triggered by a user click.
 */
export function toggleFollowCategory(categoryName) {
  if (!categoryName) return getFollowedCategories();

  const current = getFollowedCategories();
  const exists = current.includes(categoryName);
  const next = exists
    ? current.filter((c) => c !== categoryName)
    : [...current, categoryName];

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch (e) {}

  window.dispatchEvent(
    new CustomEvent('estd_followed_categories_changed', { detail: next })
  );

  return next;
}

/**
 * Checks if a specific category name is followed.
 */
export function isCategoryFollowed(categoryName) {
  return getFollowedCategories().includes(categoryName);
}

/**
 * React hook to read and manipulate followed categories reactively.
 */
export function useFollowedCategories() {
  const [followedCategories, setFollowedCategories] = useState(getFollowedCategories);

  useEffect(() => {
    const handleUpdate = () => {
      setFollowedCategories(getFollowedCategories());
    };

    window.addEventListener('estd_followed_categories_changed', handleUpdate);
    window.addEventListener('storage', handleUpdate);

    return () => {
      window.removeEventListener('estd_followed_categories_changed', handleUpdate);
      window.removeEventListener('storage', handleUpdate);
    };
  }, []);

  const toggleCategory = useCallback((catName) => {
    const updated = toggleFollowCategory(catName);
    setFollowedCategories(updated);
  }, []);

  const isFollowing = useCallback(
    (catName) => followedCategories.includes(catName),
    [followedCategories]
  );

  return {
    followedCategories,
    toggleCategory,
    isFollowing,
    count: followedCategories.length,
  };
}
