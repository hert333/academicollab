import React, { useState, useEffect } from 'react';
import API from '../services/api';

// FIXED: Harmonized option targets with absolute backend database keys
const ROLE_OPTIONS = ['Student', 'Project Manager', 'Supervisor', 'Admin'];

export default function RoleManagementDashboard() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [actionPendingId, setActionPendingId] = useState(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await API.get('users/');
      if (Array.isArray(response.data)) {
        setUsers(response.data);
      } else {
        throw new Error('Invalid structural data shape returned from API.');
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to aggregate system user data registries.');
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId, targetRole) => {
    if (!ROLE_OPTIONS.includes(targetRole)) {
      setError(`Rejected mutation assignment: '${targetRole}' is out of bounds.`);
      return;
    }

    try {
      // Lock execution interface to block double-submit mutations
      setActionPendingId(userId);
      setError(null);
      setSuccessMessage(null);

      // FIXED: Swapped out non-existent custom action for standard RESTful resource route
      const response = await API.patch(`users/${userId}/`, {
        role_name: targetRole, // Explicit string name mapping for downstream serialization engines
      });

      // Optimistic client array update matching real-time synchronization states
      setUsers((prevUsers) =>
        prevUsers.map((user) => (user.id === userId ? { ...user, role: targetRole } : user))
      );
      
      setSuccessMessage(`User ID #${userId} structural access elevated to ${targetRole} successfully.`);
    } catch (err) {
      console.error('Role modification fault:', err.response?.data);
      setError(err.response?.data?.detail || 'Database transaction rejected the requested assignment alteration.');
    } finally {
      // Release interaction execution lock
      setActionPendingId(null);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '30px', fontFamily: 'sans-serif', color: '#666' }}>
        <h3>Loading System Identity Tree Matrix...</h3>
      </div>
    );
  }

  return (
    <div style={{ padding: '40px', fontFamily: 'sans-serif', backgroundColor: '#f9f9f9', minHeight: '100vh' }}>
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        <h2 style={{ color: '#1a1a1a', borderBottom: '2px solid #eaeaea', paddingBottom: '15px' }}>
          Hierarchical Role Management Console
        </h2>

        {error && (
          <div style={{ padding: '15px', backgroundColor: '#ffebe9', color: '#ce3c2e', borderRadius: '6px', marginBottom: '20px', border: '1px solid #ffc8c4' }}>
            <strong>System Error:</strong> {error}
          </div>
        )}

        {successMessage && (
          <div style={{ padding: '15px', backgroundColor: '#e6f6ec', color: '#1f7a42', borderRadius: '6px', marginBottom: '20px', border: '1px solid #c3edd5' }}>
            <strong>Status Check:</strong> {successMessage}
          </div>
        )}

        <div style={{ backgroundColor: '#ffffff', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)', overflow: 'hidden' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
            <thead>
              <tr style={{ backgroundColor: '#f1f3f5', color: '#495057', borderBottom: '1px solid #dee2e6' }}>
                <th style={{ padding: '15px' }}>User ID</th>
                <th style={{ padding: '15px' }}>Identity / Profile</th>
                <th style={{ padding: '15px' }}>Email Contact</th>
                <th style={{ padding: '15px' }}>Assigned Hierarchical Role</th>
                <th style={{ padding: '15px' }}>Access Control Adjustments</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => {
                const currentRole = user.role_details?.name || user.role || 'Unassigned';
                return (
                  <tr key={user.id} style={{ borderBottom: '1px solid #f1f3f5', transition: 'background 0.2s' }}>
                    <td style={{ padding: '15px', fontWeight: 'bold', color: '#666' }}>#{user.id}</td>
                    <td style={{ padding: '15px', color: '#212529', fontWeight: '500' }}>{user.username}</td>
                    <td style={{ padding: '15px', color: '#495057' }}>{user.email}</td>
                    <td style={{ padding: '15px' }}>
                      <span style={{ 
                        padding: '6px 12px', 
                        borderRadius: '20px', 
                        fontSize: '12px', 
                        fontWeight: 'bold',
                        backgroundColor: currentRole === 'Admin' || currentRole === 'Supervisor' ? '#fde8e8' : currentRole === 'Project Manager' ? '#e1effe' : '#e5e7eb',
                        color: currentRole === 'Admin' || currentRole === 'Supervisor' ? '#9b1c1c' : currentRole === 'Project Manager' ? '#1e429f' : '#374151'
                      }}>
                        {currentRole}
                      </span>
                    </td>
                    <td style={{ padding: '15px' }}>
                      <select
                        value={currentRole}
                        disabled={actionPendingId === user.id}
                        onChange={(e) => handleRoleChange(user.id, e.target.value)}
                        style={{
                          padding: '8px 12px',
                          borderRadius: '6px',
                          border: '1px solid #ccd0d4',
                          backgroundColor: actionPendingId === user.id ? '#e9ecef' : '#ffffff',
                          cursor: actionPendingId === user.id ? 'not-allowed' : 'pointer',
                          outline: 'none'
                        }}
                      >
                        {ROLE_OPTIONS.map((opt) => (
                          <option key={opt} value={opt}>
                            Assign {opt} Permissions
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                );
              })}
              {users.length === 0 && !error && (
                <tr>
                  <td colSpan="5" style={{ padding: '30px', textAlign: 'center', color: '#868e96' }}>
                    Zero user registrations detected in database context.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}