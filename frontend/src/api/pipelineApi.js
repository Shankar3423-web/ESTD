import { apiRequest } from './client';

/**
 * Triggers the end-to-end ESTD backend pipeline execution.
 * @param {Object} options - Optional parameters { categories, target_per_category }
 */
export async function runPipeline(options = {}) {
  return apiRequest('/pipeline/run', {
    method: 'POST',
    body: JSON.stringify(options),
  });
}

/**
 * Retrieves the live status and progress of a pipeline job.
 * @param {string} jobId - The job identifier
 */
export async function getJobStatus(jobId) {
  return apiRequest(`/pipeline/jobs/${jobId}`);
}

/**
 * Retrieves the status of the most recently executed job.
 */
export async function getLatestJob() {
  return apiRequest('/pipeline/jobs/latest');
}

/**
 * Retrieves runner state (whether actively running and active job id).
 */
export async function getPipelineStatus() {
  return apiRequest('/pipeline/status');
}

/**
 * Retrieves aggregate system health and subsystem overview.
 */
export async function getSystemOverview() {
  return apiRequest('/pipeline/overview');
}
