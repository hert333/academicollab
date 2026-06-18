// frontend/src/components/analytics/GanttChart.jsx
import React, { useState, useRef, useEffect } from 'react';
import API from '../../services/api';

export default function GanttChart({ boardData, project, onTimelineUpdated }) {
  const [tasks, setTasks] = useState([]);
  const [dragState, setDragState] = useState(null);
  const containerRef = useRef(null);
  
  const dayWidth = 40; // Horizontal grid pixel calculation scale representing 1 operational calendar day

  // Unify incoming data stream configurations from different prop names across views
  const activeDataset = boardData || project;

  useEffect(() => {
    const extractedTasks = activeDataset?.columns?.flatMap(col => 
      col.tasks?.map(task => {
        // Safe mapping parameters for scheduling records; handles variations in database schema keys
        const startRaw = task.start_date || task.start || new Date().toISOString().split('T')[0];
        const dueRaw = task.due_date || task.end_date || task.end || new Date(Date.now() + 86400000 * 3).toISOString().split('T')[0];
        
        return {
          ...task,
          columnId: col.id,
          columnName: col.name,
          start: new Date(startRaw + 'T00:00:00'),
          end: new Date(dueRaw + 'T00:00:00')
        };
      }) || []
    ) || [];
    
    setTasks(extractedTasks);
  }, [activeDataset]);

  if (tasks.length === 0) {
    return (
      <div className="p-12 text-slate-400 font-mono text-sm bg-slate-900 border border-slate-800 rounded-xl text-center">
        [!] NO_SCHEDULED_TIMELINES_DETECTED — Assign milestone ranges within the workspaces to map progress nodes.
      </div>
    );
  }

  // Determine structural boundary parameters for timeline rendering calculations
  const startTimes = tasks.map(t => t.start.getTime());
  const endTimes = tasks.map(t => t.end.getTime());
  const minTime = new Date(Math.min(...startTimes));
  minTime.setDate(minTime.getDate() - 3); // Left coordinate pad margin
  
  const maxTime = new Date(Math.max(...endTimes));
  maxTime.setDate(maxTime.getDate() + 7); // Right coordinate pad margin

  const totalDays = Math.ceil((maxTime - minTime) / (1000 * 60 * 60 * 24)) || 1;
  const timelineWidth = totalDays * dayWidth;

  const formatDateString = (dateObj) => {
    const yyyy = dateObj.getFullYear();
    const mm = String(dateObj.getMonth() + 1).padStart(2, '0');
    const dd = String(dateObj.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
  };

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
          newEnd = new Date(newStart.getTime()); // Enforce bounding boundary constraint logic
        }
      }

      return { ...t, start: newStart, end: newEnd };
    }));
  };

  const handlePointerUp = async () => {
    if (!dragState) return;

    const modifiedTask = tasks.find(t => t.id === dragState.taskId);
    if (!modifiedTask) {
      setDragState(null);
      return;
    }

    const payloadStart = formatDateString(modifiedTask.start);
    const payloadDue = formatDateString(modifiedTask.end);
    
    const contextBackup = { ...dragState };
    setDragState(null);

    try {
      // Maps with centralized API routing schema config matching Django patterns
      const response = await API.patch(`kanban/tasks/${contextBackup.taskId}/`, {
        start_date: payloadStart,
        end_date: payloadDue // Updates underlying tracking array fields directly on coordination models
      });

      if (response.status === 200 && onTimelineUpdated) {
        onTimelineUpdated(); // Direct parent view state synchronization refresh loop callback
      }
    } catch (err) {
      console.error('API Timeline Mutation Failure. Restoring context tracking data:', err);
      // Fallback: Revert component state layout calculations using history frame values
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
      className="w-full bg-slate-900 rounded-xl border border-slate-800 p-6 overflow-hidden select-none mt-6"
      ref={containerRef}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
    >
      <div className="mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-800/60 pb-4 gap-2">
        <div>
          <h2 className="text-lg font-bold tracking-tight text-white font-mono uppercase">HCI_Interactive_Gantt_Engine</h2>
          <p className="text-xs text-slate-400 mt-1">Drag task centers to shift timelines. Grab right edge dividers to lengthen due parameters.</p>
        </div>
        <div className="flex items-center gap-3 shrink-0 self-start sm:self-center">
          {tasks.some(t => t.dependencies?.length > 0) && (
            <span className="text-[10px] text-amber-400 font-mono bg-amber-950/40 border border-amber-900/60 px-2 py-0.5 rounded">
              DEPENDENCIES_ACTIVE
            </span>
          )}
          <span className="text-[10px] bg-indigo-950 text-indigo-400 font-mono px-2 py-0.5 rounded border border-indigo-800">
            TRACKING: {tasks.length} NODES
          </span>
        </div>
      </div>

      <div className="overflow-x-auto border border-slate-950 rounded-lg bg-slate-950/40">
        <div style={{ width: `${timelineWidth + 240}px` }} className="flex flex-col">
          
          {/* Timeline Header Track */}
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

          {/* Grid Rows Track Mapping Layout */}
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
                    <div className="text-[9px] text-slate-500 font-mono uppercase mt-0.5 flex gap-2">
                      <span className="truncate max-w-[100px]">{task.columnName}</span>
                      {task.dependencies?.length > 0 && (
                        <span className="text-amber-500">DEP: {task.dependencies.length}</span>
                      )}
                    </div>
                  </div>

                  <div className="flex relative grow h-full items-center">
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
                      <span className="truncate touch-none pointer-events-none uppercase text-[9px]">
                        {task.priority || 'MEDIUM'}
                      </span>
                      
                      {/* Interaction Handle: Right Bound Resizer Element Handle */}
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