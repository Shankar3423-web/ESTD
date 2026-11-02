import { apiRequest } from './client';

/**
 * Fetches dashboard articles from PostgreSQL knowledge source with attached Google Document data.
 * @param {Object} params - Query filters { category, search, limit }
 */
export async function fetchArticles({ category, search, limit = 50 } = {}) {
  const queryParams = new URLSearchParams();
  if (category && category !== 'All') {
    queryParams.append('category', category);
  }
  if (search && search.trim()) {
    queryParams.append('search', search.trim());
  }
  if (limit) {
    queryParams.append('limit', limit);
  }

  const queryStr = queryParams.toString() ? `?${queryParams.toString()}` : '';
  return apiRequest(`/pipeline/articles${queryStr}`);
}

/**
 * Fetches a single article from the Step 5 knowledge source by ID.
 * @param {number} articleId
 */
export async function fetchArticleById(articleId) {
  return apiRequest(`/api/v1/knowledge/articles/${articleId}`);
}

/**
 * Fetches the Step 8 Google Document status for an article.
 * @param {number} articleId
 */
export async function fetchDocumentStatus(articleId) {
  return apiRequest(`/step8/documents/${articleId}`);
}
