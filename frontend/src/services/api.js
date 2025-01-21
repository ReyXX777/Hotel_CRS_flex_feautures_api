import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json', // Added default headers
  },
});

// Add a request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log('Request sent to:', config.url); // Log outgoing requests
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Add a response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('Response error:', error.response.data); // Log response errors
    } else {
      console.error('Network error:', error.message); // Log network errors
    }
    return Promise.reject(error);
  }
);

export default api;
