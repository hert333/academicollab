import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import RoleManagementDashboard from './components/RoleManagementDashboard';
import Login from './components/Login';

const UnauthorizedPlaceholder = () => (
  <div style={{ padding: 40, fontFamily: 'sans-serif', color: '#dc3545' }}>
    <h2>403 - Structural Access Denied</h2>
    <p>Your current assigned identity weight is barred from this node context path.</p>
  </div>
);

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public Routing Context Profiles */}
          <Route path="/login" element={<Login />} />
          <Route path="/unauthorized" element={<UnauthorizedPlaceholder />} />

          {/* Secure Routing Nodes - Root Administrator Authority Required */}
          <Route element={<ProtectedRoute allowedRoles={['Admin']} />}>
            <Route path="/admin/roles" element={<RoleManagementDashboard />} />
          </Route>

          {/* Fallback Entry Pointer Verification */}
          <Route path="*" element={<Navigate to="/admin/roles" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}