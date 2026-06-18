// frontend/src/components/ProtectedRoute.jsx
import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
// FIX: Point directly to the specialized hooks file using a named import
import { useAuth } from '../hooks/useAuth'; 

const ROLE_HIERARCHY = {
  'STUDENT': 1,
  'PROJECT MANAGER': 2,
  'SUPERVISOR': 3,
  'ADMIN': 4
};

const ProtectedRoute = ({ allowedRoles }) => {
  const { user, loading } = useAuth();

  // 1. Structural Identity Loading Guard Clause
  if (loading) {
    return (
      <div className="p-6 font-mono text-xs text-slate-500 bg-slate-950 min-h-screen flex items-center justify-center">
        Verifying Structural Credentials...
      </div>
    );
  }

  // 2. Unauthenticated Boundary Catch
  if (!user) {
    return <Navigate to="/login" replace />;
  }

  // 3. Normalize User Role to Match Unified DB States
  const rawRole = user.role_details?.name || user.role || '';
  const userRoleString = rawRole.toUpperCase();
  const userWeight = ROLE_HIERARCHY[userRoleString] || 0;
  
  // 4. Secure Evaluation Engine
  const hasAccess = (() => {
    if (userRoleString === 'ADMIN') return true;

    const normalizedAllowed = allowedRoles.map(r => r.toUpperCase());

    return normalizedAllowed.some(requiredRole => {
      const requiredWeight = ROLE_HIERARCHY[requiredRole] || 0;
      
      if (requiredRole === 'ADMIN' && userRoleString !== 'ADMIN') return false;

      return userRoleString === requiredRole || userWeight >= requiredWeight;
    });
  })();

  // 5. Enforce Boundary Access Verdict
  if (!hasAccess) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
};

export default ProtectedRoute;