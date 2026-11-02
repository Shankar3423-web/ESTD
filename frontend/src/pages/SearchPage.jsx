import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Search,
  X,
  Sparkles,
  ShieldCheck,
  Zap,
  ArrowRight,
  Cpu,
  Film,
  TrendingUp,
  Compass,
  Trophy,
  CheckCircle2,
  ChevronRight,
  RefreshCw,
  Flame,
  Radio,
} from 'lucide-react';
import StoryCard from '../components/story/StoryCard';
import VideoRail from '../components/story/VideoRail';
import VideoModalPlayer from '../components/story/VideoModalPlayer';
import ImpactChips from '../components/story/ImpactChips';
import EmptyState from '../components/common/EmptyState';
import ErrorState from '../components/common/ErrorState';
import { askEstdIntelligence, fetchStories } from '../api/estdApi';
import { CATEGORIES, SUBCATEGORIES_BY_CATEGORY, getCategoryMeta } from '../constants/taxonomy';

// Category icon map for visual badges
const CATEGORY_ICON_MAP = {
  Tech: Cpu,
  Entertainment: Film,
  'Business & Finance': TrendingUp,
  Developments: Compass,
  Sports: Trophy,
};

// Curated prominent subcategories for 'All'
const FEATURED_SUBCATEGORIES = [
  'Artificial Intelligence',
  'Startups & Venture Capital',
  'Cricket',
  'Digital Platforms & Big Tech',
  'Movies & Cinema',
  'Energy, Climate & Environment',
  'Cybersecurity & Privacy',
  'Financial Markets & Banking',
  'Football',
  'Emerging Tech & Semiconductors',
];

