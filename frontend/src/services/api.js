import axios from 'axios';

// Leverage Vite environment variable schema with safe local network fallback configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const API = axios.create({
  baseURL: `${API_BASE_URL}/api/`,
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json'
  }
});

let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else {
      promise.resolve(token);
    }
  });
  failedQueue = [];
};

// Request Interceptor: Uniformly inject active authorization vector states
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Manage sliding window token rotation and request queue holding
API.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    if (originalRequest.url.includes('auth/token/refresh/')) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject });
      })
        .then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return API(originalRequest);
        })
        .catch((err) => Promise.reject(err));
    }

    originalRequest._retry = true;
    isRefreshing = true;

    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('Refresh token asset omitted from client storage.');
      }

      // Explicit isolated instance configuration prevents cascading interceptor recursion
      const response = await axios.post(`${API_BASE_URL}/api/auth/token/refresh/`, {
        refresh: refreshToken,
      });

      const newAccessToken = response.data.access;
      localStorage.setItem('access_token', newAccessToken);

      processQueue(null, newAccessToken);
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      
      return API(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default API;