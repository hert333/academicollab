// frontend/src/components/KanbanBoard.jsx
import React, { useState, useEffect } from 'react';
import { useKanbanBoard } from '../hooks/useKanbanBoard';
import GanttChart from './analytics/GanttChart';

export default function KanbanBoard({ boardId, userRole }) {
  const [activeView, setActiveView] = useState('KANBAN');
  const [draggedTaskId, setDraggedTaskId] = useState(null);
  const [sourceColumnId, setSourceColumnId] = useState(null);
  const [newColName, setNewColName] = useState('');
  const [selectedColumnForTask, setSelectedColumnForTask] = useState(null);
  const [newTaskTitle, setNewTaskTitle] = useState('');

  // Determine user execution context permissions based on RBAC identity parameters
  const isSupervisor = userRole?.toUpperCase() === 'SUPERVISOR' || userRole?.toUpperCase() === 'ADMIN';

  // Leverage the consolidated hook layout mapping engine
  const {
    board,
    loading,
    isMutating,
    errors,
    loadBoard,
    moveTaskOptimistically,
    createNewColumn,
    createNewTask,
    purgeColumn
  } = useKanbanBoard();

  useEffect(() => {
    if (boardId) {
      loadBoard(boardId);
    }
  }, [boardId, loadBoard]);

  const handleDragStart = (e, taskId, colId) => {
    if (isMutating) {
      e.preventDefault();
      return;
    }
    setDraggedTaskId(taskId);
    setSourceColumnId(colId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = async (e, targetColId, targetIndex) => {
    e.preventDefault();
    if (!draggedTaskId || !sourceColumnId || isMutating) return;

    if (sourceColumnId === targetColId && board?.columns) {
      const column = board.columns.find(c => c.id === targetColId);
      const currentIndex = column?.tasks?.findIndex(t => t.id === draggedTaskId);
      if (currentIndex === targetIndex) {
        cleanDragState();
        return;
      }
    }

    try {
      await moveTaskOptimistically(draggedTaskId, sourceColumnId, targetColId, targetIndex);
    } catch (err) {
      console.error("Drag reordering transaction rejected:", err);
    } finally {
      cleanDragState();
    }
  };

  const cleanDragState = () => {
    setDraggedTaskId(null);
    setSourceColumnId(null);
  };

  const handleAddColumn = async (e) => {
    e.preventDefault();
    if (!newColName.trim() || !boardId) return;
    await createNewColumn(boardId, newColName.trim());
    setNewColName('');
  };

  const handleAddTask = async (e) => {
    e.preventDefault();
    if (!newTaskTitle.trim() || !selectedColumnForTask) return;
    await createNewTask(selectedColumnForTask, newTaskTitle.trim(), "Generated workspace item context.");
    setNewTaskTitle('');
    setSelectedColumnForTask(null);
  };

  const handlePurgeColumn = async (columnId) => {
    if (!window.confirm("Confirm permanent removal of this tracking lane configuration?")) return;
    await purgeColumn(columnId);
  };

  const getPriorityStyles = (p) => {
    switch (p?.toUpperCase()) {
      case 'CRITICAL': return 'bg-rose-950/40 text-rose-400 border-rose-900';
      case 'HIGH': return 'bg-amber-950/40 text-amber-400 border-amber-900';
      case 'MEDIUM': return 'bg-indigo-950/40 text-indigo-400 border-indigo-900';
      default: return 'bg-slate-900 text-slate-400 border-slate-800';
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-slate-400 font-medium bg-slate-950 min-h-screen font-mono flex items-center justify-center">
        <span className="animate-pulse">HYDRATING_WORKSPACE_METRICS...</span>
      </div>
    );
  }

  if (errors) {
    return (
      <div className="p-8 text-rose-500 font-semibold bg-slate-950 min-h-screen font-mono">
        ERROR: {errors.detail || 'Failed to resolve workspace pipeline layout.'}
      </div>
    );
  }

  return (
    <div className="w-full min-h-screen bg-slate-950 p-2 text-slate-100 font-sans">
      <header className="mb-8 flex justify-between items-center border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-2xl font-bold tracking-tight text-white">{board?.title || board?.name || 'Workspace Execution Module'}</h1>
            <span className="text-[10px] font-mono font-bold tracking-wider uppercase px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-400">
              {userRole || 'Student Mode'}
            </span>
          </div>
          <p className="text-slate-400 text-xs max-w-2xl">{board?.description || 'Active academic tracking board execution view.'}</p>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="bg-slate-900 border border-slate-800 p-1 rounded-lg flex gap-1 font-mono text-xs">
            <button 
              onClick={() => setActiveView('KANBAN')} 
              className={`px-3 py-1.5 rounded-md font-bold transition-all cursor-pointer ${activeView === 'KANBAN' ? 'bg-indigo-600 text-white' : 'text-slate-400'}`}
            >
              VIEW_KANBAN
            </button>
            <button 
              onClick={() => setActiveView('GANTT')} 
              className={`px-3 py-1.5 rounded-md font-bold transition-all cursor-pointer ${activeView === 'GANTT' ? 'bg-indigo-600 text-white' : 'text-slate-400'}`}
            >
              VIEW_GANTT
            </button>
          </div>
          {isMutating && (
            <span className="text-[10px] font-mono text-indigo-400 bg-indigo-950/50 border border-indigo-800/80 px-2.5 py-1 rounded animate-pulse">
              SYNCING_STATE_DB
            </span>
          )}
        </div>
      </header>

      {activeView === 'GANTT' ? (
        <GanttChart boardData={board} onTimelineUpdated={() => loadBoard(boardId)} />
      ) : (
        <div className="flex gap-5 overflow-x-auto pb-4 items-start viewport-scroll-setup">
          {board?.columns?.map((column) => (
            <div 
              key={column.id} 
              className="w-80 shrink-0 bg-slate-900 rounded-xl border border-slate-800 p-4 flex flex-col max-h-[75vh]"
              onDragOver={handleDragOver} 
              onDrop={(e) => handleDrop(e, column.id, column.tasks?.length || 0)}
            >
              <div className="flex justify-between items-center mb-4 px-1">
                <div className="flex items-center gap-2 truncate pr-2">
                  <h2 className="font-semibold text-slate-200 text-sm tracking-wide truncate">{column.name}</h2>
                  <span className="text-xs font-bold bg-slate-800 text-slate-400 px-2.5 py-0.5 rounded-full border border-slate-700 shrink-0">
                    {column.tasks?.length || 0}
                  </span>
                </div>
                {isSupervisor && (
                  <button 
                    onClick={() => handlePurgeColumn(column.id)}
                    className="text-slate-500 hover:text-rose-400 font-mono text-xs transition-colors cursor-pointer shrink-0"
                    title="Purge Lane Block"
                  >
                    ×
                  </button>
                )}
              </div>

              <div className="flex flex-col gap-3 overflow-y-auto pr-1 grow min-h-[100px]">
                {column.tasks?.map((task, index) => (
                  <div
                    key={task.id} 
                    draggable={!isMutating}
                    onDragStart={(e) => handleDragStart(e, task.id, column.id)}
                    onDragOver={handleDragOver}
                    onDrop={(e) => { e.stopPropagation(); handleDrop(e, column.id, index); }}
                    className={`group bg-slate-950 p-4 rounded-lg border border-slate-800 hover:border-indigo-500/40 transition-all ${
                      draggedTaskId === task.id ? 'opacity-20 border-dashed border-indigo-500' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <h3 className="font-semibold text-xs text-white group-hover:text-indigo-400 transition-colors line-clamp-2">
                        {task.title}
                      </h3>
                      <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wider border shrink-0 ${getPriorityStyles(task.priority)}`}>
                        {task.priority || 'MEDIUM'}
                      </span>
                    </div>
                    {task.description && (
                      <p className="text-[11px] text-slate-400 line-clamp-2 mb-2 leading-relaxed">
                        {task.description}
                      </p>
                    )}
                    {(task.start_date || task.end_date) && (
                      <div className="text-[9px] text-slate-500 font-mono flex items-center gap-1 border-t border-slate-900 pt-2 mt-1">
                        <span>🗓️ {task.start_date || '...'} → {task.end_date || '...'}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {isSupervisor && (
                <div className="mt-3 pt-2 border-t border-slate-800/80">
                  {selectedColumnForTask === column.id ? (
                    <form onSubmit={handleAddTask} className="space-y-2">
                      <input 
                        type="text" 
                        autoFocus 
                        required 
                        placeholder="Task text context..." 
                        value={newTaskTitle} 
                        onChange={(e) => setNewTaskTitle(e.target.value)}
                        className="w-full px-2 py-1.5 bg-slate-950 border border-slate-800 text-xs text-white rounded focus:outline-none focus:border-indigo-500"
                      />
                      <div className="flex justify-end gap-1.5">
                        <button 
                          type="button" 
                          onClick={() => setSelectedColumnForTask(null)} 
                          className="px-2 py-1 bg-slate-800 rounded text-[10px] font-bold cursor-pointer"
                        >
                          Cancel
                        </button>
                        <button 
                          type="submit" 
                          className="px-2 py-1 bg-indigo-600 rounded text-[10px] font-bold text-white cursor-pointer"
                        >
                          Add
                        </button>
                      </div>
                    </form>
                  ) : (
                    <button 
                      onClick={() => setSelectedColumnForTask(column.id)} 
                      className="w-full py-1.5 border border-dashed border-slate-800 hover:border-slate-700 rounded-lg text-center text-[11px] text-slate-400 font-medium transition-colors cursor-pointer"
                    >
                      + Add Target Task
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}

          {/* Supervisor Workspace Extension: Create New Flow Pipeline Columns */}
          {isSupervisor && (
            <div className="w-80 shrink-0 bg-slate-900/40 border border-dashed border-slate-800 rounded-xl p-4">
              <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">Provision Progress Column</h3>
              <form onSubmit={handleAddColumn} className="space-y-2">
                <input 
                  type="text" 
                  required 
                  placeholder="Column label..." 
                  value={newColName} 
                  onChange={(e) => setNewColName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 text-xs text-white rounded-lg focus:outline-none focus:border-indigo-500"
                />
                <button 
                  type="submit" 
                  className="w-full py-2 bg-slate-800 hover:bg-slate-700 rounded-lg font-semibold text-xs text-indigo-400 transition-colors cursor-pointer"
                >
                  Deploy Column Block
                </button>
              </form>
            </div>
          )}
        </div>
      )}
    </div>
  );
}