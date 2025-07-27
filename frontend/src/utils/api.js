import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API calls - Updated to match backend endpoints
export const authAPI = {
  login: (email, password) => api.post('/api/auth/login', { email, password }),
  register: (email, password) => api.post('/api/auth/register', { email, password }),
  me: () => api.get('/api/auth/me'),
  updateTier: (tier) => api.put('/api/auth/tier', { tier }),
};

// Player API calls - Updated to match Python service endpoints
const pythonAPI = axios.create({
  baseURL: process.env.REACT_APP_PYTHON_API_URL || 'http://localhost:18001',
  timeout: 30000,
});

// Add auth interceptor for Python API
pythonAPI.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

export const playerAPI = {
  search: (query, limit = 10) => pythonAPI.post('/api/players/search', { query, limit }),
  getStats: (playerId, options = {}) => pythonAPI.get(`/api/players/${playerId}/stats`, { params: options }),
  getSummary: (playerId) => pythonAPI.get(`/api/players/${playerId}/summary`),
  getTrending: (limit = 10) => pythonAPI.get(`/api/players/trending`, { params: { limit } }),
  bulkStats: (playerIds, statTypes) => pythonAPI.post('/api/players/bulk-stats', { player_ids: playerIds, stat_types: statTypes }),
};

// Analytics API calls - Updated to match actual endpoints
export const analyticsAPI = {
  getDatabaseStats: () => pythonAPI.get('/api/test/database-stats'),
  getDataVerification: () => pythonAPI.get('/api/test/2025-data-verification'),
  collectData: (date) => pythonAPI.post(`/api/test/collect-data${date ? `?date=${date}` : ''}`),
  collectFangraphs: (season = 2025) => pythonAPI.post(`/api/test/collect-fangraphs?season=${season}`),
  collectSeasonStatcast: (season = 2025) => pythonAPI.post(`/api/test/collect-season-statcast?season=${season}`),
};

// AI API calls
export const aiAPI = {
  chat: (query, context = {}) => api.post('/api/ai/chat', { query, context }),
  analyzeProp: (playerName, propType, bettingLine, gameContext = {}) =>
    api.post('/api/ai/analyze-prop', { 
      player_name: playerName, 
      prop_type: propType, 
      betting_line: bettingLine, 
      game_context: gameContext 
    }),
  explainStats: (playerName, statistics) =>
    api.post('/api/ai/explain-stats', { player_name: playerName, statistics }),
  getSuggestions: () => api.get('/api/ai/suggestions'),
  batchAnalyze: (queries) => api.post('/api/ai/batch-analyze', { queries }),
  getConversations: (limit = 20, offset = 0) =>
    api.get('/api/ai/conversations', { params: { limit, offset } }),
  getUsageStats: () => api.get('/api/ai/usage-stats'),
  health: () => api.get('/api/ai/health'),
};

// Utility functions
export const handleAPIError = (error) => {
  if (error.response) {
    // Server responded with error status
    return error.response.data?.error || error.response.data?.message || 'Server error';
  } else if (error.request) {
    // Request was made but no response received
    return 'Network error - please check your connection';
  } else {
    // Something else happened
    return error.message || 'An unexpected error occurred';
  }
};

export const formatAPIResponse = (response) => {
  return {
    data: response.data,
    cached: response.data.cached || false,
    timestamp: new Date().toISOString(),
  };
};

export default api;