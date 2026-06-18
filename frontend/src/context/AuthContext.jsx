// frontend/src/context/AuthContext.jsx
import React, { createContext, useState, useEffect, useContext } from 'react';
import API from '../services/api';

export const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setUser(null);
  };

  useEffect(() => {
    let isMounted = true;

    const verifyUser = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) {
        if (isMounted) setLoading(false);
        return;
      }
      try {
        const response = await API.get('auth/user-profile/');
        if (isMounted) {
          setUser(response.data);
        }
      } catch (err) {
        console.error("Hydration state verification failed:", err.response?.data || err.message);
        if (isMounted) {
          logout();
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    verifyUser();

    return () => {
      isMounted = false;
    };
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
      const profileResponse = await API.get('auth/user-profile/', {
        headers: {
          Authorization: `Bearer ${access}`
        }
      });
      setUser(profileResponse.data);
      return profileResponse.data; 
    } catch (profileError) {
      logout();
      throw profileError;
    }
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

// =========================================================================
// CRITICAL IMPLEMENTATION PATCH: EXPORT NAMED HOOK FOR DECOUPLED VIEWS
// =========================================================================
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be executed within an explicit AuthProvider wrapper boundary.');
  }
  return context;
};