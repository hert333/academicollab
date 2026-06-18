// frontend/src/components/RoleManagementDashboard.jsx
import React, { useState, useEffect } from 'react';
import API from '../services/api';

export default function RoleManagementDashboard() {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [actionPendingId, setActionPendingId] = useState(null);

  useEffect(() => {
    let isMounted = true;

    const fetchDirectoryMetadata = async () => {
      try {
        setLoading(true);
        setError(null);

        // Parallel queries leverage global axios interceptor automatically
        const [usersResponse, rolesResponse] = await Promise.all([
          API.get('auth/users/'),
          API.get('auth/roles/')
        ]);

        if (!isMounted) return;

        if (Array.isArray(usersResponse.data)) {
          setUsers(usersResponse.data);
        } else {
          throw new Error('Invalid structural data shape received from directory engine.');
        }

        if (Array.isArray(rolesResponse.data)) {
          setRoles(rolesResponse.data);
        }
      } catch (err) {
        console.error("Directory hydration error context:", err);
        if (isMounted) {
          setError(err.response?.data?.detail || err.message || 'Failed to aggregate system user data registries.');
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchDirectoryMetadata();
    return () => { isMounted = false; };
  }, []);

  const handleRoleChange = async (userId, targetRoleId) => {
    const roleIdInt = parseInt(targetRoleId, 10);
    if (isNaN(roleIdInt)) return;

    try {
      setActionPendingId(userId);
      setError(null);
      setSuccessMessage(null);

      // Execute restful patch directly utilizing managed global interceptor context
      const response = await API.patch(`auth/users/${userId}/`, {
        role: roleIdInt
      });

      const updatedRoleDetails = response.data.role_details || 
                                 roles.find(r => r.id === roleIdInt) || 
                                 { name: 'Updated Role' };

      setUsers((prevUsers) =>
        prevUsers.map((user) =>
          user.id === userId
            ? { ...user, role: roleIdInt, role_details: updatedRoleDetails }
            : user
        )
      );

      setSuccessMessage(`User ID #${userId} structural access elevated to ${updatedRoleDetails.name} successfully.`);
    } catch (err) {
      console.error('Role modification mutation fault:', err.response?.data);
      setError(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Database transaction rejected alteration.');
    } finally {
      setActionPendingId(null);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-slate-400 bg-slate-950 min-h-screen font-sans flex items-center justify-center">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin"></div>
          <h3 className="text-xs font-mono tracking-wider">Hydrating System Identity Tree Matrix...</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 font-sans p-6 bg-slate-950 min-h-screen text-slate-100">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white mb-1">Hierarchical Role Management Console</h1>
        <p className="text-sm text-slate-400">Map security privileges, modify group access tiers, and manage RBAC tokens across system profiles.</p>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/40 border border-rose-800/60 text-rose-400 rounded-lg text-xs font-mono flex items-center gap-2">
          <span className="font-sans font-bold uppercase tracking-wider text-[10px] bg-rose-900 px-1.5 py-0.5 rounded text-white">System Error</span>
          {error}
        </div>
      )}

      {successMessage && (
        <div className="p-4 bg-emerald-950/40 border border-emerald-800/60 text-emerald-400 rounded-lg text-xs font-mono flex items-center gap-2">
          <span className="font-sans font-bold uppercase tracking-wider text-[10px] bg-emerald-900 px-1.5 py-0.5 rounded text-white">Status Check</span>
          {successMessage}
        </div>
      )}

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
                const currentRoleName = user.role_details?.name || 'Unassigned';
                const currentRoleId = user.role || '';
                const isPending = actionPendingId === user.id;

                return (
                  <tr 
                    key={`user-row-${user.id}`} 
                    className={`hover:bg-slate-800/20 transition-colors duration-150 ${
                      isPending ? 'opacity-40 pointer-events-none bg-indigo-950/10' : ''
                    }`}
                  >
                    <td className="py-4 px-6 font-mono text-xs text-slate-500 font-bold">#{user.id}</td>
                    <td className="py-4 px-6 font-semibold text-white">{user.username}</td>
                    <td className="py-4 px-6 text-slate-400 font-mono text-xs">{user.email}</td>
                    <td className="py-4 px-6">
                      <span className={`text-[10px] font-bold px-2.5 py-1 rounded uppercase tracking-wide border ${
                        currentRoleName.toUpperCase() === 'ADMIN' || currentRoleName.toUpperCase() === 'SUPERVISOR' 
                          ? 'bg-rose-950/40 text-rose-400 border-rose-900/60' 
                          : currentRoleName.toUpperCase() === 'PROJECT MANAGER' 
                            ? 'bg-indigo-950/40 text-indigo-400 border-indigo-900/60' 
                            : 'bg-slate-950 text-slate-400 border-slate-800'
                      }`}>
                        {currentRoleName}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right">
                      <select
                        value={currentRoleId}
                        disabled={isPending}
                        onChange={(e) => handleRoleChange(user.id, e.target.value)}
                        className={`bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:border-indigo-500 transition-all font-medium select-none ${
                          isPending ? 'cursor-not-allowed opacity-50 bg-slate-900' : 'cursor-pointer hover:border-slate-700'
                        }`}
                      >
                        <option value="" disabled>Choose Security Context...</option>
                        {roles.map((opt) => (
                          <option key={`opt-${opt.id}`} value={opt.id} className="bg-slate-950 text-slate-300">
                            Assign {opt.name} Permissions
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                );
              })}

              {users.length === 0 && !error && (
                <tr>
                  <td colSpan="5" className="py-12 px-6 text-center text-xs text-slate-500 font-mono select-none">
                    Zero user registrations detected in active database context partition.
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