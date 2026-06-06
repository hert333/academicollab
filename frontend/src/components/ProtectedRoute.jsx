import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const ROLE_HIERARCHY = {
  'Student': 1,
  'Project Manager': 2,
  'Supervisor': 3,
  'Admin': 4
};

const ProtectedRoute = ({ allowedRoles }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>Verifying Structural Credentials...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  const userRoleString = user.role_details?.name || user.role;
  const userWeight = ROLE_HIERARCHY[userRoleString] || 0;
  
  const hasAccess = allowedRoles.some(role => {
    if (userRoleString === 'Admin' || userRoleString === 'Supervisor') return true;
    
    const requiredWeight = ROLE_HIERARCHY[role] || 0;
    return userWeight >= requiredWeight;
  });

  if (!hasAccess) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;