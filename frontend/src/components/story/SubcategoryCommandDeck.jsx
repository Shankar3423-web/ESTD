import React, { useMemo, useState } from 'react';
import {
  Sparkles,
  Layers,
  Search,
  Cpu,
  Cloud,
  Smartphone,
  ShieldCheck,
  Code2,
  Zap,
  Film,
  Music,
  Tv,
  Video,
  Star,
  Gamepad2,
  Award,
  BookOpen,
  Trophy,
  Flame,
  Target,
  Wind,
  Gauge,
  Medal,
  Landmark,
  Building2,
  Leaf,
  HeartPulse,
  GraduationCap,
  Atom,
  Globe2,
  TrendingUp,
  Rocket,
  Briefcase,
  Wallet,
  BarChart3,
  Check,
} from 'lucide-react';

/**
 * Intelligent icon resolver based on subcategory keywords
 */
function getSubcategoryIcon(subName = '') {
  const s = subName.toLowerCase();

  // Tech
  if (s.includes('intel') || s.includes('ai') || s.includes('gpt')) return Cpu;
  if (s.includes('cloud') || s.includes('software')) return Cloud;
  if (s.includes('gadget') || s.includes('consumer') || s.includes('hardware')) return Smartphone;
  if (s.includes('secur') || s.includes('privacy')) return ShieldCheck;
  if (s.includes('develop') || s.includes('source') || s.includes('code')) return Code2;
  if (s.includes('semiconductor') || s.includes('chip') || s.includes('emerg')) return Zap;
  if (s.includes('platform') || s.includes('big tech')) return Layers;

  // Entertainment
  if (s.includes('movie') || s.includes('cinema')) return Film;
  if (s.includes('music') || s.includes('audio')) return Music;
  if (s.includes('tv') || s.includes('ott') || s.includes('series')) return Tv;
  if (s.includes('creator') || s.includes('influencer')) return Video;
  if (s.includes('celeb') || s.includes('culture') || s.includes('pop')) return Star;
  if (s.includes('game') || s.includes('gaming')) return Gamepad2;
  if (s.includes('award') || s.includes('event')) return Award;
  if (s.includes('story') || s.includes('digital')) return BookOpen;

  // Sports
  if (s.includes('cricket')) return Flame;
  if (s.includes('foot') || s.includes('soccer')) return Target;
  if (s.includes('tennis')) return Target;
  if (s.includes('badminton')) return Wind;
  if (s.includes('motor') || s.includes('f1') || s.includes('racing')) return Gauge;
  if (s.includes('athletic') || s.includes('olympic')) return Medal;
  if (s.includes('esport')) return Gamepad2;
  if (s.includes('sport')) return Trophy;

  // Developments
  if (s.includes('govern') || s.includes('policy')) return Landmark;
  if (s.includes('infra') || s.includes('urban')) return Building2;
  if (s.includes('energy') || s.includes('climate') || s.includes('environ')) return Leaf;
  if (s.includes('health') || s.includes('medic')) return HeartPulse;
  if (s.includes('educat') || s.includes('learn')) return GraduationCap;
  if (s.includes('science') || s.includes('research')) return Atom;
  if (s.includes('global') || s.includes('geopolitic')) return Globe2;

  // Business & Finance
  if (s.includes('market') || s.includes('bank')) return TrendingUp;
  if (s.includes('startup') || s.includes('venture')) return Rocket;
  if (s.includes('strategy') || s.includes('earning') || s.includes('corporate')) return Briefcase;
  if (s.includes('personal finance') || s.includes('wealth')) return Wallet;
  if (s.includes('econom') || s.includes('macro')) return BarChart3;

  return Layers;
}

/**
 * SubcategoryCommandDeck — Replaces horizontal scroll with an elegant,
 * non-scrolling wrap-around Bento pill command matrix with icons and live story counts.
 */
