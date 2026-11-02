import React, { useState, useEffect } from 'react';
import { Sparkles, CheckCircle2 } from 'lucide-react';

/**
 * WatchSentimentPulse: Gen-Z "Fact vs Cap" Live Reaction & Community Consensus Bar.
 * - Dynamic: consensus progress bar is revealed ONLY once user casts a reaction vote.
 * - Live reaction counting: Clicking increments (+1) dynamically like Likes and persists.
 * - Toggle & Switch support: Click active reaction to un-vote, or click another to switch.
 */
export default function WatchSentimentPulse({
  storyId,
  initialLikes = 320,
  accentColor = '#00E5FF',
}) {
  const storageKey = `estd_pulse_${storyId || 'general'}`;

  // Initial reactions state with persistent counts and userVoted
  const [reactions, setReactions] = useState(() => {
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) return JSON.parse(stored);
    } catch {
      // fallback
    }
    const seed = typeof storyId === 'number' ? storyId : 42;
    return {
      fact: Math.max(12, ((seed * 19) % 180) + 45),
      cap: Math.max(3, ((seed * 7) % 40) + 8),
      fire: Math.max(20, ((seed * 23) % 250) + 60),
      mindblown: Math.max(8, ((seed * 11) % 90) + 15),
      bruh: Math.max(2, ((seed * 5) % 35) + 5),
      userVoted: null, // null until user clicks
    };
  });

  const [floatingEmoji, setFloatingEmoji] = useState(null);

  // Sync state if storyId changes
  useEffect(() => {
    try {
      const stored = localStorage.getItem(storageKey);
      if (stored) {
        setReactions(JSON.parse(stored));
      } else {
        const seed = typeof storyId === 'number' ? storyId : 42;
        setReactions({
          fact: Math.max(12, ((seed * 19) % 180) + 45),
          cap: Math.max(3, ((seed * 7) % 40) + 8),
          fire: Math.max(20, ((seed * 23) % 250) + 60),
          mindblown: Math.max(8, ((seed * 11) % 90) + 15),
          bruh: Math.max(2, ((seed * 5) % 35) + 5),
          userVoted: null,
        });
      }
    } catch {
      // ignore
    }
  }, [storyId, storageKey]);

  const handleVote = (type, emojiChar) => {
    setReactions((prev) => {
      const isAlreadyVoted = prev.userVoted === type;
      const updated = { ...prev };

      if (isAlreadyVoted) {
        // Toggle off: decrement vote count and hide consensus bar
        updated[type] = Math.max(0, (updated[type] || 0) - 1);
        updated.userVoted = null;
        setFloatingEmoji({ emoji: emojiChar, label: '-1 Removed', id: Date.now() });
      } else {
        // If previously voted for another icon, decrement that old one
        if (prev.userVoted && updated[prev.userVoted] !== undefined) {
          updated[prev.userVoted] = Math.max(0, updated[prev.userVoted] - 1);
        }
        // Increment newly clicked icon
        updated[type] = (updated[type] || 0) + 1;
        updated.userVoted = type;
        setFloatingEmoji({ emoji: emojiChar, label: '+1 Added', id: Date.now() });
      }

      try {
        localStorage.setItem(storageKey, JSON.stringify(updated));
      } catch {
        // ignore
      }

      return updated;
    });

    setTimeout(() => setFloatingEmoji(null), 1200);
  };

  const hasVoted = Boolean(reactions.userVoted);

  // Compute Fact vs Cap ratio
  const factSide = (reactions.fact || 0) + (reactions.fire || 0);
  const capSide = (reactions.cap || 0) + (reactions.bruh || 0);
  const total = factSide + capSide || 1;
  const factPercent = Math.min(99, Math.max(1, Math.round((factSide / total) * 100)));
  const capPercent = 100 - factPercent;
  const totalVotes =
    (reactions.fact || 0) +
    (reactions.cap || 0) +
    (reactions.fire || 0) +
    (reactions.mindblown || 0) +
    (reactions.bruh || 0);

  return (
    <div className="watch-sentiment-pulse-container" aria-label="Community Fact vs Cap Pulse">
      {/* Floating emoji notification */}
      {floatingEmoji && (
        <div key={floatingEmoji.id} className="watch-floating-reaction-badge">
          <span>{floatingEmoji.emoji}</span>
          <span className="watch-floating-reaction-text">{floatingEmoji.label}</span>
        </div>
      )}

      <div className="watch-sentiment-header-row">
        <div className="watch-sentiment-title-wrap">
          <Sparkles size={14} style={{ color: accentColor }} />
          <span className="watch-sentiment-label">Community Pulse & Integrity</span>
          <span className="watch-sentiment-genz-tag">GEN-Z CONSENSUS</span>
        </div>

        {hasVoted ? (
          <div className="watch-sentiment-ratio-badge animate-fade-in">
            <span className="watch-ratio-fact">{factPercent}% Fact / Receipts</span>
            <span className="watch-ratio-divider">•</span>
            <span className="watch-ratio-cap">{capPercent}% Cap / Spin</span>
            <span className="watch-total-votes-count">({totalVotes} votes)</span>
          </div>
        ) : (
          <div className="watch-sentiment-cta-hint">
            <span>Tap an icon to vote & reveal live consensus</span>
          </div>
        )}
      </div>

      {/* Consensus Ratio Bar: DYNAMICALLY shown only when user votes! */}
      {hasVoted && (
        <div className="watch-consensus-bar-track animate-reveal">
          <div
            className="watch-consensus-bar-fill fact-fill"
            style={{
              width: `${factPercent}%`,
              background: `linear-gradient(90deg, #10b981, ${accentColor})`,
            }}
            title={`${factPercent}% Verified & Fact-checked`}
          />
          <div
            className="watch-consensus-bar-fill cap-fill"
            style={{
              width: `${capPercent}%`,
              background: 'linear-gradient(90deg, #f59e0b, #ef4444)',
            }}
            title={`${capPercent}% Questioned / Spin`}
          />
        </div>
      )}

      {/* Reaction Buttons Pill Dock */}
      <div className="watch-reaction-pills-dock">
        {/* Fact */}
        <button
          type="button"
          className={`watch-reaction-btn ${reactions.userVoted === 'fact' ? 'active-fact' : ''}`}
          onClick={() => handleVote('fact', '🎯')}
          title="Verified fact with receipts"
        >
          <span className="watch-reaction-emoji">🎯</span>
          <span className="watch-reaction-name">Fact</span>
          <span className="watch-reaction-count">{reactions.fact}</span>
        </button>

        {/* Cap */}
        <button
          type="button"
          className={`watch-reaction-btn ${reactions.userVoted === 'cap' ? 'active-cap' : ''}`}
          onClick={() => handleVote('cap', '🧢')}
          title="Questionable claim / Corporate PR spin"
        >
          <span className="watch-reaction-emoji">🧢</span>
          <span className="watch-reaction-name">Cap</span>
          <span className="watch-reaction-count">{reactions.cap}</span>
        </button>

        {/* Fire / Lit */}
        <button
          type="button"
          className={`watch-reaction-btn ${reactions.userVoted === 'fire' ? 'active-fire' : ''}`}
          onClick={() => handleVote('fire', '🔥')}
          title="Huge development / Must watch"
        >
          <span className="watch-reaction-emoji">🔥</span>
          <span className="watch-reaction-name">Lit</span>
          <span className="watch-reaction-count">{reactions.fire}</span>
        </button>

        {/* Mindblown / Wild */}
        <button
          type="button"
          className={`watch-reaction-btn ${reactions.userVoted === 'mindblown' ? 'active-mindblown' : ''}`}
          onClick={() => handleVote('mindblown', '🤯')}
          title="Mind-blowing revelation"
        >
          <span className="watch-reaction-emoji">🤯</span>
          <span className="watch-reaction-name">Wild</span>
          <span className="watch-reaction-count">{reactions.mindblown}</span>
        </button>

        {/* Bruh */}
        <button
          type="button"
          className={`watch-reaction-btn ${reactions.userVoted === 'bruh' ? 'active-bruh' : ''}`}
          onClick={() => handleVote('bruh', '💀')}
          title="Unbelievable fail / Bruh moment"
        >
          <span className="watch-reaction-emoji">💀</span>
          <span className="watch-reaction-name">Bruh</span>
          <span className="watch-reaction-count">{reactions.bruh}</span>
        </button>
      </div>
    </div>
  );
}
