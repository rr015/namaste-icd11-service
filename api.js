// src/services/api.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

let authToken = null;

export const setAuthToken = (token) => {
  authToken = token;
};

export const getAuthToken = () => {
  return authToken;
};

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  if (authToken) {
    config.headers.Authorization = `Bearer ${authToken}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear token and redirect to login if unauthorized
      setAuthToken(null);
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API methods
export const authAPI = {
  login: (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    return api.post('/token', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
  },
};

export const terminologyAPI = {
  // Search and basic operations
  search: (searchRequest) => api.post('/search', searchRequest),
  autocomplete: (prefix, system, limit = 5) => 
    api.get('/autocomplete', { params: { prefix, system, limit } }),
  translate: (translateRequest) => api.post('/translate', translateRequest),
  getCodeDetails: (system, code) => api.get(`/code/${system}/${code}`),
  
  // WHO API Integration
  searchWHO: (query, system = 'icd11_tm2') => 
    api.post('/who/search', { query, system }),
  autoMap: (namasteCode, namasteDisplay) => 
    api.post('/who/auto-map', { namaste_code: namasteCode, namaste_display: namasteDisplay }),
  getWHOStatus: () => api.get('/who/status'),
  testWHO: () => api.get('/test/who-api'),
  
  // Admin endpoints
  importCSV: (request) => api.post('/admin/import/csv', request),
  syncWHO: (request) => api.post('/admin/sync/who', request),
  getVersions: () => api.get('/admin/versions'),
  activateVersion: (version) => api.post(`/admin/versions/${version}/activate`),
  
  // FHIR endpoints
  getCodeSystem: (system, version) => 
    api.get(`/fhir/CodeSystem/${system}`, { params: { version } }),
  getConceptMap: (source, target) => 
    api.get(`/fhir/ConceptMap/${source}/to/${target}`),
  createProblemList: (problemEntry) => api.post('/fhir/ProblemList', problemEntry),
  importFHIRBundle: (bundle) => api.post('/fhir/Bundle', bundle),
  
  // Compliance and audit endpoints
  getCompliancePolicies: () => api.get('/compliance/policies'),
  getSNOMEDLOINCMappings: (code) => api.get(`/snomed/loinc/mappings/${code}`),
  getTerminologyMappings: (system, code) => 
    api.get(`/terminology/mappings/${system}/${code}`),
  getAuditLogs: () => api.get('/audit/logs'),
  
  // Consent management
  createConsent: (consentData) => api.post('/consent', consentData),
  getConsent: (consentId) => api.get(`/consent/${consentId}`),
  
  // Data export
  exportData: (system, format = 'json') => 
    api.get(`/export/${system}`, { params: { format } }),
  
  // Debug and monitoring
  healthCheck: () => api.get('/health'),
  debugRoutes: () => api.get('/debug/routes'),
  debugDataStats: () => api.get('/debug/data-stats'),
};

// Utility functions for common API patterns
export const apiUtils = {
  // Handle API responses with consistent error handling
  handleResponse: async (apiCall, successCallback, errorCallback) => {
    try {
      const response = await apiCall;
      if (successCallback) successCallback(response.data);
      return response.data;
    } catch (error) {
      console.error('API Error:', error);
      const errorMessage = error.response?.data?.detail || error.message;
      if (errorCallback) errorCallback(errorMessage);
      throw new Error(errorMessage);
    }
  },

  // Download data as file
  downloadFile: (data, filename, type = 'application/json') => {
    const blob = new Blob([data], { type });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    window.URL.revokeObjectURL(url);
  },

  // Format search parameters
  formatSearchParams: (params) => {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== null && value !== undefined) {
        searchParams.append(key, value.toString());
      }
    });
    return searchParams;
  },
};

// Export specific API instances for direct use if needed
export { api as default, api as axiosInstance };