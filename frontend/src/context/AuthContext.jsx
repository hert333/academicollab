import React, { createContext, useState, useContext, useEffect } from 'react';
import API from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const verifyUser = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        // Headers are injected automatically by the intercepted client instance
        const response = await API.get('auth/user-profile/');
        setUser(response.data);
      } catch (err) {
        console.error("Hydration state verification failed:", err.response?.data || err.message);
        logout();
      } finally {
        setLoading(false);
      }
    };
    verifyUser();
  }, []);

  const login = async (username, password) => {
    const response = await API.post('auth/token/', { username, password });
    
    if (!response.data || !response.data.access || !response.data.refresh) {
      throw new Error("Invalid token payload structure returned from server.");
    }

    const { access, refresh } = response.data;
    
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    
    try {
      const profileResponse = await API.get('auth/user-profile/');
      setUser(profileResponse.data);
      return profileResponse.data; 
    } catch (profileError) {
      logout();
      throw profileError;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, setUser }}>
      {loading ? (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', fontFamily: 'sans-serif', color: '#666' }}>
          Loading System Security Extensions...
        </div>
      ) : (
        children
      )}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);