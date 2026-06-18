// frontend/src/components/UserManagementDashboard.jsx
import React, { useState, useEffect } from 'react';
import API from '../services/api';

export default function UserManagementDashboard() {
  const [users, setUsers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    role: '',
    project_id: ''
  });

  useEffect(() => {
    let isMounted = true;

    const fetchContextData = async () => {
      try {
        setError(null);
        
        const results = await Promise.allSettled([
          API.get('auth/users/'), 
          API.get('kanban/projects/'),
          API.get('auth/roles/')
        ]);
        
        if (!isMounted) return;

        // 1. Synchronize Active Enclave Users Directory
        if (results[0].status === 'fulfilled') {
          const payload = results[0].value.data;
          setUsers(Array.isArray(payload) ? payload : (payload.results || []));
        } else {
          console.error("Users directory sync fault:", results[0].reason);
        }

        // 2. Synchronize Active Multi-Tenant Project Contexts
        if (results[1].status === 'fulfilled') {
          const payload = results[1].value.data;
          setProjects(Array.isArray(payload) ? payload : (payload.results || []));
        } else {
          console.error("Workspace projects sync fault:", results[1].reason);
        }

        // 3. Synchronize Structural Security Privilege Layer
        if (results[2].status === 'fulfilled') {
          const payload = results[2].value.data;
          setRoles(Array.isArray(payload) ? payload : (payload.results || []));
        } else {
          console.error("Security Role matrix sync fault:", results[2].reason);
          setError("Infrastructure Fault: Unable to load platform authorization metadata context.");
        }

      } catch (err) {
        console.error("Unexpected subsystem pipeline fault:", err);
        if (isMounted) setError("Network execution pipeline transmission break.");
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchContextData();
    return () => { isMounted = false; };
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleProvisionSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    if (!formData.project_id) {
      setError("An explicit destination workspace project boundary must be assigned before deploying profile.");
      setIsSubmitting(false);
      return;
    }

    try {
      // STRUCTURAL REFACTOR: Keep project_id as a pure raw string to safely map UUID formats
      const response = await API.post('auth/users/provision/', {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        role: parseInt(formData.role, 10),
        project_id: formData.project_id
      });

      setUsers((prev) => [...prev, response.data]);
      setShowModal(false);
      setFormData({ username: '', email: '', password: '', role: '', project_id: '' });
    } catch (err) {
      console.error("Atomic registration transaction rejected:", err);
      if (err.response?.data) {
        setError(typeof err.response.data === 'object' ? JSON.stringify(err.response.data) : err.response.data);
      } else {
        setError("Account multi-tenant deployment transaction failed.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) return <div className="p-6 text-slate-500 bg-slate-950 min-h-screen flex items-center justify-center font-mono text-xs">Accessing Cluster Directory Enclave...</div>;

  return (
    <div className="space-y-6 p-6 bg-slate-950 min-h-screen text-slate-100">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">User Directory Configuration</h1>
          <p className="text-sm text-slate-400">Provision identity blocks and tie them to isolated project workspaces.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold tracking-wide transition-all cursor-pointer"
        >
          Provision New Profile
        </button>
      </div>

      {error && (
        <div className="p-3 bg-rose-950/40 border border-rose-800/60 rounded-lg text-xs text-rose-400 font-mono whitespace-pre-wrap">
          {error}
        </div>
      )}

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-900/50 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
              <th className="p-4">UID</th>
              <th className="p-4">Identity / Profile</th>
              <th className="p-4">Email Contact</th>
              <th className="p-4">Hierarchical Layer</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 text-sm">
            {users.length === 0 ? (
              <tr>
                <td colSpan="4" className="p-8 text-center text-xs text-slate-500 font-mono">No identity records found in this enclave partition.</td>
              </tr>
            ) : (
              users.map((u) => (
                <tr key={`user-entry-${u.id}`} className="hover:bg-slate-800/20 text-slate-300 transition-colors">
                  <td className="p-4 font-mono text-xs text-slate-500">#{u.id}</td>
                  <td className="p-4 font-semibold text-white">{u.username}</td>
                  <td className="p-4 text-slate-400 font-mono text-xs">{u.email}</td>
                  <td className="p-4">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wide uppercase bg-slate-800 text-indigo-400 border border-slate-700">
                      {u.role_details?.name || 'No Role Assigned'}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 relative">
            <h3 className="text-base font-bold text-white mb-1">Provision Platform Identity</h3>
            <p className="text-xs text-slate-400 mb-4">Creates an account and binds a project membership atomically.</p>
            
            <form onSubmit={handleProvisionSubmit} className="space-y-4">
              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Username</label>
                <input
                  type="text" required name="username" value={formData.username} onChange={handleInputChange}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Email Address</label>
                <input
                  type="email" required name="email" value={formData.email} onChange={handleInputChange}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>

              <div>
                <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Account Secret Password</label>
                <input
                  type="password" required name="password" value={formData.password} onChange={handleInputChange}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Security Role</label>
                  <select
                    name="role" required value={formData.role} onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
                  >
                    <option value="">Select Target...</option>
                    {roles.map((r) => <option key={`role-select-${r.id}`} value={r.id}>{r.name}</option>)}
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1">Workspace Allocation</label>
                  <select
                    name="project_id" required value={formData.project_id} onChange={handleInputChange}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
                  >
                    <option value="">Select Target...</option>
                    {projects.map((p) => <option key={`project-select-${p.id}`} value={p.id}>{p.title}</option>)}
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button" onClick={() => setShowModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit" disabled={isSubmitting}
                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-white rounded-lg text-xs font-semibold cursor-pointer"
                >
                  {isSubmitting ? "Executing Transaction..." : "Deploy Profile"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}