export default function SearchPage({
  savedStories = [],
  onToggleSave,
  onListen,
}) {
  const [searchParams, setSearchParams] = useSearchParams();
  const queryParam = searchParams.get('q') || '';
  const categoryParam = searchParams.get('category') || 'All';
  const isRadarSource = searchParams.get('from') === 'radar';
  const navigate = useNavigate();

  // Cancel any lingering browser speech synthesis
  useEffect(() => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const [inputVal, setInputVal] = useState(queryParam);
  const [selectedCategory, setSelectedCategory] = useState(categoryParam);
  const [synthesisData, setSynthesisData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Landing wire stories when no search query is active
  const [landingStories, setLandingStories] = useState([]);
  const [loadingLanding, setLoadingLanding] = useState(false);

  // Video Modal State
  const [modalStory, setModalStory] = useState(null);
  const [modalVideoIndex, setModalVideoIndex] = useState(0);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Sync input value with URL queryParam
  useEffect(() => {
    setInputVal(queryParam);
  }, [queryParam]);

  // Sync category state with URL param
  useEffect(() => {
    if (categoryParam) {
      setSelectedCategory(categoryParam);
    }
  }, [categoryParam]);

  // Load landing stories if no active search query
  useEffect(() => {
    let isMounted = true;
    if (!queryParam.trim()) {
      setLoadingLanding(true);
      fetchStories({
        category: selectedCategory !== 'All' ? selectedCategory : undefined,
        limit: 12,
      })
        .then((stories) => {
          if (isMounted) setLandingStories(stories);
        })
        .catch((err) => {
          console.warn('Failed to fetch landing stories:', err);
        })
        .finally(() => {
          if (isMounted) setLoadingLanding(false);
        });
    }
    return () => {
      isMounted = false;
    };
  }, [queryParam, selectedCategory]);

  // Execute Gemini AI Intelligence Search when queryParam changes
  useEffect(() => {
    if (!queryParam.trim()) {
      setSynthesisData(null);
      return;
    }

    let isMounted = true;
    async function executeIntelligenceQuery() {
      setLoading(true);
      setError(null);
      try {
        const response = await askEstdIntelligence({
          query: queryParam.trim(),
          category: selectedCategory !== 'All' ? selectedCategory : undefined,
          limit: 20,
        });
        if (isMounted) {
          setSynthesisData(response);
        }
      } catch (err) {
        if (isMounted) {
          console.error('Ask ESTD failed:', err);
          setError(err.message || 'Failed to synthesize intelligence.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    }

    executeIntelligenceQuery();
    return () => {
      isMounted = false;
    };
  }, [queryParam, selectedCategory]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputVal.trim()) {
      const params = { q: inputVal.trim() };
      if (selectedCategory && selectedCategory !== 'All') {
        params.category = selectedCategory;
      }
      setSearchParams(params);
    }
  };

  const handleClear = () => {
    setInputVal('');
    const params = {};
    if (selectedCategory && selectedCategory !== 'All') {
      params.category = selectedCategory;
    }
    setSearchParams(params);
    setSynthesisData(null);
  };

  const handleCategorySelect = (categoryName) => {
    setSelectedCategory(categoryName);
    const params = {};
    if (queryParam.trim()) {
      params.q = queryParam.trim();
    }
    if (categoryName !== 'All') {
      params.category = categoryName;
    }
    setSearchParams(params);
  };

  const handleTopicClick = (topicName) => {
    setInputVal(topicName);
    const params = { q: topicName };
    if (selectedCategory && selectedCategory !== 'All') {
      params.category = selectedCategory;
    }
    setSearchParams(params);
  };

  // Determine which subcategory chips to display based on category
  const activeSubcategories =
    selectedCategory === 'All'
      ? FEATURED_SUBCATEGORIES
      : SUBCATEGORIES_BY_CATEGORY[selectedCategory] || [];

  const topArticle = synthesisData?.articles?.[0] || null;
  const videoRail = topArticle?.video_rail || [];

  return (
    <div style={{ maxWidth: 1240, margin: '0 auto', paddingBottom: 80, paddingLeft: 16, paddingRight: 16 }}>
      {/* Header & Intelligence Search Form */}
      <div
        style={{
          padding: '24px 0 16px',
          borderBottom: '1px solid rgba(255,255,255,0.08)',
          marginBottom: 20,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 38,
              height: 38,
              borderRadius: 10,
              background: 'linear-gradient(135deg, rgba(0, 229, 255, 0.2), rgba(168, 85, 247, 0.2))',
              border: '1px solid rgba(0, 229, 255, 0.4)',
              boxShadow: '0 0 16px rgba(0, 229, 255, 0.25)',
            }}
          >
            <Sparkles size={22} style={{ color: '#00E5FF' }} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h1 style={{ fontSize: 28, fontWeight: 800, color: '#ffffff', letterSpacing: '-0.02em', margin: 0 }}>
                Ask ESTD Intelligence
              </h1>
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  padding: '2px 8px',
                  borderRadius: 9999,
                  background: 'rgba(0, 229, 255, 0.15)',
                  color: '#00E5FF',
                  border: '1px solid rgba(0, 229, 255, 0.35)',
                }}
              >
                Gemini 2.5 Flash
              </span>
            </div>
            <p style={{ fontSize: 13.5, color: '#94a3b8', margin: '4px 0 0 0' }}>
              Real-time AI news synthesis grounded in verified ESTD wire dispatches and global knowledge.
            </p>
          </div>
        </div>

        {/* Search Input Bar */}
        <form
          onSubmit={handleSubmit}
          style={{
            position: 'relative',
            maxWidth: 780,
            marginTop: 18,
          }}
        >
          <Search
            size={20}
            style={{
              position: 'absolute',
              left: 18,
              top: '50%',
              transform: 'translateY(-50%)',
              color: '#00E5FF',
            }}
          />
          <input
            type="text"
            className="search-input"
            style={{
              width: '100%',
              boxSizing: 'border-box',
              padding: '15px 120px 15px 52px',
              fontSize: 15.5,
              borderRadius: 14,
              background: '#0D0F17',
              color: '#ffffff',
              border: '1px solid rgba(0, 229, 255, 0.3)',
              boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
              outline: 'none',
              transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
            }}
            placeholder="Ask ESTD: 'What happened in the latest Cricket match?' or 'Explain OpenAI strategy'..."
            value={inputVal}
            onChange={(e) => setInputVal(e.target.value)}
          />

          <div
            style={{
              position: 'absolute',
              right: 12,
              top: '50%',
              transform: 'translateY(-50%)',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            {inputVal && (
              <button
                type="button"
                onClick={handleClear}
                style={{
                  color: '#94a3b8',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: 6,
                  display: 'flex',
                  alignItems: 'center',
                }}
                title="Clear query"
              >
                <X size={18} />
              </button>
            )}
            <button
              type="submit"
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 5,
                background: 'linear-gradient(135deg, #00E5FF, #0088FF)',
                border: 'none',
                color: '#07090E',
                fontSize: 13,
                fontWeight: 700,
                padding: '7px 14px',
                borderRadius: 9,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
            >
              Ask
              <ArrowRight size={14} />
            </button>
          </div>
        </form>

        {/* Category Filter Chips Bar */}
        <div style={{ marginTop: 18 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
            <button
              onClick={() => handleCategorySelect('All')}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                padding: '6px 14px',
                borderRadius: 9999,
                fontSize: 13,
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                background: selectedCategory === 'All' ? 'rgba(255, 255, 255, 0.15)' : '#0F121C',
                border: selectedCategory === 'All' ? '1px solid #ffffff' : '1px solid rgba(255, 255, 255, 0.08)',
                color: selectedCategory === 'All' ? '#ffffff' : '#94a3b8',
              }}
            >
              <Sparkles size={13} style={{ color: selectedCategory === 'All' ? '#00E5FF' : '#64748b' }} />
              All Categories
            </button>

            {CATEGORIES.map((cat) => {
              const IconComp = CATEGORY_ICON_MAP[cat.name] || Sparkles;
              const isSelected = selectedCategory === cat.name;
              return (
                <button
                  key={cat.id}
                  onClick={() => handleCategorySelect(cat.name)}
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                    padding: '6px 14px',
                    borderRadius: 9999,
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    background: isSelected ? `${cat.color}22` : '#0F121C',
                    border: isSelected ? `1px solid ${cat.color}` : '1px solid rgba(255, 255, 255, 0.08)',
                    color: isSelected ? '#ffffff' : '#94a3b8',
                    boxShadow: isSelected ? `0 0 12px ${cat.color}33` : 'none',
                  }}
                >
                  <IconComp size={13} style={{ color: isSelected ? cat.color : '#64748b' }} />
                  {cat.name}
                </button>
              );
            })}
          </div>
        </div>

        {/* Dynamic Canonical Subcategory Topic Chips */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginTop: 14 }}>
          <span style={{ fontSize: 12, color: '#64748b', fontWeight: 600 }}>Explore Topics:</span>
          {activeSubcategories.map((topic) => (
            <button
              key={topic}
              onClick={() => handleTopicClick(topic)}
              style={{
                fontSize: 12,
                padding: '4px 11px',
                borderRadius: 9999,
                background: queryParam.toLowerCase() === topic.toLowerCase() ? 'rgba(0, 229, 255, 0.2)' : '#12141F',
                border:
                  queryParam.toLowerCase() === topic.toLowerCase()
                    ? '1px solid #00E5FF'
                    : '1px solid rgba(255,255,255,0.08)',
                color: queryParam.toLowerCase() === topic.toLowerCase() ? '#ffffff' : '#cbd5e1',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#00E5FF';
                e.currentTarget.style.color = '#ffffff';
              }}
              onMouseLeave={(e) => {
                if (queryParam.toLowerCase() !== topic.toLowerCase()) {
                  e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)';
                  e.currentTarget.style.color = '#cbd5e1';
                }
              }}
            >
              {topic}
            </button>
          ))}
        </div>
      </div>

      {/* Loading Skeleton & Pulse */}
      {loading && (
        <div
          style={{
            background: 'linear-gradient(135deg, #0e121e, #0a0d14)',
            border: '1px solid rgba(0, 229, 255, 0.25)',
            borderRadius: 18,
            padding: 32,
            marginTop: 20,
            marginBottom: 36,
            textAlign: 'center',
          }}
        >
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 52,
              height: 52,
              borderRadius: '50%',
              background: 'rgba(0, 229, 255, 0.1)',
              border: '1px solid rgba(0, 229, 255, 0.3)',
              marginBottom: 16,
              animation: 'spin 2s linear infinite',
            }}
          >
            <Sparkles size={26} style={{ color: '#00E5FF' }} />
          </div>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: '#ffffff', marginBottom: 8 }}>
            Synthesizing Intelligence on "{queryParam}"...
          </h3>
          <p style={{ fontSize: 13.5, color: '#94a3b8', maxWidth: 520, margin: '0 auto' }}>
            Gemini 2.5 Flash is actively analyzing wire dispatches, verifying source integrity, and drafting your executive briefing.
          </p>
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <ErrorState
          title="Intelligence Synthesis Failed"
          error={error}
          onRetry={() => setSearchParams({ q: queryParam, category: selectedCategory })}
        />
      )}

      {/* SYNTHESIZED INTELLIGENCE ANSWER PANEL (When search query returned results) */}
      {!loading && !error && synthesisData && (
        <>
          <section
            style={{
              background: 'linear-gradient(135deg, #0E121E 0%, #0A0D15 100%)',
              border: '1px solid rgba(0, 229, 255, 0.35)',
              borderRadius: 18,
              padding: '24px 28px',
              marginBottom: 32,
              boxShadow: '0 12px 36px rgba(0, 229, 255, 0.08)',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            {/* Header Badges */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', marginBottom: 14 }}>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 800,
                  textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  padding: '3px 10px',
                  borderRadius: 9999,
                  background: 'rgba(0, 229, 255, 0.15)',
                  color: '#00E5FF',
                  border: '1px solid rgba(0, 229, 255, 0.3)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 5,
                }}
              >
                <Sparkles size={12} />
                ESTD Intelligence Synthesis
              </span>

              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  padding: '3px 9px',
                  borderRadius: 9999,
                  background: 'rgba(168, 85, 247, 0.15)',
                  color: '#C084FC',
                  border: '1px solid rgba(168, 85, 247, 0.3)',
                }}
              >
                Model: {synthesisData.source_model || 'gemini-2.5-flash'}
              </span>

              {synthesisData.has_estd_articles ? (
                <span
                  style={{
                    fontSize: 11.5,
                    color: '#10B981',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 5,
                    fontWeight: 600,
                  }}
                >
                  <ShieldCheck size={14} />
                  Grounded in {synthesisData.articles_count} verified ESTD wire reports
                </span>
              ) : (
                <span
                  style={{
                    fontSize: 11.5,
                    color: '#FFB020',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 5,
                    fontWeight: 600,
                  }}
                >
                  <Zap size={13} />
                  Live AI Knowledge Synthesis • Related ESTD Wire Below
                </span>
              )}

              {synthesisData.cached && (
                <span style={{ fontSize: 11, color: '#64748b' }}>
                  • Instant cache hit
                </span>
              )}

              {isRadarSource && (
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    padding: '3px 10px',
                    borderRadius: 9999,
                    background: 'rgba(255, 32, 184, 0.15)',
                    color: '#FF20B8',
                    border: '1px solid rgba(255, 32, 184, 0.4)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 5,
                  }}
                >
                  <Radio size={12} style={{ animation: 'radarPulseBeacon 1.2s infinite' }} />
                  Live Radar Event Dispatch
                </span>
              )}
            </div>

            {/* Headline */}
            <h2
              style={{
                fontSize: 24,
                fontWeight: 800,
                color: '#ffffff',
                lineHeight: 1.3,
                marginBottom: 12,
                letterSpacing: '-0.01em',
              }}
            >
              {synthesisData.headline}
            </h2>

            {/* Executive Synthesis Answer */}
            <p
              style={{
                fontSize: 15,
                color: '#cbd5e1',
                lineHeight: 1.7,
                maxWidth: 920,
                marginBottom: 20,
              }}
            >
              {synthesisData.answer}
            </p>

            {/* Key Takeaways Box */}
            {synthesisData.key_takeaways && synthesisData.key_takeaways.length > 0 && (
              <div
                style={{
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderRadius: 14,
                  padding: '16px 20px',
                  marginBottom: 20,
                }}
              >
                <div
                  style={{
                    fontSize: 12,
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    letterSpacing: '0.08em',
                    color: '#00E5FF',
                    marginBottom: 10,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <CheckCircle2 size={14} />
                  Key Intelligence Takeaways
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  {synthesisData.key_takeaways.map((takeaway, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: 10,
                        fontSize: 13.5,
                        color: '#e2e8f0',
                        lineHeight: 1.5,
                      }}
                    >
                      <span
                        style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          minWidth: 18,
                          height: 18,
                          borderRadius: '50%',
                          background: 'rgba(0, 229, 255, 0.15)',
                          color: '#00E5FF',
                          fontSize: 10,
                          fontWeight: 700,
                          marginTop: 2,
                        }}
                      >
                        {idx + 1}
                      </span>
                      <span>{takeaway}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Suggested Follow-up Topics */}
            {synthesisData.suggested_topics && synthesisData.suggested_topics.length > 0 && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginTop: 14 }}>
                <span style={{ fontSize: 12, color: '#64748b', fontWeight: 600 }}>Suggested Follow-ups:</span>
                {synthesisData.suggested_topics.map((topic, i) => (
                  <button
                    key={i}
                    onClick={() => handleTopicClick(topic)}
                    style={{
                      fontSize: 12,
                      padding: '4px 11px',
                      borderRadius: 9999,
                      background: 'rgba(168, 85, 247, 0.1)',
                      border: '1px solid rgba(168, 85, 247, 0.25)',
                      color: '#D8B4FE',
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = '#00E5FF';
                      e.currentTarget.style.color = '#ffffff';
                      e.currentTarget.style.background = 'rgba(0, 229, 255, 0.15)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = 'rgba(168, 85, 247, 0.25)';
                      e.currentTarget.style.color = '#D8B4FE';
                      e.currentTarget.style.background = 'rgba(168, 85, 247, 0.1)';
                    }}
                  >
                    {topic}
                    <ChevronRight size={11} />
                  </button>
                ))}
              </div>
            )}

            {/* Video Suggestions Rail (if available) */}
            {videoRail.length > 0 && (
              <div style={{ marginTop: 22, paddingTop: 18, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                <VideoRail
                  videos={videoRail}
                  storyId={topArticle?.id}
                  accentColor="#00E5FF"
                  title="Suggested Multi-Angle News Videos"
                  subtitle="Video angles matching your query"
                  onSelectVideo={(vid, idx) => {
                    setModalStory(topArticle);
                    setModalVideoIndex(idx);
                    setIsModalOpen(true);
                  }}
                />
              </div>
            )}
          </section>

          {/* VERIFIED MATCHING STORIES GRID */}
          <section>
            <div className="section-header" style={{ marginBottom: 18 }}>
              <h3 className="section-title">
                {synthesisData.has_estd_articles ? (
                  <>
                    <ShieldCheck size={18} style={{ color: '#10B981' }} />
                    Verified Matching Stories ({synthesisData.articles?.length || 0})
                  </>
                ) : (
                  <>
                    <Flame size={18} style={{ color: '#FFB020' }} />
                    Trending Stories Across ESTD News Wire
                  </>
                )}
              </h3>
              <span className="section-subtitle">
                {synthesisData.has_estd_articles
                  ? 'Grounded articles cross-referenced for this briefing'
                  : 'Related dispatches from active news categories'}
              </span>
            </div>

            {synthesisData.articles && synthesisData.articles.length > 0 ? (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
                  gap: 22,
                }}
              >
                {synthesisData.articles.map((story) => (
                  <StoryCard
                    key={story.id}
                    story={story}
                    variant="supporting"
                    onListen={onListen}
                    isSaved={savedStories.some((s) => s.id === story.id)}
                    onToggleSave={onToggleSave}
                    onWatchVideo={(s) => {
                      setModalStory(s);
                      setModalVideoIndex(0);
                      setIsModalOpen(true);
                    }}
                  />
                ))}
              </div>
            ) : (
              <div
                style={{
                  background: '#0D101A',
                  border: '1px solid rgba(255,255,255,0.08)',
                  borderRadius: 14,
                  padding: 32,
                  textAlign: 'center',
                  color: '#94a3b8',
                }}
              >
                No news articles currently stored in this specific subcategory. Try clearing your category filter or exploring another topic above.
              </div>
            )}
          </section>
        </>
      )}

      {/* DEFAULT LANDING EXPLORER (When NO search query is active) */}
      {!loading && !error && !queryParam && (
        <>
          {/* CATEGORY & SUBCATEGORY EXPLORER MATRIX */}
          <section style={{ marginBottom: 40 }}>
            <div className="section-header" style={{ marginBottom: 18 }}>
              <h3 className="section-title">
                <Sparkles size={18} style={{ color: '#00E5FF' }} />
                Explore ESTD Knowledge Base by Category
              </h3>
              <span className="section-subtitle">
                Click any topic or subcategory to generate real-time AI intelligence
              </span>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
                gap: 18,
              }}
            >
              {CATEGORIES.map((cat) => {
                const IconComp = CATEGORY_ICON_MAP[cat.name] || Sparkles;
                const subcats = SUBCATEGORIES_BY_CATEGORY[cat.name] || [];
                return (
                  <div
                    key={cat.id}
                    style={{
                      background: 'linear-gradient(135deg, #0e121e, #0a0d15)',
                      border: `1px solid ${cat.color}26`,
                      borderRadius: 16,
                      padding: 20,
                      display: 'flex',
                      flexDirection: 'column',
                      justifyContent: 'space-between',
                      transition: 'border-color 0.2s ease, transform 0.2s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.borderColor = cat.color;
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.borderColor = `${cat.color}26`;
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <div
                            style={{
                              width: 32,
                              height: 32,
                              borderRadius: 8,
                              background: `${cat.color}18`,
                              border: `1px solid ${cat.color}33`,
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                            }}
                          >
                            <IconComp size={16} style={{ color: cat.color }} />
                          </div>
                          <h4 style={{ fontSize: 16, fontWeight: 700, color: '#ffffff', margin: 0 }}>
                            {cat.name}
                          </h4>
                        </div>
                        <span
                          style={{
                            fontSize: 11,
                            fontWeight: 700,
                            padding: '2px 8px',
                            borderRadius: 9999,
                            background: `${cat.color}15`,
                            color: cat.color,
                          }}
                        >
                          {subcats.length} Topics
                        </span>
                      </div>

                      <p style={{ fontSize: 12.5, color: '#94a3b8', lineHeight: 1.45, marginBottom: 14 }}>
                        {cat.description}
                      </p>

                      {/* Subcategory Pills */}
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                        {subcats.map((sub) => (
                          <button
                            key={sub}
                            onClick={() => {
                              setSelectedCategory(cat.name);
                              handleTopicClick(sub);
                            }}
                            style={{
                              fontSize: 11.5,
                              padding: '3px 9px',
                              borderRadius: 8,
                              background: '#121624',
                              border: '1px solid rgba(255, 255, 255, 0.08)',
                              color: '#cbd5e1',
                              cursor: 'pointer',
                              transition: 'all 0.15s ease',
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.borderColor = cat.color;
                              e.currentTarget.style.color = '#ffffff';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.borderColor = 'rgba(255, 255, 255, 0.08)';
                              e.currentTarget.style.color = '#cbd5e1';
                            }}
                          >
                            {sub}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          {/* TRENDING WIRE STORIES SECTION */}
          <section>
            <div className="section-header" style={{ marginBottom: 18 }}>
              <h3 className="section-title">
                <Flame size={18} style={{ color: '#FFB020' }} />
                Trending Stories in ESTD Wire
              </h3>
              <span className="section-subtitle">
                Latest verified reports across all five news intelligence desks
              </span>
            </div>

            {loadingLanding ? (
              <div style={{ height: 260, background: '#12141c', borderRadius: 16 }} />
            ) : (
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))',
                  gap: 22,
                }}
              >
                {landingStories.map((story) => (
                  <StoryCard
                    key={story.id}
                    story={story}
                    variant="supporting"
                    onListen={onListen}
                    isSaved={savedStories.some((s) => s.id === story.id)}
                    onToggleSave={onToggleSave}
                    onWatchVideo={(s) => {
                      setModalStory(s);
                      setModalVideoIndex(0);
                      setIsModalOpen(true);
                    }}
                  />
                ))}
              </div>
            )}
          </section>
        </>
      )}

      {/* Video Lightbox Modal */}
      {isModalOpen && modalStory && (
        <VideoModalPlayer
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          story={modalStory}
          initialVideoIndex={modalVideoIndex}
          accentColor={modalStory.categoryMeta?.color || '#00E5FF'}
          isSaved={savedStories.some((s) => s.id === modalStory.id)}
          onToggleSave={onToggleSave}
        />
      )}

      {/* Equalizer and Radar Pulse Animations */}
      <style>{`
        @keyframes eqPulse1 {
          0% { height: 4px; }
          100% { height: 16px; }
        }
        @keyframes eqPulse2 {
          0% { height: 18px; }
          100% { height: 6px; }
        }
        @keyframes eqPulse3 {
          0% { height: 8px; }
          100% { height: 20px; }
        }
      `}</style>
    </div>
  );
}