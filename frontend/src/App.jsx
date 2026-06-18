// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useParams, useNavigate, Outlet } from 'react-router-dom';
import API from './services/api';
import { AuthProvider } from './context/AuthContext';
import { useAuth } from './hooks/useAuth'; // Synchronized target hook location across the system
import ProtectedRoute from './components/ProtectedRoute';
import RoleManagementDashboard from './components/RoleManagementDashboard';
import UserManagementDashboard from './components/UserManagementDashboard';
import KanbanBoard from './components/KanbanBoard';
import Login from './components/Login';
import WorkspaceDashboard from './pages/WorkspaceDashboard';

const UnauthorizedPlaceholder = () => (
  <div className="p-10 font-sans text-rose-500 bg-slate-950 min-h-screen">
    <h2 className="text-2xl font-bold mb-2">403 - Structural Access Denied</h2>
    <p className="text-slate-400 text-sm">Your current assigned identity weight is barred from accessing this node path.</p>
  </div>
);

function AppLayout() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const { projectId } = useParams();
  const token = localStorage.getItem('access_token');
  const { user, loading: authLoading, logout } = useAuth();
  
  const currentRole = (user?.role_details?.name || user?.role || '').toUpperCase();

  useEffect(() => {
    let isMounted = true;

    const fetchWorkspaceMeta = async () => {
      if (!token || authLoading || !user) return;
      
      try {
        // Aligned to correctly point to the coordination app namespace endpoint path
        const res = await API.get('kanban/projects/');
        if (isMounted) {
          setProjects(res.data);
        }
      } catch (err) {
        console.error("Failed to fetch sidebar workspace metadata collection.", err);
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchWorkspaceMeta();

    return () => {
      isMounted = false;
    };
  }, [token, authLoading, user]);

  if (authLoading) {
    return (
      <div className="p-6 font-mono text-xs text-slate-500 bg-slate-950 min-h-screen flex items-center justify-center">
        Synchronizing Cluster Enclave Identity Vectors...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans antialiased">
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between p-4 shrink-0 select-none">
        <div className="space-y-6">
          <div className="flex items-center justify-between px-2">
            <Link to="/workspaces" className="flex items-center gap-2 group">
              <div className="h-6 w-6 rounded bg-indigo-600 flex items-center justify-center font-bold text-xs text-white group-hover:bg-indigo-500 transition-colors">AC</div>
              <span className="font-bold text-lg tracking-wide bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent group-hover:text-white transition-colors">
                AcademiCollab
              </span>
            </Link>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between items-center px-2">
              <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Projects</h2>
            </div>
            <nav className="space-y-1 max-h-[40vh] overflow-y-auto pr-1">
              {loading ? (
                <div className="text-xs text-slate-500 px-2">Syncing channels...</div>
              ) : projects.length > 0 ? (
                projects.map((proj) => (
                  <Link 
                    key={proj.id}
                    to={`/kanban/${proj.id}`}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150 truncate ${
                      projectId === String(proj.id) 
                        ? 'bg-indigo-600 text-white font-semibold' 
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                    }`}
                  >
                    <span className={projectId === String(proj.id) ? 'text-white' : 'text-indigo-500'}>#</span> {proj.title}
                  </Link>
                ))
              ) : (
                <div className="text-xs text-slate-600 italic px-2">No active projects linked</div>
              )}
            </nav>
          </div>

          <div className="pt-2 border-t border-slate-800/60">
            <Link to="/workspaces" className="flex items-center gap-2 px-3 py-2 text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800/50 rounded-lg transition-all">
              <span className="text-indigo-400 text-sm">⊞</span> Switch Workspace Environment
            </Link>
          </div>

          {currentRole === 'ADMIN' && (
            <div className="pt-4 border-t border-slate-800/60 space-y-1">
              <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-2 mb-2">Management</h2>
              <Link to="/admin/users" className="block px-3 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all">
                User Directory Configuration
              </Link>
              <Link to="/admin/roles" className="block px-3 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-slate-800/50 transition-all">
                RBAC Weight Metrics
              </Link>
            </div>
          )}
        </div>
        
        <div className="flex flex-col gap-2 border-t border-slate-800 pt-4 px-2">
          <div className="flex justify-between items-center text-[11px] text-slate-500">
            <span className="font-medium">Role: <b className="text-indigo-400 text-[10px]">{currentRole}</b></span>
            <button onClick={logout} className="text-rose-500 hover:text-rose-400 font-semibold transition-colors cursor-pointer">
              Disconnect
            </button>
          </div>
          <div className="text-[10px] text-slate-600 font-medium">
            Cluster Enclave: Verified
          </div>
        </div>
      </aside>

      <main className="flex-1 overflow-auto relative bg-slate-950 p-6">
        <Outlet context={{ currentRole }} />
      </main>
    </div>
  );
}

function KanbanRouteWrapper() {
  const { projectId } = useParams();
  const { user } = useAuth();
  const currentRole = (user?.role_details?.name || user?.role || '').toUpperCase();

  return <KanbanBoard boardId={projectId} userRole={currentRole} />;
}

function RootIndexRedirect() {
  const navigate = useNavigate();
  const { loading } = useAuth();
  
  useEffect(() => {
    if (loading) return;
    
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login', { replace: true });
      return;
    }
    
    navigate('/workspaces', { replace: true });
  }, [loading, navigate]);

  return (
    <div className="p-6 font-mono text-xs text-slate-500 bg-slate-950 min-h-screen flex items-center justify-center">
      Resolving Target Routing Context Vector...
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/unauthorized" element={<UnauthorizedPlaceholder />} />
          
          <Route element={<AppLayout />}>
            <Route path="/" element={<RootIndexRedirect />} />
            
            <Route element={<ProtectedRoute allowedRoles={['STUDENT', 'PROJECT MANAGER', 'SUPERVISOR', 'ADMIN']} />}>
              <Route path="/workspaces" element={<WorkspaceDashboard />} />
              <Route path="/kanban/:projectId" element={<KanbanRouteWrapper />} />
            </Route>

            <Route element={<ProtectedRoute allowedRoles={['ADMIN']} />}>
              <Route path="/admin/users" element={<UserManagementDashboard />} />
              <Route path="/admin/roles" element={<RoleManagementDashboard />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}