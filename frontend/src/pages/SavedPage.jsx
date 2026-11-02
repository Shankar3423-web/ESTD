import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bookmark, Sparkles, Trash2, ArrowRight } from 'lucide-react';
import StoryCard from '../components/story/StoryCard';
import VideoModalPlayer from '../components/story/VideoModalPlayer';
import EmptyState from '../components/common/EmptyState';

export default function SavedPage({
  savedStories = [],
  onToggleSave,
  onClearAll,
  onListen,
  watchLaterStories = [],
  onToggleWatchLater,
}) {
  const navigate = useNavigate();
  const [modalStory, setModalStory] = useState(null);
  const [modalVideoIndex, setModalVideoIndex] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <div style={{ maxWidth: 1280, margin: '0 auto', paddingBottom: 80 }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '24px 0 20px',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          marginBottom: 28,
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Bookmark size={24} style={{ color: '#FFB020' }} />
            <h1 style={{ fontSize: 30, fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em' }}>
              Saved Stories ({savedStories.length})
            </h1>
          </div>
          <p style={{ fontSize: 13.5, color: '#94a3b8', marginTop: 4 }}>
            Your curated reading list of fact-grounded briefs, video perspectives, and source reports.
          </p>
        </div>

        {savedStories.length > 0 && (
          <button
            onClick={onClearAll}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 6,
              padding: '8px 16px',
              borderRadius: 8,
              background: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              color: '#fca5a5',
              fontSize: 12.5,
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            <Trash2 size={14} />
            Clear All Saved
          </button>
        )}
      </div>

      {savedStories.length === 0 ? (
        <EmptyState
          title="No Saved Stories Yet"
          description="Bookmark stories from the Home feed, category feeds, or the Story Object to build your personal intelligence briefing."
          actionLabel="Explore Home Feed"
          onAction={() => navigate('/')}
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
            gap: 24,
          }}
        >
          {savedStories.map((story) => (
            <StoryCard
              key={story.id}
              story={story}
              variant="supporting"
              onListen={onListen}
              isSaved={true}
              onToggleSave={onToggleSave}
              watchLaterStories={watchLaterStories}
              onToggleWatchLater={onToggleWatchLater}
              isWatchLater={watchLaterStories.some((s) => String(s.id) === String(story.id))}
              onWatchVideo={(s) => {
                setModalStory(s);
                setModalVideoIndex(0);
                setIsModalOpen(true);
              }}
            />
          ))}
        </div>
      )}

      {/* Video Modal Player */}
      {isModalOpen && modalStory && (
        <VideoModalPlayer
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          story={modalStory}
          initialVideoIndex={modalVideoIndex}
          accentColor={modalStory.categoryMeta?.color || '#FFB020'}
          isSaved={true}
          onToggleSave={onToggleSave}
        />
      )}
    </div>
  );
}
