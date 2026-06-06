import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, useParams, useNavigate, Outlet } from 'react-router-dom';
import API from './services/api';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import RoleManagementDashboard from './components/RoleManagementDashboard';
import UserManagementDashboard from './components/UserManagementDashboard';
import KanbanBoard from './components/KanbanBoard';
import Login from './components/Login';

const UnauthorizedPlaceholder = () => (
  <div className="p-10 font-sans text-rose-500 bg-slate-950 min-h-screen">
    <h2 className="text-2xl font-bold mb-2">403 - Structural Access Denied</h2>
    <p className="text-slate-400 text-sm">Your current assigned identity weight is barred from this node context path.</p>
  </div>
);

function AppLayout() {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const { projectId } = useParams();
  const token = localStorage.getItem('access_token');

  useEffect(() => {
    const fetchWorkspaceMeta = async () => {
      if (!token) return;
      try {
        // FIXED: Replaced raw axios with intercepted API instance client to ensure token lifecycle coverage
        const res = await API.get('kanban/projects/');
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
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between p-4 shrink-0 select-none">
        <div className="space-y-6">
          <div className="flex items-center gap-2 px-2">
            <div className="h-6 w-6 rounded bg-indigo-600 flex items-center justify-center font-bold text-xs text-white">AC</div>
            <span className="font-bold text-lg tracking-wide bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent">
              AcademiCollab
            </span>
          </div>
          
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
                    projectId === String(proj.id) 
                      ? 'bg-indigo-600 text-white font-semibold' 
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                  }`}
                >
                  <span className={projectId === String(proj.id) ? 'text-white' : 'text-indigo-500'}>#</span> {proj.title}
                </Link>
              ))}
            </nav>
          </div>

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

      <main className="flex-1 overflow-auto relative bg-slate-950 p-6">
        <Outlet />
      </main>
    </div>
  );
}

function RootIndexRedirect() {
  const navigate = useNavigate();
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      navigate('/login', { replace: true });
      return;
    }
    
    // FIXED: Patched to use internal API configuration client, mapping permissions routing safely
    API.get('kanban/projects/')
      .then(res => {
        if (res.data.length > 0) {
          navigate(`/kanban/${res.data[0].id}`, { replace: true });
        } else {
          navigate('/admin/roles', { replace: true });
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
          <Route path="/login" element={<Login />} />
          <Route path="/unauthorized" element={<UnauthorizedPlaceholder />} />

          <Route element={<ProtectedRoute allowedRoles={['Admin', 'Faculty', 'Student']} />}>
            <Route element={<AppLayout />}>
              <Route path="/" element={<RootIndexRedirect />} />
              <Route path="/kanban/:projectId" element={<KanbanBoardWrapper />} />
              
              <Route element={<ProtectedRoute allowedRoles={['Admin']} />}>
                <Route path="/admin/roles" element={<RoleManagementDashboard />} />
                <Route path="/admin/users" element={<UserManagementDashboard />} />
              </Route>
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

function KanbanBoardWrapper() {
  const { projectId } = useParams();
  return <KanbanBoard projectId={projectId} />;
}