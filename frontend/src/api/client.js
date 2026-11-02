/**
 * Base HTTP client for communicating exclusively with the ESTD FastAPI backend.
 * Never connects directly to PostgreSQL, Gemini, Google Drive, or news providers.
 */
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function apiRequest(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const response = await fetch(url, {
      ...options,
      headers,
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const errorMsg =
        data?.detail?.message ||
        data?.error?.message ||
        data?.detail ||
        `HTTP ${response.status}: ${response.statusText}`;
      const error = new Error(errorMsg);
      error.status = response.status;
      error.code = data?.detail?.code || data?.error?.code || 'API_ERROR';
      error.details = data;
      throw error;
    }

    return data;
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      const netError = new Error(
        `Unable to reach ESTD backend at ${BASE_URL}. Ensure the FastAPI server is running.`
      );
      netError.code = 'NETWORK_ERROR';
      throw netError;
    }
    throw err;
  }
}
