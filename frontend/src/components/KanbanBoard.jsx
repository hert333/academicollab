// frontend/src/components/kanban/KanbanBoard.jsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import GanttChart from './analytics/GanttChart';

export default function KanbanBoard({ boardId }) {
  const [activeView, setActiveView] = useState('KANBAN');
  const [board, setBoard] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [syncing, setSyncing] = useState(false);

  // Structural tracking variables for native HTML5 drag operations
  const [draggedTaskId, setDraggedTaskId] = useState(null);
  const [sourceColumnId, setSourceColumnId] = useState(null);

  const API_BASE = window._env_?.VITE_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';

  useEffect(() => {
    // Structural guard matrix preventing execution tracking errors when state hasn't hydrated
    if (!boardId || boardId === 'undefined') {
      return;
    }
    fetchBoardData();
  }, [boardId]);

  const fetchBoardData = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await axios.get(`${API_BASE}/api/kanban/boards/${boardId}/`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setBoard(res.data);
      setError(null);
    } catch (err) {
      setError('Failed to resolve target board configuration layout.');
    } finally {
      setLoading(false);
    }
  };

  const handleDragStart = (e, taskId, colId) => {
    setDraggedTaskId(taskId);
    setSourceColumnId(colId);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', String(taskId));
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    if (e.dataTransfer.types.includes('text/plain')) {
      e.dataTransfer.dropEffect = 'move';
    }
  };

  const handleDrop = async (e, targetColId, targetIndex) => {
    e.preventDefault();
    if (!draggedTaskId || !sourceColumnId) return;

    // Cache structural state depth before mutations to guarantee isolated rollback capabilities
    const rollbackCache = JSON.parse(JSON.stringify(board));

    const sourceColumn = board.columns.find(c => c.id === sourceColumnId);
    const targetColumn = board.columns.find(c => c.id === targetColId);
    if (!sourceColumn || !targetColumn) return;

    const movingTask = sourceColumn.tasks.find(t => t.id === draggedTaskId);
    if (!movingTask) return;

    let modifiedColumns = [...board.columns];

    // Scenario A: Mutating positions within the exact same structural lane
    if (sourceColumnId === targetColId) {
      const remainingTasks = Array.from(sourceColumn.tasks).filter(t => t.id !== draggedTaskId);
      remainingTasks.splice(targetIndex, 0, movingTask);
      
      const reindexedTasks = remainingTasks.map((t, idx) => ({ ...t, position: idx }));
      
      modifiedColumns = board.columns.map(col => 
        col.id === sourceColumnId ? { ...col, tasks: reindexedTasks } : col
      );
    } 
    // Scenario B: Boundary crossing mutations across independent columns
    else {
      const cleanSourceTasks = Array.from(sourceColumn.tasks).filter(t => t.id !== draggedTaskId)
        .map((t, idx) => ({ ...t, position: idx }));
      
      const destinationTasks = Array.from(targetColumn.tasks);
      const mutatedTaskEntry = { ...movingTask, column: targetColId };
      destinationTasks.splice(targetIndex, 0, mutatedTaskEntry);
      
      const reindexedTargetTasks = destinationTasks.map((t, idx) => ({ ...t, position: idx }));

      modifiedColumns = board.columns.map(col => {
        if (col.id === sourceColumnId) return { ...col, tasks: cleanSourceTasks };
        if (col.id === targetColId) return { ...col, tasks: reindexedTargetTasks };
        return col;
      });
    }

    // Apply instantaneous state representation to viewport layer (Optimistic UI Paradigm)
    setBoard({ ...board, columns: modifiedColumns });
    setSyncing(true);

    try {
      const token = localStorage.getItem('access_token');
      
      // Execute standard synchronization request targeting the specialized concurrency endpoint
      const response = await axios.patch(
        `${API_BASE}/api/kanban/tasks/${draggedTaskId}/move/`,
        {
          target_column_id: targetColId,
          position: targetIndex
        },
        {
          headers: { 
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}` 
          }
        }
      );

      if (response.status !== 200) {
        throw new Error(`SERVER_ERROR_CODE: ${response.status}`);
      }
    } catch (err) {
      console.error('Database mutation fault encountered. Restoring baseline layout map:', err);
      setBoard(rollbackCache);
    } finally {
      setSyncing(false);
      setDraggedTaskId(null);
      setSourceColumnId(null);
    }
  };

  if (loading) return <div className="p-8 text-slate-400 font-medium bg-slate-950 min-h-screen font-mono">HYDRATING_KANBAN_PIPELINE_MAPS...</div>;
  if (error) return <div className="p-8 text-rose-500 font-semibold bg-slate-950 min-h-screen font-mono">ERROR: {error}</div>;

  return (
    <div className="w-full min-h-screen bg-slate-950 p-6 text-slate-100 selection:bg-indigo-500">
      <header className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2">{board?.name}</h1>
          <p className="text-slate-400 text-sm max-w-2xl">{board?.description}</p>
        </div>
        
        <div className="flex items-center gap-4">
          {/* View Management Switch Controllers */}
          <div className="bg-slate-900 border border-slate-800 p-1 rounded-lg flex gap-1 font-mono text-xs">
            <button 
              onClick={() => setActiveView('KANBAN')}
              className={`px-3 py-1.5 rounded-md font-bold transition-all duration-150 ${activeView === 'KANBAN' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}
            >
              VIEW_KANBAN
            </button>
            <button 
              onClick={() => setActiveView('GANTT')}
              className={`px-3 py-1.5 rounded-md font-bold transition-all duration-150 ${activeView === 'GANTT' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'}`}
            >
              VIEW_GANTT
            </button>
          </div>

          {syncing && (
            <span className="text-xs font-mono text-indigo-400 bg-indigo-950/50 border border-indigo-800/80 px-3 py-1 rounded-md animate-pulse">
              SYNCING_STATE_DB
            </span>
          )}
        </div>
      </header>

      {/* Dynamic Render Boundary Splitter */}
      {activeView === 'GANTT' ? (
        <GanttChart boardData={board} />
      ) : (
        <div className="flex gap-5 overflow-x-auto pb-4 items-start select-none">
          {board?.columns?.map((column) => (
            <div 
              key={column.id}
              className="w-80 shrink-0 bg-slate-900 rounded-xl border border-slate-800 p-4 flex flex-col max-h-[80vh]"
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, column.id, column.tasks?.length || 0)}
            >
              <div className="flex justify-between items-center mb-4 px-1">
                <h2 className="font-semibold text-slate-200 text-base tracking-wide">{column.name}</h2>
                <span className="text-xs font-bold bg-slate-800 text-slate-400 px-2.5 py-1 rounded-full border border-slate-700">
                  {column.tasks?.length || 0}
                </span>
              </div>

              <div className="flex flex-col gap-3 overflow-y-auto pr-1 grow min-h-[150px]">
                {column.tasks?.map((task, index) => (
                  <div
                    key={task.id}
                    draggable
                    onDragStart={(e) => handleDragStart(e, task.id, column.id)}
                    onDragOver={handleDragOver}
                    onDrop={(e) => {
                      e.stopPropagation(); 
                      handleDrop(e, column.id, index);
                    }}
                    className={`group bg-slate-950 p-4 rounded-lg border border-slate-800 hover:border-indigo-500/50 cursor-grab active:cursor-grabbing transition-all duration-200 shadow-sm hover:shadow-indigo-950/20 ${
                      draggedTaskId === task.id ? 'opacity-20 border-dashed border-indigo-500 scale-95' : ''
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

                    {task.assigned_to_details && (
                      <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-900">
                        <div className="w-5 h-5 rounded-full bg-indigo-600 flex items-center justify-center text-[10px] font-bold text-white uppercase">
                          {task.assigned_to_details.username.substring(0, 2)}
                        </div>
                        <span className="text-[11px] text-slate-400 font-medium">
                          @{task.assigned_to_details.username}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}