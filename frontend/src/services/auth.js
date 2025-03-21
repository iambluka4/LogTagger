import axios from 'axios';
import { API_BASE } from './api';

// Storage keys
const ACCESS_TOKEN_KEY = 'logtagger_access_token';
const REFRESH_TOKEN_KEY = 'logtagger_refresh_token';
const USER_KEY = 'logtagger_user';

// Set Authorization header for all requests
export const setAuthHeader = (token) => {
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete axios.defaults.headers.common['Authorization'];
  }
};

// Login user
export const loginUser = async (username, password) => {
  try {
    const response = await axios.post(`${API_BASE}/api/auth/login`, {
      username,
      password,
    });
    
    // Store tokens and user info
    localStorage.setItem(ACCESS_TOKEN_KEY, response.data.access_token);
    localStorage.setItem(REFRESH_TOKEN_KEY, response.data.refresh_token);
    localStorage.setItem(USER_KEY, JSON.stringify(response.data.user));
    
    // Set auth header for future requests
    setAuthHeader(response.data.access_token);
    
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Login failed' };
  }
};

// Logout user
export const logoutUser = () => {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  setAuthHeader(null);
};

// Check if user is authenticated
export const isAuthenticated = () => {
  return !!localStorage.getItem(ACCESS_TOKEN_KEY);
};

// Get current user info
export const getCurrentUser = () => {
  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;
  
  try {
    return JSON.parse(userStr);
  } catch (e) {
    return null;
  }
};

// Get stored token
export const getToken = () => {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
};

// Refresh token
export const refreshToken = async () => {
  try {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }
    
    const response = await axios.post(`${API_BASE}/api/auth/refresh`, {}, {
      headers: {
        'Authorization': `Bearer ${refreshToken}`
      }
    });
    
    localStorage.setItem(ACCESS_TOKEN_KEY, response.data.access_token);
    setAuthHeader(response.data.access_token);
    
    return response.data.access_token;
  } catch (error) {
    logoutUser();
    throw error;
  }
};

// Initialize authentication from stored token
export const initAuth = () => {
  const token = getToken();
  if (token) {
    setAuthHeader(token);
    return true;
  }
  return false;
};

// Check if user has a specific role
export const hasRole = (requiredRole) => {
  const user = getCurrentUser();
  return user && user.role === requiredRole;
};

// Check if user is admin
export const isAdmin = () => {
  return hasRole('admin');
};

// Check if user is analyst or admin
export const isAnalyst = () => {
  const user = getCurrentUser();
  return user && (user.role === 'analyst' || user.role === 'admin');
};
