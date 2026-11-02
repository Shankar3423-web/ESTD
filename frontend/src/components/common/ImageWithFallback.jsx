import React, { useState, useEffect } from 'react';
import { Cpu, Film, TrendingUp, Compass, Trophy, GraduationCap, Newspaper } from 'lucide-react';
import { getCategoryMeta } from '../../constants/taxonomy';
import { getTopicFallbackImage, optimizeImageUrl } from '../../api/estdApi';

const CATEGORY_ICONS = {
  Tech: Cpu,
  Entertainment: Film,
  'Business & Finance': TrendingUp,
  Developments: Compass,
  Sports: Trophy,
  Education: GraduationCap,
};

const SIZE_WIDTHS = {
  hero: 840,
  card: 520,
  row: 400,
  thumb: 140,
  auto: 520,
};

/**
 * High-Performance Image Component with instant rendering, progressive loading,
 * automatic WebP dimension optimization, and graceful zero-flicker fallback.
 */
export default function ImageWithFallback({
  src,
  alt = 'ESTD News Image',
  className = '',
  category = 'Tech',
  subcategory = 'General',
  aspectRatio = '16/9',
  size = 'auto',
  priority = false,
  id,
}) {
  const [hasError, setHasError] = useState(false);
  const [attemptedFallback, setAttemptedFallback] = useState(false);
  const [isLoaded, setIsLoaded] = useState(false);

  const catMeta = getCategoryMeta(category) || {};
  const accentColor = catMeta.color || '#00E5FF';
  const IconComponent = CATEGORY_ICONS[category] || Newspaper;

  const targetWidth = SIZE_WIDTHS[size] || 520;
  const rawSeed = id || alt || category;
  const fallbackPhoto = getTopicFallbackImage(category, subcategory, rawSeed);

  // Compute active image source with smart optimization
  const initialSource = src || fallbackPhoto;
  const currentSrc = !attemptedFallback ? initialSource : fallbackPhoto;
  const optimizedSrc = optimizeImageUrl(currentSrc, targetWidth);

  useEffect(() => {
    setHasError(false);
    setAttemptedFallback(false);
    setIsLoaded(false);
  }, [src, category, subcategory]);

  const handleImageError = () => {
    if (!attemptedFallback && fallbackPhoto && currentSrc !== fallbackPhoto) {
      // Instantly switch to the fast local/thematic fallback
      setAttemptedFallback(true);
    } else {
      setHasError(true);
      setIsLoaded(true);
    }
  };

  // If both primary and fallback failed, show sleek editorial desk badge
  if (!optimizedSrc || (hasError && attemptedFallback)) {
    return (
      <div
        className={`image-fallback-container ${className}`}
        style={{
          width: '100%',
          height: '100%',
          aspectRatio,
          background: `radial-gradient(circle at 50% 40%, ${accentColor}18 0%, #0d1017 80%)`,
          border: `1px solid ${accentColor}25`,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 10,
          color: '#94a3b8',
          fontSize: 12,
          padding: 16,
          textAlign: 'center',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: '50%',
            background: `${accentColor}18`,
            border: `1px solid ${accentColor}44`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: accentColor,
            boxShadow: `0 0 16px ${accentColor}22`,
          }}
        >
          <IconComponent size={22} />
        </div>
        <div>
          <span style={{ fontWeight: 600, color: '#e2e8f0', letterSpacing: '-0.01em' }}>
            {subcategory !== 'General' ? subcategory : category}
          </span>
          <span style={{ display: 'block', fontSize: 11, color: '#64748b', marginTop: 2 }}>
            ESTD News Intelligence
          </span>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        background: '#12141c',
      }}
    >
      {/* Subtle non-blocking shimmer behind the image */}
      {!isLoaded && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'linear-gradient(90deg, #12141c 25%, #1c202c 50%, #12141c 75%)',
            backgroundSize: '200% 100%',
            animation: 'skeleton-shimmer 1.4s infinite ease-in-out',
            zIndex: 1,
            pointerEvents: 'none',
          }}
        />
      )}

      {/* Rendered Image — No crossOrigin to avoid CORS blocks, progressive streaming */}
      <img
        src={optimizedSrc}
        alt={alt}
        loading={priority ? 'eager' : 'lazy'}
        decoding="async"
        fetchPriority={priority ? 'high' : 'auto'}
        referrerPolicy="no-referrer"
        className={className}
        onLoad={() => setIsLoaded(true)}
        onError={handleImageError}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          display: 'block',
          position: 'relative',
          zIndex: 2,
          opacity: isLoaded ? 1 : 0.85,
          transition: 'opacity 0.2s ease-in-out',
        }}
      />
    </div>
  );
}
