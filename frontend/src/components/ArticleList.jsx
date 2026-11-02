import React, { useState, useMemo } from 'react';
import { Newspaper, Search, Filter } from 'lucide-react';
import ArticleCard from './ArticleCard';

const CATEGORIES = [
  'All',
  'Entertainment',
  'Sports',
  'Tech',
  'Developments',
  'Business & Finance',
];

export default function ArticleList({
  articles = [],
  isLoading,
  selectedCategory,
  onSelectCategory,
  onTriggerPipeline,
}) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSubcategory, setSelectedSubcategory] = useState('All');

  // Reset subcategory when category changes
  const handleCategoryChange = (cat) => {
    setSelectedSubcategory('All');
    onSelectCategory(cat);
  };

  const availableSubcategories = useMemo(() => {
    if (selectedCategory === 'All') return [];
    const subs = new Set();
    articles.forEach((art) => {
      if (art.category === selectedCategory && art.subcategory) {
        subs.add(art.subcategory);
      }
    });
    return Array.from(subs).sort();
  }, [articles, selectedCategory]);

  const filteredArticles = useMemo(() => {
    return articles.filter((art) => {
      // Category filter
      if (selectedCategory !== 'All' && art.category !== selectedCategory) {
        return false;
      }
      // Subcategory filter
      if (selectedSubcategory !== 'All' && art.subcategory !== selectedSubcategory) {
        return false;
      }
      // Search term filter
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const inTitle = art.title?.toLowerCase().includes(query);
        const inSource = art.source_name?.toLowerCase().includes(query);
        const inCat = art.category?.toLowerCase().includes(query);
        const inSubcat = art.subcategory?.toLowerCase().includes(query);
        const inSummary = art.executive_summary?.toLowerCase().includes(query);
        return inTitle || inSource || inCat || inSubcat || inSummary;
      }
      return true;
    });
  }, [articles, selectedCategory, selectedSubcategory, searchTerm]);

  return (
    <div className="dashboard-section">
      <div className="section-header">
        <div className="section-title">
          <Newspaper size={18} />
          Processed ESTD Articles & Google Documents ({filteredArticles.length})
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="filter-bar">
        <div className="category-tabs">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              className={`tab-btn ${selectedCategory === cat ? 'active' : ''}`}
              onClick={() => handleCategoryChange(cat)}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="search-box">
          <Search size={16} color="#94a3b8" />
          <input
            type="text"
            className="search-input"
            placeholder="Search by title, source, subcategory..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      {/* Subcategory Pills (if available for selected category) */}
      {availableSubcategories.length > 0 && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 16, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginRight: 4 }}>
            Subcategories:
          </span>
          <button
            className={`tab-btn ${selectedSubcategory === 'All' ? 'active' : ''}`}
            style={{ fontSize: 11, padding: '3px 10px' }}
            onClick={() => setSelectedSubcategory('All')}
          >
            All
          </button>
          {availableSubcategories.map((sub) => (
            <button
              key={sub}
              className={`tab-btn ${selectedSubcategory === sub ? 'active' : ''}`}
              style={{ fontSize: 11, padding: '3px 10px' }}
              onClick={() => setSelectedSubcategory(sub)}
            >
              {sub}
            </button>
          ))}
        </div>
      )}

      {/* Articles Grid / Empty State */}
      {isLoading ? (
        <div className="empty-state">
          <h3>Loading articles from knowledge base...</h3>
          <p>Connecting to PostgreSQL knowledge source.</p>
        </div>
      ) : filteredArticles.length === 0 ? (
        <div className="empty-state">
          <Newspaper size={48} color="#475569" style={{ margin: '0 auto 16px' }} />
          <h3>No processed ESTD articles yet</h3>
          <p>
            {searchTerm || selectedCategory !== 'All'
              ? 'No articles match the selected category or search filters.'
              : 'Click "Fetch & Process Latest News" above to run the live backend intelligence pipeline.'}
          </p>
          {articles.length === 0 && (
            <button
              className="btn btn-primary"
              style={{ marginTop: 16 }}
              onClick={onTriggerPipeline}
            >
              Fetch & Process Latest News
            </button>
          )}
        </div>
      ) : (
        <div className="articles-grid">
          {filteredArticles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      )}
    </div>
  );
}
