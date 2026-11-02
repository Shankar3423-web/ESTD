import React from 'react';
import { ExternalLink, FileText, CheckCircle, Globe, Calendar } from 'lucide-react';

export default function ArticleCard({ article }) {
  const getCategoryClass = (category) => {
    switch (category) {
      case 'Entertainment':
        return 'tag-ent';
      case 'Sports':
        return 'tag-sports';
      case 'Tech':
      case 'Technology':
      case 'Artificial Intelligence':
        return 'tag-tech';
      case 'Developments':
      case 'Education':
      case 'Science':
        return 'tag-dev';
      case 'Business & Finance':
      case 'Business':
        return 'tag-biz';
      default:
        return 'tag-tech';
    }
  };

  const hasDoc = article.google_doc && article.google_doc.status === 'CREATED';

  return (
    <div className="article-card">
      <div>
        <div className="article-card-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
            <span className={`category-tag ${getCategoryClass(article.category)}`}>
              {article.category}
            </span>
            {article.subcategory && (
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 600,
                  padding: '2px 8px',
                  borderRadius: 4,
                  background: 'rgba(255, 255, 255, 0.08)',
                  color: '#e2e8f0',
                  border: '1px solid rgba(255, 255, 255, 0.12)',
                }}
              >
                {article.subcategory}
              </span>
            )}
          </div>
          <span className="mono" style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            ID: #{article.id}
          </span>
        </div>

        <h3 className="article-title">{article.title}</h3>

        <div className="article-meta" style={{ marginTop: 8 }}>
          {article.published_at && (
            <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <Calendar size={12} />
              {new Date(article.published_at).toLocaleDateString()}
            </span>
          )}
          <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <Globe size={12} />
            {article.source_name || 'Unknown Source'} ({article.source_type})
          </span>
        </div>
      </div>

      {article.executive_summary && (
        <div className="article-summary">
          <div style={{ fontSize: 11, fontWeight: 700, color: '#93c5fd', marginBottom: 4, textTransform: 'uppercase' }}>
            Executive Synthesis (Gemini AI)
          </div>
          <p>{article.executive_summary}</p>
        </div>
      )}

      <div style={{ marginTop: 12, padding: '10px 12px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: 8, fontSize: 12, display: 'flex', flexDirection: 'column', gap: 4 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--text-secondary)' }}>ESTD Status:</span>
          <strong style={{ color: '#60a5fa' }}>{article.pipeline_status}</strong>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: 'var(--text-secondary)' }}>Google Doc:</span>
          <strong style={{ color: hasDoc ? '#34d399' : '#94a3b8' }}>
            {hasDoc ? 'Created ✓' : article.google_doc?.status || 'Pending'}
          </strong>
        </div>
      </div>

      <div className="article-footer" style={{ marginTop: 14 }}>
        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: 'var(--text-muted)', fontSize: 12, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 4 }}
          title="Open original source URL"
        >
          Source URL <ExternalLink size={11} />
        </a>

        {hasDoc && article.google_doc?.document_url ? (
          <a
            href={article.google_doc.document_url}
            target="_blank"
            rel="noopener noreferrer"
            className="doc-btn"
          >
            <FileText size={14} />
            View Google Document
            <ExternalLink size={12} />
          </a>
        ) : (
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            Google Doc: {article.google_doc?.status || 'Not generated yet'}
          </span>
        )}
      </div>
    </div>
  );
}
