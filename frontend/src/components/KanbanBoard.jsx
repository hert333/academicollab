import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function KanbanBoard({ projectId }) {
  const [project, setProject] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Tracks active structural drag state metadata locally
  const [draggedTaskId, setDraggedTaskId] = useState(null);
  const [sourceColumnId, setSourceColumnId] = useState(null);

  const API_BASE = window._env_?.VITE_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchBoardData();
  }, [projectId]);

  const fetchBoardData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await axios.get(`${API_BASE}/api/kanban/projects/${projectId}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProject(res.data);
      setLoading(false);
    } catch (err) {
      setError('Failed to resolve project Kanban asset map from remote endpoint.');
      setLoading(false);
    }
  };

  const handleDragStart = (e, taskId, colId) => {
    setDraggedTaskId(taskId);
    setSourceColumnId(colId);
    e.dataTransfer.setData('text/plain', taskId);
  };

  const handleDragOver = (e) => {
    e.preventDefault(); // Required initialization target to permit drop event triggers
  };

  const handleDrop = async (e, targetColId, targetIndex) => {
    e.preventDefault();
    if (!draggedTaskId) return;

    const sourceCol = project.columns.find(c => c.id === sourceColumnId);
    const targetCol = project.columns.find(c => c.id === targetColId);
    const movingTask = sourceCol.tasks.find(t => t.id === draggedTaskId);

    // Optimistic UI Rendering Generation to maximize HCI perceived velocity
    const updatedColumns = project.columns.map(col => {
      let nextTasks = [...col.tasks];
      
      if (col.id === sourceColumnId) {
        nextTasks = nextTasks.filter(t => t.id !== draggedTaskId);
      }
      
      if (col.id === targetColId) {
        // Adjust array configuration insertion parameters 
        const insertAt = col.id === sourceColumnId && targetIndex > movingTask.order ? targetIndex - 1 : targetIndex;
        nextTasks.splice(insertAt, 0, { ...movingTask, column: targetColId });
      }

      // Re-index array ordering structures sequentially
      return {
        ...col,
        tasks: nextTasks.map((t, idx) => ({ ...t, order: idx }))
      };
    });

    setProject({ ...project, columns: updatedColumns });

    try {
      const token = localStorage.getItem('access_token');
      await axios.post(`${API_BASE}/api/kanban/tasks/${draggedTaskId}/reorder/`, {
        target_column_id: targetColId,
        new_order: targetIndex
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
    } catch (err) {
      // Revert optimization state vectors if server rejects the data modification command
      fetchBoardData();
    } finally {
      setDraggedTaskId(null);
      setSourceColumnId(null);
    }
  };

  if (loading) return <div className="p-8 text-slate-400 font-medium">Hydrating Kanban pipeline maps...</div>;
  if (error) return <div className="p-8 text-rose-500 font-semibold">{error}</div>;

  return (
    <div className="w-full min-h-screen bg-slate-950 p-6 text-slate-100 selection:bg-indigo-500">
      <header className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-white mb-2">{project?.title}</h1>
        <p className="text-slate-400 text-sm max-w-2xl">{project?.description}</p>
      </header>

      {/* Kanban Column View Framework Matrix */}
      <div className="flex gap-5 overflow-x-auto pb-4 items-start select-none">
        {project?.columns?.map((column) => (
          <div 
            key={column.id}
            className="w-80 shrink-0 bg-slate-900 rounded-xl border border-slate-800 p-4 flex flex-col max-h-[80vh]"
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, column.id, column.tasks.length)}
          >
            <div className="flex justify-between items-center mb-4 px-1">
              <h2 className="font-semibold text-slate-200 text-base tracking-wide">{column.name}</h2>
              <span className="text-xs font-bold bg-slate-800 text-slate-400 px-2.5 py-1 rounded-full border border-slate-700">
                {column.tasks?.length || 0}
              </span>
            </div>

            {/* Task Item Stack View Area */}
            <div className="flex flex-col gap-3 overflow-y-auto pr-1 grow min-h-[150px]">
              {column.tasks?.map((task, index) => (
                <div
                  key={task.id}
                  draggable
                  onDragStart={(e) => handleDragStart(e, task.id, column.id)}
                  onDragOver={handleDragOver}
                  onDrop={(e) => {
                    e.stopPropagation(); // Shield child drop targets from parent tracking loops
                    handleDrop(e, column.id, index);
                  }}
                  className={`group bg-slate-950 p-4 rounded-lg border border-slate-800 hover:border-indigo-500/50 cursor-grab active:cursor-grabbing transition-all duration-200 shadow-sm hover:shadow-indigo-950/20 ${
                    draggedTaskId === task.id ? 'opacity-40 border-dashed border-indigo-500' : ''
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <h3 className="font-medium text-sm text-slate-100 group-hover:text-indigo-400 transition-colors duration-150">
                      {task.title}
                    </h3>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider border ${
                      task.priority === 'CRITICAL' ? 'bg-rose-950/40 text-rose-400 border-rose-900' :
                      task.priority === 'HIGH' ? 'bg-amber-950/40 text-amber-400 border-amber-900' :
                      task.priority === 'MEDIUM' ? 'bg-indigo-950/40 text-indigo-400 border-indigo-900' :
                      'bg-slate-900 text-slate-400 border-slate-800'
                    }`}>
                      {task.priority}
                    </span>
                  </div>
                  
                  {task.description && (
                    <p className="text-xs text-slate-400 line-clamp-2 mb-3 leading-relaxed">
                      {task.description}
                    </p>
                  )}

                  {task.assigned_to_detail && (
                    <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-900">
                      <div className="w-5 h-5 rounded-full bg-indigo-600 flex items-center justify-center text-[10px] font-bold text-white uppercase">
                        {task.assigned_to_detail.username.substring(0, 2)}
                      </div>
                      <span className="text-[11px] text-slate-400 font-medium">
                        {task.assigned_to_detail.username}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}