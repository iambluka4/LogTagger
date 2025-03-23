import axios from 'axios';

// Базова URL вашого backend
export const API_BASE = "http://localhost:5000";

// Setup axios instance без токенів авторизації
const apiClient = axios.create({
  baseURL: API_BASE
});

// API Functions

// Config - We need to ensure this points to the right endpoint
export const getConfig = async () => {
  try {
    console.log('Fetching configuration...');
    const response = await axios.get('/api/system-config'); // system-config endpoint
    console.log('Configuration fetched:', response.data);
    return response;
  } catch (error) {
    console.error('Error fetching configuration:', error);
    throw error;
  }
};

// For API configuration specifically
export const getApiConfig = async () => {
  try {
    console.log('Fetching API configuration...');
    const response = await axios.get('/api/config'); // api-config endpoint
    console.log('API Configuration fetched:', response.data);
    return response;
  } catch (error) {
    console.error('Error fetching API configuration:', error);
    throw error;
  }
};

export const updateApiConfig = async (config) => {
  try {
    console.log('Updating API configuration with data:', config);
    const response = await axios.post('/api/config', config);
    console.log('API Configuration update response:', response.data);
    return response;
  } catch (error) {
    console.error('Error updating API configuration:', error);
    throw error;
  }
};

export const updateConfig = async (config) => {
  try {
    console.log('Updating configuration with data:', config);
    const response = await axios.post('/api/system-config', config);
    console.log('Configuration update response:', response.data);
    return response;
  } catch (error) {
    console.error('Error updating configuration:', error);
    throw error;
  }
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

const apiCall = (endpoint) => {
  return fetch(endpoint)
}