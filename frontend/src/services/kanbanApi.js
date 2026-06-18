// frontend/src/services/kanbanApi.js
import axios from 'axios';

// Target configured environment variable based on build system (Vite standard)
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/**
 * Centrally Managed Client Runtime
 */
const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Zero-Trust Token Ingestion Interceptor
 * Maps authentication tracking context automatically using JWT Bearer signatures
 */
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * Standard Exception Aggregator
 */
const handleApiError = (error) => {
  if (error.response) {
    throw error.response.data;
  } else if (error.request) {
    throw { network_error: ['Upstream application gateway unreachable. Check docker network state.'] };
  } else {
    throw { system_error: [error.message] };
  }
};

/**
 * Unified Coordination & Visualization API Operations
 */
export const kanbanApi = {
  /**
   * Fetch complete project layout with ordered columns and nested tasks
   */
  fetchProjectTree: async (projectId) => {
    try {
      const response = await apiClient.get(`/coordination/projects/${projectId}/`);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Mutate column-level parameters or structural data definitions
   */
  createColumn: async (payload) => {
    try {
      const response = await apiClient.post('/kanban/columns/', payload);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  updateColumn: async (columnId, payload) => {
    try {
      const response = await apiClient.patch(`/kanban/columns/${columnId}/`, payload);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  deleteColumn: async (columnId) => {
    try {
      await apiClient.delete(`/kanban/columns/${columnId}/`);
    } catch (error) {
      handleApiError(error);
    }
  },

  /**
   * Mutate column ranking sequences across the workspace board layout
   */
  reorderColumns: async (columnId, newOrder) => {
    try {
      const response = await apiClient.post(`/kanban/columns/${columnId}/reorder-columns/`, {
        new_order: newOrder,
      });
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Instantiation and modification layers for atomic task components
   */
  createTask: async (payload) => {
    try {
      const response = await apiClient.post('/kanban/tasks/', payload);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  updateTask: async (taskId, payload) => {
    try {
      const response = await apiClient.patch(`/kanban/tasks/${taskId}/`, payload);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  deleteTask: async (taskId) => {
    try {
      await apiClient.delete(`/kanban/tasks/${taskId}/`);
    } catch (error) {
      handleApiError(error);
    }
  },

  /**
   * Mutate task structural sorting assignments within or across column groupings
   */
  reorderTask: async (taskId, targetColumnId, position) => {
    try {
      const response = await apiClient.post(`/kanban/tasks/${taskId}/reorder/`, {
        target_column_id: targetColumnId,
        position: position,
      });
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Sync Gantt chart chronological intervals back to the physical schema definitions
   */
  updateTaskTimeline: async (taskId, startDate, endDate) => {
    try {
      const response = await apiClient.post(`/kanban/tasks/${taskId}/update-timeline/`, {
        start_date: startDate,
        end_date: endDate,
      });
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },

  /**
   * Map dependencies across items and force backend cycle evaluations
   */
  setTaskDependencies: async (taskId, dependencyIds) => {
    try {
      const response = await apiClient.post(`/kanban/tasks/${taskId}/set-dependencies/`, {
        dependency_ids: dependencyIds,
      });
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
};