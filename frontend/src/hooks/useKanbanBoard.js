// frontend/src/hooks/useKanbanBoard.js
import { useState, useCallback } from 'react';
import API from '../services/api';

export const useKanbanBoard = () => {
  const [board, setBoard] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isMutating, setIsMutating] = useState(false);
  const [errors, setErrors] = useState(null);

  /**
   * Fetch and sort the complete workspace tree for a targeted project.
   */
  const loadBoard = useCallback(async (projectId) => {
    if (!projectId || projectId === 'undefined') return;
    setLoading(true);
    setErrors(null);
    try {
      const response = await API.get(`kanban/projects/${projectId}/`);
      const data = response.data;
      
      // Enforce strict sequencing constraints across structural elements
      if (data && Array.isArray(data.columns)) {
        data.columns.sort((a, b) => (a.order || 0) - (b.order || 0));
        data.columns.forEach(col => {
          if (Array.isArray(col.tasks)) {
            col.tasks.sort((a, b) => (a.order || 0) - (b.order || 0));
          } else {
            col.tasks = [];
          }
        });
      }
      setBoard(data);
    } catch (err) {
      console.error("Failed to load workspace tree data metrics:", err);
      setErrors(err.response?.data || { detail: "Failed to resolve backend context transmission." });
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Optimistically update UI elements during card drag-and-drop actions.
   * Restores a deep snapshot if the backend operation returns an error.
   */
  const moveTaskOptimistically = useCallback(async (
    taskId,
    sourceColumnId,
    targetColumnId,
    newPosition
  ) => {
    if (!board) return;

    // 1. Snapshot structural integrity state for network failure fallbacks
    const rollbackState = JSON.parse(JSON.stringify(board));
    setIsMutating(true);
    setErrors(null);

    // 2. Perform deep copies to modify client-side memory spaces safely
    const workingBoard = JSON.parse(JSON.stringify(board));
    let targetTask;

    workingBoard.columns = workingBoard.columns.map(col => {
      if (col.id === sourceColumnId) {
        targetTask = col.tasks.find(t => t.id === taskId);
        return { ...col, tasks: col.tasks.filter(t => t.id !== taskId) };
      }
      return col;
    });

    if (!targetTask) {
      setIsMutating(false);
      return;
    }

    // Adjust the parent tracking relationship property assignment
    targetTask.column = targetColumnId;

    workingBoard.columns = workingBoard.columns.map(col => {
      if (col.id === targetColumnId) {
        const updatedTasks = [...col.tasks];
        updatedTasks.splice(newPosition, 0, targetTask);
        // Normalize sequencing to prevent unique-together collisions on structural records
        return { ...col, tasks: updatedTasks.map((t, idx) => ({ ...t, order: idx })) };
      }
      if (col.id === sourceColumnId) {
        return { ...col, tasks: col.tasks.map((t, idx) => ({ ...t, order: idx })) };
      }
      return col;
    });

    setBoard(workingBoard);

    // 3. Transmit state to the API route handler matching coordination.urls configuration
    try {
      await API.post(`kanban/tasks/${taskId}/reorder/`, {
        target_column_id: targetColumnId,
        new_order: newPosition,
      });
    } catch (error) {
      console.error("Critical board reorder alignment failure. Reverting state topology...", error);
      setErrors(error.response?.data || { detail: "Network mutation transaction rejected." });
      setBoard(rollbackState);
    } finally {
      setIsMutating(false);
    }
  }, [board]);

  /**
   * Append a new tracking lane column wrapper to the dataset array.
   */
  const createNewColumn = useCallback(async (projectId, name) => {
    if (!board) return;
    setIsMutating(true);
    setErrors(null);
    try {
      const response = await API.post('kanban/columns/', {
        project: projectId,
        name,
        order: board.columns.length
      });
      const newCol = { ...response.data, tasks: [] };
      setBoard(prev => prev ? { ...prev, columns: [...prev.columns, newCol] } : null);
    } catch (err) {
      console.error("Column initialization sequence rejected:", err);
      setErrors(err.response?.data || err);
    } finally {
      setIsMutating(false);
    }
  }, [board]);

  /**
   * Initialize a new task data node within a specified column lane.
   */
  const createNewTask = useCallback(async (columnId, title, description) => {
    if (!board) return;
    setIsMutating(true);
    setErrors(null);
    
    const targetedColumn = board.columns.find(c => c.id === columnId);
    const orderMetric = targetedColumn ? targetedColumn.tasks.length : 0;

    try {
      const response = await API.post('kanban/tasks/', {
        column: columnId,
        title,
        description,
        assigned_to: null,
        order: orderMetric,
        priority: 'MEDIUM',
        due_date: null,
        start_date: null,
        end_date: null,
        dependencies: []
      });

      setBoard(prev => {
        if (!prev) return null;
        return {
          ...prev,
          columns: prev.columns.map(col => 
            col.id === columnId ? { ...col, tasks: [...col.tasks, response.data] } : col
          )
        };
      });
    } catch (err) {
      console.error("Task creation transaction rejected:", err);
      setErrors(err.response?.data || err);
    } finally {
      setIsMutating(false);
    }
  }, [board]);

  /**
   * Synchronize schedule boundaries for timeline data components.
   */
  const updateTaskTimeline = useCallback(async (taskId, startDate, endDate) => {
    if (!board) return;
    const rollbackState = JSON.parse(JSON.stringify(board));

    // Optimistically project accurate time metrics to the UI canvas layer
    setBoard((prevBoard) => {
      if (!prevBoard) return prevBoard;
      return {
        ...prevBoard,
        columns: prevBoard.columns.map((col) => ({
          ...col,
          ...col,
          tasks: col.tasks.map((t) =>
            t.id === taskId ? { ...t, start_date: startDate, end_date: endDate } : t
          ),
        })),
      };
    });

    try {
      await API.patch(`kanban/tasks/${taskId}/`, {
        start_date: startDate,
        end_date: endDate,
      });
    } catch (error) {
      console.error("Timeline date modification update rejected. Reverting context states...", error);
      setBoard(rollbackState);
      setErrors(error.response?.data || { detail: "Timeline synchronization failure." });
    }
  }, [board]);

  /**
   * Purge a structural column lane sequence from your context database environment.
   */
  const purgeColumn = useCallback(async (columnId) => {
    if (!board) return;
    setIsMutating(true);
    setErrors(null);
    try {
      await API.delete(`kanban/columns/${columnId}/`);
      setBoard(prev => prev ? {
        ...prev,
        columns: prev.columns.filter(col => col.id !== columnId)
      } : null);
    } catch (err) {
      console.error("Column removal transaction failed:", err);
      setErrors(err.response?.data || err);
    } finally {
      setIsMutating(false);
    }
  }, [board]);

  return {
    board,
    loading,
    isMutating,
    errors,
    loadBoard,
    moveTaskOptimistically,
    createNewColumn,
    createNewTask,
    updateTaskTimeline,
    purgeColumn
  };
};