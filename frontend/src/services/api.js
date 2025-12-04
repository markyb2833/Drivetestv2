import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  // Drives
  getDrives: async () => {
    const response = await api.get('/drives');
    return response.data;
  },

  getDrive: async (serial) => {
    const response = await api.get(`/drives/${serial}`);
    return response.data;
  },

  startTest: async (serial, testType = 'smart') => {
    const response = await api.post(`/drives/${serial}/test`, { test_type: testType });
    return response.data;
  },

  getTestStatus: async (serial) => {
    const response = await api.get(`/drives/${serial}/test`);
    return response.data;
  },

  cancelTest: async (serial) => {
    const response = await api.delete(`/drives/${serial}/test`);
    return response.data;
  },

  // Bay Map
  getBayMap: async () => {
    const response = await api.get('/bay-map');
    return response.data;
  },

  getBayDetails: async (bayNumber) => {
    const response = await api.get(`/bay-map/${bayNumber}`);
    return response.data;
  },

  // Session
  getSession: async () => {
    const response = await api.get('/session');
    return response.data;
  },

  createSession: async (poNumber, userName) => {
    const response = await api.post('/session', {
      po_number: poNumber,
      user_name: userName,
    });
    return response.data;
  },

  updatePONumber: async (poNumber) => {
    const response = await api.put('/session/po', {
      po_number: poNumber,
    });
    return response.data;
  },

  // Settings
  getSettings: async (category) => {
    const params = category ? { category } : {};
    const response = await api.get('/settings', { params });
    return response.data;
  },

  getSetting: async (key) => {
    const response = await api.get(`/settings/${key}`);
    return response.data;
  },

  updateSetting: async (key, value, category = 'system') => {
    const response = await api.put(`/settings/${key}`, {
      value,
      category,
    });
    return response.data;
  },

  // Configuration
  getTestConfig: async () => {
    const response = await api.get('/config/tests');
    return response.data;
  },

  updateTestConfig: async (config) => {
    const response = await api.put('/config/tests', config);
    return response.data;
  },

  getBackplaneConfig: async () => {
    const response = await api.get('/config/backplane');
    return response.data;
  },

  updateBackplaneConfig: async (config) => {
    const response = await api.put('/config/backplane', config);
    return response.data;
  },

  // System
  getSystemStatus: async () => {
    const response = await api.get('/system/status');
    return response.data;
  },
};

