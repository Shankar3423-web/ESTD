import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  X,
  Share2,
  Check,
  ChevronLeft,
  ChevronRight,
  ArrowRight,
} from 'lucide-react';
import ImageWithFallback from '../common/ImageWithFallback';
import { getCategoryMeta } from '../../constants/taxonomy';
import {
  generateSmartBrevityBullets,
  formatCleanHeadline,
  formatCleanTopicName,
} from '../../utils/flashBitesUtils';

/**
 * FlashBiteModal — Full-Screen Interactive Smart Brevity Micro-Reader Modal.
 * Used across HomePage Flash Bites rail and StoryObject article view.
 */
export default function FlashBiteModal({
  isOpen = false,
  story = null,
  stories = [],
  initialIndex = 0,
  onClose,
}) {
  const navigate = useNavigate();

  // Story list to display (fall back to single story if no list provided)
  const storyList = useMemo(() => {
    if (stories && stories.length > 0) return stories;
    if (story) return [story];
    return [];
  }, [stories, story]);

  // Determine starting index
  const resolvedInitialIndex = useMemo(() => {
    if (story && storyList.length > 0) {
      const idx = storyList.findIndex((s) => String(s.id) === String(story.id));
      if (idx !== -1) return idx;
    }
    return Math.min(Math.max(0, initialIndex), Math.max(0, storyList.length - 1));
  }, [story, storyList, initialIndex]);

  const [activeIndex, setActiveIndex] = useState(resolvedInitialIndex);
  const [copied, setCopied] = useState(false);

  // Sync activeIndex whenever initialIndex or story changes
  useEffect(() => {
    if (isOpen) {
      setActiveIndex(resolvedInitialIndex);
    }
  }, [isOpen, resolvedInitialIndex]);

  // Active Story
  const currentStory = storyList[activeIndex] || story;

  // Category accent
  const currentAccent = useMemo(() => {
    if (!currentStory) return '#00E5FF';
    const meta = getCategoryMeta(currentStory.category);
    return meta?.color || '#00E5FF';
  }, [currentStory]);

  // 3-Block Smart Brevity Bullets
  const currentBullets = useMemo(() => {
    if (!currentStory) return [];
    return generateSmartBrevityBullets(currentStory);
  }, [currentStory]);

  // Keyboard navigation
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (onClose) onClose();
      } else if (e.key === 'ArrowLeft' && storyList.length > 1) {
        setActiveIndex((prev) => Math.max(0, prev - 1));
      } else if (e.key === 'ArrowRight' && storyList.length > 1) {
        setActiveIndex((prev) => Math.min(storyList.length - 1, prev + 1));
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, storyList.length, onClose]);

  const handleShare = (e, targetStory) => {
    e.stopPropagation();
    if (!targetStory) return;
    const url = `${window.location.origin}/story/${targetStory.id}`;
    if (navigator.share) {
      navigator
        .share({
          title: targetStory.headline,
          text: targetStory.brief,
          url,
        })
        .catch(() => copyLink(url));
    } else {
      copyLink(url);
    }
  };

  const copyLink = (url) => {
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReadFull = () => {
    if (!currentStory) return;
    if (onClose) onClose();
    navigate(`/story/${currentStory.id}`);
  };

  if (!isOpen || !currentStory) return null;

  return (
    <div
      className="flash-modal-backdrop"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      {/* Ambient Luminescent Aura Glow behind the glass card */}
      <div
        className="flash-modal-ambient-glow"
        style={{ '--modal-accent': currentAccent }}
      />

      <div
        className="flash-modal-container"
        onClick={(e) => e.stopPropagation()}
        style={{ '--modal-accent': currentAccent }}
      >
        {/* Sticky Glass Top Header */}
        <div className="flash-modal-top-section">
          {/* Top Multi-Segment Progress Bars (when multiple stories) */}
          {storyList.length > 1 && (
            <div className="flash-modal-progress-bar">
              {storyList.map((_, idx) => (
                <div
                  key={idx}
                  className={`flash-progress-seg ${
                    idx === activeIndex
                      ? 'active'
                      : idx < activeIndex
                      ? 'completed'
                      : ''
                  }`}
                  onClick={() => setActiveIndex(idx)}
                />
              ))}
            </div>
          )}

          {/* Modal Meta Header */}
          <div className="flash-modal-header">
            <div className="flash-modal-meta">
              <span
                className="flash-modal-cat-badge"
                style={{
                  backgroundColor: `${currentAccent}22`,
                  borderColor: `${currentAccent}66`,
                  color: currentAccent,
                }}
              >
                {formatCleanTopicName(currentStory)}
              </span>
              <span className="flash-modal-source">
                {currentStory.sourceName || 'Verified Source'}
              </span>
              <span className="flash-modal-readtime">
                ⚡ 60s Flash Brief
              </span>
            </div>

            <div className="flash-modal-actions">
              <button
                type="button"
                className="flash-modal-action-btn"
                onClick={(e) => handleShare(e, currentStory)}
                title="Share Story"
                aria-label="Share Story"
              >
                {copied ? <Check size={16} color="#10B981" /> : <Share2 size={16} />}
              </button>
              <button
                type="button"
                className="flash-modal-action-btn"
                onClick={onClose}
                title="Close (Esc)"
                aria-label="Close modal"
              >
                <X size={18} />
              </button>
            </div>
          </div>
        </div>

        {/* Scrollable Content Body with Hero and Bullets */}
        <div className="flash-modal-scroll-body">
          {/* Visual Hero */}
          <div className="flash-modal-hero">
            <ImageWithFallback
              src={currentStory.imageUrl}
              alt={currentStory.headline}
              category={currentStory.category}
              subcategory={currentStory.subcategory}
              className="flash-modal-hero-img"
              size="large"
            />
            <div className="flash-modal-hero-overlay" />
            <h2 className="flash-modal-headline">{formatCleanHeadline(currentStory)}</h2>
          </div>

          {/* Combined 3-Block Flash Intelligence Cards */}
          <div className="flash-modal-bullets">
            {currentBullets.map((bullet, i) => (
              <div key={i} className={`flash-bullet-card flash-bullet-card-${i}`}>
                <div className="flash-bullet-header">
                  <span className="flash-bullet-icon">{bullet.icon}</span>
                  <span className="flash-bullet-label">{bullet.label}</span>
                  {bullet.badge && (
                    <span className="flash-bullet-subbadge">{bullet.badge}</span>
                  )}
                </div>
                {bullet.bullets && bullet.bullets.length > 0 ? (
                  <ul className="flash-bullet-list">
                    {bullet.bullets.map((item, idx) => {
                      const parts = item.split(': ');
                      return (
                        <li key={idx} className="flash-bullet-list-item">
                          <span className="flash-bullet-dot">▪</span>
                          <div className="flash-bullet-item-content">
                            {parts.length > 1 ? (
                              <>
                                <strong className="flash-bullet-strong">{parts[0]}:</strong>{' '}
                                <span>{parts.slice(1).join(': ')}</span>
                              </>
                            ) : (
                              <span>{item}</span>
                            )}
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <p className="flash-bullet-text">{bullet.text}</p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Sticky Glass Footer Controls */}
        <div className="flash-modal-footer">
          {storyList.length > 1 && (
            <div className="flash-modal-nav">
              <button
                type="button"
                className="flash-nav-btn"
                onClick={() => setActiveIndex((p) => Math.max(0, p - 1))}
                disabled={activeIndex === 0}
              >
                <ChevronLeft size={16} />
                <span>Prev</span>
              </button>
              <button
                type="button"
                className="flash-nav-btn"
                onClick={() =>
                  setActiveIndex((p) => Math.min(storyList.length - 1, p + 1))
                }
                disabled={activeIndex === storyList.length - 1}
              >
                <span>Next</span>
                <ChevronRight size={16} />
              </button>
            </div>
          )}

          <button
            type="button"
            className="flash-full-story-btn"
            onClick={handleReadFull}
          >
            <span>Read Full Intelligence</span>
            <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}

