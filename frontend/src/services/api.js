import axios from "axios";

// API Base URL
export const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:5000";

// Create an axios instance
const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

// Видаляємо будь-які перевірки автентифікації в interceptors
apiClient.interceptors.response.use(
  response => response,
  error => {
    // Видаляємо перенаправлення на логін при отриманні 401 помилки
    const errorResponse = {
      message: error.response?.data?.message || error.message || 'Unknown error',
      status: error.response?.status,
      timestamp: new Date().toISOString(),
      url: error.config?.url,
      method: error.config?.method
    };
    
    // Логуємо помилку для відлагодження
    console.error("API Error:", errorResponse);
    
    // Продовжуємо показувати помилку, але не перенаправляємо на логін
    throw error;
  }
);

// Оптимізуємо логування
export const enableApiLogging = (enable = true) => {
  if (enable && !window._apiLoggingEnabled) {
    window._apiLoggingEnabled = true;
    
    // Уникаємо дублювання перехоплювачів
    const requestInterceptor = apiClient.interceptors.request.use(config => {
      console.log('API Request:', {
        url: config.url,
        method: config.method,
        data: config.data,
        params: config.params
      });
      return config;
    });
    
    const responseInterceptor = apiClient.interceptors.response.use(
      response => {
        console.log('API Response:', {
          status: response.status,
          url: response.config.url,
          data: response.data
        });
        return response;
      },
      error => {
        console.error('API Error:', {
          status: error.response?.status,
          url: error.config?.url,
          message: error.response?.data?.message || error.message
        });
        return Promise.reject(error);
      }
    );
    
    // Зберігаємо ідентифікатори для можливого відключення
    window._apiInterceptors = {
      request: requestInterceptor,
      response: responseInterceptor
    };
  } else if (!enable && window._apiLoggingEnabled) {
    // Відключаємо логування за потреби
    apiClient.interceptors.request.eject(window._apiInterceptors.request);
    apiClient.interceptors.response.eject(window._apiInterceptors.response);
    window._apiLoggingEnabled = false;
  }
  
  return apiClient;
};

// Увімкніть це тільки для розробки
if (process.env.NODE_ENV === 'development') {
  enableApiLogging();
}

// Покращуємо normalizeEventData для безпечного доступу до вкладених властивостей
export const normalizeEventData = (event) => {
  if (!event) return null;
  
  const result = { ...event };
  
  // Стандартизація формату для manual_tags
  if (!result.labels) {
    result.labels = {};
  }
  
  // Переконуємося, що labels.manual_tags завжди масив
  if (!result.labels.manual_tags) {
    result.labels.manual_tags = [];
  } else if (typeof result.labels.manual_tags === 'string') {
    result.labels.manual_tags = result.labels.manual_tags.trim() 
      ? result.labels.manual_tags.split(',').map(tag => tag.trim()) 
      : [];
  }
  
  // Створюємо окремі зручні властивості для common values
  result.manual_tags = result.labels.manual_tags || [];
  result.true_positive = result.labels.true_positive;
  result.attack_type = result.labels.attack_type;
  
  // Додаємо безпечну перевірку наявності ml_labels
  result.has_ml_suggestions = Boolean(
    result.labels && 
    result.labels.ml_labels && 
    Object.keys(result.labels.ml_labels).length > 0
  );
  
  return result;
};

