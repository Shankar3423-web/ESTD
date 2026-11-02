/**
 * Watch section utilities for category matching and balanced interleaving.
 */

export function matchCategory(storyCategory, targetSlug) {
  if (!storyCategory || !targetSlug) return false;
  if (targetSlug === 'all' || targetSlug === 'All') return true;
  const s = storyCategory.toLowerCase().trim();
  const t = targetSlug.toLowerCase().trim();
  if (t === 'business-finance' || t === 'business & finance' || t.includes('business') || t.includes('finance')) {
    return s.includes('biz') || s.includes('finance') || s.includes('business');
  }
  if (t === 'tech') return s === 'tech' || s.includes('tech');
  if (t === 'entertainment') return s.includes('entertainment') || s.includes('entertain');
  if (t === 'developments') return s.includes('development') || s.includes('develop');
  if (t === 'sports') return s.includes('sport');
  return s === t;
}

/**
 * Interleaves stories round-robin across categories so the 'All' feed
 * presents a rich, balanced combination instead of contiguous category blocks.
 */
export function interleaveStoriesByCategory(storiesList) {
  if (!storiesList || storiesList.length === 0) return [];
  const categoryOrder = [
    'Tech',
    'Business & Finance',
    'Entertainment',
    'Sports',
    'Developments',
  ];

  const buckets = {};
  for (const cat of categoryOrder) {
    buckets[cat] = [];
  }
  const otherBucket = [];

  for (const s of storiesList) {
    const sCat = s.category || '';
    let matched = false;
    for (const catName of categoryOrder) {
      if (matchCategory(sCat, catName)) {
        buckets[catName].push(s);
        matched = true;
        break;
      }
    }
    if (!matched) {
      otherBucket.push(s);
    }
  }

  const result = [];
  const maxLen = Math.max(
    ...categoryOrder.map((c) => buckets[c].length),
    otherBucket.length
  );

  for (let i = 0; i < maxLen; i++) {
    for (const catName of categoryOrder) {
      if (i < buckets[catName].length) {
        result.push(buckets[catName][i]);
      }
    }
    if (i < otherBucket.length) {
      result.push(otherBucket[i]);
    }
  }

  return result;
}

