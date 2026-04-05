import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000'
});

/**
 * Check if the backend is reachable.
 */
export async function checkBackendStatus() {
    try {
      await axios.get('http://localhost:8000/health', { timeout: 2000 });
      return true;
    } catch (err) {
      return false;
    }
}

export async function submitAnalysis(formData) {
    console.log('[API] Submitting analysis with FormData:');
    for (let pair of formData.entries()) {
      console.log(`  ${pair[0]}: ${pair[1] instanceof File ? pair[1].name : pair[1]}`);
    }

    try {
      const response = await api.post('/api/analysis/full', formData);
      console.log('[API] Analysis response:', response.data);
      return response.data;
    } catch (err) {
      console.error('[API] submission failed:', err);
      throw new Error(err.response?.data?.detail || 'Analysis request failed. Please check if the backend is running.');
    }
}
  
export async function getReport(reportId) {
    try {
      const response = await api.get(`/api/report/${reportId}`);
      return response.data;
    } catch (err) {
      console.error('[API] getReport failed:', err);
      throw new Error(err.response?.data?.detail || 'Could not retrieve report.');
    }
}
  
export async function translateText(informalText) {
    console.log('[API] Translating:', informalText);
    const response = await api.post('/api/roadmap/translate', {
      informal_text: informalText,
    });
    return response.data; // Return full object: { original_text, polished_text, professional_text, tone }
}
  
export async function getGitHubPortfolio(username) {
    const response = await api.get(`/api/github/${username}`);
    return response.data;
}