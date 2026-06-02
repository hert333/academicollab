import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useParams, useNavigate, Outlet } from 'react-router-dom';
import axios from 'axios';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import RoleManagementDashboard from './components/RoleManagementDashboard';
import UserManagementDashboard from './components/UserManagementDashboard';
import KanbanBoard from './components/KanbanBoard';
import Login from './components/Login';

const API_BASE = window._env_?.VITE_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';

const UnauthorizedPlaceholder = () => (
  <div className="p-10 font-sans text-rose-500 bg-slate-950 min-h-screen">
    <h2 className="text-2xl font-bold mb-2">403 - Structural Access Denied</h2>
    <p className="text-slate-400 text-sm">Your current assigned identity weight is barred from this node context path.</p>
  </div>
);

/**
 * Global Architecture Layout Wrapper
 * Leverages React Router <Outlet /> to inject child views dynamically while preserving sidebar state
 */
function AppLayout() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const { projectId } = useParams();
  const navigate = useNavigate();

  // Safely extract token information for structural conditional access blocks if required
  const token = localStorage.getItem('access_token');

  useEffect(() => {
    const fetchWorkspaceMeta = async () => {
      if (!token) return;
      try {
        const res = await axios.get(`${API_BASE}/api/kanban/projects/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setProjects(res.data);
      } catch (err) {
        console.error("Failed to fetch sidebar workspace metadata collection.", err);
      } finally {
        setLoading(false);
      }
    };
    fetchWorkspaceMeta();
  }, [token]);

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans antialiased">
      {/* Central Sidebar Component Grid */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between p-4 shrink-0 select-none">
        <div className="space-y-6">
          <div className="flex items-center gap-2 px-2">
            <div className="h-6 w-6 rounded bg-indigo-600 flex items-center justify-center font-bold text-xs text-white">AC</div>
            <span className="font-bold text-lg tracking-wide bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
              AcademiCollab
            </span>
          </div>
          
          {/* Section A: Shared Workspaces */}
          <div className="space-y-2">
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-2">Workspace Boards</h2>
            <nav className="space-y-1 max-h-[40vh] overflow-y-auto pr-1">
              {loading ? (
                <div className="text-xs text-slate-500 px-2">Syncing channels...</div>
              ) : projects.map((proj) => (
                <Link 
                  key={proj.id}
                  to={`/kanban/${proj.id}`}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-150 truncate ${
                    projectId === proj.id 
                      ? 'bg-indigo-600 text-white font-semibold' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  <span className={projectId === proj.id ? 'text-white' : 'text-indigo-500'}>#</span> {proj.title}
                </Link>
              ))}
            </nav>
          </div>

          {/* Section B: Administrative Core Controls */}
          <div className="pt-4 border-t border-slate-800/60 space-y-1">
            <h2 className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-2 mb-2">Management</h2>
            <Link 
              to="/admin/users" 
              className={`block px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                window.location.pathname === '/admin/users' ? 'bg-slate-800 text-indigo-400 font-semibold' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              User Directory Configuration
            </Link>
            <Link 
              to="/admin/roles" 
              className={`block px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                window.location.pathname === '/admin/roles' ? 'bg-slate-800 text-indigo-400 font-semibold' : 'text-slate-400 hover:text-white hover:bg-slate-800/50'
              }`}
            >
              RBAC Weight Metrics
            </Link>
          </div>
        </div>
        
        <div className="border-t border-slate-800 pt-4 px-2 text-[11px] text-slate-500 font-medium">
          Cluster Enclave: Verified
        </div>
      </aside>

      {/* Primary View Insertion Port */}
      <main className="flex-1 overflow-auto relative bg-slate-950 p-6">
        <Outlet />
      </main>
    </div>
  );
}

/**
 * Fallback Component to handle intelligent root redirection based on user project metrics
 */
function RootIndexRedirect() {
  const navigate = useNavigate();
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login', { replace: true });
      return;
    }
    // Fetch base workspace tracking targets to perform automated route assignment
    axios.get(`${API_BASE}/api/kanban/projects/`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    .then(res => {
      if (res.data.length > 0) {
        navigate(`/kanban/${res.data[0].id}`, { replace: true });
      } else {
        navigate('/admin/roles', { replace: true }); // Admin default fallback boundary
      }
    })
    .catch(() => navigate('/login', { replace: true }));
  }, [navigate]);

  return <div className="p-8 text-slate-400 bg-slate-950 min-h-screen">Resolving routing vector indices...</div>;
}

export default function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Unprotected Identity Challenge Targets */}
          <Route path="/login" element={<Login />} />
          <Route path="/unauthorized" element={<UnauthorizedPlaceholder />} />

          {/* Secure Layout Graph Structure */}
          <Route element={<ProtectedRoute allowedRoles={['Admin', 'Faculty', 'Student']} />}>
            <Route element={<AppLayout />}>
              <Route path="/" element={<RootIndexRedirect />} />
              <Route path="/kanban/:projectId" element={<KanbanBoardWrapper />} />
              
              {/* Nested Administrative Guard Execution Block */}
              <Route element={<ProtectedRoute allowedRoles={['Admin']} />}>
                <Route path="/admin/roles" element={<RoleManagementDashboard />} />
                <Route path="/admin/users" element={<UserManagementDashboard />} />
              </Route>
            </Route>
          </Route>

          {/* Global Fallback Route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

// Clean parameter forwarding wrapper for the KanbanBoard layout element
function KanbanBoardWrapper() {
  const { projectId } = useParams();
  return <KanbanBoard projectId={projectId} />;
}