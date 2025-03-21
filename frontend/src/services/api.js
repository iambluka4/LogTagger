import axios from 'axios';
import { refreshToken, getToken, logoutUser } from './auth';

// Базова URL вашого backend
export const API_BASE = "http://localhost:5000";

// Setup axios instance
const apiClient = axios.create({
  baseURL: API_BASE
});

// Add request interceptor
apiClient.interceptors.request.use(
  config => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  error => Promise.reject(error)
);

// Add response interceptor for token refresh
apiClient.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config;
    
    // If error is 401 and we haven't tried to refresh the token yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        // Try to refresh the token
        const token = await refreshToken();
        // Retry the original request with new token
        originalRequest.headers.Authorization = `Bearer ${token}`;
        return apiClient(originalRequest);
      } catch (refreshError) {
        // If refresh fails, logout and redirect to login
        logoutUser();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// API Functions

// Config
export const getConfig = () => {
  return apiClient.get('/api/config');
};

export const updateConfig = (data) => {
  return apiClient.post('/api/config', data);
};

export const testConnection = (connectionData) => {
  return apiClient.post('/api/config/test-connection', connectionData);
};

// Events
export const getEvents = (params = {}) => {
  return apiClient.get('/api/events', { params });
};

export const getEvent = (eventId) => {
  return apiClient.get(`/api/events/${eventId}`);
};

export const labelEvent = (eventId, labelData) => {
  return apiClient.post(`/api/events/${eventId}/label`, labelData);
};

// Fetch events from SIEM systems
export const fetchEvents = (params = {}) => {
  return apiClient.post('/api/events/fetch', params);
};

// Export events
export const exportEvents = (format = 'csv', filters = {}) => {
  return apiClient.post('/api/events/export', { format, filters });
};

// User management
export const getUsers = () => {
  return apiClient.get('/api/users');
};

export const getUser = (userId) => {
  return apiClient.get(`/api/users/${userId}`);
};

export const createUser = (userData) => {
  return apiClient.post('/api/users', userData);
};

export const updateUser = (userId, userData) => {
  return apiClient.put(`/api/users/${userId}`, userData);
};

export const deleteUser = (userId) => {
  return apiClient.delete(`/api/users/${userId}`);
};

// MITRE ATT&CK Framework
export const getMitreTactics = () => {
  return apiClient.get('/api/mitre/tactics');
};

export const getMitreTechniques = (tacticId = null) => {
  const params = tacticId ? { tactic_id: tacticId } : {};
  return apiClient.get('/api/mitre/techniques', { params });
};

// Export job status
export const getExportJobs = () => {
  return apiClient.get('/api/export-jobs');
};

export const getExportJob = (jobId) => {
  return apiClient.get(`/api/export-jobs/${jobId}`);
};

export const downloadExport = (filePath) => {
  return apiClient.get(`/api/download/${filePath}`, {
    responseType: 'blob'
  });
};

// Dashboard statistics
export const getDashboardStats = () => {
  return apiClient.get('/api/dashboard/stats');
};

export const getTopAttackTypes = (params = {}) => {
  return apiClient.get('/api/dashboard/top-attacks', { params });
};

export const getEventTimeline = (params = {}) => {
  return apiClient.get('/api/dashboard/timeline', { params });
};

export const getSeverityDistribution = () => {
  return apiClient.get('/api/dashboard/severity');
};

export const getMitreDistribution = () => {
  return apiClient.get('/api/dashboard/mitre-distribution');
};