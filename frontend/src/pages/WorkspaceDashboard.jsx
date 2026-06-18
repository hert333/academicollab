// frontend/src/pages/WorkspaceDashboard.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getWorkspaces, createWorkspace } from '../services/api';
import { useAuth } from '../hooks/useAuth';

export default function WorkspaceDashboard() {
  const [workspaces, setWorkspaces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Explicit administrative role authorization vector extraction
  const currentRole = (user?.role_details?.name || user?.role || '').toUpperCase();
  const isAdmin = currentRole === 'ADMIN';

  useEffect(() => {
    let isMounted = true;
    
    const fetchClusterWorkspaces = async () => {
      try {
        const response = await getWorkspaces();
        if (isMounted) {
          setWorkspaces(response.data);
        }
      } catch (err) {
        console.error("Failed to hydrate workspace collection:", err);
        if (isMounted) {
          setError('Failed to fetch accessible workspace nodes from secure cluster.');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchClusterWorkspaces();
    return () => { isMounted = false; };
  }, []);

  const handleCreateWorkspace = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;

    setSubmitting(true);
    setError('');

    try {
      const response = await createWorkspace({ name, description });
      setWorkspaces((prev) => [response.data, ...prev]);
      setIsModalOpen(false);
      setName('');
      setDescription('');
    } catch (err) {
      console.error("Workspace instantiation error:", err);
      setError(err.response?.data?.error || 'Failed to initialize workspace runtime environment.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950 text-xs font-mono text-slate-500">
        Hydrating Active Workspace Node Mappings...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        
        {/* Workspace Hub Header Section */}
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-800 pb-6">
          <div>
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
              Academic Environments
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Select or deploy a decoupled cluster partition to manage projects, Kanban tasks, and timelines.
            </p>
          </div>

          {isAdmin && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold rounded-lg shadow-lg shadow-indigo-600/20 transition-all duration-150 active:scale-[0.98] cursor-pointer"
            >
              Provision Workspace
            </button>
          )}
        </div>

        {/* Global Structural Error Handlers */}
        {error && (
          <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-lg text-xs font-medium text-rose-400">
            System Alert: {error}
          </div>
        )}

        {/* Main Grid View */}
        {workspaces.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {workspaces.map((ws) => (
              <div
                key={ws.id}
                onClick={() => navigate(`/workspaces/${ws.id}`)}
                className="group flex flex-col justify-between p-6 bg-slate-900 border border-slate-800 hover:border-indigo-500/50 rounded-xl cursor-pointer transition-all duration-200 shadow-xl hover:shadow-indigo-950/20"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono text-indigo-400 tracking-wider font-semibold uppercase">
                      Tenant Node
                    </span>
                    <span className="text-[10px] font-mono text-slate-500">
                      {new Date(ws.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <h3 className="text-lg font-bold text-white group-hover:text-indigo-400 transition-colors truncate">
                    {ws.name}
                  </h3>
                  <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                    {ws.description || "No supplemental descriptive summary metadata declared for this isolation segment."}
                  </p>
                </div>

                <div className="pt-6 border-t border-slate-800/60 mt-6 flex items-center justify-between text-[11px] text-slate-500">
                  <span>Owner: <b className="text-slate-300 font-medium">{ws.created_by_detail?.username || 'System'}</b></span>
                  <span className="text-indigo-500 font-semibold group-hover:translate-x-1 transition-transform duration-150">
                    Connect &rarr;
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center p-16 border border-dashed border-slate-800 bg-slate-900/20 rounded-2xl text-center">
            <div className="h-10 w-10 rounded-xl bg-slate-900 flex items-center justify-center font-bold text-slate-600 mb-4 border border-slate-800">#</div>
            <h4 className="text-sm font-semibold text-slate-300">No partitions assigned to identity</h4>
            <p className="text-xs text-slate-500 max-w-xs mt-1 leading-relaxed">
              You are currently unmapped to any active structural workspaces. Contact your platform supervisor.
            </p>
          </div>
        )}

        {/* Modal Window: Instantiation Form (Only rendered if Admin validation clears) */}
        {isModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 animate-fade-in">
            <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl p-6 space-y-6">
              <div>
                <h3 className="text-lg font-bold text-white">Initialize New Workspace</h3>
                <p className="text-xs text-slate-400 mt-1">Deploy an isolated context node into the database layer.</p>
              </div>

              <form onSubmit={handleCreateWorkspace} className="space-y-4">
                <div className="space-y-1">
                  <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Workspace Title</label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g., Computer Science Dissertation Team"
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">Scope / Description</label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Define context boundaries, strict isolation variables, or research goals..."
                    rows={3}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 transition-colors resize-none"
                  />
                </div>

                <div className="flex gap-3 justify-end pt-2">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(false)}
                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg transition-colors cursor-pointer"
                  >
                    Abort
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 text-white text-xs font-semibold rounded-lg shadow-md transition-colors cursor-pointer"
                  >
                    {submitting ? 'Deploying...' : 'Confirm Matrix Allocation'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}