import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000/api/',
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Mutex lock configurations to protect concurrent thread/asynchronous pipelines
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Structural Interceptor for automatic JWT token payload distribution
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

// FIXED: Asynchronous Response Interceptor for sliding token refresh execution
API.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Guard statement: Check if error is not a 401 or if request has already been retried
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    // Guard statement: Avoid infinite looping if the refresh endpoint itself rejects
    if (originalRequest.url.includes('auth/token/refresh/')) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // Queue requests while token generation runs concurrently
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

      // Bypass instance interceptors by utilizing direct axios call to prevent locking deadlocks
      const response = await axios.post('http://localhost:8000/api/auth/token/refresh/', {
        refresh: refreshToken,
      });

      const newAccessToken = response.data.access;
      localStorage.setItem('access_token', newAccessToken);

      processQueue(null, newAccessToken);
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
      
      return API(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      
      // Evict corrupted/expired tokens to drop state cleanly back to portal landing zones
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      
      // Force page relocation if active context binding drops completely
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