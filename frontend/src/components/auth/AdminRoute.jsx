import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';

// Simple structural hook lookup - swap with your actual global AuthContext if configured
export default function AdminRoute() {
  const token = localStorage.getItem('access_token');
  
  // Base64 decode the payload segment of the SimpleJWT token signature to check client-side claims
  const getIsAdminFromToken = () => {
    if (!token) return false;
    try {
      const payloadBase64 = token.split('.')[1];
      const decodedPayload = JSON.parse(atob(payloadBase64));
      // Matches the 'role' claim injected into the JWT structure from the backend serialization layer
      return decodedPayload.role === 'Admin' || decodedPayload.is_superuser === true;
    } catch (e) {
      return false;
    }
  };

  const isAdmin = getIsAdminFromToken();

  // Enforce zero-trust client-side boundary conditions by dropping unauthorized sessions to entrypoints
  return isAdmin ? <Outlet /> : <Navigate to="/unauthorized" replace />;
}