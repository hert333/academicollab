import React, { useState, useEffect } from 'react';
import axios from 'axios';

// Environment variable consumption matching professional IT orchestration standards
const API_BASE_URL = window._env_?.VITE_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function UserManagementDashboard() {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processingId, setProcessingId] = useState(null);

  // Structural context helper to extract verification signatures
  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      }
    };
  };

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Parallel execution matrix optimization
      const [usersResponse, rolesResponse] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/users/`, getAuthHeaders()),
        axios.get(`${API_BASE_URL}/api/roles/`, getAuthHeaders())
      ]);
      setUsers(usersResponse.data);
      setRoles(rolesResponse.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'System initialization failure. Verify admin authorization states.');
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId, newRoleId) => {
    // Blocks dual-submission network hazards
    setProcessingId(userId);
    setError(null);

    try {
      const payload = { role: newRoleId ? parseInt(newRoleId, 10) : null };
      const response = await axios.patch(
        `${API_BASE_URL}/api/users/${userId}/`, 
        payload, 
        getAuthHeaders()
      );

      // Secure local state synchronization without requiring global tree re-fetch
      setUsers(prevUsers => 
        prevUsers.map(user => 
          user.id === userId ? { ...user, role: response.data.role, role_details: response.data.role_details } : user
        )
      );
    } catch (err) {
      const backendError = err.response?.data?.role || err.response?.data?.detail;
      setError(backendError || 'Mutation execution aborted by security boundary rules.');
      // Reload core matrix if internal system variance occurred
      fetchInitialData();
    } finally {
      setProcessingId(null);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-slate-400 bg-slate-950 min-h-screen font-sans flex items-center">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin"></div>
          <h3 className="text-sm font-medium">Resolving system telemetry frameworks...</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in font-sans">
      {/* Structural Title Header Grid */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white mb-1">Identity & RBAC Access Matrix</h1>
          <p className="text-xs text-slate-400">Track registration paths, analyze core user states, and monitor cluster connectivity.</p>
        </div>
        
        <button 
          onClick={fetchInitialData}
          className="px-4 py-2 rounded-lg text-xs font-bold tracking-wide uppercase bg-slate-950 border border-slate-800 text-slate-200 hover:text-white hover:border-indigo-500/50 hover:bg-slate-900 transition-all font-mono shrink-0"
        >
          SYNC_STATE
        </button>
      </div>

      {/* Exception Error Notification Banner */}
      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-900/60 text-rose-400 rounded-lg text-xs font-medium">
          <span className="font-bold uppercase tracking-wider text-[10px] bg-rose-900/50 px-1.5 py-0.5 rounded mr-2">EXECUTION_PANIC</span>
          {typeof error === 'object' ? JSON.stringify(error) : error}
        </div>
      )}

      {/* Modern Slate Database Data Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/50 text-[11px] font-bold uppercase tracking-wider text-slate-400 select-none">
                <th className="py-4 px-6">User ID</th>
                <th className="py-4 px-6">Identity Name</th>
                <th className="py-4 px-6">Email Vector</th>
                <th className="py-4 px-6">Active State</th>
                <th className="py-4 px-6 text-right">Assigned Hierarchical Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-sm text-slate-300">
              {users.map(user => {
                const isProcessing = processingId === user.id;
                
                return (
                  <tr 
                    key={user.id} 
                    className={`hover:bg-slate-800/20 transition-colors duration-150 ${
                      isProcessing ? 'opacity-40 pointer-events-none bg-indigo-950/10' : ''
                    }`}
                  >
                    <td className="py-4 px-6 font-mono text-xs text-slate-500 font-bold">#{user.id}</td>
                    <td className="py-4 px-6 font-semibold text-white">{user.username}</td>
                    <td className="py-4 px-6 text-slate-400 font-mono text-xs">{user.email}</td>
                    <td className="py-4 px-6">
                      <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded uppercase tracking-wider border ${
                        user.is_active 
                          ? 'bg-emerald-950/40 text-emerald-400 border-emerald-900/40' 
                          : 'bg-rose-950/40 text-rose-400 border-rose-900/40'
                      }`}>
                        {user.is_active ? 'ACTIVE' : 'SUSPENDED'}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <select
                        value={user.role || ''}
                        disabled={isProcessing}
                        onChange={(e) => handleRoleChange(user.id, e.target.value)}
                        className={`bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500 transition-all font-medium select-none ${
                          isProcessing ? 'cursor-not-allowed opacity-50 bg-slate-900' : 'cursor-pointer hover:border-slate-700'
                        }`}
                      >
                        <option value="" className="bg-slate-950 text-slate-500">Unassigned (Null Role)</option>
                        {roles.map(role => (
                          <option key={role.id} value={role.id} className="bg-slate-950 text-slate-300">
                            {role.name}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                );
              })}

              {users.length === 0 && !error && (
                <tr>
                  <td colSpan="5" className="py-12 px-6 text-center text-xs text-slate-500 font-medium select-none">
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