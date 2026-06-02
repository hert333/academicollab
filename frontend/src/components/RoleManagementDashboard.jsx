import React, { useState, useEffect } from 'react';
import API from '../services/api';

// Harmonized option targets matching absolute backend database keys
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

      // RESTful structural data exchange payload submission
      await API.patch(`users/${userId}/`, {
        role_name: targetRole, // Explicit string mapping for serialization engines
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
      <div className="p-8 text-slate-400 bg-slate-950 min-h-screen font-sans flex items-center">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin"></div>
          <h3 className="text-sm font-medium">Hydrating System Identity Tree Matrix...</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in font-sans">
      {/* View Header Matrix */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white mb-1">Hierarchical Role Management Console</h1>
        <p className="text-xs text-slate-400">Map security privileges, modify group access tiers, and manage RBAC tokens across system profiles.</p>
      </div>

      {/* Execution Diagnostics Notification Hub */}
      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-900/60 text-rose-400 rounded-lg text-xs font-medium flex items-center gap-2">
          <span className="font-bold uppercase tracking-wider text-[10px] bg-rose-900/50 px-1.5 py-0.5 rounded">System Error</span>
          {error}
        </div>
      )}

      {successMessage && (
        <div className="p-4 bg-emerald-950/40 border border-emerald-900/60 text-emerald-400 rounded-lg text-xs font-medium flex items-center gap-2">
          <span className="font-bold uppercase tracking-wider text-[10px] bg-emerald-900/50 px-1.5 py-0.5 rounded">Status Check</span>
          {successMessage}
        </div>
      )}

      {/* High-Contrast Management Grid Layout */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 bg-slate-900/50 text-[11px] font-bold uppercase tracking-wider text-slate-400 select-none">
                <th className="py-4 px-6">User ID</th>
                <th className="py-4 px-6">Identity / Profile</th>
                <th className="py-4 px-6">Email Contact</th>
                <th className="py-4 px-6">Assigned Hierarchical Role</th>
                <th className="py-4 px-6 text-right">Access Control Adjustments</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-sm text-slate-300">
              {users.map((user) => {
                const currentRole = user.role_details?.name || user.role || 'Unassigned';
                const isPending = actionPendingId === user.id;

                return (
                  <tr 
                    key={user.id} 
                    className={`hover:bg-slate-800/20 transition-colors duration-150 ${
                      isPending ? 'opacity-40 pointer-events-none bg-indigo-950/10' : ''
                    }`}
                  >
                    <td className="py-4 px-6 font-mono text-xs text-slate-500 font-bold">#{user.id}</td>
                    <td className="py-4 px-6 font-semibold text-white">{user.username}</td>
                    <td className="py-4 px-6 text-slate-400 font-mono text-xs">{user.email}</td>
                    <td className="py-4 px-6">
                      <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase tracking-wide border ${
                        currentRole === 'Admin' || currentRole === 'Supervisor' 
                          ? 'bg-rose-950/40 text-rose-400 border-rose-900/60' 
                          : currentRole === 'Project Manager' 
                            ? 'bg-indigo-950/40 text-indigo-400 border-indigo-900/60' 
                            : 'bg-slate-950 text-slate-400 border-slate-800'
                      }`}>
                        {currentRole}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <select
                        value={currentRole}
                        disabled={isPending}
                        onChange={(e) => handleRoleChange(user.id, e.target.value)}
                        className={`bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500 transition-all font-medium select-none ${
                          isPending ? 'cursor-not-allowed opacity-50 bg-slate-900' : 'cursor-pointer hover:border-slate-700'
                        }`}
                      >
                        {ROLE_OPTIONS.map((opt) => (
                          <option key={opt} value={opt} className="bg-slate-950 text-slate-300">
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