export default function SubcategoryCommandDeck({
  subcategories = [],
  selectedSubcategory = 'All',
  onSelectSubcategory,
  stories = [],
  categoryName = 'Tech',
  accentColor = '#00E5FF',
}) {
  const [filterQuery, setFilterQuery] = useState('');

  // Pre-calculate live story counts per subcategory
  const countsBySubcategory = useMemo(() => {
    const map = {};
    for (const sub of subcategories) {
      const subLower = sub.toLowerCase().trim();
      let matchCount = 0;
      for (const story of stories) {
        const storySub = (story.subcategory || '').toLowerCase().trim();
        if (
          storySub === subLower ||
          storySub.includes(subLower) ||
          subLower.includes(storySub)
        ) {
          matchCount++;
        }
      }
      map[sub] = matchCount;
    }
    return map;
  }, [stories, subcategories]);

  const totalCategoryStories = stories.length;

  // Filter and prioritize active subcategories with verified stories first
  const visibleSubcategories = useMemo(() => {
    let list = [...subcategories];
    if (filterQuery.trim()) {
      const q = filterQuery.toLowerCase();
      list = list.filter((sub) => sub.toLowerCase().includes(q));
    }
    // Sort so subcategories with active verified stories appear first
    list.sort((a, b) => {
      const countA = countsBySubcategory[a] || 0;
      const countB = countsBySubcategory[b] || 0;
      if (countA > 0 && countB === 0) return -1;
      if (countB > 0 && countA === 0) return 1;
      return 0;
    });
    return list;
  }, [subcategories, filterQuery, countsBySubcategory]);

  return (
    <div
      className="subcategory-command-deck"
      style={{
        '--deck-accent': accentColor,
      }}
    >
      {/* Top Deck Header: Section Title + Quick Search Pill */}
      <div className="scd-header">
        <div className="scd-title-group">
          <div
            className="scd-icon-badge"
            style={{
              background: `${accentColor}18`,
              color: accentColor,
              borderColor: `${accentColor}44`,
            }}
          >
            <Layers size={14} />
          </div>
          <div>
            <h3 className="scd-heading">
              Explore {categoryName} Subcategories
            </h3>
            <span className="scd-subtext">
              Curated perspectives &bull; Zero hidden scrolling
            </span>
          </div>
        </div>

        {/* Quick Filter Pill */}
        {subcategories.length > 5 && (
          <div className="scd-search-box">
            <Search size={13} className="scd-search-icon" />
            <input
              type="text"
              placeholder="Filter topics..."
              value={filterQuery}
              onChange={(e) => setFilterQuery(e.target.value)}
              className="scd-search-input"
            />
            {filterQuery && (
              <button
                type="button"
                className="scd-search-clear"
                onClick={() => setFilterQuery('')}
              >
                &times;
              </button>
            )}
          </div>
        )}
      </div>

      {/* Non-Scrolling Wrap Matrix */}
      <div
        className="scd-pills-matrix"
        role="tablist"
        aria-label={`${categoryName} subcategories`}
      >
        {/* Master "All" Capsule */}
        <button
          type="button"
          className={`scd-pill master-pill ${selectedSubcategory === 'All' ? 'active' : ''}`}
          onClick={() => onSelectSubcategory('All')}
          role="tab"
          aria-selected={selectedSubcategory === 'All'}
          style={{
            '--pill-accent': accentColor,
          }}
        >
          <div className="scd-pill-icon">
            <Sparkles size={13} />
          </div>
          <span className="scd-pill-label">All {categoryName}</span>
          <span className="scd-pill-count">
            {totalCategoryStories}
          </span>
        </button>

        {/* Individual Subcategory Capsules */}
        {visibleSubcategories.map((sub) => {
          const isSelected = selectedSubcategory === sub;
          const SubIcon = getSubcategoryIcon(sub);
          const count = countsBySubcategory[sub] || 0;

          return (
            <button
              key={sub}
              type="button"
              className={`scd-pill ${isSelected ? 'active' : ''}`}
              onClick={() => onSelectSubcategory(sub)}
              role="tab"
              aria-selected={isSelected}
              style={{
                '--pill-accent': accentColor,
              }}
            >
              <div className="scd-pill-icon">
                <SubIcon size={13} />
              </div>
              <span className="scd-pill-label">{sub}</span>
              <span className="scd-pill-count">
                {count}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
