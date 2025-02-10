import axios from 'axios';

// Базова URL вашого backend
const API_BASE = "http://localhost:5000";

const getConfig = async () => {
  return axios.get(`${API_BASE}/api/config`);
};

const updateConfig = async (data) => {
  return axios.post(`${API_BASE}/api/config`, data);
};

const getAlerts = async () => {
  return axios.get(`${API_BASE}/api/alerts`);
};

const labelAlert = async (alertId, labelData) => {
  return axios.post(`${API_BASE}/api/alerts/${alertId}/label`, labelData);
};

const getUsers = async () => {
  return axios.get(`${API_BASE}/api/users`);
};

const createUser = async (data) => {
  return axios.post(`${API_BASE}/api/users`, data);
};

const deleteUser = async (userId) => {
  return axios.delete(`${API_BASE}/api/users/${userId}`);
};

export {
  getConfig,
  updateConfig,
  getAlerts,
  labelAlert,
  getUsers,
  createUser,
  deleteUser
};
