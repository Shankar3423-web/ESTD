import React from 'react';
import { useParams } from 'react-router-dom';
import WatchHub from '../components/watch/WatchHub';
import WatchTheatreView from '../components/watch/WatchTheatreView';

/**
 * WatchPage: Master Coordinator for the ESTD Video Experience.
 * - Route `/watch`: Renders the high-octane WatchHub (Hero Spotlight, 60s Reels, Perspectives, Category Shelves)
 * - Route `/watch/:storyId`: Renders the YouTube-Fidelity WatchTheatreView (16:9 player, 5-Angle Switcher, Up Next)
 */
export default function WatchPage({
  savedStories = [],
  onToggleSave,
  watchLaterStories = [],
  onToggleWatchLater,
}) {
  const { storyId } = useParams();

  if (storyId) {
    return (
      <WatchTheatreView
        storyId={storyId}
        savedStories={savedStories}
        onToggleSave={onToggleSave}
        watchLaterStories={watchLaterStories}
        onToggleWatchLater={onToggleWatchLater}
      />
    );
  }

  return (
    <WatchHub
      savedStories={savedStories}
      onToggleSave={onToggleSave}
      watchLaterStories={watchLaterStories}
      onToggleWatchLater={onToggleWatchLater}
    />
  );
}
