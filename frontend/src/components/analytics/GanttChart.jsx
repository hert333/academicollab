// frontend/src/components/analytics/GanttChart.jsx

import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

export default function GanttChart({ boardData, onTimelineUpdated }) {
  const [tasks, setTasks] = useState([]);
  const [dragState, setDragState] = useState(null);
  const containerRef = useRef(null);

  const API_BASE = window._env_?.VITE_API_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const dayWidth = 40; // Horizontal grid pixel calculation scale representing 1 operational calendar day

  // Synchronize internal state with changes from incoming server components
  useEffect(() => {
    const extractedTasks = boardData?.columns?.flatMap(col => 
      col.tasks?.map(task => {
        // Enforce safe standard layout fallbacks inside calculation objects
        const startRaw = task.start_date ? task.start_date : new Date().toISOString().split('T')[0];
        const dueRaw = task.due_date ? task.due_date : new Date(Date.now() + 86400000 * 3).toISOString().split('T')[0];
        
        return {
          ...task,
          columnId: col.id,
          columnName: col.name,
          start: new Date(startRaw + 'T00:00:00'),
          end: new Date(dueRaw + 'T00:00:00')
        };
      })
    ) || [];
    setTasks(extractedTasks);
  }, [boardData]);

  if (tasks.length === 0) {
    return <div className="p-6 text-slate-500 font-mono text-sm bg-slate-900 border border-slate-800 rounded-xl">NO_TIMELINE_DATA_AVAILABLE</div>;
  }

  // Determine structural boundary parameters for timeline render canvas
  const startTimes = tasks.map(t => t.start.getTime());
  const endTimes = tasks.map(t => t.end.getTime());
  const minTime = new Date(Math.min(...startTimes));
  minTime.setDate(minTime.getDate() - 3); // Left coordinate pad margin
  
  const maxTime = new Date(Math.max(...endTimes));
  maxTime.setDate(maxTime.getDate() + 7); // Right coordinate pad margin

  const totalDays = Math.ceil((maxTime - minTime) / (1000 * 60 * 60 * 24));
  const timelineWidth = totalDays * dayWidth;

  const formatDateString = (dateObj) => {
    const yyyy = dateObj.getFullYear();
    const mm = String(dateObj.getMonth() + 1).padStart(2, '0');
    const dd = String(dateObj.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  };

  // Capture vector coordinates when interaction elements are triggered
  const handlePointerDown = (e, task, mode) => {
    e.preventDefault();
    e.stopPropagation();
    
    setDragState({
      taskId: task.id,
      mode: mode, // 'SHIFT_BLOCK' or 'RESIZE_EDGE'
      initialClientX: e.clientX,
      initialStart: new Date(task.start.getTime()),
      initialEnd: new Date(task.end.getTime())
    });
  };

  const handlePointerMove = (e) => {
    if (!dragState) return;

    const deltaX = e.clientX - dragState.initialClientX;
    const daysDelta = Math.round(deltaX / dayWidth);

    setTasks(prevTasks => prevTasks.map(t => {
      if (t.id !== dragState.taskId) return t;

      let newStart = new Date(dragState.initialStart.getTime());
      let newEnd = new Date(dragState.initialEnd.getTime());

      if (dragState.mode === 'SHIFT_BLOCK') {
        newStart.setDate(newStart.getDate() + daysDelta);
        newEnd.setDate(newEnd.getDate() + daysDelta);
      } else if (dragState.mode === 'RESIZE_EDGE') {
        newEnd.setDate(newEnd.getDate() + daysDelta);
        if (newEnd < newStart) {
          newEnd = new Date(newStart.getTime()); // Enforce bounding constraint logic
        }
      }

      return { ...t, start: newStart, end: newEnd };
    }));
  };

  const handlePointerUp = async () => {
    if (!dragState) return;

    const modifiedTask = tasks.find(t => t.id === dragState.taskId);
    const payloadStart = formatDateString(modifiedTask.start);
    const payloadDue = formatDateString(modifiedTask.end);
    
    const contextBackup = { ...dragState };
    setDragState(null);

    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.patch(
        `${API_BASE}/api/kanban/tasks/${contextBackup.taskId}/update-timeline/`,
        {
          start_date: payloadStart,
          due_date: payloadDue
        },
        {
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`
          }
        }
      );

      if (response.status === 200 && onTimelineUpdated) {
        onTimelineUpdated(); // Direct parent synchronization state refresh loop
      }
    } catch (err) {
      console.error('API Mutation Failure. Restoring pristine tracking frames:', err);
      // Fallback: Revert component state layout calculations safely using history frame values
      setTasks(prevTasks => prevTasks.map(t => {
        if (t.id !== contextBackup.taskId) return t;
        return { 
          ...t, 
          start: contextBackup.initialStart, 
          end: contextBackup.initialEnd 
        };
      }));
    }
  };

  return (
    <div 
      className="w-full bg-slate-900 rounded-xl border border-slate-800 p-6 overflow-hidden select-none"
      ref={containerRef}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
    >
      <div className="mb-6">
        <h2 className="text-xl font-bold tracking-tight text-white font-mono">HCI_INTERACTIVE_GANTT_ENGINE</h2>
        <p className="text-xs text-slate-400 mt-1">Drag task centers horizontally to shift project timelines. Grab right edge lines to change due date ranges.</p>
      </div>

      <div className="overflow-x-auto border border-slate-950 rounded-lg bg-slate-950/40">
        <div style={{ width: `${timelineWidth + 240}px` }} className="flex flex-col">
          
          {/* Main Grid Render Header */}
          <div className="flex border-b border-slate-900 bg-slate-950 text-slate-400 text-xs font-mono py-3">
            <div className="w-60 shrink-0 pl-4 font-bold border-r border-slate-900 text-slate-300">TASK_IDENTIFIER</div>
            <div className="flex relative grow">
              {Array.from({ length: totalDays }).map((_, idx) => {
                const dayLabel = new Date(minTime);
                dayLabel.setDate(dayLabel.getDate() + idx);
                return (
                  <div 
                    key={idx} 
                    style={{ width: `${dayWidth}px` }} 
                    className="shrink-0 text-center text-[10px] border-r border-slate-900/30 font-medium"
                  >
                    {dayLabel.getDate()}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Grid Layout Rows Mapping Layer */}
          <div className="divide-y divide-slate-900/60 bg-slate-900/10">
            {tasks.map((task) => {
              const leftDays = Math.ceil((task.start - minTime) / (1000 * 60 * 60 * 24));
              const durationDays = Math.max(1, Math.ceil((task.end - task.start) / (1000 * 60 * 60 * 24)));
              
              const leftOffset = leftDays * dayWidth;
              const barWidth = durationDays * dayWidth;
              const activeTrackingMatch = dragState?.taskId === task.id;

              return (
                <div key={task.id} className="flex items-center h-14 group hover:bg-slate-900/30 transition-colors">
                  <div className="w-60 shrink-0 pl-4 pr-2 border-r border-slate-900 h-full flex flex-col justify-center bg-slate-950/20">
                    <span className="text-sm font-medium text-slate-200 truncate">{task.title}</span>
                    <span className="text-[10px] text-slate-500 font-mono uppercase mt-0.5">{task.columnName}</span>
                  </div>

                  <div className="flex relative grow h-full items-center">
                    {/* Native Drag Timeline Visual Bar component */}
                    <div
                      onPointerDown={(e) => handlePointerDown(e, task, 'SHIFT_BLOCK')}
                      style={{
                        left: `${leftOffset}px`,
                        width: `${barWidth}px`
                      }}
                      className={`absolute h-8 rounded-md flex items-center justify-between pl-3 pr-1 font-sans text-[11px] font-bold tracking-wide border shadow-sm cursor-grab active:cursor-grabbing transition-shadow ${
                        activeTrackingMatch ? 'ring-2 ring-indigo-500 opacity-90 shadow-xl z-50' : 'z-10'
                      } ${
                        task.priority === 'CRITICAL' ? 'bg-rose-950/80 text-rose-300 border-rose-800' :
                        task.priority === 'HIGH' ? 'bg-amber-950/80 text-amber-300 border-amber-800' :
                        task.priority === 'MEDIUM' ? 'bg-indigo-950/80 text-indigo-300 border-indigo-800' :
                        'bg-slate-800 text-slate-300 border-slate-700'
                      }`}
                    >
                      <span className="truncate touch-none pointer-events-none">{task.priority}</span>
                      
                      {/* Interaction Handle: Right Bound Resizer Element */}
                      <div 
                        onPointerDown={(e) => handlePointerDown(e, task, 'RESIZE_EDGE')}
                        className="w-2.5 h-full cursor-ew-resize hover:bg-white/20 active:bg-white/40 rounded-r-sm transition-colors"
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

        </div>
      </div>
    </div>
  );
}