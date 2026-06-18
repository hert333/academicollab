// frontend/src/hooks/useAuth.js (or .jsx)
import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be executed inside an AuthProvider element tree.');
  }
  return context;
};