// Configuration
export const getConfig = async () => {
  try {
    console.log('Fetching configuration...');
    const response = await apiClient.get('/api/system-config');
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
    const response = await apiClient.get('/api/config');
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
    const response = await apiClient.post('/api/config', config);
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
    const response = await apiClient.post('/api/system-config', config);
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

// Функція для обробки відповіді з подіями
const processEventsResponse = (response) => {
  if (response.data && response.data.events) {
    response.data.events = response.data.events.map(normalizeEventData);
  }
  return response;
};

export const getEvents = async (params = {}) => {
  const response = await apiClient.get('/api/events', { params });
  return processEventsResponse(response);
};

export const getEvent = async (eventId) => {
  const response = await apiClient.get(`/api/events/${eventId}`);
  response.data = normalizeEventData(response.data);
  return response;
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
export const getDashboardStats = async (params = {}) => {
  try {
    const response = await apiClient.get('/api/dashboard/stats', { params });
    return response;
  } catch (error) {
    console.warn('Error fetching dashboard stats:', error);
    // Повертаємо фіктивні дані для уникнення поломки UI
    return { 
      data: {
        total_events: 0,
        events_today: 0,
        labeled_events: 0,
        true_positives: 0,
        siem_sources: []
      } 
    };
  }
};

export const getTopAttackTypes = async (params = {}) => {
  try {
    const response = await apiClient.get('/api/dashboard/top-attacks', { params });
    return response;
  } catch (error) {
    console.warn('Error fetching top attack types:', error);
    return { data: [] };
  }
};

export const getEventTimeline = async (params = {}) => {
  try {
    const response = await apiClient.get('/api/dashboard/timeline', { params });
    return response;
  } catch (error) {
    console.warn('Error fetching event timeline:', error);
    return { data: [] };
  }
};

export const getSeverityDistribution = async () => {
  try {
    const response = await apiClient.get('/api/dashboard/severity');
    return response;
  } catch (error) {
    console.warn('Error fetching severity distribution:', error);
    return { 
      data: {
        low: 0,
        medium: 0,
        high: 0,
        critical: 0
      } 
    };
  }
};

export const getMitreDistribution = () => {
  return apiClient.get('/api/dashboard/mitre-distribution');
};

// ML Service API
export const getMLStatus = async () => {
  try {
    const response = await apiClient.get('/api/ml/status');
    return response;
  } catch (error) {
    console.error('Error getting ML status:', error);
    
    // Якщо помилка пов'язана з вимкненим ML, повертаємо структуровану відповідь
    if (error.response?.data?.message?.includes('disabled')) {
      return {
        data: {
          status: 'disabled',
          message: error.response.data.message
        }
      };
    }
    
    throw error;
  }
};

export const classifyEvent = async (eventId) => {
  try {
    return await apiClient.post(`/api/ml/classify/${eventId}`);
  } catch (error) {
    console.error(`Error classifying event ${eventId}:`, error);
    throw error;
  }
};

export const batchClassifyEvents = async (eventIds) => {
  if (!Array.isArray(eventIds) || eventIds.length === 0) {
    throw new Error('Invalid event IDs: must be a non-empty array');
  }
  
  try {
    return await apiClient.post('/api/ml/batch-classify', { event_ids: eventIds });
  } catch (error) {
    console.error('Error batch classifying events:', error);
    throw error;
  }
};

export const verifyEventLabel = (eventId, verificationData) => {
  return apiClient.post(`/api/ml/verify-label/${eventId}`, verificationData);
};

export const getMLMetrics = (limit = 10) => {
  return apiClient.get('/api/ml/metrics', { params: { limit } });
};

export const updateMLMetrics = (dateRange = {}) => {
  return apiClient.post('/api/ml/update-metrics', dateRange);
};

export const getUnverifiedEvents = (params = {}) => {
  return apiClient.get('/api/ml/unverified-events', { params });
};

// Перейменуйте функцію, щоб уникнути конфлікту імен

// Додаємо новий метод для перевірки здоров'я сервісів
export const checkServicesHealth = async () => {
  try {
    const response = await apiClient.get('/api/services/health');
    return response;
  } catch (error) {
    console.error('Error checking services health:', error);
    throw error;
  }
};

// Додаємо функцію для верифікації міток
export const verifyEventLabels = (eventId, verifiedLabels) => {
  return apiClient.post(`/api/events/${eventId}/verify-labels`, {
    verified_labels: verifiedLabels
  });
};